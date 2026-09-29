#!/usr/bin/env python3
"""Run focused image-quality controls; never promote rejected artwork.

Each worker has a 50-second process-tree deadline. CI runs test and audit
workers separately, preserving evidence even if the first worker fails.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"

QUALITY_TESTS = (
    "test_render_svg.py",
    "test_paint_fields.py",
    "test_gloss_pairs.py",
    "test_capsule_geometry.py",
    "test_edge_quality.py",
    "test_quality_runner.py",
)

EXPECTED_ARTWORKS = {(subject, profile) for subject in ("deepseek", "endministrator-female", "endministrator-male") for profile in ("short", "full")}


def execution_context():
    """Bind results to the actual inputs, including uncommitted local changes."""
    patterns = ["tools/*.py", "tests/*.py", "tests/fixtures/paint/*", "skills/aikon/scripts/*.py", "requirements-ci.txt", "ref/user-mode/r1.png", "ref/user-mode/r2.png", "ref/site/*.png", "ref/feedback/2026-09-29/accepted-composition-defective-paint.png", "outputs/calibration/illustration/full-imagegen-v1.png", "outputs/fixtures/*/round-002/*.svg", "docs/validation/paint-fields/reference-audit.json", "docs/validation/paint-fields/frozen-rules.json", "docs/validation/paint-fields/annotation-registration.json", "docs/validation/edges-v3/run_audit.py", "docs/validation/quality-v3/artwork-verdicts.json"]
    patterns += ["docs/validation/edges-v3/fixtures/*.svg", "docs/validation/edges-v3/positive-calibration/summary.json"]
    files = sorted({path for pattern in patterns for path in ROOT.glob(pattern) if path.is_file()})
    records = [(path.relative_to(ROOT).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()) for path in files]
    fingerprint = hashlib.sha256(json.dumps(records, separators=(",", ":")).encode()).hexdigest()
    return {"input_sha256": fingerprint, "github_run_id": os.environ.get("GITHUB_RUN_ID"), "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"), "github_sha": os.environ.get("GITHUB_SHA")}


def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def rejected_artwork_records(root=ROOT):
    root = Path(root)
    path = root / "docs/validation/quality-v3/artwork-verdicts.json"
    ledger = json.loads(path.read_text(encoding="utf-8"))
    if ledger.get("schema") != "aikon.artwork-verdicts.v1" or len(ledger.get("artworks", [])) != 6:
        raise ValueError("Expected the six explicit rejected round-002 records")
    found = set()
    records = []
    for record in ledger["artworks"]:
        relative = Path(record["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Verdict source must remain inside the repository")
        key = (record["subject"], record["profile"])
        expected_path = "outputs/fixtures/" + record["subject"] + "/round-002/" + record["profile"] + ".svg"
        if key not in EXPECTED_ARTWORKS or relative.as_posix() != expected_path:
            raise ValueError("Verdict does not identify its canonical subject/profile artifact")
        if key in found or record["user_verdict"] != "rejected":
            raise ValueError("Duplicate or silently promoted human verdict")
        found.add(key)
        digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        if digest != record["sha256"]:
            raise ValueError("Rejected historical artwork changed; create a new revision instead")
        records.append({"subject": record["subject"], "profile": record["profile"], "source": relative.as_posix(), "sha256": digest, "user_verdict": "rejected"})
    if found != EXPECTED_ARTWORKS:
        raise ValueError("Human verdict ledger must cover exactly three subjects times two profiles")
    return records


def begin_stage(output, mode, context):
    invocation = uuid.uuid4().hex
    save(output / (mode + ".json"), {"status": "running", "context": context, "invocation": invocation})
    return invocation


def execute_stage(output, mode, invocation, context):
    """Any early import/load error invalidates prior pass evidence."""
    try:
        rc = run_tests(output) if mode == "tests" else run_audit(output)
        report = json.loads((output / (mode + ".json")).read_text(encoding="utf-8"))
        if execution_context() != context:
            raise ValueError("Quality inputs changed during the stage")
    except Exception as error:
        report = {"status": "error", "error": type(error).__name__ + ": " + str(error)}
        rc = 1
    report.update({"context": context, "invocation": invocation})
    save(output / (mode + ".json"), report)
    prefix = "AIKON_QUALITY_TESTS " if mode == "tests" else "AIKON_IMAGE_QUALITY "
    print(prefix + json.dumps(report, ensure_ascii=True, separators=(",", ":")))
    return rc


def run_tests(output):
    output.mkdir(parents=True, exist_ok=True)
    suite = unittest.TestSuite()
    selected = {}
    for pattern in QUALITY_TESTS:
        current = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern=pattern)
        selected[pattern] = current.countTestCases()
        if not selected[pattern]:
            raise ValueError("Missing image-quality test module: " + pattern)
        suite.addTests(current)
    start = time.monotonic()
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log = stream.getvalue()
    (output / "tests.log").write_text(log, encoding="utf-8")
    # Missing optional image dependencies are a failure in the quality CI, not
    # evidence that the unexecuted raster checks passed.
    report = {"schema": "aikon.quality-tests.v1", "status": "pass" if result.wasSuccessful() and not result.skipped else "fail", "selected_modules": selected, "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped), "elapsed_seconds": round(time.monotonic() - start, 3), "meaning": "quality-detector test results, not artwork acceptance"}
    save(output / "tests.json", report)
    print(log[-2000:])
    return 0 if report["status"] == "pass" else 1


def run_audit(output):
    from tools.analyze_capsule_geometry import reference_study
    from tools.analyze_edge_quality import run_reference_audit
    from tools.reference_paint_regression import run_reference_regression
    from tools.render_svg import backend_info
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    report = {"schema": "aikon.image-quality-audit.v1", "status": "running", "artwork_acceptance": "rejected_by_user", "reference_similarity_99": "not_assessed", "pitch_and_identity": "not_assessed", "gates": {}, "backend": backend_info()}
    save(output / "audit.json", report)
    try:
        report["artworks"] = rejected_artwork_records()
        capsule_rc = reference_study(output / "capsules")
        capsules = json.loads((output / "capsules/summary.json").read_text(encoding="utf-8"))
        report["gates"]["capsules"] = {"controls_pass": capsule_rc == 0 and capsules["control_suite_pass"], "r1_eye_status": [r["status"] for r in capsules["r1"]["eyes"]], "rejected_deepseek_eye_status": [[r["status"] for r in candidate["eyes"]] for candidate in capsules["old_candidates"]], "evidence": "capsules/summary.json"}
        edges = run_reference_audit(output / "edges")
        report["gates"]["edges"] = {"controls_pass": edges["control_suite_pass"], "evidence": "edges/summary.json"}
        paint = run_reference_regression(ROOT, output / "paint-references")
        report["gates"]["paint"] = {"controls_pass": paint["ok"], "real_reference_count": len(paint["cases"]), "limitations": paint["limitations"], "evidence": "paint-references/report.json"}
        report["status"] = "pass" if all(gate["controls_pass"] for gate in report["gates"].values()) else "fail"
    except Exception as error:
        report["status"] = "error"
        report["error"] = type(error).__name__ + ": " + str(error).replace(str(ROOT), "<workspace>")
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["meaning"] = "Pass means positive/negative detector observations matched expectations. All six artwork verdicts remain rejected."
    save(output / "audit.json", report)
    return 0 if report["status"] == "pass" else 1


def publish_summary(output, upload_outcome):
    records = {}
    current = execution_context()
    for name in ("tests", "audit"):
        path = output / (name + ".json")
        try:
            records[name] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            records[name] = {"status": "missing_or_invalid"}
        if records[name].get("context") != current or not records[name].get("invocation"):
            records[name] = {"status": "stale_or_unbound"}
        failure = output / (name + "-supervision-failed.json")
        if failure.exists():
            try:
                failed = json.loads(failure.read_text(encoding="utf-8"))
                if failed.get("invocation") == records[name].get("invocation"):
                    records[name]["status"] = "supervision_failed"
            except (OSError, ValueError):
                records[name]["status"] = "invalid_supervision_record"
    complete = all(row.get("status") == "pass" for row in records.values())
    result = {"schema": "aikon.quality-ci-summary.v1", "gate_validation": "pass" if complete else "fail", "stage_status": {key: value.get("status") for key, value in records.items()}, "context": current, "tests_run": records["tests"].get("tests_run"), "gates": records["audit"].get("gates", {}), "artwork_acceptance": records["audit"].get("artwork_acceptance", "not_claimed"), "reference_similarity_99": "not_assessed", "artifact_upload": upload_outcome}
    save(output / "ci-summary.json", result)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8", newline="\n") as stream:
            stream.write("### Image-quality gate evidence\n\nOne fixed Ubuntu environment.\n\n")
            stream.write("- Gate validation: `" + result["gate_validation"] + "`\n")
            stream.write("- Artwork verdicts: `" + result["artwork_acceptance"] + "`\n")
            stream.write("- 99% likeness / head-up pose / identity acceptance: **not established**\n")
            stream.write("- Artifact upload: `" + upload_outcome + "`\n\n")
            stream.write("Detailed evidence is also printed as AIKON_IMAGE_QUALITY in the audit log. Detector-test success does not accept the six rejected drawings.\n")
    print("AIKON_QUALITY_SUMMARY " + json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return 0 if complete else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("tests", "audit", "summary"))
    parser.add_argument("--output", type=Path, default=Path(".local/quality"))
    parser.add_argument("--artifact-outcome", choices=("success", "failure", "skipped", "cancelled", "not_attempted"), default="not_attempted")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--invocation", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.worker:
        from tools.run_visual_e2e import run_bounded
        context = execution_context()
        invocation = begin_stage(args.output, args.mode, context) if args.mode != "summary" else uuid.uuid4().hex
        try:
            return run_bounded([sys.executable, "-B", __file__, "--worker", "--mode", args.mode, "--output", str(args.output), "--artifact-outcome", args.artifact_outcome, "--invocation", invocation], timeout=50)
        except Exception as error:
            save(args.output / (args.mode + "-supervision-failed.json"), {"status": "fail", "error": str(error), "artwork_acceptance": "not_claimed", "context": context, "invocation": invocation})
            return 2
    args.output.mkdir(parents=True, exist_ok=True)
    if args.mode != "summary":
        pending = json.loads((args.output / (args.mode + ".json")).read_text(encoding="utf-8"))
        if pending.get("invocation") != args.invocation or pending.get("status") != "running":
            raise ValueError("Worker does not match an active stage")
        return execute_stage(args.output, args.mode, args.invocation, pending["context"])
    return publish_summary(args.output, args.artifact_outcome)


if __name__ == "__main__":
    raise SystemExit(main())
