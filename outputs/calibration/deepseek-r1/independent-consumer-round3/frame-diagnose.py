"""Bounded raw-alpha frame diagnosis; no artwork mutation."""
from pathlib import Path
import os,sys,threading,json
t=threading.Timer(45,lambda:os._exit(124));t.daemon=True;t.start()
import numpy as np
from PIL import Image,ImageDraw
from io import BytesIO
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[3]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text
NS='http://www.w3.org/2000/svg'
raw=np.asarray(Image.open(REPO/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png').convert('RGBA'))
old=np.asarray(Image.open(ROOT/'r002/preview-1280.png').convert('RGBA'))
tree=ET.parse(ROOT/'r002/short.svg').getroot()
frame=next(e for e in tree.iter() if e.get('id')=='canvas-crop')
d=list(frame)[0].get('d')
svg=f'<svg xmlns="{NS}" viewBox="0 0 1280 1280"><path d="{d}" fill="white"/></svg>'
frame_rgba=np.asarray(Image.open(BytesIO(render_svg_text(svg,1280))).convert('RGBA'))
a=frame_rgba[:,:,3];b=raw[:,:,3]
ma=a>=128;mb=b>=128;xor=ma^mb
full=(a==255)&(b==255)
alpha_err=np.abs(a.astype(float)-b.astype(float))
bg=15.;rs=raw[:,:,:3].astype(float)*b[:,:,None]/255+bg*(1-b[:,:,None]/255)
ro=old[:,:,:3].astype(float)*old[:,:,3:4]/255+bg*(1-old[:,:,3:4]/255)
rgb_err=np.abs(rs-ro).mean(2)
active=((old[:,:,3]>0)|((raw[:,:,:3].max(2)>30)&(b>0)))
frame_affected=alpha_err>1
def bound(m):return m&~ndi.binary_erosion(m)
y1,x1=np.nonzero(bound(ma));y2,x2=np.nonzero(bound(mb))
dist=cKDTree(np.column_stack((x2,y2))).query(np.column_stack((x1,y1)))[0]
regions={'upper-left':(0,640,0,640),'upper-right':(0,640,640,1280),'lower-left':(640,1280,0,640),'lower-right':(640,1280,640,1280)}
report={'existing_crop_path':d,'source_alpha_values':len(np.unique(b)),'source_alpha_opaque':int((b==255).sum()),'source_alpha_transparent':int((b==0).sum()),'crop_binary_xor_pixels':int(xor.sum()),'crop_binary_iou':float((ma&mb).sum()/(ma|mb).sum()),'crop_alpha_mae':float(alpha_err.mean()),'crop_boundary_mean_distance_px':float(dist.mean()),'crop_boundary_max_distance_px':float(dist.max()),'rgb_absolute_error_sum_all':float(rgb_err.sum()),'rgb_absolute_error_sum_frame_affected':float(rgb_err[frame_affected].sum()),'active_pixels_frame_affected':int((active&frame_affected).sum()),'regions':{}}
for name,(y0,y3,x0,x3) in regions.items():
    sl=np.s_[y0:y3,x0:x3];f=frame_affected[sl]
    report['regions'][name]={'binary_xor':int(xor[sl].sum()),'active_frame_affected_pixels':int((active[sl]&f).sum()),'rgb_error_sum':float(rgb_err[sl].sum()),'rgb_error_sum_frame_affected':float(rgb_err[sl][f].sum())}
report['source_boundary_rows']={str(y):[int(np.where(mb[y])[0].min()),int(np.where(mb[y])[0].max())] if mb[y].any() else None for y in [0,1,5,10,20,40,80,120,160,200,240,280,300,320,960,1000,1040,1080,1120,1160,1200,1240,1260,1270,1275,1279]}
(ROOT/'frame-diagnosis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
diff=np.zeros((1280,1280,3),dtype=np.uint8);diff[ma&~mb]=[255,80,50];diff[mb&~ma]=[50,190,255];diff[bound(mb)]=[255,255,255]
Image.fromarray(diff).save(ROOT/'frame-alpha-difference.png')
print(json.dumps(report));t.cancel()
