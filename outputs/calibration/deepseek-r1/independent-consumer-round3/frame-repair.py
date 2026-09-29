"""r003: fit only raw alpha's rounded frame; preserve all non-crop SVG bytes."""
from pathlib import Path
import os,sys,threading,json,re,hashlib,shutil
timer=threading.Timer(45,lambda:os._exit(124));timer.daemon=True;timer.start()
import numpy as np
from PIL import Image,ImageDraw
from scipy.optimize import minimize_scalar
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from io import BytesIO
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[3]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text,validate_svg
refpath=REPO/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png'
raw=np.asarray(Image.open(refpath).convert('RGBA'));alpha=raw[:,:,3].astype(float)/255
corners=[alpha,alpha[:,::-1],alpha[::-1,:],alpha[::-1,::-1]]
samples=[]
for ci,a in enumerate(corners):
    for y in range(3,281):
        row=a[y,:320];cross=np.where(row>=.5)[0]
        if not len(cross) or cross[0]==0:continue
        j=int(cross[0]);x=j-.5+(.5-row[j-1])/(row[j]-row[j-1])
        samples.append((ci,x,y+.5))
s=np.asarray(samples)
def predict(r,y):return r-np.sqrt(np.maximum(0,r*r-(y-r)**2))
opt=minimize_scalar(lambda r:np.mean((predict(r,s[:,2])-s[:,1])**2),bounds=(285,315),method='bounded',options={'xatol':1e-9})
r=float(opt.x);k=4*(np.sqrt(2)-1)/3;q=r*(1-k);n=1280-r
d=(f'M {r:.6f} 0 H {n:.6f} C {1280-q:.6f} 0 1280 {q:.6f} 1280 {r:.6f} '
   f'V {n:.6f} C 1280 {1280-q:.6f} {1280-q:.6f} 1280 {n:.6f} 1280 '
   f'H {r:.6f} C {q:.6f} 1280 0 {1280-q:.6f} 0 {n:.6f} '
   f'V {r:.6f} C 0 {q:.6f} {q:.6f} 0 {r:.6f} 0 Z')
before=(ROOT/'r002/short.svg').read_text(encoding='utf-8')
pattern=r'(<clipPath id="canvas-crop"><path d=")([^"]+)(")'
hit=re.search(pattern,before);assert hit
after=before[:hit.start(2)]+d+before[hit.end(2):]
assert re.sub(pattern,r'\1FRAME\3',before)==re.sub(pattern,r'\1FRAME\3',after)
validate_svg(after)
dest=ROOT/'r003';dest.mkdir(exist_ok=True)
(dest/'short.svg').write_text(after,encoding='utf-8')
for size in [1280,128,48,24]:(dest/f'preview-{size}.png').write_bytes(render_svg_text(after,size))
shutil.copy2(ROOT/'frame-repair.py',dest/'sourcecode.py');shutil.copy2(ROOT/'r003-prompt.md',dest/'actualprompt.md')
def frame(d):
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 1280"><path d="{d}" fill="white"/></svg>'
    return np.asarray(Image.open(BytesIO(render_svg_text(svg,1280))).convert('RGBA'))[:,:,3]
old_frame=frame(hit.group(2));new_frame=frame(d);ra=raw[:,:,3]
old=np.asarray(Image.open(ROOT/'r002/preview-1280.png').convert('RGBA'));new=np.asarray(Image.open(dest/'preview-1280.png').convert('RGBA'))
def comp(a):
    cov=a[:,:,3:4].astype(float)/255
    return a[:,:,:3].astype(float)*cov+15*(1-cov)
