"""Render the saved SVGs, preserve renderer metadata, and build a local review sheet."""
from pathlib import Path
import sys
import json
import hashlib

HERE = Path(__file__).resolve().parent
REPO = next(parent for parent in HERE.parents if (parent / 'tools' / 'render_svg.py').exists())
sys.path.insert(0, str(REPO))
from tools.render_svg import render_svg_file
from PIL import Image, ImageDraw

def main():
    reports={}
    for profile in ('short','full'):
        reports[profile]={}
        for size in (1024,128,48,24):
            reports[profile][str(size)]=render_svg_file(HERE/f'{profile}.svg',HERE/f'{profile}-{size}.png',size)
    sheet=Image.new('RGB',(1032,700),'#e9edf0')
    draw=ImageDraw.Draw(sheet)
    for index,profile in enumerate(('short','full')):
        x=8+index*516
        draw.text((x,8),profile,fill='#1b2735')
        rgba=Image.open(HERE/f'{profile}-1024.png').convert('RGBA').resize((500,500),Image.Resampling.LANCZOS)
        sheet.paste(rgba,(x,28),rgba)
        for offset,size in enumerate((128,48,24)):
            thumb=Image.open(HERE/f'{profile}-{size}.png').convert('RGBA')
            px=x+offset*166
            draw.text((px,546),str(size)+' px',fill='#1b2735')
            sheet.paste(thumb,(px,568),thumb)
    sheet.save(HERE/'review-sheet.png')
    reports['scope']={'mechanical_render':'completed','artistic_acceptance':'pending user','image_generation_model_used':False,'small_previews':'actual renders, not downsampled 1024 image'}
    (HERE/'render-report.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({p: {'svg':reports[p]['1024']['source_sha256'],'png1024':reports[p]['1024']['png_sha256']} for p in ('short','full')},indent=2))

if __name__=='__main__':
    main()
