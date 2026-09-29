from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
from PIL import Image,ImageDraw,ImageFont

OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('male_author',OUT/'draw.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.compose_overview('r004')
manifest={'schema':'aikon.round-candidates.v1','round':'round-003','entity':'endministrator-male','current_revision':'r004','status':'structurally_checked_and_agent_visually_reviewed','reference_basis':'official illustration','user_decision':'male_mask = 两种都画','user_acceptance':'unassessed','files':[]}
board=Image.new('RGB',(1400,1420),'#161d27')
draw=ImageDraw.Draw(board)
for col,branch in enumerate(('unmasked','masked')):
 for row,profile in enumerate(('short','full')):
  p=OUT/branch/profile/'revisions'/'r004'
  for name,dest in [(f'{profile}.svg',f'{profile}.svg'),('preview-1280.png',f'{profile}.png'),('actual-prompt.md',f'{profile}.prompt.md')]:shutil.copy2(p/name,OUT/branch/dest)
  file=OUT/branch/f'{profile}.svg'
  manifest['files'].append({'branch':branch,'profile':profile,'svg':str(file.relative_to(OUT)).replace('\\','/'),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'revision_path':str(p.relative_to(OUT)).replace('\\','/'),'preview':f'{branch}/{profile}.png'})
  im=Image.open(p/'preview-dark.png').convert('RGB').resize((640,640),Image.Resampling.LANCZOS)
  x=30+col*695;y=40+row*700;board.paste(im,(x,y));draw.text((x,y-20),branch+' / '+profile,fill='white')
board.save(OUT/'dark-review-r004.png')
(OUT/'current.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copy2(OUT/'quality-summary-r004.json',OUT/'quality-summary.json')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
