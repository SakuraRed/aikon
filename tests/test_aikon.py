"""Contract tests: hostile inputs, preservation, and revision failure recovery.

Run: python -B -m unittest discover -s tests -v
These tests make no claim about visual acceptance or cross-harness behavior.
"""

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET


SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "aikon" / "scripts" / "aikon.py"
SPEC = importlib.util.spec_from_file_location("aikon_helper", SCRIPT)
aikon = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(aikon)
NS = {"s": "http://www.w3.org/2000/svg"}


def scene():
    return {
        "schema": "aikon.scene.v1",
        "title": 'A & B <test> "eyes" 图标',
        "background": "#242529",
        "head": {"angle": 17, "pivot": [256, 256]},
        "eyes": {"centers": [[115, 305], [270, 305]], "width": 29, "height": 81, "fill": "#18191b"},
        "layers": [
            {"id": "hair-back", "shapes": [
                {"tag": "path", "attrs": {"d": "M-40 120 Q190 0 420 120 L420 512 L-40 512 Z", "fill": "#382921"}}
            ]},
            {"id": "face", "shapes": [
                {"tag": "ellipse", "attrs": {"cx": 190, "cy": 325, "rx": 220, "ry": 245, "fill": "#f3c492"}}
            ]},
            {"id": "eyes"},
        ],
    }


