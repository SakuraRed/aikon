"""Portable material compilation contracts, not visual acceptance.

Run: python -B -m unittest discover -s tests -p test_material_composer.py -v
"""

import copy
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET


SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "aikon" / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("material_composer", SCRIPTS / "compose_materials.py")
composer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(composer)
sys.path.pop(0)
NS = "{http://www.w3.org/2000/svg}"
HAS_RENDERER = importlib.util.find_spec("resvg_py") is not None and importlib.util.find_spec("PIL") is not None

SVG = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160">
<defs><linearGradient id="prior"><stop offset="0" stop-color="#123456"/><stop offset="1" stop-color="#789abc"/></linearGradient></defs>
<g transform="translate(13 17)" fill-rule="evenodd">
 <rect id="back" x="1" y="3" width="120" height="120" fill="url(#prior)"/>
 <g><path id="surface" transform="rotate(12 50 50)" d="M10 10 H90 V90 H10 Z M35 35 H65 V65 H35 Z" fill="url(#prior)"/></g>
 <g><rect id="owner" transform="rotate(12 50 50)" x="4" y="6" width="100" height="96" fill="none"/></g>
 <circle id="detail" cx="8" cy="9" r="3" fill="#fefefe"/>
 <rect x="3" y="3" width="2" height="2" fill="#102030"/>
