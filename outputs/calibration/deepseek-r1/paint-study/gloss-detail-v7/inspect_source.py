"""Read-only source inspection; writes crops solely into this study directory."""
from pathlib import Path
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
REV = ROOT / 'outputs/calibration/deepseek-r1/revisions/v006'
REF = ROOT / 'ref/subjects/deepseek/cetus-desktop'
source = Image.open(REF / 'r1-clean-source-1280.png').convert('RGBA')
native = Image.open(REF / 'CETUS-ico.original.png').convert('RGBA')
before = Image.open(REV / 'comparison/candidate-render.png').convert('RGBA')
geometry = json.loads((REV / 'geometry.json').read_text(encoding='utf-8-sig'))
fields = json.loads((REV / 'paint-fields.json').read_text(encoding='utf-8-sig'))
selected = ['eye-left','eye-right','whale-side-fin-rim','whale-fin-rim-left-fold']
selected += [r['id'] for r in geometry['regions'] if r['id'].startswith('frill-white')]
(HERE / 'selected-input.json').write_text(json.dumps({'regions':[r for r in geometry['regions'] if r['id'] in selected], 'fields':[r for r in fields['palette'] if r['id'] in selected]},indent=2),encoding='utf-8')
boxes = {'eye-left':(135,650,290,900), 'eye-right':(565,810,720,1045), 'fin':(978,960,1264,1155), 'frill-upper':(190,120,495,250), 'frill-right':(747,268,923,457)}
for name,box in boxes.items():
    width,height = box[2]-box[0],box[3]-box[1]
    board = Image.new('RGB',(width*3*2,height*2+26),(24,25,27))
    draw = ImageDraw.Draw(board)
    for index,(label,pic) in enumerate([('source native',native.crop(tuple(round(v*3.2) for v in box)).resize((width*2,height*2),Image.Resampling.LANCZOS)),('source 1280',source.crop(box).resize((width*2,height*2),Image.Resampling.NEAREST)),('v006',before.crop(box).resize((width*2,height*2),Image.Resampling.NEAREST))]):
        bg=Image.new('RGBA',pic.size,(15,15,15,255)); bg.alpha_composite(pic)
        board.paste(bg.convert('RGB'),(index*width*2,26));draw.text((index*width*2+5,6),label,fill='white')
    board.save(HERE / (name + '-source-before.png'))
    native.crop(tuple(round(v*3.2) for v in box)).save(HERE / (name+'-native-crop.png'))
print(json.dumps({'source_size':source.size,'native_size':native.size,'regions':[{r['id']:r['d']} for r in geometry['regions'] if r['id'] in selected]},indent=2))
