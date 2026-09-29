"""Write production prompts BEFORE running sourcecode.py. No network required."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
REFS = {
    "F02": "ref/subjects/endministrator/research-female/female-official-full.png",
    "F09": "ref/subjects/endministrator/research-male/official-profile-b-female-comparison.jpg",
    "F05": "ref/subjects/endministrator/research-female/official-gallery-0212.jpg",
    "F06": "ref/subjects/endministrator/research-male/official-campaign-unmasked-duo.jpg",
    "F04": "ref/subjects/endministrator/research-female/suppressor-official-front.jpg",
    "style-r1": "ref/user-mode/r1-working.png",
    "style-r2": "ref/user-mode/r2.png",
}
COMMON = """# 女管理员实际绘图合同 — round-003

任务模式：新主体风格迁移。reference_basis=official illustration。
真实用户决定：female_mask=both，原生回答“两种都画”；并非用户视觉接受。
不读取、不复制被拒绝的旧管理员 SVG；用语义贝塞尔面重新创作。

实际看图记录：F02/F09 为女性正常佩戴形态与服装；F05 只取左下黑发女性，
F06 只取右侧女性。两张无面具官方插画均见青蓝/青绿色眼部且未见眼镜；
仅据此作暗青灰 capsule 材料映射，不断言当前3D精确眼色。
F04 只补装置分件，不把商品正视摆放投影替代正常佩戴。
r1 仅迁移自然解析色场、胶囊与柔和仰头投影，不移植其蓝发、褶边或蝴蝶结。
r2 仅支持 full 具有真实颈领与服饰范围，不取其帽子。

女性身份：宽窄不同的额发与包颊短 bob、方向不同的外翘末端、很小的冠顶翘束；
画面左上鬓侧保留异长金属长条、近同向短片与横向扣片的叠接、切角及暗厚度。
不把发卡画成任意平面 X，不把女性几何用作男性默认。

画布1280×1280，透明、无水印、真实可编辑SVG。自然仰头由宽的下半脸、
上方收束发际及投影中的额发—眼线—下颌关系共同表达，roll约13度只负责
画面内倾斜，不能宣称测得唯一3D pitch。
脸为独立不对称轮廓，奶油暖白色宽缓径向场；不画鼻嘴、眉毛或写实眼眶。
头发是不透明底材上的少量连续 linear/radial 场，宽受光沿大束弧度分布。
不使用grain、滤镜、pattern、碎片量化描摹、位图、独立尖三角高光或云斑。
硬件可以有真实硬质转面，头发不借用金属切面。边界抗锯齿与材质内部区分。

先保存本提示词，再绘制。保存源码、原SVG、1280/128/48/24真实渲染，
检查深浅底和透明。看图后在新revision先保存修改提示，再修正。
格式/几何通过不等于审美接受，不标99%，所有最终候选等待用户审计。
"""

for branch in ("masked", "unmasked"):
    for profile in ("short", "full"):
        out = ROOT / branch / profile / "revisions" / "r001"
        out.mkdir(parents=True, exist_ok=True)
        source = (REPO / f"skills/aikon/references/prompts/source-{profile}.zh-CN.md").read_text(encoding="utf-8")
        branch_text = (
            "正常佩戴 Originium Suppressor：覆盖双眼并向鼻梁区下探；中央硬质折面、两侧向上延伸片、浅灰边和黄色连接件相互连接。上缘受刘海遮挡，侧端连到鬓侧。禁止上移为额冠、普通墨镜、薄条、透视面具或画替代眼。对源两眼可见规则明确例外。"
            if branch == "masked" else
            "完全移除抑制器及其侧件，独立保留女性多片发卡。两眼同源等形、互相平行；使用近直侧壁与半圆端帽的真正 capsule，short比约2.8:1、full约2.7:1。色相依据F05/F06映射为暗青灰，允许微弱连续眼材渐变和细窄一体边缘，不加虹膜、白点、瞳孔或眼镜。"
        )
        profile_text = (
            "short：头部和脸部大幅进入画面，左侧和下方自然裁切；脸域下半宽阔、下巴延伸出画布，右上透明。主要宽额发、两侧短bob、异长外翘端及身份硬件可辨，完全不画身体与领子。"
            if profile == "short" else
            "full：独立重设计头部路径和取景，脸下缘收在画面约y1030附近，颈部、暗色内层、浅灰高领、橙色前连接、多层长环银扣、深外领浅内面与黄色肩领片在底部连续相接。加入后发与内领遮挡、不同宽度侧发；不是缩小short加任意领子。服装结构只来自F02/F09，图内不画手武器或海报元素。"
        )
        prompt = COMMON + f"\nEntity=endministrator-female / Branch={branch} / Profile={profile}\n\n" + branch_text + "\n\n" + profile_text + "\n\n## 完整源译文与许可（冲突按上述运行覆盖）\n\n" + source
        target = out / "prompt.zh-CN.md"
        if target.exists():
            raise SystemExit(f"Refuse overwrite: {target}")
        target.write_text(prompt, encoding="utf-8")

evidence = {
    "round": "round-003", "entity": "endministrator-female",
    "reference_basis": "official illustration", "user_mask_choice": "both",
    "decision_evidence": "docs/validation/2026-09-29-live-native-answers.json#female_mask",
    "sources": {k: {"path": v, "sha256": hashlib.sha256((REPO/v).read_bytes()).hexdigest(), "actually_viewed": True} for k,v in REFS.items()},
    "unproven": ["current game 3D exact colors", "hidden clip mechanics", "unique 3D pitch angle", "user acceptance", "99 percent similarity"],
    "source_license": "APG / @multi_serio_ai prompt translations: CC BY-NC 4.0; third-party reference images private research only",
}
(ROOT / "reference-evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print("Four r001 production prompts saved before drawing.")
