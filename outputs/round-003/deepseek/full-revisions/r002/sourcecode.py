"""Full r002: evidence-based neck clearance and lower hair flow repair."""
from pathlib import Path
import os,threading,sys,json,hashlib,copy,shutil
t=threading.Timer(45,lambda:os._exit(124));t.daemon=True;t.start()
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text,validate_svg
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
def tag(n):return '{'+NS+'}'+n
base=(ROOT/'full-revisions/r001/full.svg').read_text(encoding='utf-8');tree=ET.fromstring(base)
ids={e.get('id'):e for e in tree.iter() if e.get('id')}
ids['full-composition'].set('transform','translate(0 0) scale(0.74)')
ids['full-selected-maid-attire'].set('transform','translate(0 60) rotate(18 430 1490)')
ids['full-back-hair-parent'].set('d','M 735 1100 C 952 1092 1077 1197 1168 1340 C 1228 1511 1177 1653 1197 1750 C 1083 1660 1022 1575 1000 1487 C 1024 1595 893 1710 742 1730 C 805 1577 828 1379 733 1280 Z')
ids['full-back-hair-flow'].set('d','M 882 1215 C 968 1347 935 1506 797 1652 C 928 1607 981 1550 977 1445 C 995 1540 1059 1616 1123 1627 C 1091 1554 1083 1425 1059 1336 C 993 1278 937 1240 882 1215 Z')
ids['full-back-hair-fold'].set('d','M 882 1230 C 927 1359 913 1487 861 1552 C 882 1431 868 1347 799 1283 Z')

# Retain the observed fin/source support and let same-field lower support
# continue behind it; remove r001's diagonal invented termination.
src=ET.parse(REPO/'outputs/calibration/deepseek-r1/independent-consumer-round3/r004/short.svg').getroot()
original={e.get('id'):e for e in src.iter() if e.get('id')}
ids['rear-hair'].set('d',original['rear-hair'].get('d'))
stage=ids['full-composition']
flow=ET.Element(tag('path'),{'id':'full-front-underlock-continuation','d':'M 735 1240 C 890 1244 887 1479 801 1585 C 735 1654 656 1653 602 1675 C 731 1512 749 1365 735 1240 Z','fill':'url(#measured-hair-crown-parent)'})
stage.insert(list(stage).index(ids['full-r1-head']),flow)

svg=ET.tostring(tree,encoding='unicode');validate_svg(svg)
dest=ROOT/'full-revisions/r002';dest.mkdir(parents=True,exist_ok=True)
(dest/'full.svg').write_text(svg,encoding='utf-8')
for size in [1280,128,48,24]:(dest/f'full-{size}.png').write_bytes(render_svg_text(svg,size))
shutil.copy2(ROOT/'full-revise.py',dest/'sourcecode.py');shutil.copy2(ROOT/'full-r002.prompt.zh-CN.md',dest/'actualprompt.md')
for name in ['full.svg','full-1280.png','full-128.png','full-48.png','full-24.png']:shutil.copy2(dest/name,ROOT/name)
board=Image.new('RGB',(960,410));dr=ImageDraw.Draw(board)
for i,bg in enumerate(['#f6f4ee','#0f0f0f','#bcbcc5']):
    dr.rectangle((i*320,0,i*320+319,409),fill=bg)
    for yy,s in [(32,128),(220,48),(320,24)]:
        im=Image.open(dest/f'full-{s}.png').convert('RGBA');board.paste(im,(i*320+36,yy),im);dr.text((i*320+180,yy+4),f'{s}px',fill='#888888')
board.save(dest/'inspection-board.png');board.save(ROOT/'full-inspection-board.png')
overview=Image.new('RGB',(1536,820),'#edeef3');dr=ImageDraw.Draw(overview)
for i,profile in enumerate(['short','full']):
    im=Image.open(ROOT/f'{profile}-1280.png').convert('RGBA').resize((768,768),Image.Resampling.LANCZOS);overview.paste(im,(i*768,40),im);dr.text((i*768+24,16),profile.upper(),fill='#343b57')
overview.save(ROOT/'pair-overview.png')
small=Image.new('RGB',(768,560),'#eeeef2');dr=ImageDraw.Draw(small)
for bgrow,bg in enumerate(['#f6f4ee','#0f0f0f']):
    dr.rectangle((0,bgrow*280,768,bgrow*280+279),fill=bg)
    for col,profile in enumerate(['short','full']):
        dr.text((col*384+20,bgrow*280+12),profile.upper(),fill='#888888')
        for x,size in [(20,128),(190,48),(290,24)]:
            im=Image.open(ROOT/f'{profile}-{size}.png').convert('RGBA');small.paste(im,(col*384+x,bgrow*280+65),im)
small.save(ROOT/'pair-small-sizes.png')
a=np.asarray(Image.open(dest/'full-1280.png').convert('RGBA'))
preserved=['identity-crescent','left-sweep','center-fringe','right-main-lock','right-inner-fringe','bow-left','bow-right','eye-left','eye-right']
report={'revision':'r002','svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'base_sha256':hashlib.sha256(base.encode()).hexdigest(),'short_sha256':hashlib.sha256((ROOT/'short.svg').read_bytes()).hexdigest(),'source_A_choice':'user','outfit_official_status':'not claimed; selected alternative clothing reference','r1_identity_path_d_preserved':{name:ids[name].get('d')==original[name].get('d') for name in preserved},'new_inferences':['unseen lower jaw','neck and garment pose adaptation','continuing lower hair'],'alpha':{'transparent_pixels':int((a[:,:,3]==0).sum()),'opaque_pixels':int((a[:,:,3]==255).sum()),'upper_right_alpha':int(a[50,1200,3])},'limitations':['full has no same-pose gold reference','unseen jaw and lower hair remain creative adaptation','no full heavy detector suite run','short strict B99 contract is separate root work','not user accepted']}
(dest/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(ROOT/'full-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report));t.cancel()
