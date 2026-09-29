#!/usr/bin/env python3
"""Bounded same-geometry raster edge diagnostics, not an aesthetic score.

Compare a candidate PNG (or the SVG's native render) with a 4x area-integrated
render of the same SVG. PNG-only input is advisory, never a passing edge gate.
Optional numpy/Pillow/scipy/resvg dependencies are already in requirements-ci.txt.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

for _variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_variable] = "1"

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

try:
    from . import render_svg
except ImportError:
    import render_svg


SCHEMA = "aikon.edge-quality.v1"
MAX_SIZE = 1024
SUPERSAMPLE = 4
# Frozen engineering tolerances, not aesthetic or similarity percentages.
# Positive-only calibration and exact provenance live in edges-v3/README.md.
RULES = {
    "coverage_edge_mae_max_0_255": 8.0,
    "coverage_large_error_min_0_255": 32.0,
    "coverage_large_error_fraction_max": 0.03,
    "color_edge_mae_max_0_255": 8.0,
    "color_large_error_min_0_255": 32.0,
    "color_large_error_fraction_max": 0.03,
    "color_local_bad_pixels_max": 3,
    "interior_alpha_deficit_min_0_255": 3.0,
    "interior_alpha_bad_pixels_max": 3,
    "minimum_edge_samples": 16,
}


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False) + "\n", encoding="utf-8")


def decoded_hash(image):
    image = image.convert("RGBA")
    return hashlib.sha256(f"RGBA:{image.width}x{image.height}:".encode()
                          + image.tobytes()).hexdigest()


def _check_image(image):
    if not isinstance(image, Image.Image):
        raise ValueError("candidate must be a Pillow Image")
    if min(image.size) < 1 or max(image.size) > MAX_SIZE:
        raise ValueError("candidate must fit within 1024 x 1024; no implicit resize")
    return image.convert("RGBA")


def _image(svg, size):
    with Image.open(io.BytesIO(render_svg.render_svg_text(svg, size))) as result:
        result.load()
        return result.convert("RGBA")


def _precise_reference_svg(svg):
    root = render_svg.validate_svg(svg)
    # Rasterization hints are not geometry. The target retains its hints; only
    # this numerical coverage reference requests precise shape integration.
    for element in root.iter():
        element.attrib.pop("shape-rendering", None)
        if "style" in element.attrib:
            element.set("style", ";".join(piece for piece in element.get("style").split(";")
                                           if piece.partition(":")[0].strip().lower() != "shape-rendering"))
    root.set("shape-rendering", "geometricPrecision")
    return ET.tostring(root, encoding="unicode")


def _area_reference(image, size):
    """sRGB-encoded premultiplied area integration; no hidden RGB leakage.

    Match this icon renderer's encoded-sRGB coverage convention, rather than
    claiming physically linear radiometry. Resize alpha and premultiplied color
    separately. Float bands avoid intermediate 8-bit premultiplication error.
    """
    raw = np.asarray(image)
    alpha = raw[:, :, 3].astype(np.float32) / 255.0
    bands = []
    for channel in range(3):
        band = Image.fromarray(raw[:, :, channel] * alpha)
        bands.append(np.asarray(band.resize(size, Image.Resampling.BOX), dtype=np.float32))
    low_alpha = np.asarray(Image.fromarray(alpha).resize(size, Image.Resampling.BOX), dtype=np.float32)
    premult = np.stack(bands, axis=2)
    straight = np.divide(premult, low_alpha[:, :, None], out=np.zeros_like(premult),
                         where=low_alpha[:, :, None] > 1e-7)
    return np.concatenate((straight, low_alpha[:, :, None] * 255.0), axis=2)


def _metric(error, mask, large):
    values = error[mask]
    count = int(values.size)
    return {
        "sample_pixels": count,
        "mae_0_255": float(values.mean()) if count else None,
        "rms_0_255": float(np.sqrt(np.mean(values * values))) if count else None,
        "p95_0_255": float(np.percentile(values, 95)) if count else None,
        "max_0_255": float(values.max()) if count else None,
        "large_error_pixels": int(np.count_nonzero(values > large)),
        "large_error_fraction": float(np.mean(values > large)) if count else None,
        "large_error_threshold_0_255": large,
    }


def _color_clusters(error, mask, threshold=32.0):
    """Descriptive local evidence; join only one-pixel gaps, count original hits."""
    bad = mask & (error > threshold)
    labels, count = ndi.label(ndi.binary_dilation(bad, iterations=1), structure=np.ones((3, 3), bool))
    counts = np.bincount(labels[bad], minlength=count + 1)
    clusters = []
    for label in np.argsort(counts[1:])[::-1][:10] + 1:
        if not counts[label]:
            continue
        yy, xx = np.nonzero((labels == label) & bad)
        clusters.append({"bad_pixels": int(counts[label]), "bbox_pixels": [int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1],
                         "peak_error_0_255": float(error[(labels == label) & bad].max())})
    return {"large_error_threshold_0_255": threshold, "join_gap_pixels": 1,
            "largest_bad_pixel_count": int(counts[1:].max()) if count else 0,
            "top_clusters": clusters}


def analyze_svg_edges(svg_text, candidate=None, size=256, supersample=SUPERSAMPLE):
    """Return (JSON report, image/mask/error maps) for one exact SVG canvas.

    No automatic registration, crop or resizing of the candidate is performed.
    A mismatch may be raster degradation OR different input geometry/paint; the
    report does not infer intent. Only supersample=4 is calibrated and accepted.
    """
    if isinstance(size, bool) or not isinstance(size, int) or not 32 <= size <= MAX_SIZE:
        raise ValueError("size must be an integer between 32 and 1024")
    if isinstance(supersample, bool) or not isinstance(supersample, int) or supersample != SUPERSAMPLE:
        raise ValueError("only the calibrated 4x supersample contract is supported")
    native = _image(svg_text, size)
    supplied = candidate is not None
    candidate = _check_image(candidate) if supplied else native
    if candidate.size != native.size:
        raise ValueError("candidate dimensions must match the SVG canvas at requested size")
    high = _image(_precise_reference_svg(svg_text), size * supersample)
    reference = _area_reference(high, native.size)
    del high
    actual = np.asarray(candidate, dtype=np.float32)
    ca, ra = actual[:, :, 3], reference[:, :, 3]
    alpha_error = np.abs(ca - ra)
    # nearest border handling treats an intentional viewport crop as a crop,
    # not as an unexplained transparent line outside the canvas.
    local_alpha_range = ndi.maximum_filter(ra, 3, mode="nearest") - ndi.minimum_filter(ra, 3, mode="nearest")
    boundary = ndi.binary_dilation((local_alpha_range > 1) | ((ra > 1) & (ra < 254)), iterations=1)
    reference_premult = reference[:, :, :3] * (ra[:, :, None] / 255.)
    actual_premult = actual[:, :, :3] * (ca[:, :, None] / 255.)
    # Include opaque material boundaries so a crisp two-color diagonal cannot
    # evade the diagnostic just because alpha stays 255 everywhere.
    local_color_range = np.max(ndi.maximum_filter(reference_premult, size=(3, 3, 1), mode="nearest")
                               - ndi.minimum_filter(reference_premult, size=(3, 3, 1), mode="nearest"), axis=2)
    material_boundary = ndi.binary_dilation((local_color_range > 24) & (ra >= 254), iterations=1)
    color_boundary = (boundary | material_boundary) & (ra >= 16) & (ca >= 16)
    # Alpha-weighted straight-color residual disentangles contamination from
    # coverage loss. Also report actual composite errors on both backgrounds.
    color_error = np.max(np.abs(actual[:, :, :3] - reference[:, :, :3]), axis=2)
    color_error *= np.minimum(ca, ra) / 255.
    interior = ndi.binary_erosion(ra >= 254, iterations=2, border_value=1)
    alpha_deficit = np.maximum(ra - ca, 0)
    interior_bad = interior & (alpha_deficit > RULES["interior_alpha_deficit_min_0_255"])
    metrics = {
        "coverage": _metric(alpha_error, boundary, RULES["coverage_large_error_min_0_255"]),
        "color": _metric(color_error, color_boundary, RULES["color_large_error_min_0_255"]),
        "local_color": _color_clusters(color_error, color_boundary),
        "interior_alpha": {"sample_pixels": int(interior.sum()), "bad_pixels": int(interior_bad.sum()),
                           "max_deficit_0_255": float(alpha_deficit[interior].max()) if interior.any() else None,
                           "meaning": "deficit against opaque interior of this SVG, not intended-shape validation"},
    }
    composites = {}
    for label, background in (("dark", 24.), ("light", 244.)):
        ac = actual_premult + background * (1 - ca[:, :, None] / 255.)
        rc = reference_premult + background * (1 - ra[:, :, None] / 255.)
        error = np.max(np.abs(ac - rc), axis=2)
        metrics["composite_" + label] = _metric(error, boundary | material_boundary, 32.)
        composites["candidate_" + label] = np.clip(ac, 0, 255).round().astype("uint8")
        composites["reference_" + label] = np.clip(rc, 0, 255).round().astype("uint8")
    issues = []
    for name, code in (("coverage", "edge_coverage_mismatch"), ("color", "edge_color_contamination_or_material_mismatch")):
        metric = metrics[name]
        if metric["sample_pixels"] >= RULES["minimum_edge_samples"]:
            reasons = []
            if metric["mae_0_255"] > RULES[name + "_edge_mae_max_0_255"]:
                reasons.append("mean absolute error exceeds frozen bound")
            if metric["large_error_fraction"] > RULES[name + "_large_error_fraction_max"]:
                reasons.append("fraction of errors above 32/255 exceeds frozen bound")
            if reasons:
                issues.append({"code": code, "reasons": reasons})
    if int(interior_bad.sum()) > RULES["interior_alpha_bad_pixels_max"]:
        issues.append({"code": "unexpected_interior_alpha_deficit", "bad_pixels": int(interior_bad.sum())})
    if metrics["local_color"]["largest_bad_pixel_count"] > RULES["color_local_bad_pixels_max"]:
        issues.append({"code": "local_edge_color_contamination_or_material_mismatch",
                       "largest_bad_pixel_count": metrics["local_color"]["largest_bad_pixel_count"],
                       "reason": "connected visible-color residual above32/255 exceeds3 original bad pixels; one-pixel gaps joined"})
    assessed = [name for name in ("coverage", "color") if metrics[name]["sample_pixels"] >= RULES["minimum_edge_samples"]]
    report = {
        "schema": SCHEMA, "status": "fail" if issues else "no_rule_failure" if assessed else "insufficient_edge_evidence",
        "mode": "same_svg_supersampled_reference", "canvas": list(candidate.size), "supersample": supersample,
        "reference_method": "4x precise SVG render; premultiplied encoded-sRGB BOX area integration",
        "source_sha256": hashlib.sha256(svg_text.encode("utf-8")).hexdigest(),
        "candidate_rgba_sha256": decoded_hash(candidate), "candidate_source": "supplied_png" if supplied else "native_svg_render",
        "native_byte_identity_is_not_a_quality_rule": True, "backend": render_svg.backend_info(),
        "rules": dict(RULES), "rule_provenance": "docs/validation/edges-v3/README.md", "metrics": metrics,
        "validation_scope": {"positive_calibration_long_edges": [128, 256], "prototype_supported_long_edge_range": [32, 1024],
                             "limits_outside_calibration": "API budget is not validation at every size; inspect evidence at the actual export size",
                             "reference_edge_band_pixels": int(boundary.sum()),
                             "fractional_coverage_pixels": int(((ra > 1) & (ra < 254)).sum()),
                             "contour_measure_note": "pixel sample counts, not arc-length estimate; aggregate fraction changes with contour complexity"},
        "assessed_edge_channels": assessed, "issues": issues,
        "limitations": ["Same SVG geometry and paint are assumed, not verified against a character reference.",
                        "Supersampling is a numerical comparator, not an artist-approved ground truth.",
                        "Small/local errors under these aggregate bounds can remain undetected.",
                        "SVG-authored holes, intended jagged geometry, grain and incorrect shape can repeat in both renders.",
                        "No conclusion about character identity, tilt, capsule shape, highlight naturalness or user acceptance."],
        "visual_acceptance": "not_assessed",
    }
    maps = {"candidate": actual.round().astype("uint8"), "reference": np.clip(reference, 0, 255).round().astype("uint8"),
            "coverage_edge_mask": boundary, "material_edge_mask": material_boundary, "color_edge_mask": color_boundary,
            "alpha_error": alpha_error, "color_error": color_error, "interior_alpha_deficit": alpha_deficit * interior,
            "interior_alpha_bad_mask": interior_bad, **composites}
    return report, maps


def run_reference_audit(output_path):
    """Return auditable control results, writing injected images and differences.

    This is a repo-validation API: it uses versioned fixtures under docs, not a
    dependency of the distributed authoring skill. Caller must bound wall time.
    CLI --audit supplies a 45-second worker/process-tree timeout.
    """
    import importlib.util
    path = Path(__file__).resolve().parents[1] / "docs/validation/edges-v3/run_audit.py"
    spec = importlib.util.spec_from_file_location("aikon_edge_reference_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.worker(Path(output_path))
    return json.loads((Path(output_path) / "summary.json").read_text(encoding="utf-8"))


def analyze_png_advisory(image):
    """Describe observable alpha only; no reference means no pass/fail claim."""
    image = _check_image(image)
    alpha = np.asarray(image)[:, :, 3]
    return {"schema": SCHEMA, "status": "advisory_not_verifiable", "mode": "png_without_geometry_reference",
            "canvas": list(image.size), "candidate_rgba_sha256": decoded_hash(image),
            "observable": {"transparent_pixels": int((alpha == 0).sum()), "partial_alpha_pixels": int(((alpha > 0) & (alpha < 255)).sum()),
                           "opaque_pixels": int((alpha == 255).sum())},
            "issues": [], "visual_acceptance": "not_assessed",
            "limitations": ["A hard alpha boundary can be a legal aligned/cropped edge or aliasing; no diagnosis without geometry.",
                            "Partial alpha can be antialiasing or unintended translucency; counts alone cannot decide.",
                            "No absence-of-fringe, noise, aliasing or interior-alpha-defect claim is made."]}


def save_evidence(output_path, report, maps=None):
    output = Path(output_path)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "report.json", report)
    if maps is None:
        return
    for name, array in maps.items():
        if array.dtype == bool:
            pixels = array.astype("uint8") * 255
        elif array.ndim == 2:
            pixels = np.clip(array * 4, 0, 255).round().astype("uint8")
        else:
            pixels = array
        Image.fromarray(pixels).save(output / (name + ".png"))
    # Actual pixels, not a generated illustration; crops use nearest display
    # enlargement deliberately so inspection does not conceal staircase errors.
    panel = min(384, max(report["canvas"]))
    board = Image.new("RGB", (panel * 3, (panel + 28) * 2), "#e9e9e9")
    draw = ImageDraw.Draw(board)
    for row, label in enumerate(("light", "dark")):
        for col, key in enumerate(("candidate_" + label, "reference_" + label, "alpha_error" if row == 0 else "color_error")):
            array = maps[key]
            if array.ndim == 2:
                array = np.clip(array * 4, 0, 255).round().astype("uint8")
            image = Image.fromarray(array).convert("RGB")
            image.thumbnail((panel, panel), Image.Resampling.LANCZOS)
            board.paste(image, (col * panel, row * (panel + 28) + 24))
            draw.text((col * panel + 4, row * (panel + 28) + 4), key + (" x4" if col == 2 else ""), fill="#111111")
    board.save(output / "overview.png")
    energy = maps["alpha_error"] + maps["color_error"]
    y, x = np.unravel_index(int(np.argmax(energy)), energy.shape)
    width, height = report["canvas"]
    left, top = max(0, min(width - 48, int(x) - 24)), max(0, min(height - 48, int(y) - 24))
    box = (left, top, min(width, left + 48), min(height, top + 48))
    crop_board = Image.new("RGB", (384 * 2, 408), "#eeeeee")
    crop_draw = ImageDraw.Draw(crop_board)
    for col, key in enumerate(("candidate_light", "reference_light")):
        sample = Image.fromarray(maps[key]).crop(box).resize((384, 384), Image.Resampling.NEAREST)
        crop_board.paste(sample, (col * 384, 24))
        crop_draw.text((col * 384 + 3, 4), key + " nearest inspection", fill="#111111")
    crop_board.save(output / "worst-edge-crop.png")
    write_json(output / "crop-location.json", {"box_pixels": box, "selection": "maximum alpha-error + visible-color-error", "display": "nearest enlargement only; analysis uses original pixels"})
    clusters = report["metrics"]["local_color"]["top_clusters"]
    if clusters:
        x0, y0, x1, y1 = clusters[0]["bbox_pixels"]
        left = max(0, min(width - 48, (x0 + x1) // 2 - 24))
        top = max(0, min(height - 48, (y0 + y1) // 2 - 24))
        local_box = (left, top, min(width, left + 48), min(height, top + 48))
        local_board = Image.new("RGB", (768, 816), "#eeeeee")
        local_draw = ImageDraw.Draw(local_board)
        for row, background in enumerate(("light", "dark")):
            for col, side in enumerate(("candidate", "reference")):
                key = side + "_" + background
                sample = Image.fromarray(maps[key]).crop(local_box).resize((384, 384), Image.Resampling.NEAREST)
                local_board.paste(sample, (col * 384, row * 408 + 24))
                local_draw.text((col * 384 + 3, row * 408 + 4), key + " local cluster", fill="#111111")
        local_board.save(output / "local-color-cluster-crop.png")
        write_json(output / "local-crop-location.json", {"box_pixels": local_box, "cluster": clusters[0], "selection": "largest count of original bad color pixels, not diluted global mean"})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--svg", type=Path)
    source.add_argument("--png", type=Path, help="PNG-only advisory; never passes the edge gate")
    source.add_argument("--audit", action="store_true", help="write independent positive/negative detector controls")
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--size", type=int, default=256)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not args.svg and args.candidate:
        parser.error("--candidate requires --svg")
    if not args.worker:
        try:
            from .run_visual_e2e import run_bounded
        except ImportError:
            from run_visual_e2e import run_bounded
        try:
            original = list(argv) if argv is not None else sys.argv[1:]
            return run_bounded([sys.executable, "-B", str(Path(__file__).resolve()), *original, "--worker"], timeout=45)
        except subprocess.TimeoutExpired:
            print("Edge diagnostic exceeded 45 seconds; owned worker tree reclaimed", file=sys.stderr)
            return 124
    try:
        if args.audit:
            report = run_reference_audit(args.output)
            print(json.dumps({"status": report["status"], "controls": len(report["records"])}))
            return 0 if report["status"] == "pass" else 2
        if args.png:
            with Image.open(args.png) as image:
                report, maps = analyze_png_advisory(image), None
        else:
            svg = args.svg.read_text(encoding="utf-8-sig")
            if args.candidate:
                with Image.open(args.candidate) as image:
                    report, maps = analyze_svg_edges(svg, image, args.size)
            else:
                report, maps = analyze_svg_edges(svg, size=args.size)
        save_evidence(args.output, report, maps)
        print(json.dumps({"status": report["status"], "issues": report["issues"]}))
        return 2 if report["status"] == "fail" else 3 if report["status"] in {"advisory_not_verifiable", "insufficient_edge_evidence"} else 0
    except (ValueError, OSError, RuntimeError) as error:
        print(json.dumps({"status": "error", "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
