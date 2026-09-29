"""Independent violations of the fixed r1 comparison contract."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from tools import compare_r1_reference as comparison


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "ref/user-mode/r1.png"


class R1ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference, cls.masks = comparison.load_reference(REFERENCE)

    def test_reference_only_masks_separate_background_face_and_watermark(self):
        self.assertFalse(self.masks["subject"][30, 1100])
        self.assertTrue(self.masks["subject"][1100, 400])
        self.assertFalse(self.masks["valid"][1220, 1170])
        self.assertTrue(self.masks["valid"][1170, 1170])
        self.assertLess((~self.masks["valid"]).mean(), .006)

    def test_background_identity_does_not_hide_wrong_subject(self):
        candidate = self.reference.copy()
        candidate[self.masks["subject"], :3] = [240, 30, 10]
        result = comparison.compare_pixels(self.reference, candidate, self.masks)
        self.assertEqual(result["background"]["mae_srgb8"], 0)
        self.assertGreater(result["subject"]["mae_srgb8"], 80)
        self.assertGreater(result["subject"]["mae_srgb8"], result["whole_valid_canvas_context_only"]["mae_srgb8"])
        self.assertEqual(result["acceptance"]["user_99_percent_target"], "not_assessed")

    def test_local_eye_shift_is_reported_without_registration(self):
        candidate = self.reference.copy()
        candidate[650:900, 125:305] = np.roll(candidate[650:900, 125:305], 18, axis=1)
        result = comparison.compare_pixels(self.reference, candidate, self.masks)
        self.assertGreater(result["local_regions"]["eye_left"]["context"]["mae_srgb8"], 10)
        self.assertEqual(result["local_regions"]["eye_right"]["context"]["mae_srgb8"], 0)

    def test_local_fin_shift_is_reported_without_moving_eyes(self):
        candidate = self.reference.copy()
        candidate[725:1160, 970:1270] = np.roll(candidate[725:1160, 970:1270], 20, axis=0)
        result = comparison.compare_pixels(self.reference, candidate, self.masks)
        self.assertGreater(result["local_regions"]["head_side_fin"]["context"]["mae_srgb8"], 3)
        self.assertEqual(result["local_regions"]["eye_left"]["context"]["mae_srgb8"], 0)

    def test_watermark_only_changes_do_not_change_any_reported_metric(self):
        candidate = self.reference.copy()
        baseline = comparison.compare_pixels(self.reference, candidate, self.masks)
        candidate[~self.masks["valid"]] = [255, 0, 250, 0]
        changed = comparison.compare_pixels(self.reference, candidate, self.masks)
        self.assertEqual(changed, baseline)

    def test_new_or_modified_reference_cannot_silently_redefine_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            wrong = Path(temporary) / "edited-r1.png"
            candidate = self.reference.copy()
            candidate[1200, 1170] = [15, 15, 15, 255]
            Image.fromarray(candidate).save(wrong)
            with self.assertRaisesRegex(ValueError, "hash differs"):
                comparison.load_reference(wrong)

    def test_foreground_alpha_failure_is_not_hidden_by_black_composite(self):
        candidate = self.reference.copy()
        baseline = comparison.compare_pixels(self.reference, candidate, self.masks)
        candidate[self.masks["subject"], 3] = 0
        missing = comparison.compare_pixels(self.reference, candidate, self.masks)
        self.assertEqual(missing["silhouette_alpha_proxy"]["iou"], 0)
        self.assertLess(missing["alpha"]["subject_mean_alpha"], baseline["alpha"]["subject_mean_alpha"])

    def test_wrong_array_size_not_resampled(self):
        with self.assertRaisesRegex(ValueError, "no silent resampling"):
            comparison.compare_pixels(self.reference, self.reference[::2, ::2], self.masks)

    def test_canvas_change_and_undeclared_uniform_resize_rejected(self):
        original = '<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024"><circle r="100"/></svg>'
        comparison.validate_canvas(original, 1024)
        for invalid in (original.replace("1024", "2048"),
                        original.replace("0 0 1024 1024", "10 10 1024 1024"),
                        original.replace("<circle", '<g transform="scale(0.5)"><circle').replace("</svg>", "</g></svg>").replace('width="1024"', 'width="512"')):
            with self.assertRaises(ValueError):
                comparison.validate_canvas(invalid, 1024)

    def test_freeze_is_source_only_and_refuses_changed_protocol(self):
        with tempfile.TemporaryDirectory() as temporary:
            comparison.freeze_reference(REFERENCE, temporary)
            path = Path(temporary) / "protocol.json"
            protocol = json.loads(path.read_text(encoding="utf-8"))
            protocol["watermark_box_xyxy_half_open"] = [0, 0, 1280, 1280]
            path.write_text(json.dumps(protocol), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no overwrite"):
                comparison.freeze_reference(REFERENCE, temporary)

    def test_actual_svg_render_saves_evidence_and_does_not_align_internal_scale(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            svg = '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1280" viewBox="0 0 1280 1280"><g transform="scale(SCALE)"><rect x="0" y="200" width="950" height="1000" rx="160" fill="#496ba9"/></g></svg>'
            results = []
            for index, scale in enumerate(("1", ".8")):
                path = folder / (str(index) + ".svg")
                path.write_text(svg.replace("SCALE", scale), encoding="utf-8")
                output = folder / str(index)
                result = comparison.compare_svg(REFERENCE, path, output, canvas_size=1280)
                results.append(result)
                with Image.open(output / "candidate-render.png") as image:
                    self.assertEqual(image.size, (1280, 1280))
                self.assertTrue((output / "diff-x4.png").is_file())
                self.assertTrue((output / "overlay-half.png").is_file())
                self.assertEqual(result["acceptance"]["visual_acceptance"], "not_assessed")
                with self.assertRaisesRegex(ValueError, "retain prior evidence"):
                    comparison.compare_svg(REFERENCE, path, output, canvas_size=1280)
            self.assertNotEqual(results[0]["silhouette_alpha_proxy"]["iou"], results[1]["silhouette_alpha_proxy"]["iou"])
            self.assertGreater(results[1]["silhouette_alpha_proxy"]["false_negative_pixels"], results[0]["silhouette_alpha_proxy"]["false_negative_pixels"])


if __name__ == "__main__":
    unittest.main()
