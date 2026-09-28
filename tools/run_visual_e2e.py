#!/usr/bin/env python3
"""Run bounded, offline paint compilation and pixel validation with evidence."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

ROOT = Path(__file__).resolve().parents[1]


class CleanupError(RuntimeError):
    """A timed-out owned process tree could not be confirmed reclaimed."""


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_compiler():
    spec = importlib.util.spec_from_file_location("aikon_paint_compiler", ROOT / "skills/aikon/scripts/paint_svg.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_bounded(command, timeout=50):
    """Wait for our worker and reclaim its whole tree on timeout.

    Windows venv python.exe may be a launcher with an additional Python child;
    killing just that launcher would leave validation running in the background.
    """
    child = subprocess.Popen(command, start_new_session=os.name != "nt")
    try:
        return child.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            try:
                result = subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], timeout=5, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise CleanupError("Could not complete process-tree cleanup for PID " + str(child.pid)) from error
            if result.returncode != 0:
                raise CleanupError("Process-tree cleanup was not confirmed for PID " + str(child.pid))
        else:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            child.wait(timeout=3)
        except subprocess.TimeoutExpired as error:
            raise CleanupError("Owned worker did not exit after cleanup: PID " + str(child.pid)) from error
        raise


def negative_controls(checks, diagnostic, compiler, geometry, plan, svg, output, rules):
    import numpy as np
    from PIL import Image
    from scipy import ndimage as ndi
    output.mkdir(parents=True, exist_ok=True)
    source = '''<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256">
    <defs><linearGradient id="ramp"><stop stop-color="#526270"/><stop offset="1" stop-color="#627280"/></linearGradient></defs>
    <circle cx="128" cy="128" r="108" fill="url(#ramp)"/></svg>'''
    positive = checks.render_image(source, 256)
    arr = np.array(positive)
    mask = arr[:, :, 3] >= 128
    interior = ndi.binary_erosion(mask, iterations=18)
    contract = {"schema": "aikon.paint-fields.v1", "long_edge": 256, "rules": rules, "regions": [{"id": "test-surface", "mask_id": "surface", "expectation": "smooth_field"}]}
    variants = {"legal-gradient-and-AA": arr.copy()}
    grain = arr.copy()
    rng = np.random.default_rng(20260929)
    grain[:, :, :3][interior] = np.clip(grain[:, :, :3][interior].astype(float) + rng.normal(0, 3., (int(interior.sum()), 3)), 0, 255).round().astype("uint8")
    variants["seeded-grain"] = grain
    translucent = arr.copy()
    translucent[115:139, 115:139, 3] = 249
    variants["subtle-interior-alpha"] = translucent
    island = arr.copy()
    island[122:134, 122:134, :3] = np.minimum(island[122:134, 122:134, :3].astype(int) + 32, 255).astype("uint8")
    variants["small-interior-highlight"] = island
    cases = []
    for name, pixels in variants.items():
        image = Image.fromarray(pixels)
        image.save(output / (name + ".png"))
        report, _ = diagnostic.analyze_image(image, contract, region_masks={"surface": mask})
        expected_failure = name != "legal-gradient-and-AA"
        observed_failure = report["status"] == "fail"
        codes = sorted({issue["code"] for issue in report["issues"]})
        required = {"seeded-grain": "grain_above_reference_bound", "subtle-interior-alpha": "translucent_interior", "small-interior-highlight": "unexpected_color_islands_in_declared_smooth_field"}.get(name)
        matched = observed_failure == expected_failure and (not required or required in codes)
        cases.append({"name": name, "expected_failure": expected_failure, "observed_failure": observed_failure, "codes": codes, "expectation_met": matched})
        write_json(output / (name + ".json"), report)
    def expect_rejection(name, callback):
        try:
            callback()
        except (ValueError, compiler.PaintError) as error:
            cases.append({"name": name, "expected_failure": True, "observed_failure": True, "expectation_met": True, "reason": str(error)})
        else:
            cases.append({"name": name, "expected_failure": True, "observed_failure": False, "expectation_met": False})
    import xml.etree.ElementTree as ET
    mutated = ET.fromstring(svg)
    ET.SubElement(mutated, "{" + checks.NS + "}path", {"id": "unplanned-highlight", "d": "M40 40H60V60H40Z", "fill": "#ffffff"})
    expect_rejection("unplanned-highlight-shape", lambda: checks.check_compiled_structure(ET.tostring(mutated), plan))
    noisy = ET.fromstring(svg)
    ET.SubElement(noisy, "{" + checks.NS + "}filter", {"id": "injected-filter"})
    expect_rejection("injected-filter", lambda: checks.check_compiled_structure(ET.tostring(noisy), plan))
    expect_rejection("geometry-source-hash-tamper", lambda: compiler.compile_paint(geometry + b"\n", plan))
    shifted = ET.fromstring(svg)
    shifted.set("viewBox", "1 1 1254 1254")
    expect_rejection("frozen-canvas-tamper", lambda: checks.check_geometry_lock(geometry, ET.tostring(shifted), plan))
    expect_rejection("missing-full-profile", lambda: checks.check_profile_pair({"short": svg}))
    expect_rejection("duplicate-profile-bytes", lambda: checks.check_profile_pair({"short": svg, "full": svg}))
    report = {"cases": cases, "status": "pass" if all(case["expectation_met"] for case in cases) else "fail", "seed": 20260929, "interpretation": "Detection controls, not artistic ratings"}
    write_json(output / "controls.json", report)
    return report


def overview(images, statuses, output):
    from PIL import Image, ImageDraw
    board = Image.new("RGB", (600, 660), "#e6e4e0")
    draw = ImageDraw.Draw(board)
    for row, profile in enumerate(("short", "full")):
        if profile not in images:
            continue
        draw.text((15, row * 330 + 8), profile + " | machine: " + statuses.get(profile, "error"), fill="#222222")
        for column, background in enumerate(("#f4f0eb", "#202128")):
            panel = Image.new("RGBA", (280, 280), background)
            sample = images[profile].resize((280, 280), Image.Resampling.LANCZOS)
            panel.alpha_composite(sample)
            board.paste(panel.convert("RGB"), (10 + column * 300, row * 330 + 30))
        draw.text((15, row * 330 + 312), "visual review and user acceptance: not assessed", fill="#222222")
    board.save(output / "overview.png")


def run_suite(output):
    import numpy as np
    from PIL import Image
    try:
        from . import paint_checks as checks, analyze_paint_fields as diagnostic
        from .reference_paint_regression import run_reference_regression
    except ImportError:
        import paint_checks as checks
        import analyze_paint_fields as diagnostic
        from reference_paint_regression import run_reference_regression
    compiler = load_compiler()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    report = {"schema": "aikon.visual-e2e.v1", "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "runtime": {"python": platform.python_version(), "platform": platform.system(), "pid": os.getpid(), "parent_pid": os.getppid(), "backend": checks.render_svg.backend_info(), "numeric_threads": 1}, "profiles": {}, "status": "running", "highlight_naturalness": "not_automatically_assessed", "visual_review": "not_assessed", "user_acceptance": "not_claimed"}
    write_json(output / "report.json", report)
    fixture = ROOT / "tests/fixtures/paint"
    images, artifacts, plans, statuses = {}, {}, {}, {}
    try:
        report["reference_binding"] = checks.check_reference_binding(ROOT, fixture / "reference-bindings.json")
        geometry = (fixture / "geometry.svg").read_bytes()
        rules = json.loads((ROOT / "docs/validation/paint-fields/frozen-rules.json").read_text(encoding="utf-8"))["rules"]
        for profile in ("short", "full"):
            folder = output / profile
            folder.mkdir(exist_ok=True)
            plan = json.loads((fixture / (profile + ".paint.json")).read_text(encoding="utf-8"))
            if plan["profile"] != profile:
                raise ValueError("Fixture profile label does not match file")
            plans[profile] = plan
            svg, compiled = compiler.compile_paint(geometry, plan)
            duplicate, duplicate_report = compiler.compile_paint(geometry, plan)
            if svg != duplicate or compiled != duplicate_report:
                raise ValueError("Compiler is not deterministic on this source and plan")
            checks.check_geometry_lock(geometry, svg, plan)
            checks.check_compiled_structure(svg, plan)
            artifacts[profile] = svg
            (folder / "icon.svg").write_bytes(svg)
            write_json(folder / "compile.json", compiled)
            for size in (1024, 128, 48, 24):
                image = checks.render_image(svg, size)
                image.save(folder / ("icon-" + str(size) + ".png"))
                if size == 1024:
                    images[profile] = image
            masks = checks.raster_masks(svg, plan, 1024, folder / "layer-masks")
            ownership = checks.ownership_checks(masks, plan, 1024)
            write_json(folder / "ownership.json", ownership)
            contract, visible, exclusions = checks.visible_material_contract(svg, masks, plan, rules)
            for identifier, mask in visible.items():
                Image.fromarray(mask.astype("uint8") * 255).save(folder / "layer-masks" / ("visible-" + identifier + ".png"))
            write_json(folder / "material-coverage.json", exclusions)
            write_json(folder / "pixel-contract.json", contract)
            # The diagnostic API receives full geometry-derived masks, including
            # all visible material interiors and a whole-subject alpha mask.
            pixels, maps = diagnostic.analyze_image(images[profile], contract, region_masks=visible)
            write_json(folder / "pixels.json", pixels)
            for name in ("islands", "interior_alpha", "fringe"):
                Image.fromarray(maps[name].astype("uint8") * 255).save(folder / (name + ".png"))
            status = "fail" if ownership["status"] == "fail" or pixels["status"] == "fail" else "no_rule_failure"
            statuses[profile] = status
            report["profiles"][profile] = {"status": status, "deterministic_export": True, "geometry_unchanged": True, "compile": compiled, "ownership_issues": ownership["issues"], "pixel_issues": pixels["issues"], "pixel_status": pixels["status"], "mask_count": len(masks), "mask_selection": "every selected layer, adjusted for actual painter order", "sizes": [1024, 128, 48, 24]}
            write_json(output / "report.json", report)
            print(json.dumps({"profile": profile, "status": status, "ownership_issues": ownership["issues"], "pixel_issues": pixels["issues"]}), flush=True)
        report["profile_sha256"] = checks.check_profile_pair(artifacts)
        report["controls"] = negative_controls(checks, diagnostic, compiler, geometry, plans["short"], artifacts["short"], output / "controls", rules)
        report["reference_regression"] = run_reference_regression(ROOT, output / "reference-regression")
        report["status"] = "pass" if all(value == "no_rule_failure" for value in statuses.values()) and report["controls"]["status"] == "pass" and report["reference_regression"]["ok"] else "fail"
    except Exception as error:
        report["status"] = "error"
        report["error_type"] = type(error).__name__
        report["error"] = str(error).replace(str(ROOT), "<workspace>")
    finally:
        if images:
            overview(images, statuses, output)
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        write_json(output / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".local/e2e"))
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.worker:
        try:
            return run_bounded([sys.executable, "-B", __file__, "--output", str(args.output), "--worker"])
        except subprocess.TimeoutExpired:
            write_json(args.output / "timeout.json", {"status": "timeout", "worker_limit_seconds": 50, "cleanup_budget_seconds": 8, "visual_review": "not_assessed"})
            print("Visual E2E exceeded 50 seconds; owned process tree reclaimed and partial evidence retained", file=sys.stderr)
            return 124
        except CleanupError as error:
            write_json(args.output / "cleanup-failed.json", {"status": "cleanup_failed", "error": str(error), "process_tree_reclaimed": "not_confirmed", "visual_review": "not_assessed"})
            print(str(error), file=sys.stderr)
            return 125
    report = run_suite(args.output)
    print(json.dumps({"status": report["status"], "elapsed_seconds": report["elapsed_seconds"], "error": report.get("error")}, ensure_ascii=False))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
