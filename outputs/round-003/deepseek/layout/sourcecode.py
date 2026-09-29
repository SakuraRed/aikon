"""Non-final full composition study; collar decision remains pending."""
from pathlib import Path
import os,threading,sys,json,copy,hashlib,shutil
t=threading.Timer(45,lambda:os._exit(124));t.daemon=True;t.start()
import xml.etree.ElementTree as ET
from PIL import Image
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text,validate_svg
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
def tag(n):return '{'+NS+'}'+n
tree=ET.parse(ROOT/'short.svg').getroot();g=tree.find(tag('g'));defs=tree.find(tag('defs'))
g.set('transform','translate(0 0) scale(0.78)')
tree.find(tag('title')).text='DeepSeek full composition study — collar unresolved'
tree.find(tag('desc')).text='Non-final layout. Original head identity is preserved; unseen lower jaw, neck and continuing back hair are creative extrapolations. Collar selection is still pending.'
grad=ET.SubElement(defs,tag('linearGradient'),{'id':'full-inferred-neck','gradientUnits':'userSpaceOnUse','x1':'440','y1':'1370','x2':'425','y2':'1550'})
for z,c in [(0,'#eecdc4'),(.35,'#f3d6cc'),(1,'#f8e5da')]:ET.SubElement(grad,tag('stop'),{'offset':str(z),'stop-color':c})
def path(name,d,fill):return ET.Element(tag('path'),{'id':name,'d':d,'fill':fill})
hair=path('full-inferred-back-hair','M 793 1150 C 855 1302 891 1453 850 1568 C 808 1648 736 1664 666 1680 C 739 1572 771 1424 735 1290 Z','url(#measured-rear-lower-flow)')
neck=path('full-inferred-neck-shape','M 341 1372 C 364 1441 385 1487 375 1566 L 634 1546 C 575 1476 568 1416 601 1360 Z','url(#full-inferred-neck)')
g.insert(0,hair);g.insert(1,neck)
for name in ['face-parent','face-continuous-illumination']:
    e=next(q for q in g if q.get('id')==name)
    d=e.get('d');assert 'L -20 1289 Z' in d
    e.set('d',d.replace('L -20 1289 Z','C 653 1370 538 1422 396 1399 C 219 1390 70 1321 -20 1238 Z'))
dest=ROOT/'layout';dest.mkdir(exist_ok=True)
svg=ET.tostring(tree,encoding='unicode');validate_svg(svg)
(dest/'full-layout.svg').write_text(svg,encoding='utf-8')
(dest/'full-layout-1280.png').write_bytes(render_svg_text(svg,1280))
shutil.copy2(ROOT/'full-layout.py',dest/'sourcecode.py');shutil.copy2(ROOT/'full-layout.prompt.zh-CN.md',dest/'actualprompt.md')
(dest/'layout.json').write_text(json.dumps({'status':'layout-only collar unresolved','scale':.78,'new_inferences':['previously unseen jaw below raw y1289','neck support','lower back hair continuation'],'preserved':'source eyes, forehead, hook, side fin, bow, head pleats and all local material fields'},indent=2),encoding='utf-8')
print('full layout rendered; no collar decision encoded');t.cancel()
