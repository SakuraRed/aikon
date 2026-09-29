from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
source = Image.open(ROOT / 'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png').convert('RGBA')
candidate = Image.open(ROOT / 'outputs/calibration/deepseek-r1/revisions/v004/comparison/candidate-render.png').convert('RGBA')
boxes = {'right-crease': (730, 690, 895, 1115), 'center-crease': (620,470,725,770), 'fin-rim': (960,960,1270,1160), 'main-boundary': (450,230,870,760)}
for name, box in boxes.items():
    scale = 2
    w, h = (box[2]-box[0])*scale, (box[3]-box[1])*scale
    board=Image.new('RGB',(w*2,h+32),'#151515')
    draw=ImageDraw.Draw(board)
    for i,(title,im) in enumerate([('Source',source),('v004',candidate)]):
        crop=im.crop(box).resize((w,h),Image.Resampling.NEAREST)
        board.paste(crop,(i*w,32),crop)
        draw.text((i*w+8,8),title,fill='white')
    board.save(HERE/f'{name}-before.png')
print('Saved four source/candidate ROI boards.')
