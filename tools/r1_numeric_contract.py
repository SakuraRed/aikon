#!/usr/bin/env python3
"""Measure the selected R1 B contract; never infer visual/user acceptance.

Only source foreground contributes RGB scores. Transparent-canvas integrity is
separate; preview mattes are never written into the SVG. CLI work is supervised.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.compare_r1_reference import _silhouette, validate_canvas
from tools.render_svg import backend_info, render_svg_text
from tools.source_foreground import exterior_foreground

CONTRACT_PATH = ROOT / "docs/validation/r1-numeric-contract-b.json"
CONTRACT_SHA256 = "609a8cfc7f0febc8fbd5f4812cf31ee6a853be693b52740770fc95e2e90a5f59"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_contract():
    raw = CONTRACT_PATH.read_bytes()
    if digest(raw) != CONTRACT_SHA256:
        raise ValueError("Frozen B contract changed; version and review a replacement explicitly")
    contract = json.loads(raw)
    if contract["schema"] != "aikon.r1-numeric-contract.v1" or contract["selected_option"] != "pixel_hit_b":
        raise ValueError("Unsupported selected contract")
    if contract["background_rgb_in_score"] is not False or contract["output_background"] != "transparent":
        raise ValueError("Background RGB must not enter the score; output must be transparent")
    return contract, digest(raw)


def measure_arrays(reference, candidate, source_subject, regions, contract):
    """Deterministic array seam for independent controls, not SVG provenance.

    Production fixes reference bytes, masks, ROI, canvas and actual SVG render.
    Small arrays are accepted here solely to exercise diagnostic failure modes.
    """
    ref, cand = np.asarray(reference), np.asarray(candidate)
    if ref.dtype != np.uint8 or cand.dtype != np.uint8 or ref.ndim != 3 or ref.shape[-1] != 4 or cand.shape != ref.shape:
        raise ValueError("Matching uint8 RGBA arrays required; no resampling")
    subject = np.asarray(source_subject)
    if subject.dtype != bool or subject.shape != ref.shape[:2] or not subject.any():
        raise ValueError("Nonempty source-only Boolean foreground required")
    if not regions:
        raise ValueError("Critical regions are required")
    masks = {"subject": subject}
    for name, region in regions.items():
        region = np.asarray(region)
        if name == "subject" or region.dtype != bool or region.shape != subject.shape or not (region & subject).any():
            raise ValueError("Every critical ROI must contain source foreground")
        masks[name] = region & subject
    limits = contract["thresholds"]
    # This fixed matte is used only for source-subject AA colors. No background
    # pixel is in a scoring mask, and no artwork byte is modified.
    rgb = []
    for arr in (ref, cand):
        alpha = arr[..., 3:4].astype(np.float64) / 255
        rgb.append(arr[..., :3] * alpha + 15 * (1 - alpha))
    error = np.abs(rgb[0] - rgb[1])
    metrics, checks = {}, []

    def check(name, value, bound, relation):
        valid = value is not None and bool(np.isfinite(value))
        passed = valid and (value <= bound if relation == "max" else value >= bound)
        checks.append({"id": name, "observed": value, "limit": bound, "relation": relation, "passed": bool(passed)})

    for name, mask in masks.items():
        values = error[mask]
        hit = np.max(values, axis=1) <= limits["pixel_max_channel_error_srgb8"]
        metrics[name] = {
            "pixels": int(mask.sum()),
            "mae_srgb8": float(values.mean()),
            "rmse_srgb8": float(np.sqrt(np.mean(values ** 2))),
            "hit_fraction": float(hit.mean()),
            "miss_pixels": int((~hit).sum()),
            "max_channel_tolerance_srgb8": limits["pixel_max_channel_error_srgb8"],
        }
        prefix = "subject" if name == "subject" else "roi"
        for metric in ("mae_srgb8", "rmse_srgb8"):
            check(name + "." + metric, metrics[name][metric], limits[prefix + "_" + metric + "_max"], "max")
        check(name + ".hit_fraction", metrics[name]["hit_fraction"], limits["subject_and_each_roi_hit_fraction_min"], "min")

    silhouette = _silhouette(subject, cand[..., 3] >= 128, np.ones_like(subject))
    check("silhouette.iou", silhouette["iou"], limits["silhouette_iou_min"], "min")
    check("boundary.p95_px", silhouette["boundary"]["symmetric_p95_px"], limits["boundary_p95_px_max"], "max")
    check("boundary.max_px", silhouette["boundary"]["symmetric_max_px"], limits["boundary_max_px_max"], "max")

    # No color constraint on background RGB. Enforce zero alpha clearly outside
    # the allowed subject-boundary tolerance; near edges are handled above and
    # by the existing edge gate, not a competing bespoke antialias threshold.
    margin = int(limits["boundary_max_px_max"])
    outside = ~ndi.binary_dilation(subject, structure=np.ones((3, 3)), iterations=margin)
    if not outside.any():
        raise ValueError("No independent transparent-background evidence")
    leaks = int(np.count_nonzero(cand[..., 3][outside]))
    check("transparent_canvas.nonzero_alpha_outside_subject_margin", leaks, 0, "max")
    return {
        "numeric_status": "pass" if all(c["passed"] for c in checks) else "fail",
        "color_metrics": metrics,
        "checks": checks,
        "silhouette": silhouette,
        "transparency": {"source_boundary_margin_px": margin, "examined_pixels": int(outside.sum()), "nonzero_alpha_pixels": leaks},
        "background_rgb_in_score": False,
        "quality_vetoes": "not_evaluated_here; existing capsule, edge and supported material checks required",
        "visual_acceptance": "not_assessed",
        "user_acceptance": "not_assessed",
        "overall_artwork_acceptance": "not_assessed",
    }


def evaluate_svg(candidate_path, output):
    contract, contract_sha = load_contract()
    reference_raw = (ROOT / contract["reference"]).read_bytes()
    if digest(reference_raw) != contract["reference_sha256"]:
        raise ValueError("Frozen source changed")
    reference = np.asarray(Image.open(io.BytesIO(reference_raw)).convert("RGBA"))
    size = contract["size"]
    if reference.shape != (size, size, 4):
        raise ValueError("Reference dimensions changed")
    subject, _ = exterior_foreground(reference)
    if digest(subject.tobytes()) != contract["source_mask_sha256"]:
        raise ValueError("Frozen source foreground changed")
    regions = {}
    for name, (x0, y0, x1, y1) in contract["regions_xyxy_half_open"].items():
        regions[name] = np.zeros_like(subject)
        regions[name][y0:y1, x0:x1] = True
    raw = Path(candidate_path).read_bytes()
    svg = raw.decode("utf-8-sig")
    validate_canvas(svg, size)
    png = render_svg_text(svg, size)
    candidate = np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"))
    report = measure_arrays(reference, candidate, subject, regions, contract)
    report.update({
        "schema": "aikon.r1-contract-result.v1", "contract_sha256": contract_sha,
        "reference_sha256": digest(reference_raw), "source_mask_sha256": digest(subject.tobytes()),
        "svg_sha256": digest(raw), "render_png_sha256": digest(png), "renderer": backend_info(),
        "alignment": "none", "watermark_exclusion": None,
    })
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use new evidence directory; never overwrite prior reports")
    output.mkdir(parents=True, exist_ok=True)
    (output / "render.png").write_bytes(png)
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = p.parse_args()
    if not args.worker:
        from tools.run_visual_e2e import run_bounded
        try:
            return run_bounded([sys.executable, "-B", str(Path(__file__).resolve()), *sys.argv[1:], "--worker"], timeout=45)
        except subprocess.TimeoutExpired:
            print("R1 contract evaluation exceeded45 seconds; owned worker tree reclaimed", file=sys.stderr)
            return 124
    report = evaluate_svg(args.candidate, args.output)
    print(json.dumps({"numeric_status": report["numeric_status"], "subject": report["color_metrics"]["subject"], "failed_checks": [c for c in report["checks"] if not c["passed"]], "artwork_acceptance": report["overall_artwork_acceptance"]}, ensure_ascii=False))
    return 0 if report["numeric_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
