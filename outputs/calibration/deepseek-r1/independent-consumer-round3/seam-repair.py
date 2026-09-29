"""r004 one-shot local paint continuity repair, preserving original geometry."""
from pathlib import Path
import os,sys,threading,json,copy,hashlib,shutil
t=threading.Timer(45,lambda:os._exit(124));t.daemon=True;t.start()
import numpy as np
from PIL import Image,ImageDraw
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[3]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text,validate_svg
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
def tag(n):return '{'+NS+'}'+n
base=(ROOT/'r003/short.svg').read_text(encoding='utf-8');root=ET.fromstring(base)
old={e.get('id'):copy.deepcopy(e) for e in root.iter() if e.get('id')}
defs=root.find(tag('defs'));g=root.find(tag('g'))
parts={e.get('id'):e for e in g}

# r003 has a exposed 1–3 px crown sliver between the center-fringe and main
# lock around y490–520. Continue the right-lock material through that sliver.
# Its finite rectangular paint support is hidden by the unchanged opaque
# neighboring objects on every other edge; it introduces no artwork outline.
clip=ET.SubElement(defs,tag('clipPath'),{'id':'upper-fringe-seam-support-clip'})
ET.SubElement(clip,tag('rect'),{'x':'690','y':'440','width':'70','height':'100'})
support=copy.deepcopy(parts['hair-crown-parent']);support.set('id','upper-fringe-seam-support')
support.set('fill','url(#measured-right-main-lock)');support.set('clip-path','url(#upper-fringe-seam-support-clip)')
g.insert(list(g).index(parts['hair-crown-parent'])+1,support)

# The premature upper cap is not a new source material. Share the crown's
# existing continuous field at the top, then analytically taper its coverage
# into the existing main-lock field. No blur and no new hard transition edge.
fade=ET.SubElement(defs,tag('linearGradient'),{'id':'upper-fringe-material-fade','gradientUnits':'userSpaceOnUse','x1':'0','y1':'340','x2':'0','y2':'440'})
for z,a in [(0,1),(.3,1),(.55,.8),(.8,.3),(1,0)]:
    ET.SubElement(fade,tag('stop'),{'offset':str(z),'stop-color':'#ffffff','stop-opacity':str(a)})
mask=ET.SubElement(defs,tag('mask'),{'id':'upper-fringe-material-mask','maskUnits':'userSpaceOnUse','x':'0','y':'0','width':'1280','height':'1280'})
ET.SubElement(mask,tag('rect'),{'x':'0','y':'0','width':'1280','height':'1280','fill':'url(#upper-fringe-material-fade)'})
cap=copy.deepcopy(parts['right-main-lock']);cap.set('id','upper-fringe-shared-crown-field')
cap.set('fill','url(#measured-hair-crown-parent)');cap.set('mask','url(#upper-fringe-material-mask)')
g.insert(list(g).index(parts['right-main-lock'])+1,cap)

# Every original ID's attributes, geometry, children and paint remain exact.
now={e.get('id'):e for e in root.iter() if e.get('id')}
for name,e in old.items():
    if name=='portrait':continue
    assert ET.tostring(e)==ET.tostring(now[name]),name
svg=ET.tostring(root,encoding='unicode');validate_svg(svg)
dest=ROOT/'r004';dest.mkdir(exist_ok=True)
(dest/'short.svg').write_text(svg,encoding='utf-8')
for size in [1280,128,48,24]:(dest/f'preview-{size}.png').write_bytes(render_svg_text(svg,size))
shutil.copy2(ROOT/'seam-repair.py',dest/'sourcecode.py');shutil.copy2(ROOT/'r004-prompt.md',dest/'actualprompt.md')
raw=np.asarray(Image.open(REPO/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png').convert('RGBA'))
prev=np.asarray(Image.open(ROOT/'r003/preview-1280.png').convert('RGBA'));out=np.asarray(Image.open(dest/'preview-1280.png').convert('RGBA'))
def comp(a):
    c=a[:,:,3:4].astype(float)/255;return a[:,:,:3].astype(float)*c+15*(1-c)
ref=comp(raw);before=comp(prev);after=comp(out)
roi=(slice(320,610),slice(610,810));target=(slice(340,540),slice(650,750))
def metrics(a):
    d=a-ref;return {'ROI_MAE':float(np.abs(d[roi]).mean()),'target_MAE':float(np.abs(d[target]).mean()),'full_canvas_MAE':float(np.abs(d).mean()),'full_canvas_RMSE':float(np.sqrt((d*d).mean()))}
diagnosis=json.loads((ROOT/'seam-diagnosis.json').read_text(encoding='utf-8'))
side=[]
for sample in diagnosis['boundary_samples']:
    x=sample['boundary_x'];y=sample['y']
    side.append({'x':x,'y':y,'source_jump':sample['source_jump'],'r003_jump':sample['r003_jump'],'r004_jump':float(np.linalg.norm(after[y,x+4]-after[y,x-4]))})
changed=np.any(prev!=out,axis=2);y,x=np.nonzero(changed)
report={'revision':'r004','base_sha256':hashlib.sha256(base.encode()).hexdigest(),'svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'original_IDs_attributes_and_children_identical':True,'crop_and_all_original_path_d_unchanged':True,'alpha_bytes_identical':bool(np.array_equal(prev[:,:,3],out[:,:,3])),'added_parts':['upper-fringe-seam-support','upper-fringe-shared-crown-field'],'before':metrics(before),'after':metrics(after),'changed_pixels':len(x),'changed_bbox':[int(x.min()),int(y.min()),int(x.max()),int(y.max())],'boundary_two_side_samples':side,'recommendation':'r004' if metrics(after)['ROI_MAE']<metrics(before)['ROI_MAE'] else 'retain-r003','acceptance':'pending parent frozen comparator and visual review'}
(dest/'measurements.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
pair=Image.new('RGB',(1200,580))
for i,a in enumerate([ref,before,after]):pair.paste(Image.fromarray(np.rint(a[roi]).astype('uint8')).resize((400,580)),(i*400,0))
pair.save(dest/'local-source-r003-r004.png')
full=Image.new('RGB',(1280,640),(15,15,15))
for i,a in enumerate([raw,out]):
    im=Image.fromarray(a).resize((640,640),Image.Resampling.LANCZOS);full.paste(im,(i*640,0),im)
full.save(dest/'reference-comparison.png')
board=Image.new('RGB',(960,410));dr=ImageDraw.Draw(board)
for i,bg in enumerate(['#f6f4ee','#0f0f0f','#bcbcc5']):
    dr.rectangle((i*320,0,i*320+319,409),fill=bg)
    for yy,size in [(32,128),(220,48),(320,24)]:
        im=Image.open(dest/f'preview-{size}.png').convert('RGBA');board.paste(im,(i*320+36,yy),im)
        dr.text((i*320+181,yy+4),f'{size} px',fill='#888888')
board.save(dest/'inspection-board.png')
print(json.dumps(report));t.cancel()
