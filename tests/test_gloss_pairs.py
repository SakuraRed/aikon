"""Real rendering controls for paired glossy SVGs, not aesthetic score tests."""

import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import review_gloss_pairs as review

HAS_RENDERER = all(importlib.util.find_spec(name) is not None for name in ("resvg_py", "PIL", "numpy", "scipy"))
SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
<defs><linearGradient id="hair"><stop stop-color="#475ca5"/><stop offset="1" stop-color="#6f8cd1"/></linearGradient>
<radialGradient id="eye"><stop stop-color="#303c55"/><stop offset="1" stop-color="#192038"/></radialGradient></defs>
<circle id="face" cx="64" cy="68" r="48" fill="#fff1e9"/>
<path id="bang" d="M20 44Q40 4 100 40L95 48Q75 26 20 44Z" fill="url(#hair)"/>
<ellipse id="eye-left" cx="45" cy="68" rx="7" ry="13" fill="url(#eye)"/>
<ellipse id="eye-right" cx="81" cy="68" rx="7" ry="13" fill="url(#eye)"/>
</svg>'''
FULL = SVG.replace('L95 48Q75 26 20 44Z', 'L96 55Q60 37 20 44Z')


class StructureTests(unittest.TestCase):
    def test_recolor_and_gradient_rewrite_do_not_create_new_geometry(self):
        first = review.analyze_svg(SVG)[1]
        recolor = SVG.replace('#fff1e9', '#bbccdd').replace('id="hair"', 'id="paint2"').replace('url(#hair)', 'url(#paint2)').replace('<linearGradient id="paint2">', '<linearGradient id="paint2" x2=".3">')
        self.assertEqual(first['geometry_sha256'], review.analyze_svg(recolor)[1]['geometry_sha256'])
        self.assertNotEqual(first['geometry_sha256'], review.analyze_svg(FULL)[1]['geometry_sha256'])

    def test_bitmap_filter_pattern_and_external_paint_are_rejected(self):
        for body in ('<image href="data:image/png;base64,AA=="/>', '<filter id="noise"><feTurbulence/></filter>', '<pattern id="dots" width="1" height="1"/>', '<rect fill="URL(https://example.com/x)"/>'):
            with self.subTest(body=body), self.assertRaises(ValueError):
                review.analyze_svg(SVG.replace('</svg>', body + '</svg>'))

    def test_gradient_stops_and_geometry_budgets_have_boundaries(self):
        cases = [SVG.replace('<stop offset="1" stop-color="#6f8cd1"/>', ''), SVG.replace('</linearGradient>', '<stop offset=".2" stop-color="#123456"/></linearGradient>'), SVG.replace('</svg>', '<circle r="1"/>' * 300 + '</svg>')]
        for source in cases:
            with self.subTest(length=len(source)), self.assertRaises(ValueError):
                review.analyze_svg(source)

    def test_missing_eye_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'eye-left'):
            review.analyze_svg(SVG.replace('id="eye-left"', 'id="unidentified"'))


@unittest.skipUnless(HAS_RENDERER, 'install optional requirements-ci.txt for raster checks')
class RasterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='aikon gloss ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pair = self.root / 'subject' / 'round-002'
        self.pair.mkdir(parents=True)

    def write_pair(self, short=SVG, full=FULL):
        (self.pair / 'short.svg').write_text(short, encoding='utf-8')
        (self.pair / 'full.svg').write_text(full, encoding='utf-8')

    def review(self):
        return review.review_pairs([self.pair], self.root / 'evidence', sizes=(128, 48, 24))

    def test_legal_smooth_gradient_eye_gloss_passes_actual_rendering(self):
        self.write_pair()
        report = self.review()
        self.assertEqual(report['status'], 'pass', report)
        pair = report['pairs'][0]
        self.assertGreater(pair['differences'][0]['changed_rgba_pixels'], 0)
        self.assertGreater(pair['differences'][0]['alpha_iou'], .99)
        for profile in pair['profiles'].values():
            self.assertTrue(profile['canonical_rerender_pixels_equal'])
            self.assertEqual(profile['pixels']['eyes']['eye-left']['visible_fraction'], 1)
            self.assertEqual(len(profile['renders'][0]['rgba_sha256']), 64)
        self.assertEqual(report['visual_review'], 'not_assessed')

    def test_exact_duplicate_is_rejected(self):
        self.write_pair(SVG, SVG)
        report = self.review()
        self.assertEqual(report['status'], 'fail')
        self.assertIn('exact_duplicate_svg', report['pairs'][0]['issues'])

    def test_color_only_difference_is_rejected_even_with_different_pixels(self):
        self.write_pair(SVG, SVG.replace('#fff1e9', '#eed9be'))
        report = self.review()
        pair = report['pairs'][0]
        self.assertEqual(report['status'], 'fail')
        self.assertIn('same_geometry_recolor_only', pair['issues'])
        self.assertGreater(pair['differences'][0]['changed_rgba_pixels'], 100)

    def test_hidden_geometry_addition_cannot_disguise_recolor_only_pair(self):
        hidden = SVG.replace('<circle id="face"', '<rect x="55" y="50" width="15" height="15" fill="#abc"/><circle id="face"').replace('#fff1e9', '#eed9be')
        self.write_pair(SVG, hidden)
        report = self.review()
        self.assertEqual(report['status'], 'fail')
        self.assertIn('no_visible_geometry_difference_at_128', report['pairs'][0]['issues'])

    def test_cached_png_noise_is_rejected_without_changing_svg(self):
        from PIL import Image
        self.write_pair()
        image = Image.open(io.BytesIO(review.renderer.render_svg_text(SVG, 128))).convert('RGBA')
        image.putpixel((65, 92), (131, 152, 135, 255))
        image.save(self.pair / 'short-128.png')
        report = self.review()
        short = report['pairs'][0]['profiles']['short']
        self.assertEqual(report['status'], 'fail')
        self.assertIn('cached_png_pixel_mismatch_at_128', short['issues'])
        self.assertEqual(short['renders'][0]['cached_preview']['mismatched_pixels'], 1)

    def test_png_metadata_or_compression_does_not_fake_contamination(self):
        from PIL import Image, PngImagePlugin
        self.write_pair()
        image = Image.open(io.BytesIO(review.renderer.render_svg_text(SVG, 128)))
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text('note', 'Different encoding, identical pixels')
        image.save(self.pair / 'short-128.png', compress_level=0, pnginfo=metadata)
        self.assertEqual(self.review()['status'], 'pass')

    def test_hidden_eye_and_cropped_eye_fail_real_depth_check(self):
        for source in (SVG.replace('</svg>', '<rect x="35" y="52" width="22" height="32" fill="#333"/></svg>'), SVG.replace('cx="45" cy="68"', 'cx="1" cy="68"')):
            with self.subTest(source=source):
                self.write_pair(source, FULL)
                record = self.review()['pairs'][0]['profiles']['short']
                self.assertEqual(record['status'], 'fail')
                self.assertIn('eye-left_not_fully_visible', record['issues'])

    def test_face_clip_cannot_conceal_a_cropped_eye(self):
        source = SVG.replace('</defs>', '<clipPath id="cut"><rect x="46" y="0" width="100" height="128"/></clipPath></defs>').replace('id="eye-left"', 'id="eye-left" clip-path="url(#cut)"')
        self.write_pair(source, FULL)
        short = self.review()['pairs'][0]['profiles']['short']
        self.assertIn('eye-left_not_fully_visible', short['issues'])

    def test_transparent_glaze_over_opaque_base_is_allowed_but_translucent_body_is_not(self):
        glaze = SVG.replace('</defs>', '<linearGradient id="glaze"><stop stop-color="#ffffff" stop-opacity=".1"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient></defs>').replace('</svg>', '<path d="M53 88Q64 85 75 88L70 98H58Z" fill="url(#glaze)"/></svg>')
        self.write_pair(glaze, FULL)
        self.assertEqual(self.review()['status'], 'pass')
        translucent = SVG.replace('r="48" fill=', 'r="48" opacity=".95" fill=')
        self.write_pair(translucent, FULL)
        self.assertIn('translucent_material_interior', self.review()['pairs'][0]['profiles']['short']['issues'])

    def test_sloping_outline_at_viewport_bottom_is_not_inferred_material_interior(self):
        # This real opaque polygon ends across the last raster row. Resvg's AA
        # is fractional there; no pixels below the viewport have been observed.
        garment = '<path d="M24 110H104V128.4L24 126.6Z" fill="#334455"/>'
        self.write_pair(SVG.replace('</svg>', garment + '</svg>'), FULL)
        result = self.review()
        self.assertEqual(result['status'], 'pass')
        alpha = result['pairs'][0]['profiles']['short']['pixels']['alpha']
        self.assertEqual(alpha['interior_alpha_below_254'], 0)
        self.assertGreater(alpha['viewport_boundary']['partial_alpha_candidates'], 0)
        self.assertEqual(alpha['viewport_boundary']['status'], 'not_classified_as_material_interior')

    def test_same_sloping_edge_moved_inside_with_shared_boundary_still_fails(self):
        # Complementary opaque shapes independently antialias their shared line.
        # Without overlap, source-over composition leaves a real alpha seam.
        garment = '<path d="M24 110H104V120.4L24 118.6Z" fill="#334455"/><path d="M24 118.6L104 120.4V130H24Z" fill="#445566"/>'
        self.write_pair(SVG.replace('</svg>', garment + '</svg>'), FULL)
        result = self.review()
        self.assertEqual(result['status'], 'fail')
        short = result['pairs'][0]['profiles']['short']
        self.assertIn('translucent_material_interior', short['issues'])
        self.assertGreater(short['pixels']['alpha']['interior_alpha_below_254'], 0)
        self.assertLess(short['pixels']['alpha']['defect_bbox_xyxy'][3], 126)

    def test_cli_has_real_multisize_hash_evidence_and_exit_status(self):
        self.write_pair()
        command = [sys.executable, '-B', str(ROOT / 'tools/review_gloss_pairs.py'), '--pair-dir', str(self.pair), '--output', str(self.root / 'cli')]
        process = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)
        prefix, payload = process.stdout.strip().split(' ', 1)
        self.assertEqual(prefix, 'AIKON_GLOSS_EVIDENCE')
        result = json.loads(payload)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual([row['size'] for row in result['pairs'][0]['profiles']['full']['renders']], [1024, 128, 48, 24])


ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    unittest.main()
