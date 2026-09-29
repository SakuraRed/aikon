"""Read-only paint-domain audit of eight final SVGs. No art/threshold edits.

Each run audits one candidate and must be launched through run_bounded <=50s.
All source fields are opaque in this audited cohort. Unsupported alpha/styles
fail closed; renderable leaves under defs/clipPath are never treated as paint.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import io
import json
import os
import sys
import xml.etree.ElementTree as ET

for variable in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[variable]='1'
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from tools.render_svg import render_svg_text,validate_svg,backend_info
from tools import analyze_paint_fields as paint
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage as ndi
import numpy as np

OUT=Path(__file__).resolve().parent
SIZE=1024
SVG='http://www.w3.org/2000/svg'
DRAWABLE={'path','rect','circle','ellipse','line','polygon','polyline'}
FAMILY_COLORS={'face':(243,156,79),'hair':(88,166,229),'eyes':(52,215,216),'mask':(178,116,222),'metal':(91,198,128),'cloth':(229,203,77),'other':(143,151,160)}

def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def image(svg,size=SIZE):
    return Image.open(io.BytesIO(render_svg_text(svg,size))).convert('RGBA')

def walk_painted(root):
    result=[]
    def walk(node,in_defs=False,chain=(),inherited_fill='#000000',inherited_stroke='none'):
        tag=node.tag.split('}')[-1]
        if tag in ('defs','clipPath','mask'):return
        fill=node.get('fill',inherited_fill);stroke=node.get('stroke',inherited_stroke)
        chain=chain+(({'tag':tag,'id':node.get('id'),'transform':node.get('transform'),'clip-path':node.get('clip-path')},) if tag in ('svg','g') else ())
        if tag in DRAWABLE and (fill!='none' or stroke!='none'):
            if not node.get('id'):raise ValueError('Unidentified rendered leaf cannot enter auditable ownership map')
            result.append((node,fill,stroke,chain))
        for child in node:walk(child,False,chain,fill,stroke)
    walk(root)
    return result

def assert_opaque_subset(root):
    for node in root.iter():
        for k,v in node.attrib.items():
            if k=='style':raise ValueError('Inline CSS requires separately verified paint resolution')
            if 'opacity' in k and float(v)!=1:raise ValueError('Non-opaque field is not supported by this binary ownership audit')
        for attr in ('fill','stroke','stop-color'):
            value=node.get(attr,'')
            if value.startswith(('rgba','hsla')) or value=='transparent' or (value.startswith('#') and len(value) in (5,9)):
                raise ValueError('Alpha-bearing color requires an alpha-aware ownership model')
    if any(n.tag.endswith('mask') for n in root.iter()):raise ValueError('SVG mask requires independent luminance/alpha resolution')

def family(id,fill):
    if id in ('face','face-visible-domain','full-visible-face'):return 'face'
    if id in ('eye-left','eye-right'):return 'eyes'
    if id in ('suppressor-shadow','fringe-contact-shadow') or id.endswith('-cast'):return 'other'
    if id.startswith('suppressor-'):return 'mask'
    if id.startswith(('clip-','ring-','fastener-','zipper-metal','zipper-pull')) or id=='yellow-silver-connector':return 'metal'
    hair_fields=('crown-material','sweep-material','mid-sweep-material','fall-material','back-material','side-material')
    if 'url(#hair-' in fill or any(fill=='url(#'+x+')' for x in hair_fields):return 'hair'
    if id.startswith(('hood-','coat-','neck-','collar-','standing-collar','upper-chest','chest-','outer-collar','yellow-shoulder','yellow-plate')):return 'cloth'
    return 'other'

def render_ownership(root,target):
    audit=copy.deepcopy(root)
    for node,fill,stroke,_ in walk_painted(audit):
        label='#ffffff' if node.get('id')==target else '#000000'
        node.set('fill',label if fill!='none' else 'none')
        node.set('stroke',label if stroke!='none' else 'none')
    return image(ET.tostring(audit,encoding='unicode'))

def controls():
    # Independent expected ownership with transformed/clipped support and hole.
    src='''<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128"><defs><clipPath id="c"><path id="not-painted" d="M10 10 H90 V90 H10 Z"/></clipPath></defs><g transform="translate(10 10)"><g clip-path="url(#c)"><rect id="support" x="0" y="0" width="110" height="110" fill="#6688aa"/><path id="upper" d="M20 20 H80 V80 H20 Z M35 35 H65 V65 H35 Z" fill="#aa7766" fill-rule="evenodd"/></g></g></svg>'''
    root=validate_svg(src);assert_opaque_subset(root)
    ids=[n.get('id') for n,*_ in walk_painted(root)]
    assert ids==['support','upper']
    original=np.array(image(src,128))
    outcomes={}
    for target in ids:
        recolored=copy.deepcopy(root)
        for n,f,s,_ in walk_painted(recolored):n.set('fill','#ffffff' if n.get('id')==target else '#000000')
        a=np.array(image(ET.tostring(recolored,encoding='unicode'),128))
        assert np.array_equal(a[:,:,3],original[:,:,3])
        own=(a[:,:,:3]==255).all(axis=2)&(a[:,:,3]==255)
        points={'outside':(15,15),'support_rim':(25,25),'upper_surface':(35,35),'hole_reveals_support':(55,55)}
        measured={name:bool(own[y,x]) for name,(x,y) in points.items()}
        expected={'outside':False,'support_rim':target=='support','upper_surface':target=='upper','hole_reveals_support':target=='support'}
        assert measured==expected,(target,measured,expected)
        outcomes[target]=measured
    # False opaque rewriting must be rejected, not silently black-painted.
    invalid=copy.deepcopy(root);next(n for n in invalid.iter() if n.get('id')=='support').set('opacity','.5')
    try:assert_opaque_subset(invalid)
    except ValueError:alpha_rejected=True
    else:raise AssertionError('non-opaque field was not rejected')
    write(OUT/'ownership-controls.json',{'status':'pass','rendered_ids':ids,'definitions_excluded':True,'draw_order_clip_transform_hole_checks':outcomes,'alpha_equality':True,'nonopaque_rejected':alpha_rejected,'scope':'ownership extraction mechanics only, not actual candidate masks or artistic acceptance'})

def run(candidate):
    sex,branch,profile=candidate.split('/')
    source=ROOT/f'outputs/round-003/endministrator-{sex}/{branch}/{profile}.svg'
    target=OUT/(sex+'-'+branch+'-'+profile);target.mkdir(parents=True,exist_ok=True)
    if (target/'summary.json').exists():raise ValueError('Completed audit snapshot is immutable')
    rules_file=ROOT/'docs/validation/paint-fields/frozen-rules.json'
    rules=json.loads(rules_file.read_text(encoding='utf-8'))['rules']
    raw_source=source.read_bytes();text=raw_source.decode('utf-8');root=validate_svg(text);assert_opaque_subset(root)
    original=image(text);original.save(target/'candidate-1024.png');rgba=np.array(original)
    opaque=rgba[:,:,3]==255
    leaves=walk_painted(root)
    masks={};records=[];owned=np.zeros((SIZE,SIZE),bool);overlap=np.zeros((SIZE,SIZE),bool)
    audit_union=np.zeros((SIZE,SIZE),bool);label_colors=np.zeros((SIZE,SIZE,3),dtype=np.uint8)
    (target/'masks').mkdir(exist_ok=True)
    alpha_mismatch_union=np.zeros((SIZE,SIZE),bool)
    conservative_exclusion=np.zeros((SIZE,SIZE),bool)
    opaque_inner=ndi.minimum_filter(opaque,size=7,mode='reflect')
    for number,(node,fill,stroke,chain) in enumerate(leaves):
        id=node.get('id');fam=family(id,fill)
        label=np.array(render_ownership(root,id))
        equal=np.array_equal(label[:,:,3],rgba[:,:,3])
        mismatch=label[:,:,3]!=rgba[:,:,3]
        if (mismatch&opaque_inner).any():raise ValueError('Ownership recolor changes original interior alpha: '+id)
        alpha_mismatch_union|=mismatch
        # Exact equality is reported honestly. A discovered one-LSB coverage
        # difference on an external AA pixel is not silently called equal.
        # Exclude every possible 49x49 footprint touching any discrepant pixel;
        # this cannot improve/report cleanliness of the excluded boundary.
        excluded=ndi.maximum_filter(mismatch,size=49,mode='reflect') if mismatch.any() else mismatch
        conservative_exclusion|=excluded
        mask=(label[:,:,:3]==255).all(axis=2)&(label[:,:,3]==255)&opaque&~excluded
        overlap|=owned&mask;owned|=mask;label_colors[mask]=FAMILY_COLORS[fam]
        count=int(mask.sum())
        record={'id':id,'family':fam,'original_fill':fill,'original_stroke':stroke,'ancestor_chain':chain,'visible_unmixed_pixels':count,'original_alpha_exactly_preserved':equal,'alpha_mismatch_pixels':int(mismatch.sum()),'alpha_mismatch_max_0_255':int(np.abs(label[:,:,3].astype(int)-rgba[:,:,3].astype(int)).max()),'mismatch_in_3px_opaque_interior':False,'conservative_49px_support_exclusion_pixels':int(excluded.sum()),'paint_domain':'unassessed_other_semantics' if fam=='other' else 'unassessed_insufficient_visible_area' if count<64 else 'included_individual_leaf'}
        if fam!='other' and count>=64:
            masks[id]=mask;audit_union|=mask
            Image.fromarray(mask.astype('uint8')*255).save(target/'masks'/f'{id}.png')
        records.append(record)
    if overlap.any():raise ValueError('Ambiguous same-pixel full ownership detected')
    contract={'schema':paint.SCHEMA,'long_edge':SIZE,'rules':rules,'threshold_provenance':'Unchanged docs/validation/paint-fields/frozen-rules.json; source raw SHA '+sha(rules_file),'regions':[{'id':id,'mask_id':id,'expectation':'smooth_field'} for id in masks]}
    report,maps=paint.analyze_image(original,contract,masks)
    report['source_binding']={'raw_svg_sha256':hashlib.sha256(raw_source).hexdigest(),'path':source.relative_to(ROOT).as_posix(),'decoded_rgba_sha256':paint.decoded_hash(original),'renderer':backend_info(),'analysis_input':'native exact final SVG render at1024; no 1280-to1024 image/mask resampling','analyzer_sha256':sha(ROOT/'tools/analyze_paint_fields.py'),'rules_file_sha256':sha(rules_file)}
    write(target/'paint-report.json',report);write(target/'regions.json',contract)
    grain_union=np.zeros((SIZE,SIZE),bool);mottle_union=np.zeros_like(grain_union)
    findings=[];families={}
    for region in report['regions']:
        id=region['id'];r=next(x for x in records if x['id']==id);fam=r['family']
        fields=maps['texture_support'][id]
        grain_union|=fields['grain'];mottle_union|=fields['mottle']
        entry={'id':id,'family':fam,'visible_pixels':r['visible_unmixed_pixels'],'legacy_status':region['status'],'legacy_failures':region['failures'],'islands':region['color_islands'],'opacity':region['opacity'],'full_kernel_support':region['texture_support_evidence']['scales']}
        findings.append(entry)
        f=families.setdefault(fam,{'visible_pixels':0,'grain_supported_pixels':0,'mottle_supported_pixels':0,'regions':0,'legacy_failures':0,'grain_exceeds':0,'mottle_exceeds':0,'mottle_unassessed_regions':0})
        f['regions']+=1;f['visible_pixels']+=entry['visible_pixels'];f['legacy_failures']+=bool(region['failures'])
        for name in ('grain','mottle'):
            evidence=entry['full_kernel_support'][name]
            f[name+'_supported_pixels']+=evidence['sample_pixels'];f[name+'_exceeds']+=bool(evidence['exceeds_bound'])
        f['mottle_unassessed_regions']+=entry['full_kernel_support']['mottle']['measurement_status'].startswith('not_assessed')
    base=Image.new('RGBA',original.size,'#f7f5f0');base.alpha_composite(original);base_rgb=np.array(base.convert('RGB'))
    overlay=base_rgb.copy();overlay[owned]=np.uint8(np.rint(.60*base_rgb[owned]+.40*label_colors[owned]))
    boundaries=np.zeros_like(owned)
    for mask in masks.values():boundaries|=mask&~ndi.binary_erosion(mask,iterations=1)
    overlay[boundaries]=[255,207,48]
    Image.fromarray(overlay).save(target/'ownership-overlay.png')
    Image.fromarray(label_colors).save(target/'visible-owner-families.png')
    for name,mask in [('unmixed-owned',owned),('audit-covered',audit_union),('grain-supported',grain_union),('mottle-supported',mottle_union),('legacy-islands',maps['islands']),('recolor-alpha-mismatch',alpha_mismatch_union),('recolor-conservative-exclusion',conservative_exclusion)]:
        Image.fromarray(mask.astype('uint8')*255).save(target/(name+'.png'))
    support=base_rgb.copy();support[mottle_union]=np.uint8(.45*support[mottle_union]+.55*np.array([50,201,111]));support[grain_union&~mottle_union]=np.uint8(.5*support[grain_union&~mottle_union]+.5*np.array([255,188,48]));Image.fromarray(support).save(target/'full-support-overlay.png')
    board=Image.new('RGB',(1536,620),'#e9ecef');draw=ImageDraw.Draw(board)
    for col,(name,im) in enumerate([('Final native SVG',base.convert('RGB')),('Leaf boundaries + families',Image.fromarray(overlay)),('Full kernel: green=mottle; amber=grain',Image.fromarray(support))]):
        board.paste(im.resize((512,512),Image.Resampling.LANCZOS),(col*512,40));draw.text((col*512+8,15),name,fill='#172536')
    legend='face=orange / hair=blue / eyes=cyan / mask=purple / metal=green / cloth=yellow; family unions only for display, never smooth-field tests'
    draw.text((8,566),candidate+' | '+legend,fill='#172536');board.save(target/'inspection-board.png')
    if maps['islands'].any():
        red=base_rgb.copy();red[maps['islands']]=[245,46,55];Image.fromarray(red).save(target/'islands-overlay.png')
    summary={'candidate':candidate,'source_binding':report['source_binding'],'ownership_method':'Each target opaque rendered leaf is white; all other rendered leaves black. Original order, clips, transforms, holes and stroke geometry retained; defs paths excluded. Exact white/alpha255 pixels only, with original alpha255 and a conservative49x49 exclusion around any instrument alpha discrepancy.','ownership_alpha_equality_all_leaves':not bool(alpha_mismatch_union.any()),'recolor_alpha_mismatch_union_pixels':int(alpha_mismatch_union.sum()),'recolor_alpha_mismatch_max_0_255':max(r['alpha_mismatch_max_0_255'] for r in records),'recolor_conservative_exclusion_pixels':int(conservative_exclusion.sum()),'recolor_interior_alpha_mismatch':False,'painted_leaf_count':len(leaves),'measured_leaf_count':len(masks),'all_unmixed_visible_pixels':int(owned.sum()),'opaque_pixels':int(opaque.sum()),'opaque_pixels_with_mixed_or_no_single_owner':int((opaque&~owned).sum()),'audit_domain_pixels':int(audit_union.sum()),'audit_fraction_of_opaque':float(audit_union.sum()/max(1,opaque.sum())),'grain_full_support_pixels':int(grain_union.sum()),'mottle_full_support_pixels':int(mottle_union.sum()),'grain_fraction_of_opaque':float(grain_union.sum()/max(1,opaque.sum())),'mottle_fraction_of_opaque':float(mottle_union.sum()/max(1,opaque.sum())),'families':families,'legacy_status':report['status'],'legacy_issues':report['issues'],'regions':findings,'leaf_ownership':records,'not_covered':['Opaque/AA mixed boundary pixels','49x49 footprint neighborhoods around any recolor instrument alpha discrepancy; exact equality failure is not concealed','Fields whose family is not declared','Regions with <64 fully visible pixels','Thin regions without the full13x13 or49x49 filtering footprint','Aesthetic correctness or reference fidelity; arbitrary radial fields are outside quadratic-island model'],'original_art_mutated':False,'frozen_thresholds_changed':False,'visual_acceptance':'not_assessed','whole_art_pass':'not_claimed'}
    write(target/'summary.json',summary)
    if source.read_bytes()!=raw_source:raise ValueError('Source changed during audit; discard this snapshot and rebind')
    print(json.dumps({'candidate':candidate,'legacy_status':report['status'],'regions':len(masks),'issues':report['issues'],'audit_fraction':summary['audit_fraction_of_opaque'],'grain_fraction':summary['grain_fraction_of_opaque'],'mottle_fraction':summary['mottle_fraction_of_opaque'],'families':families},ensure_ascii=False,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidate');ap.add_argument('--controls',action='store_true');args=ap.parse_args()
    if args.controls:controls()
    else:run(args.candidate)
