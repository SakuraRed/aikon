"""Formal DeepSeek pair derivation. Every invocation hard-limited to 45s."""
from pathlib import Path
import os,threading,sys,json,hashlib,copy,shutil
timer=threading.Timer(45,lambda:os._exit(124));timer.daemon=True;timer.start()
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text,validate_svg,backend_info
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
def tag(n):return '{'+NS+'}'+n
basepath=REPO/'outputs/calibration/deepseek-r1/independent-consumer-round3/r004/short.svg'
base=basepath.read_text(encoding='utf-8');tree=ET.fromstring(base)
oldpaths={e.get('id'):e.get('d') for e in tree.iter(tag('path'))}
group=tree.find(tag('g'));assert group.get('clip-path')=='url(#canvas-crop)'
group.attrib.pop('clip-path')
defs=tree.find(tag('defs'));defs.remove(next(e for e in defs if e.get('id')=='canvas-crop'))
tree.find(tag('title')).text='DeepSeek short — supervised r1 derivation, transparent'
tree.find(tag('desc')).text='User-bound r1 whale-girl identity; hooked forelock, head fin, bow and pleated headband. Natural projected capsule eyes. Independent r004 derivation with frame crop removed; unaccepted candidate.'
assert {e.get('id'):e.get('d') for e in group.iter(tag('path'))}=={k:v for k,v in oldpaths.items() if k and k!='canvas-crop'}
svg=ET.tostring(tree,encoding='unicode');validate_svg(svg)
revision=ROOT/'revisions/r001';revision.mkdir(parents=True,exist_ok=True)
(ROOT/'short.svg').write_text(svg,encoding='utf-8');(revision/'short.svg').write_text(svg,encoding='utf-8')
report={'derivation':'supervised repair, not new blind test','base':str(basepath.relative_to(REPO)),'base_sha256':hashlib.sha256(base.encode()).hexdigest(),'short_sha256':hashlib.sha256(svg.encode()).hexdigest(),'subject_path_d_unchanged':True,'whole_tile_clip_removed':True,'canvas_background_paths':0,'backend':backend_info(),'acceptance':'unassessed','renderings':{}}
for size in [1280,128,48,24]:
    data=render_svg_text(svg,size);(ROOT/f'short-{size}.png').write_bytes(data);(revision/f'short-{size}.png').write_bytes(data)
    report['renderings'][str(size)]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
a=np.asarray(Image.open(ROOT/'short-1280.png').convert('RGBA'))
report['alpha']={'fully_opaque_pixels':int((a[:,:,3]==255).sum()),'fully_transparent_pixels':int((a[:,:,3]==0).sum()),'right_upper_1200_50':int(a[50,1200,3])}
board=Image.new('RGB',(960,410));d=ImageDraw.Draw(board)
for i,bg in enumerate(['#f6f4ee','#0f0f0f','#bcbcc5']):
    d.rectangle((i*320,0,i*320+319,409),fill=bg)
    for y,size in [(32,128),(220,48),(320,24)]:
        im=Image.open(ROOT/f'short-{size}.png').convert('RGBA');board.paste(im,(i*320+36,y),im);d.text((i*320+180,y+4),f'{size}px',fill='#888888')
board.save(ROOT/'short-inspection-board.png')
(ROOT/'short-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
shutil.copy2(ROOT/'draw.py',revision/'short-sourcecode.py');shutil.copy2(ROOT/'short.prompt.zh-CN.md',revision/'short.prompt.zh-CN.md')
print(json.dumps(report));timer.cancel()
