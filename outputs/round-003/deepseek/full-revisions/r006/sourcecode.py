from pathlib import Path
import os,threading,sys,json,hashlib,copy,shutil,xml.etree.ElementTree as ET
t=threading.Timer(45,lambda:os._exit(124));t.daemon=True;t.start()
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text,validate_svg
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
def tag(n):return '{'+NS+'}'+n
base=(ROOT/'full-revisions/r005/full.svg').read_text(encoding='utf-8');tree=ET.fromstring(base)
ids={e.get('id'):e for e in tree.iter() if e.get('id')};defs=tree.find(tag('defs'));head=ids['full-r1-head']
clip=ET.SubElement(defs,tag('clipPath'),{'id':'full-face-hair-owner-clip','clipPathUnits':'userSpaceOnUse'})
for name in ['face-parent','hair-crown-parent','left-sweep','center-fringe','right-inner-fringe','right-main-lock']:
    ET.SubElement(clip,tag('path'),{'d':ids[name].get('d')})
names=['full-face-single-coverage','fringe-shadow-left','fringe-shadow-right','full-hair-single-coverage']
core=ET.Element(tag('g'),{'id':'full-face-hair-opaque-owner','clip-path':'url(#full-face-hair-owner-clip)'})
index=min(list(head).index(ids[name]) for name in names)
ids['full-face-single-coverage'].attrib.pop('clip-path')
for name in names:e=ids[name];head.remove(e);core.append(e)
head.insert(index,core)
ids['full-neck-shoulder-opaque-support'].set('d','M 240 1330 C 290 1340 368 1320 500 1350 L 500 1410 C 410 1410 312 1396 240 1380 Z')
svg=ET.tostring(tree,encoding='unicode');validate_svg(svg)
dest=ROOT/'full-revisions/r006';dest.mkdir(parents=True,exist_ok=True)
(dest/'full.svg').write_text(svg,encoding='utf-8')
for size in [1280,128,48,24]:(dest/f'full-{size}.png').write_bytes(render_svg_text(svg,size))
shutil.copy2(ROOT/'full-edge-fix2.py',dest/'sourcecode.py');shutil.copy2(ROOT/'full-r006.prompt.zh-CN.md',dest/'actualprompt.md')
(dest/'change-record.json').write_text(json.dumps({'base_sha256':hashlib.sha256(base.encode()).hexdigest(),'svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'original_d_unchanged':True,'material_gradients_unchanged':True,'purpose':'shared opaque head support across hair/face joint, fixed edge gate'},indent=2),encoding='utf-8')
print(hashlib.sha256(svg.encode()).hexdigest());t.cancel()
