#!/usr/bin/env python3
"""Fixed-coordinate evidence for the user-provided r1, never an acceptance score.

Dependencies are the repository's existing optional renderer, Pillow, numpy and
scipy. Run via a caller with a hard timeout. No image, SVG or prompt is modified.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

try:
    from .render_svg import backend_info, render_svg_text, validate_svg
except ImportError:
    from render_svg import backend_info, render_svg_text, validate_svg

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA256 = "5a16fe96fab6c06548c87250539739cc4d6dac5e1fed6628f65890a76683817e"
SIZE = 1280
BACKGROUND = (15, 15, 15)
# Coordinates were fixed from r1 alone, before measuring any new candidate.
# xyxy boxes are half-open. This is a withheld damaged observation, not inpainting.
WATERMARK_BOX = (1086, 1198, 1246, 1252)
REGION_BOXES = {
    "face_and_pose_context": (0, 460, 875, 1280),
    "eye_left": (137, 658, 289, 894),
    "eye_right": (571, 813, 716, 1043),
    "main_hair_flow": (0, 220, 1000, 1180),
    "top_hook": (199, 8, 604, 288),
    "head_side_fin": (978, 721, 1265, 1149),
    "side_bow": (960, 718, 1148, 932),
    "white_frill": (0, 126, 1045, 749),
}
PROTOCOL = {
    "schema": "aikon.r1-comparison.v1",
    "reference_sha256": SOURCE_SHA256,
    "reference_size": [SIZE, SIZE],
    "comparison_size": [SIZE, SIZE],
    "composite_background_srgb8": list(BACKGROUND),
    "watermark_box_xyxy_half_open": list(WATERMARK_BOX),
    "regions_xyxy_half_open": {k: list(v) for k, v in REGION_BOXES.items()},
    "subject_mask": "source alpha >=128 and max(abs(source RGB-[15,15,15])) >8",
    "candidate_subject_mask": "rendered alpha >=128",
    "boundary_rule": "8-connected inner boundary; ignore canvas and watermark edges with fixed 2px valid-domain erosion",
    "alignment": "none; SVG canvas declared explicitly; render whole canvas to1280; preserveAspectRatio absent or xMidYMid meet",
    "error_space": "8-bit sRGB composited over #0f0f0f; no gamma-linear or perceptual interpretation",
    "acceptance": "not_assessed; no scalar is equated to user's 99 percent target",
}


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def _box_mask(box):
    mask = np.zeros((SIZE, SIZE), dtype=bool)
    x0, y0, x1, y1 = box
    mask[y0:y1, x0:x1] = True
    return mask


def composite(rgba):
    pixels = np.asarray(rgba)
    if pixels.shape != (SIZE, SIZE, 4) or pixels.dtype != np.uint8:
        raise ValueError("RGBA input must be native 1280x1280 uint8; no silent resampling")
    alpha = pixels[:, :, 3:4].astype(np.float32) / 255
    return pixels[:, :, :3].astype(np.float32) * alpha + np.array(BACKGROUND, dtype=np.float32) * (1 - alpha)


def load_reference(reference_path):
    data = Path(reference_path).read_bytes()
    if sha256(data) != SOURCE_SHA256:
        raise ValueError("Reference hash differs from frozen r1; do not replace calibration ground truth silently")
    image = Image.open(io.BytesIO(data)).convert("RGBA")
    if image.size != (SIZE, SIZE):
        raise ValueError("Frozen reference canvas changed")
    pixels = np.asarray(image)
    valid = ~_box_mask(WATERMARK_BOX)
    distance = np.max(np.abs(pixels[:, :, :3].astype(np.int16) - np.array(BACKGROUND)), axis=2)
    subject = (pixels[:, :, 3] >= 128) & (distance > 8)
    regions = {name: _box_mask(box) & valid for name, box in REGION_BOXES.items()}
    return pixels, {"valid": valid, "subject": subject, "regions": regions}


def _metrics(reference_rgb, candidate_rgb, mask):
    count = int(mask.sum())
    if not count:
        return {"pixels": 0, "status": "empty_region"}
    errors = np.abs(candidate_rgb[mask].astype(np.float64) - reference_rgb[mask].astype(np.float64))
    return {
        "pixels": count,
        "mae_srgb8": float(errors.mean()),
        "rmse_srgb8": float(np.sqrt(np.mean(errors ** 2))),
        "p95_max_channel_error_srgb8": float(np.percentile(errors.max(axis=1), 95)),
        "fraction_pixels_max_channel_error_le_2": float(np.mean(errors.max(axis=1) <= 2)),
        "fraction_pixels_max_channel_error_gt_16": float(np.mean(errors.max(axis=1) > 16)),
    }


def _silhouette(reference_subject, candidate_subject, valid):
    intersection = int((reference_subject & candidate_subject & valid).sum())
    union = int(((reference_subject | candidate_subject) & valid).sum())
    safe = ndi.binary_erosion(valid, iterations=2, border_value=0)
    boundaries = []
    for mask in (reference_subject, candidate_subject):
        boundaries.append((mask & ~ndi.binary_erosion(mask, structure=np.ones((3, 3)), border_value=0)) & safe)
    distances = []
    if all(boundary.any() for boundary in boundaries):
        for a, b in (boundaries, boundaries[::-1]):
            distances.append(ndi.distance_transform_edt(~b)[a])
        joined = np.concatenate(distances)
        boundary = {"status": "measured", "symmetric_mean_px": float(joined.mean()),
                    "symmetric_p95_px": float(np.percentile(joined, 95)), "symmetric_max_px": float(joined.max()),
                    "reference_samples": int(boundaries[0].sum()), "candidate_samples": int(boundaries[1].sum())}
    else:
        boundary = {"status": "missing_boundary", "symmetric_mean_px": None,
                    "symmetric_p95_px": None, "symmetric_max_px": None,
                    "reference_samples": int(boundaries[0].sum()), "candidate_samples": int(boundaries[1].sum())}
    return {"iou": intersection / union if union else None, "intersection_pixels": intersection,
            "union_pixels": union, "false_negative_pixels": int((reference_subject & ~candidate_subject & valid).sum()),
            "false_positive_pixels": int((~reference_subject & candidate_subject & valid).sum()), "boundary": boundary}


def compare_pixels(reference_pixels, candidate_pixels, masks):
    """Measure native RGBA arrays using source-only frozen masks.

    Pixel arrays are the test/measurement seam, not evidence of SVG provenance.
    Production callers must use compare_svg, which renders the actual SVG.
    """
    reference_rgb, candidate_rgb = composite(reference_pixels), composite(candidate_pixels)
    valid, subject = masks["valid"], masks["subject"]
    candidate_subject = candidate_pixels[:, :, 3] >= 128
    alpha = candidate_pixels[:, :, 3].astype(np.float32) / 255
    report = {
        "whole_valid_canvas_context_only": _metrics(reference_rgb, candidate_rgb, valid),
        "subject": _metrics(reference_rgb, candidate_rgb, valid & subject),
        "background": _metrics(reference_rgb, candidate_rgb, valid & ~subject),
        "local_regions": {name: {"context": _metrics(reference_rgb, candidate_rgb, mask),
                                  "subject_only": _metrics(reference_rgb, candidate_rgb, mask & subject)}
                          for name, mask in masks["regions"].items()},
        "silhouette_alpha_proxy": _silhouette(subject, candidate_subject, valid),
        "alpha": {"note": "Reference contains black backdrop; subject alpha is a thresholded source-only proxy, not original ground-truth alpha.",
                  "subject_mean_alpha": float(alpha[valid & subject].mean()),
                  "background_mean_alpha": float(alpha[valid & ~subject].mean()),
                  "background_pixels_alpha_ge_128": int((valid & ~subject & candidate_subject).sum())},
        "acceptance": {"user_99_percent_target": "not_assessed", "visual_acceptance": "not_assessed",
                       "identity_and_pose": "not_semantically_certified"},
    }
    return report


def _number(value):
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Canvas dimensions must be explicit finite unitless numbers") from error
    if not np.isfinite(number):
        raise ValueError("Canvas dimensions must be finite")
    return number


def validate_canvas(svg_text, canvas_size):
    if isinstance(canvas_size, bool) or not isinstance(canvas_size, int) or not 1 <= canvas_size <= 4096:
        raise ValueError("Declared canvas size must be integer 1..4096")
    root = validate_svg(svg_text)
    box = [_number(v) for v in root.get("viewBox", "").replace(",", " ").split()]
    if box != [0, 0, canvas_size, canvas_size]:
        raise ValueError("SVG viewBox must exactly match declared 0 0 N N; no automatic crop or alignment")
    for attribute in ("width", "height"):
        if _number(root.get(attribute)) != canvas_size:
            raise ValueError("SVG width and height must exactly match declared canvas size")
    if root.get("preserveAspectRatio", "xMidYMid meet").strip() != "xMidYMid meet":
        raise ValueError("Only unchanged full-canvas xMidYMid meet projection is allowed")
    return root


def freeze_reference(reference_path, output_dir):
    """Persist protocol and source-only masks; refuses changed existing freezes."""
    reference, masks = load_reference(reference_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    protocol_path = output / "protocol.json"
    encoded = _json_bytes(PROTOCOL)
    if protocol_path.exists() and protocol_path.read_bytes() != encoded:
        raise ValueError("Existing frozen protocol differs; no overwrite")
    protocol_path.write_bytes(encoded)
    for name, mask in (("valid-mask", masks["valid"]), ("subject-mask", masks["subject"]),
                       ("watermark-exclusion-mask", ~masks["valid"])):
        Image.fromarray(mask.astype(np.uint8) * 255).save(output / (name + ".png"))
    preview = Image.fromarray(np.rint(composite(reference)).astype(np.uint8)).convert("RGB")
    draw = ImageDraw.Draw(preview)
    for name, box in REGION_BOXES.items():
        draw.rectangle((box[0], box[1], box[2] - 1, box[3] - 1), outline="#ffbf00", width=2)
        draw.text((box[0] + 3, box[1] + 3), name, fill="#ffffff", stroke_width=2, stroke_fill="#000000")
    box = WATERMARK_BOX
    draw.rectangle((box[0], box[1], box[2] - 1, box[3] - 1), outline="#ff3030", width=3)
    preview.save(output / "frozen-regions.png")
    Image.fromarray(reference).crop((1065, 1175, 1265, 1272)).resize((800, 388)).save(output / "watermark-inspection.png")
    return {"protocol_sha256": sha256(encoded), "reference_sha256": SOURCE_SHA256,
            "excluded_pixels": int((~masks["valid"]).sum()), "excluded_fraction": float((~masks["valid"]).mean()),
            "subject_mask_sha256": sha256(masks["subject"].tobytes()),
            "valid_mask_sha256": sha256(masks["valid"].tobytes())}


def compare_svg(reference_path, candidate_path, output_dir, *, canvas_size):
    """Render actual SVG to 1280px and save measurements, alpha, diff and overlay."""
    reference, masks = load_reference(reference_path)
    candidate_path = Path(candidate_path)
    source = candidate_path.read_bytes()
    text = source.decode("utf-8-sig")
    validate_canvas(text, canvas_size)
    output = Path(output_dir)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Comparison output must be new or empty; retain prior evidence")
    output.mkdir(parents=True, exist_ok=True)
    png = render_svg_text(text, size=SIZE)
    candidate = np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"))
    report = compare_pixels(reference, candidate, masks)
    report.update({"schema": "aikon.r1-comparison-result.v1", "protocol": PROTOCOL,
                   "protocol_sha256": sha256(_json_bytes(PROTOCOL)), "reference_sha256": SOURCE_SHA256,
                   "candidate_svg_sha256": sha256(source), "render_png_sha256": sha256(png),
                   "candidate_declared_canvas_size": canvas_size, "render_size": [SIZE, SIZE],
                   "backend": backend_info(), "excluded_pixels": int((~masks["valid"]).sum()),
                   "subject_mask_sha256": sha256(masks["subject"].tobytes()),
                   "valid_mask_sha256": sha256(masks["valid"].tobytes())})
    (output / "candidate-render.png").write_bytes(png)
    ref_rgb, candidate_rgb = composite(reference), composite(candidate)
    valid = masks["valid"]
    diff = np.abs(candidate_rgb - ref_rgb)
    diff[~valid] = 0
    Image.fromarray(np.rint(diff).astype(np.uint8)).save(output / "diff-absolute-srgb8.png")
    amplified = np.clip(diff * 4, 0, 255)
    Image.fromarray(np.rint(amplified).astype(np.uint8)).save(output / "diff-x4.png")
    overlay = (ref_rgb + candidate_rgb) * .5
    overlay[~valid] = BACKGROUND
    Image.fromarray(np.rint(overlay).astype(np.uint8)).save(output / "overlay-half.png")
    Image.fromarray(candidate[:, :, 3]).save(output / "candidate-alpha.png")
    reference_view = ref_rgb.copy()
    reference_view[~valid] = BACKGROUND
    candidate_view = candidate_rgb.copy()
    candidate_view[~valid] = BACKGROUND
    board = Image.new("RGB", (SIZE * 3, SIZE), BACKGROUND)
    for index, pixels in enumerate((reference_view, candidate_view, amplified)):
        board.paste(Image.fromarray(np.rint(pixels).astype(np.uint8)), (SIZE * index, 0))
    board.resize((1920, 640), Image.Resampling.LANCZOS).save(output / "comparison-board.png")
    (output / "report.json").write_bytes(_json_bytes(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=ROOT / "ref/user-mode/r1.png")
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--canvas-size", type=int)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        if args.candidate is not None or args.canvas_size is not None:
            parser.error("Freeze accepts only reference and output, never a candidate")
        report = freeze_reference(args.reference, args.output)
    else:
        if args.candidate is None or args.canvas_size is None:
            parser.error("Comparison requires --candidate and explicit --canvas-size")
        report = compare_svg(args.reference, args.candidate, args.output, canvas_size=args.canvas_size)
        report = {"subject": report["subject"], "silhouette_alpha_proxy": report["silhouette_alpha_proxy"],
                  "acceptance": report["acceptance"], "output": str(args.output)}
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
