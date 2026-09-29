"""Record actual r001 visual findings before the bounded r002 correction."""
from pathlib import Path
import hashlib

root=Path(__file__).resolve().parent
for branch in ('unmasked','masked'):
    for profile in ('short','full'):
        base=root/branch/profile/'revisions'/'r001'
        out=base.parent/'r002'
        out.mkdir(parents=True,exist_ok=True)
        sha=hashlib.sha256((base/'icon.svg').read_bytes()).hexdigest()
        text=f'''# 实际看图后的 r002 修改提示

Base: r001 / {branch} / {profile}
Base SVG SHA-256: {sha}

已实际查看 overview-r001 及 full 无面具、short 面具的1280原生渲染。
可见问题：额发接触阴影是横跨额头的厚桃棕色带，与真实发际不贴合；
大块上发区域受光过少、近似单色；发卡正面偏平白。full的环扣层级偏单一。

目标修改：
1. 移除该过厚且脱离实际发际的额头影带，改由脸部已有宽缓色场承接，
   不用另一条装饰带替代；中央/侧发的真实遮挡仍由形状顺序表达。
2. 仅给大块扫额与前发场建立连续径向宽光域，亮度受限于灰黑材质，
   不添加尖三角、点状白光、grain或细碎分片；侧发轮廓和主色归属保持。
3. 金属发卡保留异长多片几何，正面增暗中心和窄亮边表达原图可见厚度。
4. full在现有领扣下增加可辨且相连的第二长环层，保留真实孔洞；领口、
   橙件和黄色肩片来源不变。short无衣领。

Preserve：所有头脸轮廓、capsule尺寸与眼对、mask正常佩戴、bob身份、
short/full独立取景、透明画布、已获答both选择。不把格式或图形通过记为人类验收。
后续须重新渲染并实看1280/128/48/24、深浅底；保存源图和实际检查结果。

## 原始本图实际绘图合同

'''+(base/'prompt.zh-CN.md').read_text(encoding='utf-8')
        dest=out/'prompt.zh-CN.md'
        if dest.exists():raise SystemExit('No overwrite '+str(dest))
        dest.write_text(text,encoding='utf-8')
print('r002 prompts saved; r001 retained')
