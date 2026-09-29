from pathlib import Path
import os,threading,sys,json,hashlib,copy,shutil,xml.etree.ElementTree as ET
t=threading.Timer(45,lambda:os._exit(124));t.daemon=True;t.start()
from PIL import Image
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text,validate_svg
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
def tag(n):return '{'+NS+'}'+n
base=(ROOT/'full-revisions/r004/full.svg').read_text(encoding='utf-8');tree=ET.fromstring(base)
ids={e.get('id'):e for e in tree.iter() if e.get('id')};defs=tree.find(tag('defs'));head=ids['full-r1-head'];stage=ids['full-composition']

hair_ids=['hair-crown-parent','upper-fringe-seam-support','left-sweep','left-sweep-fold','left-sweep-deep-fold','center-fringe','center-curl-fold','right-inner-fringe','right-inner-fold','right-main-lock','upper-fringe-shared-crown-field','right-lock-fold']
outer=['hair-crown-parent','left-sweep','center-fringe','right-inner-fringe','right-main-lock']
clip=ET.SubElement(defs,tag('clipPath'),{'id':'full-hair-owner-clip','clipPathUnits':'userSpaceOnUse'})
for name in outer:ET.SubElement(clip,tag('path'),{'d':ids[name].get('d')})
group=ET.Element(tag('g'),{'id':'full-hair-single-coverage','clip-path':'url(#full-hair-owner-clip)'})
index=min(list(head).index(ids[name]) for name in hair_ids)
for name in hair_ids:
    e=ids[name];head.remove(e)
    if name in outer:
        e.set('stroke',e.get('fill'));e.set('stroke-width','8');e.set('stroke-linejoin','round')
    group.append(e)
head.insert(index,group)

faceclip=ET.SubElement(defs,tag('clipPath'),{'id':'full-face-owner-clip','clipPathUnits':'userSpaceOnUse'})
ET.SubElement(faceclip,tag('path'),{'d':ids['face-parent'].get('d')})
face=ET.Element(tag('g'),{'id':'full-face-single-coverage','clip-path':'url(#full-face-owner-clip)'})
index=list(head).index(ids['face-parent'])
for name in ['face-parent','face-continuous-illumination']:
    e=ids[name];head.remove(e);e.set('stroke',e.get('fill'));e.set('stroke-width','8');e.set('stroke-linejoin','round');face.append(e)
head.insert(index,face)

support=ET.Element(tag('path'),{'id':'full-neck-shoulder-opaque-support','d':'M 180 1300 C 280 1340 385 1315 500 1350 L 515 1410 C 430 1430 315 1380 180 1375 Z','fill':'url(#full-dress-field)'})
stage.insert(list(stage).index(ids['full-selected-maid-attire']),support)
svg=ET.tostring(tree,encoding='unicode');validate_svg(svg)
dest=ROOT/'full-revisions/r005';dest.mkdir(parents=True,exist_ok=True)
(dest/'full.svg').write_text(svg,encoding='utf-8')
for size in [1280,128,48,24]:(dest/f'full-{size}.png').write_bytes(render_svg_text(svg,size))
shutil.copy2(ROOT/'full-edge-fix.py',dest/'sourcecode.py');shutil.copy2(ROOT/'full-r005.prompt.zh-CN.md',dest/'actualprompt.md')
(dest/'change-record.json').write_text(json.dumps({'base_sha256':hashlib.sha256(base.encode()).hexdigest(),'svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'original_d_unchanged':True,'material_gradients_unchanged':True,'support_stroke_raw_width':8,'purpose':'single outer coverage with opaque material support; frozen gate unchanged'},indent=2),encoding='utf-8')
print(hashlib.sha256(svg.encode()).hexdigest());t.cancel()
