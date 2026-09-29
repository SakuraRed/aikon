"""First bounded repair: single outer clip with opaque local material support.

Transforms actual r004 geometry; does not recreate or trace artwork. All original
semantic paths and their geometry properties remain. New clip contours are exact
vector copies/unions and do not come from a raster segmentation.
"""
from pathlib import Path
from io import BytesIO
import copy
import hashlib
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO))
from tools.render_svg import render_svg_text,validate_svg,backend_info
from tools.analyze_edge_quality import analyze_svg_edges,save_evidence
from PIL import Image,ImageDraw,ImageFont
import numpy as np

NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
def node(tag,attrs):return ET.Element('{'+NS+'}'+tag,attrs)
def byid(tree,name):return next(e for e in tree.iter() if e.get('id')==name)
def digest(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()


def clockwise_polygon(d):
    tokens=re.findall(r'[A-Za-z]|[-+]?(?:\d*\.\d+|\d+)',d)
    if set(t for t in tokens if t.isalpha())-{'M','L','Z'}:
        raise ValueError('Mask union expects original straight polygons only')
    nums=[float(t) for t in tokens if not t.isalpha()]
    if len(nums)%2:raise ValueError('invalid coordinate count')
    points=list(zip(nums[::2],nums[1::2]))
    area=sum(x1*y2-x2*y1 for (x1,y1),(x2,y2) in zip(points,points[1:]+points[:1]))
    if area<0:points.reverse()
    return 'M '+' L '.join(f'{x:g} {y:g}' for x,y in points)+' Z'


def repair(svg,branch,profile):
    tree=ET.fromstring(svg);defs=next(e for e in tree if e.tag.endswith('}defs'))
    old_geometry={e.get('id'):{k:v for k,v in e.attrib.items() if k in ('d','transform','x','y','width','height','cx','cy','rx','ry')} for e in tree.iter() if e.get('id')}
    changes=[]
    if branch=='masked':
        mask=byid(tree,'originium-suppressor');original=list(mask)
        compound=' '.join(clockwise_polygon(e.get('d')) for e in original)
        cp=node('clipPath',{'id':'suppressor-shared-outer-clip','clipPathUnits':'userSpaceOnUse'})
        cp.append(node('path',{'id':'suppressor-union-contour','d':compound,'clip-rule':'nonzero'}));defs.append(cp)
        shared=node('g',{'id':'suppressor-shared-material','clip-path':'url(#suppressor-shared-outer-clip)'})
        shared.append(node('rect',{'id':'suppressor-opaque-local-support','x':'100','y':'380','width':'840','height':'600','fill':byid(tree,'suppressor-under-body').get('fill')}))
        for child in original:mask.remove(child);shared.append(child)
        mask.append(shared)
        changes.append('One nonzero exact polygon-union clip for mask; opaque support underneath unchanged original panel paths.')
    if profile=='full':
        face=byid(tree,'outer-collar-right-face');fold=byid(tree,'outer-collar-right-fold')
        parent=next(e for e in tree.iter() if face in list(e));idx=list(parent).index(face)
        if list(parent)[idx+1] is not fold:raise ValueError('Unexpected right-collar draw order')
        cp=node('clipPath',{'id':'collar-right-shared-outer-clip','clipPathUnits':'userSpaceOnUse'})
        cp.append(node('path',{'id':'collar-right-visible-contour','d':face.get('d')}));defs.append(cp)
        shared=node('g',{'id':'collar-right-shared-material','clip-path':'url(#collar-right-shared-outer-clip)'})
        shared.append(node('rect',{'id':'collar-right-opaque-local-support','x':'700','y':'900','width':'440','height':'560','fill':face.get('fill')}))
        parent.remove(face);parent.remove(fold);shared.append(face);shared.append(fold);parent.insert(idx,shared)
        changes.append('Original right-collar face clips an opaque local support and unchanged face/fold paints once.')
    for original_id,attrs in old_geometry.items():
        updated=byid(tree,original_id)
        actual={k:v for k,v in updated.attrib.items() if k in ('d','transform','x','y','width','height','cx','cy','rx','ry')}
        if actual!=attrs:raise ValueError('Original geometry changed '+original_id)
    for e in tree:
        if e.tag.endswith('}title'):e.text=f'Female Endministrator {branch} {profile} r005'
    result=ET.tostring(tree,encoding='unicode')+'\n';validate_svg(result)
    return result,{'original_semantic_geometry_unchanged':True,'original_ids_verified':len(old_geometry),'changes':changes,'background_added':False}


def fixed_crop_board(before,after,box,output):
    canvas=Image.new('RGB',(1536,888),'#eeeeee');d=ImageDraw.Draw(canvas)
    for col,(label,maps,key) in enumerate((('r004 native',before,'candidate'),('r004 4xBOX',before,'reference'),('r005 native',after,'candidate'),('r005 4xBOX',after,'reference'))):
        for row,bg in enumerate(('light','dark')):
            crop=Image.fromarray(maps[key+'_'+bg]).crop(box).resize((384,384),Image.Resampling.NEAREST)
            canvas.paste(crop,(col*384,row*444+38));d.text((col*384+8,row*444+12),label+' / '+bg,fill='#202020')
    canvas.save(output)


def main():
    summaries=[]
    for branch,profile in (('unmasked','full'),('masked','short'),('masked','full')):
        base=ROOT/branch/profile/'revisions'/'r004';out=base.parent/'r005'
        if not (out/'prompt.zh-CN.md').exists():raise SystemExit('Save prompt first')
        if (out/'icon.svg').exists():raise SystemExit('No overwrite')
        svg=(base/'icon.svg').read_text(encoding='utf-8');new,record=repair(svg,branch,profile)
        (out/'icon.svg').write_text(new,encoding='utf-8');shutil.copy2(__file__,out/'sourcecode.py')
        record.update({'branch':branch,'profile':profile,'revision':'r005','parent':'r004','before_sha256':digest(svg),'svg_sha256':digest(new),'renderer':backend_info(),'user_acceptance':'unassessed','reference_similarity_99':'not_assessed'})
        for size in (1280,128,48,24):(out/f'preview-{size}.png').write_bytes(render_svg_text(new,size))
        old=np.asarray(Image.open(base/'preview-1280.png').convert('RGBA'));current=np.asarray(Image.open(out/'preview-1280.png').convert('RGBA'))
        record['alpha_identical_1280']=bool(np.array_equal(old[:,:,3],current[:,:,3]));record['changed_rgba_pixels_1280']=int(np.any(old!=current,axis=2).sum())
        before_report,before_maps=analyze_svg_edges(svg,size=256);after_report,after_maps=analyze_svg_edges(new,size=256)
        quality=out/'quality';save_evidence(quality/'edges',after_report,after_maps)
        box=json.loads((ROOT/'quality-r004'/f'{branch}-{profile}'/'edges'/'local-crop-location.json').read_text())['box_pixels']
        fixed_crop_board(before_maps,after_maps,box,quality/'same-location-before-after.png')
        oldmax=before_report['metrics']['local_color']['largest_bad_pixel_count'];newmax=after_report['metrics']['local_color']['largest_bad_pixel_count']
        record['edge_before']={'status':before_report['status'],'largest_cluster':oldmax}
        record['edge_after']={'status':after_report['status'],'largest_cluster':newmax,'issues':after_report['issues']}
        (out/'revision.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');summaries.append(record)
        print(json.dumps({'branch':branch,'profile':profile,'before':oldmax,'after':newmax,'alpha_identical':record['alpha_identical_1280'],'status':after_report['status']}))
    (ROOT/'repair-r005-report.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