</g></svg>'''


def gradient(kind="linear", translucent=False):
    value = {"kind": kind, "stops": [{"offset": 0, "color": "#ffd9a1"},
                                       {"offset": 1, "color": "#253a80"}]}
    value.update({"from": [0, 0], "to": [100, 80]} if kind == "linear"
                 else {"center": [24, 35], "radii": [70, 48]})
    if translucent:
        value["stops"][0]["opacity"] = 0.28
        value["stops"][1]["opacity"] = 0
    return value


def plan(svg=SVG, layered=False):
    item = {"target": "surface", "role": "material", "reason": "explicit reference observation",
            "field": gradient()}
    if layered:
        item.update({"support": [-10, -10, 140, 140], "glaze_reasons": ["broad upper light"],
                     "field": {"kind": "layered", "base": gradient(),
                               "glazes": [gradient("radial", translucent=True)]}})
    return {"schema": "aikon.material-plan.v1", "geometry_sha256": hashlib.sha256(svg).hexdigest(),
            "profile": "full", "materials": [item]}


def by_id(root):
    return {node.get("id"): node for node in root.iter() if node.get("id")}


class MaterialCompilerTests(unittest.TestCase):
    def test_local_repaint_keeps_whole_geometry_and_unselected_art(self):
        before = ET.fromstring(SVG)
        original = copy.deepcopy(plan())
        data, report = composer.compile_materials(SVG, original)
        after = ET.fromstring(data)
        old_ids, new_ids = by_id(before), by_id(after)
        self.assertEqual(plan(), original)
        for key, node in old_ids.items():
            for attribute, value in node.attrib.items():
                if attribute in composer.GEOMETRY:
                    self.assertEqual(value, new_ids[key].get(attribute), (key, attribute))
        for key in ("back", "owner", "detail", "prior"):
            self.assertEqual(ET.tostring(old_ids[key]), ET.tostring(new_ids[key]))
        self.assertEqual(len(before.findall(".//" + NS + "rect")), len(after.findall(".//" + NS + "rect")))
        self.assertEqual(report["original_shape_count"], 5)
        self.assertTrue(report["checks"]["original_geometry_preserved"])
        self.assertEqual(report["svg_sha256"], hashlib.sha256(data).hexdigest())

    def test_layered_boundary_is_original_editable_shape_and_one_shared_clip(self):
        data, report = composer.compile_materials(SVG, plan(layered=True))
        root = ET.fromstring(data)
        target = by_id(root)["surface"]
        parents = {child: parent for parent in root.iter() for child in parent}
        clip = parents[target]
        self.assertEqual(clip.tag, NS + "clipPath")
        groups = [node for node in root.iter(NS + "g") if node.get("clip-path") == "url(#" + clip.get("id") + ")"]
        self.assertEqual(len(groups), 1)
        layers = list(groups[0])
        self.assertEqual([node.tag for node in layers], [NS + "rect", NS + "rect"])
        self.assertEqual([node.get("data-material-layer") for node in layers], ["base", "glaze"])
        self.assertTrue(all(node.get("transform") == target.get("transform") for node in layers))
        self.assertEqual(sum(node.get("d") == target.get("d") for node in root.iter()), 1)
        base_gradient = by_id(root)[layers[0].get("fill")[5:-1]]
        self.assertTrue(all(stop.get("stop-opacity") == "1" for stop in base_gradient))
        self.assertEqual(report["checks"]["raster_alpha"], "unverified")
        self.assertEqual(report["checks"]["visual"], "unverified")
        self.assertEqual(report["user_acceptance"], "unassessed")

    def test_owner_same_coordinates_different_parent_and_targeted_owner(self):
        value = plan(layered=True)
        value["materials"][0]["owner"] = "owner"
        value["materials"].append({"target": "owner", "role": "support", "reason": "retained support",
                                    "field": {"kind": "solid", "color": "#ffeedd"}})
        data, report = composer.compile_materials(SVG, value)
        self.assertEqual(report["materials"][0]["owner"], "owner")
        self.assertEqual(len(ET.fromstring(data).findall(".//" + NS + "clipPath")), 2)

    def test_solid_radial_and_two_glazes_without_palette_or_eye_rules(self):
        for field in ({"kind": "solid", "color": "#e020a0"}, gradient("radial")):
            value = plan(); value["materials"][0]["role"] = "eye"
            value["materials"][0]["field"] = field
            composer.compile_materials(SVG, value)
        value = plan(layered=True)
        value["materials"][0]["field"]["glazes"].append({"kind": "solid", "color": "#fa6040", "opacity": 0.1})
        value["materials"][0]["glaze_reasons"].append("explicit warm material glaze")
        data, _ = composer.compile_materials(SVG, value)
        self.assertEqual(data.count(b'data-material-layer="glaze"'), 2)

    def test_small_support_is_never_reported_as_verified_coverage(self):
        value = plan(layered=True); value["materials"][0]["support"] = [0, 0, 1, 1]
        _, report = composer.compile_materials(SVG, value)
        self.assertEqual(report["checks"]["support_coverage"], "unverified")

    def test_input_and_output_use_existing_static_validator(self):
        invalid_documents = [
            SVG.replace(b'fill="url(#prior)"', b'fill="url(#missing)"', 1),
            SVG.replace(b'fill="url(#prior)"', b'fill="url(#surface)"', 1),
            SVG.replace(b'</svg>', b'<image href="x.png"/></svg>'),
            SVG.replace(b'</svg>', b'<filter id="fx"/></svg>'),
            SVG.replace(b'</svg>', b'<pattern id="p"/></svg>'),
        ]
        for invalid in invalid_documents:
            with self.subTest(svg=invalid[-80:]), self.assertRaises(ValueError):
                composer.compile_materials(invalid, plan(invalid))

    def test_explicit_bad_parameters_fail(self):
        mutations = [
            lambda p: p.update(geometry_sha256="0" * 64),
            lambda p: p.update(materials={}),
            lambda p: p["materials"][0].update(target=[]),
            lambda p: p["materials"][0].update(target="prior"),
            lambda p: p["materials"][0].update(owner="missing"),
            lambda p: p["materials"][0].update(owner="prior"),
            lambda p: p["materials"][0].update(owner="surface"),
            lambda p: p["materials"][0].update(reason=""),
            lambda p: p["materials"][0]["field"].update(kind="mesh"),
            lambda p: p["materials"][0]["field"].update(**{"from": [float("nan"), 0]}),
            lambda p: p["materials"][0]["field"].update(to=[float("inf"), 0]),
            lambda p: p["materials"][0]["field"].update(to=[10 ** 1000, 0]),
            lambda p: p["materials"][0]["field"].update(to=[True, 0]),
            lambda p: p["materials"][0]["field"].update(to=["10", 0]),
            lambda p: p["materials"][0]["field"].update(to=[0, 0]),
            lambda p: p["materials"][0]["field"]["stops"][0].update(color="url(#prior)"),
            lambda p: p["materials"][0]["field"]["stops"][0].update(opacity=0.5),
            lambda p: p["materials"][0]["field"]["stops"][1].update(offset=0),
            lambda p: p["materials"].append(copy.deepcopy(p["materials"][0])),
        ]
        for mutate in mutations:
            value = plan(); mutate(value)
            with self.subTest(plan=value), self.assertRaises(ValueError):
                composer.compile_materials(SVG, value)

    def test_bad_layered_parameters_fail(self):
        mutations = [
            lambda x: x.pop("support"),
            lambda x: x.update(support=[0, 0, -1, 40]),
            lambda x: x.update(support=[0, 0, float("inf"), 40]),
            lambda x: x.update(glaze_reasons=[]),
            lambda x: x["field"].update(glazes=[]),
            lambda x: x["field"].update(glazes=[gradient()] * 3),
            lambda x: x["field"]["base"]["stops"][0].update(opacity=0),
            lambda x: x["field"]["glazes"][0].update(radii=[0, 40]),
            lambda x: x["field"]["glazes"][0]["stops"][0].update(opacity=2),
            lambda x: x["field"]["glazes"][0].update(kind="layered"),
        ]
        for mutate in mutations:
            value = plan(layered=True); mutate(value["materials"][0])
            with self.subTest(plan=value), self.assertRaises(ValueError):
                composer.compile_materials(SVG, value)

    def test_inherited_opacity_and_owner_coordinate_mismatch_fail(self):
        for invalid in (SVG.replace(b'transform="translate(13 17)"', b'transform="translate(13 17)" opacity=".6"'),
                        SVG.replace(b'id="owner" transform="rotate(12 50 50)"', b'id="owner" transform="translate(1 0)"')):
            value = plan(invalid, layered=True); value["materials"][0]["owner"] = "owner"
            with self.assertRaises(ValueError):
                composer.compile_materials(invalid, value)

    def test_line_and_stroke_only_surfaces_are_rejected(self):
        for markup in ('<line id="surface" x1="0" y1="0" x2="40" y2="40" stroke="#234567"/>',
                       '<polyline id="surface" points="0,0 40,40 20,60" fill="none" stroke="#234567"/>',
                       '<path id="surface" d="M0 0 L40 40" fill="none" stroke="#234567"/>'):
            svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160">' + markup + '</svg>').encode()
            with self.subTest(markup=markup), self.assertRaisesRegex(ValueError, "filled surfaces"):
                composer.compile_materials(svg, plan(svg))

    def test_target_opacity_is_replaced_but_ancestor_fill_opacity_overridden(self):
        svg = SVG.replace(b'id="surface"', b'id="surface" opacity=".3"').replace(b'fill-rule="evenodd"', b'fill-rule="evenodd" fill-opacity=".2"')
        for layered in (False, True):
            data, _ = composer.compile_materials(svg, plan(svg, layered))
            target = by_id(ET.fromstring(data))["surface"]
            self.assertEqual(target.get("opacity"), "1")
            self.assertEqual(target.get("fill-opacity"), "1")

    def test_no_shape_translation_is_introduced(self):
        for layered in (False, True):
            data, _ = composer.compile_materials(SVG, plan(layered=layered))
            root = ET.fromstring(data)
            shape = by_id(root)["surface"]
            chain = composer.transforms(shape, composer.parents_of(root))
            self.assertEqual(chain, ["rotate(12 50 50)", "translate(13 17)"])

    def test_cli_outputs_hash_report_refuses_overwrite_and_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            portable = folder / "portable"; portable.mkdir()
            for name in ("compose_materials.py", "archive_svg.py"):
                shutil.copyfile(SCRIPTS / name, portable / name)
            geometry = folder / "geometry.svg"; geometry.write_bytes(SVG)
            materials = folder / "plan.json"; materials.write_text(json.dumps(plan()), encoding="utf-8")
            output, report = folder / "compiled.svg", folder / "report.json"
            command = [sys.executable, "-B", "-S", str(portable / "compose_materials.py"), "--geometry", str(geometry),
                       "--plan", str(materials), "--output", str(output), "--report", str(report)]
            first = subprocess.run(command, capture_output=True, text=True, cwd=folder, timeout=10)
            self.assertEqual(first.returncode, 0, first.stderr)
            original = output.read_bytes()
            self.assertEqual(json.loads(report.read_text())["svg_sha256"], hashlib.sha256(original).hexdigest())
            second = subprocess.run(command, capture_output=True, text=True, cwd=folder, timeout=10)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(output.read_bytes(), original)
            output.unlink(); report.unlink()
            for bad in ('{"schema":"a","schema":"b"}', '{"value":NaN}'):
                materials.write_text(bad, encoding="utf-8")
                failure = subprocess.run(command, capture_output=True, text=True, cwd=folder, timeout=10)
                self.assertNotEqual(failure.returncode, 0)
                self.assertFalse(output.exists())
                self.assertFalse(report.exists())

    def test_cli_descriptor_identity_failure_rolls_back_only_new_files(self):
        for failure_index in (1, 2):
            with self.subTest(failure_index=failure_index), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                geometry, materials = folder / "geometry.svg", folder / "plan.json"
                output, report, unrelated = folder / "out.svg", folder / "report.json", folder / "existing.txt"
                geometry.write_bytes(SVG); materials.write_text(json.dumps(plan()), encoding="utf-8")
                unrelated.write_bytes(b"another artifact")
                arguments = ["--geometry", str(geometry), "--plan", str(materials),
                             "--output", str(output), "--report", str(report)]
                real_fstat, real_stat = composer.os.fstat, composer.os.stat
                calls, fallback_descriptors = [], []

                def failed_fstat(descriptor):
                    calls.append(descriptor)
                    if len(calls) == failure_index:
                        raise OSError("injected initial descriptor failure")
                    return real_fstat(descriptor)

                def tracked_stat(target, *args, **kwargs):
                    if isinstance(target, int):
                        fallback_descriptors.append(target)
                    return real_stat(target, *args, **kwargs)

                with mock.patch.object(composer.os, "fstat", failed_fstat), \
                        mock.patch.object(composer.os, "stat", tracked_stat), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(composer.main(arguments), 1)
                self.assertEqual(fallback_descriptors, [calls[-1]])
                self.assertFalse(output.exists())
                self.assertFalse(report.exists())
                self.assertEqual(geometry.read_bytes(), SVG)
                self.assertEqual(json.loads(materials.read_text()), plan())
                self.assertEqual(unrelated.read_bytes(), b"another artifact")

    def test_cli_report_created_by_another_writer_is_not_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            geometry, materials = folder / "geometry.svg", folder / "plan.json"
            output, report = folder / "out.svg", folder / "report.json"
            geometry.write_bytes(SVG); materials.write_text(json.dumps(plan()), encoding="utf-8")
            arguments = ["--geometry", str(geometry), "--plan", str(materials),
                         "--output", str(output), "--report", str(report)]
            real_open = Path.open

            def another_writer(path, mode="r", *args, **kwargs):
                if path == report and mode == "xb":
                    with real_open(path, "xb") as stream:
                        stream.write(b"concurrent report")
                return real_open(path, mode, *args, **kwargs)

            with mock.patch.object(Path, "open", another_writer), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(composer.main(arguments), 1)
            self.assertFalse(output.exists())
            self.assertEqual(report.read_bytes(), b"concurrent report")
            self.assertEqual(geometry.read_bytes(), SVG)

    def test_cli_unknown_descriptor_identity_is_reported_and_left_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            geometry, materials = folder / "geometry.svg", folder / "plan.json"
            output, report = folder / "out.svg", folder / "report.json"
            geometry.write_bytes(SVG); materials.write_text(json.dumps(plan()), encoding="utf-8")
            arguments = ["--geometry", str(geometry), "--plan", str(materials),
                         "--output", str(output), "--report", str(report)]
            real_stat = composer.os.stat

            def failed_descriptor_stat(target, *args, **kwargs):
                if isinstance(target, int):
                    raise OSError("injected fallback descriptor failure")
                return real_stat(target, *args, **kwargs)

            errors = io.StringIO()
            with mock.patch.object(composer.os, "fstat", side_effect=OSError("first identity failure")), \
                    mock.patch.object(composer.os, "stat", failed_descriptor_stat), contextlib.redirect_stderr(errors):
                self.assertEqual(composer.main(arguments), 1)
            self.assertIn("descriptor identity unavailable", errors.getvalue())
            self.assertIn("left untouched", errors.getvalue())
            self.assertTrue(output.exists())
            self.assertEqual(output.read_bytes(), b"")
            self.assertFalse(report.exists())


@unittest.skipUnless(HAS_RENDERER, "optional repository resvg/Pillow renderer unavailable")
class MaterialRenderTests(unittest.TestCase):
    def test_transformed_surface_alpha_and_boundary_edit_with_negative_control(self):
        from PIL import Image, ImageChops
        from tools import render_svg

        svg = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160">
        <g transform="translate(13 17)" fill-rule="evenodd">
        <path id="surface" transform="rotate(12 50 50)" d="M10 10 H90 V90 H10 Z M35 35 H65 V65 H35 Z" fill="#334455"/>
        </g></svg>'''
        value = plan(svg, layered=True)
        value["materials"][0]["field"] = {"kind": "layered", "base": {"kind": "solid", "color": "#334455"},
                                            "glazes": [{"kind": "solid", "color": "#ffddb0", "opacity": 0.3}]}

        def alpha(source):
            raw = source.decode() if isinstance(source, bytes) else ET.tostring(source, encoding="unicode")
            return Image.open(io.BytesIO(render_svg.render_svg_text(raw, 320))).getchannel("A")

        compiled, _ = composer.compile_materials(svg, value)
        reference, actual = alpha(svg), alpha(compiled)
        self.assertEqual(reference.getbbox(), actual.getbbox())
        self.assertLessEqual(ImageChops.difference(reference, actual).getextrema()[1], 1)
        # A duplicated translucent silhouette increases edge alpha. This is a
        # deliberate negative control for the one-shared-boundary requirement.
        duplicate = ET.fromstring(svg)
        original = by_id(duplicate)["surface"]
        extra = copy.deepcopy(original)
        extra.attrib.pop("id"); extra.set("opacity", "0.3")
        duplicate.find(NS + "g").append(extra)
        excess = ImageChops.subtract(alpha(duplicate), reference)
        self.assertGreater(excess.getextrema()[1], 10)
        # Original target ID stays live: edit its actual clip geometry, and the
        # resulting mask matches the same edit to the plain source silhouette.
        compiled_root, expected_root = ET.fromstring(compiled), ET.fromstring(svg)
        revised_path = "M20 20 H70 V80 H20 Z"
        by_id(compiled_root)["surface"].set("d", revised_path)
        by_id(expected_root)["surface"].set("d", revised_path)
        revised, expected = alpha(compiled_root), alpha(expected_root)
        self.assertGreater(ImageChops.difference(actual, revised).getextrema()[1], 100)
        self.assertLessEqual(ImageChops.difference(revised, expected).getextrema()[1], 1)
        # Positive alpha agreement is sensitive to a lost/changed transform.
        by_id(compiled_root)["surface"].set("transform", "translate(9 0)")
        self.assertGreater(ImageChops.difference(alpha(compiled_root), expected).getextrema()[1], 100)

    def test_field_coordinates_match_direct_paint_under_nonidentity_transforms(self):
        from PIL import Image, ImageChops
        from tools import render_svg

        svg = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160">
        <g transform="translate(13 17) rotate(-4 60 60)">
        <path id="surface" transform="rotate(12 50 50) scale(.8 1.1)" d="M10 10 H90 V90 H10 Z"/>
        </g></svg>'''
        for kind in ("linear", "radial"):
            direct = plan(svg); direct["materials"][0]["field"] = gradient(kind)
            layered = plan(svg, layered=True)
            layered["materials"][0]["field"] = {"kind": "layered", "base": gradient(kind),
                                                "glazes": [{"kind": "solid", "color": "#ffffff", "opacity": 0}]}
            samples = []
            for value in (direct, layered):
                data, _ = composer.compile_materials(svg, value)
                samples.append(Image.open(io.BytesIO(render_svg.render_svg_text(data.decode(), 320))))
            difference = ImageChops.difference(samples[0], samples[1])
            mask = samples[0].getchannel("A").point(lambda a: 255 if a == 255 else 0)
            interior = Image.composite(difference, Image.new("RGBA", difference.size), mask)
            with self.subTest(kind=kind):
                self.assertTrue(mask.getbbox())
                self.assertLessEqual(max(channel[1] for channel in interior.getextrema()), 1)


if __name__ == "__main__":
    unittest.main()
