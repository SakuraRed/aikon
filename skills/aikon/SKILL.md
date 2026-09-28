---
name: aikon
description: 从概念、名称、图片、wiki 或其他资料研究主体并交互创作 Grok bot style SVG 图标。每次新增参考的绘图请求生成精简版和完整版，支持透明背景、主体辨识、原生提问、局部精调及版本记录。
---

# Aikon

**当前验证状态：实验中，首轮视觉产物已被用户全部拒绝。** 在修复完成前不将示例或几何检查当成合格美术基线。先按[单例校准](references/calibration.md)证明一个真实主体的风格与辨识关系，再扩展批量。

通过资料研究、原生问答与视觉反馈，将主体转成 Grok bot style 图标。交付真实矢量 SVG，默认透明背景；除非用户特别要求，输出不含任何水印。PNG 预览仅是检查证据，不替代 SVG。

**当前运行合同**：[双版本提示词与覆盖规则](references/profiles.md) 对所有创作请求生效；忠实源译文中的黑背景和单图行为不覆盖本合同。

## Start with the request

区分 **create / revise / explain**。一次新增参考的绘图请求定义为一个 **round**；在同一 round 中分别生成 **short（精简版）** 和 **full（完整版）**。局部修改保留 round 并新建 revision；替换主体或新增参考建立新 round，记录关联。仅解释规则时不自动绘图。修改先读取实际基础 SVG 及其可用记录。

先读 [全模态输入研究](references/input-research.md)，再按输入实际研究：概念或名称需解析身份，图片需视觉观察，URL/wiki 需实际阅读并核对参考。音视频或文档先使用可用工具提取图像、帧、转录和结构；未知部分保持未知，不能假装所有宿主都能解码。完成主体与风格证据记录后再确认意图。

Inspect supplied images using the host's image-viewing capability. Label each as **subject reference** (identity), **style reference** (visual treatment), or unresolved. Resolve ambiguous roles and multiple possible subjects before drawing. A text-only subject description is sufficient; ask for a picture only when missing identity details matter. If images cannot be viewed, say what remains unknown and use text or human descriptions without claiming visual inspection.

Read [the visual contract](references/style.md) and inspect relevant [original examples](assets/examples/README.md). 用户给定的强模式参考优先用于目标观感；识别其中的黑底和水印并从创作目标排除，不对原参考文件作破坏性修改。Example palettes and hairstyles belong to their fictional subjects; extract visual structure without transplanting those identity features.

将主体信息保存为可核对的轮廓与连接关系，而不只是配色和三个特征名词。头部silhouette、可见脸域、刘海遮挡、束发根部与配件方向一起构图；不要先放一个通用圆/椭圆脸盘，再把身份元素贴上去。

For objects with no face, the default is an intentional round bot reinterpretation using their colors and a few recognizable motifs. Record that transformation; a literal object silhouette is an explicit style exception.

## Settle only the current decisions

Use [native interaction](references/interaction.md) to ask independent questions whose answers change the current design. Keep stable question and option IDs in the record; map them to the host's actual schema. Recommend one choice with its concrete tradeoff. Probabilities are optional and only shown if an available service actually supplied them; no external decision service is required.

Reuse explicit user choices. Capture each value's origin: `user`, `reference_observation`, or `agent_default`. Unknown facts and unanswered preferences remain visible. User changes override defaults; mark deviations in the contract so checks do not silently enforce an obsolete design.

For a new project without a specified storage strategy, ask once where and how to save revisions before persisting project artifacts. Follow [version handling](references/versions.md); do not repeatedly ask after the user has chosen. A path or strategy already supplied by the user is an answer, not a reason to ask again.

The design contract includes subject/identity cues, source roles, colors, composition, permitted deviations, current answered decisions, unresolved questions, output location, and revision base. Treat the conversation as a valid record when file writing is unavailable.

## Produce comparable candidates

意图与关键偏好确认后，每个 round 必须交付 **short.svg 和 full.svg**，按 [profiles](references/profiles.md) 分别生效。两者是明确的 profile，不是随意做两张变体；分别保存使用的中文提示词、主体证据与参数。若需比较额外候选，在各 profile 内标为 A/B，不把 A/B 冒充 short/full。用户已要求两版本时，不再问是否需要第二版。

Prefer code. When Python 3.9+ is available, use the versioned scene format and deterministic helper described in [scene-format](references/scene-format.md). 使用 `background: null`；棋盘格或深浅展示底只放在预览页面，不写进 SVG。Subject-specific vector paths remain editable; the examples are starting points, not a closed hairstyle catalog. With no suitable runtime, write self-contained static SVG directly using the same semantic groups and visual contract. Do not require installation, a paid drawing model, or a network service for the core drawing path; source research uses available retrieval tools when needed.

Create flat vector geometry. Raster tracing or a generated concept image may inform a design, but final artwork must use actual vector shapes. Keep background, face, eyes, hair/covering, cheeks, and identity accessories separately addressable. Store exact parameters and preserve source SVG IDs for later editing.

Run available structural checks, then render and inspect using [visual validation](references/validation.md). Show actual previews and link the matching SVGs. Ask the user to choose or describe the missing quality. Seeing a filename, XML, or an evaluator score is not visual verification.

## Revise and finish

Turn feedback into a bounded edit: **base version**, **target parts**, **requested change**, **preserve list**. Modify that base without regenerating unrelated geometry. If the request conflicts with a locked feature, show the conflict and resolve it before changing that feature. Read [version handling](references/versions.md) before saving a revision.

Repeat the affected checks and inspect before/after at the intended display sizes. A second failed attempt with no new evidence calls for diagnosis, not unlimited regeneration. Continue until the user accepts the result or the remaining work truly needs an unanswered choice or unavailable capability.

Deliver the SVG, its location/version, a short account of the change, and the checks actually performed. Distinguish `draft`, `structurally_checked`, `visually_reviewed`, and `user_accepted`. Never promote a candidate to user accepted through a timeout, default selection, or a model recommendation.
