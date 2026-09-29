"""Private single-reference geometry study; not a generic character generator.

Requires numpy/scipy/Pillow/resvg already present in repo CI environment.
No color quantization, raster embedding, network or material texture fitting.
"""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import time

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import resvg_py

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
OUT = BASE / 'v2'
SOURCE = ROOT / 'ref/user-mode/r1.png'
sys.path.insert(0, str(ROOT))
from tools.vectorize_calibration import Deadline, mask_path

NS = 'http://www.w3.org/2000/svg'


def largest(mask):
    lab, n = ndi.label(mask)
    areas = np.bincount(lab.ravel()); areas[0] = 0
    return lab == areas.argmax()


def retain(mask, minimum=100):
    lab, n = ndi.label(mask)
    a = np.bincount(lab.ravel()); keep = a >= minimum; keep[0] = False
    return keep[lab]


def poly(points):
    im = Image.new('L',(1280,1280)); ImageDraw.Draw(im).polygon(points,fill=255)
    return np.array(im)>0


def pathmask(d):
    svg=f'<svg xmlns="{NS}" width="1280" height="1280"><path d="{d}" fill="white"/></svg>'
    png=resvg_py.svg_to_bytes(svg_string=svg)
    return np.array(Image.open(io.BytesIO(png)))[:,:,3]>127


