# 男管理员 · full 生产提示词

Round / Profile：`endministrator-male-001` / `full`。

主体（Subject）：《明日方舟：终末地》Endministrator（男管理员），依据已查看的官方 portrait 创作，不借用模式参考人物的发型、帽子或装饰。

主体证据：已实际查看 `endministrator-2.png`，来源为 [官方角色图](https://web.hycdn.cn/endfield/official-v4/_next/static/media/endministrator2.5ccb44a8.png)；完整来源与 SHA-256 见本 round 的 `brief.json`。灰绿色短层次尖发与侧分刘海，黑色角状遮眼装置有黄色镶线，原图无帽。装备和衣领不进入本次大脸裁切。

风格参考（Style reference）：已查看用户 r1/r2；取大块流畅刘海、极近景、左下边缘切过脸部、两个完整可见且内部纯色的 capsule eyes，屏幕左眼较高。排除原图黑底、水印、文字以及角色身份。

本 profile 生效规则：保留来源的深灰绿头发和浅暖肤色；仅一档 broad shadow、两个宽高光；眼 ratio=2.8:1、width=30、height=84；head rotation=17°。核心身份为短层次尖发、黑黄角状装置与小块侧部黄线硬件，不追加身体装备。

Aikon 覆盖：512 × 512 的真实矢量 SVG，`background: null`。不画背景、棋盘格、水印、文字、logo、嘴、鼻、手和身体。双眼局部中心为 `(117,356)` 与 `(278,356)`，同 y、同尺寸、同方向；整头与附件共同旋转。脸从左侧和底部自然裁切，右上保留连通透明 negative space。

Agent 设计调整：原图面罩遮住眼睛，与固定胶囊眼优先级冲突；将面罩缩短并移到双眼上方的 forehead 区域，保留 angular black plates 与黄线作为身份线索。该调整源于已有 style conflict rules，不是新增用户选择。禁止在黑面罩上叠黑眼后声称两眼清晰。

保留（Preserve）：已确认性别版本、短尖发轮廓与侧分方向、灰绿发色系、黑黄识别部件、无帽、完整双眼、透明画布。

变化（Change）：从官方写实立绘转换为无嘴圆脸 bot；保留原色关系与有限硬件分层，仍抑制纹理细节。所有具体曲线和坐标是本轮 Agent 设计，不冒充原图测量。

验收：运行 SVG structural check；随后由主线程实际渲染，核对透明 alpha、深浅底、24/48/128 px、两眼无遮挡、脸部左下裁切、右上透明与身份轮廓。结构通过不等于 visual passed 或 user accepted；本目录初始状态为 visual unverified。

提示词来源：本指令按 Aikon runtime profiles 整合 [Grokbot Icon Studio](https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans) 中 full 源规则的中文研究译文，并依本用户要求改为透明 SVG、强 close-up、双 profile 与可追溯验证。原作者 X @multi_serio_ai（APG）；源提示词许可 CC BY-NC 4.0，参见[来源许可](https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans/license)。此许可不自动授予官方角色图再分发权。

## r002 局部修正

依据 Agent 对 r001 的实际预览反馈，仅将后脑外轮廓改为少数有方向的曲线发束，并将黑黄 forehead 装置及其 panels 向上移动 64 个局部单位。保留 face、eyes、所有颜色、head transform 及其他图层。此为 Agent review 修正，不新增用户选择；新版本仍待实际渲染。
