"""Measure r1 eye interior and distance-to-boundary color, not an eye redraw."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from fit_fields import fit_field

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
rgb=np.asarray(Image.open(ROOT/"ref/user-mode/r1.png").convert("RGB"))
records=[]
for name in ("left","right"):
    mask=np.asarray(Image.open(ROOT/f"docs/validation/capsules-v3/r1/{name}/mask.png").convert("L"))>127
    distance=ndimage.distance_transform_edt(mask)
    bins=[]
    for low,high in ((0,1.5),(1.5,3),(3,5),(5,8),(8,16),(16,100)):
        region=(distance>low)&(distance<=high)
        vals=rgb[region]
        bins.append({"distance_px":[low,high],"pixels":len(vals),"median_rgb":np.median(vals,axis=0).tolist(),
                     "p10_rgb":np.quantile(vals,.1,axis=0).tolist(),"p90_rgb":np.quantile(vals,.9,axis=0).tolist()})
    field,stats,_=fit_field(rgb,mask,edge_pixels=5)
    records.append({"eye":name,"core_field":field,"core_stats":stats,"boundary_bands":bins})
    print(name,field["kind"],stats["rgb_rmse_255"],flush=True)
(OUT/"eye-paint-analysis.json").write_text(json.dumps(records,indent=2),encoding="utf-8")
