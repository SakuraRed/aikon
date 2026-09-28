# Aikon 技能包合同审查

日期：2026-09-28。范围：`skills/aikon/` 当前工作树，共 27 个文件。基线仓库 HEAD 为 `ce8e214c3bfae5981d82e6a3d076866994dab318`，技能目录尚未纳入该提交；本文判断针对本轮实际读取内容，不代表 HEAD 中已经存在这些文件。

本轮只读检查包内说明、源提示词、示例数据、SVG、宿主元数据和 helper 的依赖/输出边界，只新增本报告。没有再次运行 26 项 helper 测试，没有安装工具、启动浏览器或对品牌/角色外观作审美验收。审查者此前参与 helper、scene-format 和 fixture 实现；对父 Agent 编写的 SKILL、输入研究与 profiles 做了独立核对，但不能称为完全没有作者重合的第三方审计。

最终状态：初审发现 1 项 P2，主 Agent 已修复且本审查回读确认；没有剩余未关闭的实质性发现。该结论受文末范围限制约束。

## Findings

### P2 — 最小示例的 short 标签与所用参数矛盾

位置：`skills/aikon/references/scene-format.md:12`。相邻证据：`:13`、`:16`、`:17`、`:25`；约束来源：`skills/aikon/references/profiles.md:7`。

初审时，示例声明 `profile: "short"`，但使用 `angle: 17`、`width: 29`、`height: 81`，眼比为约 2.79:1，脸色为 `#f3c492`。同包的 short 合同是 15°、约 3:1 和奶油色脸。Agent 复制这个最小场景后会得到贴着 short 标签的另一套参数；而 helper 明确把 variant 视为来源标签，不会自动纠正分支内容，因此结构检查也不会发现这一混用。示例下方“未经视觉验收”的说明不能消除可直接核对的 profile 参数矛盾。

最小修复：将该示例改为对应的 short 参数，例如 15°、30/90、奶油脸；或将标签改为 full 并明确其完整 profile 含义。无需为修正文档示例而改变 helper 的标签行为，也不需要扩大测试或改其他示例。

状态：**已修复并回读验证**。主 Agent 修改后，本审查再次只读核对 `scene-format.md:12`、`:13`、`:16`、`:17`、`:25`，确认标签仍为 short，参数现为 15°、30/90（3:1）、`#fff1e5` 奶油脸；透明背景仍为 null。该文档修复不涉及 helper 逻辑，未重复执行测试。本审查未修改技能文件。

未发现 P0/P1 问题，也未发现第二项达到需修改门槛的合同矛盾。

## 已核对且相符的合同

| 用户要求 | 实际证据 | 本轮判断 |
| --- | --- | --- |
| 概念、名称、图片、wiki 等先研究，再确认意图 | `SKILL.md:16`；`references/input-research.md:5` 起按输入类型列实际步骤，随后单列研究后的确认 | 研究动作、来源角色和未知状态均有明确约束；已完整表达的意图不重复询问 |
| 每个新增参考 round 包含 short/full | `SKILL.md:14`、`:36`；`references/profiles.md:12`、`:40` | 两个 profile 同主体同 round；额外 A/B 不冒充 short/full；既有用户选择继续有效 |
| 透明背景且默认无水印 | `SKILL.md:8`、`:38`；`references/profiles.md:11`、`:14`；`references/validation.md:15` | 默认 null，展示底与最终 SVG 分开；水印例外需用户明确要求；实际 alpha 与结构检查分开 |
| 旧源提示词黑底/单图不能压过当前合同 | `SKILL.md:10`；`references/profiles.md:9` 起覆盖条款；两份源译文各自开头的研究用途提示 | 入口和 profile 双重规定优先级；源黑底保留为忠实译文，不被当作当前生成默认 |
| 简体中文源 prompt 保留关键 English | `references/prompts/source-short.zh-CN.md`、`source-full.zh-CN.md` 全文；`references/profiles.md:23` 起生产指令组成 | 两份源译文为中文，保留 capsule eyes、silhouette、close-up 等括注；生产指令要求按分支保存中文提示词 |
| 存放策略未定时首次询问，后续不重复 | `SKILL.md:30`；`references/versions.md:3` | 明确在保存项目产物前确认；用户已给位置或策略即视为已答，不自动建 Git 或推送 |
| 代码优先、真实 SVG、可精确修改 | `SKILL.md:38`、`:40`、`:46`；`references/versions.md:32` 起 | 标准库 helper 可选；无合适 runtime 可直接编写静态 SVG；指定基准、修改范围与保留项，版本不冒充验收 |
| 跨 harness 按实际工具能力诚实降级 | `references/interaction.md:5` 起；`references/validation.md:26` 起；`input-research.md:3` | 工具名称只是线索，按实际 schema；原生工具缺失、无法查看图和无法渲染均有诚实处理；同模型子 Agent 不当跨模型验证 |
| 推荐有代价，不编造概率或用户答案 | `SKILL.md:26`、`:28`；`references/interaction.md:26` 起 | 外部判断服务可选，实际条件概率对应 option；无评分则未评分，取消/空答/自动继续不构成用户选择 |

