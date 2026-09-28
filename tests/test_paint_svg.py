"""Independent authoring-contract fixtures for deterministic analytic paint.

These tests check geometry preservation, rejected requests, and real pixels;
they do not establish artistic quality or user acceptance.
"""

import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
NS = "http://www.w3.org/2000/svg"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


paint = load_module("paint_svg", ROOT / "skills/aikon/scripts/paint_svg.py")
renderer = load_module("paint_test_renderer", ROOT / "tools/render_svg.py")
HAS_RASTER = importlib.util.find_spec("resvg_py") is not None and importlib.util.find_spec("PIL") is not None


def source_geometry():
    return b'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64" opacity="0.5">
<defs><linearGradient id="old-gradient"><stop stop-color="#ffffff"/><stop offset="1" stop-color="#000000"/></linearGradient></defs>
<g id="head" transform="translate(2 1)" opacity="0.65" fill="#333333">
  <rect id="face" x="6" y="8" width="42" height="42" rx="4" fill="#b0c0d0" fill-opacity="0.4"/>
  <path id="hair" d="M6 18 Q16 0 48 8 L48 20 Q30 12 6 18Z" fill="url(#old-gradient)" transform="translate(0 1)"/>
  <ellipse id="eye" cx="22" cy="28" rx="2" ry="6" fill="#777777" stroke="#ffffff" stroke-width="3"/>
  <path id="old-sheen" d="M12 14L24 9L22 18Z" fill="#ffffff" opacity="0.35"/>
