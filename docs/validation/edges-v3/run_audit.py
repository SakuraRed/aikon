"""Produce reproducible positive/independently injected negative edge evidence.

Run this only after positive-calibration/summary.json has frozen the contract.
No character art is modified. The actual old rejected DeepSeek SVG is read-only.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.run_visual_e2e import run_bounded

REQUIRED_FIXTURES = {"cropped-materials.svg", "curve-gradient.svg", "legal-translucency.svg", "opaque-materials.svg", "sharp-corners.svg"}


def validated_fixtures(folder):
    files = sorted((Path(folder) / "fixtures").glob("*.svg"))
    if {path.name for path in files} != REQUIRED_FIXTURES:
        raise ValueError("Required positive edge fixture coverage is incomplete or changed")
    return files


def worker(output):
    import numpy as np
    from PIL import Image
    from tools import render_svg
    from tools.analyze_edge_quality import analyze_svg_edges, save_evidence, RULES
    folder = Path(__file__).resolve().parent
    fixtures = validated_fixtures(folder)
    output.mkdir(parents=True, exist_ok=True)
    calibration = json.loads((folder / "positive-calibration/summary.json").read_text(encoding="utf-8"))
    if calibration["rules"] != RULES:
        raise ValueError("Rules changed after positive-only freeze; do not silently retune")
    records = []
    def record(name, source, image, expected_code, injection):
        report, maps = analyze_svg_edges(source, image, size=256)
        target = output / name
        save_evidence(target, report, maps)
        codes = [issue["code"] for issue in report["issues"]]
        met = expected_code in codes if expected_code else report["status"] == "no_rule_failure"
        item = {"case": name, "expected_code": expected_code, "observed_codes": codes,
                "status": report["status"], "expectation_met": met, "injection": injection,
                "coverage": report["metrics"]["coverage"], "color": report["metrics"]["color"],
                "interior_alpha": report["metrics"]["interior_alpha"]}
        records.append(item)
        (target / "control.json").write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")
    for fixture in fixtures:
        record("positive-" + fixture.stem, fixture.read_text(encoding="utf-8"), None, None, "none; authored legal geometry/paint")
    source = (folder / "fixtures/curve-gradient.svg").read_text(encoding="utf-8")
    with Image.open(io.BytesIO(render_svg.render_svg_text(source, 256))) as image:
        original = image.convert("RGBA")
    with Image.open(io.BytesIO(render_svg.render_svg_text(source, 64))) as image:
        coarse = image.convert("RGBA").resize((256, 256), Image.Resampling.NEAREST)
    record("negative-nearest-staircase", source, coarse, "edge_coverage_mismatch", "64px native render upscaled to 256px with nearest neighbor")
    raw = np.array(original)
    hard = raw.copy()
    hard[:, :, 3] = np.where(hard[:, :, 3] >= 128, 255, 0).astype("uint8")
    record("negative-threshold-alpha", source, Image.fromarray(hard), "edge_coverage_mismatch", "alpha independently thresholded at128 to remove coverage antialiasing")
    fringe = raw.copy()
    ring = (fringe[:, :, 3] > 16) & (fringe[:, :, 3] < 240)
    fringe[:, :, :3][ring] = (245, 20, 210)
    record("negative-colored-alpha-fringe", source, Image.fromarray(fringe), "edge_color_contamination_or_material_mismatch", "magenta RGB injected only into existing partial-alpha ring; alpha untouched")
    # Local tolerance was fixed from positive-only component counts before this
    # short-arc injection: observed max1; engineering allowance3. Do not retune.
    local_fringe = raw.copy()
    yy, xx = np.nonzero((raw[:, :, 3] >= 96) & (raw[:, :, 3] < 240))
    selected = np.argsort((xx - 110)**2 + (yy - 17)**2)[:16]
    local_fringe[yy[selected], xx[selected], :3] = (245, 20, 210)
    record("negative-local-16px-color-fringe", source, Image.fromarray(local_fringe), "local_edge_color_contamination_or_material_mismatch", "16 existing partial-alpha pixels nearest(110,17) on one edge arc recolored; all alpha and other pixels untouched")
    hole = raw.copy()
    hole[109:139, 109:139, 3] = 239
    record("negative-interior-alpha", source, Image.fromarray(hole), "unexpected_interior_alpha_deficit", "interior alpha changed255->239 in30x30 patch; RGB untouched")
    hidden = raw.copy()
    hidden[:, :, :3][hidden[:, :, 3] == 0] = (255, 0, 255)
    record("positive-hidden-zero-alpha-rgb", source, Image.fromarray(hidden), None, "hidden transparent RGB is not visible contamination")
    material_source = (folder / "fixtures/opaque-materials.svg").read_text(encoding="utf-8")
    with Image.open(io.BytesIO(render_svg.render_svg_text(material_source, 64))) as image:
        material_coarse = image.convert("RGBA").resize((256, 256), Image.Resampling.NEAREST)
    record("negative-opaque-material-staircase", material_source, material_coarse, "edge_color_contamination_or_material_mismatch", "64px opaque two-material render nearest-upscaled; every alpha remains255")
    crisp = source.replace('<path d=', '<path shape-rendering="crispEdges" d=')
    record("negative-svg-crispEdges", crisp, None, "edge_coverage_mismatch", "same path explicitly requests crispEdges at native resolution; reference keeps same geometry and requests precise coverage")
    # This rejected art is a held-out diagnostic, not a quality positive label.
    art = ROOT / "outputs/fixtures/deepseek/round-002/short.svg"
    held_out = None
    if art.exists():
        report, maps = analyze_svg_edges(art.read_text(encoding="utf-8"), size=256)
        save_evidence(output / "held-out-rejected-deepseek", report, maps)
        held_out = {"source": art.relative_to(ROOT).as_posix(), "source_sha256": hashlib.sha256(art.read_bytes()).hexdigest(),
                    "edge_status": report["status"], "user_visual_status": "rejected", "explanation": "edge result cannot reverse rejection of identity, eyes or pose"}
    passed = all(row["expectation_met"] for row in records)
    result = {"schema": "aikon.edge-controls.v1", "status": "pass" if passed else "fail", "control_suite_pass": passed,
              "calibration_precedes_negative_controls": True, "rules": RULES, "records": records,
              "held_out": held_out, "no_artwork_written": True, "visual_acceptance": "not_assessed"}
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if result["status"] == "pass" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        return worker(args.output)
    return run_bounded([sys.executable, "-B", __file__, "--output", str(args.output), "--worker"], timeout=45)


if __name__ == "__main__":
    raise SystemExit(main())
