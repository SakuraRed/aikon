from pathlib import Path
import os,threading,sys,json,hashlib,shutil,xml.etree.ElementTree as ET
t=threading.Timer(45,lambda:os._exit(124));t.daemon=True;t.start()
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text,validate_svg
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
base=(ROOT/'full-revisions/r003/full.svg').read_text(encoding='utf-8');tree=ET.fromstring(base)
e=next(e for e in tree.iter() if e.get('id')=='full-back-hair-parent');d=e.get('d')
assert d.startswith('M 735 1100 C 952 1092 1077 1197 1168 1340')
e.set('d',d.replace('M 735 1100 C 952 1092 1077 1197 1168 1340','M 735 800 C 924 813 1041 879 1098 1023 C 1130 1152 1156 1245 1168 1340',1))
svg=ET.tostring(tree,encoding='unicode');validate_svg(svg)
dest=ROOT/'full-revisions/r004';dest.mkdir(parents=True,exist_ok=True)
(dest/'full.svg').write_text(svg,encoding='utf-8')
for s in [1280,128,48,24]:(dest/f'full-{s}.png').write_bytes(render_svg_text(svg,s))
shutil.copy2(ROOT/'full-support-fix.py',dest/'sourcecode.py');shutil.copy2(ROOT/'full-r004.prompt.zh-CN.md',dest/'actualprompt.md')
for n in ['full.svg','full-1280.png','full-128.png','full-48.png','full-24.png']:shutil.copy2(dest/n,ROOT/n)
board=Image.new('RGB',(960,410));dr=ImageDraw.Draw(board)
for i,bg in enumerate(['#f6f4ee','#0f0f0f','#bcbcc5']):
    dr.rectangle((i*320,0,i*320+319,409),fill=bg)
    for y,s in [(32,128),(220,48),(320,24)]:
        im=Image.open(dest/f'full-{s}.png').convert('RGBA');board.paste(im,(i*320+36,y),im);dr.text((i*320+180,y+4),f'{s}px',fill='#888888')
board.save(dest/'inspection-board.png');board.save(ROOT/'full-inspection-board.png')
overview=Image.new('RGB',(1536,820),'#edeef3');dr=ImageDraw.Draw(overview)
for i,profile in enumerate(['short','full']):
    im=Image.open(ROOT/f'{profile}-1280.png').convert('RGBA').resize((768,768),Image.Resampling.LANCZOS);overview.paste(im,(i*768,40),im);dr.text((i*768+24,16),profile.upper(),fill='#343b57')
overview.save(ROOT/'pair-overview.png')
small=Image.new('RGB',(768,560),'#eeeef2');dr=ImageDraw.Draw(small)
for row,bg in enumerate(['#f6f4ee','#0f0f0f']):
    dr.rectangle((0,row*280,768,row*280+279),fill=bg)
    for col,profile in enumerate(['short','full']):
        dr.text((col*384+20,row*280+12),profile.upper(),fill='#888888')
        for x,s in [(20,128),(190,48),(290,24)]:
            im=Image.open(ROOT/f'{profile}-{s}.png').convert('RGBA');small.paste(im,(col*384+x,row*280+65),im)
small.save(ROOT/'pair-small-sizes.png')
a=np.asarray(Image.open(dest/'full-1280.png').convert('RGBA'));p=np.asarray(Image.open(ROOT/'full-revisions/r003/full-1280.png').convert('RGBA'));yy,xx=np.nonzero(np.any(a!=p,2))
report=json.loads((ROOT/'full-revisions/r003/validation.json').read_text(encoding='utf-8'));report.pop('changed_from_r002_bbox',None)
report.update({'revision':'r004','svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'base_sha256':hashlib.sha256(base.encode()).hexdigest(),'changed_from_r003_bbox':[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())],'change':'continuous opaque parent support at fin root; no new ornament','alpha':{'transparent_pixels':int((a[:,:,3]==0).sum()),'opaque_pixels':int((a[:,:,3]==255).sum()),'upper_right_alpha':int(a[50,1200,3])}})
(dest/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(ROOT/'full-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report));t.cancel()
