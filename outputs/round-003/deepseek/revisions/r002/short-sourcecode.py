from pathlib import Path
import os,sys,threading,json,hashlib,shutil,xml.etree.ElementTree as ET
t=threading.Timer(45,lambda:os._exit(124));t.daemon=True;t.start()
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text,validate_svg,backend_info
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
path=REPO/'outputs/calibration/deepseek-r1/independent-consumer-round3/r004/short.svg';base=path.read_text(encoding='utf-8');root=ET.fromstring(base)
root.find('{'+NS+'}title').text='DeepSeek short — transparent supervised r1 derivation'
root.find('{'+NS+'}desc').text='Transparent subject, source-projection crop preserved. Hooked forelock, blue head fin with light edge, side bow and pleated headband are user-bound r1 identity. Derived from independent supervised r004, not a new blind test. Unaccepted candidate.'
svg=ET.tostring(root,encoding='unicode');validate_svg(svg)
rev=ROOT/'revisions/r002';rev.mkdir(parents=True,exist_ok=True)
(ROOT/'short.svg').write_text(svg,encoding='utf-8');(rev/'short.svg').write_text(svg,encoding='utf-8')
report={'revision':'r002','derivation':'supervised r004 derivation, not fresh blind test','base_sha256':hashlib.sha256(base.encode()).hexdigest(),'short_sha256':hashlib.sha256(svg.encode()).hexdigest(),'background_fill':None,'subject_crop':'preserved for source projection, not a background tile','primitive_validation':'passed generic safe-vector validation','artistic_acceptance':'not assessed','full_status':'not delivered; user selected fixing outfit reference first','renderings':{}}
for size in [1280,128,48,24]:
    data=render_svg_text(svg,size);(ROOT/f'short-{size}.png').write_bytes(data);(rev/f'short-{size}.png').write_bytes(data)
    report['renderings'][str(size)]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
a=np.asarray(Image.open(ROOT/'short-1280.png').convert('RGBA'));b=np.asarray(Image.open(path.parent/'preview-1280.png').convert('RGBA'))
report['rendered_RGBA_identical_to_r004']=bool(np.array_equal(a,b));report['alpha']={'transparent_pixels':int((a[:,:,3]==0).sum()),'opaque_pixels':int((a[:,:,3]==255).sum()),'upper_right_alpha':int(a[50,1200,3])}
board=Image.new('RGB',(960,410));d=ImageDraw.Draw(board)
for i,bg in enumerate(['#f6f4ee','#0f0f0f','#bcbcc5']):
    d.rectangle((i*320,0,i*320+319,409),fill=bg)
    for yy,s in [(32,128),(220,48),(320,24)]:
        im=Image.open(ROOT/f'short-{s}.png').convert('RGBA');board.paste(im,(i*320+36,yy),im);d.text((i*320+180,yy+4),f'{s}px',fill='#888888')
board.save(ROOT/'short-inspection-board.png')
(ROOT/'short-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
shutil.copy2(ROOT/'short-finalize.py',rev/'short-sourcecode.py');shutil.copy2(ROOT/'short-r002.prompt.zh-CN.md',rev/'short.prompt.zh-CN.md')
print(json.dumps(report));t.cancel()
