"""Integration checks for complete-mask coverage and diagnostic sensitivity."""
import hashlib
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import subprocess
import time
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OPTIONAL = all(importlib.util.find_spec(module) is not None for module in ("resvg_py", "PIL", "numpy", "scipy"))
sys.path.insert(0, str(ROOT))
if OPTIONAL:
    from tools import paint_checks as checks
    from tools import run_visual_e2e as e2e
    from tools import analyze_paint_fields as diagnostic
    import numpy as np


@unittest.skipUnless(OPTIONAL, "install optional requirements-ci.txt for visual E2E tests")
class VisualContractTests(unittest.TestCase):
    def test_failed_cleanup_is_not_reported_as_successful_timeout_recovery(self):
        worker = mock.Mock(pid=98765)
        worker.wait.side_effect = subprocess.TimeoutExpired(["worker"], 0.1)
        with mock.patch.object(e2e.subprocess, "Popen", return_value=worker), mock.patch.object(e2e.os, "name", "nt"), mock.patch.object(e2e.subprocess, "run", return_value=mock.Mock(returncode=1)):
            with self.assertRaises(e2e.CleanupError):
                e2e.run_bounded(["worker"], timeout=0.1)

    def test_geometry_gate_freezes_existing_clips_but_allows_receiver_wrapper(self):
        compiler = e2e.load_compiler()
        source = b'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">
        <defs><clipPath id="border"><rect width="40" height="40"/></clipPath></defs>
        <g id="original-parent" clip-path="url(#border)">
          <rect id="face" width="50" height="50"/>
          <ellipse id="cheek" cx="35" cy="30" rx="10" ry="5" transform="rotate(20 35 30)"/>
        </g></svg>'''
        plan = {"schema": "aikon.paint-plan.v1", "profile": "short", "geometry_sha256": hashlib.sha256(source).hexdigest(), "layers": [
            {"id": "face", "role": "surface", "paint": {"type": "solid", "color": "#d8c8b8"}},
            {"id": "cheek", "role": "blush", "owner": "face", "paint": {"type": "solid", "color": "#d89090"}},
        ]}
        output, _ = compiler.compile_paint(source, plan)
        checks.check_geometry_lock(source, output, plan)
        output_tree = ET.fromstring(output)
        self.assertIsNotNone(output_tree.find(".//*[@id='paint-ownership-cheek']"))
        smaller_clip = copy.deepcopy(output_tree)
        smaller_clip.find(".//*[@id='border']/{" + checks.NS + "}rect").set("width", "10")
        smaller_bytes = ET.tostring(smaller_clip)
        self.assertEqual(checks.render_image(output, 64).getpixel((30, 30))[3], 255)
        self.assertEqual(checks.render_image(smaller_bytes, 64).getpixel((30, 30))[3], 0)
        no_ancestor_clip = copy.deepcopy(output_tree)
        no_ancestor_clip.find(".//*[@id='original-parent']").set("clip-path", "none")
        for mutated in (smaller_clip, no_ancestor_clip):
            with self.subTest(change=ET.tostring(mutated)), self.assertRaises(ValueError):
                checks.check_geometry_lock(source, ET.tostring(mutated), plan)

    def test_linear_field_gate_rejects_real_output_color_coordinate_and_alpha_tampering(self):
        compiler = e2e.load_compiler()
        source = b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><g id="parent"><rect id="face" width="64" height="64"/></g></svg>'
        plan = {"schema": "aikon.paint-plan.v1", "profile": "short", "geometry_sha256": hashlib.sha256(source).hexdigest(), "layers": [{"id": "face", "role": "surface", "paint": {"type": "linear", "from": [0, 0], "to": [64, 0], "colors": ["#555555", "#666666"]}}]}
        output, _ = compiler.compile_paint(source, plan)
        checks.check_compiled_structure(output, plan)
        changes = [
            ("stop", "stop-color", "#ff0000"), ("stop", "offset", "0.25"),
            ("stop", "stop-opacity", "0.7"), ("gradient", "x2", "12"),
            ("gradient", "gradientUnits", "objectBoundingBox"),
            ("gradient", "gradientTransform", "rotate(90)"),
            ("gradient", "spreadMethod", "repeat"),
            ("parent", "opacity", "0.5"),
            ("face", "style", "fill:#ff0000"),
        ]
        for target, attribute, value in changes:
            mutated = ET.fromstring(output)
            if target == "stop":
                node = mutated.find(".//{" + checks.NS + "}stop")
            elif target == "gradient":
                node = mutated.find(".//{" + checks.NS + "}linearGradient")
            else:
                node = mutated.find(".//*[@id='" + target + "']")
            node.set(attribute, value)
            with self.subTest(target=target, attribute=attribute), self.assertRaises(ValueError):
                checks.check_compiled_structure(ET.tostring(mutated), plan)

    def test_timeout_reclaims_spawned_child_before_it_can_write(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / "orphan-marker.txt"
            child_code = "import time,pathlib; time.sleep(1.0); pathlib.Path(" + repr(str(marker)) + ").write_text('orphan')"
            parent_code = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(child_code) + "]); time.sleep(10)"
            with self.assertRaises(subprocess.TimeoutExpired):
                e2e.run_bounded([sys.executable, "-B", "-c", parent_code], timeout=0.4)
            time.sleep(1.1)
            self.assertFalse(marker.exists(), "Timeout left a child process running")

    def test_round_requires_both_distinct_profiles(self):
        for outputs in ({"short": b"a"}, {"short": b"a", "full": b"a"}, {"short": b"a", "full": b""}):
            with self.subTest(outputs=outputs), self.assertRaises(ValueError):
                checks.check_profile_pair(outputs)
        self.assertEqual(set(checks.check_profile_pair({"short": b"short-svg", "full": b"full-svg"})), {"short", "full"})

    def test_deepseek_binding_rejects_role_loss_hash_drift_or_whale_substitution(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "ref/user-mode").mkdir(parents=True)
            data = b"independent r1 fixture"
            (root / "ref/user-mode/r1.png").write_bytes(data)
            path = root / "bindings.json"
            binding = {"reference": "ref/user-mode/r1.png", "roles": ["subject", "style"], "sha256": hashlib.sha256(data).hexdigest()}
            path.write_text(json.dumps({"bindings": {"deepseek": binding}}), encoding="utf-8")
            self.assertEqual(checks.check_reference_binding(root, path)["status"], "matched")
            for field, value in (("roles", ["style"]), ("reference", "ref/user-mode/whale.png"), ("sha256", "0" * 64)):
                mutated = {**binding, field: value}
                path.write_text(json.dumps({"bindings": {"deepseek": mutated}}), encoding="utf-8")
                with self.subTest(field=field), self.assertRaises(ValueError):
                    checks.check_reference_binding(root, path)

    def test_rendered_mask_retains_parent_transform_and_source_clip(self):
        source = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">
        <defs><clipPath id="clip"><rect x="4" y="4" width="20" height="20"/></clipPath></defs>
        <g transform="translate(8 8)" clip-path="url(#clip)">
          <rect id="target" x="0" y="0" width="40" height="40" fill="#ff0000"/>
          <rect id="other" x="0" y="0" width="64" height="64" fill="#0000ff"/>
        </g></svg>'''
        masks = checks.raster_masks(source, {"layers": [{"id": "target"}]}, 64)
        target = masks["target"]
        self.assertEqual(int((target >= 128).sum()), 400)
        self.assertEqual(int(target[16, 16]), 255)
        self.assertEqual(int(target[6, 6]), 0)
        self.assertEqual(int(target[35, 35]), 0)

    def test_anchor_gate_rejects_floating_or_leaking_shadow_from_real_svg(self):
        cases = {
            "anchored": ('x="8" y="8" width="40" height="4"', []),
            "floating": ('x="24" y="24" width="10" height="8"', ["floating_shadow_component"]),
            "leaking": ('x="44" y="18" width="16" height="8"', ["pixels_outside_receiver"]),
        }
        plan = {"layers": [{"id": "face", "role": "surface"}, {"id": "shadow", "role": "occlusion-shadow", "owner": "face"}]}
        for name, (attributes, required) in cases.items():
            source = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect id="face" x="8" y="8" width="40" height="40"/><rect id="shadow" ' + attributes + '/></svg>'
            masks = checks.raster_masks(source, plan, 64)
            report = checks.ownership_checks(masks, plan, 64)
            codes = [issue["code"] for issue in report["issues"]]
            with self.subTest(case=name):
                for code in required:
                    self.assertIn(code, codes)
                if not required:
                    self.assertEqual(report["status"], "no_rule_failure")
                self.assertEqual(report["naturalness"], "not_automatically_assessed")

    def test_invisible_selected_layer_cannot_claim_complete_mask_coverage(self):
        source = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect id="hidden" x="8" y="8" width="40" height="40" display="none"/></svg>'
        with self.assertRaisesRegex(ValueError, "no measurable rendered coverage"):
            checks.raster_masks(source, {"layers": [{"id": "hidden"}]}, 64)

    def test_material_masks_cover_full_visible_surface_and_disclose_occlusion(self):
        source = b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect id="face" x="8" y="8" width="40" height="40"/><rect id="shadow" x="8" y="8" width="40" height="4"/><rect id="eye" x="20" y="20" width="4" height="8"/></svg>'
        plan = {"layers": [{"id": "face", "role": "surface"}, {"id": "shadow", "role": "occlusion-shadow", "owner": "face"}, {"id": "eye", "role": "eye"}]}
        masks = checks.raster_masks(source, plan, 64)
        contract, visible, exclusions = checks.visible_material_contract(source, masks, plan, {})
        face = next(row for row in exclusions if row["id"] == "face")
        self.assertEqual(face["raw_mask_pixels"], 1600)
        self.assertEqual(face["shadow_excluded_pixels"], 160)
        self.assertEqual(face["all_later_layer_excluded_pixels"], 192)
        self.assertEqual(int(visible["face"].sum()), 1408)
        self.assertEqual(int(visible["whole-subject"].sum()), 1600)
        self.assertFalse(visible["face"][21, 21])
        self.assertTrue(visible["face"][45, 45])
        self.assertTrue(all("mask_id" in region and "bbox" not in region for region in contract["regions"]))

    def test_end_to_end_controls_detect_injected_pixel_and_structural_faults(self):
        compiler = e2e.load_compiler()
        source = b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect id="face" x="8" y="8" width="40" height="40"/></svg>'
        plan = {"schema": "aikon.paint-plan.v1", "geometry_sha256": hashlib.sha256(source).hexdigest(), "profile": "short", "layers": [{"id": "face", "role": "surface", "paint": {"type": "solid", "color": "#d8c8b8"}}]}
        svg, _ = compiler.compile_paint(source, plan)
        with tempfile.TemporaryDirectory() as folder:
            report = e2e.negative_controls(checks, diagnostic, compiler, source, plan, svg, Path(folder), diagnostic.DEFAULT_RULES)
            self.assertEqual(report["status"], "pass", report)
            self.assertEqual(len(report["cases"]), 10)
            self.assertTrue((Path(folder) / "small-interior-highlight.png").exists())
            self.assertFalse(report["cases"][0]["observed_failure"])
            self.assertTrue(all(case["observed_failure"] for case in report["cases"][1:]))


if __name__ == "__main__":
    unittest.main()
