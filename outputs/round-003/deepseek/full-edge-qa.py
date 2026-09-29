"""Bounded evidence only for r005/r006; no artwork mutation."""
from pathlib import Path
import os,threading,sys,json,hashlib
t=threading.Timer(45,lambda:os._exit(124));t.daemon=True;t.start()
from io import BytesIO
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];sys.path.insert(0,str(REPO))
from tools import render_svg,review_gloss_pairs as review,analyze_capsule_geometry as capsule
summaries=[]
for rev in ['r005','r006']:
    dest=ROOT/'full-revisions'/rev;svg=(dest/'full.svg').read_text(encoding='utf-8');root=render_svg.validate_svg(svg)
    qa=dest/'capsule';qa.mkdir(exist_ok=True);expected=[];visible=[];visibility=[]
    for name in ['eye-left','eye-right']:
        a=np.asarray(Image.open(BytesIO(render_svg.render_svg_text(review._eye_markup(root,name,False),1024))).convert('RGBA'))
        b=np.asarray(Image.open(BytesIO(render_svg.render_svg_text(review._eye_markup(root,name,True),1024))).convert('RGBA'))
        em=a[:,:,3].astype(float)/255;vm=b[:,:,0].astype(float)/255*(b[:,:,3].astype(float)/255)
        expected.append(em);visible.append(vm)
        Image.fromarray(np.rint(em*255).astype('uint8')).save(qa/(name+'-isolated.png'))
        Image.fromarray(np.rint(vm*255).astype('uint8')).save(qa/(name+'-visible.png'))
        visibility.append({'id':name,'visible_to_isolated_mass_ratio':float(np.minimum(em,vm).sum()/em.sum()),'absolute_mask_difference_sum':float(np.abs(em-vm).sum())})
    isolated_report=capsule.analyze_pair(expected);visible_report=capsule.analyze_pair(visible)
    result={'svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'isolation_method':'unmodified review_gloss_pairs._eye_markup at1024','isolated':isolated_report,'visible':visible_report,'visibility':visibility,'acceptance':'shape diagnostic only, not artwork acceptance'}
    (qa/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    board=Image.new('RGB',(960,410));dr=ImageDraw.Draw(board)
    for i,bg in enumerate(['#f6f4ee','#0f0f0f','#bcbcc5']):
        dr.rectangle((i*320,0,i*320+319,409),fill=bg)
        for yy,size in [(32,128),(220,48),(320,24)]:
            im=Image.open(dest/f'full-{size}.png').convert('RGBA');board.paste(im,(i*320+36,yy),im);dr.text((i*320+180,yy+4),f'{size}px',fill='#888888')
    board.save(dest/'inspection-board.png')
    summaries.append({'revision':rev,'sha256':result['svg_sha256'],'isolated_eye_status':[e['status'] for e in isolated_report['eyes']],'visible_eye_status':[e['status'] for e in visible_report['eyes']],'visibility':visibility})
out=Image.new('RGB',(1536,768),'#f1f1f5')
for col,rev in enumerate(['r004','r005','r006']):
    im=Image.open(ROOT/'full-revisions'/rev/'full-1280.png').convert('RGBA').resize((512,512),Image.Resampling.LANCZOS);out.paste(im,(col*512,35),im)
    ImageDraw.Draw(out).text((col*512+12,12),rev,fill='#343b57')
out.save(ROOT/'full-edge-repair-comparison.png')
print(json.dumps(summaries));t.cancel()
