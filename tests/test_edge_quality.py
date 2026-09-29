"""Independent pixel perturbations test the detector, not current icon identity."""
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEPENDENCIES = all(importlib.util.find_spec(name) for name in ("numpy", "PIL", "scipy", "resvg_py"))
FIXTURES = ROOT / "docs/validation/edges-v3/fixtures"


@unittest.skipUnless(DEPENDENCIES, "optional requirements-ci.txt needed")
class EdgeQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import numpy as np
        from PIL import Image
        from tools import analyze_edge_quality, render_svg
        cls.np, cls.Image, cls.gate, cls.renderer = np, Image, analyze_edge_quality, render_svg
        cls.source = (FIXTURES / "curve-gradient.svg").read_text(encoding="utf-8")
        cls.base = Image.open(io.BytesIO(render_svg.render_svg_text(cls.source, 256))).convert("RGBA")

    def codes(self, report):
        return {issue["code"] for issue in report["issues"]}

    def test_legal_curves_sharp_corners_gradients_crop_black_outline_and_materials(self):
        for path in sorted(FIXTURES.glob("*.svg")):
            for size in (128, 256):
                with self.subTest(fixture=path.name, size=size):
                    report, _ = self.gate.analyze_svg_edges(path.read_text(encoding="utf-8"), size=size)
                    self.assertEqual(report["status"], "no_rule_failure", report["issues"])
                    for background in ("dark", "light"):
                        error = report["metrics"]["composite_" + background]
                        self.assertLess(error["mae_0_255"], 8)
                    self.assertEqual(report["visual_acceptance"], "not_assessed")

    def test_nearest_neighbor_staircase_fails_even_when_edge_rgb_has_no_color_pollution(self):
        source = '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><circle cx="127.5" cy="128" r="105" fill="#42618a"/></svg>'
        image = self.Image.open(io.BytesIO(self.renderer.render_svg_text(source, 64))).convert("RGBA")
        candidate = image.resize((256, 256), self.Image.Resampling.NEAREST)
        report, _ = self.gate.analyze_svg_edges(source, candidate)
        self.assertIn("edge_coverage_mismatch", self.codes(report))
        self.assertLess(report["metrics"]["color"]["mae_0_255"], 2)

    def test_binary_alpha_without_rgb_change_is_not_mistaken_for_good_antialiasing(self):
        raw = self.np.array(self.base)
        raw[:, :, 3] = self.np.where(raw[:, :, 3] >= 128, 255, 0)
        report, _ = self.gate.analyze_svg_edges(self.source, self.Image.fromarray(raw))
        self.assertEqual(self.codes(report), {"edge_coverage_mismatch"})

    def test_svg_crisp_edges_hint_is_compared_to_precise_coverage_of_same_path(self):
        crisp = self.source.replace('<path d=', '<path shape-rendering="crispEdges" d=')
        report, _ = self.gate.analyze_svg_edges(crisp)
        self.assertIn("edge_coverage_mismatch", self.codes(report))

    def test_colored_partial_alpha_fringe_does_not_need_alpha_change(self):
        raw = self.np.array(self.base)
        ring = (raw[:, :, 3] > 16) & (raw[:, :, 3] < 240)
        raw[:, :, :3][ring] = (245, 20, 210)
        report, _ = self.gate.analyze_svg_edges(self.source, self.Image.fromarray(raw))
        self.assertIn("edge_color_contamination_or_material_mismatch", self.codes(report))
        self.assertNotIn("edge_coverage_mismatch", self.codes(report))
        for background in ("dark", "light"):
            self.assertGreater(report["metrics"]["composite_" + background]["large_error_pixels"], 100)

    def test_short_sixteen_pixel_contamination_is_caught_despite_good_global_average(self):
        raw = self.np.array(self.base)
        yy, xx = self.np.nonzero((raw[:, :, 3] >= 96) & (raw[:, :, 3] < 240))
        selection = self.np.argsort((xx - 110)**2 + (yy - 17)**2)[:16]
        raw[yy[selection], xx[selection], :3] = (245, 20, 210)
        report, _ = self.gate.analyze_svg_edges(self.source, self.Image.fromarray(raw))
        self.assertIn("local_edge_color_contamination_or_material_mismatch", self.codes(report))
        self.assertLess(report["metrics"]["color"]["mae_0_255"], 8)
        self.assertLess(report["metrics"]["color"]["large_error_fraction"], .03)
        self.assertEqual(report["metrics"]["color"]["large_error_pixels"], 16)

    def test_interior_alpha_patch_is_separate_from_edge_and_color(self):
        raw = self.np.array(self.base)
        raw[109:139, 109:139, 3] = 239
        report, _ = self.gate.analyze_svg_edges(self.source, self.Image.fromarray(raw))
        self.assertEqual(self.codes(report), {"unexpected_interior_alpha_deficit"})
        self.assertEqual(report["metrics"]["interior_alpha"]["bad_pixels"], 900)

    def test_hidden_transparent_rgb_is_not_visible_fringe(self):
        raw = self.np.array(self.base)
        raw[:, :, :3][raw[:, :, 3] == 0] = (255, 0, 255)
        report, _ = self.gate.analyze_svg_edges(self.source, self.Image.fromarray(raw))
        self.assertEqual(report["status"], "no_rule_failure")

    def test_opaque_material_staircase_cannot_evade_gate_with_all_alpha255(self):
        source = (FIXTURES / "opaque-materials.svg").read_text(encoding="utf-8")
        low = self.Image.open(io.BytesIO(self.renderer.render_svg_text(source, 64))).convert("RGBA")
        raw = low.resize((256, 256), self.Image.Resampling.NEAREST)
        self.assertTrue(self.np.all(self.np.asarray(raw)[:, :, 3] == 255))
        report, _ = self.gate.analyze_svg_edges(source, raw)
        self.assertIn("edge_color_contamination_or_material_mismatch", self.codes(report))
        self.assertEqual(report["metrics"]["coverage"]["sample_pixels"], 0)

    def test_single_png_and_featureless_canvas_cannot_report_pass(self):
        advisory = self.gate.analyze_png_advisory(self.base)
        self.assertEqual(advisory["status"], "advisory_not_verifiable")
        empty = '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#446699"/></svg>'
        report, _ = self.gate.analyze_svg_edges(empty)
        self.assertEqual(report["status"], "insufficient_edge_evidence")

    def test_budget_mismatched_canvas_and_uncalibrated_sampling_fail_closed(self):
        for size in (0, 31, 1025, True, 256.5):
            with self.subTest(size=size), self.assertRaises(ValueError):
                self.gate.analyze_svg_edges(self.source, size=size)
        for factor in (1, 2, 8, 4.0, True):
            with self.subTest(factor=factor), self.assertRaises(ValueError):
                self.gate.analyze_svg_edges(self.source, supersample=factor)
        with self.assertRaisesRegex(ValueError, "dimensions"):
            self.gate.analyze_svg_edges(self.source, self.base.resize((255, 256)))
        with self.assertRaisesRegex(ValueError, "1024"):
            self.gate.analyze_png_advisory(self.Image.new("RGBA", (1025, 1)))

    def test_evidence_contains_real_dark_light_masks_errors_and_local_pixel_coordinates(self):
        raw = self.np.array(self.base)
        ring = (raw[:, :, 3] > 16) & (raw[:, :, 3] < 240)
        raw[:, :, :3][ring] = (245, 20, 210)
        report, maps = self.gate.analyze_svg_edges(self.source, self.Image.fromarray(raw))
        with tempfile.TemporaryDirectory(prefix="aikon-edge-") as directory:
            self.gate.save_evidence(directory, report, maps)
            path = Path(directory)
            for filename in ("candidate.png", "reference.png", "candidate_dark.png", "reference_light.png", "alpha_error.png", "color_error.png", "color_edge_mask.png", "local-color-cluster-crop.png", "crop-location.json"):
                self.assertTrue((path / filename).is_file(), filename)
            self.assertEqual(json.loads((path / "report.json").read_text())["status"], "fail")
            self.assertEqual(self.np.asarray(self.Image.open(path / "candidate.png")).tolist(), raw.tolist())

    def test_cli_png_advisory_is_not_exit_zero_and_does_not_change_input(self):
        with tempfile.TemporaryDirectory(prefix="aikon-edge-cli-") as directory:
            path = Path(directory)
            source = path / "source.png"
            self.base.save(source)
            original = source.read_bytes()
            # The test owns this direct no-child worker and imposes15s itself;
            # production CLI process-tree timeout is exercised by --audit above.
            command = [sys.executable, "-B", str(ROOT / "tools/analyze_edge_quality.py"), "--png", str(source), "--output", str(path / "result"), "--worker"]
            result = subprocess.run(command, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 3, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "advisory_not_verifiable")
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
