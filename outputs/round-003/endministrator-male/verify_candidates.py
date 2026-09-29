"""Bounded artifact checks; no threshold tuning or aesthetic pass inference."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
OUT=Path(__file__).resolve().parent
from tools.render_svg import render_svg_text, validate_svg
from tools.analyze_edge_quality import analyze_svg_edges
from tools.analyze_capsule_geometry import extract_dark_roi, analyze_pair
from PIL import Image,ImageDraw
import numpy as np

def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

parser=argparse.ArgumentParser();parser.add_argument('--revision',default='r004');args=parser.parse_args()
revision=args.revision
base_revision='r003' if revision=='r004' else 'r002'
reports=[]
for branch in ('masked','unmasked'):
 for profile in ('short','full'):
  p=OUT/branch/profile/'revisions'/revision
  q=p/'quality';q.mkdir(exist_ok=True)
  svg=(p/f'{profile}.svg').read_text(encoding='utf-8')
  root=validate_svg(svg)
  original=Image.open(p/'preview-1280.png').convert('RGBA')
  raw=np.array(original)
  repeat={}
  for size in (1280,128,48,24):
   fresh=Image.open(io.BytesIO(render_svg_text(svg,size))).convert('RGBA')
   cached=Image.open(p/f'preview-{size}.png').convert('RGBA')
   repeat[str(size)]={'RGBA_equal':fresh.tobytes()==cached.tobytes(),'cached_sha256':hashlib.sha256((p/f'preview-{size}.png').read_bytes()).hexdigest()}
  edge,maps=analyze_svg_edges(svg,size=256)
  write(q/'edges.json',edge)
  a=Image.fromarray(maps['candidate_light']).convert('RGB');b=Image.fromarray(maps['reference_light']).convert('RGB')
  bd=Image.new('RGB',(512,256),'white');bd.paste(a,(0,0));bd.paste(b,(256,0));bd.save(q/'native-vs-area.png')
  heat=np.clip(maps['color_error']*5,0,255).astype('uint8');Image.fromarray(heat).save(q/'color-error-x5.png')
  top=edge['metrics']['local_color']['top_clusters']
  if top:
   x0,y0,x1,y1=top[0]['bbox_pixels'];box=(max(0,x0-8),max(0,y0-8),min(256,x1+8),min(256,y1+8))
   left=a.crop(box).resize((400,400),Image.Resampling.NEAREST);right=b.crop(box).resize((400,400),Image.Resampling.NEAREST)
   crop=Image.new('RGB',(800,400));crop.paste(left,(0,0));crop.paste(right,(400,0));crop.save(q/'largest-cluster.png')
  if branch=='unmasked':
   items=([(90,620,270,925),(510,730,695,1030)],[(170,780),(600,850)]) if profile=='short' else ([(95,500,255,765),(450,600,615,855)],[(175,620),(520,730)])
   masks=[extract_dark_roi(original,box,seed,max_channel=100) for box,seed in zip(*items)]
   capsule=analyze_pair(masks)
   capsule['extraction']={'mode':'actual rendered dark connected component','bboxes':items[0],'seeds':items[1],'max_channel':100,'threshold_not_used_as_style_acceptance':True}
   write(q/'capsules.json',capsule)
   for index,mask in enumerate(masks):Image.fromarray((mask*255).astype('uint8')).save(q/f'eye-{index+1}-actual-mask.png')
   eyes=[r['status'] for r in capsule['eyes']]
  else:eyes='not applicable: user-authorized real opaque eye occlusion; no eye geometry added'
  previous=np.array(Image.open(OUT/branch/profile/'revisions'/base_revision/'preview-1280.png').convert('RGBA'))
  report={'branch':branch,'profile':profile,'revision':revision,'svg_sha256':hashlib.sha256((p/f'{profile}.svg').read_bytes()).hexdigest(),'normalized_source_sha256':hashlib.sha256(svg.encode()).hexdigest(),'hash_note':'svg_sha256 hashes raw file bytes; edge source_sha256 hashes decoded newline-normalized source text on Windows. Both are recorded, not interchanged.','static_svg_subset':'pass','rerender':repeat,'transparent_pixels':int((raw[:,:,3]==0).sum()),'opaque_pixels':int((raw[:,:,3]==255).sum()),'partially_covered_pixels':int(((raw[:,:,3]>0)&(raw[:,:,3]<255)).sum()),'base_revision':base_revision,'changed_pixels_from_base':int(np.any(raw!=previous,axis=2).sum()),'capsules':eyes,'edge_status':edge['status'],'edge_local_bad_pixels':edge['metrics']['local_color']['largest_bad_pixel_count'],'edge_interior_alpha_bad_pixels':edge['metrics']['interior_alpha']['bad_pixels'],'paint_status':'not assessed: no independent material masks/field model for this new geometry; visual review and no-noise construction are separate evidence','identity_and_pitch':'human visual review required; no numeric resemblance assertion','visual_acceptance':'not_user_accepted'}
  write(q/'summary.json',report);reports.append(report)
write(OUT/f'quality-summary-{revision}.json',{'candidates':reports,'thresholds':'unchanged existing frozen capsule and edge rules','global_status':'candidate evidence, not complete art acceptance'})
print(json.dumps(reports,ensure_ascii=False,indent=2))
