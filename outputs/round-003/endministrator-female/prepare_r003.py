"""Save two full-only material correction prompts before editing."""
from pathlib import Path
import hashlib
root=Path(__file__).resolve().parent
for branch in ('unmasked','masked'):
    base=root/branch/'full'/'revisions'/'r002';out=base.parent/'r003'
    out.mkdir(exist_ok=True)
    prompt=f'''# r003 full-only 实看修订

Base=r002 / {branch} / full.
SVG SHA-256={hashlib.sha256((base/'icon.svg').read_bytes()).hexdigest()}.

已实看本图1280及总览。右鬓上层与包颊束重叠处出现三角状较亮色面，
这是两束采用不同全局色场的拼接，不是需要保留的独立高光。
只把 full-right-temple-lock 的 material 改为相邻包颊束同一个连续场，
所有路径、附件、脸、眼和服装几何保留，消除额外亮片观感。
另外领扣复用了为上方发卡建立的user-space金属场，坐标远超支持域而
退成近纯色；为 ring-* 金属长环声明自己的局部线性色场，保持孔洞、
相叠与接点，避免把平金属称作已完成自然光泽。
不重画short；其候选仍为r002。无用户验收或99%声明。

## 上一版实际合同

'''+(base/'prompt.zh-CN.md').read_text(encoding='utf-8')
    dest=out/'prompt.zh-CN.md'
    if dest.exists():raise SystemExit('refuse overwrite')
    dest.write_text(prompt,encoding='utf-8')
print('Two full-only r003 prompts saved')
