#!/usr/bin/env python3
"""Optional real render/evidence step; invoke with the repo validation environment."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from tools.render_svg import render_svg_file
from PIL import Image, ImageDraw


def main():
    spec = importlib.util.spec_from_file_location('deepseek_original', HERE/'generate.py')
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    reports = {}
    for profile in ('short', 'full'):
        source = (HERE/(profile+'.svg')).read_bytes()
        expected = generator.generate(profile).encode('utf-8')
        assert source == expected == generator.generate(profile).encode('utf-8')
        parsed = ET.fromstring(source)
        assert all(node.attrib.get('opacity','1') == '1' for node in parsed.iter())
        reports[profile] = {'repeated_generation_byte_equal': True, 'source_sha256': hashlib.sha256(source).hexdigest(), 'renders': {}}
        for size in (1024,128,48,24):
            reports[profile]['renders'][str(size)] = render_svg_file(HERE/(profile+'.svg'), HERE/f'{profile}-{size}.png', size)
    board = Image.new('RGB', (1120,750), '#f3f1ed')
    draw = ImageDraw.Draw(board)
    for col, profile in enumerate(('short','full')):
        draw.text((36+col*560,18), 'DEEPSEEK / '+profile.upper()+' / ROUND 002', fill='#243451')
        source = Image.open(HERE/f'{profile}-1024.png').convert('RGBA')
        source.thumbnail((512,512), Image.Resampling.LANCZOS)
        board.paste(source,(24+col*560,46),source)
        x=40+col*560
        for size in (128,48,24):
            sample = Image.open(HERE/f'{profile}-{size}.png').convert('RGBA')
            board.paste(sample,(x,590),sample)
            draw.text((x,725),str(size)+'px', fill='#243451')
            x += size+35
    board.save(HERE/'overview.png')
    (HERE/'render-report.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'profiles':2,'renders':8,'repeat_equal':True,'output':str(HERE)},ensure_ascii=False))


if __name__ == '__main__':
    main()
