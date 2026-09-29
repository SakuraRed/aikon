"""Bounded same-source material study. Fit data is never embedded in SVG."""
import argparse, copy, hashlib, importlib.util, json, math, shutil, time
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.optimize import lsq_linear

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
spec=importlib.util.spec_from_file_location('single',HERE.parent/'material-fit-v5/fit_fields_v5.py')
single=importlib.util.module_from_spec(spec);spec.loader.exec_module(single)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,value): Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf8')
def stops(colors): return [{'offset':i/(len(colors)-1),'rgb':c.tolist(),'color':'#'+''.join(f'{round(v):02x}' for v in c)} for i,c in enumerate(colors)]

def basis(field,xy):
    if field['kind']=='solid': return np.ones((len(xy),1))
    if field['kind']=='linear':
        delta=np.array(field['to'])-field['from'];t=(xy-field['from'])@delta/(delta@delta)
    else: t=np.sqrt(np.square((xy-field['center'])/field['radii']).sum(axis=1))
    t=np.clip(t,0,1)
    offsets=np.array([s['offset'] for s in field['stops']])
    # Handles future nonuniform stops, not only equally spaced internal knots.
    idx=np.minimum(np.maximum(np.searchsorted(offsets,t,side='right')-1,0),len(offsets)-2)
    frac=(t-offsets[idx])/(offsets[idx+1]-offsets[idx]);b=np.zeros((len(t),len(offsets)))
    b[np.arange(len(t)),idx]=1-frac;b[np.arange(len(t)),idx+1]=frac
    return b

def alpha(glaze,xy):
    t=np.sqrt(np.square((xy-glaze['center'])/glaze['radii']).sum(axis=1))
    return np.clip(1-t,0,1)*glaze['peak_opacity']

def eval_field(field,xy):
    if field['kind']=='layered':
        result=eval_field(field['base'],xy)
        for g in field['glazes']:
            a=alpha(g,xy)[:,None];result=result*(1-a)+np.array(g['stops'][0]['rgb'])*a
        return result
    colors=np.array([field['rgb']]) if field['kind']=='solid' else np.array([s['rgb'] for s in field['stops']])
    return basis(field,xy)@colors

def solve(base,glazes,xy,values,lo,hi):
    b=basis(base,xy)
    for g in glazes:
        a=alpha(g,xy)[:,None];b=np.column_stack([b*(1-a),a])
    # All RGB coefficients are bounded even when a basis knot has no samples.
    # Tiny anchors retain the material mean there; unsupported colors cannot
    # explode into bright tips (the prior v5 failure).
    gram=b.T@b+1e-4*np.eye(b.shape[1]);rhs=b.T@values+1e-4*np.tile(values.mean(axis=0),(b.shape[1],1))
    chol=np.linalg.cholesky(gram);targets=np.linalg.solve(chol,rhs)
    colors=np.column_stack([lsq_linear(chol.T,targets[:,c],bounds=(lo[c],hi[c]),tol=1e-7,max_iter=35).x for c in range(3)])
    prediction=b@colors
    error=float(np.sqrt(np.mean((prediction-values)**2)))
    out=copy.deepcopy(base);n=1 if base['kind']=='solid' else len(base['stops'])
    if out['kind']=='solid':out.update(rgb=colors[0].tolist())
    else:out['stops']=stops(colors[:n])
    if glazes:
        layers=[]
        for i,g in enumerate(glazes):
            gg=copy.deepcopy(g);gg['kind']='radial';gg['stops']=[{'offset':0,'rgb':colors[n+i].tolist(),'opacity':g['peak_opacity']},{'offset':1,'rgb':colors[n+i].tolist(),'opacity':0}];layers.append(gg)
        out={'kind':'layered','base':out,'glazes':layers}
    return out,error

