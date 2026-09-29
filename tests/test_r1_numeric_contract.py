"""Independent positive/negative controls for the user's selected B contract."""
import unittest
from unittest.mock import patch
import subprocess
from pathlib import Path
import numpy as np
from tools.r1_numeric_contract import load_contract, measure_arrays, evaluate_svg, main


class R1NumericContractTests(unittest.TestCase):
    def setUp(self):
        self.contract, _ = load_contract()
        self.reference = np.full((128, 128, 4), (15, 15, 15, 255), dtype=np.uint8)
        self.subject = np.zeros((128, 128), dtype=bool)
        self.subject[24:104, 24:104] = True
        self.reference[self.subject] = (90, 120, 180, 255)
        self.candidate = self.reference.copy()
        self.candidate[~self.subject] = (0, 0, 0, 0)
        self.regions = {"critical_bow": np.zeros_like(self.subject)}
        self.regions["critical_bow"][40:60, 40:60] = True

    def measure(self, candidate=None):
        return measure_arrays(self.reference, self.candidate if candidate is None else candidate, self.subject, self.regions, self.contract)

    def test_exact_subject_on_transparent_canvas_passes_numeric_only(self):
        report = self.measure()
        self.assertEqual(report["numeric_status"], "pass")
        self.assertEqual(report["color_metrics"]["subject"]["hit_fraction"], 1)
        self.assertEqual(report["overall_artwork_acceptance"], "not_assessed")
        self.assertEqual(report["user_acceptance"], "not_assessed")

    def test_background_rgb_is_entirely_irrelevant_when_transparent(self):
        before = self.measure()
        self.candidate[~self.subject, :3] = (251, 0, 163)
        self.reference[~self.subject, :3] = (233, 255, 32)
        self.assertEqual(before, self.measure())

    def test_opaque_source_background_cannot_be_delivered_as_transparent_svg(self):
        report = self.measure(self.reference)
        self.assertEqual(report["color_metrics"]["subject"]["hit_fraction"], 1)
        self.assertEqual(report["numeric_status"], "fail")
        self.assertGreater(report["transparency"]["nonzero_alpha_pixels"], 0)

    def test_small_critical_defect_cannot_hide_inside_good_global_average(self):
        self.candidate[43:48, 43:48, 0] += 6
        report = self.measure()
        self.assertGreater(report["color_metrics"]["subject"]["hit_fraction"], .99)
        self.assertLess(report["color_metrics"]["critical_bow"]["hit_fraction"], .99)
        self.assertEqual(report["numeric_status"], "fail")

    def test_five_is_inclusive_but_six_is_not_in_pixel_hit_rule(self):
        self.candidate[43:48, 43:48, 0] += 5
        report = self.measure()
        self.assertEqual(report["numeric_status"], "pass")
        self.assertEqual(report["color_metrics"]["critical_bow"]["hit_fraction"], 1)
        self.candidate[43:48, 43:48, 0] += 1
        self.assertEqual(self.measure()["numeric_status"], "fail")

    def test_pixel_hits_do_not_cancel_global_color_bias(self):
        self.candidate[self.subject, :3] += 4
        report = self.measure()
        self.assertEqual(report["color_metrics"]["subject"]["hit_fraction"], 1)
        self.assertEqual(report["numeric_status"], "fail")
        self.assertIn("subject.mae_srgb8", [c["id"] for c in report["checks"] if not c["passed"]])

    def test_tiny_alpha_contamination_outside_subject_is_caught(self):
        self.candidate[3, 3] = (245, 100, 40, 1)
        report = self.measure()
        self.assertEqual(report["color_metrics"]["subject"]["hit_fraction"], 1)
        self.assertEqual(report["transparency"]["nonzero_alpha_pixels"], 1)
        self.assertEqual(report["numeric_status"], "fail")

    def test_small_remote_silhouette_fragment_cannot_hide_in_iou(self):
        self.candidate[4:7, 4:7] = (90, 120, 180, 255)
        report = self.measure()
        self.assertGreater(report["silhouette"]["iou"], .995)
        self.assertGreater(report["silhouette"]["boundary"]["symmetric_max_px"], 8)
        self.assertEqual(report["numeric_status"], "fail")

    def test_missing_or_empty_critical_region_never_passes(self):
        for regions in ({}, {"empty": np.zeros_like(self.subject)}):
            with self.assertRaises(ValueError):
                measure_arrays(self.reference, self.candidate, self.subject, regions, self.contract)

    def test_implicit_resampling_or_float_scale_is_rejected(self):
        for candidate in (self.candidate[::2, ::2], self.candidate.astype(float)):
            with self.assertRaises(ValueError):
                self.measure(candidate)

    def test_contract_byte_tampering_is_rejected(self):
        with patch("tools.r1_numeric_contract.CONTRACT_PATH") as path:
            path.read_bytes.return_value = b'{"thresholds": {"hit_fraction": 0.1}}'
            with self.assertRaisesRegex(ValueError, "Frozen B contract changed"):
                load_contract()

    def test_reference_hash_tampering_is_rejected_before_candidate_read(self):
        contract = dict(self.contract, reference_sha256="0" * 64)
        with patch("tools.r1_numeric_contract.load_contract", return_value=(contract, "test")):
            with self.assertRaisesRegex(ValueError, "Frozen source changed"):
                evaluate_svg(Path("never-read.svg"), Path("never-written"))

    def test_source_mask_tampering_is_rejected_before_candidate_read(self):
        contract = dict(self.contract, source_mask_sha256="0" * 64)
        with patch("tools.r1_numeric_contract.load_contract", return_value=(contract, "test")):
            with self.assertRaisesRegex(ValueError, "Frozen source foreground changed"):
                evaluate_svg(Path("never-read.svg"), Path("never-written"))

    def test_cli_propagates_worker_result_and_labels_timeout(self):
        argv = ["r1_numeric_contract.py", "--candidate", "not-read.svg", "--output", "not-written"]
        with patch("sys.argv", argv):
            for status in (0, 2):
                with patch("tools.run_visual_e2e.run_bounded", return_value=status):
                    self.assertEqual(main(), status)
            with patch("tools.run_visual_e2e.run_bounded", side_effect=subprocess.TimeoutExpired("owned", 45)):
                self.assertEqual(main(), 124)


if __name__ == "__main__":
    unittest.main()
