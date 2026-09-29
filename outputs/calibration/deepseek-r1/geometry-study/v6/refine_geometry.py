"""Bounded, source-assisted correction of five named material boundaries.

This is not a general character generator. It retains v5 face, eye, silhouette,
accessory outlines and all opaque material foundations byte-for-byte.
"""
import copy
import hashlib
import importlib.util
import io
import json
import shutil
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import resvg_py

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
OLD=HERE.parent/'v5'
SOURCE=ROOT/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png'
sys.path.insert(0,str(ROOT))
from tools.vectorize_calibration import Deadline, mask_path

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def pathmask(d):
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1280"><path d="{d}" fill="white"/></svg>'
    return np.asarray(Image.open(io.BytesIO(resvg_py.svg_to_bytes(svg_string=svg))))[:,:,3]>127

def curve_from_samples(samples):
    """One cubic Bezier x(y), constrained by observed structural edge positions."""
    p=np.asarray(samples,float); y0,y1=p[0,1],p[-1,1]
    t=(p[:,1]-y0)/(y1-y0)
    c=np.polynomial.polynomial.polyfit(t,p[:,0],3)
    x=[c[0],c[0]+c[1]/3,c[0]+2*c[1]/3+c[2]/3,sum(c)]
    y=[y0,y0+(y1-y0)/3,y0+2*(y1-y0)/3,y1]
    return list(zip(x,y)),float(np.max(abs(np.polynomial.polynomial.polyval(t,c)-p[:,0])))

def ribbon(left_samples,right_samples):
    a,ae=curve_from_samples(left_samples);b,be=curve_from_samples(right_samples)
    pt=lambda p:f'{p[0]:.4f},{p[1]:.4f}'
    return f'M {pt(a[0])} C {pt(a[1])} {pt(a[2])} {pt(a[3])} L {pt(b[3])} C {pt(b[2])} {pt(b[1])} {pt(b[0])} Z',{'left_max_sample_error_px':ae,'right_max_sample_error_px':be,'left_samples':left_samples,'right_samples':right_samples}

