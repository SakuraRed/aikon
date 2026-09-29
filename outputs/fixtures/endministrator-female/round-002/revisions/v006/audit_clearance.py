"""Narrow geometry evidence for this revision, not a universal style rule."""
from pathlib import Path
import sys, json, copy, io
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
REPO=next(p for p in HERE.parents if (p/'tools'/'render_svg.py').exists())
sys.path.insert(0,str(REPO))
from tools.render_svg import render_svg_text
from PIL import Image,ImageDraw
import numpy as np
from scipy.ndimage import distance_transform_edt

def mask(raw,identifier):
    root=ET.fromstring(raw)
    group=next(e for e in root if e.attrib.get('id')=='subject')
    for e in list(group):
        if e.attrib.get('id')!=identifier:
            group.remove(e)
    return np.asarray(Image.open(io.BytesIO(render_svg_text(ET.tostring(root,encoding='unicode'),1024))).convert('RGBA'))[:,:,3]>127

def main():
    records={}
    for name,hair,previous in [('endministrator-female','fringe-right','v005-before-eye-clearance'),('endministrator-male','right-fringe-main','v003-before-eye-clearance')]:
        folder=HERE.parents[1]/name/'round-002'
        detail={}
        for profile in ('short','full'):
            entries={}
            for revision,path in [('before',folder/'revisions'/previous/f'{profile}.svg'),('after',folder/f'{profile}.svg')]:
                raw=path.read_text(encoding='utf-8')
                eye_mask=mask(raw,'eye-right'); hair_mask=mask(raw,hair)
                entries[revision]={'minimum_eye_to_target_fringe_pixel_distance':float(distance_transform_edt(~hair_mask)[eye_mask].min()),'eye_opaque_pixels':int(eye_mask.sum())}
            detail[profile]=entries
        (folder/'eye-clearance-report.json').write_text(json.dumps(detail,indent=2)+'\n',encoding='utf-8')
        records[name]=detail
    print(json.dumps(records,indent=2))

if __name__=='__main__':main()
