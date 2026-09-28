"""Artifact evidence tests with actual encoded and decoded image changes."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("write_ci_evidence", ROOT / "tools/write_ci_evidence.py")
evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evidence)
HAS_PILLOW = importlib.util.find_spec("PIL") is not None


@unittest.skipUnless(HAS_PILLOW, "install optional requirements-ci.txt for PNG evidence tests")
class EvidenceTests(unittest.TestCase):
    def make_run(self, root, status="pass"):
        from PIL import Image
        report = {"schema": "aikon.visual-e2e.v1", "status": status, "profiles": {}, "profile_sha256": {},
                  "controls": {"status": "pass", "cases": [{"expectation_met": True}, {"expectation_met": True}]},
                  "reference_regression": {"status": "passed", "cases": [{"expectation_met": True}]},
                  "visual_review": "not_assessed", "user_acceptance": "not_claimed"}
        for profile, color in (("short", (24, 48, 72, 255)), ("full", (36, 60, 84, 255))):
            folder = root / profile
            folder.mkdir(parents=True)
            svg = ('<svg xmlns="http://www.w3.org/2000/svg"><title>' + profile + '</title></svg>').encode()
            (folder / "icon.svg").write_bytes(svg)
            digest = hashlib.sha256(svg).hexdigest()
            report["profiles"][profile] = {"status": "no_rule_failure", "compile": {"svg_sha256": digest}}
            report["profile_sha256"][profile] = digest
            for size in (1024, 128, 48, 24):
                Image.new("RGBA", (size, size), color).save(folder / ("icon-" + str(size) + ".png"))
        (root / "report.json").write_text(json.dumps(report), encoding="utf-8")
        return report

    def invoke(self, root, summary=None):
        arguments = ["--input", str(root), "--artifact-upload-outcome", "failure", "--worker"]
        if summary:
            arguments += ["--summary", str(summary)]
        output = io.StringIO()
        with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": ""}), contextlib.redirect_stdout(output):
            code = evidence.main(arguments)
        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("AIKON_EVIDENCE "))
        return code, json.loads(lines[0].removeprefix("AIKON_EVIDENCE "))

    def test_complete_real_files_preserve_status_upload_failure_and_counts(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            report = self.make_run(root)
            summary = root / "summary.md"
            code, manifest = self.invoke(root, summary)
            self.assertEqual(code, 0)
            self.assertEqual(manifest["status"], report["status"])
            self.assertEqual(manifest["artifact_upload_outcome"], "failure")
            self.assertTrue(manifest["evidence_complete"])
            self.assertEqual(manifest["controls"]["count"], 2)
            self.assertEqual(manifest["real_references"]["count"], 1)
            self.assertEqual(manifest["visual_review"], "not_claimed")
            self.assertEqual(manifest["user_acceptance"], "not_claimed")
            png = manifest["profiles"]["short"]["pngs"]["24"]
            path = root / png["path"]
            self.assertEqual(png["png_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            with Image.open(path) as image:
                expected = hashlib.sha256(b"RGBA:24x24:" + image.convert("RGBA").tobytes()).hexdigest()
            self.assertEqual(png["decoded_rgba_sha256"], expected)
            self.assertTrue(summary.exists())

    def test_missing_or_corrupt_png_invalidates_a_successful_report(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.make_run(root)
            missing = root / "full/icon-48.png"
            missing.unlink()
            code, manifest = self.invoke(root)
            self.assertNotEqual(code, 0)
            self.assertEqual(manifest["status"], "pass")
            self.assertFalse(manifest["evidence_complete"])
            self.assertIn({"file": "full/icon-48.png", "code": "missing_png"}, manifest["issues"])
            missing.write_bytes(b"\x89PNG\r\n\x1a\nBROKEN")
            code, manifest = self.invoke(root)
            self.assertNotEqual(code, 0)
            self.assertEqual(manifest["profiles"]["full"]["pngs"]["48"]["status"], "invalid")
            self.assertNotIn("decoded_rgba_sha256", manifest["profiles"]["full"]["pngs"]["48"])

    def test_encoding_changes_only_byte_hash_but_pixel_changes_decode_hash(self):
        from PIL import Image, PngImagePlugin
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.make_run(root)
            path = root / "short/icon-24.png"
            first = evidence.build_manifest(root)["profiles"]["short"]["pngs"]["24"]
            with Image.open(path) as original:
                image = original.copy()
            metadata = PngImagePlugin.PngInfo()
            metadata.add_text("encoding_note", "same pixels, different container")
            image.save(path, pnginfo=metadata, compress_level=0)
            recoded = evidence.build_manifest(root)["profiles"]["short"]["pngs"]["24"]
            self.assertNotEqual(first["png_sha256"], recoded["png_sha256"])
            self.assertEqual(first["decoded_rgba_sha256"], recoded["decoded_rgba_sha256"])
            image.putpixel((3, 7), (25, 48, 72, 255))
            image.save(path)
            changed = evidence.build_manifest(root)["profiles"]["short"]["pngs"]["24"]
            self.assertNotEqual(first["decoded_rgba_sha256"], changed["decoded_rgba_sha256"])

    def test_missing_and_failed_reports_are_never_promoted_to_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            code, manifest = self.invoke(root)
            self.assertNotEqual(code, 0)
            self.assertEqual(manifest["report_file_status"], "missing")
            self.assertIsNone(manifest["status"])
            self.assertIsNone(manifest["controls"]["count"])
            self.make_run(root, status="fail")
            code, manifest = self.invoke(root)
            self.assertNotEqual(code, 0)
            self.assertEqual(manifest["status"], "fail")
            self.assertTrue(manifest["evidence_complete"])

    def test_svg_drift_and_wrong_png_dimensions_are_evidence_failures(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.make_run(root)
            svg = root / "short/icon.svg"
            svg.write_bytes(svg.read_bytes() + b"\n")
            Image.new("RGBA", (32, 32)).save(root / "full/icon-24.png")
            code, manifest = self.invoke(root)
            self.assertNotEqual(code, 0)
            self.assertIn({"file": "short/icon.svg", "code": "svg_differs_from_report"}, manifest["issues"])
            self.assertIn({"file": "full/icon-24.png", "code": "invalid_or_undecodable_png"}, manifest["issues"])


if __name__ == "__main__":
    unittest.main()
