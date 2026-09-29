"""Arrange actual cached SVG renders for human review; no artwork changes."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont

root=Path(__file__).resolve().parent
font_path=Path('C:/Windows/Fonts/msyh.ttc')
font=ImageFont.truetype(str(font_path),18) if font_path.exists() else ImageFont.load_default()
small=ImageFont.truetype(str(font_path),14) if font_path.exists() else ImageFont.load_default()
items=[('DeepSeek',root/'deepseek','deepseek'),('Female / unmasked',root/'endministrator-female/unmasked','female'),('Female / masked',root/'endministrator-female/masked','female'),('Male / unmasked',root/'endministrator-male/unmasked','male'),('Male / masked',root/'endministrator-male/masked','male')]
tile=320;gap=16;top=74;row_h=378
board=Image.new('RGB',(gap+len(items)*(tile+gap),top+2*row_h),'#e8edf3')
draw=ImageDraw.Draw(board)
draw.text((16,12),'Aikon / round-003 / transparent SVG candidates',font=font,fill='#182638')
draw.text((16,40),'Top: short     Bottom: full     Preview mattes are not SVG backgrounds. All candidates await review.',font=small,fill='#4a596a')
records=[]
for column,(label,path,kind) in enumerate(items):
    for row,profile in enumerate(('short','full')):
        if kind=='deepseek':png=path/(profile+'-1280.png')
        elif kind=='female':png=path/(profile+'-preview.png')
        else:png=path/(profile+'.png')
        svg=path/(profile+'.svg');image=Image.open(png).convert('RGBA').resize((tile,tile),Image.Resampling.LANCZOS)
        bg=Image.new('RGBA',(tile,tile),'#fafafa');grid=ImageDraw.Draw(bg)
        for y in range(0,tile,16):
            for x in range(0,tile,16):
                if (x//16+y//16)%2:grid.rectangle((x,y,x+15,y+15),fill='#e5e9ef')
        bg.alpha_composite(image)
        x=gap+column*(tile+gap);y=top+row*row_h
        draw.text((x,y),label,font=small,fill='#253349')
        draw.text((x,y+22),profile,font=small,fill='#526279')
        board.paste(bg.convert('RGB'),(x,y+46))
        records.append({'svg':svg.relative_to(root).as_posix(),'svg_sha256':hashlib.sha256(svg.read_bytes()).hexdigest(),'preview':png.relative_to(root).as_posix(),'preview_sha256':hashlib.sha256(png.read_bytes()).hexdigest()})
board.save(root/'review-board.png')
(root/'review-board-inputs.json').write_text(json.dumps({'records':records,'meaning':'Presentation of actual cached renders; no final SVG background added.'},indent=2)+'\n',encoding='utf-8')
