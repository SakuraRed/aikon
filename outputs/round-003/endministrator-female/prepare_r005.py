"""Freeze bounded edge-repair prompts before modifying r004 artwork."""
from pathlib import Path
import hashlib
root=Path(__file__).resolve().parent
for branch,profile in (('unmasked','full'),('masked','short'),('masked','full')):
    base=root/branch/profile/'revisions'/'r004';out=base.parent/'r005'
    out.mkdir(exist_ok=True)
    prompt=f'''# r005 有界边缘修复：共享裁切与不透明材料支撑

Base r004 / {branch} / {profile}
SVG SHA-256: {hashlib.sha256((base/'icon.svg').read_bytes()).hexdigest()}

实际诊断：r004在256px native 与同SVG4×精确渲染 premultiplied sRGB BOX
比较中，full右领翼簇6px，masked鼻尖簇11/17px，均超过冻结3px上限。
已实看三个失败局部，怀疑贴边转面逐层抗锯齿混入下方皮肤/衬里颜色。

第一次限定实现尝试：
- masked：把现有硬件可见轮廓的全部直线多边形保持原顶点，统一同向
  nonzero子路径合为一次采样的clip轮廓；组内铺足够大的不透明同材质底，
  所有原来的分面/窄金属棱边/黄连接件路径、顺序和投影保持。
- full：右外领的真实主轮廓仅采样一次，组内同材质不透明支撑，再绘原
  外领与折面路径；白内衬、黄片、头发及其他服饰不变。
这是对现有SVG结构的可复现变换，不读取像素追踪、master角色或新参考。
画布持续透明；支撑只在已有主体clip内，禁止把背景或预览底填进SVG。

保持全部原semantic path的d/transform属性、颜色场、胶囊、姿态、衣领
结构、正常面罩位置与全画布alpha；新clip只限制原形状并不提高阈值。
渲染1280/128/48/24，保存前后同位置native/4xBOX局部、原hash/新hash与
边缘质量结果。若首次无改善，最多另一次明确根因实现，之后带限制返回。
unmasked short原先通过，继续用r004，不修改。

## 原实际绘图与修订合同

'''+(base/'prompt.zh-CN.md').read_text(encoding='utf-8')
    target=out/'prompt.zh-CN.md'
    if target.exists():raise SystemExit('refuse overwrite')
    target.write_text(prompt,encoding='utf-8')
print('Three r005 prompts saved before repair')