def stats(pred,values):
    delta=pred-values
    return {'rgb_rmse_255':float(np.sqrt(np.mean(delta**2))),'rgb_mae_255':float(np.mean(abs(delta))),
            'pixel_rmse_p95_255':float(np.quantile(np.sqrt(np.mean(delta**2,axis=1)),.95)),
            'predicted_min_rgb':pred.min(axis=0).tolist(),'predicted_max_rgb':pred.max(axis=0).tolist()}

def fit_region(rgb,mask,base,layer_allowed,retain_existing=False):
    yy,xx=np.nonzero(mask);allxy=np.column_stack((xx+.5,yy+.5));allvalues=rgb[mask].astype(float)
    interior=ndimage.binary_erosion(mask,iterations=2)
    if interior.sum()<32:interior=mask.copy()
    iy,ix=np.nonzero(interior);xy=np.column_stack((ix+.5,iy+.5));values=rgb[interior].astype(float)
    lo=np.maximum(0,np.quantile(values,.002,axis=0)-2);hi=np.minimum(255,np.quantile(values,.998,axis=0)+2)
    # The all-visible support, not eroded core, defines source spatial extent.
    bounds=[xx.min(),yy.min(),xx.max()+1,yy.max()+1];w,h=bounds[2]-bounds[0],bounds[3]-bounds[1]
    original=copy.deepcopy(base)
    if base['kind']=='linear':
        # Reparameterize onto the complete VISIBLE support, including tips.
        # The old bbox/corner projection often left outer knots unsupported.
        direction=np.array(base['to'])-base['from'];direction/=np.linalg.norm(direction)
        q=allxy@direction;base=copy.deepcopy(base)
        base['from']=(direction*q.min()).tolist();base['to']=(direction*q.max()).tolist()
    sample=np.linspace(0,len(xy)-1,min(2400,len(xy))).astype(int);sx,sv=xy[sample],values[sample]
    field,err=solve(base,[],sx,sv,lo,hi);baseline=copy.deepcopy(field)
    trials=[{'glazes':0,'sample_rmse':err}]
    selected=[]
    if layer_allowed and min(w,h)>50:
        choices=[]
        # Broad physical extent only: >=65% width/height, nine material-relative
        # locations. Two selected fields at most, no residual-driven tiny spots.
        for nx,ny in ((0,0),(0,.5),(0,1),(.5,0),(.5,.5),(.5,1),(1,0),(1,.5),(1,1)):
            for scale in (.70,1.15):
                choices.append({'center':[float(bounds[0]+nx*w),float(bounds[1]+ny*h)],'radii':[float(w*scale),float(h*scale)],'peak_opacity':.35})
        for stage in range(2):
            scored=[]
            for g in choices:
                if g in selected:continue
                candidate,e=solve(base,selected+[g],sx,sv,lo,hi);scored.append((e,candidate,g))
            e,candidate,g=min(scored,key=lambda item:item[0]);trials.append({'glazes':stage+1,'sample_rmse':e,'proposed_glaze':g})
            # Additional optical complexity must earn a material-sized gain.
            if err-e < max(.15,.05*err):break
            selected.append(g);field,err=candidate,e
    if retain_existing:
        field=original;selected=[]
    before=eval_field(original,allxy);after=eval_field(field,allxy)
    distance=ndimage.distance_transform_edt(mask);tip=(distance[mask]<=2)
    return field,{'fit_pixels':int(interior.sum()),'all_visible_pixels':int(mask.sum()),'source_color_bounds_rgb':[lo.tolist(),hi.tolist()],
       'candidate_models':trials,'before_all_visible':stats(before,allvalues),'after_all_visible':stats(after,allvalues),
       'before_interior':stats(eval_field(original,xy),values),'after_interior':stats(eval_field(field,xy),values),
       'thin_or_edge_pixels':int(tip.sum()),'thin_or_edge_after':stats(after[tip],allvalues[tip]),
       'all_visible_outside_color_bounds':int(np.any((after<lo-1e-6)|(after>hi+1e-6),axis=1).sum()),
       'glaze_count':len(selected),'retained_existing_field':retain_existing},interior

