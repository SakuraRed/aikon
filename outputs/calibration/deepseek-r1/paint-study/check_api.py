"""Small independent analytic controls; no implementation-mirroring assertions."""
import json
from pathlib import Path
import numpy as np
from fit_fields import fit_field,evaluate_field,svg_paint

yy,xx=np.mgrid[:120,:140]
mask=(xx>12)&(xx<128)&(yy>12)&(yy<108)
xy=np.column_stack((xx[mask]+.5,yy[mask]+.5))
records=[]
for name,image in (
    ("constant",np.broadcast_to([44,77,132],(120,140,3)).astype(float)),
    ("linear_y",np.stack((35+(yy+.5)*.3,65+(yy+.5)*.15,140+(yy+.5)*.2),axis=2)),
    ("radial_center",np.stack((230-np.hypot(xx+.5-70,yy+.5-60)*.12,
                               225-np.hypot(xx+.5-70,yy+.5-60)*.21,
                               238-np.hypot(xx+.5-70,yy+.5-60)*.17),axis=2))):
    field,stats,use=fit_field(image,mask)
    assert stats["rgb_rmse_255"]<.45,(name,stats)
    definition,fill=svg_paint(field,name)
    assert all(token not in definition for token in ("<image","filter=","<pattern"))
    assert field["kind"]=="solid" or len(field["stops"])<=5
    records.append({"control":name,"chosen":field["kind"],"rgb_rmse":stats["rgb_rmse_255"],
                    "predicate":"known independent smooth field recovered <0.45 RGB levels; no raster/filter/pattern"})
Path(__file__).with_name("api-checks.json").write_text(json.dumps(records,indent=2),encoding="utf-8")
print(json.dumps(records,indent=2))
