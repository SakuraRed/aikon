"""Portable standard-library paint-only SVG patch; no source images or fitting.

Existing material paths and coverage clips remain unchanged. Open rim curves are
exact subsequences of those fixed material boundaries, never new silhouettes.
"""
from copy import deepcopy
import xml.etree.ElementTree as ET

NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
def tag(name): return '{'+NS+'}'+name

def apply_gloss(svg, plan):
    root=ET.fromstring(svg)
    by_id={e.get('id'):e for e in root.iter() if e.get('id')}
    defs=root.find(tag('defs'))
    parents={child:parent for parent in root.iter() for child in parent}
    for identifier in ['eye-left','eye-right']:
        eye=by_id[identifier]
        for width,opacity in plan['eye_outer']:
            by_id[f'{identifier}-warm-rim-{width}'].set('stroke-opacity',str(opacity))
        parent=parents[eye]
        for suffix in ['inner-transition','inner-rim']:
            parent.remove(by_id[identifier+'-'+suffix])
        position=list(parent).index(eye)+1
        for index,band in enumerate(plan['eye_inner']):
            stroke=ET.Element(tag('path'),{'id':identifier+'-gloss-band-'+str(index),'d':eye.get('d'),'fill':'none','fill-rule':eye.get('fill-rule','evenodd'),'stroke':band['color'],'stroke-width':str(band['width']),'stroke-opacity':str(band['opacity']),'stroke-linejoin':'round','clip-path':f'url(#clip-{identifier})'})
            parent.insert(position+index,stroke)
    fragments=[]
    for item in plan['open_rims']:
        identifier=item['owner']; owner=by_id[identifier]; parent=parents[owner]
        clip_id='gloss-owner-'+identifier
        clip=ET.SubElement(defs,tag('clipPath'),{'id':clip_id})
        ET.SubElement(clip,tag('path'),{'d':owner.get('d'),'clip-rule':owner.get('fill-rule','evenodd')})
        group=ET.Element(tag('g'),{'id':identifier+'-microgloss','clip-path':f'url(#{clip_id})'})
        for i,band in enumerate(item['bands']):
            ET.SubElement(group,tag('path'),{'id':identifier+'-edge-light-'+str(i),'d':item['d'],'fill':'none','stroke':band['color'],'stroke-width':str(band['width']),'stroke-opacity':str(band['opacity']),'stroke-linecap':'round','stroke-linejoin':'round'})
        parent.insert(list(parent).index(owner)+1,group)
        fragments.append(ET.tostring(clip,encoding='unicode')+ET.tostring(group,encoding='unicode'))
    return ET.tostring(root,encoding='unicode'),fragments
