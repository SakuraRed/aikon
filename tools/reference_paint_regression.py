#!/usr/bin/env python3
"""Offline regression on real paint references and the user's rejected paint.

run_reference_regression(root, output) returns a report and writes metrics and
the exact masks. It reads frozen rules; it never recalibrates on failed images.
The command-line wrapper enforces its wall-clock limit with one child process.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image


_SPEC = importlib.util.spec_from_file_location("aikon_reference_paint_fields", Path(__file__).with_name("analyze_paint_fields.py"))
_PAINT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PAINT)

FIXTURE_EXPECTATIONS = {
    "r1": "reference_gradients_have_no_local_rule_failure",
    "short-pink": "reference_gradients_have_no_local_rule_failure",
    "short-blue": "reference_gradients_have_no_local_rule_failure",
    "short-black": "reference_gradients_have_no_local_rule_failure",
    "full-teal": "reference_gradients_have_no_local_rule_failure",
    "r2": "reference_gradients_have_no_local_rule_failure",
    "user-defect": "known_short_texture_limitation_with_separate_opacity_failure",
    "full-circled-source": "both_real_circled_fields_fail_frozen_mottle_bound",
}
TEXTURE_CODES = {"grain_above_reference_bound", "mottle_above_reference_bound"}
CIRCLED_FIELDS = {"circled-upper-field", "circled-lower-field"}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_reference_regression(root, output):
    """Run eight real fixtures offline; missing sources or contracts are errors.

    The caller must bound this function's execution (the CLI does so itself).
    A passing regression means expected observations were reproduced; it does
    not make rejected images acceptable or prove general aesthetic accuracy.
    """
    root, output = Path(root).resolve(), Path(output).resolve()
    inputs = root / "docs" / "validation" / "paint-fields"
    manifest_path = inputs / "reference-audit.json"
    frozen_path = inputs / "frozen-rules.json"
    registration_path = inputs / "annotation-registration.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    registration = json.loads(registration_path.read_text(encoding="utf-8"))
    if frozen["rules"]["mottle_rms_max"] != 0.5:
        raise ValueError("real circled regression requires the frozen 0.50 mottle bound; review threshold changes explicitly")
    assets = {asset["id"]: asset for asset in manifest["assets"]}
    if len(assets) != len(manifest["assets"]):
        raise ValueError("duplicate fixture id in reference manifest")
    missing = set(FIXTURE_EXPECTATIONS) - set(assets)
    if missing:
        raise ValueError("missing required real fixtures: " + ", ".join(sorted(missing)))
    if registration["source"] != assets["full-circled-source"]["path"]:
        raise ValueError("circle registration no longer refers to the measured full source")
    output.mkdir(parents=True, exist_ok=True)
    cases = []
    for name, expected in FIXTURE_EXPECTATIONS.items():
        asset = assets[name]
        relative_path = Path(asset["path"])
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError("fixture sources must be repository-relative paths")
        source = root / relative_path
        contract = {"schema": _PAINT.SCHEMA, "long_edge": 1024, "regions": asset["regions"],
                    "rules": frozen["rules"], "threshold_provenance": frozen["formula"]}
        with Image.open(source) as image:
            metrics, maps = _PAINT.analyze_image(image, contract)
        codes = sorted({issue["code"] for issue in metrics["issues"]})
        by_region = {region["id"]: region for region in metrics["regions"]}
        limitations = []
        if name == "full-circled-source":
            matched = CIRCLED_FIELDS <= set(by_region) and all(
                "mottle_above_reference_bound" in by_region[field]["failures"]
                for field in CIRCLED_FIELDS)
            expected_codes = {field: ["mottle_above_reference_bound"] for field in sorted(CIRCLED_FIELDS)}
        elif name == "user-defect":
            matched = not (TEXTURE_CODES & set(codes)) and "translucent_interior" in codes
            expected_codes = {"at_least_one_opaque_region": ["translucent_interior"],
                              "unresolved_texture_codes": []}
            limitations.append("The short image's subtle texture is not reliably separated by the frozen texture bounds. Opacity failure is a separate observation, not a successful texture rejection or visual acceptance.")
        else:
            matched = not metrics["issues"]
            expected_codes = {"all_declared_regions": []}
        case_output = output / name
        case_output.mkdir(exist_ok=True)
        _PAINT.write_json(case_output / "metrics.json", metrics)
        _PAINT.write_json(case_output / "regions-used.json", contract)
        masks = []
        for index, (region_id, mask) in enumerate(maps["regions"].items()):
            filename = f"region-{index:02d}.png"
            Image.fromarray(mask.astype("uint8") * 255).save(case_output / filename)
            masks.append({"region_id": region_id, "path": f"{name}/{filename}", "selected_pixels": int(mask.sum())})
        case = {"id": name, "role": asset["role"], "source": relative_path.as_posix(),
                "source_sha256": _sha(source), "decoded_rgba_sha256": metrics["decoded_rgba_sha256"],
                "source_size": metrics["source_size"], "analysis_size": metrics["analysis_size"],
                "expected_outcome": expected, "expected_codes": expected_codes,
                "actual_codes": codes, "actual_detector_status": metrics["status"],
                "expectation_met": bool(matched), "visual_acceptance": "not_assessed",
                "regions": [{"id": r["id"], **r["geometry"], "expectation": r["expectation"],
                             "actual_codes": r["failures"], "texture": r["texture"],
                             "opacity": r["opacity"], "color_island_count": r["color_islands"]["count"]}
                            for r in metrics["regions"]], "mask_files": masks,
                "metrics_path": f"{name}/metrics.json", "limitations": limitations}
        if name == "full-circled-source":
            case["annotation_registration"] = registration
        cases.append(case)
        del maps
    ok = all(case["expectation_met"] for case in cases)
    report = {"schema": "aikon.real-paint-regression.v1", "ok": ok,
              "status": "passed" if ok else "failed", "visual_acceptance": "not_assessed",
              "meaning_of_pass": "Known real-fixture observations reproduced; rejected paint remains rejected and short texture remains unresolved.",
              "frozen_rules": frozen["rules"], "threshold_provenance": frozen["formula"],
              "input_contract_hashes": {"manifest_sha256": _sha(manifest_path), "frozen_rules_sha256": _sha(frozen_path),
                                        "annotation_registration_sha256": _sha(registration_path)},
              "cases": cases, "failures": [case["id"] for case in cases if not case["expectation_met"]],
              "limitations": ["Manual real-image ROIs provide bounded regression evidence, not whole-image acceptance.",
                              "The short fixture's subtle texture is still not separated at frozen thresholds.",
                              "Color islands alone do not distinguish legal highlights from implausible ones.",
                              "This suite does not prove generalization to arbitrary subjects, generators, scales or renderers."]}
    _PAINT.write_json(output / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=int, default=50)
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
            print("real paint regression exceeded its wall-clock limit", file=sys.stderr)
            return 124
    report = run_reference_regression(args.root, args.output)
    print(json.dumps({"ok": report["ok"], "status": report["status"], "cases": len(report["cases"]),
                      "failures": report["failures"], "report": str(Path(args.output) / "report.json")}))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
