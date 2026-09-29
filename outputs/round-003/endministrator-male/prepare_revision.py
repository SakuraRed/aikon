from pathlib import Path
import hashlib
import json

OUT=Path(__file__).resolve().parent
observed={
 'status':'visually_reviewed_not_accepted',
 'actually_viewed':['overview-r001.png (including actual 128/48/24 previews)','unmasked/full/revisions/r001/preview-1280.png','masked/short/revisions/r001/preview-1280.png'],
 'failures':['Full unmasked eyes are occluded at their upper ends; short right eye partly occluded.','Crown has three overly tall spikes with triangular separate paint; too crown-like.','Right outer hair groups are too regular.','Full face covers almost all dark inner collar; neck connection insufficient.','Pale metal rings lack separation from the pale chest field.'],
 'preserve':['Male-only asymmetrical swept-short hairstyle; no female clip or bob.','Opaque mask remains over both eyes; no forehead relocation or fake eyes.','Transparent vector authoring and smooth analytic paints.','Independent short/full geometry and actual garment topology.'],
 'not_claimed':['99% visual fidelity','User acceptance','Complete paint/edge CI pass']
}
(OUT/'visual-review-r001.json').write_text(json.dumps(observed,indent=2)+'\n',encoding='utf-8')
for branch in ('masked','unmasked'):
 for profile in ('short','full'):
  base=OUT/branch/profile/'revisions'/'r001'
  target=OUT/branch/profile/'revisions'/'r002'
  target.mkdir(parents=True,exist_ok=True)
  sha=hashlib.sha256((base/f'{profile}.svg').read_bytes()).hexdigest()
  text=(base/'actual-prompt.md').read_text(encoding='utf-8')
  text+='\n\n## r002：基于实际可见缺陷的局部修正\n'
  text+=f'基础版本：r001，SVG SHA-256 {sha}。r001源码、prompt、SVG和预览均已保留。\n'
  text+='保留实体、分支、透明背景、同源眼对、装置位置及连续上色。将过高三叉冠改为不等长低幅发顶束，取消发顶的内部尖三角亮面；打散右侧等距外翘轮廓。主扫发及下降鬓束保持身份。\n'
  if branch=='unmasked':text+='修短右刘海向内尖端；full眼对一起下移以完整露出capsule圆端，保持同形和平行，不用遮挡掩盖眼形。short眼对位置保持，清除右端发丝遮眼。\n'
  if profile=='full':text+='full下颌上移但保留宽圆下脸，并重新定义暗内高领可见支撑和灰白外领边界，使头—颈—领实际相接；金属长环增加低对比暗边，保留孔洞和连结。不要更改成缩放short。\n'
  text+='扩大连续发束色场可辨范围而不新增局部白亮点、云纹或贴片。再次实际渲染后检查全部四图大图、小图和深浅底；保留尚未解决的限制。\n'
  (target/'actual-prompt.md').write_text(text,encoding='utf-8')
print('r001 preserved; four r002 actual prompts saved before revision')
