"""Independent contour controls plus actual rejected-output regression."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from tools import analyze_capsule_geometry as gate
from tools import render_svg
from tools import review_gloss_pairs as review

ROOT = Path(__file__).resolve().parents[1]


def pillow_shape(kind, width=56, height=112, angle=0, size=256, blur=0):
    """Pillow geometry, independent of the gate's signed-distance fixtures."""
    scale = 4
    canvas = Image.new("L", (size * scale, size * scale), 0)
    d = ImageDraw.Draw(canvas)
    x0, y0 = (size - width) * scale / 2, (size - height) * scale / 2
    x1, y1 = x0 + width * scale - 1, y0 + height * scale - 1
    if kind == "capsule":
        d.rounded_rectangle((x0, y0, x1, y1), radius=width * scale / 2, fill=255)
    elif kind == "ellipse":
        d.ellipse((x0, y0, x1, y1), fill=255)
    elif kind == "square":
        d.rectangle((x0, y0, x1, y1), fill=255)
    elif kind == "short_round_caps":
        d.rounded_rectangle((x0, y0, x1, y1), radius=width * scale / 10, fill=255)
    elif kind == "pointed":
        cx, cy = size * scale / 2, size * scale / 2
        d.polygon(((cx, y0), (x1, y0 + width * scale / 2), (x1, y1 - width * scale / 2), (cx, y1), (x0, y1 - width * scale / 2), (x0, y0 + width * scale / 2)), fill=255)
    else:
        raise ValueError(kind)
    canvas = canvas.rotate(angle, resample=Image.Resampling.BICUBIC)
    canvas = canvas.resize((size, size), Image.Resampling.LANCZOS)
    if blur:
        canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(canvas, dtype=float) / 255