def main():
    deadline=Deadline(43)
    doc=json.loads((OLD/'geometry.json').read_text(encoding='utf-8'))
    assert sha(SOURCE)==doc['reference_sha256']
    (HERE/'masks').mkdir(exist_ok=True)
    for p in (OLD/'masks').glob('*.png'): shutil.copyfile(p,HERE/'masks'/p.name)
    shutil.copyfile(OLD/'subject-mask.png',HERE/'subject-mask.png')
    regions={r['id']:r for r in doc['regions']}
    oldm={k:np.asarray(Image.open(OLD/r['mask_path']))>127 for k,r in regions.items()}
    masks={k:v.copy() for k,v in oldm.items()}
    blue=np.asarray(Image.open(OLD/'masks/blue-underpaint.png'))>127
    yy,xx=np.indices(blue.shape)
    hairunion=np.logical_or.reduce([m for k,m in masks.items() if k.startswith('hair')])
    # Source-observed centers of the broad top boundary: (579,300),
    # (633,350), (668,400), (696,450), (719,500), (738,550).
    # Below y600 this colour boundary becomes soft. The path is geometry for
    # fitting continuous fields, not permission to add a hard painted contour.
    maincurve='M -10,200 L 500,277 C 563,277 630,327 668,400 C 713,478 756,587 775,672 C 776,714 791,787 777,846 C 776,855 774,865 771,876 L 806,918 L -10,918 Z'
    movable=masks['hair-front-main']|masks['hair-right-fringe']
    roi=(yy>=277)&(yy<918)
    newmain=pathmask(maincurve)&movable&roi
    masks['hair-front-main'][roi]=newmain[roi]
    masks['hair-right-fringe'][roi]=(movable&~newmain)[roi]
    # Restore the original broad ownership at top-left; only the center-right
    # interface is under study, not the unrelated crown/left shadow interface.
    preserve=(xx<470)&(yy<300)
    for k in ['hair-front-main','hair-right-fringe']: masks[k][preserve]=oldm[k][preserve]
    # A tapered dark fold follows an occlusion seam and reaches the face edge.
    # Its silhouette comes from the source, never from ellipse/glint primitives.
    right_crease,right_crease_fit=ribbon([(775,672),(776,700),(781,750),(781,800),(776,850),(771,876)],[(775,672),(778,700),(788,750),(796,800),(802,850),(805,900),(806,918)])
    under_left=[(870,802),(869,825),(866,850),(861,875),(854,900),(847,925),(837,950),(825,975),(822,980)]
    under_right=[(870,802),(870,825),(870,850),(869,875),(867,900),(864,925),(860,950),(855,975),(848,1000),(840,1025),(831,1050),(820,1075),(808,1097)]
    a,ae=curve_from_samples(under_left);b,be=curve_from_samples(under_right)
    a[0]=b[0]=(870,802);a[-1]=(822,980);b[-1]=(808,1097)
    pt=lambda p:f'{p[0]:.4f},{p[1]:.4f}'
    underfold=f'M {pt(a[0])} C {pt(a[1])} {pt(a[2])} {pt(a[3])} C 824,1022 820,1065 808,1097 C {pt(b[2])} {pt(b[1])} {pt(b[0])} Z'
    underfold_fit={'left_max_sample_error_px':ae,'right_max_sample_error_px':be,'left_samples':under_left,'right_samples':under_right,'face_occlusion':'below 980 the left contour follows the visible face occlusion; no latent edge crosses the skin gap'}
    curves={
      'hair-center-right-crease':'M 667,511 C 668,547 664,580 658,599 L 704,735 C 686,675 672,580 667,511 Z',
      'hair-right-face-crease':right_crease,
      'hair-right-underfold':underfold,
    }
    # Old named folds return to their correct neighbouring broad fields before
    # the replacement; no hole is created by erasing the old geometry.
    mainownership=pathmask(maincurve)
    for k in curves:
        masks['hair-front-main']|=masks[k]&mainownership
        masks['hair-right-fringe']|=masks[k]&~mainownership
        masks[k][:]=False
    for k,d in curves.items():
        m=pathmask(d)&hairunion
        for other in masks:
            if other.startswith('hair'): masks[other]&=~m
        masks[k]=m
    # The narrow lower fin surface has two continuous folded faces. Move only
    # their shared interface; the pale rim's exterior is unchanged.
    rim=masks['whale-side-fin-rim']|masks['whale-fin-rim-left-fold']
    fincurve='M 950,950 L 1280,1050 L 1137,1096 C 1108,1088 1074,1076 1050,1055 L 1042,1096 L 950,1150 Z'
    masks['whale-fin-rim-left-fold']=pathmask(fincurve)&rim
    masks['whale-side-fin-rim']=rim&~masks['whale-fin-rim-left-fold']
    changed=[]
    for k,m in masks.items():
        deadline.check()
        if np.array_equal(m,oldm[k]): continue
        r=regions[k]
        if k in ['hair-right-face-crease','hair-right-underfold']:
            # Preserve finite, subpixel tapered tips. Passing this geometry back
            # through a binary-mask simplifier truncated the visible taper.
            r['d']=curves[k]
            r['curve_statistics']={'source':'direct finite cubic structural boundary','curve_vertices':7 if k=='hair-right-underfold' else 6,'raster_fit_mask':'same path thresholded at 0.5 and intersected with original hair support for colour sampling only'}
        else:
            r['d'],r['curve_statistics']=mask_path(m,tolerance=.8,smooth=1.0,deadline=deadline)
        r['pixels']=int(m.sum())
        ys,xs=np.where(m);r['bbox']=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
        r['source_method']='source-reviewed finite semantic Bezier boundaries; original source support retained'
        r['uncertainty']='source-assisted geometry; soft main/right hair transition requires continuous paint fields'
        Image.fromarray(m.astype('uint8')*255).save(HERE/r['mask_path'])
        changed.append({'id':k,'old_pixels':int(oldm[k].sum()),'new_pixels':int(m.sum()),'changed_mask_pixels':int((m^oldm[k]).sum()),'old_mask_sha256':sha(OLD/r['mask_path']),'new_mask_sha256':sha(HERE/r['mask_path'])})
    doc['refinement']={'parent_geometry_sha256':sha(OLD/'geometry.json'),'scope':'five source-observed semantic boundary corrections; face eyes silhouette underpaints unchanged','manual_boundaries':{'main_ownership':maincurve,**curves,'fin_internal_fold':fincurve},'structural_boundary_fits':{'hair-right-face-crease':right_crease_fit,'hair-right-underfold':underfold_fit},'changed_regions':changed}
    doc['limitations'].append('Main/right field interface fades below y600; renderer must not draw a stroke or add a narrow highlight there.')
    (HERE/'geometry.json').write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
    # Exact path overlays, not just fitted masks, for source review.
    paths=[]
    for k in [q['id'] for q in changed]:
        paths.append(f'<path d="{regions[k]["d"]}" fill="none" stroke="#ff3355" stroke-width=".8"/>')
    xml='<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1280">'+''.join(paths)+'</svg>'
    overlay=Image.open(SOURCE).convert('RGBA')
    overlay=Image.alpha_composite(overlay,Image.open(io.BytesIO(resvg_py.svg_to_bytes(svg_string=xml))).convert('RGBA'))
    overlay.save(HERE/'source-path-overlay.png')
    (HERE/'source-path-overlay.svg').write_text(xml,encoding='utf-8')
    # Geometry-only A/B uses the exact old fields for all regions; it is not a
    # new paint result and cannot be used as the final calibration claim.
    candidate=(ROOT/'outputs/calibration/deepseek-r1/revisions/v004/short.svg').read_text(encoding='utf-8')
    import xml.etree.ElementTree as ET
    svgroot=ET.fromstring(candidate)
    for elem in svgroot.iter():
        ident=elem.attrib.get('id')
        if ident in [q['id'] for q in changed]: elem.set('d',regions[ident]['d'])
    xml=ET.tostring(svgroot,encoding='unicode')
    (HERE/'geometry-only-old-paint.svg').write_text(xml,encoding='utf-8')
    raw=resvg_py.svg_to_bytes(svg_string=xml)
    (HERE/'geometry-only-old-paint.png').write_bytes(raw)
    im=Image.open(io.BytesIO(raw)).convert('RGBA')
    before=Image.open(ROOT/'outputs/calibration/deepseek-r1/revisions/v004/comparison/candidate-render.png').convert('RGBA')
    source=Image.open(SOURCE).convert('RGBA')
    boxes={'right-crease':(730,660,895,1115),'center-crease':(620,470,725,770),'fin-rim':(960,960,1270,1160),'main-boundary':(450,230,870,760)}
    metrics={}
    for name,box in boxes.items():
        w,h=box[2]-box[0],box[3]-box[1]
        board=Image.new('RGB',(w*3,h+25),'#151515');draw=ImageDraw.Draw(board)
        for i,(title,pic) in enumerate([('Source',source),('v004 old geometry',before),('v6 geometry old paint',im)]):
            crop=pic.crop(box);board.paste(crop,(i*w,25),crop);draw.text((i*w+3,5),title,fill='white')
        board.save(HERE/f'{name}-geometry-ab.png')
        sa=np.asarray(source.crop(box)).astype(float);ba=np.asarray(before.crop(box)).astype(float);na=np.asarray(im.crop(box)).astype(float)
        metrics[name]={'bbox':box,'old_rgb_mae':float(abs(sa[:,:,:3]-ba[:,:,:3]).mean()),'geometry_only_rgb_mae':float(abs(sa[:,:,:3]-na[:,:,:3]).mean()),'interpretation':'paint unchanged; diagnostic metric, not acceptance'}
    evid={'source_sha256':sha(SOURCE),'parent_geometry_sha256':sha(OLD/'geometry.json'),'geometry_sha256':sha(HERE/'geometry.json'),'script_sha256':sha(Path(__file__)),'regions':len(doc['regions']),'changed_regions':changed,'preserved_regions':[k for k in regions if k not in {q['id'] for q in changed}],'underpaint_byte_identity':all(sha(OLD/p['mask_path'])==sha(HERE/p['mask_path']) for p in doc['underpaints']),'geometry_only_roi_metrics':metrics}
    (HERE/'refinement-evidence.json').write_text(json.dumps(evid,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'geometry_sha256':evid['geometry_sha256'],'changed':changed,'roi_metrics':metrics}))

if __name__=='__main__':main()
