from pathlib import Path
import json
import numpy as np
from scipy import ndimage
from PIL import Image
from fit_fields import evaluate_field

OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[3]
RUN=OUT/"material-fit-v2-petals"
geometry=json.loads((RUN/"geometry-input/geometry.json").read_text())
fields=json.loads((RUN/"fields.json").read_text())
paints={r["id"]:r["field"] for r in fields["palette"]}
rgb=np.asarray(Image.open(ROOT/"ref/user-mode/r1.png").convert("RGB"))
records=[]
for region in geometry["regions"]:
    name=region["id"]
    if not(name.startswith("frill-white") or name=="whale-side-fin-rim"):
        continue
    mask=np.asarray(Image.open(RUN/"geometry-input"/region["mask_path"]).convert("L"))>127
    distance=ndimage.distance_transform_edt(mask)
    bands=[]
    for low,high in ((0,1.5),(1.5,3),(3,5),(5,8),(8,16),(16,1000)):
        sample=(distance>low)&(distance<=high)
        yy,xx=np.nonzero(sample)
        pred=evaluate_field(paints[name],np.column_stack((xx+.5,yy+.5)))
        residual=rgb[sample]-pred
        bands.append({"distance_px":[low,high],"pixels":len(xx),
                      "median_source_minus_analytic_rgb":np.median(residual,axis=0).tolist(),
                      "mean_source_minus_analytic_rgb":residual.mean(axis=0).tolist()})
    records.append({"id":name,"bands":bands})
(OUT/"material-rim-analysis.json").write_text(json.dumps(records,indent=2),encoding="utf-8")
for r in records:
    print(r["id"],[(b["distance_px"],np.round(b["median_source_minus_analytic_rgb"],2).tolist()) for b in r["bands"]],flush=True)
