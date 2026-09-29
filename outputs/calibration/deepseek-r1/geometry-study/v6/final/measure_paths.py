"""Measure rendered vector paths against disclosed source edge observations."""
import io
import json
import hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import resvg_py

HERE=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def render(d):
    xml=f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1280"><path d="{d}" fill="white" fill-rule="evenodd"/></svg>'
    return np.asarray(Image.open(io.BytesIO(resvg_py.svg_to_bytes(svg_string=xml))))[:,:,3]>=8

old=json.loads((HERE.parent/'v5/geometry.json').read_text())
new=json.loads((HERE/'geometry.json').read_text())
reports={}
for name,obs in new['refinement']['structural_boundary_fits'].items():
    measured={}
    for label,g in [('v5',old),('v6',new)]:
        m=render(next(r['d'] for r in g['regions'] if r['id']==name))
        distance=ndi.distance_transform_edt(~(m^ndi.binary_erosion(m)))
        samples=[]
        for side in ['left','right']:
            for x,y in obs[side+'_samples']:
                # The original face occludes the underfold's left edge below
                # y975. Those latent curve constraints are not visible truth.
                if name=='hair-right-underfold' and side=='left' and y>975:continue
                samples.append({'side':side,'source_xy':[x,y],'distance_to_rendered_boundary':float(distance[y,x])})
        vals=np.array([s['distance_to_rendered_boundary'] for s in samples])
        measured[label]={'samples':samples,'count':len(samples),'mean_distance_px':float(vals.mean()),'max_distance_px':float(vals.max()),'p95_distance_px':float(np.quantile(vals,.95))}
    reports[name]=measured
result={'geometry_sha256':digest(HERE/'geometry.json'),'reference_sha256':new['reference_sha256'],'method':'nearest Euclidean pixel-boundary distance from disclosed source-observed edge coordinates to actual rendered path at coverage >=8/255 (retains subpixel tapered tips); no candidate rescale/warp; not a whole-image acceptance score','reports':reports,'preserved':{k:next(r for r in old['regions'] if r['id']==k)['d']==next(r for r in new['regions'] if r['id']==k)['d'] for k in ['face','eye-left','eye-right']},'underpaint_paths_unchanged':old['underpaints']==new['underpaints']}
(HERE/'rendered-boundary-measurements.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:{v:{a:b for a,b in d.items() if a!='samples'} for v,d in q.items()} for k,q in reports.items()}))
