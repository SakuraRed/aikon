"""Independent material-domain controls; neither a visual score nor a new gate."""
from pathlib import Path
import importlib.util
import unittest

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("paint_support", ROOT / "tools/analyze_paint_fields.py")
paint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(paint)


def scene(kind="solid", width=192, outside=(240, 10, 150)):
    yy, xx = np.mgrid[:256, :256]
    mask = (abs(xx-127.5) < width/2) & (yy >= 32) & (yy < 224)
    arr = np.empty((256, 256, 4), dtype=np.uint8)
    arr[:, :, :3] = outside
    arr[:, :, 3] = 255
    field = np.full((256, 256, 3), (70, 105, 140), dtype=float)
    if kind == "linear":
        field += ((yy-128) / 192)[:, :, None] * np.array([40, 30, 20])
    elif kind == "radial":
        field += (12 * np.exp(-((xx-128)**2+(yy-128)**2) / (2*90**2)))[:, :, None]
    elif kind == "radial-cone":
        t = np.clip(np.hypot(xx-128, yy-128)/100, 0, 1)
        field = (1-t[:, :, None])*np.array([250, 230, 180]) + t[:, :, None]*np.array([30, 65, 150])
    elif kind == "grain":
        field += np.random.default_rng(98413).integers(-12, 13, (256, 256, 3))
    elif kind == "mottle":
        field += (5*np.sin(xx*2*np.pi/30)*np.sin(yy*2*np.pi/30))[:, :, None]
    elif kind == "island":
        field[((xx-128)**2+(yy-128)**2)<12**2] = (165, 175, 80)
    elif kind == "alpha":
        arr[110:142, 116:140, 3] = 128
    arr[mask, :3] = np.rint(field[mask]).astype(np.uint8)
    contract = {"long_edge": 256, "regions": [
        {"id": "surface", "mask_id": "material", "expectation": "smooth_field"}]}
    return Image.fromarray(arr), contract, {"material": mask}


def analyze(kind="solid", width=192, outside=(240, 10, 150)):
    return paint.analyze_image(*scene(kind, width, outside))


class PaintSupportTests(unittest.TestCase):
    def test_complete_kernel_observation_is_independent_of_outside_material_color(self):
        for kind in ("solid", "linear", "radial"):
            with self.subTest(kind=kind):
                first, _ = analyze(kind, outside=(0, 0, 0))
                second, _ = analyze(kind, outside=(255, 255, 255))
                a = first["regions"][0]["texture_support_evidence"]["scales"]
                b = second["regions"][0]["texture_support_evidence"]["scales"]
                for scale in ("grain", "mottle"):
                    self.assertEqual(a[scale]["rms_0_255"], b[scale]["rms_0_255"])
                    self.assertFalse(a[scale]["exceeds_bound"])

    def test_full_kernel_masks_do_not_use_image_edges_to_drop_internal_defects(self):
        clean, clean_maps = analyze()
        damaged, damaged_maps = analyze("island")
        for scale in ("grain", "mottle"):
            self.assertTrue(np.array_equal(clean_maps["texture_support"]["surface"][scale],
                                           damaged_maps["texture_support"]["surface"][scale]))
        self.assertTrue(damaged["regions"][0]["texture_support_evidence"]["scales"]["mottle"]["exceeds_bound"])

    def test_narrow_legal_materials_are_explicitly_unassessed_at_the_mottle_scale(self):
        for kind in ("solid", "linear", "radial"):
            result, _ = analyze(kind, width=32)
            support = result["regions"][0]["texture_support_evidence"]
            self.assertFalse(support["unassessed_pixels_are_clean"])
            self.assertGreater(support["scales"]["grain"]["sample_pixels"], 64)
            self.assertEqual(support["scales"]["mottle"]["sample_pixels"], 0)
            self.assertIsNone(support["scales"]["mottle"]["exceeds_bound"])

    def test_thin_material_is_not_reported_as_clean_after_erosion(self):
        result, _ = analyze(width=6)
        region = result["regions"][0]
        self.assertIn("insufficient_opacity_evidence", region["failures"])
        self.assertIn("insufficient_texture_evidence", region["failures"])
        for data in region["texture_support_evidence"]["scales"].values():
            self.assertIsNone(data["rms_0_255"])
            self.assertIn("not_assessed", data["measurement_status"])

    def test_grain_and_mottle_negative_controls_remain_sensitive(self):
        for kind, scale in (("grain", "grain"), ("mottle", "mottle")):
            result, _ = analyze(kind)
            support = result["regions"][0]["texture_support_evidence"]
            self.assertTrue(support["scales"][scale]["exceeds_bound"])
            self.assertIn(scale+"_above_reference_bound", result["regions"][0]["failures"])
        narrow, _ = analyze("grain", width=32)
        self.assertTrue(narrow["regions"][0]["texture_support_evidence"]["scales"]["grain"]["exceeds_bound"])

    def test_alpha_defect_is_not_hidden_by_rgb_support(self):
        result, _ = analyze("alpha")
        self.assertIn("translucent_interior", result["regions"][0]["failures"])
        self.assertGreater(result["regions"][0]["opacity"]["translucent_pixels"], 0)

    def test_advisory_support_does_not_promote_known_radial_model_limit_to_pass(self):
        result, _ = analyze("radial-cone")
        self.assertEqual(result["visual_acceptance"], "not_assessed")
        self.assertIn("unexpected_color_islands_in_declared_smooth_field", result["regions"][0]["failures"])
        self.assertIn("outside this model", result["regions"][0]["texture_support_evidence"]["island_model"])


if __name__ == "__main__":
    unittest.main()
