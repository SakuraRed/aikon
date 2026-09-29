from pathlib import Path
import threading, os, sys, copy, json, hashlib, re, shutil
t=threading.Timer(45,lambda:os._exit(124));t.daemon=True;t.start()
import numpy as np
from PIL import Image, ImageDraw
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent; REPO=ROOT.parents[3]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text,validate_svg
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
raw=np.asarray(Image.open(REPO/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png').convert('RGBA'))
root=ET.parse(ROOT/'r001/short.svg').getroot(); parts={e.get('id'):e for e in root.iter() if e.get('id')}
shutil.copy2(ROOT/'draw.py',ROOT/'r001/sourcecode.py')
shutil.copy2(ROOT/'actualprompt.md',ROOT/'r001/actualprompt.md')

# Same shared boundary, opposite direction: removes exposed dark support sliver.
left=parts['left-sweep'];d=left.get('d')
d=d.replace('C431.321 266.000 367.000 346.941 354.000 403.000','C452.820 274.000 379.000 363.000 354.000 403.000')
left.set('d',d)

# Observe the finite lower free-lock region: pale blue vs darker rear hair.
# Threshold only selects the semantic boundary; it is not exported as fragments.
samples=[]
for y in range(990,1257,2):
    row=raw[y,:,:3]; xx=np.arange(1280)
    m=(xx>=820)&(xx<=1000)&(row[:,0]<145)&(row[:,1]>117)&(row[:,2]>174)&(row[:,2].astype(float)-row[:,1]>40)
    x=np.where(m)[0]
    if len(x): samples.append([int(x.max())+.5,float(y)])
samples=np.array(samples)
def fit_x_y(ya,yb,xa,xb):
    dat=samples[(samples[:,1]>=ya)&(samples[:,1]<=yb)]
    u=(dat[:,1]-ya)/(yb-ya)
    B=np.column_stack((3*(1-u)**2*u,3*(1-u)*u*u))
    rhs=dat[:,0]-(1-u)**3*xa-u**3*xb
    ctrl=np.linalg.lstsq(B,rhs,rcond=None)[0]
    pred=(1-u)**3*xa+B@ctrl+u**3*xb
    return [ctrl[0],ya+(yb-ya)/3,ctrl[1],ya+2*(yb-ya)/3,xb,yb],float(np.abs(pred-dat[:,0]).mean())
join=float(np.interp(1150,samples[:,1],samples[:,0]));c1,e1=fit_x_y(978,1150,992,join);c2,e2=fit_x_y(1150,1256,join,838)
lock=parts['right-main-lock'];d=lock.get('d')
old='C993.915 1109.518 959.138 1184.323 918.000 1247.000 C870.000 1252.715 890.000 1294.266 838.000 1256.000'
replacement='C'+' '.join(f'{q:.3f}' for q in c1)+' C'+' '.join(f'{q:.3f}' for q in c2)
assert old in d;lock.set('d',d.replace(old,replacement))

dest=ROOT/'r002';dest.mkdir(exist_ok=True)
svg=ET.tostring(root,encoding='unicode');validate_svg(svg)
(dest/'short.svg').write_text(svg,encoding='utf-8')
for size in [1280,128,48,24]:(dest/f'preview-{size}.png').write_bytes(render_svg_text(svg,size))
shutil.copy2(ROOT/'revise.py',dest/'sourcecode.py');shutil.copy2(ROOT/'revision-prompt.md',dest/'actualprompt.md')
out=np.asarray(Image.open(dest/'preview-1280.png').convert('RGBA'))
mask=(raw[:,:,:3].max(2)>30)&(raw[:,:,3]>200)
rgb=raw[:,:,:3]*(raw[:,:,3:4]/255)+15*(1-raw[:,:,3:4]/255)
pred=out[:,:,:3]*(out[:,:,3:4]/255)+15*(1-out[:,:,3:4]/255)
err=pred-rgb
report={'revision':'r002','svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'measured_lower_lock_boundary':samples.tolist(),'piecewise_cubic_controls':[c1,c2],'mean_horizontal_fit_residual_px':[e1,e2],'diagnostic_only':{'mask':'source maxRGB>30 and alpha>200, no exclusions; not frozen comparator','MAE':float(np.abs(err[mask]).mean()),'RMSE':float(np.sqrt((err[mask]**2).mean()))},'acceptance':'unassessed'}
(dest/'measurements.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
pair=Image.new('RGB',(1280,640),(15,15,15))
for i,a in enumerate([raw,out]):
    im=Image.fromarray(a).resize((640,640),Image.Resampling.LANCZOS);pair.paste(im,(i*640,0),im)
pair.save(dest/'reference-comparison.png')
board=Image.new('RGB',(960,410));dr=ImageDraw.Draw(board)
for i,bg in enumerate(['#f6f4ee','#0f0f0f','#bcbcc5']):
    dr.rectangle((i*320,0,i*320+319,409),fill=bg)
    for y,s in [(32,128),(220,48),(320,24)]:
        im=Image.open(dest/f'preview-{s}.png').convert('RGBA');board.paste(im,(i*320+36,y),im)
        dr.text((i*320+181,y+4),f'{s} px',fill='#888888')
board.save(dest/'inspection-board.png')
for name in ['short.svg','preview-1280.png','preview-128.png','preview-48.png','preview-24.png','reference-comparison.png','inspection-board.png']:
    shutil.copy2(dest/name,ROOT/name)
print(json.dumps({'revision':'r002','diagnostic':report['diagnostic_only'],'contour_fit_px':[e1,e2]}));t.cancel()
