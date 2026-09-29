"""Expand diagnostic canvas to distinguish edge AA from internal paint gaps."""
from pathlib import Path
import sys,json,io,copy
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
REPO=next(p for p in HERE.parents if (p/'tools'/'render_svg.py').exists())
sys.path.insert(0,str(REPO))
from tools.render_svg import render_svg_text
from PIL import Image
import numpy as np
from scipy import ndimage as ndi

def main():
    for subject,points in [('endministrator-female',[(485,1023),(486,1023)]),('endministrator-male',[(426,1023),(427,1023)])]:
        folder=HERE.parents[1]/subject/'round-002'
        root=ET.fromstring((folder/'full.svg').read_text(encoding='utf-8'))
        root.set('width','1100');root.set('height','1100');root.set('viewBox','0 0 1100 1100')
        pixels=np.asarray(Image.open(io.BytesIO(render_svg_text(ET.tostring(root,encoding='unicode'),1100))).convert('RGBA'))
        alpha=pixels[:,:,3]; occupied=alpha>0
        interior=ndi.binary_erosion(occupied,structure=np.ones((3,3),bool),iterations=3,border_value=0)
        rows=[]
        for x,y in points:
            rows.append({'xy':[x,y],'alpha':int(alpha[y,x]),'inside_3px_eroded_actual_silhouette':bool(interior[y,x]),'alpha_5x5':alpha[y-2:y+3,x-2:x+3].tolist()})
        report={'method':'Expanded viewBox/canvas to 1100 square without changing any subject coordinates. This reveals actual outside silhouette below original viewport.', 'points':rows}
        (folder/'viewport-edge-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(subject,json.dumps(report))

if __name__=='__main__':main()
