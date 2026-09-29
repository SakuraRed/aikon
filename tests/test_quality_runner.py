"""Evidence lifecycle controls: failures cannot reuse a historical green result."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import run_image_quality as runner


class EvidenceLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.context = {"input_sha256": "current", "github_run_id": "1"}
        self.patch = mock.patch.object(runner, "execution_context", return_value=self.context)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def passed(self, mode, context=None):
        runner.save(self.root / (mode + ".json"), {"status": "pass", "context": context or self.context, "invocation": mode + "-latest", "artwork_acceptance": "rejected_by_user"})

    def summary(self):
        with mock.patch.dict(runner.os.environ, {"GITHUB_STEP_SUMMARY": ""}), contextlib.redirect_stdout(io.StringIO()):
            code = runner.publish_summary(self.root, "failure")
        return code, json.loads((self.root / "ci-summary.json").read_text(encoding="utf-8"))

    def test_early_stage_exception_cannot_reuse_prior_pass(self):
        self.passed("tests")
        self.passed("audit")
        invocation = runner.begin_stage(self.root, "tests", self.context)
        with mock.patch.object(runner, "run_tests", side_effect=ImportError("missing detector")), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runner.execute_stage(self.root, "tests", invocation, self.context), 1)
        code, summary = self.summary()
        self.assertEqual(code, 1)
        self.assertEqual(summary["stage_status"]["tests"], "error")

    def test_running_timeout_and_changed_inputs_are_not_green(self):
        self.passed("audit")
        invocation = runner.begin_stage(self.root, "tests", self.context)
        runner.save(self.root / "tests-supervision-failed.json", {"invocation": invocation, "status": "fail"})
        self.assertEqual(self.summary()[0], 1)
        self.passed("tests", {"input_sha256": "older", "github_run_id": "1"})
        self.assertEqual(self.summary()[1]["stage_status"]["tests"], "stale_or_unbound")

    def test_successful_detector_checks_preserve_rejected_human_verdict(self):
        self.passed("tests")
        self.passed("audit")
        code, summary = self.summary()
        self.assertEqual(code, 0)
        self.assertEqual(summary["artwork_acceptance"], "rejected_by_user")
        self.assertEqual(summary["artifact_upload"], "failure")
        self.assertEqual(summary["reference_similarity_99"], "not_assessed")

    def test_six_aliases_of_one_artwork_do_not_cover_six_rejected_artworks(self):
        entries = []
        for subject, profile in sorted(runner.EXPECTED_ARTWORKS):
            path = Path("outputs/fixtures") / subject / "round-002" / (profile + ".svg")
            source = self.root / path
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes((subject + profile).encode())
            entries.append({"subject": subject, "profile": profile, "path": path.as_posix(), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "user_verdict": "rejected"})
        ledger = self.root / "docs/validation/quality-v3/artwork-verdicts.json"
        runner.save(ledger, {"schema": "aikon.artwork-verdicts.v1", "artworks": entries})
        self.assertEqual(len(runner.rejected_artwork_records(self.root)), 6)
        for entry in entries[1:]:
            entry["path"] = entries[0]["path"]
            entry["sha256"] = entries[0]["sha256"]
        runner.save(ledger, {"schema": "aikon.artwork-verdicts.v1", "artworks": entries})
        with self.assertRaisesRegex(ValueError, "canonical"):
            runner.rejected_artwork_records(self.root)

    def test_missing_edge_positive_cannot_shrink_the_gate_silently(self):
        path = runner.ROOT / "docs/validation/edges-v3/run_audit.py"
        spec = importlib.util.spec_from_file_location("edge_fixture_audit_for_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        (self.root / "fixtures").mkdir()
        for name in module.REQUIRED_FIXTURES - {"sharp-corners.svg"}:
            (self.root / "fixtures" / name).write_text("<svg/>", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "incomplete"):
            module.validated_fixtures(self.root)


if __name__ == "__main__":
    unittest.main()
