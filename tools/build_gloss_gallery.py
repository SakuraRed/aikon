"""Build a local review page and contact sheet from actual delivered PNGs."""
from pathlib import Path
import hashlib
import html
import json

ROOT = Path(__file__).resolve().parents[1]
SUBJECTS = (
    ("deepseek", "DeepSeek", "蓝发、白色褶边与侧蝴蝶结，以 r1 为主体与模式。"),
    ("endministrator-female", "女管理员", "齐肩层次短发、银色交错发夹；眼罩上移以露出双眼。"),
    ("endministrator-male", "男管理员", "不对称短发与翘束；眼罩上移，保留黑灰与黄色线索。"),
)


def main():
    from PIL import Image, ImageDraw, ImageFont
    output = ROOT / "outputs/fixtures/gloss-v2-review"
    output.mkdir(parents=True, exist_ok=True)
    fonts = [Path("C:/Windows/Fonts/msyh.ttc"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    font_path = next((path for path in fonts if path.is_file()), None)
    font = ImageFont.truetype(str(font_path), 26) if font_path else ImageFont.load_default(size=26)
    small = ImageFont.truetype(str(font_path), 19) if font_path else ImageFont.load_default(size=19)
    board = Image.new("RGB", (1040, 1704), "#eeeae4")
    draw = ImageDraw.Draw(board)
    draw.text((28, 18), "Aikon · natural-gloss-v2 · 待审计候选", font=font, fill="#20232b")
    draw.text((28, 58), "左：精简版    右：完整版    /    同一主体，真实 SVG 渲染", font=small, fill="#555b65")
    sections, records = [], []
    for row, (slug, title, detail) in enumerate(SUBJECTS):
        directory = ROOT / "outputs/fixtures" / slug / "round-002"
        top = 98 + row * 530
        draw.text((28, top), title, font=font, fill="#20232b")
        cards = []
        for col, (profile, label) in enumerate((("short", "精简版"), ("full", "完整版"))):
            source = directory / (profile + "-1024.png")
            with Image.open(source) as image:
                icon = image.convert("RGBA").resize((470, 470), Image.Resampling.LANCZOS)
            panel = Image.new("RGBA", icon.size, "#20232b")
            panel.alpha_composite(icon)
            board.paste(panel.convert("RGB"), (28 + col * 510, top + 43))
            href = "../" + slug + "/round-002/" + profile
            cards.append('<article><h3>' + label + '</h3><div class="art"><img alt="' + html.escape(title + " " + label) + '" src="' + href + '.svg"></div><p><a href="' + href + '.svg">SVG</a><a href="' + href + '-1024.png">1024 PNG</a><a href="' + href + '.prompt.zh-CN.md">实际提示词</a></p></article>')
            records.append({"subject": slug, "profile": profile, "svg": (directory / (profile + ".svg")).relative_to(ROOT).as_posix(), "svg_sha256": hashlib.sha256((directory / (profile + ".svg")).read_bytes()).hexdigest(), "preview_sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
        sections.append('<section><h2>' + title + '</h2><p class="detail">' + detail + '</p><div class="pair">' + ''.join(cards) + '</div></section>')
    board.save(output / "contact-sheet.png")
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Aikon · 六图审阅</title>
<style>
:root{color-scheme:light;--paper:#eeeae4;--ink:#242832;--stage:#20232b}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1200px;padding:30px;margin:auto}h1{font-size:28px;margin:0}h2{font-size:23px;margin:32px 0 0}h3{font-size:16px;font-weight:500;margin:8px 0}.detail{color:#616672;margin:2px 0 14px}.controls{display:flex;gap:12px;flex-wrap:wrap;margin:22px 0;align-items:center}button,select{font:inherit;border:1px solid #bbc0c8;background:#faf8f5;border-radius:5px;padding:5px 13px;cursor:pointer}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}.art{background:var(--stage);aspect-ratio:1;display:grid;place-items:center;overflow:hidden}.art img{width:100%;height:100%;object-fit:contain}body.checker .art{background-color:#fff;background-image:conic-gradient(#d5d8df 25%,transparent 0 50%,#d5d8df 0 75%,transparent 0);background-size:24px 24px}article p{display:flex;gap:18px;margin:7px 0}a{color:#344d8e;text-underline-offset:3px}.references{display:flex;gap:20px;flex-wrap:wrap;margin-top:25px}.references img{width:180px;height:180px;object-fit:contain;background:#20232b}.note{color:#616672}footer{margin:30px 0} @media(max-width:640px){main{padding:16px}.pair{gap:12px}article p{font-size:12px;gap:9px;flex-wrap:wrap}}
</style><main><h1>六图审阅 · natural-gloss-v2</h1><p class="note">左列为精简版，右列为完整版。所有图片均由对应 SVG 实际渲染，当前为待审计候选。</p>
<div class="controls"><span>展示底色</span><button data-bg="#20232b">深色</button><button data-bg="#fbf8f2">浅色</button><button data-bg="checker">透明棋盘</button><label>头像尺寸 <select id="size"><option value="100%">随窗口</option><option value="128px">128 px</option><option value="48px">48 px</option><option value="24px">24 px</option></select></label></div>
''' + ''.join(sections) + '''
<details><summary>查看本轮参考</summary><div class="references"><figure><img src="../../../ref/user-mode/r1.png" alt="r1"><figcaption>r1：DeepSeek 身份与光泽模式</figcaption></figure><figure><img src="../../calibration/illustration/full-imagegen-v1.png" alt="完整版整体参考"><figcaption>完整版整体参考</figcaption></figure><figure><img src="../../../ref/subjects/endministrator/female.png" alt="女管理员官方参考"><figcaption>女管理员原形象</figcaption></figure><figure><img src="../../../ref/subjects/endministrator/male.png" alt="男管理员官方参考"><figcaption>男管理员原形象</figcaption></figure></div><p class="note">参考中的背景、水印与已指出的纹理缺陷不属于创作目标。管理员额饰上移属于本轮风格适配。</p></details><footer class="note">本轮主要检查：两版是否可区分、光泽是否自然、主体是否可辨、眼缘与发束是否清楚。机器检查没有替你作审美决定。</footer></main>
<script>document.querySelectorAll('[data-bg]').forEach(b=>b.onclick=()=>{document.body.classList.toggle('checker',b.dataset.bg==='checker');if(b.dataset.bg!=='checker')document.documentElement.style.setProperty('--stage',b.dataset.bg)});document.querySelector('#size').onchange=e=>document.querySelectorAll('.art img').forEach(img=>{img.style.width=e.target.value;img.style.height=e.target.value});</script></html>'''
    (output / "index.html").write_text(page, encoding="utf-8", newline="\n")
    (output / "manifest.json").write_text(json.dumps({"schema": "aikon.review-gallery.v1", "records": records, "user_acceptance": "pending"}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gallery": str(output / "index.html"), "contact_sheet": str(output / "contact-sheet.png"), "artworks": len(records)}))


if __name__ == "__main__":
    main()
