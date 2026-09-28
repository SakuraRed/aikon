# 可移植技能、原生问答与 SVG 一致性研究

研究日期：2026-09-28。关联调查：[标准技能移植、原生问答与 SVG 一致性验证](https://github.com/SakuraRed/aikon/issues/3)。本文记录事实、由事实推导的工程约束及待选策略，不记录未经用户回答的产品决定。

## 结论与证据范围

可移植的基本单位是包含 `SKILL.md` 及相对路径资源的目录。Agent Skills 统一元数据与内容组织，不统一安装目录、原生问答工具、图像查看、代码执行或视觉质量。因而 Aikon 可以发布同一份核心技能，但兼容声明必须落实到“宿主版本、运行模式、模型、实际可用工具与通过的用例”。这是对[标准覆盖范围](https://agentskills.io/specification)与下文宿主差异的工程推论。

代码优先能把已确定的设计约束落实成可检查几何，固定参数与生成器还能实现可复现导出；它不能保证不同模型把任意主体资料理解成完全相同的参数。“相同效果”应拆成视觉语言一致、几何一致、渲染一致和用户认可四种证据，不能混用。

本轮完成官方标准、官方文档与公开源码阅读，使用 AnySearch 发现 `code.doc`、`code.snippet` 后作辅助搜索；不采纳搜索摘要作为最终证据。未安装、运行或认证其他 harness，未运行 SVG 渲染器，未测量跨模型效果。因此宿主支持均为文档或源码级证据；当前 Codex 工具 schema 是本会话的可观察事实，尚非交互回归测试。

OpenAI 信息先核对了本机 CLI 启动入口与当前工具 schema；启动入口指向的历史包目录不存在，无法据此审计 CLI 源码，随后查官方文档。旧文档入口现重定向至 `learn.chatgpt.com`，本文引用最终页面。可变文档与 OpenCode `dev` 源码均以本次读取日期为证据时点，发布兼容声明前需锁定并复查实际版本。

## 1. 标准内容与宿主扩展

Agent Skills 必需项是 `SKILL.md` 的 YAML frontmatter 中的 `name`、`description`，后接 Markdown；可带 `scripts/`、`references/`、`assets/`。`name` 长度最多 64，目录名应匹配；`description` 最多 1024 字符；`compatibility` 最多 500 字符。`allowed-tools` 仍为实验字段。规范鼓励分层加载，将较长资料放入按需读取的资源，并用技能目录内的相对路径关联。[Agent Skills specification](https://agentskills.io/specification)

由此得到的工程边界：

- 核心说明只依赖标准字段；角色知识、风格定义、问答维度、修改规则与验收规则放入普通 Markdown/JSON/SVG 资源。具体目录布局仍可调整。
- 用途与触发条件放在简短 description 的前部；完整提示词放正文或引用文件。宿主会截短元数据展示，不能依靠描述末尾承载关键规则。
- 不把 Claude 的动态命令注入、`context: fork`、`model`、hooks，或 Codex 专属配置写成必需执行机制。Claude 明确将这些列为其扩展；OpenCode 会忽略不认识的 frontmatter。[Claude Code skills](https://code.claude.com/docs/en/skills#using-skill-frontmatter-outside-claude-code)、[OpenCode skills](https://opencode.ai/docs/skills/#write-frontmatter)
- 技能文本不能创造不存在的工具，也不能改变宿主权限。用 `allowed-tools` 声明某工具不是跨宿主安装该工具的办法。
- Jev、AnySearch、wayfinder 和本机其他私有技能属于 Aikon 的研发能力，不是分发技能的默认前置依赖。联网、付费服务和绘图 API 也不应成为代码 SVG 核心路径的隐含要求。

## 2. 宿主兼容事实

### 2.1 技能加载

| 对象 | 已核对的入口 | 对 Aikon 的影响 | 证据等级 |
| --- | --- | --- | --- |
| Codex | 仓库和用户的 `.agents/skills`；仓库扫描从工作目录向仓库根部进行；支持符号链接 | 同一技能目录可复制到文档支持的扫描位置；不将本机 `.codex` 路径写入核心 | 官方文档；未安装验证 |
| Claude Code | `.claude/skills/<name>/SKILL.md`，项目与用户级位置；支持标准并另有扩展 | 独立提供安装说明；不假定 `.agents/skills` 自动发现 | 官方文档；未安装验证 |
| OpenCode | `.opencode/skills`、`.claude/skills`、`.agents/skills` 的项目/用户位置；原生 `skill` 按需加载 | 要同时检查技能发现与 skill 权限；禁用时不会进入可用技能列表 | 官方文档；未安装验证 |
| Z.ai 的 ZCode，候选解释 | `~/.zcode/skills/<name>/SKILL.md`；可通过设置页复制或链接导入外部 Agent 技能 | 可复用目录，但复制后不自动同步，符号链接依赖原路径；远端工作区需另外同步 | 官方文档；产品身份和实际版本待确认 |

来源：[Codex Build skills](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)、[Claude Code skills locations](https://code.claude.com/docs/en/skills#choose-where-skills-load)、[OpenCode skills](https://opencode.ai/docs/skills/)、[ZCode Skill](https://zcode.z.ai/en/docs/skill)。

`zcode` 在用户原始需求中没有给出厂商或链接。本轮找到 Z.ai 的一手产品文档，但不能把名称相似作为身份确认。上表仅描述此候选；若用户指的是另一产品，不能继承兼容结论。

ZCode 官方还记载：缺少 `name`/`description` 或 description 超过 1024 字符会导致技能被忽略；正文超过 100 KB 会被截断；启用技能过多会使元数据退化为仅名称。标准可解析不等于模型能可靠触发。[ZCode format and context limits](https://zcode.z.ai/en/docs/skill#format-limits)

### 2.2 原生问答与回答映射

| 对象 | 已知工具与结构 | 不可直接共用的部分 | 当前结论 |
| --- | --- | --- | --- |
| 本会话 Codex Desktop | 暴露 `request_user_input`；说明要求每次 1–3 题、每题 2–3 项；问题包含 `id/header/question/options` | 无多选字段；宿主自动添加自由输入；题数约束和可用模式按当次 schema | 仅当前运行时观察，不宣称所有 Codex 版本都相同 |
| Claude Agent SDK / Claude Code 工具接口 | `AskUserQuestion`；文档为 1–4 题、每题 2–4 项；`multiSelect`；回答按问题文本映射标签 | 与 Codex 的问题 ID 映射不同；SDK 自定义 UI 需要回调处理；官方注明 Agent tool 子 Agent 中不可用 | 可据文档写映射说明，尚未实际调用 |
| OpenCode | `question`；`questions` 中有 `question/header/options/multiple`；回答为按问题顺序排列的标签数组 | `multiple` 名称不同；源码区分请求 ID 与问题内容；取消有独立错误；工具输入 Prompt 不暴露服务 Info 的 `custom` 字段 | 按实际运行时 schema 使用，不能照搬内部服务的全部字段 |
| Z.ai ZCode，候选解释 | 官方确认任务中存在普通问答，以及独立的权限/计划确认 | 本轮未找到足以确认原生工具名称、字段及题数限制的公开 schema | 启动时探测；未查到不等于不存在 |

来源：[Claude SDK user input](https://code.claude.com/docs/en/agent-sdk/user-input#handle-clarifying-questions)、[Claude SDK limitations](https://code.claude.com/docs/en/agent-sdk/user-input#limitations)、[OpenCode question tool](https://opencode.ai/docs/tools/#question)、[OpenCode tool implementation](https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/opencode/src/tool/question.ts)、[OpenCode question schema](https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/schema/src/v1/question.ts)、[OpenCode cancellation handling](https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/opencode/src/question/index.ts)、[ZCode question behavior](https://zcode.z.ai/en/docs/safety-confirm#questions-that-continue-on-timeout)。

稳定的内部 `question_id` 和 `option_id` 应由 Aikon 的记录保持；宿主只接受标签或问题文本时，记录当次映射，收到真实答案后再转换回来。不要把 schema 未声明的 `option_id` 硬塞进工具参数。多个选择维度只有相互独立时才合批：表情依赖眼睛结构时应分轮，背景与输出存放位置则可能独立。此处是工程策略，具体询问深度仍待产品决策。

### 2.3 等待与缺答不具有统一语义

Codex app-server 官方协议现在公开了 `tool/requestUserInput` 的 `autoResolutionMs`，值为毫秒整数或 `null`，客户端可据此自动处理未答题。它是客户端协议字段；并不证明当前内置 `request_user_input` 向模型暴露该参数，也不证明存在可供用户设置的同名配置。当前工具 schema 没有等待时长参数。[Codex App Server](https://learn.chatgpt.com/docs/app-server#toolrequestuserinput)

Z.ai ZCode 官方文档则明确记载普通问题默认等待五分钟后自动继续，可在设置关闭自动继续；权限与计划批准不受此倒计时影响。此事实只适用于该文档描述的 ZCode，不能迁移成 Codex 的配置结论。[ZCode Safety Confirmation](https://zcode.z.ai/en/docs/safety-confirm#questions-that-continue-on-timeout)

Aikon 的记录至少区分 `answered`、`unanswered`、`dismissed`、`tool_unavailable`，保留用户自由文本。宿主自动继续、空数组、异常或关闭面板都不能写成用户选了推荐项。未答的必要条件保持待决；已有明确选择不重新投票。可以继续独立准备工作，但不能把依赖该选择的成品标为用户已认可。

## 3. 按能力降级，而非按品牌猜测

下表为待实现的能力契约，不是新增强制平台依赖。

| 必要能力 | 可用时 | 缺失或被限制时 | 允许作出的完成声明 |
| --- | --- | --- | --- |
| 读取技能与相对资源 | 按需加载规范、参考、模板 | 仅能收到正文时，将缺失资源列明；不能假装已读参考 | 说明已提供，不声称完整技能已加载 |
| 原生结构化问题工具 | 主 Agent 按真实 schema 提问，记录工具返回 | 用户未限定原生工具时可用普通聊天；若明确要求原生，报告限制并保留未答状态，不擅自换成别的表单 | 区分原生交互、聊天交互、未完成交互 |
| 图像理解 | 实际查看 style 与 subject 图；记录观察 | 可依据用户文字和已有人类标注继续；未知形状保持未知 | 不能宣称已视觉筛选或已理解图片 |
| 文件写入 | 保存 SVG 和版本记录 | 输出完整可保存源码及清晰文件名 | 源码已生成，文件未落盘 |
| 本地代码执行 | 调用已审计的生成/检查脚本 | 直接编写静态 SVG；可执行检查留待有能力环境 | 不声称脚本检查通过 |
| SVG 渲染/截图 | 实际导出各尺寸预览并查看 | 交付源码，标记视觉未验证，保留用户预览反馈入口 | 格式检查与视觉检查分别报告 |
| Git | 用户选择后按现有仓库约定记录 | 普通目录、revision manifest 与内容哈希 | 可追溯文件版本，不声称有 Git 提交 |
| 图像生成 API | 作为探索或参考辅助 | 代码路径仍可工作 | 位图概念图不能充当最终矢量 SVG |
| Jev / AnySearch | 在授权范围内作为研发或可选辅助 | 使用证据、代价和未评分标识继续可进行部分 | 不编造决策概率，不把服务调用做成隐含硬依赖 |

这套降级允许说明清楚地移植，但“任何模型”仍须具备完成相应步骤的基础能力；文本技能无法替不支持视觉的模型提供图像感知。技能的承诺应是明确工作方法、约束和失败出口，而非未经验证的能力保证。

## 4. 代码 SVG 如何减少模型与环境差异

### 4.1 真矢量与限定子集

SVG 允许嵌入图像和其他内容，因此 XML 可解析、扩展名为 `.svg` 都不能证明产物是可编辑矢量。[SVG embedded content](https://www.w3.org/TR/SVG2/embedded.html)

Aikon 可以定义比 SVG 标准更窄的“交付子集”：静态 `path/rect/circle/ellipse/polygon/polyline/line` 与 `g/defs` 等经过验收的元素；无位图 `<image>`、远程资源、脚本、事件处理器和 `foreignObject`。渐变、clipPath、mask 与滤镜是否允许，应由实际风格需要和兼容测试决定，不因名称是 SVG 就默认全部开放。此处是 Aikon 可选工程约束，不是声称 SVG 标准禁止这些能力。[SVG processing modes](https://www.w3.org/TR/SVG2/conform.html)

### 4.2 可精确约束的几何

`viewBox` 决定用户坐标到显示视口的映射，`preserveAspectRatio` 影响缩放和裁切；描边宽度、端点和拐角也影响可见边界。只记录路径中心线会漏掉描边越界。[SVG coordinates](https://www.w3.org/TR/SVG2/coords.html)、[SVG painting](https://www.w3.org/TR/SVG2/painting.html)

由此可把视觉语言拆成可检查参数，具体值须来自参考分析及用户决定：

- 画布与安全边距：归一化坐标、主体占画布比例、描边后的边界。
- 层次：背景、主体轮廓、脸部、眼睛、识别特征、装饰的稳定分组与绘制顺序。
- 形状：头身比例、圆角、眼距、眼睛高宽、曲线控制点、对称轴与允许的不对称。
- 笔触：描边宽度或轮廓填充方案、linecap/linejoin、连接处与负空间。
- 色彩：显式色值、透明度、有限调色板以及背景；不依赖未知父页面的 `currentColor`。
- 主体辨识：需保留的特征与可省略细节分别记录，不让装饰挤占辨识特征。

这些参数有助于重现，但不保证任意角色都适合一套固定部件。若主体超出参数系统表达范围，必须暴露自由矢量扩展或声明限制，不能为了“模板通过”抹掉核心身份。

### 4.3 三种实现强度，仍待选择

| 工程方式 | 能固定什么 | 主要代价 | 可作出的复现声明 |
| --- | --- | --- | --- |
| 规则与参考约束，Agent 直接写 SVG | 输出子集、比例范围、调色板和检查流程 | 模型仍自主选择路径，版本间可能漂移 | 验收项一致；不保证路径相同 |
| 固定模板与参数化部件 | 常见主体结构与局部参数 | 表达空间受模板覆盖限制；需要扩展部件 | 相同模板、参数、版本可重建结构 |
| 版本化中间设计数据与确定性生成器 | 参数、算法、序列化、可重建导出 | 需要维护数据契约、生成器与迁移 | 同输入和生成器可测字节一致；前提是无非确定因素 |

这三者可以组合。当前研究未选定一种，也未规定具体视觉比例。

### 4.4 渲染与小尺寸

`shape-rendering` 只是渲染提示，`crispEdges` 可能调整像素对齐或关闭抗锯齿，不能使任意曲线自动清晰或强制所有渲染器像素相同。[SVG rendering hints](https://www.w3.org/TR/SVG2/painting.html#ShapeRenderingProperty)

浏览器截图会受到 OS、浏览器版本、字体、硬件和运行模式等影响。固定截图基线环境可用于回归测试，但跨环境像素差异不能直接归因于模型。[Playwright visual comparisons](https://playwright.dev/docs/test-snapshots)

resvg 官方将自己定位为静态 SVG 渲染器，声明在支持平台可产生相同像素，并列明动画和部分 SVG 支持限制。它可成为固定版本的参考渲染器候选；要记录版本、输入、字体/外部资源、尺寸与参数，不把该项目声明当成本仓库已实测的保证，也不把 resvg 等价于全部浏览器。[resvg README](https://github.com/linebender/resvg#reproducibility)

小尺寸有独立的设计成本。Carbon 官方图标规范以像素网格、边距和展开描边控制其 UI 图标，说明生产尺寸会影响几何处理；其 32 px、2 px 边距和整数坐标是 Carbon 的规则，不能当作 Grok bot 风格的普遍标准。[Carbon v10 icon production guidelines](https://v10.carbondesignsystem.com/guidelines/icons/contribute/)

Aikon 可在约定实际用途后建立 16/24/32/48/64/128 px 等尺寸检查板；这些只是候选检查尺寸。应在 100% 比例查看：眼睛和关键饰件是否仍可区分，负空间是否闭合，描边是否吞掉五官，轮廓是否被裁切。大图缩小后不清晰时，可以选择单一主 SVG 微调，或创建明确标注的光学校正版；不能暗中在不同尺寸交付不同设计。

## 5. 一致性的可验证定义

下列定义将“尽可能同样效果”变成可比较证据；各层是否为发布门槛及阈值尚待用户决定。

| 层级 | 保持相同的条件 | 检查对象 | 不能替代什么 |
| --- | --- | --- | --- |
| A. 契约一致 | 相同 style profile、主体资料、已回答设计合同 | 画布、色板、描边范围、必要特征、禁用元素 | 不能证明好看或像同一角色 |
| B. 几何一致 | 相同设计数据、生成器版本及数值规则 | 规范化元素树、路径/坐标、分组、边界；或稳定序列化后的哈希 | 文本不同仍可能视觉一样，文本相同也不等于用户喜欢 |
| C. 渲染一致 | 相同 SVG、渲染器版本、尺寸、背景及资源 | 解码后 RGBA 像素；同环境可要求零差异，跨渲染器采用另定容差 | PNG 文件哈希不等于像素比较；跨环境不能无条件要求零差异 |
| D. 风格与身份一致 | 同一比较面板、尺寸、观察条件 | 盲化并列评审：视觉语言、主体辨识度、用户锁定特征、小尺寸清晰度 | LLM 打分不是用户验收，不是经过校准的成功概率 |
| E. 局部修改一致 | 相同基准版本、明确 target 与 preserve 集合 | 指定属性变化、其余分组/参数未变化，以及允许区域外的视觉差异 | 不能只看整个文件“改了多少行” |

对自然语言生成的不确定部分，可以比较同一任务在不同宿主/模型下的多次输出，报告每个维度与失败案例；不能拿一次成功或一张相似示例推导“任意模型一致”。若使用评分，定义量表、评分者与分歧处理；阈值须预先锁定，不在看到失败后悄悄放宽。

## 6. 局部修改和版本来源

工程上可保留语义分组和稳定 ID，例如 `head/eyes/identity-mark/accessory`，用明确的目标参数修改，而不是每次重写整张图。记录 `base_revision`、修改区域、目标值和 `preserve` 清单。遇到约束冲突，如眼睛增大侵占被锁定饰件，应返回冲突证据而非同时改掉饰件。

若使用优化工具，编辑母版与压缩导出版应分开。SVGO 的 `cleanupIds` 会删除未引用 ID、缩短 ID；这可破坏依赖语义 ID 的后续修改入口。保留策略须显式配置并验证，不应让无提示的优化覆盖母版。[SVGO cleanupIds](https://svgo.dev/docs/plugins/cleanupIds/)

版本记录可以借鉴 W3C PROV 对实体、生成活动、来源派生关系和责任主体的区分，不要求实现 RDF 或完整 PROV 系统。[W3C PROV-DM](https://www.w3.org/TR/prov-dm/)

最小记录候选如下，具体目录与 Git 使用仍由用户选择：

```text
<user-chosen-output-root>/<project-or-subject>/
  references/                  # 原始输入或获准保存的副本、来源索引
  brief.json                   # 主体、风格合同、决策来源、未答项
  revisions/
    r001/
      icon.svg                 # 可编辑母版；最终必需产物类型
      design.json              # 若采用参数化路径
      preview.png              # 检查证据，不冒充最终 SVG
      revision.json            # parent、输入哈希、工具版本、修改与验收
      feedback.md              # 实际反馈及处理结果
```

记录至少包括：来源 URL/输入文件摘要、取得时间、权利状态；skill/style profile/generator 版本；harness/model 标识（已知时）；用户选择与 Agent 假设分开；父版本；实际修改；SVG 内容哈希；渲染条件；验证结果与未完成检查；用户接受状态。没有调用绘图模型时不伪造生成提示词日志。使用用户原始素材时，不自动上传、扩大分发范围或把私人路径写入可分享文件。

哈希可证明后续文件是否与记录一致，不能证明参考素材授权、原始资料真实性或用户已批准。Git 也只负责内容历史；产品意义上的 revision 与用户验收仍须单独记录。

## 7. 行为与视觉验证矩阵

这是后续创建—测试—视觉验证—反馈—修正循环的候选验收计划，本轮未执行。测试对象是外部可观察行为，不以复述实现的断言凑数量。

| 场景 | 预期行为 | 保留证据 |
| --- | --- | --- |
| 风格参考和主体图片均有 | 正确区分两类参考；先实际查看；不把风格样例的身份套给主体 | 输入索引、观察记录、设计合同 |
| 仅文字或无法查看图片 | 说明哪些身份信息未知，使用授权的文字路径继续 | 能力记录、未验证字段 |
| 完整 brief | 直接利用既定选择，不重问已答题 | 决策日志、问答调用次数及内容 |
| 独立问题和依赖问题混合 | 独立项可合批；依赖项待上游选择；选择与代价对应同一 option | 实际工具入参与回包、ID 映射 |
| 取消、空 answers、宿主自动继续 | 不记录为用户选择，不将相关成品标为接受；继续独立工作 | 状态迁移和保留的待决项 |
| 原生工具不可用 | 按用户要求处理降级，不伪称调用成功，不循环撞同一错误 | 工具 schema/错误与降级声明 |
| SVG 夹带 PNG、远程链接或脚本 | 依据交付子集拒绝或修复；检查 CSS URL 与属性，不能只搜 `<image>` | 结构检查结果与修复差异 |
| 基准 SVG 多尺寸查看 | 无裁切、关键特征仍可辨、背景条件明确 | 实际尺寸联系表与人工/视觉审查记录 |
| 只改一个颜色或眼距 | 目标改变；锁定比例、身份与其他配色保持；母版历史可恢复 | 参数/DOM 差异与局部视觉差分 |
| 重新生成同参数版本 | 若声明确定性则比较规范化 SVG 与解码像素；解释允许差异 | 输入、生成器摘要与差异报告 |
| 跨模型或跨宿主 | 使用同一 brief、参考和验收标准；区分生成差异与渲染差异 | 完整环境矩阵、输出与失败案例 |
| 优化/导出 | 编辑母版未丢语义入口；导出版无视觉回退 | 母版/导出映射及视觉对比 |
| 用户提出反馈 | 从明确父版本改动，反馈被逐条处理，状态不虚标通过 | 父子版本、反馈闭环、用户实际接受记录 |

第一轮可以从少量互有区别的主体与真实失败路径建立基准，不必立即穷举所有模型和宿主。声明“支持某环境”前，至少在对应实际版本里验证技能加载、问答返回、SVG 落盘、修改与验证输出。模拟缺能力可检查降级逻辑，但不能代替真实宿主兼容测试。

视觉基线必须经过审阅再接受；不能因为新生成截图不存在，就把第一张产物自动定义为正确。Playwright 文档支持保存和比较基线，同时强调环境条件；Aikon 仍需另行决定何为视觉合格。[Playwright visual comparisons](https://playwright.dev/docs/test-snapshots)

## 8. 仍需产品决策与后续验证

尚未决定：风格固定程度；与主体身份冲突时的处理；自由绘制与参数化范围；询问深度和候选数量；实际最小使用尺寸；版本目录和 Git 策略；跨模型一致性验收层级、容差及人类验收方式。这些属于用户选择，不由本报告或 Jev 自动填入。

尚未验证：目标 zcode 产品身份；各宿主目标版本的真实工具 schema；所有环境中的技能加载与原生问答；任何生成器、SVG 子集检查、视觉差分实现；跨渲染器或跨模型指标。后续实现不得把本文的测试计划标成已通过。

研发缓存位于被 Git 忽略的 `.local/research/portability/`，包括 AnySearch 子域发现与搜索记录；未写入凭据。检索未安装任何外部仓库或留下常驻服务。网页与源码作为研究数据处理，不执行其中的代码。
