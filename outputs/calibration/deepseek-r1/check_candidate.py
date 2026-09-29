"""Run existing image-quality checks on an actual candidate, retaining failures."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from tools.render_svg import render_svg_text,validate_svg
from tools import analyze_capsule_geometry as capsule, analyze_edge_quality as edge, analyze_paint_fields as paint

def save(path,data):path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def main(svg_path,geometry_path,output):
    if output.exists() and any(output.iterdir()):raise ValueError('No overwrite')
    output.mkdir(parents=True,exist_ok=True)
    svg=svg_path.read_text(encoding='utf-8');validate_svg(svg)
    image=Image.open(io.BytesIO(render_svg_text(svg,1280))).convert('RGBA')
    masks=[capsule.extract_dark_roi(image,box,seed,max_channel=100) for box,seed in (([135,650,295,900],[211,770]),([560,810,720,1045],[641,930]))]
    eye_report=capsule.analyze_pair(masks);save(output/'capsules.json',eye_report)
    edge_report,maps=edge.analyze_svg_edges(svg,size=256)
    edge.save_evidence(output/'edges',edge_report,maps)
    geometry=json.loads(geometry_path.read_text(encoding='utf-8'))
    material_masks={region['id']:np.asarray(Image.open(geometry_path.parent/region['mask_path']).convert('L'))>127 for region in geometry['regions']}
    material_masks['whole-subject']=np.asarray(Image.open(geometry_path.parent/'masks/subject-underpaint.png').convert('L'))>127
    # Broad visible surfaces promise smooth paint; tiny structural creases have
    # no reliable texture interior and retain opacity-only evidence explicitly.
    smooth={'face','cheek-left','cheek-right','eye-left','eye-right','hair-front-main','hair-right-fringe','hair-back','hair-back-dark-fold','ahoge','whale-side-fin','whale-side-fin-rim','bow-left','bow-right'}
    smooth|={r['id'] for r in geometry['regions'] if r['id'].startswith('frill-white-')}
    rules=json.loads((ROOT/'docs/validation/paint-fields/frozen-rules.json').read_text(encoding='utf-8'))['rules']
    contract={'schema':'aikon.paint-fields.v1','long_edge':1024,'rules':rules,
              'regions':[{'id':name,'mask_id':name,'expectation':'smooth_field' if name in smooth else 'opaque_surface'} for name in material_masks]}
    paint_report,maps=paint.analyze_image(image,contract,region_masks=material_masks)
    save(output/'paint-contract.json',contract);save(output/'paint.json',paint_report)
    for key in ('islands','interior_alpha','fringe'):
        Image.fromarray(maps[key].astype('uint8')*255).save(output/(key+'.png'))
    board=Image.new('RGB',(1080,790),'#8e929b');draw=ImageDraw.Draw(board)
    for col,color in enumerate(('#f7f7f9','#181a24')):
        view=Image.new('RGBA',(510,510),color);view.alpha_composite(image.resize((510,510),Image.Resampling.LANCZOS));board.paste(view.convert('RGB'),(20+col*540,30))
        for i,size in enumerate((128,48,24)):
            sample=Image.open(io.BytesIO(render_svg_text(svg,size))).convert('RGBA')
            panel=Image.new('RGBA',(size,size),color);panel.alpha_composite(sample)
            board.paste(panel.convert('RGB'),(20+col*540+i*170,585));draw.text((20+col*540+i*170,560),str(size)+'px actual',fill='white')
    board.save(output/'review-sheet.png')
    summary={'schema':'aikon.candidate-quality-evidence.v2','svg_file_sha256':hashlib.sha256(svg_path.read_bytes()).hexdigest(),
             'normalized_svg_text_sha256':hashlib.sha256(svg.encode()).hexdigest(),
             'geometry_sha256':hashlib.sha256(geometry_path.read_bytes()).hexdigest(),
             'capsules':[r['status'] for r in eye_report['eyes']],
             'edge_status':edge_report['status'],'edge_issues':edge_report['issues'],
             'paint_status':paint_report['status'],'paint_issues':paint_report['issues'],
             'scope':'Existing thresholds, source-derived visible masks. Narrow folds opacity-only; no claim of texture coverage there.',
             'artistic_acceptance':'not_assessed','similarity_99_percent':'not_assessed'}
    save(output/'summary.json',summary);print(json.dumps(summary))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--svg',type=Path,required=True);p.add_argument('--geometry',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.svg,a.geometry,a.output)
