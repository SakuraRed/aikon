"""Measure a real SVG against the frozen, unwatermarked upstream sampling grid."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from tools.compare_r1_reference import REGION_BOXES, compare_pixels, composite, validate_canvas
from tools.render_svg import render_svg_text, backend_info

REFERENCE=ROOT/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png'
EXPECTED='60c234f594ad81319fa74bb4fa8392f10a125127d46bf1d3b47e618b25813da2'

def sha(data):return hashlib.sha256(data).hexdigest()

def evaluate(candidate,output):
    if sha(REFERENCE.read_bytes())!=EXPECTED:
        raise ValueError('Frozen upstream reference changed')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new output directory')
    raw=candidate.read_bytes();svg=raw.decode('utf-8-sig')
    validate_canvas(svg,1280)
    output.mkdir(parents=True,exist_ok=True)
    reference=np.asarray(Image.open(REFERENCE).convert('RGBA'))
    png=render_svg_text(svg,1280)
    pixels=np.asarray(Image.open(io.BytesIO(png)).convert('RGBA'))
    valid=np.ones((1280,1280),dtype=bool)
    subject=(reference[:,:,3]>=128)&(np.max(np.abs(reference[:,:,:3].astype(int)-15),axis=2)>8)
    regions={}
    for name,(x0,y0,x1,y1) in REGION_BOXES.items():
        mask=np.zeros_like(valid);mask[y0:y1,x0:x1]=True;regions[name]=mask
    report=compare_pixels(reference,pixels,{'valid':valid,'subject':subject,'regions':regions})
    report.update({'schema':'aikon.r1-upstream-comparison.v4','reference_sha256':EXPECTED,
                   'reference_contract':'ref/subjects/deepseek/cetus-desktop/reference-contract-v4.json',
                   'candidate_svg_sha256':sha(raw),'render_png_sha256':sha(png),'backend':backend_info(),
                   'watermark_exclusion':None,'alignment':'none; unchanged1280 canvas',
                   'source_attribution':'AvroraCL/CETUS-Desktop at7f14ea7819dfb025bafce2f0d088e4901aefead6',
                   'normalization_note':'Uniform4096-to1280 upstream RGBA only; original user r1 untouched'})
    (output/'candidate-render.png').write_bytes(png)
    ref_rgb,candidate_rgb=composite(reference),composite(pixels)
    diff=np.clip(np.abs(ref_rgb-candidate_rgb)*4,0,255)
    board=Image.new('RGB',(1920,670),'#181a20');draw=ImageDraw.Draw(board)
    for i,(data,label) in enumerate(((ref_rgb,'Unwatermarked upstream reference'),(candidate_rgb,'Actual editable SVG render'),(diff,'Absolute RGB difference x4'))):
        board.paste(Image.fromarray(np.rint(data).astype('uint8')).resize((640,640),Image.Resampling.LANCZOS),(i*640,30));draw.text((i*640+10,10),label,fill='white')
    board.save(output/'comparison-board.png')
    Image.fromarray(np.rint(diff).astype('uint8')).save(output/'diff-x4.png')
    (output/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    for size in (128,48,24):
        (output/f'preview-{size}.png').write_bytes(render_svg_text(svg,size))
    print(json.dumps({'subject':report['subject'],'silhouette':report['silhouette_alpha_proxy'],'output':str(output)}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();evaluate(args.candidate,args.output)