</g></svg>'''


def solid(identifier, role, color, **extra):
    return {"id": identifier, "role": role, "paint": {"type": "solid", "color": color}, **extra}


def plan_for(geometry, layers=None):
    if layers is None:
        layers = [
            solid("face", "surface", "#e8d8c8"),
            solid("hair", "surface", "#344964"),
            solid("eye", "eye", "#1b2030"),
        ]
    return {
        "schema": "aikon.paint-plan.v1", "geometry_sha256": hashlib.sha256(geometry).hexdigest(),
        "profile": "short", "layers": layers,
    }


def element(tree, identifier):
    return next(node for node in tree.iter() if node.get("id") == identifier)


class PaintContractTests(unittest.TestCase):
    def test_cli_preserves_unicode_reason_under_ascii_console(self):
        geometry = source_geometry()
        request = plan_for(geometry)
        reason = "头发遮挡产生的弱阴影"
        request["layers"].append(solid("old-sheen", "occlusion-shadow", "#d2c2b2", owner="face", anchor="receiver-boundary", reason=reason))
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "geometry.svg").write_bytes(geometry)
            (folder / "plan.json").write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(ROOT / "skills/aikon/scripts/paint_svg.py"), "--geometry", str(folder / "geometry.svg"), "--plan", str(folder / "plan.json"), "--output", str(folder / "icon.svg"), "--report", str(folder / "report.json")], capture_output=True, timeout=10, env={**os.environ, "PYTHONIOENCODING": "ascii"})
            self.assertEqual(result.returncode, 0, result.stderr)
            reported = json.loads(result.stdout.decode("ascii"))
            self.assertEqual(reported["shadow_anchors"][0]["reason"], reason)
            self.assertEqual(json.loads((folder / "report.json").read_text(encoding="utf-8")), reported)
            self.assertEqual(reported["svg_sha256"], hashlib.sha256((folder / "icon.svg").read_bytes()).hexdigest())

    def test_selected_geometry_and_transform_order_are_frozen(self):
        geometry = source_geometry()
        source = ET.fromstring(geometry)
        request = plan_for(geometry)
        original_request = copy.deepcopy(request)
        output, report = paint.compile_paint(geometry, request)
        result = ET.fromstring(output)
        self.assertEqual(result.get("viewBox"), "0 0 64 64")
        for identifier, attrs in {
            "face": ("x", "y", "width", "height", "rx"),
            "hair": ("d", "transform"),
            "eye": ("cx", "cy", "rx", "ry"),
            "head": ("transform",),
        }.items():
            for attr in attrs:
                self.assertEqual(element(result, identifier).get(attr), element(source, identifier).get(attr))
        self.assertEqual([node.get("id") for node in element(result, "head")], ["face", "hair", "eye"])
        self.assertTrue(report["selected_geometry_unchanged"])
        self.assertEqual(report["checks"]["visual"], "not_run")
        self.assertEqual(report["checks"]["user_acceptance"], "not_claimed")
        self.assertEqual(request, original_request)
        self.assertEqual(geometry, source_geometry())

    def test_same_source_and_plan_produce_identical_bytes_and_report(self):
        geometry = source_geometry()
        request = plan_for(geometry)
        first = paint.compile_paint(geometry, request)
        second = paint.compile_paint(bytes(geometry), copy.deepcopy(request))
        self.assertEqual(first, second)
        self.assertEqual(first[1]["svg_sha256"], hashlib.sha256(first[0]).hexdigest())

    def test_prior_translucent_patches_and_inherited_alpha_are_removed(self):
        geometry = source_geometry()
        output, report = paint.compile_paint(geometry, plan_for(geometry))
        result = ET.fromstring(output)
        ids = {node.get("id") for node in result.iter()}
        self.assertNotIn("old-sheen", ids)
        self.assertNotIn("old-gradient", ids)
        for node in result.iter():
            self.assertNotIn("opacity", node.attrib)
            self.assertNotIn("fill-opacity", node.attrib)
            self.assertNotIn("stroke-opacity", node.attrib)
        self.assertIn("old-sheen", report["discarded_prior_paint"])
        self.assertEqual(element(result, "eye").get("fill"), "#1b2030")

    def test_smooth_field_has_two_opaque_endpoints_and_explicit_space(self):
        geometry = source_geometry()
        request = plan_for(geometry)
        request["layers"][1]["paint"] = {
            "type": "linear", "from": [6, 2], "to": [46, 22], "colors": ["#344964", "#405570"],
        }
        output, report = paint.compile_paint(geometry, request)
        gradients = ET.fromstring(output).findall(".//{" + NS + "}linearGradient")
        self.assertEqual(len(gradients), 1)
        self.assertEqual(gradients[0].get("gradientUnits"), "userSpaceOnUse")
        self.assertEqual([(stop.get("offset"), stop.get("stop-color")) for stop in gradients[0]], [("0", "#344964"), ("1", "#405570")])
        self.assertTrue(all(stop.get("stop-opacity", "1") == "1" for stop in gradients[0]))
        self.assertEqual(report["gradient_count"], 1)

    def test_unplanned_highlight_role_noise_and_external_content_are_rejected(self):
        geometry = source_geometry()
        request = plan_for(geometry)
        request["layers"].append(solid("old-sheen", "highlight", "#ffffff"))
        with self.assertRaises(paint.PaintError):
            paint.compile_paint(geometry, request)
        additions = [
            '<filter id="noise"><feTurbulence baseFrequency="0.4"/></filter>',
            '<script>fetch("https://example.com")</script>',
            '<image href="data:image/png;base64,AAAA"/>',
            '<linearGradient id="external" href="https://example.com/paint.svg#g"/>',
        ]
        for addition in additions:
            bad = geometry.replace(b"</svg>", addition.encode() + b"</svg>")
            with self.subTest(addition=addition), self.assertRaises(paint.PaintError):
                paint.compile_paint(bad, plan_for(bad))
        for injection in ('onload="alert(1)"', 'clip-path="url(file:///tmp/private.svg#x)"', 'clip-path="URL(file:///tmp/private.svg#x)"'):
            bad = geometry.replace(b'id="face"', ('id="face" ' + injection).encode())
            with self.subTest(injection=injection), self.assertRaises(paint.PaintError):
                paint.compile_paint(bad, plan_for(bad))

    def test_shadows_require_receiver_boundary_and_a_reason(self):
        geometry = b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect id="face" x="8" y="8" width="40" height="40"/><path id="shadow" d="M8 8H48V12H8Z"/></svg>'
        valid = plan_for(geometry, [solid("face", "surface", "#d8c8b8"), solid("shadow", "occlusion-shadow", "#ccc0b0", owner="face", anchor="receiver-boundary", reason="Hair above the forehead blocks the light.")])
        output, report = paint.compile_paint(geometry, valid)
        self.assertTrue(output)
        self.assertEqual(report["shadow_anchors"][0]["owner"], "face")
        for field in ("owner", "anchor", "reason"):
            request = copy.deepcopy(valid)
            del request["layers"][1][field]
            with self.subTest(missing=field), self.assertRaises(paint.PaintError):
                paint.compile_paint(geometry, request)
        for field, value in (("owner", "shadow"), ("anchor", "arbitrary-interior"), ("reason", "  ")):
            request = copy.deepcopy(valid)
            request["layers"][1][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(paint.PaintError):
                paint.compile_paint(geometry, request)

    def test_stale_source_hash_and_duplicate_layer_selection_fail(self):
        geometry = source_geometry()
        request = plan_for(geometry)
        with self.assertRaises(paint.PaintError):
            paint.compile_paint(geometry.replace(b'rx="4"', b'rx="5"'), request)
        request["layers"].append(copy.deepcopy(request["layers"][0]))
        with self.assertRaises(paint.PaintError):
            paint.compile_paint(geometry, request)

    def test_nonfinite_paint_coordinates_and_excessive_gradient_contrast_fail(self):
        geometry = source_geometry()
        gradient = {"type": "linear", "from": [0, 0], "to": [64, 64], "colors": ["#344964", "#405570"]}
        bad_fields = []
        for coordinate in (float("nan"), float("inf"), -float("inf"), True):
            bad = copy.deepcopy(gradient)
            bad["from"][0] = coordinate
            bad_fields.append(bad)
        for colors in (["#000000", "#ffffff"], ["#000040", "#800000"], ["#111111", "#222222", "#111111"]):
            bad = copy.deepcopy(gradient)
            bad["colors"] = colors
            bad_fields.append(bad)
        bad = copy.deepcopy(gradient)
        bad["to"] = bad["from"][:]
        bad_fields.append(bad)
        for bad in bad_fields:
            request = plan_for(geometry)
            request["layers"][1]["paint"] = bad
            with self.subTest(paint=bad), self.assertRaises(paint.PaintError):
                paint.compile_paint(geometry, request)

    def test_gradient_cannot_be_assigned_to_eyes_or_blush(self):
        geometry = source_geometry()
        for role in ("eye", "blush"):
            request = plan_for(geometry)
            request["layers"][2]["role"] = role
            if role == "blush":
                request["layers"][2]["owner"] = "face"
            request["layers"][2]["paint"] = {"type": "linear", "from": [0, 0], "to": [10, 0], "colors": ["#111111", "#222222"]}
            with self.subTest(role=role), self.assertRaises(paint.PaintError):
                paint.compile_paint(geometry, request)


@unittest.skipUnless(HAS_RASTER, "install optional requirements-ci.txt for real paint pixel tests")
class PaintRasterTests(unittest.TestCase):
    def raster(self, source):
        from PIL import Image
        image = Image.open(io.BytesIO(renderer.render_svg_text(source.decode() if isinstance(source, bytes) else source, size=64)))
        image.load()
        return image

    def test_rebuilt_opaque_paint_does_not_depend_on_old_alpha(self):
        geometry = source_geometry()
        output, _ = paint.compile_paint(geometry, plan_for(geometry))
        image = self.raster(output)
        self.assertEqual(image.getpixel((38, 39)), (232, 216, 200, 255))
        self.assertEqual(image.getpixel((24, 29)), (27, 32, 48, 255))
        self.assertEqual(image.getpixel((63, 63))[3], 0)

    def test_two_stop_field_renders_a_monotone_continuous_interior(self):
        geometry = b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect id="surface" x="4" y="4" width="56" height="56"/></svg>'
        request = plan_for(geometry, [{"id": "surface", "role": "surface", "paint": {"type": "linear", "from": [4, 4], "to": [60, 4], "colors": ["#344964", "#445974"]}}])
        output, _ = paint.compile_paint(geometry, request)
        image = self.raster(output)
        row = [image.getpixel((x, 32)) for x in range(8, 56)]
        self.assertTrue(all(pixel[3] == 255 for pixel in row))
        self.assertGreater(row[-1][0], row[0][0] + 10)
        self.assertTrue(all(0 <= right[0] - left[0] <= 1 for left, right in zip(row, row[1:])))

    def test_rotated_blush_is_clipped_in_parent_space_without_rotating_face(self):
        geometry = b'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">
        <rect id="face" x="8" y="8" width="40" height="32"/>
        <ellipse id="blush" cx="46" cy="28" rx="16" ry="10" transform="rotate(45 46 28)"/>
        </svg>'''
        request = plan_for(geometry, [solid("face", "surface", "#e8d8c8"), solid("blush", "blush", "#e0a8b0", owner="face")])
        output, report = paint.compile_paint(geometry, request)
        image = self.raster(output)
        owner = self.raster('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect x="8" y="8" width="40" height="32" fill="#ffffff"/></svg>')
        outside = [(x, y) for y in range(64) for x in range(64) if owner.getpixel((x, y))[3] == 0]
        self.assertTrue(all(image.getpixel(position)[3] == 0 for position in outside), "Blush leaked beyond the unrotated face receiver")
        self.assertGreater(sum(image.getpixel((x, y))[:3] == (224, 168, 176) for y in range(64) for x in range(64)), 30)
        result = ET.fromstring(output)
        self.assertEqual(element(result, "blush").get("transform"), "rotate(45 46 28)")
        self.assertIsNone(element(result, "face").get("transform"))
        self.assertTrue(report["selected_geometry_unchanged"])
        # This independently constructed wrong-space clip must leak, proving the
        # fixture is sensitive to the historical parent/local coordinate bug.
        wrong = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">
        <defs><clipPath id="face-clip" clipPathUnits="userSpaceOnUse"><rect x="8" y="8" width="40" height="32"/></clipPath></defs>
        <rect x="8" y="8" width="40" height="32" fill="#e8d8c8"/>
        <ellipse cx="46" cy="28" rx="16" ry="10" transform="rotate(45 46 28)" fill="#e0a8b0" clip-path="url(#face-clip)"/>
        </svg>'''
        faulty_image = self.raster(wrong)
        self.assertGreater(sum(faulty_image.getpixel(position)[3] > 0 for position in outside), 8)


if __name__ == "__main__":
    unittest.main()
