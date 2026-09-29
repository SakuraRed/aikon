"""Check actual changed pixels and crease coverage against the frozen face."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from tools.render_svg import render_svg_text

BASE=Path(__file__).resolve().parent
NS='{http://www.w3.org/2000/svg}'

def alpha(svg):return np.asarray(Image.open(io.BytesIO(render_svg_text(svg,1280))).convert('RGBA'))[:,:,3]

def main():
    geometry=BASE/'paint-study/natural-fields-v6/final-fit/geometry-input/geometry.json'
    g=json.loads(geometry.read_text(encoding='utf-8'))
    face=np.asarray(Image.open(geometry.parent/'masks/face.png').convert('L'))>127
    rows=[];images=[]
    for name in ('v005','v006'):
        p=BASE/'revisions'/name/'short.svg';text=p.read_text(encoding='utf-8');root=ET.fromstring(text)
        subset=ET.Element(NS+'svg',{'width':'1280','height':'1280','viewBox':'0 0 1280 1280'})
        subset.append(copy.deepcopy(root.find(NS+'defs')))
        target=next(x for x in root.iter() if x.get('id')=='hair-right-face-crease')
        target=copy.deepcopy(target);target.set('fill','white')
        ownership=next((x for x in root.iter() if x.get('id')=='right-face-crease-ownership'),None)
        if ownership is not None:
            container=ET.SubElement(subset,NS+'g',dict(ownership.attrib));container.append(target)
        else:subset.append(target)
        coverage=alpha(ET.tostring(subset,encoding='unicode'))
        overlap=(coverage>=128)&face
        ys,xs=np.nonzero(overlap)
        rows.append({'revision':name,'svg_file_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                     'face_overlap_pixels':int(overlap.sum()),
                     'face_overlap_deeper_than_2px':int((overlap&(ndi.distance_transform_edt(face)>2)).sum()),
                     'bbox':None if not len(xs) else [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]})
        images.append(np.asarray(Image.open(io.BytesIO(render_svg_text(text,1280))).convert('RGBA')))
    changed=np.any(images[0]!=images[1],axis=2);ys,xs=np.nonzero(changed)
    record={'schema':'aikon.actual-owner-revision-check.v1','geometry_sha256':hashlib.sha256(geometry.read_bytes()).hexdigest(),
            'records':rows,'changed_pixels':int(changed.sum()),'changed_bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],
            'alpha_unchanged':bool(np.array_equal(images[0][:,:,3],images[1][:,:,3])),
            'meaning':'Real rendered ownership, not mask-only check; AA boundary overlap separately visible. Not whole artwork acceptance.'}
    (BASE/'revisions/v006/owner-regression.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))
    if rows[0]['face_overlap_deeper_than_2px']==0 or rows[1]['face_overlap_deeper_than_2px']!=0 or not record['alpha_unchanged']:
        raise SystemExit('Expected negative-to-positive owner repair not proven')

if __name__=='__main__':main()
