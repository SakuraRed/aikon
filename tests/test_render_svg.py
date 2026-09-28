"""Real raster assertions for the optional, offline SVG verification adapter."""

import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "render_svg.py"
SPEC = importlib.util.spec_from_file_location("render_svg", SCRIPT)
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)
HAS_RENDERER = importlib.util.find_spec("resvg_py") is not None
HAS_PILLOW = importlib.util.find_spec("PIL") is not None

GRADIENT_CLIP = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
<defs>
  <linearGradient id="paint" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#ff0000"/>
    <stop offset="1" stop-color="#0000ff"/>
  </linearGradient>
  <clipPath id="clip"><circle cx="32" cy="32" r="24"/></clipPath>
</defs>
<rect width="64" height="64" fill="url(#paint)" clip-path="url(#clip)" opacity="0.5"/>
</svg>'''


class VectorBoundaryTests(unittest.TestCase):
    def test_local_gradients_and_clips_are_valid(self):
        renderer.validate_svg(GRADIENT_CLIP)
        renderer.validate_svg(GRADIENT_CLIP.replace('fill="url(#paint)"', 'style="fill:url(\'#paint\');stroke:none"'))

    def test_active_or_resource_loading_svg_is_rejected(self):
        bad_bodies = [
            '<script>alert(1)</script>',
            '<image href="data:image/png;base64,aGVsbG8="/>',
            '<image href="https://example.com/image.png"/>',
            '<foreignObject><div>HTML</div></foreignObject>',
            '<style>@import "https://example.com/font.css";</style>',
            '<text x="1" y="20">Host-dependent font</text>',
            '<animate attributeName="fill" values="red;blue"/>',
            '<filter id="noise"><feTurbulence/></filter>',
            '<linearGradient id="g" href="https://example.com/colors.svg#g"/>',
            '<linearGradient id="g" href="file:///etc/passwd"/>',
            '<path d="M0 0L1 1" onload="alert(1)"/>',
            '<path d="M0 0L1 1" fill="url(https://example.com/g)"/>',
            '<path d="M0 0L1 1" style="fill:u\\72l(https://example.com/g)"/>',
            '<path d="M0 0L1 1" style="fill:u/**/rl(https://example.com/g)"/>',
            '<path d="M0 0L1 1" xml:base="https://example.com/"/>',
        ]
        for body in bad_bodies:
            with self.subTest(body=body), self.assertRaises(ValueError):
                renderer.validate_svg('<svg xmlns="http://www.w3.org/2000/svg">' + body + '</svg>')

    def test_dtd_stylesheet_and_non_svg_namespaces_are_rejected(self):
        samples = [
            '<!DOCTYPE svg [<!ENTITY x "payload">]><svg xmlns="http://www.w3.org/2000/svg"><title>&x;</title></svg>',
            '<?xml-stylesheet href="https://example.com/a.css"?><svg xmlns="http://www.w3.org/2000/svg"/>',
            '<svg xmlns="http://www.w3.org/2000/svg"><script xmlns="urn:other"/></svg>',
        ]
        for source in samples:
            with self.subTest(source=source), self.assertRaises(ValueError):
                renderer.validate_svg(source)

    def test_mixed_case_and_xml_encoded_external_references_cannot_reach_backend(self):
        for paint in ('URL(file:///private.svg#x)', 'UrL(https://example.com/x)', 'url(&#104;ttps://example.com/x)'):
            source = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="64" height="64" fill="' + paint + '"/></svg>'
            with self.subTest(paint=paint), self.assertRaises(ValueError):
                renderer.validate_svg(source)

    def test_document_size_element_and_depth_budgets_fail_before_native_render(self):
        bodies = ["<desc>" + "x" * 2_000_000 + "</desc>", "<g>" * 66 + "</g>" * 66, "<rect/>" * 10_001]
        for body in bodies:
            with self.subTest(length=len(body)), self.assertRaises(ValueError):
                renderer.validate_svg('<svg xmlns="http://www.w3.org/2000/svg">' + body + '</svg>')

    def test_missing_paint_and_duplicate_ids_do_not_silently_render(self):
        for source in (
            GRADIENT_CLIP.replace('url(#paint)', 'url(#missing)'),
            GRADIENT_CLIP.replace('id="clip"', 'id="paint"'),
        ):
            with self.assertRaises(ValueError):
                renderer.validate_svg(source)

    def test_render_budget_and_input_overwrite_are_rejected_before_backend(self):
        for size in (0, -1, 4097, 0.5, True):
            with self.subTest(size=size), self.assertRaises(ValueError):
                renderer.render_svg_text(GRADIENT_CLIP, size)
        with self.assertRaisesRegex(ValueError, "paths must differ"):
            renderer.render_svg_file("a.svg", "a.svg")


@unittest.skipUnless(HAS_RENDERER and HAS_PILLOW, "install optional requirements-ci.txt for raster tests")
class RasterIntegrationTests(unittest.TestCase):
    def image(self, source=GRADIENT_CLIP, size=64):
        from PIL import Image
        image = Image.open(io.BytesIO(renderer.render_svg_text(source, size)))
        image.load()
        return image

    def test_gradient_clip_and_true_partial_alpha_survive_rendering(self):
        image = self.image()
        self.assertEqual(image.mode, "RGBA")
        self.assertEqual(image.size, (64, 64))
        self.assertEqual(image.getpixel((2, 2))[3], 0)
        left, right = image.getpixel((16, 32)), image.getpixel((48, 32))
        self.assertGreater(left[0], left[2] + 90)
        self.assertGreater(right[2], right[0] + 90)
        self.assertTrue(126 <= left[3] <= 129)
        self.assertTrue(126 <= right[3] <= 129)
        self.assertEqual(image.getpixel((3, 32))[3], 0)

    def test_radial_gradient_and_local_inheritance_preserve_paint(self):
        source = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="64" height="64">
        <defs><radialGradient id="base"><stop stop-color="#fff"/>
        <stop offset="1" stop-color="#000"/></radialGradient>
        <radialGradient id="inherited" xlink:href="#base"/></defs>
        <circle cx="32" cy="32" r="24" fill="url(#inherited)"/></svg>'''
        image = self.image(source)
        self.assertGreater(image.getpixel((32, 32))[0], image.getpixel((53, 32))[0] + 150)
        self.assertEqual(image.getpixel((0, 0))[3], 0)

    def test_fixed_input_is_byte_reproducible_and_size_preserves_aspect(self):
        first = renderer.render_svg_text(GRADIENT_CLIP, 64)
        self.assertEqual(first, renderer.render_svg_text(GRADIENT_CLIP, 64))
        image = self.image('<svg xmlns="http://www.w3.org/2000/svg" width="80" height="40"><rect width="80" height="40" fill="#13579b"/></svg>', 64)
        self.assertEqual(image.size, (64, 32))
        self.assertEqual(image.getpixel((32, 16)), (19, 87, 155, 255))

    def test_cli_succeeds_with_paths_containing_spaces_and_rejects_unsafe_input(self):
        with tempfile.TemporaryDirectory(prefix="aikon raster ") as directory:
            source = Path(directory) / "source icon.svg"
            output = Path(directory) / "rendered icon.png"
            source.write_text(GRADIENT_CLIP, encoding="utf-8")
            command = [sys.executable, "-B", str(SCRIPT), str(source), "--output", str(output), "--size", "64"]
            result = subprocess.run(command, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["mode"], "RGBA")
            self.assertEqual(report["backend"]["version"], "0.5.0")
            good_png = output.read_bytes()
            source.write_text('<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.com/x"/></svg>', encoding="utf-8")
            rejected = subprocess.run(command, capture_output=True, text=True, timeout=15)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertFalse(json.loads(rejected.stderr)["ok"])
            self.assertEqual(output.read_bytes(), good_png)


if __name__ == "__main__":
    unittest.main()