rgb=comp(raw);inside=(ra==255);source_subject=(raw[:,:,:3].max(2)>30)&inside
alpha_band=np.abs(old_frame.astype(float)-ra.astype(float))>1
def metrics(a,f):
    err=comp(a)-rgb;fm=f>=128;rm=ra>=128
    by,bx=np.nonzero(fm&~ndi.binary_erosion(fm));ty,tx=np.nonzero(rm&~ndi.binary_erosion(rm))
    distance=cKDTree(np.column_stack((tx,ty))).query(np.column_stack((bx,by)))[0]
    return {'full_canvas_rgb_MAE':float(np.abs(err).mean()),'full_canvas_rgb_RMSE':float(np.sqrt((err**2).mean())),
      'source_opaque_subject_rgb_MAE':float(np.abs(err[source_subject]).mean()),'source_opaque_subject_rgb_RMSE':float(np.sqrt((err[source_subject]**2).mean())),
      'source_opaque_subject_missing_alpha_mass':float((1-a[:,:,3][source_subject].astype(float)/255).sum()),
      'source_opaque_subject_pixels_not_fully_covered':int((a[:,:,3][source_subject]<255).sum()),
      'outside_source_frame_alpha_mass':float((a[:,:,3][ra==0].astype(float)/255).sum()),
      'crop_binary_xor_pixels':int((fm^rm).sum()),'crop_binary_iou':float((fm&rm).sum()/(fm|rm).sum()),
      'crop_alpha_MAE':float(np.abs(f.astype(float)-ra.astype(float)).mean()),'crop_boundary_mean_distance_px':float(distance.mean()),'crop_boundary_max_distance_px':float(distance.max()),
      'rgb_absolute_error_sum_prior_frame_difference_band':float(np.abs(err[alpha_band]).sum()/3)}
report={'revision':'r003','scope':'canvas-crop path d only','non_crop_svg_bytes_identical':True,'source_sha256':hashlib.sha256(refpath.read_bytes()).hexdigest(),'base_sha256':hashlib.sha256(before.encode()).hexdigest(),'svg_sha256':hashlib.sha256(after.encode()).hexdigest(),'circle_radius_px':r,'half_alpha_samples':len(samples),'half_alpha_fit_mean_horizontal_residual_px':float(np.abs(predict(r,s[:,2])-s[:,1]).mean()),'half_alpha_fit_max_horizontal_residual_px':float(np.abs(predict(r,s[:,2])-s[:,1]).max()),'corner_curve_count':4,'before':metrics(old,old_frame),'after':metrics(new,new_frame),'caveat':'Source alpha measures the frame only; source-background removal and all internal material/object mismatches remain unchanged. These diagnostics do not replace frozen v5.'}
(dest/'measurements.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(dest/'source-alpha-boundary-samples.json').write_text(json.dumps(samples),encoding='utf-8')
Image.fromarray(new_frame).save(dest/'fitted-frame-alpha.png')
pair=Image.new('RGB',(1280,640),(15,15,15))
for i,a in enumerate([raw,new]):
    im=Image.fromarray(a).resize((640,640),Image.Resampling.LANCZOS);pair.paste(im,(i*640,0),im)
pair.save(dest/'reference-comparison.png')
changes=np.max(np.abs(new.astype(float)-old.astype(float)),axis=2)>0
visual=np.zeros((1280,1280,3),dtype=np.uint8);visual[changes]=[255,90,60]
Image.fromarray(visual).save(dest/'changed-pixel-map.png')
board=Image.new('RGB',(960,410));dr=ImageDraw.Draw(board)
for i,bg in enumerate(['#f6f4ee','#0f0f0f','#bcbcc5']):
    dr.rectangle((i*320,0,i*320+319,409),fill=bg)
    for y,size in [(32,128),(220,48),(320,24)]:
        im=Image.open(dest/f'preview-{size}.png').convert('RGBA');board.paste(im,(i*320+36,y),im)
        dr.text((i*320+181,y+4),f'{size} px',fill='#888888')
board.save(dest/'inspection-board.png')
for name in ['short.svg','preview-1280.png','preview-128.png','preview-48.png','preview-24.png','reference-comparison.png','inspection-board.png']:shutil.copy2(dest/name,ROOT/name)
print(json.dumps(report));timer.cancel()
