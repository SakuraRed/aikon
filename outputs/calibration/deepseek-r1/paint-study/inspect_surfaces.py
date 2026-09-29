from pathlib import Path
from PIL import Image,ImageDraw

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
source=Image.open(ROOT/"ref/user-mode/r1.png").convert("RGBA")
old=Image.open(OUT/"material-fit-v2/analytic-material-preview.png").convert("RGBA")
new=Image.open(OUT/"material-fit-v2-petals/analytic-material-preview.png").convert("RGBA")
source.crop((960,970,1265,1160)).resize((915,570)).save(OUT/"fin-rim-source-zoom.png")
bounds=(180,110,420,245)
board=Image.new("RGB",(1440,330),"#181a20")
draw=ImageDraw.Draw(board)
for i,(im,label) in enumerate(((source,"Source"),(old,"0.35 simpler-model tolerance"),(new,"0.05 simpler-model tolerance"))):
    crop=im.crop(bounds).resize((480,270),Image.Resampling.LANCZOS)
    bg=Image.new("RGBA",crop.size,"#101010");bg.alpha_composite(crop)
    board.paste(bg.convert("RGB"),(480*i,50));draw.text((480*i+15,15),label,fill="white")
board.save(OUT/"white-petal-ablation.png")
