from pathlib import Path
import importlib.util
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage
from scipy.optimize import lsq_linear
from PIL import Image,ImageDraw

OUT=Path(__file__).resolve().parent; BASE=OUT.parent/"material-fit-v5"; ROOT=OUT.parents[4]
sys.path.insert(0,str(ROOT))
from tools.render_svg import render_svg_text
spec=importlib.util.spec_from_file_location("fitter",BASE/"fit_fields_v5.py")
fitter=importlib.util.module_from_spec(spec);spec.loader.exec_module(fitter)
report=json.loads((BASE/"fields.json").read_text());geometry=json.loads((BASE/"geometry-input/geometry.json").read_text())
old=next(r for r in report["palette"] if r["id"]=="hair-right-face-crease")
region=next(r for r in geometry["regions"] if r["id"]==old["id"])
mask=np.asarray(Image.open(BASE/"geometry-input"/region["mask_path"]).convert("L"))>127
source=Image.open(BASE/"source-input.png").convert("RGBA"); rgb=np.asarray(source)[...,:3]
yy,xx=np.nonzero(mask);xy=np.column_stack((xx+.5,yy+.5));target=rgb[mask].astype(float)
y0,y1=float(yy.min()),float(yy.max()+1)
t=(yy+.5-y0)/(y1-y0); weights=fitter._weights(t,5)
colors=np.zeros((5,3))
# The otherwise unobserved thin tip and terminal are directly anchored to
# their actual source bands. Median resists antialias mixture, but every
# visible pixel still remains in the reported error.
colors[0]=np.median(target[yy<y0+8],axis=0)
colors[-1]=np.median(target[yy>=y1-8],axis=0)
residual_target=target-weights[:,[0]]*colors[0]-weights[:,[-1]]*colors[-1]
lower=target.min(axis=0);upper=target.max(axis=0)
for channel in range(3):
    colors[1:4,channel]=lsq_linear(weights[:,1:4],residual_target[:,channel],
                                  bounds=(lower[channel],upper[channel]),tol=1e-10,max_iter=100).x
field={"kind":"linear","from":[775.5,y0],"to":[775.5,y1],
       "x1":775.5,"y1":y0,"x2":775.5,"y2":y1,"gradientUnits":"userSpaceOnUse",
       "stops":fitter._stops(colors),"parameters":9,
       "fit_constraints":"fixed source-aligned long axis; observed endpoint medians; internal stops bounded to observed full-mask RGB extrema"}
new_pred=fitter.evaluate_field(field,xy);old_pred=fitter.evaluate_field(old["field"],xy)
interior=ndimage.binary_erosion(mask,iterations=2)[mask]
tip=yy<775
def errors(pred):
    result={}
    for name,keep in (("all_807_visible_pixels",np.ones(len(yy),bool)),("old_eroded_interior_216_pixels",interior),("tip_y745_to774",tip)):
        diff=pred[keep]-target[keep]
        result[name]={"pixels":int(keep.sum()),"rgb_rmse_255":float(np.sqrt((diff**2).mean())),
                      "rgb_mae_255":float(np.abs(diff).mean()),"max_predicted_rgb":pred[keep].max(axis=0).tolist()}
    return result
patch={"schema":"aikon.single-paint-field-patch.v1","id":old["id"],
       "source_sha256":report["source_sha256"],"geometry_manifest_sha256":report["geometry_manifest_sha256"],
       "original_field_sha256":hashlib.sha256(json.dumps(old["field"],sort_keys=True,separators=(",",":")).encode()).hexdigest(),
       "source_mask_sha256":old["source_mask_sha256"],"field":field,
       "old_errors":errors(old_pred),"new_errors":errors(new_pred),
       "scope":"only this field; no geometry edit, no source edit, no acceptance threshold edit"}
(OUT/"patch.json").write_text(json.dumps(patch,indent=2),encoding="utf-8")
svg_path=OUT.parents[1]/"revisions/v002/short.svg"
svg=svg_path.read_text(encoding="utf-8")
root=ET.fromstring(svg)
definition,_=fitter.svg_paint(field,"paint-hair-right-face-crease")
new_node=ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg">'+definition+'</svg>')[0]
for parent in root.iter():
    for index,child in enumerate(list(parent)):
        if child.get("id")=="paint-hair-right-face-crease":
            parent.remove(child);parent.insert(index,new_node)
ET.register_namespace("","http://www.w3.org/2000/svg")
patched_svg=ET.tostring(root,encoding="unicode")
(OUT/"field-only-test.svg").write_text(patched_svg,encoding="utf-8")
(OUT/"field-only-test.png").write_bytes(render_svg_text(patched_svg,size=1280))
actual=Image.open(OUT/"field-only-test.png").convert("RGBA")
old_image=Image.open(svg_path.parent/"comparison/candidate-render.png").convert("RGBA")
bounds=(755,733,819,930);board=Image.new("RGB",(960,950),"#181a21");draw=ImageDraw.Draw(board)
for i,(im,label) in enumerate(((source,"Clean source"),(old_image,"v002"),(actual,"One-field patch actual SVG"))):
    crop=im.crop(bounds).resize((288,886),Image.Resampling.NEAREST)
    bg=Image.new("RGBA",crop.size,"#101010");bg.alpha_composite(crop);board.paste(bg.convert("RGB"),(i*320+10,50));draw.text((i*320+10,15),label,fill="white")
board.save(OUT/"patch-local-comparison.png")
print(json.dumps({"old":patch["old_errors"],"new":patch["new_errors"],"field":field},indent=2))
