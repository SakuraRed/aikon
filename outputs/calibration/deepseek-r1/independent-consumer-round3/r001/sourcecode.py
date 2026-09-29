"""Supervised reference-based repair of own independent baseline; 45 s wall stop."""
from pathlib import Path
import sys, os, threading, json, hashlib, copy, re, time
timer=threading.Timer(45,lambda:os._exit(124)); timer.daemon=True; timer.start()
import numpy as np
from PIL import Image, ImageDraw
from io import BytesIO
from scipy import ndimage as ndi
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text, validate_svg, backend_info
NS='http://www.w3.org/2000/svg'; ET.register_namespace('',NS)
def tag(n): return '{'+NS+'}'+n
baseline=REPO/'outputs/calibration/deepseek-r1/independent-consumer-round2/short.svg'
reference=REPO/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png'
ref=np.asarray(Image.open(reference).convert('RGBA'))
tree=ET.fromstring(baseline.read_text(encoding='utf-8'))
defs=tree.find(tag('defs')); group=tree.find(tag('g'))
parts=list(group); measurements={}
def serialize(t): return ET.tostring(t,encoding='unicode')
def render(t): return np.asarray(Image.open(BytesIO(render_svg_text(serialize(t),1280))).convert('RGBA'))
def owners(t):
    t=copy.deepcopy(t); g=t.find(tag('g'))
    for i,e in enumerate(g):
        e.set('fill',f'#{i+1:02x}0000'); e.attrib.pop('stroke',None)
    a=render(t); return a[:,:,0],a[:,:,3]
owner,alpha=owners(tree)
# Source boundary candidates are actual high spatial-derivative locations.
# This is an edge measurement, not palette quantization or a region tessellation.
rgb=ref[:,:,:3].astype(float)
gx=ndi.sobel(rgb,axis=1)/8; gy=ndi.sobel(rgb,axis=0)/8
strength=np.sqrt((gx*gx+gy*gy).sum(axis=2))
ys,xs=np.nonzero(strength>12)
edge_tree=cKDTree(np.column_stack((xs,ys)))
def parse_path(d):
    tok=re.findall(r'[MLCHVZmlchvz]|[-+]?(?:\d*\.\d+|\d+)',d)
    segments=[]; p=np.zeros(2); start=p.copy(); n=0
    while n<len(tok):
        op=tok[n]; n+=1
        count={'M':2,'L':2,'C':6,'H':1,'V':1,'Z':0}[op]
        v=np.array([float(q) for q in tok[n:n+count]]); n+=count
        if op=='M': p=v.copy();start=p.copy();segments.append((op,v.copy(),None))
        elif op=='C': segments.append((op,v.copy(),p.copy()));p=v[-2:].copy()
        elif op=='L': segments.append((op,v.copy(),p.copy()));p=v.copy()
        elif op=='H': segments.append((op,v.copy(),p.copy()));p[0]=v[0]
        elif op=='V': segments.append((op,v.copy(),p.copy()));p[1]=v[0]
        else: segments.append((op,v.copy(),p.copy()));p=start.copy()
    return segments

# Curves keep their endpoints and topology. Sparse interior controls move only
# where the reference contains a strong boundary close to the exposed curve.
geometry_ids={'right-main-lock','hair-crown-parent','left-sweep','center-fringe','right-inner-fringe','identity-crescent','headband-fold-parent','frill-left','frill-center','frill-center-right','frill-upper-right','frill-mid-right','frill-side','frill-side-bottom','rear-hair','rear-frill-support','rear-frill-light','rear-frill-center','rear-frill-end','bow-left','bow-right'}
for idx,e in enumerate(parts):
    if e.get('id') not in geometry_ids: continue
    segs=parse_path(e.get('d')); rewritten=[]; before=[];after=[]; fitted=0
    for op,v,p0 in segs:
        if op=='C':
            ctr=v.reshape(3,2); ts=np.linspace(.03,.97,34)
            basis=np.array([(1-ts)**3,3*(1-ts)**2*ts,3*(1-ts)*ts**2,ts**3]).T
            points=basis@np.vstack([p0,ctr]); pix=np.rint(points).astype(int)
            valid=(pix[:,0]>=3)&(pix[:,0]<1277)&(pix[:,1]>=3)&(pix[:,1]<1277)
            for j in np.where(valid)[0]:
                x,y=pix[j]; patch=owner[y-2:y+3,x-2:x+3]
                valid[j]=np.any(patch==idx+1) and np.any(patch!=idx+1)
            dist,ind=edge_tree.query(points)
            valid &= dist<18
            if valid.sum()>=7:
                b=basis[valid]; tgt=np.column_stack((xs[ind[valid]],ys[ind[valid]]))
                old=ctr[:2].copy(); A=b[:,1:3]
                rhs=tgt-b[:,0,None]*p0-b[:,3,None]*ctr[2]
                reg=.16
                new=np.linalg.lstsq(np.vstack((A,np.eye(2)*reg)),np.vstack((rhs,old*reg)),rcond=None)[0]
                new=np.clip(new,old-24,old+24)
                pred=b@np.vstack((p0,new,ctr[2]))
                before.extend(dist[valid].tolist()); after.extend(np.linalg.norm(pred-tgt,axis=1).tolist())
                ctr[:2]=new;v=ctr.ravel();fitted+=1
        rewritten.append(op+(' '.join(f'{q:.3f}' for q in v) if len(v) else ''))
    e.set('d',' '.join(rewritten))
    measurements[e.get('id')]={'fitted_cubic_segments':fitted,'exposed_samples':len(before),'edge_distance_before':float(np.mean(before)) if before else None,'fit_residual':float(np.mean(after)) if after else None}

