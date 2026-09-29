"""Save the actual four instructions before any candidate SVG is authored."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
refs = {
    'M01': 'ref/subjects/endministrator/research-male/official-male-full.png',
    'M02': 'ref/subjects/endministrator/research-male/official-profile-a-male.jpg',
    'M03': 'ref/subjects/endministrator/research-male/official-campaign-unmasked-duo.jpg',
    'M04': 'ref/subjects/endministrator/research-female/official-gallery-0212.jpg',
    'M05': 'ref/subjects/endministrator/research-male/official-suppressor-display.jpg',
    'R1': 'ref/user-mode/r1-working.png',
    'R2': 'ref/user-mode/r2.png',
}
observations = {
    'M01': 'Male: asymmetric short black hair, swept frontal mass, short outward groups; mask over both eyes; dark inner high neck, grey pale standing collar, connected silver ring and yellow angled chest/shoulder plate.',
    'M02': 'A card: actual male; large sweep toward picture left, narrow falling group on picture right; short nape; overlapping dark mask central plate and rising side plates. No female hairclip.',
    'M03': 'Male on picture left only: cyan eye, swept short fringe, separate nape tufts; no glasses. Illustration, not gameplay frame.',
    'M04': 'Male at centre only: two cyan eyes under asymmetric swept fringe. Female at lower left and large grey-haired foreground character excluded.',
    'M05': 'Opaque angular central plate, lower nose-bridge drop, two tall side plates, pale edge/connectors and yellow fastening points. No woven pattern or typography copied.',
    'R1': 'Style only: continuous broad hair fields, cream face field, dark glossy capsules, lower-left cropped raised-head reading; DeepSeek identity elements excluded.',
    'R2': 'Full framing only: cheek-to-chin arc and visible neck/collar; no blue hair, crown or identity transfer.',
}
manifest = {
    'schema': 'aikon.reference-observations.v1',
    'entity': 'endministrator-male',
    'reference_basis': 'official illustration',
    'reference_inspection': 'All seven original files actually viewed using host view_image in this task before authoring.',
    'refs': {k: {'path': p, 'sha256': hashlib.sha256((ROOT/p).read_bytes()).hexdigest(), 'observation': observations[k]} for k,p in refs.items()},
    'decision': {'question_id': 'male_mask', 'actual_answer': '两种都画', 'expanded_branches': ['masked', 'unmasked'], 'evidence': 'docs/validation/2026-09-29-live-native-answers.json'},
    'unknowns': ['Exact current 3D eye sRGB', 'Hidden fastening engineering', 'Full back-of-head anatomy', 'User visual acceptance'],
    'source_notice': 'Official artworks are research references only; asset-specific redistribution permission unverified. APG source prompt translation retains CC BY-NC 4.0.'
}
(OUT/'references.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

common = '''
## 本次实际生产指令
任务模式：新主体风格迁移；不复制r1的身份，不复用旧管理员SVG或女性几何。
Entity：男性 Endministrator。reference_basis=official illustration。
真实决策：male_mask 原生回答“两种都画”；本文件只实例化指定分支，非用户验收。
先构建男性自身偏心冠顶、向画面左侧弧扫的大束刘海、画面右侧长短不一的鬓束、短后颈外翘；不用女bob或女发卡。
脸域依据刘海/太阳穴/侧颊和下颌关系独立绘制，仰头由额发压缩、眼线和宽阔下脸的投影关系表达，不以rotate替代pitch。
使用1280×1280透明画布、无水印、无描边框、无文字。产物为可寻址路径、局部gradient和clip的真实SVG；不得嵌位图、滤镜、噪声、量化碎片或采样trace。
上色：深灰黑材料底，宽幅中性偏冷柔光随发流连续变化；有真实交叠才产生暗分界，不贴尖三角高光；奶油面部宽缓暖色场；腮红弱粉色平面。
来源青蓝眼色在本次创作中映射为低饱和深青黑capsule；映射色不是官方RGB。
透明只属于画布，主体材料底不透明。阴影/光泽支持区属于真实材质，禁止游离亮片。
验收：静态向量检查、实际resvg渲染、1280/128/48/24观察、深浅底alpha与男女身份边界；结果保持候选待用户审计，不宣称99%。
'''
branch_text = {
 'masked': '本分支正常佩戴Originium Suppressor，完整遮住两眼，上沿被刘海部分压住。中央硬质分面下探鼻梁，下部成对面板、上伸侧片、浅色连接和黄色小接点互相连接。不得上移为额冠、半透明露眼、画替代眼或简化为黑横条。此用户选择明确覆盖源两眼全露默认。',
 'unmasked': '本分支完全移除抑制器及额侧延伸件。依据M04中央男性和M03左侧男性，显示两枚等形平行胶囊眼：近直侧边+圆端帽，源基线short约3:1、full约2.7:1；非ellipse，无虹膜、白点、睫毛或眼镜。浅弱暗青色场与连续细缘提供光泽。',
}
profile_text = {
 'short': '构图：超近景，从左下方探入，头/脸左缘和下缘裁切，右上留透明；顺时针约15°。仅头，不显示胸衣。以5–7个主要宽发流面表达男性偏扫短发、成组不等长外翻轮廓，不以等距尖齿形成锯齿圆环。下巴超出底边，但两枚可见眼或完整mask主体保持在画布内。',
 'full': '构图：在同一1280画布单独重构头—颈—上胸关系，脸下缘在约960处可读，短后颈束盖住暗内高领。按M01/M02建立灰白有前拉链立领、低于内领的银灰长环扣、两侧不同形外领翼、画面右侧黄色折角肩胸片及接点。头部冠顶/扫束/鬓侧也重新配置，可见分组更完整；不得仅对short整体缩放后补任意领子。避免对称证件照，整体偏左下，侧发可触边。头发保持自然宽光，不堆微小碎面。',
}
for branch in ('masked','unmasked'):
    for profile in ('short','full'):
        p = OUT/branch/profile/'revisions'/'r001'
        p.mkdir(parents=True,exist_ok=True)
        source = (ROOT/f'skills/aikon/references/prompts/source-{profile}.zh-CN.md').read_text(encoding='utf-8')
        text = f'# Round 003 / endministrator-male / {branch} / {profile} / r001\n\n'+source+common+'\n'+branch_text[branch]+'\n\n'+profile_text[profile]+'\n\n实看证据与哈希见本轮references.json。未通过项目必须保留，不因CI或导出成功而宣告视觉通过。\n'
        (p/'actual-prompt.md').write_text(text,encoding='utf-8')
print('saved four actual prompts and reference evidence; no candidate SVG written by this script')
