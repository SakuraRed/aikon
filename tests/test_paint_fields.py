"""Independent image controls for the paint diagnostics, not implementation mirrors."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image, ImageDraw


SOURCE = Path(__file__).resolve().parents[1] / "tools" / "analyze_paint_fields.py"
SPEC = importlib.util.spec_from_file_location("paint_fields", SOURCE)
paint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(paint)


def contract(expectation="smooth_field"):
    return {"schema": paint.SCHEMA, "long_edge": 256, "regions": [
        {"id": "surface", "bbox": [.12, .12, .88, .88], "expectation": expectation}]}


def run(image, specification=None):
    return paint.analyze_image(image, contract() if specification is None else specification)[0]


class PaintFieldsTests(unittest.TestCase):
    def test_flat_field_and_quantized_linear_ramp_are_legal(self):
        flat = Image.new("RGBA", (256, 256), (70, 105, 140, 255))
        ramp = np.zeros((256, 256, 4), dtype=np.uint8)
        ramp[:, :, :3] = np.rint(np.linspace([40, 60, 90], [130, 150, 180], 256))[None, :, :]
        ramp[:, :, 3] = 255
        for image in (flat, Image.fromarray(ramp)):
            result = run(image)
            self.assertEqual(result["issues"], [])
            self.assertEqual(result["visual_acceptance"], "not_assessed")

    def test_gentle_radial_gradient_is_not_a_blanket_gradient_ban(self):
        yy, xx = np.mgrid[:256, :256]
        field = 90 + 12 * np.exp(-((xx-128)**2 + (yy-128)**2) / (2*90**2))
        rgb = np.repeat(np.rint(field)[:, :, None], 3, axis=2).astype("uint8")
        self.assertEqual(run(Image.fromarray(rgb))["issues"], [])

    def test_injected_grain_is_rejected_on_a_previously_clean_field(self):
        rng = np.random.default_rng(8094)
        noise = rng.integers(-10, 11, (256, 256, 3), dtype=np.int16)
        result = run(Image.fromarray(np.uint8(110 + noise)))
        self.assertIn("grain_above_reference_bound", [i["code"] for i in result["issues"]])

    def test_medium_scale_mottling_is_distinct_from_fine_grain(self):
        yy, xx = np.mgrid[:256, :256]
        wave = 110 + 5 * np.sin(xx * 2*np.pi/30) * np.sin(yy * 2*np.pi/30)
        rgb = np.repeat(np.rint(wave)[:, :, None], 3, axis=2).astype("uint8")
        result = run(Image.fromarray(rgb))
        codes = [i["code"] for i in result["issues"]]
        self.assertIn("mottle_above_reference_bound", codes)
        self.assertNotIn("grain_above_reference_bound", codes)

    def test_translucent_surface_is_detected_without_hiding_rgb_metrics(self):
        result = run(Image.new("RGBA", (256, 256), (80, 100, 120, 128)))
        self.assertIn("translucent_interior", [i["code"] for i in result["issues"]])
        self.assertGreater(result["regions"][0]["texture"]["sample_pixels"], 1000)
        self.assertAlmostEqual(result["regions"][0]["opacity"]["translucent_fraction"], 1)

    def test_extra_color_islands_break_a_declared_smooth_surface(self):
        image = Image.new("RGB", (256, 256), (65, 75, 95))
        draw = ImageDraw.Draw(image)
        draw.polygon([(70, 70), (100, 78), (78, 101)], fill=(130, 150, 170))
        draw.ellipse((150, 145, 177, 164), fill=(125, 145, 165))
        result = run(image)
        self.assertIn("unexpected_color_islands_in_declared_smooth_field", [i["code"] for i in result["issues"]])
        self.assertGreaterEqual(result["regions"][0]["color_islands"]["count"], 2)

    def test_highlight_evidence_is_not_automatically_bad_art(self):
        image = Image.new("RGB", (256, 256), (40, 85, 105))
        ImageDraw.Draw(image).ellipse((65, 67, 95, 85), fill=(220, 230, 190))
        result = run(image, contract("evidence_only"))
        self.assertGreater(result["regions"][0]["color_islands"]["count"], 0)
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["regions"][0]["status"], "evidence_only")

    def test_normal_antialias_edge_and_hidden_rgb_are_not_fringes(self):
        big = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        ImageDraw.Draw(big).ellipse((70, 70, 954, 954), fill=(40, 90, 140, 255))
        aa = big.resize((256, 256), Image.Resampling.LANCZOS)
        result = run(aa, {"schema": paint.SCHEMA, "long_edge": 256, "regions": [
            {"id": "disc-interior", "bbox": [.3, .3, .7, .7], "expectation": "opaque_surface"}]})
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["global_alpha_evidence"]["suspected_fringe_pixels"], 0)
        pixels = np.array(aa)
        pixels[pixels[:, :, 3] == 0, :3] = [255, 0, 255]
        hidden = run(Image.fromarray(pixels), {"schema": paint.SCHEMA, "long_edge": 256})
        self.assertEqual(hidden["global_alpha_evidence"]["suspected_fringe_pixels"], 0)

    def test_no_region_is_evidence_only_and_bad_contract_is_not_silently_accepted(self):
        image = Image.new("RGB", (256, 256), "white")
        report = run(image, {})
        self.assertEqual(report["regions"][0]["status"], "evidence_only")
        broken = contract()
        broken["regions"][0]["bbox"] = [1, 0, 0, 1]
        with self.assertRaises(ValueError):
            run(image, broken)

    def test_foreign_colored_alpha_edge_produces_advisory_fringe_evidence(self):
        image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((20, 20, 235, 235), fill=(255, 0, 255, 128))
        draw.ellipse((23, 23, 232, 232), fill=(40, 90, 140, 255))
        result = run(image, {})
        self.assertGreater(result["global_alpha_evidence"]["suspected_fringe_pixels"], 100)
        self.assertTrue(result["global_alpha_evidence"]["fringe_is_advisory"])
        self.assertEqual(result["visual_acceptance"], "not_assessed")

    def test_explicit_mask_selects_clean_or_corrupted_paint_in_the_same_image(self):
        pixels = np.full((256, 256, 3), 110, dtype=np.uint8)
        rng = np.random.default_rng(7921)
        pixels[35:115, 35:115] = np.uint8(110 + rng.integers(-15, 16, (80, 80, 3)))
        image = Image.fromarray(pixels)
        damaged, clean = np.zeros((256, 256), bool), np.zeros((256, 256), bool)
        damaged[40:110, 40:110] = True
        clean[145:225, 145:225] = True
        specification = {"schema": paint.SCHEMA, "long_edge": 256, "regions": [
            {"id": "material", "mask_id": "surface", "expectation": "smooth_field"}]}
        good, good_maps = paint.analyze_image(image, specification, {"surface": clean})
        bad, _ = paint.analyze_image(image, specification, {"surface": damaged})
        self.assertEqual(good["issues"], [])
        self.assertIn("grain_above_reference_bound", [i["code"] for i in bad["issues"]])
        self.assertEqual(good["regions"][0]["geometry"], {"mask_id": "surface"})
        self.assertTrue(np.array_equal(good_maps["regions"]["material"], clean))
        with tempfile.TemporaryDirectory() as folder:
            paint.save_evidence(folder, good, good_maps, specification)
            with Image.open(Path(folder) / "region-00.png") as saved:
                self.assertTrue(np.array_equal(np.asarray(saved) > 0, clean))

    def test_explicit_mask_contract_rejects_ambiguity_missing_size_type_and_empty(self):
        image = Image.new("RGB", (256, 256), (90, 90, 90))
        base = {"id": "material", "mask_id": "surface", "expectation": "smooth_field"}
        variants = [
            ({**base, "bbox": [0, 0, 1, 1]}, {"surface": np.ones((256, 256), bool)}, "exactly one"),
            ({**base, "polygon": [[0, 0], [1, 0], [1, 1]]}, {"surface": np.ones((256, 256), bool)}, "exactly one"),
            (base, {}, "unknown region mask"),
            (base, {"surface": np.ones((128, 256), bool)}, "dimensions"),
            (base, {"surface": np.ones((256, 256), dtype=np.uint8)}, "boolean"),
            (base, {"surface": np.zeros((256, 256), bool)}, "empty"),
        ]
        for region, masks, message in variants:
            with self.subTest(message=message, keys=list(region)):
                with self.assertRaisesRegex(ValueError, message):
                    paint.analyze_image(image, {"regions": [region]}, masks)

    def test_explicit_mask_tracks_image_reduction_without_softening_edges(self):
        image = Image.new("RGB", (512, 256), (90, 100, 110))
        mask = np.zeros((256, 512), bool)
        mask[64:192, 128:384] = True
        specification = {"long_edge": 256, "regions": [
            {"id": "material", "mask_id": "surface", "expectation": "smooth_field"}]}
        result, maps = paint.analyze_image(image, specification, {"surface": mask})
        self.assertEqual(result["analysis_size"], [256, 128])
        expected = np.zeros((128, 256), bool)
        expected[32:96, 64:192] = True
        self.assertTrue(np.array_equal(maps["regions"]["material"], expected))
        self.assertEqual(result["issues"], [])
        disappearing = np.zeros_like(mask)
        disappearing[0, 0] = True
        with self.assertRaisesRegex(ValueError, "became empty"):
            paint.analyze_image(image, specification, {"surface": disappearing})

    def test_real_images_preserve_reference_gradients_and_reject_circled_mottling(self):
        # These are the actual user/reference PNGs, not rendered surrogates or
        # fixtures synthesized by the detector. This also exercises report I/O.
        source = SOURCE.with_name("reference_paint_regression.py")
        spec = importlib.util.spec_from_file_location("real_paint_regression", source)
        regression = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(regression)
        with tempfile.TemporaryDirectory() as folder:
            report = regression.run_reference_regression(SOURCE.parents[1], folder)
            self.assertTrue(report["ok"], report["failures"])
            self.assertTrue((Path(folder) / "report.json").is_file())
            self.assertEqual(report["frozen_rules"]["mottle_rms_max"], 0.5)
            cases = {case["id"]: case for case in report["cases"]}
            for name in ("r1", "short-blue", "short-black", "full-teal"):
                self.assertEqual(cases[name]["actual_codes"], [])
                self.assertEqual(len(cases[name]["source_sha256"]), 64)
            full = {r["id"]: r for r in cases["full-circled-source"]["regions"]}
            for name in ("circled-upper-field", "circled-lower-field"):
                self.assertIn("mottle_above_reference_bound", full[name]["actual_codes"])
                self.assertGreater(full[name]["texture"]["mottle_rms_0_255"], 0.5)
                self.assertIn("bbox", full[name])
            short = cases["user-defect"]
            self.assertTrue(short["limitations"])
            self.assertNotIn("mottle_above_reference_bound", short["actual_codes"])
            self.assertEqual(short["visual_acceptance"], "not_assessed")


if __name__ == "__main__":
    unittest.main()
