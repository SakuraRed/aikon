#!/usr/bin/env python3
"""Measure rendered eye contours, independently of SVG tag names or labels.

API: analyze_eye_mask(mask) -> JSON-compatible report. Masks are 2-D bool or
floating coverage in [0, 1]. analyze_pair reports original two-eye geometry;
it does not score pose or resemblance. Imported callers supply a deadline.
CLI workers use the existing 50-second process-tree deadline.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Engineering tolerances fixed from analytic controls, before reference runs.
# They permit modest contour departures, not arbitrary ellipse-like eyes.
RULES = {
    "contour_aa_neighborhood_pixels": 3,
    "min_minor_diameter_pixels": 16.0,
    "min_aspect_ratio": 1.45,
    "max_aspect_ratio": 4.0,
    "capsule_rms_fraction_width_max": 0.020,
    "capsule_p95_fraction_width_max": 0.040,
    "ellipse_advantage_ratio_max": 0.55,
    "ellipse_advantage_min_capsule_error": 0.008,
}


def _coverage(mask):
    import numpy as np
    a = np.asarray(mask)
    if a.ndim != 2 or not 3 <= min(a.shape) or max(a.shape) > 4096:
        raise ValueError("Mask must be 2-D, at least 3 pixels per side, at most 4096")
    if a.dtype == bool:
        a = a.astype(float)
    elif not np.issubdtype(a.dtype, np.floating):
        raise ValueError("Use bool or floating coverage in [0, 1], not raw PNG bytes")
    if not np.isfinite(a).all() or a.min() < 0 or a.max() > 1:
        raise ValueError("Coverage must be finite and in [0, 1]")
    return a.astype(float)


def _contour(a):
    """Subpixel .5 crossings of horizontal/vertical pixel-center edges."""
    import numpy as np
    points = []
    for axis in (0, 1):
        before = a[:-1, :] if axis == 0 else a[:, :-1]
        after = a[1:, :] if axis == 0 else a[:, 1:]
        yy, xx = np.where((before >= .5) != (after >= .5))
        q = (.5 - before[yy, xx]) / (after[yy, xx] - before[yy, xx])
        points.append(np.column_stack((xx + (q if axis == 1 else 0), yy + (q if axis == 0 else 0))))
    return np.concatenate(points)


def _fit(points, center, angle, half_length, half_width, model):
    import numpy as np
    from scipy.optimize import least_squares

    def distance(params, points=points):
        cx, cy, theta, h, r = params
        dx, dy = (points - (cx, cy)).T
        t = dx * np.cos(theta) + dy * np.sin(theta)
        u = -dx * np.sin(theta) + dy * np.cos(theta)
        if model == "capsule":
            return np.hypot(u, np.maximum(np.abs(t) - h, 0)) - r
        f = (t / h) ** 2 + (u / r) ** 2 - 1
        norm = 2 * np.sqrt(t * t / h ** 4 + u * u / r ** 4)
        return f / np.maximum(norm, 1e-9)

    h0 = max(.1, half_length - half_width) if model == "capsule" else half_length
    initial = [*center, angle, h0, half_width]
    bounds = (
        [center[0] - half_width * .3, center[1] - half_width * .3, angle - .15, max(.01, h0 * .5), half_width * .65],
        [center[0] + half_width * .3, center[1] + half_width * .3, angle + .15, h0 * 1.5 + 1, half_width * 1.35],
    )
    fitted = least_squares(distance, initial, bounds=bounds, max_nfev=150, ftol=1e-9, xtol=1e-9, gtol=1e-9)
    residual = distance(fitted.x)
    # Normalize both candidate families against the same observed minor width.
    scale = 2 * half_width
    cx, cy, theta, h, r = fitted.x
    return {
        "converged": bool(fitted.success),
        "center_xy": [float(cx), float(cy)],
        "major_axis_degrees_clockwise_from_x": float(np.degrees(theta) % 180),
        "radius_or_half_width_pixels": float(r),
        "half_segment_or_half_length_pixels": float(h),
        "rms_distance_pixels": float(np.sqrt(np.mean(residual ** 2))),
        "rms_fraction_observed_width": float(np.sqrt(np.mean(residual ** 2)) / scale),
        "p95_fraction_observed_width": float(np.percentile(abs(residual), 95) / scale),
        "distance_definition": "exact signed capsule distance" if model == "capsule" else "first-order Euclidean ellipse contour distance",
    }


def analyze_eye_mask(mask):
    """Classify only a supplied eye outline; no identity, color, or pose score."""
    import numpy as np
    from scipy import ndimage as ndi
    a = _coverage(mask)
    solid = a >= .5
    _, count = ndi.label(solid)
    report = {"schema": "aikon.capsule-geometry.v1", "status": "fail", "issues": [], "rules": dict(RULES), "components": int(count), "mask_shape_hw": list(a.shape)}
    if count != 1:
        report["issues"].append("empty_or_disconnected_eye_mask")
        return report
    if solid[0].any() or solid[-1].any() or solid[:, 0].any() or solid[:, -1].any():
        report["issues"].append("eye_mask_touches_canvas_edge")
        return report
    holes = ndi.binary_fill_holes(solid) & ~solid
    if holes.any():
        report["issues"].append("eye_mask_contains_holes")
    # Only coverage adjacent to the observed contour participates in moments.
    # A remote faint speck must not rotate the PCA axis of the actual eye.
    # Lanczos3 downsampling has a three-pixel support; square neighborhoods also
    # cover diagonals. This is a sampling-boundary allowance, not smoothing or a
    # larger fit tolerance. Remote faint components remain reported as defects.
    support = ndi.binary_dilation(solid, structure=np.ones((3, 3), bool), iterations=RULES["contour_aa_neighborhood_pixels"])
    remote_coverage = a[~support].sum()
    report["coverage_outside_contour_neighborhood"] = float(remote_coverage)
    if remote_coverage > .5:
        report["issues"].append("stray_coverage_outside_eye_contour")
    yy, xx = np.nonzero(support & (a > 0))
    weights = a[yy, xx]
    coords = np.column_stack((xx, yy))
    center = np.average(coords, axis=0, weights=weights)
    delta = coords - center
    covariance = (delta * weights[:, None]).T @ delta / weights.sum()
    values, vectors = np.linalg.eigh(covariance)
    major = vectors[:, np.argmax(values)]
    if major[1] < 0:
        major = -major
    minor = np.array([-major[1], major[0]])
    angle = float(np.arctan2(major[1], major[0]))
    points = _contour(a)
    if len(points) > 20000:
        report["issues"].append("excessive_contour_complexity")
        return report
    projected = np.column_stack(((points - center) @ major, (points - center) @ minor))
    lengths = np.ptp(projected, axis=0)
    # A single exactly-half-covered pixel has four coincident .5 crossings;
    # a half-covered line has zero transverse extent. PCA roundoff may make
    # that zero a few ulps wide. Do not divide before recognizing degeneracy.
    roundoff = 16 * np.finfo(float).eps * max(a.shape)
    if not np.isfinite(lengths).all() or np.min(lengths) <= roundoff:
        report["issues"].append("degenerate_eye_contour")
        report["status"] = "not_assessed"
        report["contour_extent_pixels"] = lengths.tolist() if np.isfinite(lengths).all() else None
        return report
    height, width = lengths
    aspect = height / width
    report["observed"] = {
        "center_xy": center.tolist(), "major_axis_degrees_clockwise_from_x": math.degrees(angle) % 180,
        "center_xy_canvas_fraction": [float(center[0] / a.shape[1]), float(center[1] / a.shape[0])],
        "major_length_pixels": float(height), "minor_width_pixels": float(width),
        "major_length_canvas_diagonal_fraction": float(height / math.hypot(*a.shape)),
        "minor_width_canvas_diagonal_fraction": float(width / math.hypot(*a.shape)),
        "aspect_ratio": float(aspect), "area_coverage_pixels": float(a.sum()),
        "area_fraction_oriented_box": float(a.sum() / (height * width)),
        "contour_points": len(points),
    }
    if width < RULES["min_minor_diameter_pixels"]:
        report["issues"].append("insufficient_resolution_for_contour_gate")
        report["status"] = "not_assessed"
        return report
    if not RULES["min_aspect_ratio"] <= aspect <= RULES["max_aspect_ratio"]:
        report["issues"].append("outside_elongated_capsule_aspect_contract")
    fits = {name: _fit(points, center, angle, height / 2, width / 2, name) for name in ("capsule", "ellipse")}
    report["fits"] = fits
    c, e = fits["capsule"], fits["ellipse"]
    if not c["converged"] or not e["converged"]:
        report["issues"].append("contour_fit_did_not_converge")
    if c["rms_fraction_observed_width"] > RULES["capsule_rms_fraction_width_max"]:
        report["issues"].append("capsule_contour_rms_exceeded")
    if c["p95_fraction_observed_width"] > RULES["capsule_p95_fraction_width_max"]:
        report["issues"].append("capsule_contour_tail_exceeded")
    ratio = e["rms_fraction_observed_width"] / max(c["rms_fraction_observed_width"], 1e-9)
    report["ellipse_to_capsule_rms_ratio"] = ratio
    if ratio < RULES["ellipse_advantage_ratio_max"] and c["rms_fraction_observed_width"] > RULES["ellipse_advantage_min_capsule_error"]:
        report["issues"].append("ellipse_explains_contour_better")
    # Intersection profiles are evidence, not independently tuned pass values.
    profiles = []
    t, u = projected.T
    for fraction in np.linspace(-.9, .9, 19):
        select = abs(t - fraction * height / 2) <= max(1., height * .015)
        profiles.append({"major_fraction": float(fraction), "width_fraction": float(np.ptp(u[select]) / width) if select.sum() >= 2 else None})
    report["width_profile"] = profiles
    report["status"] = "no_rule_failure" if not report["issues"] else "fail"
    report["scope"] = "near-circular-ended elongated capsule contour only; not pose, naturalness, identity, or reference similarity"
    return report


def analyze_pair(masks):
    """Keep original geometry; no independent eye alignment erases differences."""
    import numpy as np
    if len(masks) != 2:
        raise ValueError("Exactly two eye masks are required")
    if np.asarray(masks[0]).shape != np.asarray(masks[1]).shape:
        raise ValueError("Eye masks must use the same original canvas")
    reports = [analyze_eye_mask(mask) for mask in masks]
    result = {"eyes": reports, "relationship": None}
    if all("observed" in r for r in reports):
        a, b = (r["observed"] for r in reports)
        dx, dy = np.array(b["center_xy"]) - a["center_xy"]
        separation = math.hypot(dx, dy)
        difference = abs(a["major_axis_degrees_clockwise_from_x"] - b["major_axis_degrees_clockwise_from_x"])
        result["relationship"] = {
            "center_vector_xy_pixels": [float(dx), float(dy)],
            "center_distance_pixels": separation,
            "center_distance_canvas_diagonal_fraction": separation / math.hypot(*np.asarray(masks[0]).shape),
            "eye_line_degrees_clockwise_from_x": math.degrees(math.atan2(dy, dx)),
            "major_axis_difference_degrees": min(difference, 180 - difference),
            "major_length_ratio_right_over_left": b["major_length_pixels"] / a["major_length_pixels"],
            "minor_width_ratio_right_over_left": b["minor_width_pixels"] / a["minor_width_pixels"],
            "status": "measurement_only_not_pitch_estimation",
        }
    return result


def extract_dark_roi(image, bbox, seed_xy, max_channel=100):
    """Transparent ROI protocol: seed's connected dark component, no smoothing.

    bbox uses integer original-image x0,y0,x1,y1. Threshold and all retained
    pixels are public; use only after viewing to ensure hair is excluded.
    """
    import numpy as np
    from scipy import ndimage as ndi
    a = np.asarray(image.convert("RGBA"))
    x0, y0, x1, y1 = bbox
    sx, sy = seed_xy
    if not (0 <= x0 < x1 <= a.shape[1] and 0 <= y0 < y1 <= a.shape[0] and x0 <= sx < x1 and y0 <= sy < y1):
        raise ValueError("ROI and seed must be inside the image")
    candidates = (a[y0:y1, x0:x1, :3].max(axis=2) <= max_channel) & (a[y0:y1, x0:x1, 3] >= 250)
    labels, _ = ndi.label(candidates)
    selected = labels[sy - y0, sx - x0]
    if selected == 0:
        raise ValueError("Seed is not a dark opaque pixel")
    local_mask = labels == selected
    if local_mask[0].any() or local_mask[-1].any() or local_mask[:, 0].any() or local_mask[:, -1].any():
        raise ValueError("Extracted eye reaches ROI edge; review ROI instead of trimming")
    result = np.zeros(a.shape[:2], bool)
    result[y0:y1, x0:x1] = local_mask
    return result


def analytic_mask(shape="capsule", width=60, height=120, angle=0, size=256, supersample=4):
    """Independent analytic fixtures rasterized with area supersampling."""
    import numpy as np
    if supersample not in (1, 2, 4, 8) or size * supersample > 2048:
        raise ValueError("Unsupported analytic fixture budget")
    coords = (np.arange(size * supersample) + .5) / supersample - size / 2
    y, x = np.meshgrid(coords, coords, indexing="ij")
    theta = math.radians(angle)
    u, t = x * math.cos(theta) + y * math.sin(theta), -x * math.sin(theta) + y * math.cos(theta)
    r, h = width / 2, height / 2
    if shape == "capsule":
        inside = u * u + np.maximum(abs(t) - (h - r), 0) ** 2 <= r * r
    elif shape == "ellipse":
        inside = (u / r) ** 2 + (t / h) ** 2 <= 1
    elif shape == "squared_caps":
        corner = r * .2
        inside = np.maximum(abs(u) - r + corner, 0) ** 2 + np.maximum(abs(t) - h + corner, 0) ** 2 <= corner ** 2
    elif shape == "pointed_caps":
        inside = (abs(t) <= h) & (abs(u) <= r * np.minimum(1, (h - abs(t)) / r))
    else:
        raise ValueError("Unknown analytic fixture shape")
    return inside.reshape(size, supersample, size, supersample).mean(axis=(1, 3))


def _save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def save_eye_evidence(mask, report, output, source=None):
    import numpy as np
    from PIL import Image, ImageDraw
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    a = _coverage(mask)
    Image.fromarray(np.uint8(np.rint(a * 255))).save(output / "mask.png")
    _save(output / "report.json", report)
    yy, xx = np.nonzero(a >= .5)
    if not len(xx):
        return
    bbox = (max(0, int(xx.min()) - 12), max(0, int(yy.min()) - 12), min(a.shape[1], int(xx.max()) + 13), min(a.shape[0], int(yy.max()) + 13))
    base = source.convert("RGB") if source is not None else Image.fromarray(np.uint8(np.rint(a * 255))).convert("RGB")
    overlay = base.copy()
    draw = ImageDraw.Draw(overlay)
    for px, py in _contour(a):
        draw.point((round(px), round(py)), fill="#ff2d8b")
    base.crop(bbox).save(output / "source-crop.png")
    # Preserve aspect ratio in actual diagnostic panel; no geometry-normalized
    # artwork is used as the output or as an apparent visual correction.
    crop = overlay.crop(bbox)
    crop.thumbnail((380, 460))
    panel = Image.new("RGB", (760, 500), "#eeeeee")
    panel.paste(crop, ((380 - crop.width) // 2, 24))
    draw = ImageDraw.Draw(panel)
    draw.text((16, 476), report["status"], fill="#111111")
    observed = report.get("observed")
    if observed and "fits" in report:
        draw.text((390, 18), "Contour width / observed max width", fill="#111111")
        draw.rectangle((400, 48, 740, 450), outline="#777777")
        profile = report["width_profile"]
        pts = [(400 + 340 * p["width_fraction"], 249 + 210 * p["major_fraction"]) for p in profile if p["width_fraction"] is not None]
        if len(pts) > 1:
            draw.line(pts, fill="#d72071", width=3)
        draw.text((390, 458), "aspect %.3f  axis %.2f deg" % (observed["aspect_ratio"], observed["major_axis_degrees_clockwise_from_x"]), fill="#111111")
    panel.save(output / "contour-profile.png")


def reference_study(output):
    import numpy as np
    from PIL import Image
    from tools import review_gloss_pairs as review
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    controls = []
    for shape in ("capsule", "ellipse", "squared_caps", "pointed_caps"):
        for width, height, angle in ((60, 120, 0), (60, 120, 17), (24, 60, -31), (80, 240, 43)):
            size = 384 if height > 200 else 256
            name = "%s-w%s-h%s-a%s" % (shape, width, height, angle)
            mask = analytic_mask(shape, width, height, angle, size)
            report = analyze_eye_mask(mask)
            expected = "no_rule_failure" if shape == "capsule" else "fail"
            controls.append({"name": name, "expected": expected, "observed": report["status"], "specific_issues": report["issues"], "matches_expected": report["status"] == expected})
            save_eye_evidence(mask, report, output / "controls" / name)
    r1_path = ROOT / "ref/user-mode/r1.png"
    image = Image.open(r1_path).convert("RGBA")
    extraction = [
        {"name": "left", "bbox": [135, 650, 295, 900], "seed_xy": [211, 770], "max_channel": 100},
        {"name": "right", "bbox": [560, 810, 720, 1045], "seed_xy": [641, 930], "max_channel": 100},
    ]
    masks = [extract_dark_roi(image, row["bbox"], row["seed_xy"], row["max_channel"]) for row in extraction]
    pair = analyze_pair(masks)
    for row, mask, report in zip(extraction, masks, pair["eyes"]):
        save_eye_evidence(mask, report, output / "r1" / row["name"], image)
    pair.update({"source": "ref/user-mode/r1.png", "source_sha256": hashlib.sha256(r1_path.read_bytes()).hexdigest(), "quality": "user_supplied_positive_reference_not_global_quality_certification", "extraction": extraction, "extraction_method": "opaque RGB max <= threshold, seed-connected component; no smoothing, filling, or manual contour edits"})
    _save(output / "r1" / "pair.json", pair)
    candidates = []
    for profile in ("short", "full"):
        path = ROOT / "outputs/fixtures/deepseek/round-002" / (profile + ".svg")
        svg = path.read_text(encoding="utf-8")
        root = review.renderer.validate_svg(svg)
        rendered = Image.open(io.BytesIO(review.renderer.render_svg_text(svg, 1024))).convert("RGBA")
        masks = []
        for name in ("eye-left", "eye-right"):
            # The identifier selects the semantic target only. No tag name,
            # element attributes, or identifier determines its shape verdict.
            expected = review.rgba(review.renderer.render_svg_text(review._eye_markup(root, name, False), 1024))
            masks.append(expected[:, :, 3].astype(float) / 255)
        record = analyze_pair(masks)
        record.update({"source": path.relative_to(ROOT).as_posix(), "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "quality": "rejected_by_user", "method": "rendered primary eye alpha; actual depths/visibility are independently checked by review_gloss_pairs"})
        for name, mask, report in zip(("left", "right"), masks, record["eyes"]):
            save_eye_evidence(mask, report, output / ("old-deepseek-" + profile) / name, rendered)
        _save(output / ("old-deepseek-" + profile) / "pair.json", record)
        candidates.append(record)
    sensitivity = []
    for threshold in (80, 100, 120):
        trial_masks = [extract_dark_roi(image, row["bbox"], row["seed_xy"], threshold) for row in extraction]
        trial = analyze_pair(trial_masks)
        sensitivity.append({"max_channel": threshold, "pair": trial})
        for row, mask in zip(extraction, trial_masks):
            Image.fromarray(np.uint8(mask) * 255).save(output / "r1" / (row["name"] + "-threshold-" + str(threshold) + ".png"))
    all_controls_match = all(row["matches_expected"] for row in controls)
    regressions_match = (all(eye["status"] == "no_rule_failure" for trial in sensitivity for eye in trial["pair"]["eyes"]) and all(eye["status"] == "fail" and "ellipse_explains_contour_better" in eye["issues"] for candidate in candidates for eye in candidate["eyes"]))
    summary = {"schema": "aikon.capsule-study.v1", "status": "pass" if all_controls_match and regressions_match else "fail", "control_suite_pass": all_controls_match and regressions_match, "rules": RULES, "controls": controls, "all_controls_match": all_controls_match, "regression_expectations_match": regressions_match, "r1": pair, "r1_threshold_sensitivity": sensitivity, "old_candidates": candidates, "visual_acceptance": "not_claimed", "reference_similarity_99": "not_assessed", "pitch": "not_assessed"}
    _save(output / "summary.json", summary)
    print(json.dumps({"control_suite_pass": summary["control_suite_pass"], "r1": [x["status"] for x in pair["eyes"]], "old_rejected_candidates": [[x["status"] for x in p["eyes"]] for p in candidates]}))
    return 0 if summary["status"] == "pass" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mask", type=Path, help="Grayscale eye coverage PNG")
    parser.add_argument("--study", action="store_true", help="Run frozen controls, r1, and old DeepSeek")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if bool(args.mask) == args.study:
        parser.error("Choose exactly one of --mask and --study")
    if not args.worker:
        from tools.run_visual_e2e import run_bounded
        try:
            return run_bounded([sys.executable, "-B", str(Path(__file__).resolve()), *sys.argv[1:], "--worker"], timeout=50)
        except subprocess.TimeoutExpired:
            return 124
    if args.study:
        return reference_study(args.output)
    import numpy as np
    from PIL import Image
    with Image.open(args.mask) as image:
        mask = np.asarray(image.convert("L"), dtype=float) / 255
    report = analyze_eye_mask(mask)
    save_eye_evidence(mask, report, args.output)
    print(json.dumps({"status": report["status"], "issues": report["issues"]}))
    return 0 if report["status"] == "no_rule_failure" else 2


if __name__ == "__main__":
    raise SystemExit(main())
