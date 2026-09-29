from pathlib import Path
import hashlib
OUT=Path(__file__).resolve().parent
for branch in ('masked','unmasked'):
 for profile in ('short','full'):
  base=OUT/branch/profile/'revisions'/'r003';target=OUT/branch/profile/'revisions'/'r004';target.mkdir(parents=True,exist_ok=True)
  sha=hashlib.sha256((base/f'{profile}.svg').read_bytes()).hexdigest()
  text=(base/'actual-prompt.md').read_text(encoding='utf-8')+f'\n\n## r004：面具上缘同一轮廓采样\n基础r003原始文件SHA-256：{sha}。\n'
  if branch=='masked':text+='实际edge诊断定位面具上缘局部9/8坏像素簇：脸、窄黑边、浅色金属边距离不足且多次覆盖采样。只修该结构的渲染支持：中央基材、折面及浅缘统一由原base外轮廓clip一次，基材与浅缘向裁切外延伸；保留原整体边界、鼻梁下降、侧片、脊线、黄连接和头发。浅色边与真实外边一致，消除无来源的极窄双重黑带；不调阈值、不模糊、不改PNG。\n'
  else:text+='本次不修改无面具SVG，明确保持r003所有像素，统一r004集合便于交接；不声称该图新增改善。\n'
  text+='保留全部既有revision。重新渲染并按原冻结256px edge门槛检查；若仍失败如实保留。\n'
  (target/'actual-prompt.md').write_text(text,encoding='utf-8')
print('r004 prompts saved before clip repair')
