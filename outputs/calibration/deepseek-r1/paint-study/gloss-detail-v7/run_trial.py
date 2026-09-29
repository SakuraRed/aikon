"""One explicit SVG trial at a time, preserving source, render and metrics."""
from pathlib import Path
import sys,json,hashlib,copy,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
from tools.paint_checks import render_image
from gloss_paint import apply_gloss,tag

HERE=Path(__file__).resolve().parent
REV=ROOT/'outputs/calibration/deepseek-r1/revisions/v006'
plan_path=HERE/sys.argv[1]
out=HERE/plan_path.stem
out.mkdir(exist_ok=False)
before_svg=(REV/'short.svg').read_text(encoding='utf-8')
plan=json.loads(plan_path.read_text())
after_svg,fragments=apply_gloss(before_svg,plan)
(out/'before.svg').write_text(before_svg,encoding='utf-8')
(out/'after.svg').write_text(after_svg,encoding='utf-8')
(out/'open-rim-fragments.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1280">'+''.join(fragments)+'</svg>',encoding='utf-8')
before=render_image(before_svg,1280).convert('RGBA');before.save(out/'before.png')
after=render_image(after_svg,1280).convert('RGBA');after.save(out/'after.png')
source=Image.open(ROOT/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png').convert('RGBA')
a=np.asarray(before).astype(float);b=np.asarray(after).astype(float);s=np.asarray(source).astype(float)
aroot=ET.fromstring(before_svg);broot=ET.fromstring(after_svg)
original_paths={e.get('id'):e.get('d') for e in aroot.iter(tag('path')) if e.get('id')}
new_paths={e.get('id'):e.get('d') for e in broot.iter(tag('path')) if e.get('id')}
removed_allowed={i+'-'+suffix for i in ['eye-left','eye-right'] for suffix in ['inner-transition','inner-rim']}
preserved=all(new_paths.get(k)==v for k,v in original_paths.items() if k not in removed_allowed)
inputs=json.loads((HERE/'selected-input.json').read_text())
def metric(mask):
    result={'pixels':int(mask.sum())}
    for label,array in [('before',a),('after',b)]:
        diff=array[:,:,:3][mask]-s[:,:,:3][mask]
        result[label]={'mae':float(np.abs(diff).mean()),'rmse':float(np.sqrt((diff**2).mean()))}
    return result
report={'source_assisted_only':True,'source_sha256':hashlib.sha256((ROOT/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png').read_bytes()).hexdigest(),'all_existing_geometry_paths_preserved':preserved,'output_alpha_exactly_unchanged':bool(np.array_equal(a[:,:,3],b[:,:,3])),'changed_rgb_pixels':int(np.any(a[:,:,:3]!=b[:,:,:3],axis=2).sum()),'regions':{}}
changed=np.any(a[:,:,:3]!=b[:,:,:3],axis=2)
for region in inputs['regions']:
    identifier=region['id'];d=region['d']
    mask=np.asarray(render_image(f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1280"><path d="{d}" fill="white"/></svg>',1280))[:,:,3]>=128
    distance=distance_transform_edt(mask)
    external=distance_transform_edt(~mask)
    report['regions'][identifier]={'all':metric(mask),'inner_boundary_1_to_4px':metric(mask&(distance>1)&(distance<=4)),'core_beyond_6px':metric(mask&(distance>6)),'changed_pixels':int((changed&mask).sum())}
    if identifier.startswith('eye'):
        report['regions'][identifier]['outside_1_to_5px']=metric((~mask)&(external>1)&(external<=5))
boxes={'eye-left':(135,650,290,900),'eye-right':(565,810,720,1045),'fin':(978,960,1264,1155),'frill-white-05':(747,268,923,457)}
for name,box in boxes.items():
    w,h=box[2]-box[0],box[3]-box[1]
    board=Image.new('RGB',(w*6,h*2+26),(24,25,27));draw=ImageDraw.Draw(board)
    for i,(label,pic) in enumerate([('source',source),('v006 before',before),('trial after',after)]):
        crop=pic.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST)
        bg=Image.new('RGBA',crop.size,(15,15,15,255));bg.alpha_composite(crop)
        board.paste(bg.convert('RGB'),(i*w*2,26));draw.text((i*w*2+5,6),label,fill='white')
    board.save(out/(name+'-comparison.png'))
    for label,tree in [('before',aroot),('after',broot)]:
        cropped=copy.deepcopy(tree);cropped.set('width',str(w));cropped.set('height',str(h));cropped.set('viewBox',f'{box[0]} {box[1]} {w} {h}')
        (out/(name+'-'+label+'.svg')).write_text(ET.tostring(cropped,encoding='unicode'),encoding='utf-8')
full=Image.new('RGB',(1920,666),(24,25,27));draw=ImageDraw.Draw(full)
for i,(label,pic) in enumerate([('source',source),('v006 before',before),('trial after',after)]):
    crop=pic.resize((640,640),Image.Resampling.LANCZOS)
    bg=Image.new('RGBA',crop.size,(15,15,15,255));bg.alpha_composite(crop)
    full.paste(bg.convert('RGB'),(i*640,26));draw.text((i*640+5,6),label,fill='white')
full.save(out/'full-comparison.png')
(out/'metrics.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='regions'}))
for key,value in report['regions'].items():
    if value['changed_pixels']:
        print(key,json.dumps(value))
assert preserved and report['output_alpha_exactly_unchanged']