class CapsuleGeometryTests(unittest.TestCase):
    def test_independent_capsules_survive_rotation_scale_and_light_aa(self):
        for width, height, angle, blur in ((56, 112, 0, 0), (56, 112, 17, 0), (24, 60, -31, 0), (65, 195, 43, .4)):
            with self.subTest(width=width, height=height, angle=angle, blur=blur):
                result = gate.analyze_eye_mask(pillow_shape("capsule", width, height, angle, blur=blur))
                self.assertEqual(result["status"], "no_rule_failure", result)

    def test_ellipses_fail_and_have_specific_better_model_evidence(self):
        for width, height, angle in ((56, 112, 0), (56, 112, 17), (24, 60, -31), (65, 195, 43)):
            with self.subTest(angle=angle):
                result = gate.analyze_eye_mask(pillow_shape("ellipse", width, height, angle))
                self.assertEqual(result["status"], "fail")
                self.assertIn("ellipse_explains_contour_better", result["issues"])

    def test_squared_and_pointed_endcaps_fail(self):
        for kind in ("square", "short_round_caps", "pointed"):
            with self.subTest(kind=kind):
                result = gate.analyze_eye_mask(pillow_shape(kind, angle=19))
                self.assertEqual(result["status"], "fail")
                self.assertIn("capsule_contour_rms_exceeded", result["issues"])

    def test_svg_path_and_rect_tags_are_not_shape_oracles(self):
        bodies = [
            '<path id="ellipse" d="M98 96 A30 30 0 0 1 158 96 V156 A30 30 0 0 1 98 156Z"/>',
            '<rect id="not-a-capsule" x="98" y="66" width="60" height="120" rx="30"/>',
        ]
        for body in bodies:
            with self.subTest(body=body):
                png = render_svg.render_svg_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256">' + body + '</svg>', 256)
                with Image.open(io.BytesIO(png)) as image:
                    mask = np.asarray(image)[:, :, 3].astype(float) / 255
                self.assertEqual(gate.analyze_eye_mask(mask)["status"], "no_rule_failure")

    def test_empty_disconnected_and_holes_do_not_pass(self):
        empty = np.zeros((64, 64), bool)
        self.assertIn("empty_or_disconnected_eye_mask", gate.analyze_eye_mask(empty)["issues"])
        mask = pillow_shape("capsule") >= .5
        speck = mask.copy()
        speck[8:11, 8:11] = True
        self.assertIn("empty_or_disconnected_eye_mask", gate.analyze_eye_mask(speck)["issues"])
        hole = mask.copy()
        hole[124:132, 124:132] = False
        self.assertIn("eye_mask_contains_holes", gate.analyze_eye_mask(hole)["issues"])

    def test_remote_translucent_component_is_reported(self):
        mask = pillow_shape("capsule")
        mask[10:15, 10:15] = .1
        self.assertIn("stray_coverage_outside_eye_contour", gate.analyze_eye_mask(mask)["issues"])

    def test_clipping_is_a_failure_not_an_alignment_fix(self):
        mask = pillow_shape("capsule")[:, 125:]
        self.assertIn("eye_mask_touches_canvas_edge", gate.analyze_eye_mask(mask)["issues"])

    def test_tiny_eye_is_unassessed_not_certified(self):
        result = gate.analyze_eye_mask(pillow_shape("capsule", width=10, height=24))
        self.assertEqual(result["status"], "not_assessed")
        self.assertIn("insufficient_resolution_for_contour_gate", result["issues"])

    def test_half_coverage_point_and_zero_width_lines_are_strict_json(self):
        masks = []
        for kind in ("point", "horizontal", "vertical"):
            mask = np.zeros((64, 64), dtype=float)
            if kind == "point":
                mask[32, 32] = .5
            elif kind == "horizontal":
                mask[32, 20:44] = .5
            else:
                mask[20:44, 32] = .5
            masks.append(mask)
            with self.subTest(kind=kind), np.errstate(divide="raise", invalid="raise", over="raise"):
                report = gate.analyze_eye_mask(mask)
                self.assertEqual(report["status"], "not_assessed")
                self.assertIn("degenerate_eye_contour", report["issues"])
                self.assertNotIn("fits", report)
                json.dumps(report, allow_nan=False)
                with tempfile.TemporaryDirectory() as folder:
                    gate.save_eye_evidence(mask, report, folder)
                    saved = json.loads((Path(folder) / "report.json").read_text(encoding="utf-8"))
                    self.assertEqual(saved["status"], "not_assessed")
        pair = gate.analyze_pair(masks[:2])
        self.assertIsNone(pair["relationship"])
        json.dumps(pair, allow_nan=False)

    def test_unassessed_mask_cli_returns_nonzero(self):
        # 8-bit 128/255 is just above .5: a tiny nonzero contour rather than an
        # exact degenerate point. Both unresolved cases must remain non-passes.
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tiny.png"
            image = Image.new("L", (64, 64), 0)
            image.putpixel((32, 32), 128)
            image.save(path)
            argv = ["analyze_capsule_geometry.py", "--mask", str(path), "--output", str(Path(folder) / "evidence"), "--worker"]
            with patch("sys.argv", argv), redirect_stdout(io.StringIO()):
                code = gate.main()
            self.assertEqual(code, 2)
            saved = json.loads((Path(folder) / "evidence/report.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "not_assessed")
            json.dumps(saved, allow_nan=False)

    def test_circle_is_outside_elongated_contract(self):
        result = gate.analyze_eye_mask(pillow_shape("ellipse", width=60, height=60))
        self.assertEqual(result["status"], "fail")
        self.assertIn("outside_elongated_capsule_aspect_contract", result["issues"])

    def test_pair_preserves_original_offsets_and_size_relations(self):
        a = pillow_shape("capsule", width=30, height=60, angle=12, size=320)
        b = pillow_shape("capsule", width=36, height=72, angle=20, size=320)
        a = np.roll(a, -65, axis=1)
        b = np.roll(np.roll(b, 65, axis=1), 30, axis=0)
        r = gate.analyze_pair([a, b])["relationship"]
        self.assertAlmostEqual(r["center_vector_xy_pixels"][0], 130, delta=.1)
        self.assertAlmostEqual(r["center_vector_xy_pixels"][1], 30, delta=.1)
        self.assertAlmostEqual(r["major_axis_difference_degrees"], 8, delta=.3)
        self.assertAlmostEqual(r["major_length_ratio_right_over_left"], 1.2, delta=.025)
        self.assertEqual(r["status"], "measurement_only_not_pitch_estimation")

    def test_invalid_mask_inputs_rejected(self):
        for mask in (np.zeros((50, 50), np.uint8), np.full((50, 50), np.nan), np.full((50, 50), 1.1), np.zeros((50, 50, 3))):
            with self.subTest(shape=mask.shape):
                with self.assertRaises(ValueError):
                    gate.analyze_eye_mask(mask)
        with self.assertRaises(ValueError):
            gate.analyze_pair([np.zeros((30, 30), bool), np.zeros((40, 40), bool)])

    def test_high_complexity_connected_comb_is_not_simplified_to_capsule(self):
        mask = np.zeros((256, 256), bool)
        mask[5:251, 6:250:2] = True
        mask[124:132, 6:249] = True
        result = gate.analyze_eye_mask(mask)
        self.assertIn("excessive_contour_complexity", result["issues"])
        self.assertEqual(result["status"], "fail")

    def test_reference_roi_cannot_silently_trim_an_eye(self):
        image = Image.new("RGB", (100, 100), "white")
        ImageDraw.Draw(image).ellipse((20, 20, 70, 80), fill="black")
        with self.assertRaisesRegex(ValueError, "ROI edge"):
            gate.extract_dark_roi(image, [30, 10, 90, 90], [45, 45])
        with self.assertRaisesRegex(ValueError, "not a dark"):
            gate.extract_dark_roi(image, [10, 10, 90, 90], [15, 15])

    def test_real_r1_is_near_capsule_at_multiple_color_thresholds(self):
        with Image.open(ROOT / "ref/user-mode/r1.png") as image:
            for threshold in (80, 100, 120):
                for bbox, seed in (([135, 650, 295, 900], [211, 770]), ([560, 810, 720, 1045], [641, 930])):
                    with self.subTest(threshold=threshold, seed=seed):
                        mask = gate.extract_dark_roi(image, bbox, seed, threshold)
                        result = gate.analyze_eye_mask(mask)
                        self.assertEqual(result["status"], "no_rule_failure", result)
                        self.assertGreater(result["observed"]["aspect_ratio"], 1.8)
                        self.assertLess(result["observed"]["aspect_ratio"], 2.1)

    def test_actual_rejected_deepseek_eyes_fail_capsule_gate(self):
        for profile in ("short", "full"):
            svg = (ROOT / "outputs/fixtures/deepseek/round-002" / (profile + ".svg")).read_text(encoding="utf-8")
            root = render_svg.validate_svg(svg)
            for name in ("eye-left", "eye-right"):
                with self.subTest(profile=profile, eye=name):
                    png = render_svg.render_svg_text(review._eye_markup(root, name, False), 1024)
                    mask = review.rgba(png)[:, :, 3].astype(float) / 255
                    result = gate.analyze_eye_mask(mask)
                    self.assertEqual(result["status"], "fail")
                    self.assertIn("ellipse_explains_contour_better", result["issues"])


if __name__ == "__main__":
    unittest.main()
