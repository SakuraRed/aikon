from pathlib import Path
import os,threading,json,sys,copy
t=threading.Timer(45,lambda:os._exit(124));t.daemon=True;t.start()
import numpy as np
from PIL import Image,ImageDraw
import xml.etree.ElementTree as ET
from io import BytesIO
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[3]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text
ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
ref=np.asarray(Image.open(REPO/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png').convert('RGB')).astype(float)
old=np.asarray(Image.open(ROOT/'r003/preview-1280.png').convert('RGB')).astype(float)
tree=ET.parse(ROOT/'r003/short.svg').getroot();g=tree.find('{'+ns+'}g');parts=list(g)
paint={}
for e in tree.iter():
    if e.get('id') in ['measured-right-main-lock','measured-center-fringe','measured-hair-crown-parent']:
        paint[e.get('id')]=ET.tostring(e,encoding='unicode')
for i,e in enumerate(parts):e.set('fill',f'#{i+1:02x}0000');e.attrib.pop('stroke',None)
a=np.asarray(Image.open(BytesIO(render_svg_text(ET.tostring(tree,encoding='unicode'),1280))).convert('RGBA'))
owner=a[:,:,0]; main=next(i+1 for i,e in enumerate(parts) if e.get('id')=='right-main-lock')
records=[]
for y in range(350,561,10):
    row=owner[y,620:790];ix=np.where(row==main)[0]
    if not len(ix):continue
    x=int(ix.min()+620)
    lr=[ref[y,x-4].tolist(),ref[y,x+4].tolist()];lo=[old[y,x-4].tolist(),old[y,x+4].tolist()]
    records.append({'y':y,'boundary_x':x,'source_sides':lr,'r003_sides':lo,'source_jump':float(np.linalg.norm(np.array(lr[1])-lr[0])),'r003_jump':float(np.linalg.norm(np.array(lo[1])-lo[0]))})
roi=(slice(320,610),slice(610,810))
canvas=Image.new('RGB',(800,580))
for i,img in enumerate([ref,old]):canvas.paste(Image.fromarray(img[roi].astype('uint8')).resize((400,580)),(i*400,0))
canvas.save(ROOT/'seam-diagnosis-pair.png')
report={'paint_fields':paint,'boundary_samples':records,'ROI':[610,320,810,610],'roi_MAE':float(np.abs(old[roi]-ref[roi]).mean())}
(ROOT/'seam-diagnosis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report));t.cancel()
