"""Render actual semantic SVG field layers, preserving v004 rim/support logic."""
import argparse, importlib.util, json, sys, xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
from svg_fields import paint, surface

NS='{http://www.w3.org/2000/svg}'
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[4]
sys.path.insert(0,str(REPO))
from tools.render_svg import render_svg_text

def fragment(text):return ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg">'+text+'</svg>')

def render(run,output=None):
    run=Path(run);geo=json.loads((run/'geometry-input/geometry.json').read_text());doc=json.loads((run/'fields.json').read_text());fields={r['id']:r['field'] for r in doc['palette']}
    output=Path(output) if output else run
    output.mkdir(parents=True,exist_ok=True)
    root=ET.fromstring((REPO/'outputs/calibration/deepseek-r1/revisions/v004/short.svg').read_text());defs=root.find(NS+'defs');visible=root.find('.//*[@id="visible-material-surfaces"]')
    for r in geo['underpaints']:
        for node in root.iter():
            if node.get('id')==r['id']:node.set('d',r['d'])
    # Subject/face clips were byte-identical in this geometry revision.
    for r in geo['regions']:
        if r['id'].startswith('eye-'):continue
        definition,body=surface(r,fields[r['id']],'natural-'+r['id'])
        for node in fragment(definition):defs.append(node)
        matches=[node for node in list(visible) if node.get('id')==r['id']]
        if len(matches)!=1:raise ValueError(r['id'])
        old=matches[0];i=list(visible).index(old);visible.remove(old);visible.insert(i,list(fragment(body))[0])
    svg=ET.tostring(root,encoding='unicode');(output/'actual-field-study.svg').write_text(svg,encoding='utf8');(output/'actual-field-study.png').write_bytes(render_svg_text(svg,1280))
    source=Image.open(run/'source-input.png').convert('RGBA');candidate=Image.open(output/'actual-field-study.png').convert('RGBA')
    sourcebg=Image.new('RGBA',source.size,'#0f0f0f');sourcebg.alpha_composite(source)
    candidatebg=Image.new('RGBA',candidate.size,'#0f0f0f');candidatebg.alpha_composite(candidate)
    board=Image.new('RGB',(1920,665),'#17191d');d=ImageDraw.Draw(board)
    v004=Image.open(REPO/'outputs/calibration/deepseek-r1/revisions/v004/comparison/candidate-render.png').convert('RGBA');oldbg=Image.new('RGBA',v004.size,'#0f0f0f');oldbg.alpha_composite(v004)
    for i,(im,label) in enumerate([(sourcebg,'Source'),(oldbg,'v004'),(candidatebg,'v6 study: actual SVG')]):board.paste(im.resize((640,640)),(640*i,25));d.text((640*i+6,7),label,fill='white')
    board.save(output/'actual-comparison.png')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--output');a=p.parse_args();render(a.run,a.output)
