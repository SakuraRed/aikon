"""Bounded actual-art verification and presentation; no test fixtures changed."""
from pathlib import Path
from io import BytesIO
import copy
import hashlib
import json
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO))
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from tools.render_svg import validate_svg,render_svg_text,backend_info
from tools.analyze_edge_quality import analyze_svg_edges,save_evidence
from tools.analyze_capsule_geometry import analyze_pair,save_eye_evidence


def isolated_eye(svg,eye_id):
    tree=ET.fromstring(svg)
    def walk(parent):
        for node in list(parent):
            tag=node.tag.rsplit('}',1)[-1]
            if tag=='defs':continue
            if tag=='g':walk(node)
            elif node.get('id')==eye_id:
                node.set('fill','#ffffff');node.attrib.pop('stroke',None);node.attrib.pop('stroke-width',None)
            else:parent.remove(node)
    walk(tree)
    png=render_svg_text(ET.tostring(tree,encoding='unicode'),1280)
    return np.asarray(Image.open(BytesIO(png)).convert('RGBA'),dtype=float)[:,:,3]/255


def main():
    for old in ('overview.png','background-review.png','checks.json'):
        source=ROOT/old
        frozen=ROOT/(source.stem+'-review-r004'+source.suffix)
        if source.exists() and not frozen.exists():shutil.copy2(source,frozen)
    summary={'schema':'aikon.female-round3-review.v1','renderer':backend_info(),'user_acceptance':'unassessed','reference_similarity_99':'not_assessed','records':[]}
    board=Image.new('RGB',(1200,1500),'#e8edef');d=ImageDraw.Draw(board)
    try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    except OSError:font=ImageFont.load_default()
    backgrounds=Image.new('RGB',(1120,1240),'#dce2e5');bd=ImageDraw.Draw(backgrounds)
    for i,(branch,profile,rev) in enumerate((('unmasked','short','r004'),('unmasked','full','r005'),('masked','short','r005'),('masked','full','r005'))):
        base=ROOT/branch/profile/'revisions'/rev;svg=(base/'icon.svg').read_text(encoding='utf-8');validate_svg(svg)
        out=ROOT/'quality-r005'/f'{branch}-{profile}';out.mkdir(parents=True,exist_ok=True)
        evidence={'branch':branch,'profile':profile,'revision':rev,'svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'structural':'passed','cache_rgba_equal':{},'user_acceptance':'unassessed'}
        for size in (1280,128,48,24):
            cache=np.asarray(Image.open(base/f'preview-{size}.png').convert('RGBA'))
            current=np.asarray(Image.open(BytesIO(render_svg_text(svg,size))).convert('RGBA'))
            evidence['cache_rgba_equal'][str(size)]=bool(np.array_equal(cache,current))
        report,maps=analyze_svg_edges(svg,size=256);save_evidence(out/'edges',report,maps)
        evidence['edge_gate']={'status':report['status'],'issues':report['issues']}
        if branch=='unmasked':
            masks=[isolated_eye(svg,e) for e in ('eye-left','eye-right')]
            pair=analyze_pair(masks)
            (out/'capsule-pair.json').write_text(json.dumps(pair,indent=2)+'\n',encoding='utf-8')
            for label,mask,r in zip(('left','right'),masks,pair['eyes']):save_eye_evidence(mask,r,out/'capsules'/label)
            evidence['capsules']={'statuses':[x['status'] for x in pair['eyes']],'issues':[x['issues'] for x in pair['eyes']],'limitation':'isolated actual vector geometry; visible occlusion checked visually'}
        else:evidence['capsules']={'status':'not_applicable_user_selected_opaque_eye_occlusion'}
        for name in ('icon.svg','prompt.zh-CN.md'):
            dest=ROOT/branch/(profile+'.svg' if name=='icon.svg' else profile+'-prompt.zh-CN.md')
            shutil.copy2(base/name,dest)
        shutil.copy2(base/'preview-1280.png',ROOT/branch/(profile+'-preview.png'))
        img=Image.open(base/'preview-1280.png').convert('RGBA')
        x=20+(i%2)*600;y=20+(i//2)*750
        d.text((x,y),f'{branch} / {profile} / {rev}',fill='#28343f',font=font)
        panel=Image.new('RGBA',(552,552),'#20262e');panel.alpha_composite(img.resize((552,552),Image.Resampling.LANCZOS));board.paste(panel.convert('RGB'),(x,y+36))
        for j,size in enumerate((128,48,24)):
            mini=Image.open(base/f'preview-{size}.png').convert('RGBA');tile=Image.new('RGBA',mini.size,'#faf8f5');tile.alpha_composite(mini)
            board.paste(tile.convert('RGB'),(x+j*175,y+610));d.text((x+j*175,y+585),str(size)+' px',fill='#28343f',font=font)
        for j,color in enumerate(('#ffffff','#20262e','#767f87','#f6edcf')):
            tile=Image.new('RGBA',(256,256),color);tile.alpha_composite(img.resize((256,256),Image.Resampling.LANCZOS))
            backgrounds.paste(tile.convert('RGB'),(12+j*280,36+i*306))
        bd.text((12,10+i*306),f'{branch} {profile} {rev}',fill='#20262e',font=font)
        summary['records'].append(evidence)
        print(json.dumps({'branch':branch,'profile':profile,'edge':evidence['edge_gate'],'capsules':evidence['capsules']}))
    board.save(ROOT/'overview.png');backgrounds.save(ROOT/'background-review.png')
    (ROOT/'checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
