"""Compare visible core geometry at fixed original coordinates, no registration.

This is contour fidelity evidence, not an overall 99% similarity score.
"""
import io
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import resvg_py

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
NS='http://www.w3.org/2000/svg'


def largest(a):
    lab,n=ndi.label(a); areas=np.bincount(lab.ravel()); areas[0]=0
    return lab==areas.argmax()


def raster_path(d):
    xml=f'<svg xmlns="{NS}" width="1280" height="1280"><path d="{d}" fill="white" fill-rule="evenodd"/></svg>'
    return np.array(Image.open(io.BytesIO(resvg_py.svg_to_bytes(svg_string=xml))))[:,:,3]>127


def measure(reference,actual):
    a=reference^ndi.binary_erosion(reference); b=actual^ndi.binary_erosion(actual)
    dist=np.r_[ndi.distance_transform_edt(~a)[b],ndi.distance_transform_edt(~b)[a]]
    return {'mask_iou':float((reference&actual).sum()/max(1,(reference|actual).sum())),
      'symmetric_contour_mean_pixels':float(dist.mean()),'symmetric_contour_p95_pixels':float(np.percentile(dist,95)),
      'reference_area':int(reference.sum()),'actual_area':int(actual.sum())}


def extract(a):
    r,g,b=a[:,:,:3].astype(float).transpose(2,0,1); yy,xx=np.indices(r.shape)
    face=largest((r>190)&(g>150)&(b>125)&(yy>420)&(a[:,:,3]>127))
    face=ndi.binary_fill_holes(face)
    eye=(r<90)&(g<90)&(b<110)&(yy>610)&face
    eye_left=largest(eye&(xx<450));eye_right=largest(eye&(xx>=450))
    return {'face-underpaint':face,'eye-left':eye_left,'eye-right':eye_right}


def main():
    start=time.monotonic(); out=BASE/'v4'
    doc=json.loads((out/'geometry.json').read_text())
    source=np.array(Image.open(ROOT/'ref/subjects/deepseek/cetus-desktop/r1-clean-calibration-1280.png').convert('RGBA'))
    truth=extract(source)
    legacy=ET.parse(ROOT/'outputs/fixtures/deepseek/round-002/short.svg').getroot()
    legacy.set('width','1280');legacy.set('height','1280')
    old_image=Image.open(io.BytesIO(resvg_py.svg_to_bytes(svg_string=ET.tostring(legacy,encoding='unicode')))).convert('RGBA')
    old=extract(np.array(old_image))
    all_regions={x['id']:x for x in doc['regions']+doc['underpaints']}
    results={}; panels=[]
    for name,ref in truth.items():
        reconstructed=raster_path(all_regions[name]['d'])
        results[name]={'current':measure(ref,reconstructed),'rejected_round_002':measure(ref,old[name])}
    for title,masks in [('r1 reference',truth),('current semantic paths',{n:raster_path(all_regions[n]['d']) for n in truth}),('rejected round 002',old)]:
        panel=Image.new('RGB',(640,676),'#1d2029')
        bg=Image.fromarray(source).convert('RGB').resize((640,640))
        overlay=np.zeros((1280,1280,4),dtype=np.uint8)
        for i,(name,m) in enumerate(masks.items()):
            edge=ndi.binary_dilation(m^ndi.binary_erosion(m),iterations=1)
            overlay[edge]=[255,80+50*i,40,255]
        shown=Image.alpha_composite(Image.fromarray(source),Image.fromarray(overlay)).convert('RGB').resize((640,640))
        panel.paste(shown,(0,36));ImageDraw.Draw(panel).text((12,12),title,fill='white');panels.append(panel)
    canvas=Image.new('RGB',(1920,676),'#1d2029')
    for i,panel in enumerate(panels):canvas.paste(panel,(640*i,0))
    canvas.save(out/'core-geometry-comparison.png')
    report={'schema':'aikon.geometry-study-validation.v1','coordinate_system':'1280 by 1280 source coordinates; legacy SVG rendered at same size; no alignment or warping',
       'source_reference_sha256':doc['reference_sha256'],'reference_extraction':'connected bright face; dark eyes enclosed by filled face; full masks retained',
       'results':results,'limitations':['These are measured contour overlaps, not a universal similarity metric.','Current paths derive from the same source and are reconstruction/calibration, not independent model generalization.','Pose evidence preserves observed relative projection; cannot infer a unique true 3D pitch.','Whale-fin and internal hair interfaces remain partly hand-constrained; no gold segmentation or precision claim assigned.'],
       'duration_seconds':time.monotonic()-start}
    (out/'geometry-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(results))


if __name__=='__main__':main()
