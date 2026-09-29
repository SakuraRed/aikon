"""Promote parent-reviewed r006 draft aliases; no new drawing/revision."""
from pathlib import Path
import os,threading,sys,json,hashlib,shutil,xml.etree.ElementTree as ET
t=threading.Timer(45,lambda:os._exit(124));t.daemon=True;t.start()
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent;revision=ROOT/'full-revisions/r006'
for n in ['full.svg','full-1280.png','full-128.png','full-48.png','full-24.png']:shutil.copy2(revision/n,ROOT/n)
shutil.copy2(revision/'inspection-board.png',ROOT/'full-inspection-board.png')
overview=Image.new('RGB',(1536,820),'#edeef3');dr=ImageDraw.Draw(overview)
for i,profile in enumerate(['short','full']):
    im=Image.open(ROOT/f'{profile}-1280.png').convert('RGBA').resize((768,768),Image.Resampling.LANCZOS);overview.paste(im,(i*768,40),im);dr.text((i*768+24,16),profile.upper(),fill='#343b57')
overview.save(ROOT/'pair-overview.png')
small=Image.new('RGB',(768,560),'#eeeef2');dr=ImageDraw.Draw(small)
for row,bg in enumerate(['#f6f4ee','#0f0f0f']):
    dr.rectangle((0,row*280,768,row*280+279),fill=bg)
    for col,profile in enumerate(['short','full']):
        dr.text((col*384+20,row*280+12),profile.upper(),fill='#888888')
        for x,size in [(20,128),(190,48),(290,24)]:
            im=Image.open(ROOT/f'{profile}-{size}.png').convert('RGBA');small.paste(im,(col*384+x,row*280+65),im)
small.save(ROOT/'pair-small-sizes.png')
edge=json.loads((revision/'edge/report.json').read_text(encoding='utf-8'))
capsule=json.loads((revision/'capsule/report.json').read_text(encoding='utf-8'))
sha=hashlib.sha256((ROOT/'full.svg').read_bytes()).hexdigest()
report={'revision':'r006','status':'current draft; not accepted','promotion_basis':'parent actual visual review; zero interior alpha deficit and lower worst local cluster than r004','svg_sha256':sha,'short_sha256':hashlib.sha256((ROOT/'short.svg').read_bytes()).hexdigest(),'outfit':'user-selected candidate A; not official r1 clothing evidence','original_path_d_unchanged_by_edge_repairs':True,'material_gradients_unchanged_by_edge_repairs':True,'edge':{'status':edge['status'],'source_sha256':edge['source_sha256'],'interior_alpha':edge['metrics']['interior_alpha'],'local_color':edge['metrics']['local_color'],'report':'full-revisions/r006/edge/report.json'},'capsule':{'isolated':[x['status'] for x in capsule['isolated']['eyes']],'visible':[x['status'] for x in capsule['visible']['eyes']],'visibility':capsule['visibility'],'report':'full-revisions/r006/capsule/report.json'},'limits':['local color edge gate still fails:10px>3px','unseen jaw and lower hair are creative adaptation','full has no same-pose gold','short B99 contract is separate','not user artistic acceptance'],'aliases_match_revision':{n:(ROOT/n).read_bytes()==(revision/n).read_bytes() for n in ['full.svg','full-1280.png','full-128.png','full-48.png','full-24.png']}}
(ROOT/'full-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
tree=ET.parse(ROOT/'full.svg').getroot();tags={};ids=[]
for e in tree.iter():
    k=e.tag.split('}')[-1];tags[k]=tags.get(k,0)+1
    if e.get('id'):ids.append(e.get('id'))
check={'revision':'r006','source_sha256':sha,'tag_counts':tags,'forbidden_tags_present':[k for k in ['image','filter','pattern','script','text'] if tags.get(k)],'eye_ids':[x for x in ids if x in ['eye-left','eye-right']],'unique_ids':len(ids)==len(set(ids)),'status':'static structure only; edge gate fail remains'}
(ROOT/'full-primitive-check.json').write_text(json.dumps(check,indent=2),encoding='utf-8')
print(json.dumps({'full_sha256':sha,'aliases_match':all(report['aliases_match_revision'].values()),'edge_status':edge['status'],'local_bad_pixels':edge['metrics']['local_color']['largest_bad_pixel_count'],'alpha_bad_pixels':edge['metrics']['interior_alpha']['bad_pixels']}));t.cancel()
