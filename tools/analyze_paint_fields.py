#!/usr/bin/env python3
"""Deterministic paint-field diagnostics; not a visual acceptance score.

Pillow, numpy and scipy are research/CI dependencies, not skill dependencies.
CLI work runs in one bounded child. Explicit ROIs distinguish a promised smooth
surface from a composition containing deliberate boundaries and highlights.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi


SCHEMA = "aikon.paint-fields.v1"
DEFAULT_RULES = {
    "grain_rms_max": 0.85,
    "mottle_rms_max": 0.50,
    "interior_translucent_fraction_max": 0.001,
    "island_contrast_min": 12.0,
    "island_area_min": 12,
}


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2,
                                    allow_nan=False) + "\n", encoding="utf-8")


def decoded_hash(image):
    rgba = image.convert("RGBA")
    return hashlib.sha256(f"RGBA:{rgba.width}x{rgba.height}:".encode() + rgba.tobytes()).hexdigest()


def region_mask(region, size, region_masks=None, source_size=None):
    width, height = size
    geometries = [key for key in ("bbox", "polygon", "mask_id") if key in region]
    if len(geometries) != 1:
        raise ValueError("each region needs exactly one of bbox, polygon or mask_id")
    if "mask_id" in region:
        name = region["mask_id"]
        if not isinstance(name, str) or not name:
            raise ValueError("mask_id must be a nonempty string")
        if region_masks is None or name not in region_masks:
            raise ValueError("unknown region mask: " + name)
        mask = region_masks[name]
        if not isinstance(mask, np.ndarray) or mask.dtype != np.bool_ or mask.ndim != 2:
            raise ValueError("region masks must be two-dimensional boolean numpy arrays")
        source_width, source_height = source_size or size
        if mask.shape != (source_height, source_width):
            raise ValueError("region mask dimensions must match the original image: " + name)
        if not mask.any():
            raise ValueError("region mask is empty: " + name)
        if size != (source_width, source_height):
            mask = np.asarray(Image.fromarray(mask).resize(size, Image.Resampling.NEAREST), dtype=bool)
        if not mask.any():
            raise ValueError("region mask became empty at the analysis scale: " + name)
        return mask.copy()
    if "bbox" in region:
        box = region["bbox"]
        if len(box) != 4 or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
            raise ValueError("bbox must be normalized [left, top, right, bottom]")
        mask = np.zeros((height, width), bool)
        x0, y0, x1, y1 = [round(v * d) for v, d in zip(box, [width, height, width, height])]
        mask[y0:y1, x0:x1] = True
        return mask
    if "polygon" in region:
        points = region["polygon"]
        if len(points) < 3 or any(len(p) != 2 or any(not 0 <= v <= 1 for v in p) for p in points):
            raise ValueError("polygon requires at least three normalized coordinate pairs")
        canvas = Image.new("1", size)
        ImageDraw.Draw(canvas).polygon([(round(x * width), round(y * height)) for x, y in points], fill=1)
        return np.asarray(canvas, dtype=bool)
    raise ValueError("each region needs bbox, polygon or mask_id")


def rms(values):
    return float(np.sqrt(np.mean(np.square(values)))) if values.size else None


def polynomial_residual(rgb, mask):
    """Quadratic trend removes a broad legal ramp; robust refit resists islands."""
    yy, xx = np.nonzero(mask)
    if len(xx) < 64:
        return None
    x = (xx - xx.mean()) / max(float(np.ptp(xx)), 1)
    y = (yy - yy.mean()) / max(float(np.ptp(yy)), 1)
    design = np.column_stack([np.ones(len(x)), x, y, x*x, x*y, y*y])
    values = rgb[mask]
    keep = np.ones(len(x), dtype=bool)
    for _ in range(3):
        coefficients = np.linalg.lstsq(design[keep], values[keep], rcond=None)[0]
        residual = values - design @ coefficients
        error = np.sqrt(np.mean(residual**2, axis=1))
        median = np.median(error)
        mad = np.median(np.abs(error - median))
        keep = error <= max(2.0, median + 3 * 1.4826 * mad)
        if keep.sum() < 32:
            break
    result = np.zeros_like(rgb, dtype=float)
    result[mask] = residual
    return result


def analyze_image(image, contract=None, region_masks=None):
    """Analyze explicit fields; optional masks use original-image boolean pixels.

    mask_id is mutually exclusive with bbox/polygon. Masks are sampled with
    nearest-neighbor when the image is reduced; empty masks are errors, not
    evidence of a clean field. Existing two-argument callers are unchanged.
    """
    contract = contract or {}
    if region_masks is not None and not isinstance(region_masks, dict):
        raise ValueError("region_masks must be a dictionary of boolean numpy arrays")
    if contract.get("schema", SCHEMA) != SCHEMA:
        raise ValueError("unsupported paint-fields schema")
    size = int(contract.get("long_edge", 1024))
    if not 128 <= size <= 2048:
        raise ValueError("long_edge must be between 128 and 2048")
    original = image.convert("RGBA")
    factor = min(1., size / max(original.size))
    normalized = original.resize(tuple(max(1, round(v * factor)) for v in original.size), Image.Resampling.LANCZOS)
    arr = np.asarray(normalized)
    rgb, alpha = arr[:, :, :3].astype(float), arr[:, :, 3]
    height, width = alpha.shape
    support = alpha > 0
    silhouette_interior = ndi.binary_erosion(support, iterations=3, border_value=1)
    opaque = alpha >= 254
    lowpass = ndi.gaussian_filter(rgb, sigma=(1.5, 1.5, 0), mode="reflect")
    medium = ndi.gaussian_filter(rgb, sigma=(6, 6, 0), mode="reflect")
    grain = rgb - lowpass
    mottle = lowpass - medium
    composite_fields = {}
    for label, background in (("black", 0.), ("white", 255.)):
        composite = rgb * (alpha[:, :, None] / 255.) + background * (1 - alpha[:, :, None] / 255.)
        composite_low = ndi.gaussian_filter(composite, sigma=(1.5, 1.5, 0), mode="reflect")
        composite_medium = ndi.gaussian_filter(composite, sigma=(6, 6, 0), mode="reflect")
        composite_fields[label] = (composite - composite_low, composite_low - composite_medium)
    gradient = np.maximum(np.max(np.abs(np.gradient(lowpass, axis=0)), axis=2),
                          np.max(np.abs(np.gradient(lowpass, axis=1)), axis=2))
    near_edge = ndi.binary_dilation(gradient > 2.0, iterations=12)
    regions = contract.get("regions") or [{"id": "whole-image-evidence", "bbox": [0, 0, 1, 1], "expectation": "evidence_only"}]
    rules = dict(DEFAULT_RULES)
    supplied_rules = contract.get("rules", {})
    if set(supplied_rules) - set(rules):
        raise ValueError("unknown paint rule")
    for key, value in supplied_rules.items():
        if not isinstance(value, (int, float)) or not np.isfinite(value) or value < 0:
            raise ValueError("paint rules must be finite nonnegative numbers")
        rules[key] = value
    results, masks, issues = [], {}, []
    island_mask = np.zeros_like(alpha, dtype=bool)
    grain_mask = np.zeros_like(alpha, dtype=bool)
    for region in regions:
        name = region["id"]
        if name in masks:
            raise ValueError("duplicate region id")
        expectation = region.get("expectation", "evidence_only")
        if expectation not in ("smooth_field", "opaque_surface", "evidence_only"):
            raise ValueError("unknown region expectation")
        mask = region_mask(region, normalized.size, region_masks, original.size)
        masks[name] = mask
        interior = ndi.binary_erosion(mask, iterations=3, border_value=0)
        # Straight RGB is still evidence for translucent paint. Alpha has its
        # own rule; requiring opacity here would hide precisely this defect.
        paint = interior & (alpha >= 16) & ~near_edge
        count = int(paint.sum())
        texture = {"sample_pixels": count, "grain_rms_0_255": rms(grain[paint]),
                   "mottle_rms_0_255": rms(mottle[paint]),
                   "basis": "straight RGB at alpha >=16; alpha checked separately",
                   "sample_fraction_of_region_interior": float(count / max(int(interior.sum()), 1)),
                   "measurement_status": "measured" if count >= 64 else "insufficient_interior"}
        for label, (composite_grain, composite_mottle) in composite_fields.items():
            texture["composite_" + label] = {"grain_rms_0_255": rms(composite_grain[paint]),
                                            "mottle_rms_0_255": rms(composite_mottle[paint])}
        alpha_samples = interior if expectation in ("smooth_field", "opaque_surface") else interior & silhouette_interior
        alpha_count = int(alpha_samples.sum())
        alpha_bad = alpha_samples & (alpha < 254)
        opacity = {"sample_pixels": alpha_count, "translucent_pixels": int(alpha_bad.sum()),
                   "translucent_fraction": float(alpha_bad.sum() / alpha_count) if alpha_count else None,
                   "min_alpha": int(alpha[alpha_samples].min()) if alpha_count else None}
        residual = polynomial_residual(rgb, interior & (alpha >= 16))
        islands = []
        if residual is not None:
            contrast = np.sqrt(np.mean(residual**2, axis=2))
            candidate = (contrast >= rules["island_contrast_min"]) & interior & (alpha >= 16)
            candidate = ndi.binary_opening(candidate, iterations=1)
            labels, _ = ndi.label(candidate)
            for index, bounds in enumerate(ndi.find_objects(labels), start=1):
                if bounds is None:
                    continue
                component = labels[bounds] == index
                area = int(component.sum())
                if not rules["island_area_min"] <= area <= max(1, int(interior.sum() * .25)):
                    continue
                local_y, local_x = np.nonzero(component)
                yy, xx = local_y + bounds[0].start, local_x + bounds[1].start
                local_luma = residual[yy, xx] @ np.array([.2126, .7152, .0722])
                islands.append({"area_pixels": area, "bbox_normalized": [float(xx.min()/width), float(yy.min()/height), float((xx.max()+1)/width), float((yy.max()+1)/height)],
                                "median_contrast_0_255": float(np.median(contrast[yy, xx])),
                                "signed_luma_residual_0_255": float(np.median(local_luma))})
                island_mask[yy, xx] = True
        failures = []
        if expectation == "smooth_field":
            if count < 64:
                failures.append("insufficient_texture_evidence")
            else:
                if texture["grain_rms_0_255"] > rules["grain_rms_max"]:
                    failures.append("grain_above_reference_bound")
                    grain_mask |= paint
                if texture["mottle_rms_0_255"] > rules["mottle_rms_max"]:
                    failures.append("mottle_above_reference_bound")
                    grain_mask |= paint
            if islands:
                failures.append("unexpected_color_islands_in_declared_smooth_field")
        if expectation in ("smooth_field", "opaque_surface"):
            if not alpha_count:
                failures.append("insufficient_opacity_evidence")
            elif opacity["translucent_fraction"] > rules["interior_translucent_fraction_max"]:
                failures.append("translucent_interior")
        issues.extend({"region": name, "code": reason} for reason in failures)
        results.append({"id": name, "expectation": expectation, "geometry": {k: region[k] for k in ("bbox", "polygon", "mask_id") if k in region},
                        "texture": texture, "opacity": opacity,
                        "color_islands": {"count": len(islands), "components": islands,
                                          "interpretation": "geometric evidence only; specular plausibility requires layer/light-direction review"},
                        "status": "fail" if failures else ("no_rule_failure" if expectation != "evidence_only" else "evidence_only"), "failures": failures})
    global_samples = int(silhouette_interior.sum())
    global_translucent = silhouette_interior & (alpha < 254)
    # RGB under alpha=0 is ignored. AA only differs if its straight RGB strongly
    # departs from the nearest opaque pixel. This is advisory, never an art gate.
    fringe = np.zeros_like(alpha, dtype=bool)
    if opaque.any():
        distances, nearest = ndi.distance_transform_edt(~opaque, return_indices=True)
        shell = (alpha > 0) & (alpha < 254) & (distances <= 4)
        nearest_rgb = rgb[nearest[0], nearest[1]]
        composited_delta = np.max(np.abs(rgb - nearest_rgb), axis=2) * (alpha / 255.)
        fringe = shell & (composited_delta > 32)
    report = {"schema": SCHEMA, "decoded_rgba_sha256": decoded_hash(original),
              "source_size": list(original.size), "analysis_size": list(normalized.size),
              "scales": {"grain_gaussian_sigma_px": 1.5, "mottle_gaussian_sigma_px": [1.5, 6],
                         "edge_gradient_cutoff_rgb_per_px": 2., "edge_exclusion_radius_px": 12,
                         "region_erosion_px": 3, "alpha_opaque_min": 254},
              "rules": rules, "threshold_provenance": contract.get("threshold_provenance", "provisional conservative artifact bounds; not a universal style score"),
              "regions": results, "issues": issues,
              "global_alpha_evidence": {"interior_pixels": global_samples, "translucent_pixels": int(global_translucent.sum()),
                                        "translucent_fraction": float(global_translucent.sum()/global_samples) if global_samples else None,
                                        "suspected_fringe_pixels": int(fringe.sum()), "fringe_is_advisory": True},
              "status": "fail" if issues else "no_rule_failure",
              "visual_acceptance": "not_assessed", "limitations": [
                  "No-region mode is evidence only and cannot certify a clean painting.",
                  "Manual ROIs must avoid intended boundaries; masks and coverage are exported for audit.",
                  "Broad nonquadratic shading and legal highlights may create island evidence.",
                  "No pixel statistic determines whether a highlight follows strand geometry or lighting.",
                  "Transparent interior inferred from the alpha support is advisory unless an opaque surface is explicitly declared."]}
    maps = {"normalized": normalized, "islands": island_mask, "texture_regions": grain_mask,
            "interior_alpha": global_translucent, "fringe": fringe, "regions": masks,
            "grain_energy": np.sqrt(np.mean(grain**2, axis=2)), "mottle_energy": np.sqrt(np.mean(mottle**2, axis=2))}
    return report, maps


def save_evidence(output, report, maps, contract):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "metrics.json", report)
    write_json(output / "regions-used.json", contract)
    maps["normalized"].save(output / "normalized.png")
    overlay = maps["normalized"].convert("RGB")
    draw = ImageDraw.Draw(overlay)
    for index, (name, mask) in enumerate(maps["regions"].items()):
        Image.fromarray(mask.astype("uint8") * 255).save(output / f"region-{index:02d}.png")
        yy, xx = np.nonzero(mask)
        if len(xx):
            draw.rectangle([int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())], outline="#ffdd00", width=2)
            draw.text((int(xx.min()) + 4, int(yy.min()) + 4), name, fill="#ffdd00")
    overlay.save(output / "regions-overlay.png")
    for name in ("islands", "texture_regions", "interior_alpha", "fringe"):
        Image.fromarray(maps[name].astype("uint8") * 255).save(output / f"{name}-mask.png")
    for name in ("grain_energy", "mottle_energy"):
        # Fixed 0..3 RGB units legend: black=0, red=1.5, yellow=3+.
        level = np.clip(maps[name] / 3, 0, 1)
        heat = np.stack([np.minimum(level*2, 1), np.maximum(level*2-1, 0), np.zeros_like(level)], axis=-1)
        Image.fromarray(np.uint8(np.rint(heat * 255))).save(output / f"{name}-heat.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--regions")
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--fail-on-issues", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 300:
        parser.error("timeout must be in 1..300 seconds")
    if not args.worker:
        try:
            from .run_visual_e2e import run_bounded
        except ImportError:
            from run_visual_e2e import run_bounded
        try:
            return run_bounded([sys.executable, "-B", __file__, *sys.argv[1:], "--worker"], timeout=args.timeout)
        except subprocess.TimeoutExpired:
            print("paint diagnostic exceeded wall-clock limit", file=sys.stderr)
            return 124
    contract = json.loads(Path(args.regions).read_text(encoding="utf-8")) if args.regions else {}
    with Image.open(args.image) as image:
        report, maps = analyze_image(image, contract)
    report["source_file"] = Path(args.image).name
    save_evidence(args.output, report, maps, contract)
    print(json.dumps({"status": report["status"], "issues": report["issues"], "output": args.output}, ensure_ascii=False))
    return 2 if args.fail_on_issues and report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
