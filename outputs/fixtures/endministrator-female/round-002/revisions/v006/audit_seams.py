"""Record actual layer coverage at independently reported alpha points."""
from pathlib import Path
import sys,json,io,copy,math
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
REPO=next(p for p in HERE.parents if (p/'tools'/'render_svg.py').exists())
sys.path.insert(0,str(REPO))
from tools.render_svg import render_svg_text
from PIL import Image,ImageDraw

CASES=[('endministrator-female','full',[(7,652),(784,982),(784,983),(485,1023),(486,1023)]),('endministrator-male','short',[(45,494)]),('endministrator-male','full',[(426,1023),(427,1023)])]

def main():
    all_reports={}
    for subject,profile,points in CASES:
        folder=HERE.parents[1]/subject/'round-002'
        root=ET.fromstring((folder/f'{profile}.svg').read_text(encoding='utf-8'))
        full=Image.open(io.BytesIO(render_svg_text(ET.tostring(root,encoding='unicode'),1024))).convert('RGBA')
        group=next(e for e in root if e.attrib.get('id')=='subject')
        records=[{'xy':[x,y],'final_rgba':list(full.getpixel((x,y))),'layers':[]} for x,y in points]
        for index,elem in enumerate(list(group)):
            isolated=copy.deepcopy(root)
            isolated_group=next(e for e in isolated if e.attrib.get('id')=='subject')
            for other in list(isolated_group):
                if other.attrib.get('id')!=elem.attrib.get('id'):isolated_group.remove(other)
            pixels=Image.open(io.BytesIO(render_svg_text(ET.tostring(isolated,encoding='unicode'),1024))).convert('RGBA')
            for record,(x,y) in zip(records,points):
                value=pixels.getpixel((x,y))
                if value[3]>0:record['layers'].append({'id':elem.attrib.get('id'),'rgba':list(value)})
        all_reports.setdefault(subject,{})[profile]=records
    for subject,report in all_reports.items():
        (HERE.parents[1]/subject/'round-002'/'alpha-seam-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(all_reports,indent=2))

if __name__=='__main__':main()
