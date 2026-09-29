"""Bounded offline evidence; run each mode separately (no production rerender)."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image, ImageDraw
from tests.test_paint_field_support import scene
from tools import analyze_paint_fields as paint


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def controls(output):
    cases, panels = [], []
    for name, kind, width in (
        ("wide-solid", "solid", 192), ("wide-linear", "linear", 192),
        ("wide-radial", "radial", 192), ("narrow-linear", "linear", 32),
        ("narrow-radial", "radial", 32), ("thin-solid", "solid", 6),
        ("grain", "grain", 192), ("narrow-grain", "grain", 32),
        ("mottle", "mottle", 192), ("island", "island", 192),
        ("alpha", "alpha", 192), ("legal-radial-model-limit", "radial-cone", 192)):
        image, contract, masks = scene(kind, width)
        report, maps = paint.analyze_image(image, contract, masks)
        item = {"id": name, "kind": kind, "width": width,
                "input_sha256": paint.decoded_hash(image),
                "expected_material": "intentional smooth solid/linear/radial" if kind in ("solid", "linear", "radial", "radial-cone") else "injected defect: "+kind,
                "original_issues": report["issues"], "region": report["regions"][0]}
        cases.append(item)
        image.save(output/(name+".png"))
        panel = Image.new("RGB", (256, 286), "#20242d")
        panel.paste(image.convert("RGB"), (0, 30))
        ImageDraw.Draw(panel).text((6, 8), name, fill="white")
        panels.append(panel)
    board = Image.new("RGB", (1024, 858), "#20242d")
    for i, panel in enumerate(panels):
        board.paste(panel, ((i%4)*256, (i//4)*286))
    board.save(output/"controls-board.png")
    neighbors = []
    for color in ((0, 0, 0), (255, 255, 255)):
        image, contract, masks = scene("linear", 64, color)
        report, _ = paint.analyze_image(image, contract, masks)
        region = report["regions"][0]
        neighbors.append({"outside_rgb": color, "legacy_texture": region["texture"],
                          "supported_texture": region["texture_support_evidence"]})
    return {"cases": cases, "neighbor_substitution": neighbors,
            "claims": "Input material intent and injected defects are independent of detector; narrow unsupported scales and legal radial cone remain limitations, not clean certifications."}


def real(mode, output):
    base = ROOT/"outputs/calibration/deepseek-r1"
    geometry_path = base/"geometry-study/v4/geometry.json"
    geometry = json.loads(geometry_path.read_text(encoding="utf-8"))
    contract = json.loads((base/"revisions/v004/quality/paint-contract.json").read_text(encoding="utf-8"))
    masks = {r["id"]: np.asarray(Image.open(geometry_path.parent/r["mask_path"]).convert("L"))>127 for r in geometry["regions"]}
    masks["whole-subject"] = np.asarray(Image.open(geometry_path.parent/"masks/subject-underpaint.png").convert("L"))>127
    relative = ("ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png" if mode == "reference" else "outputs/calibration/deepseek-r1/revisions/v004/comparison/candidate-render.png")
    if mode == "reference" and hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() != "60c234f594ad81319fa74bb4fa8392f10a125127d46bf1d3b47e618b25813da2":
        raise ValueError("Unexpected current clean source bytes; do not substitute the rejected calibration-alpha specimen")
    old_name = "reference-paint-control.json" if mode == "reference" else "paint.json"
    original = json.loads((base/"revisions/v004/quality"/old_name).read_text(encoding="utf-8"))
    image = Image.open(ROOT/relative).convert("RGBA")
    report, maps = paint.analyze_image(image, contract, masks)
    write(output/"metrics.json", report)
    overlay = np.array(maps["normalized"].convert("RGB"))
    # Red is the old quadratic-residual evidence, yellow the declared material
    # boundaries. Neither means the underlying source contains a defect.
    from scipy import ndimage as ndi
    displayed_islands = np.zeros(overlay.shape[:2], dtype=bool)
    for region in report["regions"]:
        if region["expectation"] == "smooth_field" and region["failures"]:
            mask = maps["regions"][region["id"]]
            overlay[mask ^ ndi.binary_erosion(mask)] = [255, 220, 0]
            for component in region["color_islands"]["components"]:
                x0, y0, x1, y1 = [round(v*d) for v, d in zip(component["bbox_normalized"],
                                               [overlay.shape[1], overlay.shape[0]]*2)]
                displayed_islands[y0:y1, x0:x1] |= maps["islands"][y0:y1, x0:x1]
    overlay[displayed_islands] = [255, 0, 70]
    Image.fromarray(overlay).save(output/"contract-islands-overlay.png")
    comparison = []
    for index, region in enumerate(report["regions"]):
        support = region["texture_support_evidence"]
        comparison.append({"id": region["id"], "legacy_failures": region["failures"],
                           "legacy_texture": region["texture"], "support": support})
        if region["failures"]:
            for scale, mask in maps["texture_support"][region["id"]].items():
                Image.fromarray(np.uint8(mask)*255).save(output/f"{index:02d}-{region['id']}-{scale}-support.png")
    return {"source": relative, "source_file_sha256": hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(),
            "source_decoded_hash_matches_previous": report["decoded_rgba_sha256"] == original["decoded_rgba_sha256"],
            "source_binding_note": "Exact current source bytes are bound here; a different previous decoded hash means this is not an exact rerun of that specimen, even when issues match.",
            "legacy_issues_unchanged": report["issues"] == original["issues"],
            "legacy_rules_unchanged": report["rules"] == original["rules"],
            "original_status": report["status"], "visual_acceptance": "not_assessed",
            "regions": comparison}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("controls", "reference", "candidate"), required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if not args.worker:
        from tools.run_visual_e2e import run_bounded
        return run_bounded([sys.executable, "-B", __file__, "--mode", args.mode, "--worker"], timeout=45)
    output = Path(__file__).resolve().parent/args.mode
    output.mkdir(exist_ok=True)
    start = time.monotonic()
    result = controls(output) if args.mode == "controls" else real(args.mode, output)
    result.update({"schema": "aikon.paint-support-audit.v1", "duration_seconds": time.monotonic()-start,
                   "analyzer_sha256": hashlib.sha256((ROOT/"tools/analyze_paint_fields.py").read_bytes()).hexdigest(),
                   "frozen_rules_sha256": hashlib.sha256((ROOT/"docs/validation/paint-fields/frozen-rules.json").read_bytes()).hexdigest()})
    write(output/"report.json", result)
    print(json.dumps({"mode": args.mode, "duration_seconds": result["duration_seconds"], "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
