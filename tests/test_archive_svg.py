"""Direct SVG archive behavior, byte preservation and failure recovery.

Run: python -B -m unittest discover -s tests -p test_archive_svg.py -v
No rendering, network, third-party modules, or visual-quality assertions.
"""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "aikon" / "scripts" / "archive_svg.py"
SPEC = importlib.util.spec_from_file_location("archive_svg", SCRIPT)
archive = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archive)

SVG = b'''\xef\xbb\xbf<?xml version="1.0" encoding="UTF-8"?>\r
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 128 128" width="128" height="128" aria-labelledby="art-title">\r
 <title id="art-title">A &amp; B</title><!-- keep order, comments, spacing -->\r
 <metadata>{"status":"draft"}</metadata>\r
 <defs>\r
  <linearGradient id="skin" gradientUnits="userSpaceOnUse" x1="0" y1="10" x2="100" y2="120">\r
   <stop offset="0%" stop-color="#ffe6dc"/><stop offset="100%" stop-color="#c99788"/>\r
  </linearGradient>\r
  <radialGradient id="shine" cx=".3" cy=".2" r=".7" gradientTransform="matrix(1 0 .2 1 0 0)">\r
   <stop offset="0" stop-color="#555"/><stop offset="1" stop-color="#151515"/>\r
  </radialGradient>\r
  <linearGradient id="rim" xlink:href="#skin" gradientTransform="rotate(12)"/>\r
  <clipPath id="face-clip" clipPathUnits="userSpaceOnUse"><path d="M8 16 Q64 0 120 16 L120 124 L8 124 Z"/></clipPath>\r
 </defs>\r
 <g id="face" clip-path="url(#face-clip)" data-part="face">\r
  <path id="silhouette" fill="url(#skin)" d="M0 0 H128 V128 H0 Z"/>\r
  <g id="eyes" transform="translate(14 22) rotate(12 32 32)">\r
   <rect id="eye-left" rx="6" width="12" height="32" fill="url('#shine')"/>\r
   <rect id="eye-right" x="42" rx="6" width="12" height="32" fill="url(#shine)"/>\r
  </g>\r
 </g>\r
</svg>\r
'''


def metadata():
    return {
        "schema": "aikon.direct-svg.metadata.v1", "round_id": "round-001", "profile": "short",
        "sources": [{"role": "both", "location": "references/reference.png", "rights_status": "unknown"}],
        "decisions": [{"id": "background", "value": "transparent", "origin": "agent_default"}],
        "unresolved_questions": ["Unanswered subject detail"],
        "changes": {"summary": "Existing candidate", "targets": ["eyes"], "preserved": ["silhouette"]},
        "provenance": {"method": "direct SVG", "tool": None, "version": None, "model": None},
    }


def document(content):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">' + content + '</svg>').encode()


