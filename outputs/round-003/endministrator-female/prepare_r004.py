"""Write parent-directed, visually grounded r004 prompts before correction."""
from pathlib import Path
import hashlib
root=Path(__file__).resolve().parent
for branch in ('unmasked','masked'):
    for profile in ('short','full'):
        parent='r002' if profile=='short' else 'r003'
        base=root/branch/profile/'revisions'/parent;out=base.parent/'r004'
        out.mkdir(exist_ok=True)
        text=f'''# r004：主Agent实际看图反馈对应修改

Base={parent} / {branch} / {profile}
Base SHA-256={hashlib.sha256((base/'icon.svg').read_bytes()).hexdigest()}

主Agent已看overview-r002并对照官方B卡：
1. 顶冠与左上扫额束的材料不连续，读成闭合亮片，缺乏真实发流依据。
2. 横扣过粗，叠接金属发卡读成十字格栅；需按原图细金属异长条和小横扣收细。

限定修改：顶冠与扫额主束使用同一个宽连续解析色场，使根部亮度不在
人工分组边界跳变。保留实际发际轮廓，不新画高光片或涂白整片头发。
发卡保持异长长条、短条、横扣、叠接及厚度，横扣厚度从17收至9，缩短
少量横向外伸；长条暗面、窄亮边在其自身局部坐标声明金属场，避免将
头部坐标渐变误用于附件局部坐标而变成平白符号。
面罩中央浅棱线/侧板黄色连接保留，正常遮双眼；不扩大到额冠。

保留：脸/眼/全部头发路径、masked和unmasked互斥性、独立short/full取景、
full官方领口/环扣/肩片、透明SVG。只在新的revision修改，不覆盖旧版本。
再跑实际渲染与像素检查；失败继续明示，不调低3px局部簇阈值。

## 上一版完整实际提示

'''+(base/'prompt.zh-CN.md').read_text(encoding='utf-8')
        target=out/'prompt.zh-CN.md'
        if target.exists():raise SystemExit('refuse overwrite')
        target.write_text(text,encoding='utf-8')
print('Four r004 prompts saved')