表内未加 `skills/aikon/` 前缀的路径均相对此包。

## 包完整性与资源边界

- 检查了 30 个 Markdown 相对链接：目标均存在，且没有相对链接跳出技能包；必要规范、源译文、示例和脚本随包存在。外部来源链接用于引用，核心代码绘制路径不依赖远端服务。
- 三个自产示例主体 Moss、Relay、Lantern 均有 short/full scene 和 SVG，共六对文件。JSON 的 background 均为 null；short 为 15°、3:1 与奶油脸，full 为 17°、2.8:1 并保留不同主体底色。未发现这六份示例的分支标签混用；文档最小示例的问题已按上文回读确认修复。
- 本轮实际查看了新加入的 `assets/examples/preview.png`：内容为上述六份自产示例的预览板，含棋盘格与深色展示底；README 明确这些展示底不是 SVG 背景。查看目的为辨识包内素材来源范围，不据此宣称全部图标视觉合格。
- 包内没有看到原网页角色图、用户 r1/r2、用户立绘或下载的官方游戏图。PNG 仅为自产示例预览；六个 SVG 为路径/基本形状，没有嵌入或外链位图。这里核对的是当前文件内容与边界，不是对作品原创性作独立法律认证。
- `THIRD_PARTY_NOTICES.md` 及两份源译文保留原作者、来源、许可和翻译说明；没有把整包概括成无限制 MIT 资产，也没有把提示词许可扩展为角色图授权。本文不重新做翻译逐句审校或法律审查。
- 包内文本检索未发现本机绝对路径、固定账号路径、localhost 服务、用户素材路径、API key 或必须调用 Jev/AnySearch 的运行依赖。helper 导入均为 Python 标准库；`http://www.w3.org/2000/svg` 是 XML 命名空间，不是网络下载。
- `agents/openai.yaml` 是附加宿主展示元数据；SKILL 的执行规则不依赖该文件提供工具。没有宣称未实测的 Claude Code、OpenCode 或 ZCode 组合已经通过。

## 证据限制

1. helper 的执行证据沿用本会话此前 `python -B -X utf8 -m unittest discover -s tests -v` 的 26 项通过结果（无跳过）；本轮只核对源文件与文档，不把旧测试扩展为新增审查结论。
2. 本轮只检查包内相对链接可达，没有重新验证全部外部 URL 的在线可用性；源站许可与译文准确性由对应研究记录负责。
3. 缺工具、取消问答等降级逻辑在说明中齐备，但本轮没有实际启动其他 harness，也没有做人类交互实验；文档一致不等于运行兼容已验证。
4. 透明背景和水印的源码检查不能替代最终像素与视觉检查；其他路径也可能铺满画布或组成可见标记。包内规则对此保留了显式验证边界。
5. 审查期间父 Agent 正在完善包；后续修改应对应具体 finding 或新证据复核，不将本文自动视为任意后续版本的验收。
