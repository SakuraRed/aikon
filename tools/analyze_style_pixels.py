#!/usr/bin/env python3
"""Reproducible pixel diagnostics, NOT an art score or semantic ground truth.

Requires already installed numpy/scipy/Pillow/matplotlib. No network or browser.
Run with a manifest, output directory and optional --skip-missing while awaiting
an explicitly rendered input. Parent process enforces a wall-clock timeout.
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def worker(args):
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
    import numpy as np
    import scipy
    from scipy import ndimage as ndi
    from PIL import Image, ImageOps, ImageDraw, __version__ as pillow_version
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    size = args.size
    manifest_path = Path(args.manifest).resolve()
    config = json.loads(manifest_path.read_text(encoding='utf-8'))
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / 'assumptions-used.json', config)

    def roi_mask(roi):
        if len(roi) != 4 or not (0 <= roi[0] < roi[2] <= 1 and 0 <= roi[1] < roi[3] <= 1):
            raise ValueError('invalid normalized ROI: ' + repr(roi))
        mask = np.zeros((size, size), dtype=bool)
        x0, y0, x1, y1 = [round(v * size) for v in roi]
        mask[y0:y1, x0:x1] = True
        return mask

    def largest(mask):
        labels, count = ndi.label(mask)
        if not count:
            return np.zeros_like(mask)
        counts = np.bincount(labels.ravel())
        counts[0] = 0
        return labels == int(np.argmax(counts))

    def save_mask(folder, name, mask):
        Image.fromarray(mask.astype('uint8') * 255).save(folder / (name + '.png'))

    def background(rgb, alpha, asset, tolerance):
        low_alpha = alpha < config['alpha_threshold']
        if asset['background_mode'] == 'alpha-only':
            return low_alpha, None
        seed_roi = roi_mask(asset['background_seed_roi'])
        opaque_seed = seed_roi & ~low_alpha
        if not opaque_seed.any():
            raise ValueError('no opaque background seed pixels')
        seed_color = np.median(rgb[opaque_seed], axis=0)
        similar = np.max(np.abs(rgb.astype(float) - seed_color), axis=2) <= tolerance
        flood = ndi.binary_propagation(seed_roi & similar & ~low_alpha, mask=similar & ~low_alpha)
        return flood | low_alpha, seed_color.tolist()

    def eye_component(rgb, usable, roi, threshold):
        region = roi_mask(roi)
        dark = np.max(rgb, axis=2) < threshold
        labels, count = ndi.label(dark & usable & region)
        counts = np.bincount(labels.ravel())
        counts[0] = 0
        candidates = [i for i in range(1, count + 1) if counts[i] >= 20]
        if not candidates:
            return np.zeros_like(region), {'status': 'no_component', 'candidate_count': 0}
        chosen = max(candidates, key=lambda label: counts[label])
        mask = labels == chosen
        ys, xs = np.nonzero(mask)
        xy = np.column_stack((xs, ys)).astype(float)
        center = xy.mean(axis=0)
        values, vectors = np.linalg.eigh(np.cov((xy - center).T))
        major = vectors[:, np.argmax(values)]
        if major[1] < 0:
            major = -major
        minor = np.array([major[1], -major[0]])
        major_extent = float(np.ptp((xy - center) @ major) + 1)
        minor_extent = float(np.ptp((xy - center) @ minor) + 1)
        border = region & ~ndi.binary_erosion(region)
        touches = bool(np.any(mask & border))
        return mask, {
            'status': 'roi_clipped' if touches else 'measured', 'candidate_count': len(candidates),
            'area_px': int(mask.sum()), 'centroid_xy_normalized': (center / size).tolist(),
            'major_length_normalized': major_extent / size, 'minor_width_normalized': minor_extent / size,
            'projected_aspect_ratio': major_extent / minor_extent,
            'axis_clockwise_from_vertical_deg': float(np.degrees(np.arctan2(-major[0], major[1]))),
            'touches_manual_roi_boundary': touches,
            'bbox_xyxy_normalized': [float(xs.min()/size), float(ys.min()/size), float((xs.max()+1)/size), float((ys.max()+1)/size)],
        }

    def colors(rgb, mask, step):
        interior = ndi.binary_erosion(mask, iterations=2)
        if int(interior.sum()) < 30:
            return {'status': 'too_few_interior_pixels'}
        pixels = rgb[interior]
        quantized = pixels.astype('uint16') // step
        _, counts = np.unique(quantized, axis=0, return_counts=True)
        probabilities = np.sort(counts / counts.sum())[::-1]
        luma = pixels @ np.array([0.2126, 0.7152, 0.0722])
        return {'status': 'measured', 'pixels': int(len(pixels)), 'rgb_step': step,
                'occupied_bins': int(len(counts)), 'bins_for_95pct': int(np.searchsorted(np.cumsum(probabilities), .95) + 1),
                'entropy_bits': float(-(probabilities * np.log2(probabilities)).sum()),
                'largest_bin_fraction': float(probabilities[0]), 'top_three_bin_fraction': float(probabilities[:3].sum()),
                'luminance_std_0_255': float(luma.std())}

    def widths(mask):
        result = []
        for frac in np.arange(.20, 1.0, .02):
            y = min(size - 1, round(frac * size))
            xs = np.where(mask[max(0, y-1):min(size, y+2)].any(axis=0))[0]
            result.append({'canvas_y': round(float(frac), 3), 'left': float(xs.min()/size) if len(xs) else None,
                           'right': float((xs.max()+1)/size) if len(xs) else None,
                           'width': float((xs.max()-xs.min()+1)/size) if len(xs) else 0.0,
                           'occupied_width': float(len(xs)/size)})
        return result

    def aligned_widths(mask, pair):
        if not pair:
            return []
        center = np.asarray(pair['midpoint_xy_normalized']) * size
        theta = np.radians(pair['centerline_clockwise_deg'])
        u, v = np.array([np.cos(theta), np.sin(theta)]), np.array([-np.sin(theta), np.cos(theta)])
        yy, xx = np.nonzero(mask)
        xy = np.column_stack((xx, yy)) - center
        x, y = (xy @ u) / size, (xy @ v) / size
        result = []
        for offset in np.arange(-.45, .401, .02):
            row = x[np.abs(y - offset) <= .01]
            result.append({'offset_below_eye_line': round(float(offset), 3),
                           'width': float(np.ptp(row)) if len(row) else 0.0,
                           'occupied_width': float(len(np.unique(np.rint(row*size)))/size) if len(row) else 0.0,
                           'observed_pixels': int(len(row))})
        return result

    rows, masks_by_asset, missing = [], [], []
    for asset in config['assets']:
        source = Path(asset['path'])
        if not source.is_absolute():
            source = (manifest_path.parent / source).resolve()
        if not source.is_file():
            if args.skip_missing:
                missing.append({'id': asset['id'], 'path': str(source)})
                continue
            raise FileNotFoundError(source)
        original = Image.open(source).convert('RGBA')
        fitted = ImageOps.contain(original, (size, size), method=Image.Resampling.LANCZOS)
        normalized = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        normalized.paste(fitted, ((size - fitted.width)//2, (size - fitted.height)//2))
        pixels = np.asarray(normalized)
        rgb, alpha = pixels[:, :, :3], pixels[:, :, 3]
        folder = output / asset['id']
        folder.mkdir(exist_ok=True)
        normalized.save(folder / 'normalized.png')
        exclude = np.zeros((size, size), dtype=bool)
        for roi in asset.get('watermark_exclusion_rois', []):
            exclude |= roi_mask(roi)
        bg, seed_color = background(rgb, alpha, asset, config['background_tolerance'])
        valid = ~bg & ~exclude
        warnings = []
        bg_sensitivity = {}
        for tolerance in config['background_sensitivity']:
            other, _ = background(rgb, alpha, asset, tolerance)
            bg_sensitivity[str(tolerance)] = float((~other & ~exclude).mean())
            save_mask(folder, f'background-tolerance-{tolerance}', other)
        if max(bg_sensitivity.values()) - min(bg_sensitivity.values()) > .03:
            warnings.append('Foreground area changes by over 3 percentage points with background tolerance; dark hair/background separation is unstable.')
        if 'black' in asset['id']:
            warnings.append('Dark neutral hair may overlap the background color; the explicit background masks must be reviewed, not treated as gold.')
        eye_masks, eye_results, sensitivities = [], [], []
        for index, roi in enumerate(asset['eye_rois']):
            selected, measured = eye_component(rgb, valid, roi, config['dark_eye_threshold'])
            eye_masks.append(selected)
            eye_results.append(measured)
            sensitivity = {}
            for threshold in config['eye_sensitivity']:
                _, info = eye_component(rgb, valid, roi, threshold)
                sensitivity[str(threshold)] = info
            sensitivities.append(sensitivity)
            save_mask(folder, f'eye-{index+1}-roi', roi_mask(roi))
            save_mask(folder, f'eye-{index+1}-component', selected)
            if measured['status'] != 'measured' or measured.get('candidate_count') != 1:
                warnings.append(f'Eye {index+1}: {measured["status"]}, candidates={measured.get("candidate_count")}; do not treat as unambiguous.')
        eyes = eye_masks[0] | eye_masks[1]
        pair = None
        if all(item['status'] == 'measured' for item in eye_results):
            left, right = [np.array(item['centroid_xy_normalized']) for item in eye_results]
            delta = right - left
            pair = {'midpoint_xy_normalized': ((left+right)/2).tolist(), 'center_distance_normalized': float(np.linalg.norm(delta)),
                    'centerline_clockwise_deg': float(np.degrees(np.arctan2(delta[1], delta[0]))),
                    'mean_major_length_normalized': float(np.mean([item['major_length_normalized'] for item in eye_results])),
                    'mean_minor_width_normalized': float(np.mean([item['minor_width_normalized'] for item in eye_results])),
                    'eye_area_ratio_left_over_right': eye_results[0]['area_px']/eye_results[1]['area_px']}
            pair['spacing_over_mean_eye_width'] = pair['center_distance_normalized'] / pair['mean_minor_width_normalized']
        floats = rgb.astype(float)
        r, g, b = floats[:, :, 0], floats[:, :, 1], floats[:, :, 2]
        rule = config['warm_skin_rule']
        warm = (r > rule['red_min']) & (g > rule['green_min']) & (b > rule['blue_min']) & (r-g > rule['red_minus_green_min']) & (g-b > rule['green_minus_blue_min'])
        skin = largest(warm & valid & roi_mask(asset['skin_search_roi']))
        envelope = ndi.binary_fill_holes(skin) & valid
        covering = valid & ~envelope
        skin_sensitivity = {}
        inclusive_envelope = None
        for rg, gb in config.get('skin_ordering_sensitivity', []):
            alternative = ((r > rule['red_min']) & (g > rule['green_min']) & (b > rule['blue_min']) &
                           (r-g >= rg) & (g-b >= gb) & valid & roi_mask(asset['skin_search_roi']))
            alternative_skin = largest(alternative)
            alternative_face = ndi.binary_fill_holes(alternative_skin) & valid
            key = f'rg{rg}-gb{gb}'
            save_mask(folder, 'face-sensitivity-' + key, alternative_face)
            skin_sensitivity[key] = {
                'face_fraction_canvas': float(alternative_face.mean()),
                'covering_proxy_fraction_canvas': float((valid & ~alternative_face).mean()),
                'canvas_face_width_profile': widths(alternative_face),
                'eye_aligned_face_width_profile': aligned_widths(alternative_face, pair),
            }
            if (rg, gb) == (0, 0):
                inclusive_envelope = alternative_face
        if inclusive_envelope is not None and float(inclusive_envelope.mean()-envelope.mean()) > .02:
            warnings.append('Strict and neutral-inclusive face masks differ by over 2 canvas percentage points; strict face area/width is not reliable semantic segmentation.')
        # Some cheeks meet the canvas boundary and cannot be filled without an amodal assumption.
        warnings.append('Face envelope is the largest warm-color component with enclosed holes filled; hair-occluded face, edge-touching blush, and true head shape remain unobserved.')
        warnings.append('Covering proxy = remaining foreground, including hair, hat, accessories and segmentation residue; it is not a semantic hair label.')
        face_profile, upright_profile = widths(envelope), aligned_widths(envelope, pair)
        masks = {'background': bg, 'manual-exclusion': exclude, 'analysis-valid': valid,
                 'skin-color-component': skin, 'visible-face-envelope': envelope, 'covering-proxy': covering, 'eyes': eyes}
        for name, mask in masks.items():
            save_mask(folder, name, mask)
        overlay = np.zeros((size, size, 3), dtype='uint8')
        overlay[bg] = [50, 50, 50]
        overlay[covering] = [78, 145, 210]
        overlay[envelope] = [247, 184, 85]
        overlay[eyes] = [234, 54, 96]
        overlay[exclude] = [200, 70, 220]
        Image.fromarray(overlay).save(folder / 'segmentation-overlay.png')
        row = {'id': asset['id'], 'role': asset['role'], 'source_path': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
               'original_size': list(original.size), 'analysis_size': size, 'resampling': 'aspect-preserving contain, Lanczos, transparent padding',
               'background_seed_rgb': seed_color, 'foreground_fraction_canvas': float(valid.mean()),
               'watermark_excluded_fraction_canvas': float(exclude.mean()), 'background_fraction_canvas': float((bg & ~exclude).mean()),
               'skin_color_fraction_canvas': float(skin.mean()), 'face_envelope_fraction_canvas': float(envelope.mean()),
               'covering_proxy_fraction_canvas': float(covering.mean()),
               'visible_face_over_foreground': float(envelope.sum()/max(1, valid.sum())),
               'eyes': eye_results, 'eye_pair': pair, 'eye_threshold_sensitivity': sensitivities,
               'background_tolerance_foreground_fraction': bg_sensitivity,
               'skin_ordering_sensitivity': skin_sensitivity,
               'canvas_face_width_profile': face_profile, 'eye_aligned_face_width_profile': upright_profile,
               'color_complexity': {str(step): {'skin': colors(rgb, skin, step), 'covering_proxy': colors(rgb, covering, step)} for step in config['color_quantization_steps']},
               'curvature': {'status': 'not_estimated', 'reason': 'Hair occlusion and canvas crop prevent reliable recovery of a full head boundary; measured widths describe visible pixels only.'},
               'warnings': warnings}
        write_json(folder / 'metrics.json', row)
        rows.append(row)
        masks_by_asset.append((asset['id'], normalized, overlay, envelope, eyes, inclusive_envelope))
        print(asset['id'], 'measured; warnings=', len(warnings), flush=True)

    run = {'schema': 'aikon.pixel-analysis.v1', 'art_score': None, 'gold_segmentation': False,
           'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
           'versions': {'python': sys.version.split()[0], 'numpy': np.__version__, 'scipy': scipy.__version__, 'Pillow': pillow_version, 'matplotlib': matplotlib.__version__},
           'missing_inputs': missing, 'assets': rows}
    write_json(output / 'pixel-metrics.json', run)
    fields = ['id', 'foreground_fraction_canvas', 'face_envelope_fraction_canvas', 'covering_proxy_fraction_canvas', 'background_fraction_canvas',
              'visible_face_over_foreground', 'eye_mid_x', 'eye_mid_y', 'eye_major', 'eye_minor', 'eye_spacing', 'eye_centerline_deg',
              'skin_bins95_step16', 'skin_entropy_step16', 'covering_bins95_step16', 'inclusive_face_fraction', 'inclusive_covering_fraction']
    with (output / 'summary.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            value = {key: row[key] for key in fields if key in row}
            pair = row['eye_pair']
            if pair:
                value.update(eye_mid_x=pair['midpoint_xy_normalized'][0], eye_mid_y=pair['midpoint_xy_normalized'][1],
                             eye_major=pair['mean_major_length_normalized'], eye_minor=pair['mean_minor_width_normalized'],
                             eye_spacing=pair['center_distance_normalized'], eye_centerline_deg=pair['centerline_clockwise_deg'])
            color = row['color_complexity']['16']
            value.update(skin_bins95_step16=color['skin'].get('bins_for_95pct'), skin_entropy_step16=color['skin'].get('entropy_bits'),
                         covering_bins95_step16=color['covering_proxy'].get('bins_for_95pct'))
            inclusive = row['skin_ordering_sensitivity'].get('rg0-gb0')
            if inclusive:
                value.update(inclusive_face_fraction=inclusive['face_fraction_canvas'], inclusive_covering_fraction=inclusive['covering_proxy_fraction_canvas'])
            writer.writerow(value)
    if rows:
        fig, axes = plt.subplots(len(rows), 5, figsize=(15, max(3, len(rows)*3)), squeeze=False)
        for i, (name, normalized, overlay, envelope, eyes, inclusive) in enumerate(masks_by_asset):
            for j, data in enumerate([normalized, overlay, envelope, inclusive if inclusive is not None else envelope, eyes]):
                axes[i, j].imshow(data, cmap='gray' if j > 1 else None, vmin=0 if j > 1 else None, vmax=1 if j > 1 else None)
                axes[i, j].set_axis_off()
                if i == 0:
                    axes[i, j].set_title(['Normalized source', 'Strict masks (assumptions)', 'Strict face proxy', 'Neutral-inclusive sensitivity', 'Eye components'][j])
            axes[i, 0].text(0, -0.03, name, transform=axes[i,0].transAxes, fontsize=9)
        fig.suptitle('Pixel diagnostics — masks are algorithm assumptions, not gold or an art score', fontsize=12)
        fig.tight_layout()
        fig.savefig(output/'pixel-mask-board.png', dpi=140)
        plt.close(fig)
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        for row in rows:
            p = row['canvas_face_width_profile']
            axes[0].plot([x['width'] for x in p], [x['canvas_y'] for x in p], label=row['id'])
            p = row['eye_aligned_face_width_profile']
            axes[1].plot([x['width'] for x in p], [x['offset_below_eye_line'] for x in p], label=row['id'])
        axes[0].set(xlabel='Visible face span / canvas width', ylabel='Canvas y / height', title='Same canvas alignment; crop remains visible')
        axes[1].set(xlabel='Visible face span / canvas width', ylabel='Offset below eye line / canvas height', title='Eye-line de-rotated; no hidden-face reconstruction')
        for ax in axes:
            ax.invert_yaxis()
            ax.grid(alpha=.2)
        axes[1].legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(output/'face-width-profiles.png', dpi=160)
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(8, 6))
        for row in rows:
            p = row['skin_ordering_sensitivity'].get('rg0-gb0', {}).get('eye_aligned_face_width_profile', [])
            if p:
                ax.plot([x['width'] for x in p], [x['offset_below_eye_line'] for x in p], label=row['id'])
        ax.set(xlabel='Visible face span / canvas width', ylabel='Offset below eye line / canvas height',
               title='Neutral-inclusive sensitivity ONLY — not gold segmentation')
        ax.invert_yaxis()
        ax.grid(alpha=.2)
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(output/'face-width-neutral-inclusive.png', dpi=160)
        plt.close(fig)
        chosen_ids = ['mode-r1', 'mode-r2', 'draft-illustration-full-r001', 'candidate-illustration-short-imagegen-v1']
        selected = [(row, mask) for wanted in chosen_ids for row, mask in zip(rows, masks_by_asset) if row['id'] == wanted and row['eye_pair']]
        if selected:
            fig, axes = plt.subplots(2, len(selected), figsize=(3*len(selected), 6), squeeze=False)
            for i, (row, bundle) in enumerate(selected):
                _, normalized, _, strict, _, inclusive = bundle
                mask = inclusive if inclusive is not None else strict
                center = np.asarray(row['eye_pair']['midpoint_xy_normalized']) * size
                theta = np.radians(row['eye_pair']['centerline_clockwise_deg'])
                u, v = np.array([np.cos(theta),np.sin(theta)]), np.array([-np.sin(theta),np.cos(theta)])
                endpoints = [center - .15*size*v + offset*size*u for offset in (-.7,.7)]
                profile = row['skin_ordering_sensitivity'].get('rg0-gb0', {}).get('eye_aligned_face_width_profile', [])
                section = min(profile,key=lambda item:abs(item['offset_below_eye_line']+.15)) if profile else None
                axes[0,i].imshow(normalized)
                axes[1,i].imshow(mask, cmap='gray', vmin=0, vmax=1)
                for ax in axes[:,i]:
                    ax.plot([p[0] for p in endpoints],[p[1] for p in endpoints],color='#ff3155',linewidth=1.5)
                    ax.set_xlim(0,size)
                    ax.set_ylim(size,0)
                    ax.set_axis_off()
                axes[0,i].set_title(row['id'].replace('illustration-','').replace('imagegen-',''),fontsize=9)
                if section:
                    axes[1,i].text(.5,-.03,f"span {section['width']:.3f}W; occupied {section['occupied_width']:.3f}W",ha='center',transform=axes[1,i].transAxes,fontsize=9)
            fig.suptitle('Same pixel section: 0.15 canvas heights above each eye-pair centerline\nNeutral-inclusive face masks; crop/occlusion remain observed, not reconstructed',fontsize=11)
            fig.tight_layout()
            fig.savefig(output/'forehead-pixel-section.png',dpi=160)
            plt.close(fig)
        drafts = [r for r in rows if r['role'] == 'rejected-draft']
        references = [r for r in rows if r['role'] in {'user-style-reference', 'site-style-reference'}]
        if drafts and references:
            draft = drafts[0]
            metric_keys = ['face_envelope_fraction_canvas', 'covering_proxy_fraction_canvas', 'background_fraction_canvas']
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            x = np.arange(len(metric_keys))
            for idx, row in enumerate(rows):
                strict = np.array([row[key]*100 for key in metric_keys])
                inclusive = row['skin_ordering_sensitivity'].get('rg0-gb0', {})
                alt = np.array([inclusive.get('face_fraction_canvas', row[metric_keys[0]])*100,
                                inclusive.get('covering_proxy_fraction_canvas', row[metric_keys[1]])*100,
                                row[metric_keys[2]]*100])
                axes[0].errorbar(x, (strict+alt)/2, yerr=np.abs(strict-alt)/2, marker='o', capsize=3, label=row['id'])
            axes[0].set_xticks(x, ['Visible face', 'Covering proxy', 'Background'])
            axes[0].set(ylabel='% of canvas (strict-to-inclusive sensitivity range)', title='Pixel area assumptions, not confidence intervals/art score')
            for row in references:
                a = draft['skin_ordering_sensitivity'].get('rg0-gb0', {}).get('eye_aligned_face_width_profile', draft['eye_aligned_face_width_profile'])
                b = row['skin_ordering_sensitivity'].get('rg0-gb0', {}).get('eye_aligned_face_width_profile', row['eye_aligned_face_width_profile'])
                if len(a) == len(b) and a:
                    xs = [q['offset_below_eye_line'] for q in a]
                    inclusive_diff = np.array([q['width']-p['width'] for q,p in zip(a,b)])
                    strict_diff = np.array([q['width']-p['width'] for q,p in zip(draft['eye_aligned_face_width_profile'],row['eye_aligned_face_width_profile'])])
                    line, = axes[1].plot(xs, inclusive_diff, label='draft − '+row['id'])
                    axes[1].fill_between(xs, np.minimum(inclusive_diff,strict_diff), np.maximum(inclusive_diff,strict_diff), color=line.get_color(), alpha=.12)
            axes[1].axhline(0, color='black', linewidth=.8)
            axes[1].set(xlabel='Offset below eye line / canvas height', ylabel='Visible-width difference / canvas width', title='Inclusive curves; shading = strict-mask sensitivity')
            axes[0].legend(fontsize=7)
            axes[1].legend(fontsize=7)
            fig.tight_layout()
            fig.savefig(output/'pixel-structure-gaps.png', dpi=160)
            plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--size', type=int, choices=(512, 1024), default=512)
    parser.add_argument('--timeout', type=float, default=60)
    parser.add_argument('--skip-missing', action='store_true')
    parser.add_argument('--_worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args._worker:
        worker(args)
        return 0
    if not 0 < args.timeout <= 300:
        parser.error('--timeout must be in (0, 300] seconds')
    command = [sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()), *sys.argv[1:], '--_worker']
    started = time.monotonic()
    process = subprocess.Popen(command)
    record = {'worker_pid': process.pid, 'parent_pid': os.getpid(), 'cwd': os.getcwd(), 'command': command, 'timeout_s': args.timeout,
              'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    print(json.dumps(record, ensure_ascii=False), flush=True)
    try:
        result = process.wait(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=10)
        else:
            process.kill()  # Worker launches no subprocesses on POSIX.
        process.wait(timeout=10)
        print('HARD TIMEOUT: owned worker stopped; any partial analysis artifacts are not a completed result.', file=sys.stderr)
        return 124
    record.update(exit_code=result, elapsed_s=time.monotonic()-started, finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    write_json(out/'process-run.json', record)
    print(json.dumps({'worker_pid': process.pid, 'exit_code': result, 'elapsed_s': record['elapsed_s']}), flush=True)
    return result


if __name__ == '__main__':
    raise SystemExit(main())