class SceneTests(unittest.TestCase):
    def test_transparent_scene_has_no_background_or_fake_transparency_shape(self):
        source = scene()
        source["background"] = None
        svg = aikon.render_scene(source)
        root = ET.fromstring(svg)
        self.assertEqual([child.get("id") for child in root], [None, "head"])
        self.assertIsNone(root.find(".//*[@id='background']"))
        self.assertIsNone(root.find("s:rect", NS))
        self.assertIsNone(root.find(".//s:image", NS))
        self.assertIsNone(root.find(".//s:text", NS))
        self.assertEqual(svg, aikon.render_scene(copy.deepcopy(source)))
        result = aikon.check_svg(svg)
        self.assertTrue(result["ok"])
        self.assertEqual(result["background"], {
            "structural_status": "no_painted_canvas_rect_detected", "canvas_rects": [],
            "raster_alpha": "unverified",
        })

    def test_variant_metadata_does_not_silently_change_geometry(self):
        source = scene()
        source["background"] = None
        original = aikon.render_scene(source)
        for profile in ("short", "full"):
            source["variant"] = {"round_id": "round-001", "profile": profile}
            self.assertEqual(aikon.render_scene(source), original)

    def test_invalid_variant_and_claimed_validation_metadata_are_rejected(self):
        invalid_variants = [
            {"round_id": "../escape", "profile": "short"},
            {"round_id": "a/b", "profile": "short"},
            {"round_id": "has space", "profile": "full"},
            {"round_id": "含中文", "profile": "full"},
            {"round_id": "x" * 65, "profile": "short"},
            {"round_id": True, "profile": "short"},
            {"round_id": "round-001", "profile": "fuller"},
            {"round_id": "round-001", "profile": ["full"]},
            {"round_id": "round-001"},
            {"round_id": "round-001", "profile": "full", "checks": {"visual": "passed"}},
        ]
        for variant in invalid_variants:
            with self.subTest(variant=variant):
                source = scene()
                source["variant"] = variant
                with self.assertRaises(aikon.AikonError):
                    aikon.render_scene(source)
        source = scene()
        source["checks"] = {"visual": "passed", "raster_alpha": "passed"}
        with self.assertRaises(aikon.AikonError):
            aikon.render_scene(source)

    def test_deterministic_and_title_is_text_not_markup(self):
        source = scene()
        svg = aikon.render_scene(source)
        self.assertEqual(svg, aikon.render_scene(copy.deepcopy(source)))
        reordered = dict(reversed(list(source.items())))
        self.assertEqual(svg, aikon.render_scene(reordered))
        root = ET.fromstring(svg)
        self.assertEqual(root.find("s:title", NS).text, source["title"])
        self.assertIsNone(root.find(".//s:test", NS))
        self.assertIn(b"&amp;", svg)
        self.assertIn(b"&lt;test&gt;", svg)
        self.assertEqual(root.attrib["viewBox"], "0 0 512 512")
        self.assertEqual(aikon.check_svg(svg)["checks"], {"structural": "passed", "visual": "unverified"})

    def test_background_is_outside_rotation_and_layer_order_is_preserved(self):
        root = ET.fromstring(aikon.render_scene(scene()))
        self.assertEqual([child.get("id") for child in root], [None, "background", "head"])
        head = root.find("s:g", NS)
        self.assertEqual(head.get("transform"), "rotate(17 256 256)")
        self.assertEqual([child.get("id") for child in head], ["hair-back", "face", "eyes"])
        eyes = head.find("s:g[@id='eyes']", NS)
        self.assertEqual(len(eyes), 2)
        for attr in ("width", "height", "rx", "ry", "fill", "y"):
            self.assertEqual(eyes[0].get(attr), eyes[1].get(attr))

    def test_eye_spacing_edit_preserves_every_other_attribute_and_element(self):
        initial = scene()
        edited = copy.deepcopy(initial)
        edited["eyes"]["centers"][0][0] -= 10
        edited["eyes"]["centers"][1][0] += 10
        before, after = [ET.fromstring(aikon.render_scene(value)) for value in (initial, edited)]
        for eye_id, delta in (("eye-left", -10), ("eye-right", 10)):
            old = before.find(f".//s:rect[@id='{eye_id}']", NS)
            new = after.find(f".//s:rect[@id='{eye_id}']", NS)
            self.assertEqual(float(new.get("x")) - float(old.get("x")), delta)
            new.set("x", old.get("x"))
        self.assertEqual(ET.tostring(before), ET.tostring(after))

    def test_free_paths_and_all_supported_shapes_survive_export(self):
        value = scene()
        shapes = [
            {"tag": "path", "attrs": {"d": "M10 10 C20 5 30 5 40 10 S60 20 70 10 Q80 0 90 10 T110 10 A10 10 0 0 1 120 20 Z", "fill": "none", "stroke": "#abcdef"}},
            {"tag": "rect", "attrs": {"x": -4, "y": 3, "width": 12, "height": 15, "rx": 2}},
            {"tag": "circle", "attrs": {"cx": 100, "cy": 100, "r": 25}},
            {"tag": "ellipse", "attrs": {"rx": 10, "ry": 20}},
            {"tag": "polygon", "attrs": {"points": "1,2 3,4 5,6"}},
            {"tag": "polyline", "attrs": {"points": "1 2 3 4", "fill": "none"}},
            {"tag": "line", "attrs": {"x1": 1, "y1": 2, "x2": 3, "y2": 4, "stroke-width": 2, "stroke-linecap": "round"}},
        ]
        value["layers"].append({"id": "identity-detail", "shapes": shapes})
        svg = aikon.render_scene(value)
        root = ET.fromstring(svg)
        detail = root.find(".//s:g[@id='identity-detail']", NS)
        self.assertEqual(len(detail), 7)
        self.assertEqual(detail[0].get("d"), shapes[0]["attrs"]["d"])
        self.assertTrue(aikon.check_svg(svg)["ok"])

    def test_geometry_negative_controls(self):
        invalid = [
            ("angle", lambda s: s["head"].update(angle=14.99)),
            ("ratio", lambda s: s["eyes"].update(height=58)),
            ("width", lambda s: s["eyes"].update(width=0)),
            ("boolean", lambda s: s["head"].update(angle=True)),
            ("NaN", lambda s: s["head"].update(angle=float("nan"))),
            ("infinity", lambda s: s["head"].update(pivot=[float("inf"), 256])),
            ("x order", lambda s: s["eyes"].update(centers=[[270, 305], [115, 305]])),
            ("unequal y", lambda s: s["eyes"].update(centers=[[115, 300], [270, 305]])),
            ("three eyes", lambda s: s["eyes"].update(centers=[[1, 2], [3, 2], [4, 2]])),
            ("missing eyes", lambda s: s["layers"].pop()),
            ("duplicate eyes", lambda s: s["layers"].append({"id": "eyes"})),
            ("custom eyes", lambda s: s["layers"][-1].update(shapes=[{"tag": "circle", "attrs": {"r": 1}}])),
            ("reserved id", lambda s: s["layers"].append({"id": "eye-left", "shapes": []})),
            ("XML control", lambda s: s.update(title="bad\x01text")),
        ]
        for name, mutation in invalid:
            with self.subTest(name=name):
                value = scene()
                mutation(value)
                with self.assertRaises(aikon.AikonError):
                    aikon.render_scene(value)

    def test_overrides_are_explicit_scoped_and_do_not_allow_nonfinite_values(self):
        value = scene()
        value["head"]["angle"] = 12
        for override in ({"angle": True}, {"reason": " ", "angle": True}, {"reason": "approved", "angle": "true"}):
            value["style_overrides"] = override
            with self.assertRaises(aikon.AikonError):
                aikon.render_scene(value)
        value["style_overrides"] = {"reason": "User chose tilt-02.", "angle": True}
        self.assertIn(b"rotate(12 256 256)", aikon.render_scene(value))
        value["eyes"]["height"] = 58
        with self.assertRaises(aikon.AikonError):
            aikon.render_scene(value)
        value["style_overrides"]["eye_ratio"] = True
        aikon.render_scene(value)
        value["head"]["angle"] = float("inf")
        with self.assertRaises(aikon.AikonError):
            aikon.render_scene(value)

    def test_shape_and_attribute_injection_negative_controls(self):
        bad_shapes = [
            {"tag": "script", "attrs": {}},
            {"tag": "image", "attrs": {"href": "data:image/png;base64,AAAA"}},
            {"tag": ["path"], "attrs": {}},
            {"tag": "path", "attrs": {"d": "M0 0 L2 2", "onload": "alert(1)"}},
            {"tag": "path", "attrs": {"d": "M0 0 L2 2", "fill": "url(https://example.test/x)"}},
            {"tag": "path", "attrs": {"d": "M0 0 L2 2", "style": "fill:red"}},
            {"tag": "path", "attrs": {"d": "M0 0 L2 2", "transform": "scale(2)"}},
            {"tag": "path", "attrs": {"d": "M0 0 https://example.test"}},
            {"tag": "path", "attrs": {"d": "M0 0 L1e999 2"}},
            {"tag": "polygon", "attrs": {"points": "1,2 3,4 5,Infinity"}},
            {"tag": "polygon", "attrs": {"points": "1,,2 3,4 5,6"}},
            {"tag": "circle", "attrs": {"r": -1}},
            {"tag": "circle", "attrs": {"r": 1, "opacity": 2}},
        ]
        for shape in bad_shapes:
            with self.subTest(shape=shape):
                value = scene()
                value["layers"][0]["shapes"] = [shape]
                with self.assertRaises(aikon.AikonError):
                    aikon.render_scene(value)


