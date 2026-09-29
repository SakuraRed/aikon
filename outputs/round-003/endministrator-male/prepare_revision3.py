from pathlib import Path
import hashlib
import json

OUT=Path(__file__).resolve().parent
review={'status':'visually_reviewed_needs_local_revision','actually_viewed':['overview-r002.png','All four r002 preview-1280.png'],'improved':['All unmasked capsule ends now visibly clear.','No triangular paint inside tall crown tips.','Full garment structure clearly separates profile at same canvas.'],'remaining':['Full dark inner high collar still nearly covered by pale collar.','Mask lower silhouette still too VR-like / flat, root requested stronger nose drop and characteristic bent central ridge.','Right upper mask plate too hidden in the forehead wedge.'],'root_feedback':'Actual A-card inspection: preserve bent light ridge, central nose-bridge descent and two rising side plates; no hair highlight fragments.'}
(OUT/'visual-review-r002.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
for branch in ('masked','unmasked'):
 for profile in ('short','full'):
  base=OUT/branch/profile/'revisions'/'r002';target=OUT/branch/profile/'revisions'/'r003';target.mkdir(parents=True,exist_ok=True)
  sha=hashlib.sha256((base/f'{profile}.svg').read_bytes()).hexdigest()
  text=(base/'actual-prompt.md').read_text(encoding='utf-8')+f'\n\n## r003：主线程与本人实看后的有限修正\n基础r002 SHA-256：{sha}。原稿及全部实际文件保留。\n'
  if branch=='masked':text+='进一步对齐实际再次查看的A卡抑制器近景：中央下探鼻梁的分面和尖下缘增强，避免平底VR罩；中央顺硬面转折增加连续弯折脊线，灰白结构缘跟随该折面；将近侧上扬长片内移到实际额侧连接处，使其不被全部头发隐藏。黄连接仍附着在侧片下端，不复制织纹或独立游离高光。\n'
  if profile=='full':text+='下移灰白外立领及其前拉链/环扣组45单位，暗内高领仍从下颌后方实际连到外领，以获得足够可见深色领带区域；保留完整服饰来源及原本独立full布局。\n'
  if branch=='unmasked' and profile=='short':text+='此图不需本次可见修改；以原样对照保留同轮统一r003输出，明确零像素改变，不伪称新增质量改善。\n'
  text+='保持所有无面具capsule几何、材质和完整可见性，以及本轮所有头发路径；本次不再重画发顶。仍为候选，需端到端质量证据和用户审计。\n'
  (target/'actual-prompt.md').write_text(text,encoding='utf-8')
print('r003 prompts saved before changes')
