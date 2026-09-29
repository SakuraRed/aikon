from pathlib import Path
import importlib.util
import hashlib
import json
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw

OUT=Path(__file__).resolve().parent
BASE=OUT.parent/"material-fit-v5"
spec=importlib.util.spec_from_file_location("fitter",BASE/"fit_fields_v5.py")
fitter=importlib.util.module_from_spec(spec);spec.loader.exec_module(fitter)
fields=json.loads((BASE/"fields.json").read_text())
geometry=json.loads((BASE/"geometry-input/geometry.json").read_text())
entry=next(r for r in fields["palette"] if r["id"]=="hair-right-face-crease")
region=next(r for r in geometry["regions"] if r["id"]==entry["id"])
mask=np.asarray(Image.open(BASE/"geometry-input"/region["mask_path"]).convert("L"))>127
source=Image.open(BASE/"source-input.png").convert("RGBA"); rgb=np.asarray(source)[...,:3]
interior=ndimage.binary_erosion(mask,iterations=2)
start=np.array(entry["field"]["from"]); delta=np.array(entry["field"]["to"])-start
records=[]
for label,m in (("full_visible_mask",mask),("eroded_fit_support",interior)):
    yy,xx=np.nonzero(m);xy=np.column_stack((xx+.5,yy+.5))
    t=((xy-start)@delta)/(delta@delta)
    records.append({"scope":label,"pixels":len(xx),"x_range":[int(xx.min()),int(xx.max())],
                    "y_range":[int(yy.min()),int(yy.max())],"t_range":[float(t.min()),float(t.max())],
                    "source_rgb_min":rgb[m].min(axis=0).tolist(),"source_rgb_max":rgb[m].max(axis=0).tolist()})
bands=[]
yygrid=np.indices(mask.shape)[0]
for low,high in ((745,775),(775,805),(805,835),(835,865),(865,895),(895,914)):
    m=mask&(yygrid>=low)&(yygrid<high)
    yy,xx=np.nonzero(m)
    pred=fitter.evaluate_field(entry["field"],np.column_stack((xx+.5,yy+.5)))
    bands.append({"y_range":[low,high],"pixels":len(xx),"median_rgb":np.median(rgb[m],axis=0).tolist(),
                  "predicted_median_rgb":np.median(pred,axis=0).tolist(),"source_rgb_min":rgb[m].min(axis=0).tolist(),
                  "source_rgb_max":rgb[m].max(axis=0).tolist()})
report={"id":entry["id"],"field":entry["field"],"sampling_support":records,"long_axis_bands":bands,
        "specific_source_pixels":[{"xy":[x,y],"rgb":rgb[y,x].tolist(),"in_mask":bool(mask[y,x]),"in_fit":bool(interior[y,x])}
                                  for x,y in ((777,748),(776,752),(778,780),(785,835),(795,880))]}
(OUT/"diagnosis.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
candidate=Image.open(OUT.parents[1]/"revisions/v002/comparison/candidate-render.png").convert("RGBA")
bounds=(752,728,821,930);board=Image.new("RGB",(600,950),"#171a21");draw=ImageDraw.Draw(board)
for i,(im,label) in enumerate(((source,"Clean source"),(candidate,"v002 actual SVG render"))):
    crop=im.crop(bounds);crop.thumbnail((270,830));crop=crop.resize((270,790),Image.Resampling.NEAREST)
    bg=Image.new("RGBA",crop.size,"#101010");bg.alpha_composite(crop);board.paste(bg.convert("RGB"),(15+i*300,65));draw.text((15+i*300,20),label,fill="white")
board.save(OUT/"source-vs-v002.png")
