"""Measure source and baseline material profiles before the one trial."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
from PIL import Image
import numpy as np
from scipy.ndimage import distance_transform_edt
from tools.paint_checks import render_image
HERE=Path(__file__).resolve().parent
REV=ROOT/'outputs/calibration/deepseek-r1/revisions/v006'
source=np.asarray(Image.open(ROOT/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png').convert('RGB')).astype(float)
before=np.asarray(Image.open(REV/'comparison/candidate-render.png').convert('RGB')).astype(float)
inputs=json.loads((HERE/'selected-input.json').read_text())
report={}
for region in inputs['regions']:
    identifier=region['id'];d=region['d']
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1280"><path d="{d}" fill="white"/></svg>'
    mask=np.array(render_image(svg,1280))[:,:,3]>=128
    dist=distance_transform_edt(mask)
    outside=distance_transform_edt(~mask)
    rows=[]
    for a,b in [(0,1),(1,2),(2,3),(3,4),(4,6),(6,9),(9,14),(14,25),(25,1000)]:
        valid=mask&(dist>a)&(dist<=b)
        if valid.sum():rows.append({'distance':[a,b],'n':int(valid.sum()),'source_mean':np.mean(source[valid],axis=0).round(3).tolist(),'before_mean':np.mean(before[valid],axis=0).round(3).tolist(),'source_median':np.median(source[valid],axis=0).tolist(),'mae':float(np.abs(source[valid]-before[valid]).mean())})
    ext=[]
    if identifier.startswith('eye'):
        for a,b in [(0,1),(1,2),(2,3),(3,4),(4,5),(5,7),(7,10)]:
            valid=(~mask)&(outside>a)&(outside<=b)
            ext.append({'distance':[a,b],'source':np.mean(source[valid],axis=0).round(3).tolist(),'before':np.mean(before[valid],axis=0).round(3).tolist()})
    report[identifier]={'field':next(i['field'] for i in inputs['fields'] if i['id']==identifier),'profiles':rows,'outside_profiles':ext}
(HERE/'source-profiles.json').write_text(json.dumps(report,indent=2))
for key,value in report.items():
    print(key)
    print(json.dumps(value,indent=2))