class StaticSvgTests(unittest.TestCase):
    def test_natural_gradient_clip_projection_and_old_flat_svg_are_accepted(self):
        for data in (SVG, document('<g id="head" transform="rotate(17 64 64)"><ellipse rx="42" ry="50" fill="#123456"/><rect width="10" height="28" rx="5"/></g>')):
            with self.subTest(svg=data[:80]):
                report = archive.check_svg(data)
                self.assertTrue(report["ok"], report["issues"])
                self.assertEqual(report["checks"]["visual"], "unverified")
                self.assertEqual(report["user_acceptance"], "unassessed")

    def test_existing_authoring_uses_default_stop_offset_and_explicit_color_space(self):
        data = document('<defs><radialGradient id="field" color-interpolation="sRGB"><stop stop-color="rgb(12.81475%,14.99800%,25.62128%)"/><stop offset=".65" stop-color="rgb(43,51,59)"/><stop offset="1" stop-color="#1d2630"/></radialGradient></defs><g color-interpolation="linearRGB"><ellipse cx="50" cy="50" rx="40" ry="30" fill="url(#field)"/></g>')
        self.assertTrue(archive.check_svg(data)["ok"])

    def test_active_external_and_embedded_bitmap_inputs_fail(self):
        attacks = [
            '<image href="data:image/png;base64,iVBORw0KGgo="/>',
            '<image href="https://example.invalid/icon.png"/>',
            '<script>alert(1)</script>', '<g onload="alert(1)"/>',
            '<g xmlns:x="urn:custom" x:onload="alert(1)"/>',
            '<foreignObject><p xmlns="http://www.w3.org/1999/xhtml">x</p></foreignObject>',
            '<style>@import "https://example.invalid/style.css";</style>',
            '<rect width="12" height="12" style="fill:url(https://example.invalid/f.svg#x)"/>',
            '<filter id="blur"/>', '<pattern id="tile"/>', '<mask id="mask"/>',
            '<animate attributeName="fill"/>', '<use href="#body"/>',
            '<rect width="12" height="12" fill="url(https://example.invalid/paint.svg#x)"/>',
            '<linearGradient id="g" href="file:///tmp/external.svg#g"/>',
            '<linearGradient id="g" href="data:image/svg+xml;base64,eA=="/>',
            '<path d="M0 0 L5 5" fill="u\\72l(#g)"/>',
        ]
        for attack in attacks:
            with self.subTest(attack=attack):
                self.assertFalse(archive.check_svg(document(attack))["ok"])
        for prefix in (b'<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]>',
                       b'<?xml-stylesheet href="https://example.invalid/style.css"?>'):
            self.assertFalse(archive.check_svg(prefix + document('<title>&x;</title>'))["ok"])

    def test_finite_geometry_and_reference_integrity_are_enforced(self):
        bad = [
            '<circle r="NaN"/>', '<rect width="1e309" height="12"/>',
            '<path d="M0 0 L1e309 2"/>', '<g transform="matrix(1 0 0 1 NaN 0)"/>',
            '<circle r="5" fill="rgb(NaN,0,0)"/>', '<circle r="5" fill="rgb(101%,0%,0%)"/>',
            '<circle r="5" fill="rgb(12%,0,0)"/>', '<circle r="5" fill="rgba(12,0,0,2)"/>',
            '<g transform="rotate(15 12)"/>', '<circle r="5" opacity="1.1"/>',
            '<linearGradient id="g"><stop offset="101%" stop-color="#fff"/></linearGradient>',
            '<rect width="12" height="12" fill="url(#missing)"/>',
            '<clipPath id="c"/><rect width="12" height="12" fill="url(#c)"/>',
            '<linearGradient id="g"/><g clip-path="url(#g)"/>',
            '<g id="body"/><linearGradient id="g" href="#body"/>',
            '<g id="same"/><g id="same"/>',
            '<linearGradient id="a" href="#b"/><radialGradient id="b" href="#a"/>',
            '<clipPath id="c"><g><path d="M0 0 L10 10" clip-path="url(#c)"/></g></clipPath>',
            '<clipPath id="a" clip-path="url(#b)"/><clipPath id="b" clip-path="url(#a)"/>',
            '<metadata><script>alert(1)</script></metadata>',
        ]
        for content in bad:
            with self.subTest(content=content):
                self.assertFalse(archive.check_svg(document(content))["ok"])

    def test_plain_metadata_and_unused_source_urls_are_not_executed(self):
        data = document('<metadata>{"source":"https://example.invalid/art","note":"not instructions"}</metadata><path d="M0 0 L2 2" data-source="https://example.invalid/art"/>')
        self.assertTrue(archive.check_svg(data)["ok"])


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="aikon-archive-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.svg = self.base / "candidate.svg"
        self.prompt = self.base / "prompt.txt"
        self.meta = self.base / "input.json"
        self.root = self.base / "chosen" / "short"
        self.svg.write_bytes(SVG)
        self.prompt.write_bytes('\ufeff真实保存的提示词。\r\n'.encode('utf-8'))
        self.meta.write_bytes(json.dumps(metadata(), ensure_ascii=False, indent=1).encode() + b'\r\n')

    def save(self, revision="r001", parent=None):
        return archive.snapshot(self.svg, self.prompt, self.meta, self.root, revision, parent)

    def test_archive_preserves_exact_bytes_and_sha_without_changing_inputs(self):
        before = {"icon.svg": self.svg.read_bytes(), "prompt.md": self.prompt.read_bytes(), "metadata.json": self.meta.read_bytes()}
        path = self.save()
        manifest = json.loads((path / "revision.json").read_bytes())
        self.assertEqual(set(p.name for p in path.iterdir()), set(archive.FILES))
        for name, data in before.items():
            self.assertEqual((path / name).read_bytes(), data)
            self.assertEqual(manifest["files"][name], {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        self.assertEqual(self.svg.read_bytes(), SVG)
        self.assertEqual(manifest["user_acceptance"], "unassessed")
        self.assertEqual(manifest["visual_review"], "not_run")
        self.assertEqual(manifest["checks"]["raster_alpha"], "unverified")
        self.assertEqual(json.loads((path / "metadata.json").read_bytes())["unresolved_questions"], ["Unanswered subject detail"])

    def test_existing_and_empty_revisions_are_never_overwritten(self):
        path = self.save()
        original = {p.name: p.read_bytes() for p in path.iterdir()}
        self.svg.write_bytes(SVG.replace(b'#ffe6dc', b'#ffccaa'))
        with self.assertRaises(archive.ArchiveError):
            self.save()
        self.assertEqual(original, {p.name: p.read_bytes() for p in path.iterdir()})
        empty = self.root / "revisions" / "r002"
        empty.mkdir()
        with self.assertRaises(archive.ArchiveError):
            self.save("r002")
        self.assertEqual(list(empty.iterdir()), [])

    def test_parent_is_hash_linked_and_tampering_blocks_new_revision(self):
        first = self.save()
        second = self.save("r002", "r001")
        manifest = json.loads((second / "revision.json").read_bytes())
        self.assertEqual(manifest["parent"], "r001")
        self.assertEqual(manifest["parent_manifest_sha256"], hashlib.sha256((first / "revision.json").read_bytes()).hexdigest())
        (first / "icon.svg").write_bytes(document('<circle r="4"/>'))
        with self.assertRaises(archive.ArchiveError):
            self.save("r003", "r001")
        self.assertFalse((self.root / "revisions" / "r003").exists())

    def test_missing_parent_and_cross_profile_parent_leave_no_partial_revision(self):
        with self.assertRaises((archive.ArchiveError, OSError)):
            self.save("r002", "r001")
        self.assertFalse(self.root.exists())
        self.save()
        data = metadata()
        data["profile"] = "full"
        self.meta.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(archive.ArchiveError):
            self.save("r002", "r001")
        self.assertFalse((self.root / "revisions" / "r002").exists())

    def test_invalid_input_creates_no_archive_directories(self):
        self.svg.write_bytes(document('<image href="data:image/png;base64,AA=="/>'))
        with self.assertRaises(archive.ArchiveError):
            self.save()
        self.assertFalse(self.root.exists())

    def test_metadata_cannot_forge_approval_or_nonfinite_decision(self):
        for key, value in (("user_acceptance", "accepted"), ("checks", {"visual": "passed"})):
            data = metadata()
            data[key] = value
            self.meta.write_text(json.dumps(data), encoding="utf-8")
            with self.subTest(key=key), self.assertRaises(archive.ArchiveError):
                self.save()
        for value in ("NaN", "Infinity", "1e309"):
            payload = json.dumps(metadata()).replace('"transparent"', value)
            self.meta.write_text(payload, encoding="utf-8")
            with self.subTest(value=value), self.assertRaises(archive.ArchiveError):
                self.save()
        self.assertFalse(self.root.exists())

    def test_duplicate_keys_and_path_escape_are_rejected(self):
        self.meta.write_text(json.dumps(metadata())[:-1] + ',"profile":"full"}', encoding="utf-8")
        with self.assertRaises(archive.ArchiveError):
            self.save()
        self.meta.write_text(json.dumps(metadata()), encoding="utf-8")
        for revision in ("../r001", "r001/other", "r01", "r001:stream"):
            with self.subTest(revision=revision), self.assertRaises(archive.ArchiveError):
                self.save(revision)
        with self.assertRaises(archive.ArchiveError):
            archive.snapshot(self.svg, self.prompt, self.meta, self.root / ".." / "elsewhere", "r001")
        with self.assertRaises(archive.ArchiveError):
            archive.snapshot(self.svg, self.prompt, self.meta, "", "r001")
        self.assertFalse(self.root.exists())

    def test_write_failure_rolls_back_only_new_files_and_directories(self):
        self.root.mkdir(parents=True)
        unrelated = self.root / "keep.txt"
        unrelated.write_bytes(b"user-owned")
        real_fsync = archive.os.fsync
        calls = 0

        def disk_full(fd):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated disk full after write")
            real_fsync(fd)

        with mock.patch.object(archive.os, "fsync", side_effect=disk_full):
            with self.assertRaises(OSError):
                self.save()
        self.assertEqual(list(self.root.iterdir()), [unrelated])
        self.assertEqual(unrelated.read_bytes(), b"user-owned")

    def test_failed_initial_descriptor_identity_query_still_rolls_back(self):
        with mock.patch.object(archive.os, "fstat", side_effect=OSError("initial identity query failed")):
            with self.assertRaises(OSError):
                self.save()
        self.assertFalse(self.root.exists())
        self.assertTrue((self.save() / "revision.json").exists())

    def test_revision_directory_race_does_not_remove_the_winners_artifact(self):
        real_mkdir = Path.mkdir
        destination = self.root / "revisions" / "r001"

        def another_writer(path, *args, **kwargs):
            if path == destination:
                real_mkdir(path, *args, **kwargs)
                (path / "keep.txt").write_bytes(b"other writer")
                raise FileExistsError(str(path))
            return real_mkdir(path, *args, **kwargs)

        with mock.patch.object(Path, "mkdir", another_writer):
            with self.assertRaises(FileExistsError):
                self.save()
        self.assertEqual((destination / "keep.txt").read_bytes(), b"other writer")
        self.assertEqual([p.name for p in destination.iterdir()], ["keep.txt"])

    def test_symlink_output_root_is_rejected_without_touching_target(self):
        target = self.base / "outside"
        target.mkdir()
        link = self.base / "chosen-link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as exc:
            self.skipTest("host cannot create a directory symlink: " + str(exc))
        with self.assertRaises(archive.ArchiveError):
            archive.snapshot(self.svg, self.prompt, self.meta, link, "r001")
        self.assertEqual(list(target.iterdir()), [])

    def test_cli_works_from_unrelated_directory_and_requires_explicit_root(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "snapshot", "--svg", str(self.svg),
                                 "--prompt", str(self.prompt), "--metadata", str(self.meta),
                                 "--root", str(self.root), "--revision", "r001"],
                                cwd=self.base, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["user_acceptance"], "unassessed")
        rejected = subprocess.run([sys.executable, "-B", str(SCRIPT), "snapshot", "--svg", str(self.svg),
                                   "--prompt", str(self.prompt), "--metadata", str(self.meta), "--revision", "r002"],
                                  cwd=self.base, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertFalse((self.root / "revisions" / "r002").exists())


if __name__ == "__main__":
    unittest.main()