def main():
    started=time.monotonic(); deadline=Deadline(43)
    (OUT/'masks').mkdir(parents=True,exist_ok=True)
    a=np.array(Image.open(SOURCE).convert('RGBA')); rgb=a[:,:,:3].astype(float)
    r,g,b=rgb.transpose(2,0,1); yy,xx=np.indices(r.shape)
    # Fixed exclusion based on visually inspected watermark, not error selection.
    uncertain=(xx>=1084)&(xx<=1251)&(yy>=1193)&(yy<=1254)
    Image.fromarray(uncertain.astype('uint8')*255).save(OUT/'watermark-uncertainty.png')
    art=(b>32)&(a[:,:,3]>127)
    art=retain(art&~uncertain, 200)
    # Continue only the obscured back-hair silhouette by local row interpolation.
    known=art.copy()
    for y in range(1193,1255):
        # The right silhouette is an app-icon rounded crop, not hair noise.
        # Fixed interpolation between visible endpoints, explicitly uncertain.
        edge=int(np.interp(y,[1192,1220,1238,1255],[1128,1134,1140,1101]))
        art[y,1084:max(1084,edge+1)]=True
    # Reference segmentation is visible geometry, not inferred hidden shape.
    # Warm-colour contrast incorrectly excludes the nearly white face rim.
    # Use the connected bright face surface, separate from disconnected frill.
    face=largest((r>190)&(g>150)&(b>125)&(yy>420)&(xx<865)&art)
    face=ndi.binary_fill_holes(face)
    eyes=retain((r<90)&(g<90)&(b<110)&(yy>610)&(xx<820)&ndi.binary_dilation(face,iterations=2),1000)
    eye_l=eyes&(xx<420); eye_r=eyes&(xx>=420)
    cheeks=retain((r-g>25)&(g-b<10)&(r>230)&(yy>810)&face,500)
    cheek_l=cheeks&(xx<400); cheek_r=cheeks&(xx>400)
    warmshadow=retain(face&(r-g>25)&(yy<810),100)
    frill=(r>155)&(g>155)&(b>165)&(r-b<4)&(yy<760)&art
    frill=retain(frill,250)
    fold=frill&(g<231)
    white=frill&~fold
    rim=retain((r>125)&(g>125)&(b>150)&(yy>960)&(xx>960)&art&~uncertain,100)
    blue=art&~face&~frill&~rim
    # Hand-authored anatomical boundaries follow visible major contours.
    # Paths intentionally describe broad continuous surfaces, not color bins.
    shapes={
      'whale-side-fin':'M 987,610 C 1033,660 1067,720 1094,785 C 1110,863 1150,985 1255,1101 L 1244,1126 C 1154,1134 1010,1088 987,1001 C 1000,900 987,774 974,709 Z',
      'bow-left':'M 971,742 C 1008,699 1053,768 1054,814 C 1051,856 1029,876 989,885 Z',
      'bow-right':'M 1049,818 C 1082,775 1126,774 1136,789 C 1153,817 1133,892 1109,919 C 1086,944 1055,884 1046,860 Z',
      'bow-knot':'M 1044,817 C 1054,806 1067,815 1065,836 C 1063,855 1057,864 1047,859 C 1038,850 1039,833 1044,817 Z',
      'ahoge':'M 207,88 C 286,-22 472,2 553,81 C 616,145 602,227 523,275 L 480,287 C 524,190 429,84 335,65 C 287,54 249,67 207,88 Z',
      'hair-left-under':'M 0,290 C 122,242 212,223 280,225 C 180,245 75,312 0,390 Z',
      'hair-left-fringe':'M 0,390 C 181,159 377,247 482,277 C 420,314 377,356 352,405 C 325,490 193,630 28,680 C 5,750 12,817 35,846 C 5,839 -10,825 -10,813 Z',
      'hair-left-fringe-fold':'M 173,459 C 146,504 105,587 90,658 L 26,680 C 46,597 103,525 173,459 Z',
      'hair-left-inner-fold':'M 352,405 C 343,432 338,455 331,476 L 237,566 C 292,518 327,459 352,405 Z',
      'hair-center-fringe':'M 352,405 C 386,342 430,297 481,278 C 599,251 699,420 667,511 C 669,632 639,738 552,810 L 561,854 C 462,834 385,733 381,597 C 380,650 377,711 388,761 C 298,718 312,533 331,476 Z',
      'hair-center-fold':'M 560,724 C 549,763 548,786 552,810 L 558,800 C 554,779 558,750 560,724 Z',
      'hair-right-fringe':'M 484,277 C 670,272 884,442 944,624 L 972,742 C 1001,904 1005,1038 941,1141 C 903,1202 833,1249 840,1256 C 882,1257 913,1226 927,1108 C 903,1149 823,1184 738,1169 C 781,1144 804,1116 809,1091 L 798,1020 C 824,942 796,868 774,740 C 779,825 785,875 806,917 C 744,848 694,713 657,595 C 673,546 670,489 666,451 C 630,350 549,289 484,277 Z',
      'hair-right-underfold':'M 775,740 C 781,848 793,913 798,1020 C 851,953 872,884 870,805 C 878,891 865,1053 810,1093 L 806,916 Z',
      'hair-back':'M 961,961 C 982,1025 1039,1108 1113,1136 C 1136,1204 1137,1224 1166,1236 L 1078,1280 L 738,1280 C 778,1235 795,1207 809,1175 C 880,1181 930,1140 961,1066 Z',
      'hair-back-light':'M 927,1108 C 915,1180 875,1232 840,1256 C 883,1259 934,1222 958,1177 C 984,1123 977,1058 977,1010 C 971,1079 952,1120 927,1157 Z',
      'hair-back-dark-fold':'M 975,1158 C 982,1218 985,1241 988,1265 C 1001,1248 1011,1227 1018,1204 C 1031,1237 1042,1261 1063,1280 L 1127,1280 C 1073,1228 1046,1178 1030,1117 L 994,1091 Z',
    }
    # Visible face shading below fringe; keep separate from general skin field.
    masks={
       'face':face&~eyes&~cheeks&~warmshadow,
       'face-under-fringe-shadow':warmshadow,
       'eye-left':eye_l,'eye-right':eye_r,
       'cheek-left':cheek_l,'cheek-right':cheek_r,
       'frill-white':white,'frill-fold':fold,'whale-side-fin-rim':rim,
    }
    remaining=blue.copy()
    # Small, strongly bounded accessories take ownership before broad hair.
    order=['bow-knot','bow-left','bow-right','whale-side-fin','ahoge','hair-left-fringe-fold','hair-left-inner-fold','hair-center-fold','hair-right-underfold','hair-back-light','hair-back-dark-fold','hair-back','hair-left-under','hair-center-fringe','hair-left-fringe','hair-right-fringe']
    for name in order:
        if name=='whale-side-fin':
            gate=pathmask('M 985,570 L 1110,800 L 1275,1120 L 1252,1160 C 1105,1130 1003,1060 975,1000 Z')
            m=(b<150)&gate&remaining
        elif name=='hair-right-underfold':
            gate=pathmask('M 775,740 C 777,812 784,865 806,917 L 793,884 C 783,843 777,784 775,740 Z M 870,805 C 878,930 856,1038 810,1092 L 798,1020 C 842,958 869,873 870,805 Z')
            m=gate&remaining
        elif name=='hair-back-light':
            gate=pathmask('M 987,1000 C 981,1145 922,1265 837,1257 C 882,1227 917,1173 927,1108 C 958,1065 984,1022 987,1000 Z')
            m=gate&(g>120)&remaining
        elif name in ['bow-left','bow-right']:
            # Both wing faces have G >= 129. A geometric-only prior included
            # adjacent dark hair at the upper left, polluting material fitting.
            if name=='bow-left':
                structure=((yy>845)&(xx>987))|((xx>1024)&(xx<1047)&(yy>815)&(yy<840))
            else:
                structure=((yy>830)&(xx>1050))|((xx>1063)&(xx<1085)&(yy>829)&(yy<851))
            m=pathmask(shapes[name])&((g>=129)|structure)&remaining
        else:
            m=pathmask(shapes[name])&remaining
        m=retain(m,20)
        masks[name]=m; remaining&=~m
    # Manual curves are approximations; remaining blue pixels use nearest
    # semantic mask (bounded; no new color components or tracing texture).
    names=[name for name in order if name.startswith('hair') or name=='ahoge']
    labels=np.zeros((1280,1280),dtype=np.int16)
    for i,name in enumerate(names,1):labels[masks[name]]=i
    missing=remaining
    if missing.any():
        indices=ndi.distance_transform_edt(labels==0,return_distances=False,return_indices=True)
        nearest=labels[indices[0],indices[1]]
        for i,name in enumerate(names,1):masks[name]|=missing&(nearest==i)
    # The left and middle forelock share a continuous bright field, no real
    # surface seam at the arbitrary manual split. Preserve only real folds.
    masks['hair-front-main']=masks.pop('hair-left-fringe')|masks.pop('hair-center-fringe')
    masks['hair-right-fringe']|=masks.pop('hair-back-light')
    # Individual structural folds on the blue bow are separate finite shapes.
    bow=masks['bow-left']|masks['bow-right']|masks['bow-knot']
    bowdark=bow&(g<133)&(b>140)
    creases=bowdark&(((xx>1024)&(xx<1047)&(yy>815)&(yy<840))|((xx>1063)&(xx<1085)&(yy>829)&(yy<851)))
    rimblue=retain(bowdark&~creases,100)
    masks['bow-crease-left']=retain(creases&(xx<1050),15)
    masks['bow-crease-right']=retain(creases&(xx>=1050),15)
    masks['bow-lower-rim']=rimblue
    for name in ['bow-left','bow-right','bow-knot']:
        masks[name]&=~(creases|rimblue)
    # Real separately folded white petals need separate analytic paint fields.
    for family in ['frill-white','frill-fold']:
        lab,n=ndi.label(masks.pop(family)); areas=np.bincount(lab.ravel())
        for index,c in enumerate([c for c in range(1,n+1) if areas[c]>=100],1):
            masks[f'{family}-{index:02d}']=lab==c
    underpaint_masks={'subject-underpaint':art,'face-underpaint':face,
      'frill-underpaint':frill,'blue-underpaint':blue,'bow-underpaint':bow}
    # Semantic preview uses arbitrary distinguishing colours only, not paint.
    palette=['#efdabb','#deaa97','#17274d','#17274d','#e5a5b8','#e5a5b8','#faf6ee','#aba9cc','#c9d0dd','#af8ed0','#929ae1','#5770a7','#256274','#60a0d0','#4783ae','#6e78b7','#747dd7','#5963a8','#4683b5','#3c557d','#615991','#427fa7','#434984','#6675c1']
    regions=[]; svg=[]; edges=np.zeros_like(a); edges[:,:,3]=0
    covered=np.zeros_like(art)
    for i,(name,m) in enumerate(masks.items()):
        deadline.check()
        m=retain(m,15)
        if not m.any():
            print('OMITTED_EMPTY_REGION',name)
            continue
        # Smooth only one sampling-pixel width. Preserves tips and material edges.
        m=ndi.gaussian_filter(m.astype(float),.60)>=.5
        Image.fromarray(m.astype('uint8')*255).save(OUT/'masks'/f'{name}.png')
        d,stats=mask_path(m,tolerance=1.05,smooth=2.0,deadline=deadline)
        ys,xs=np.where(m)
        box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
        color=palette[i%len(palette)]
        svg.append(f'<path id="{name}" d="{d}" fill="{color}" fill-rule="evenodd"/>')
        role='hair' if name.startswith('hair') or name=='ahoge' else ('eye' if name.startswith('eye') else name.split('-')[0])
        method='manual semantic cubic boundary intersected with original material support' if name in shapes else 'semantic ROI plus material contrast and connected components'
        regions.append({'id':name,'semantic_role':role,'material':role,'z':i,'mask_path':f'masks/{name}.png','d':d,'fill_rule':'evenodd','bbox':box,'pixels':int(m.sum()),'source_method':method,'uncertainty':'watermark area interpolated' if np.any(m&uncertain) else 'boundary localization approximately 1 pixel; internal hair segmentation is hand constrained','occlusion':'visible-surface region only; hidden surfaces not reconstructed','curve_statistics':stats})
        boundary=m^ndi.binary_erosion(m)
        edges[boundary]=[255,30,80,255]; covered|=m
    underpaints=[]
    for name,m in underpaint_masks.items():
        before=m.copy()
        # These are backing supports, not visible fitted paint samples. Remove
        # isolated AA specks and fill only enclosed holes <=25 sampling pixels;
        # larger intentional gaps (face/eye/fin/headwear) remain exact.
        m=retain(m,26)
        lab,n=ndi.label(~m); areas=np.bincount(lab.ravel())
        border=set(np.unique(np.r_[lab[0,:],lab[-1,:],lab[:,0],lab[:,-1]]))
        tiny=[c for c in range(1,n+1) if areas[c]<=25 and c not in border]
        if tiny:m|=np.isin(lab,tiny)
        Image.fromarray(m.astype('uint8')*255).save(OUT/'masks'/f'{name}.png')
        d,stats=mask_path(m,tolerance=.85,smooth=1.2,deadline=deadline)
        underpaints.append({'id':name,'mask_path':f'masks/{name}.png','d':d,'fill_rule':'evenodd','usage':'opaque parent foundation beneath visible region paint; sample colour from corresponding face/hair/frill surface; not a separate material','curve_statistics':stats,'support_cleanup':{'max_enclosed_hole_area':25,'minimum_component_area':26,'removed_pixels':int((before&~m).sum()),'filled_pixels':int((m&~before).sum()),'visible_fit_masks_changed':False}})
    doc={'schema':'aikon.semantic-geometry.v1','canvas':{'width':1280,'height':1280},'reference':'ref/user-mode/r1.png','reference_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'watermark_uncertainty_mask':'watermark-uncertainty.png','black_background':'excluded by material support; alpha alone is not subject mask','regions':regions,'underpaints':underpaints,'validation':{'claimed_similarity':None,'uncertain_pixels':int(uncertain.sum()),'material_support_pixels':int(art.sum()),'covered_pixels':int(covered.sum()),'uncovered_material_pixels':int((art&~covered).sum()),'duration_seconds':time.monotonic()-started},'limitations':['No unique 3D pitch inferred. Original face/eye/hairline/chin projection retained.','Internal blue material boundaries are manually constrained and require source overlay review.','Region contours are visible masks and cannot certify anatomy behind occlusions.','Watermark-covered background/subject border is an explicitly uncertain interpolation.']}
    (OUT/'geometry.json').write_text(json.dumps(doc,indent=2),encoding='utf-8')
    xml=f'<svg xmlns="{NS}" width="1280" height="1280" viewBox="0 0 1280 1280"><title>Semantic geometry diagnostic, false colours</title>'+''.join(svg)+'</svg>'
    (OUT/'geometry-diagnostic.svg').write_text(xml,encoding='utf-8')
    (OUT/'geometry-diagnostic.png').write_bytes(resvg_py.svg_to_bytes(svg_string=xml))
    overlay=Image.alpha_composite(Image.fromarray(a),Image.fromarray(edges))
    overlay.save(OUT/'reference-boundary-overlay.png')
    Image.fromarray(art.astype('uint8')*255).save(OUT/'subject-mask.png')
    print(json.dumps({'regions':len(regions),'vertices':sum(q['curve_statistics']['curve_vertices'] for q in regions),'validation':doc['validation']}))


if __name__=='__main__':main()