class SVGCheckerTests(unittest.TestCase):
    def test_legacy_opaque_background_is_valid_but_reported_as_opaque(self):
        svg = aikon.render_scene(scene())
        result = aikon.check_svg(svg)
        self.assertTrue(result["ok"])
        self.assertEqual(result["background"]["structural_status"], "opaque_canvas_rect")
        self.assertEqual(result["background"]["canvas_rects"], [
            {"id": "background", "fill": "#242529", "declared_fill_alpha": 1.0},
        ])
        self.assertEqual(result["background"]["raster_alpha"], "unverified")

    def test_background_alpha_is_only_a_structural_fact(self):
        svg = aikon.render_scene(scene()).replace(b'id="background"', b'id="background" fill-opacity="0.5" opacity="0.5"')
        result = aikon.check_svg(svg)
        self.assertTrue(result["ok"])
        self.assertEqual(result["background"]["structural_status"], "translucent_canvas_rect")
        self.assertEqual(result["background"]["canvas_rects"][0]["declared_fill_alpha"], 0.25)
        self.assertEqual(result["background"]["raster_alpha"], "unverified")
        source = scene()
        source["background"] = None
        source["layers"].insert(0, {"id": "large-shape", "shapes": [
            {"tag": "path", "attrs": {"d": "M-1000 -1000 L2000 -1000 L2000 2000 L-1000 2000 Z", "fill": "#ffffff"}},
        ]})
        covered_by_path = aikon.check_svg(aikon.render_scene(source))
        self.assertEqual(covered_by_path["background"]["structural_status"], "no_painted_canvas_rect_detected")
        self.assertEqual(covered_by_path["background"]["raster_alpha"], "unverified")
        self.assertEqual(covered_by_path["checks"]["visual"], "unverified")

    def test_bitmap_external_resources_active_content_and_arbitrary_transforms_fail(self):
        safe = aikon.render_scene(scene()).decode()
        attacks = [
            safe.replace("</svg>", '<image href="data:image/png;base64,AAAA"/></svg>'),
            safe.replace("</svg>", '<image href="https://example.test/a.svg"/></svg>'),
            safe.replace("</svg>", '<script>alert(1)</script></svg>'),
            safe.replace("</svg>", '<foreignObject><div>html</div></foreignObject></svg>'),
            safe.replace('id="head"', 'id="head" onload="alert(1)"'),
            safe.replace('fill="#242529"', 'fill="url(https://example.test/pattern)"'),
            safe.replace('id="face"', 'id="face" transform="translate(2 3)"'),
            safe.replace('rotate(17 256 256)', 'matrix(1 0 0 1 2 3)'),
            '<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]>' + safe,
            '<?xml-stylesheet href="https://example.test/a.css"?>' + safe,
            safe.replace("</svg>", '<g><g id="other-head" transform="rotate(17 256 256)"/></g></svg>'),
        ]
        for svg in attacks:
            with self.subTest(svg=svg[-100:]):
                result = aikon.check_svg(svg.encode())
                self.assertFalse(result["ok"])
                self.assertTrue(result["issues"])
                self.assertEqual(result["checks"]["visual"], "unverified")

    def test_head_transform_must_be_on_a_direct_root_child(self):
        svg = aikon.render_scene(scene()).decode()
        nested = svg.replace('<g id="head"', '<g><g id="head"').replace("</svg>", "</g></svg>")
        self.assertFalse(aikon.check_svg(nested)["ok"])

    def test_xml_declaration_allowed_but_bad_xml_and_duplicate_ids_fail(self):
        svg = aikon.render_scene(scene())
        self.assertTrue(aikon.check_svg(b'<?xml version="1.0" encoding="utf-8"?>\n' + svg)["ok"])
        self.assertFalse(aikon.check_svg(svg[:-10])["ok"])
        self.assertFalse(aikon.check_svg(svg.replace(b'id="face"', b'id="eyes"'))["ok"])
        self.assertFalse(aikon.check_svg(svg.replace(b'width="29"', b'width="NaN"'))["ok"])


class FileTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="aikon-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def test_render_refuses_overwrite_and_explicit_draft_replace_works(self):
        target = self.root / "draft.svg"
        aikon.write_render(target, b"original")
        with self.assertRaises(aikon.AikonError):
            aikon.write_render(target, b"new")
        self.assertEqual(target.read_bytes(), b"original")
        aikon.write_render(target, b"new", replace=True)
        self.assertEqual(target.read_bytes(), b"new")
        self.assertFalse(list(self.root.glob(".aikon-*")))

    def test_snapshot_hashes_parent_and_history_are_preserved(self):
        first = aikon.snapshot(scene(), self.root, "r001", note="first")
        original_svg = (first / "icon.svg").read_bytes()
        manifest = json.loads((first / "revision.json").read_text(encoding="utf-8"))
        self.assertIsNone(manifest["parent"])
        self.assertIsNone(manifest["round_id"])
        self.assertIsNone(manifest["profile"])
        self.assertEqual(manifest["svg_sha256"], hashlib.sha256(original_svg).hexdigest())
        self.assertEqual(manifest["scene_sha256"], hashlib.sha256((first / "scene.json").read_bytes()).hexdigest())
        self.assertEqual(manifest["checks"], {"structural": "passed", "visual": "unverified"})
        changed = scene()
        changed["eyes"]["centers"][0][0] -= 10
        second = aikon.snapshot(changed, self.root, "r002", parent="r001", note="wider spacing")
        self.assertEqual((first / "icon.svg").read_bytes(), original_svg)
        self.assertNotEqual((second / "icon.svg").read_bytes(), original_svg)
        self.assertEqual(json.loads((second / "revision.json").read_text())["parent"], "r001")

    def test_snapshot_records_the_exact_round_and_profile_without_visual_claims(self):
        for index, profile in enumerate(("short", "full"), 1):
            with self.subTest(profile=profile):
                source = scene()
                source["background"] = None
                source["variant"] = {"round_id": "2026_round-001", "profile": profile}
                saved = aikon.snapshot(source, self.root, f"r{index:03}", note="User metadata is not a visual test result")
                manifest = json.loads((saved / "revision.json").read_text(encoding="utf-8"))
                stored = json.loads((saved / "scene.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["round_id"], source["variant"]["round_id"])
                self.assertEqual(manifest["profile"], profile)
                self.assertEqual(stored["variant"], source["variant"])
                self.assertEqual(manifest["checks"], {"structural": "passed", "visual": "unverified"})
                self.assertEqual(manifest["background"]["raster_alpha"], "unverified")
                self.assertEqual(manifest["background"]["canvas_rects"], [])
                self.assertIsNone(manifest["parent"])

    def test_revision_overwrite_missing_parent_and_traversal_fail(self):
        aikon.snapshot(scene(), self.root, "r001", note="keep")
        for revision, parent in (("r001", None), ("../escape", None), ("/escape", None),
                                 ("r003", "r404"), ("r003", "../r001"), ("r003", "r003")):
            with self.subTest(revision=revision, parent=parent):
                with self.assertRaises((aikon.AikonError, FileNotFoundError)):
                    aikon.snapshot(scene(), self.root, revision, parent=parent)
        empty = self.root / "revisions" / "r002"
        empty.mkdir()
        with self.assertRaises(aikon.AikonError):
            aikon.snapshot(scene(), self.root, "r002")
        with self.assertRaises((aikon.AikonError, FileNotFoundError)):
            aikon.snapshot(scene(), self.root, "r003", parent="r002")
        self.assertEqual(list(empty.iterdir()), [])

    def test_modified_parent_is_rejected(self):
        first = aikon.snapshot(scene(), self.root, "r001")
        (first / "icon.svg").write_bytes(b"changed out of band")
        with self.assertRaises(aikon.AikonError):
            aikon.snapshot(scene(), self.root, "r002", parent="r001")
        self.assertFalse((self.root / "revisions" / "r002").exists())

    def test_failed_snapshot_commit_cleans_only_its_own_partial_files(self):
        prior = aikon.snapshot(scene(), self.root, "r001")
        original = (prior / "icon.svg").read_bytes()
        replace = aikon.os.replace
        calls = 0

        def disk_failure(src, dst):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated disk failure after one committed file")
            return replace(src, dst)

        with mock.patch.object(aikon.os, "replace", side_effect=disk_failure):
            with self.assertRaises(OSError):
                aikon.snapshot(scene(), self.root, "r002", parent="r001")
        self.assertEqual((prior / "icon.svg").read_bytes(), original)
        self.assertFalse((self.root / "revisions" / "r002").exists())
        self.assertFalse(list((self.root / "revisions").glob(".aikon-*")))

    def test_failed_staging_write_leaves_no_revision_or_temp_directory(self):
        with mock.patch.object(Path, "write_bytes", side_effect=OSError("simulated staging failure")):
            with self.assertRaises(OSError):
                aikon.snapshot(scene(), self.root, "r001")
        self.assertEqual(list((self.root / "revisions").iterdir()), [])

    def make_symlink(self, link, target, directory=True):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError) as exc:
            self.skipTest("platform does not permit symlink creation: " + str(exc))

    def test_symlink_directory_escape_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        marker = outside / "marker.txt"
        marker.write_text("preserve")
        self.make_symlink(self.root / "linked", outside)
        with self.assertRaises(aikon.AikonError):
            aikon.snapshot(scene(), self.root / "linked", "r001")
        with self.assertRaises(aikon.AikonError):
            aikon.write_render(self.root / "linked" / "a.svg", b"svg")
        self.assertEqual([p.name for p in outside.iterdir()], ["marker.txt"])

    def test_symlink_revision_directory_and_output_file_are_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        project = self.root / "project"
        project.mkdir()
        self.make_symlink(project / "revisions", outside)
        with self.assertRaises(aikon.AikonError):
            aikon.snapshot(scene(), project, "r001")
        target = outside / "keep.svg"
        target.write_bytes(b"keep")
        self.make_symlink(self.root / "alias.svg", target, directory=False)
        with self.assertRaises(aikon.AikonError):
            aikon.write_render(self.root / "alias.svg", b"changed", replace=True)
        self.assertEqual(target.read_bytes(), b"keep")

    def test_duplicate_json_keys_and_nonfinite_json_fail(self):
        source = self.root / "bad.json"
        for text in ('{"schema":"a","schema":"b"}', '{"angle":NaN}', '{"angle":Infinity}'):
            with self.subTest(text=text):
                source.write_text(text, encoding="utf-8")
                with self.assertRaises(aikon.AikonError):
                    aikon.read_scene(source)

    def cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True, encoding="utf-8", timeout=10)

    def test_cli_render_check_snapshot_and_required_root(self):
        source, svg = self.root / "input.json", self.root / "draft.svg"
        source.write_bytes(aikon.canonical_json(scene()))
        rendered = self.cli("render", "--scene", source, "--output", svg)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        checked = self.cli("check", "--svg", svg)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertEqual(json.loads(checked.stdout)["checks"]["visual"], "unverified")
        no_root = self.cli("snapshot", "--scene", source, "--revision", "r001", "--note", "draft")
        self.assertNotEqual(no_root.returncode, 0)
        saved = self.cli("snapshot", "--scene", source, "--root", self.root / "project",
                         "--revision", "r001", "--note", "draft")
        self.assertEqual(saved.returncode, 0, saved.stderr)
        self.assertTrue((self.root / "project" / "revisions" / "r001" / "revision.json").is_file())
        invalid = self.root / "unsafe.svg"
        invalid.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><image/></svg>')
        failed = self.cli("check", "--svg", invalid)
        self.assertEqual(failed.returncode, 1)
        self.assertFalse(json.loads(failed.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
