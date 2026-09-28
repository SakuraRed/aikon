#!/usr/bin/env python3
"""Write a compact, offline CI evidence manifest when artifact upload fails.

stdout is one AIKON_EVIDENCE JSON line. Hashes describe files actually read;
they do not replace visual review. The CLI supervises a bounded worker.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sys


SIZES = (1024, 128, 48, 24)
PROFILES = ("short", "full")
UPLOAD_OUTCOMES = ("success", "failure", "cancelled", "skipped", "not_attempted", "unknown")


def read_limited(path, limit):
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("file exceeds evidence size budget")
    return data


def case_counts(section):
    if not isinstance(section, dict) or not isinstance(section.get("cases"), list):
        return {"status": "not_recorded", "count": None, "expectations_met": None}
    cases = section["cases"]
    return {"status": section.get("status"), "count": len(cases), "expectations_met": sum(isinstance(case, dict) and case.get("expectation_met") is True for case in cases)}


def build_manifest(directory, artifact_upload_outcome="unknown"):
    if artifact_upload_outcome not in UPLOAD_OUTCOMES:
        raise ValueError("Unknown artifact upload outcome")
    directory = Path(directory)
    manifest = {
        "schema": "aikon.ci-evidence.v1", "status": None,
        "report_file_status": "missing", "report_sha256": None,
        "artifact_upload_outcome": artifact_upload_outcome,
        "decoded_hash_format": "sha256(UTF-8('RGBA:{width}x{height}:') + decoded RGBA bytes)",
        "visual_review": "not_claimed", "user_acceptance": "not_claimed",
        "profiles": {}, "issues": [],
    }
    def issue(file, code):
        manifest["issues"].append({"file": file, "code": code})
    report = {}
    try:
        raw = read_limited(directory / "report.json", 2_000_000)
        manifest["report_sha256"] = hashlib.sha256(raw).hexdigest()
        report = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON constant")))
        if not isinstance(report, dict) or report.get("schema") != "aikon.visual-e2e.v1":
            raise ValueError("Unsupported E2E report")
        manifest["report_file_status"] = "read"
        manifest["status"] = report.get("status")
    except FileNotFoundError:
        issue("report.json", "missing_report")
    except (OSError, ValueError, UnicodeError):
        manifest["report_file_status"] = "invalid"
        issue("report.json", "invalid_report")
        report = {}
    manifest["controls"] = case_counts(report.get("controls"))
    manifest["real_references"] = case_counts(report.get("reference_regression"))
    runtime = report.get("runtime", {})
    manifest["runtime"] = {key: runtime.get(key) for key in ("python", "platform", "backend")} if isinstance(runtime, dict) else {}
    manifest["reported_claims"] = {key: report.get(key) for key in ("visual_review", "user_acceptance", "highlight_naturalness")}
    reported_profiles = report.get("profiles", {})
    if not isinstance(reported_profiles, dict):
        reported_profiles = {}
    reported_hashes = report.get("profile_sha256", {})
    if not isinstance(reported_hashes, dict):
        reported_hashes = {}
    for profile in PROFILES:
        profile_report = reported_profiles.get(profile, {})
        if not isinstance(profile_report, dict):
            profile_report = {}
        evidence = {"reported_status": profile_report.get("status"), "svg": {}, "pngs": {}}
        manifest["profiles"][profile] = evidence
        relative_svg = profile + "/icon.svg"
        svg = {"path": relative_svg, "status": "missing"}
        evidence["svg"] = svg
        try:
            data = read_limited(directory / relative_svg, 4_000_000)
            svg.update(status="read", byte_length=len(data), sha256=hashlib.sha256(data).hexdigest())
            if not data.strip():
                raise ValueError("Empty SVG")
            expected = reported_hashes.get(profile)
            compile_report = profile_report.get("compile", {})
            compile_hash = compile_report.get("svg_sha256") if isinstance(compile_report, dict) else None
            if any(value is not None and value != svg["sha256"] for value in (expected, compile_hash)):
                svg["status"] = "hash_mismatch"
                issue(relative_svg, "svg_differs_from_report")
            elif manifest["status"] == "pass" and not (expected or compile_hash):
                issue(relative_svg, "missing_reported_svg_hash")
        except FileNotFoundError:
            issue(relative_svg, "missing_svg")
        except (OSError, ValueError):
            svg["status"] = "invalid"
            issue(relative_svg, "invalid_svg")
        for size in SIZES:
            relative_png = profile + "/icon-" + str(size) + ".png"
            png = {"path": relative_png, "status": "missing"}
            evidence["pngs"][str(size)] = png
            try:
                raw_png = read_limited(directory / relative_png, 16_000_000)
                png.update(byte_length=len(raw_png), png_sha256=hashlib.sha256(raw_png).hexdigest())
                from PIL import Image
                with Image.open(io.BytesIO(raw_png)) as image:
                    if image.format != "PNG" or image.size != (size, size) or getattr(image, "n_frames", 1) != 1:
                        raise ValueError("PNG format or dimensions differ from expected profile size")
                    image.verify()
                with Image.open(io.BytesIO(raw_png)) as image:
                    rgba = image.convert("RGBA")
                    rgba.load()
                    prefix = f"RGBA:{rgba.width}x{rgba.height}:".encode("utf-8")
                    png.update(status="decoded", width=rgba.width, height=rgba.height,
                               source_mode=image.mode,
                               decoded_rgba_sha256=hashlib.sha256(prefix + rgba.tobytes()).hexdigest())
            except FileNotFoundError:
                issue(relative_png, "missing_png")
            except Exception:
                # Decoder errors, including oversized image headers, must keep
                # the manifest printable and cannot become successful evidence.
                png["status"] = "invalid"
                issue(relative_png, "invalid_or_undecodable_png")
    manifest["evidence_complete"] = manifest["report_file_status"] == "read" and not manifest["issues"]
    return manifest


def step_summary(manifest):
    def safe(value):
        return str(value).replace("`", "\\`").replace("\r", " ").replace("\n", " ").replace("|", "\\|")
    lines = ["### Aikon evidence", "",
             "Reported E2E status: `" + safe(manifest["status"]) + "`. Evidence complete: `" + str(manifest["evidence_complete"]).lower() + "`.",
             "Artifact upload outcome: `" + safe(manifest["artifact_upload_outcome"]) + "`. Visual review and user acceptance: **not claimed**.",
             "", "| Evidence | Count | Expectations met |", "| --- | ---: | ---: |"]
    for key in ("real_references", "controls"):
        counts = manifest[key]
        lines.append("| " + key + " | " + safe(counts["count"]) + " | " + safe(counts["expectations_met"]) + " |")
    lines.extend(["", "| File | Byte SHA-256 | Decoded RGBA SHA-256 |", "| --- | --- | --- |"])
    for profile in PROFILES:
        evidence = manifest["profiles"][profile]
        for file in [evidence["svg"], *evidence["pngs"].values()]:
            lines.append("| " + file["path"] + " | " + file.get("png_sha256", file.get("sha256", "unavailable")) + " | " + file.get("decoded_rgba_sha256", "not applicable" if file is evidence["svg"] else "unavailable") + " |")
    if manifest["issues"]:
        lines.extend(["", "Evidence issues:", ""])
        lines.extend("- `" + issue["file"] + "`: `" + issue["code"] + "`" for issue in manifest["issues"])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(".local/e2e"))
    parser.add_argument("--artifact-upload-outcome", choices=UPLOAD_OUTCOMES, default="unknown")
    parser.add_argument("--summary", type=Path, help="Overrides GITHUB_STEP_SUMMARY when provided")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not args.worker:
        try:
            from .run_visual_e2e import run_bounded
        except ImportError:
            from run_visual_e2e import run_bounded
        command = [sys.executable, "-B", __file__, "--input", str(args.input), "--artifact-upload-outcome", args.artifact_upload_outcome, "--worker"]
        if args.summary:
            command.extend(["--summary", str(args.summary)])
        return run_bounded(command, timeout=20)
    manifest = build_manifest(args.input, args.artifact_upload_outcome)
    summary = args.summary or (Path(os.environ["GITHUB_STEP_SUMMARY"]) if os.environ.get("GITHUB_STEP_SUMMARY") else None)
    if summary:
        try:
            protected = {str((args.input / "report.json").resolve())}
            protected.update(str((args.input / file["path"]).resolve()) for profile in manifest["profiles"].values() for file in [profile["svg"], *profile["pngs"].values()])
            if str(summary.resolve()) in protected:
                raise ValueError("Summary path would overwrite an input artifact")
            with summary.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(step_summary(manifest))
        except (OSError, ValueError):
            manifest["issues"].append({"file": "step-summary", "code": "summary_write_failed"})
            manifest["evidence_complete"] = False
    print("AIKON_EVIDENCE " + json.dumps(manifest, ensure_ascii=True, separators=(",", ":"), allow_nan=False), flush=True)
    return 0 if manifest["status"] == "pass" and manifest["evidence_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
