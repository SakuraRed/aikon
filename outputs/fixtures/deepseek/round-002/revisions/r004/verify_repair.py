#!/usr/bin/env python3
"""Compare the real archived r003 and repaired r004; optional render dependencies."""
from pathlib import Path
import hashlib
import json
import sys
from PIL import Image

REV = Path(__file__).resolve().parent
ROUND = REV.parents[1]
ROOT = ROUND.parents[3]
sys.path.insert(0, str(ROOT))
from tools.render_svg import render_svg_text

old = Image.open(ROUND/'revisions/r003/full-1024.png').convert('RGBA')
new = Image.open(ROUND/'full-1024.png').convert('RGBA')
changed = [(x,y) for y in range(1024) for x in range(1024) if old.getpixel((x,y)) != new.getpixel((x,y))]
target = [(x,y) for y in range(632,648) for x in range(60,63)]
bad_before = [(x,y) for x,y in target if old.getpixel((x,y))[3] < 255]
bad_after = [(x,y) for x,y in bad_before if new.getpixel((x,y))[3] < 255]
old_short = (ROUND/'revisions/r003/short.svg').read_bytes()
assert old_short == (ROUND/'short.svg').read_bytes()
short_checks = {}
for size in (1024,128,48,24):
    expected = render_svg_text(old_short.decode('utf-8'),size)
    actual = (ROUND/f'short-{size}.png').read_bytes()
    short_checks[str(size)] = actual == expected
    assert short_checks[str(size)]
assert not bad_after, bad_after
report = {
    'source_revision': 'r003', 'repair_revision': 'r004',
    'changed_pixels_1024': len(changed),
    'changed_bbox_1024': [min(x for x,y in changed),min(y for x,y in changed),max(x for x,y in changed)+1,max(y for x,y in changed)+1],
    'reported_roi_nonopaque_before': len(bad_before), 'same_pixels_nonopaque_after':len(bad_after),
    'same_pixels_alpha_after':sorted(set(new.getpixel(p)[3] for p in bad_before)),
    'short_svg_byte_equal':True, 'short_png_vs_archived_svg':short_checks,
    'full_svg_sha256':hashlib.sha256((ROUND/'full.svg').read_bytes()).hexdigest(),
    'full_png_sha256':hashlib.sha256((ROUND/'full-1024.png').read_bytes()).hexdigest(),
    'method':'Opaque left side-hair material overlap path; no filter, blur, canvas fill or threshold change.',
    'independent_validation':'requested separately; this file reports only local repair checks',
    'user_acceptance':'pending',
}
(REV/'repair-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
