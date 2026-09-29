from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
GEO=OUT.parent/"geometry-study"
source=Image.open(ROOT/"ref/user-mode/r1.png").convert("RGB")
report=json.loads((OUT/"material-fit-v1/fields.json").read_text())
geometry=json.loads((GEO/"geometry.json").read_text())
regions={r["id"]:r for r in geometry["regions"]}
preview=Image.open(OUT/"material-fit-v1/analytic-material-preview.png").convert("RGBA")
chosen=sorted(report["palette"],key=lambda r:r["stats"]["rgb_rmse_255"],reverse=True)[:9]
board=Image.new("RGB",(1600,len(chosen)*310),"#191b22")
draw=ImageDraw.Draw(board)
for i,item in enumerate(chosen):
    mask=Image.open(GEO/regions[item["id"]]["mask_path"]).convert("L")
    bounds=mask.getbbox();left,top,right,bottom=bounds
    bounds=(max(0,left-8),max(0,top-8),min(1280,right+8),min(1280,bottom+8))
    src=source.crop(bounds); pred=preview.crop(bounds); m=mask.crop(bounds)
    tint=src.convert("RGBA")
    red=Image.new("RGBA",tint.size,(255,35,70,0));red.putalpha(m.point(lambda a:a//3))
    tint=Image.alpha_composite(tint,red)
    for j,im in enumerate((src,tint,pred)):
        im.thumbnail((500,260),Image.Resampling.LANCZOS)
        bg=Image.new("RGBA",(500,260),"#101010");bg.alpha_composite(im.convert("RGBA"),((500-im.width)//2,(260-im.height)//2))
        board.paste(bg.convert("RGB"),(j*525+15,i*310+40))
    draw.text((15,i*310+10),f'{item["id"]}  RGB RMSE={item["stats"]["rgb_rmse_255"]:.3f} /255; source / source + mask / current analytic paint',fill="white")
board.save(OUT/"high-residual-regions.png")