TARGETS={'face','hair-front-main','hair-right-fringe','hair-right-underfold','hair-left-fringe-fold','hair-center-fold','whale-side-fin','whale-side-fin-rim','ahoge','bow-left','bow-right'}

def run(geometry,output,only=None):
    start=time.monotonic();geometry=Path(geometry);output=Path(output)
    if output.exists():raise ValueError('immutable run output must not exist')
    output.mkdir(parents=True);gbytes=geometry.read_bytes();g=json.loads(gbytes)
    source=REPO/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png'
    if sha(source)!=g['reference_sha256']:raise ValueError('source mismatch')
    (output/'source-input.png').write_bytes(source.read_bytes());snap=output/'geometry-input';snap.mkdir()
    (snap/'geometry.json').write_bytes(gbytes)
    for r in g['regions']+g['underpaints']:
        dest=snap/r['mask_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(geometry.parent/r['mask_path'],dest)
    if geometry.read_bytes()!=gbytes:raise RuntimeError('geometry changed during snapshot')
    previous=REPO/'outputs/calibration/deepseek-r1/revisions/v004/paint-fields.json';base_doc=json.loads(previous.read_text());base={r['id']:r for r in base_doc['palette']}
    rgb=np.array(Image.open(source).convert('RGB'));result=copy.deepcopy(base_doc);result['schema']='aikon.r1-natural-fields.v1';result['palette']=[]
    result.update(geometry_manifest_sha256=sha(snap/'geometry.json'),geometry_manifest_file='geometry-input/geometry.json',source_snapshot_file='source-input.png',previous_fields_sha256=sha(previous))
    for r in g['regions']:
        rid=r['id'];mask=np.array(Image.open(snap/r['mask_path']).convert('L'))>127
        old=base[rid];oldfield=old['field']
        # Every field is validated/rebound to actual masks; changed masks always
        # refit their base model before any layered selection.
        changed=old.get('source_mask_sha256')!=sha(snap/r['mask_path'])
        basefield=copy.deepcopy(oldfield)
        if changed and mask.sum()>32:
            try:basefield,_,_=single.fit_field(rgb,mask)
            except ValueError:
                vals=rgb[mask];basefield={'kind':'solid','rgb':np.median(vals,axis=0).tolist()}
        allowed=rid in TARGETS or rid.startswith('frill-white-')
        if only and rid not in only:allowed=False
        field,report,_=fit_region(rgb,mask,basefield,allowed,retain_existing=not changed and not allowed)
        yy,xx=np.nonzero(mask);allxy=np.column_stack((xx+.5,yy+.5))
        report['v004_field_on_actual_v6_mask_all_visible']=stats(eval_field(oldfield,allxy),rgb[mask].astype(float))
        item=copy.deepcopy(old);item.update(field=field,source_mask_sha256=sha(snap/r['mask_path']),stats=report)
        item['stats']['geometry_mask_changed']=changed;result['palette'].append(item)
        print(rid,round(report['before_interior']['rgb_rmse_255'],3),'->',round(report['after_interior']['rgb_rmse_255'],3),'glazes',report['glaze_count'],flush=True)
    result['execution_seconds']=time.monotonic()-start
    result['fitting_policy']={'max_glazes':2,'glaze_peak_opacity':.35,'minimum_radial_radius_fraction_of_material_bbox':.70,'whole_visible_prediction_bounds_checked':True,'arbitrary_watermark_exclusion':False}
    dump(output/'fields.json',result);shutil.copyfile(__file__,output/'fit_natural.py');shutil.copyfile(HERE/'svg_fields.py',output/'svg_fields.py')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--geometry',required=True);p.add_argument('--output',required=True);p.add_argument('--only',nargs='*');a=p.parse_args();run(a.geometry,a.output,a.only)