# Explicit measured correction at the lower free tip: same source contour,
# preserved topology; source tip is y~1256 rather than baseline 1278.
lock=next(e for e in parts if e.get('id')=='right-main-lock')
d=lock.get('d').replace('838.000 1278.000','838.000 1256.000')
lock.set('d',d)
owner,alpha=owners(tree)

def hexc(v): return '#'+''.join(f'{int(q):02x}' for q in np.clip(np.rint(v),0,255))
paint_report={}
for idx,e in enumerate(parts):
    name=e.get('id')
    if name in {'eye-left-rim','eye-right-rim','fringe-shadow-left','fringe-shadow-right'}: continue
    mask=ndi.binary_erosion(owner==idx+1,iterations=4)
    # Remove misregistered boundaries using local chromatic consistency with
    # own original rendered material, and sample finite analytic fields only.
    y,x=np.nonzero(mask)
    if len(x)<70: continue
    stride=max(1,len(x)//2500); x=x[::stride];y=y[::stride]; target=rgb[y,x]
    if name.startswith('eye-'):
        ok=(target.max(1)<90)
    elif name=='face-parent':
        ok=(target[:,0]>215)&(target[:,1]>185)&(target[:,2]>175)
    elif name.startswith('cheek-'):
        ok=(target[:,0]>230)&(target[:,0]-target[:,1]>15)
    elif 'frill' in name or name.startswith('headband'):
        ok=(target.min(1)>145)&(np.abs(target[:,0]-target[:,1])<24)
    else:
        ok=(target[:,2]-target[:,0]>25)&(target[:,2]-target[:,1]>20)
    x=x[ok];y=y[ok];target=target[ok]
    if len(x)<50: continue
    if name=='face-parent':
        # Physically simple model: warm base with one soft elliptical white
        # illumination, plus a weak vertical base tint. No texture primitives.
        xx=x/1280;yy=y/1280
        def predict(p):
            t=yy[:,None]
            base=p[:3]*(1-t)+p[3:6]*t
            r=np.sqrt(((xx-p[6])/p[8])**2+((yy-p[7])/p[9])**2)
            a=np.clip(1-r,0,1)**p[10]
            return base*(1-a[:,None])+255*a[:,None]
        init=[255,239,227,249,233,229,.29,.72,.68,.63,1.6]
        lo=[235,205,195,230,205,195,0,.45,.2,.2,.25]
        hi=[255,255,255,255,255,255,.7,1.,1.5,1.5,5.]
        opt=least_squares(lambda p:(predict(p)-target).ravel(),init,bounds=(lo,hi),max_nfev=90,loss='soft_l1',f_scale=3)
        p=opt.x; gid='measured-face-base'
        g=ET.SubElement(defs,tag('linearGradient'),{'id':gid,'gradientUnits':'userSpaceOnUse','x1':'0','x2':'0','y1':'0','y2':'1280'})
        for z,c in [(0,p[:3]),(1,p[3:6])]:ET.SubElement(g,tag('stop'),{'offset':str(z),'stop-color':hexc(c)})
        e.set('fill','url(#'+gid+')')
        rg=ET.SubElement(defs,tag('radialGradient'),{'id':'measured-face-light','gradientUnits':'userSpaceOnUse','cx':'0','cy':'0','r':'1','gradientTransform':f'translate({p[6]*1280} {p[7]*1280}) scale({p[8]*1280} {p[9]*1280})'})
        for z in np.linspace(0,1,13): ET.SubElement(rg,tag('stop'),{'offset':f'{z:.6f}','stop-color':'#ffffff','stop-opacity':f'{(1-z)**p[10]:.6f}'})
        light=copy.deepcopy(e);light.set('id','face-continuous-illumination');light.set('fill','url(#measured-face-light)');group.insert(list(group).index(e)+1,light)
        paint_report[name]={'samples':len(x),'model':'linear base plus elliptical white illumination','fit_mae':float(np.abs(predict(p)-target).mean()),'parameters':p.tolist()}
        continue
    # One continuous low-frequency field for each named material. Direction is
    # fitted from a robust RGB plane; six knots preserve smooth broad lighting.
    X=np.column_stack((np.ones(len(x)),x/1280,y/1280))
    coeff=np.linalg.lstsq(X,target,rcond=None)[0]
    direction=coeff[1:,:].mean(axis=1)
    if np.linalg.norm(direction)<.3:
        color=np.median(target,axis=0);e.set('fill',hexc(color));paint_report[name]={'samples':len(x),'model':'solid','color':hexc(color)};continue
    direction/=np.linalg.norm(direction)
    xy=np.column_stack((x,y)); proj=xy@direction
    low=float(proj.min());high=float(proj.max());span=max(1,high-low)
    t=np.clip((proj-low)/span,0,1);knots=np.linspace(0,1,6)
    B=np.array([np.maximum(0,1-np.abs(t-z)*5) for z in knots]).T
    # Endpoint priors prevent narrow-tip extrapolation into invented highlights.
    cols=np.linalg.lstsq(B,target,rcond=None)[0]
    for j in range(6): cols[j]=np.clip(cols[j],np.percentile(target,1,axis=0)-2,np.percentile(target,99,axis=0)+2)
    gid='measured-'+name
    g=ET.SubElement(defs,tag('linearGradient'),{'id':gid,'gradientUnits':'userSpaceOnUse','x1':str(direction[0]*low),'y1':str(direction[1]*low),'x2':str(direction[0]*high),'y2':str(direction[1]*high)})
    for z,c in zip(knots,cols):ET.SubElement(g,tag('stop'),{'offset':str(z),'stop-color':hexc(c)})
    e.set('fill','url(#'+gid+')')
    paint_report[name]={'samples':len(x),'model':'continuous six-stop linear field','fit_mae':float(np.abs(B@cols-target).mean()),'range': [hexc(c) for c in cols],'direction':direction.tolist()}

rev=ROOT/'r001';rev.mkdir(exist_ok=True)
svg=serialize(tree);validate_svg(svg)
(rev/'short.svg').write_text(svg,encoding='utf-8')
for size in [1280,128,48,24]:(rev/f'preview-{size}.png').write_bytes(render_svg_text(svg,size))
out=np.asarray(Image.open(rev/'preview-1280.png').convert('RGBA'))
subject=(ref[:,:,:3].max(2)>30)&(ref[:,:,3]>200)
# Fixed diagnostic only; independent parent frozen comparator remains authority.
bg=15; src=rgb*(ref[:,:,3:4]/255)+bg*(1-ref[:,:,3:4]/255)
out_rgb=out[:,:,:3]*(out[:,:,3:4]/255)+bg*(1-out[:,:,3:4]/255)
diff=out_rgb-src
report={'experiment':'supervised independent repair','baseline_sha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),'svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'backend':backend_info(),'geometry':measurements,'paint':paint_report,'diagnostic_only':{'mask':'source maxRGB>30 and alpha>200, no exclusions; not frozen comparator','MAE':float(np.abs(diff[subject]).mean()),'RMSE':float(np.sqrt((diff[subject]**2).mean()))},'acceptance':'unassessed'}
(rev/'measurements.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
pair=Image.new('RGB',(1280,640),(15,15,15))
for i,a in enumerate([ref,out]):
    im=Image.fromarray(a).resize((640,640),Image.Resampling.LANCZOS);pair.paste(im,(i*640,0),im)
pair.save(rev/'reference-comparison.png')
# Mark measured raw high-contrast locations against the unwarped source.
overlay=Image.fromarray(ref).convert('RGB');dr=ImageDraw.Draw(overlay)
for i,e in enumerate(parts):
    if e.get('id') not in geometry_ids:continue
    for op,v,p in parse_path(e.get('d')):
        if op!='C':continue
        tt=np.linspace(0,1,24);bb=np.array([(1-tt)**3,3*(1-tt)**2*tt,3*(1-tt)*tt**2,tt**3]).T
        pp=bb@np.vstack((p,v.reshape(3,2)));dr.line([tuple(q) for q in pp],fill=(255,70,50),width=1)
overlay.save(rev/'measured-boundary-overlay.png')
print(json.dumps({'revision':'r001','diagnostic':report['diagnostic_only'],'parts':len(list(group)),'fitted_parts':sum(v['fitted_cubic_segments']>0 for v in measurements.values())}))
timer.cancel()
