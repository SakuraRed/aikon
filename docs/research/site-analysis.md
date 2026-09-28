# Grokbot Icon Studio 一手资料研究

研究日期：2026-09-28（Asia/Hong_Kong）

对应调查：[网页概念、完整提示词及视觉样例](https://github.com/SakuraRed/aikon/issues/2)
状态：公开提示词、页面及客户端交互已核对；已查看十图联系表；未生成作品、未运行站点代码、未测试站点的模型质量主张。

## 结论与证据边界

Grokbot Icon 在原作者的完整版提示词里被定义为一套具体视觉规格：双黑胶囊眼、无口鼻圆脸、倾斜近景裁切、主体身份保留和简化色块。它不是对 Grok 模型的调用要求。页面反而推荐 ChatGPT，并称其他工具尤其 Grok 可能难以达到其预期；这是作者经验陈述，未提供可复核的跨模型试验。

网站是“展示例图、取得提示词、跳转外部绘图服务”的入口，并非网页内 SVG 编辑器。它没有声明矢量输出、参数化几何、原生 Agent 提问、精确版本差分或产物目录协议；这些均属于 Aikon 需要新增和验证的能力。

不能把十张示例图全部当成严格验收模板。短版和完整版文字规范有差异，实际示例也存在偏离。尤其完整示例中可见手部，与完整版的禁止手部条款冲突。Aikon 必须分别记录文字约束、视觉观察和用户最终选择。

来源：[简体中文入口](https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans)、[公开提示词请求实现](https://grokbot-icon-studio.serio-ai.chatgpt.site/_next/static/chunks/request-prompt-KZWqjenF.js)、[图库组件](https://grokbot-icon-studio.serio-ai.chatgpt.site/_next/static/chunks/icon-gallery-8AkMI93c.js)。

## 获取方法与原文完整性

1. 复核主线程通过 AnySearch 提取的入口文本；本调查另以 AnySearch 提取许可页，与直接 HTTP 页面文本交叉核对。
2. 直接读取公开 HTML，提取其中实际引用的 JavaScript bundle URL；只读文本，没有执行下载代码。
3. `request-prompt-KZWqjenF.js` 显示页面的复制功能读取 `POST /api/prompt`，请求头为 `X-Prompt-Action: copy`、`X-Prompt-Variant: short|full`。
4. 使用同源 `Origin`、入口页 `Referer` 和正常页面会话读取两版正文，HTTP 200，`Content-Type: text/plain; charset=utf-8`。第一次未带同源信息的请求返回 403；没有尝试绕过认证、限流或隐藏入口。
5. 将响应正文按 UTF-8 保存到忽略目录。下列哈希对应保存后的正文文件，不声称是服务器版本号或签名。

| 原文 | 字符数 | UTF-8 字节数 | SHA-256 | 本地研究缓存 |
| --- | ---: | ---: | --- | --- |
| 韩文短版 | 378 | 886 | `cb8b0ff7fd103eec7e4ec9ba8d2fa77106e0a73197257d09a8e666b4ee50dac2` | `.local/research/site/prompt-short-ko.txt` |
| 韩文完整版 | 3193 | 7524 | `0f80861a9efdc2a9e0a6ef3ee4daf832e9227f3ff4cefa0559d60f212ca2c038` | `.local/research/site/prompt-full-ko.txt` |

`/api/prompt` 是 POST 读取入口；直接在地址栏 GET 该 URL 不等同于上述请求。页面语言不会更改提示词语言，两版均为韩文。缓存保留完整公开文本供本地审计，未放进分发技能包。本报告是技术释义和研究观察，不冒充官方中文译本。

## 页面中各个概念与交互

### 首页

- **短版／完整版**是两套提示词及各自五张示例，不是分辨率、付费等级或质量保证。
- **示例选择**仅替换放大的展示图及说明。初始是短版 `pink`；选择完整版示例不意味着点击任意复制按钮时自动改用完整版。复制／跳转按钮各自绑定明确的 `short` 或 `full`。
- **复制**获取所选版本正文并写入剪贴板。实现包含 Clipboard API 和旧式复制回退；显示处理中、成功、错误反馈。
- **在 ChatGPT 中使用**打开本地 `/zh-hans/chatgpt?variant=...` 过渡页。该页用 `X-Prompt-Action: chatgpt` 读取对应正文，再执行 `https://chatgpt.com/?prompt=` 加 URL 编码提示词的跳转。客户端给该请求 15 秒超时，失败显示重试和返回入口。
- **主体原图**仍需用户在目标绘图服务中添加；没有发现入口页上传图片并代用户传送的功能。
- **语言选择**有韩、英、日、简中、繁中。语言界面不是提示词翻译器。

来源：[复制组件](https://grokbot-icon-studio.serio-ai.chatgpt.site/_next/static/chunks/copy-prompt-D9RppEWl.js)、[ChatGPT 过渡页组件](https://grokbot-icon-studio.serio-ai.chatgpt.site/_next/static/chunks/chatgpt-handoff-CnCSMEOK.js)、[入口页](https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans)。以上为源码与页面观察，不是浏览器端交互验收。

### 作品集

独立入口为 [Gallery](https://grokbot-icon-studio.serio-ai.chatgpt.site/gallery/?lang=zh-Hans)。它展示作者和社区作品，具有发布者筛选、随机／时间排序、网格数量选择、分页加载、单图放大、前后导航和语言切换。默认批次为 24 张，移动端网格最多 4 × 4；客户端对过期图片票据有续期逻辑。

源码显示图片由 `/api/gallery/page` 等公开浏览接口返回，图片地址包含有效期票据，不能把临时地址当作永久引用。本调查没有下载社区图库或请求批量图片接口。页面说明版权归各自创作者，来源包括转发、提及作者和作者看到的帖子，并明确要求不要未经许可批量采集。

来源：[图库客户端](https://grokbot-icon-studio.serio-ai.chatgpt.site/gallery/app.js)、[图库本地化文本](https://grokbot-icon-studio.serio-ai.chatgpt.site/gallery/ui.json)。

### 许可与代币说明

[许可页](https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans/license) 区分四件事：提示词文本的许可；使用提示词生成的输出；输入素材的第三方权利；站点代码和示例素材各自的权利。其声明不能被压成“网站所有内容可自由再分发”。具体边界见下文。

[关于代币](https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans/coins) 是作者澄清声明，不是创作参数：作者称没有发行、运营或批准相关代币，第三方链接、赠与或将作者列为费用接收方不表示作者关联或认可。本文仅记录该站点自己的声明，不评价第三方项目。

## 短版与完整版的语义差异

| 维度 | 短版 | 完整版 |
| --- | --- | --- |
| 身份来源 | 保留发色、发型轮廓、代表装饰 | 还保留肤色／表面色；选择约三项核心形态特征 |
| 脸色 | 奶油色 | 以主体原有肤色／表面色为准 |
| 用色 | 粉彩、平涂、最少阴影 | 原始代表色、平涂；可用一档大面积弱阴影 |
| 眼比例 | 长∶粗 = 3∶1 | 长∶宽约 2.5–3∶1 |
| 倾斜 | 顺时针 15° | 顺时针约 15–20°，且明确左眼高于右眼 |
| 身份装饰 | 简略提及 | 眼镜、胡须、耳、帽、机械件等有具体保留边界 |
| 参考防串色 | 未单列 | 主体外貌只能来自主体参考，不能从风格图挪用 |
| 衣领 | 禁止身体，没有单列例外 | 身份需要时可保留底部少量颈部或衣领 |
| 冲突处理 | 眼和无嘴机器人脸优先于原图再现 | 给出五级优先顺序和局部调整方式 |
| 用户意图 | 输出一张图 | 区分生成、缺图、多主体、讲解、修改和真实性声明 |

表中均为对实际取得的两份韩文正文的功能释义。两份文本不是同一组参数的长短压缩版，不能混用固定奶油色与保留原始肤色并宣称语义完全相同。

## 完整版逐段概念释义

下表按原文段落顺序记录其功能，避免把网站指令自动升级为 Aikon 行为。完整韩文仅保存在上述研究缓存。

| 原文章节 | 段落功能与准确含义 |
| --- | --- |
| 目标 1–2 | 将输入主体变成单张极简机器人头像；身份取自原图，脸、眼、构图、着色由风格规格约束。名称在该文本内指视觉规格。 |
| 原始信息 1 | 检查肤／表面色、发色及发型整体，包括长短、分缝、卷曲、刘海和束发。 |
| 原始信息 2 | 耳、帽、眼镜、胡须、装饰、机械件只选择身份必需项；保留基本色，核心形态约三项，以大轮廓优先。 |
| 原始信息 3–5 | 不统一所有人的肤／发色；秃发或被遮盖状态应保留；不新增原图没有的特征。原表情、写实骨骼和复杂服装不照搬。风格参考不得提供主体身份特征。 |
| 脸 1–2 | 圆润大脸配简化身份轮廓，圆比例和倾斜表现可爱；面颊到下颌平滑，不作尖下巴或写实骨架。 |
| 脸 3–5 | 无任何形式的嘴与鼻；两侧小、淡、低饱和椭圆腮红；眼和腮红周围留足净面。眼镜不得挡眼，胡须不得变成嘴或写实面部结构。 |
| 眼 1–2 | 恰好两个等大的近黑实心圆端长条。正脸局部坐标下为竖直眼，长宽比约 2.5–3；双眼平行，长轴垂直于双眼中心连线，与整头共同倾斜。 |
| 眼 3–5 | 胶囊本身就是眼，没有内置眼球或瞳孔。禁用虹膜、眼白、高光、渐变、睫毛、眼皮、眉、装饰边，以及类似数字 1 的钩和底座；原眼色眼形让位于此规格。 |
| 构图 1–2 | 正方形、单主体、脸和头部大幅放大；从左下窥入，整头顺时针约 15–20°，视觉左眼略高。头发、眼和附着饰件同角度。 |
| 构图 3–5 | 左／下自然裁切，下巴触底或出框，右上留深色背景。双眼不受刘海或装饰遮挡；避开小头像居中证件照和对称构图。无躯干、无手，仅身份需要时可露极少颈或领。 |
| 头发／装饰／着色 1–3 | 以少量大而顺滑的发块保留方向、长度感和轮廓；几乎不用外描边，靠相邻色面区分；平涂代表色，约一档宽而弱的阴影，必要发亮面限一两块。 |
| 头发／装饰／着色 4–5 | 机械和装饰保留轮廓及大连接部位，省略小螺丝、电线、线路和密集花纹；缩小后眼和身份大轮廓仍须可读。 |
| 背景／排除 1–3 | 整张近黑炭灰纯色；排除场景、纹样、圆框、徽章边、文字、数字、标志、气泡和光粒效果；排除写实、3D、油画、粗糙草稿、强光泽、复杂明暗及碎发。 |
| 冲突处理 | 顺序为双胶囊眼 → 无口鼻圆脸 → 双眼完整的倾斜超近景 → 原始主色与识别特征 → 其他。刘海挡眼时微调发块；裁切隐藏关键装饰时小幅调位置／尺寸，不凭空发明特征。 |
| 执行／后改 1–2 | 生成请求返回一张实际生成的图；只附单图可视作转换意图。看不到待转图需索取；多主体未指定需问清主体。 |
| 执行／后改 3–5 | 只问提示词、规则、分析、用法则回答文字；规格书不写进图内。后改仅修改指定部分；不得虚称未实际生成或查看的结果已完成或已验证。 |

最后一节是来源站点的工作流，不是 Aikon 已接受的产品合同。用户已明确要求 Aikon 互动决策、SVG 产物和版本管理，不能直接继承“无说明只返一图”作为强制交付格式。

## 公开参考图与实际观察

下列 URL 均来自首页 HTML 和图库组件。HTML 全部声明 `1254 × 1254`；主 Agent 另验证十个下载文件的实际尺寸均为 `1254 × 1254`。本调查使用主 Agent 生成的 `.local/research/visuals/all-samples.jpg` 查看十张缩览，没有逐像素测量原图或据此声明精确色号／角度。

| 集合 | 图像 | 内容格式 | 联系表中的观察 |
| --- | --- | --- | --- |
| short | [pink](https://grokbot-icon-studio.serio-ai.chatgpt.site/images/pink.png) | PNG | 大脸、左下裁切、右上负空间、发块较简；适合研究主体构图。 |
| short | [blonde](https://grokbot-icon-studio.serio-ai.chatgpt.site/images/blonde.jpg) | JPEG | 屏幕左眼低于右眼，与文字要求的倾斜方向相反；头发细节较多。 |
| short | [black](https://grokbot-icon-studio.serio-ai.chatgpt.site/images/black.png) | PNG | 大脸与胶囊眼突出；主轮廓清楚，可分析齐刘海的避眼空间。 |
| short | [teal](https://grokbot-icon-studio.serio-ai.chatgpt.site/images/teal.jpg) | JPEG | 头发有较醒目的高亮块，密度高于最简平涂基准。 |
| short | [blue](https://grokbot-icon-studio.serio-ai.chatgpt.site/images/blue.png) | PNG | 大脸裁切和右上深色空白较清楚；主发块仍有几处层次。 |
| full | [dark-bob](https://grokbot-icon-studio.serio-ai.chatgpt.site/images/full/dark-bob.png) | PNG | 头部更完整、更小；发块阴影和颈部信息增加。 |
| full | [blonde](https://grokbot-icon-studio.serio-ai.chatgpt.site/images/full/blonde.png) | PNG | 更多发束、亮暗层次、耳饰与衣领。 |
| full | [teal](https://grokbot-icon-studio.serio-ai.chatgpt.site/images/full/teal.png) | PNG | 上方空白和服装信息更多，与最强脸部放大规则有距离。 |
| full | [ponytail](https://grokbot-icon-studio.serio-ai.chatgpt.site/images/full/ponytail.png) | PNG | 马尾用于身份轮廓，脸占画面较小、阴影层次更多。 |
| full | [black](https://grokbot-icon-studio.serio-ai.chatgpt.site/images/full/black.png) | PNG | 右侧可见手和腕部，直接违反无手条款；不能作为全项合格样例。 |

这些是作品的观察标签，不是对作者总体质量的评分。图片可供研究不等于已获再分发授权。研究参考应保留“正向证据／已知偏差／适用条款”，避免整图笼统标成合格金标准。

## 可转为 SVG 合同的规则

以下是从文字规格导出的工程解释，尚非用户选定实现，也不是来源站点已有功能。

| 可验证对象 | 可表达的合同 | 检查的实际边界 |
| --- | --- | --- |
| 画布 | 正方形 `viewBox`、纯色背景、单主体 | XML 与结构可检查；主体数量的视觉语义仍需看图。 |
| 眼形 | 两个同参数的圆端胶囊，例如 `rect` 圆角半径为宽度一半；近黑纯色 | 不能仅数所有 `rect`；需要可识别眼部图层或对象。 |
| 眼几何 | 在头部局部坐标中两眼等高、等大、平行；长轴与中心连线垂直 | SVG 屏幕坐标 y 向下，正角 `rotate` 是视觉顺时针；宜对共同头部组旋转，避免眼与头角度漂移。 |
| 画面方向 | 约 15–20° 顺时针与左眼较高同时成立 | 若另选短版基准则 15°；数值范围应作为明确的风格版本参数，不能暗中混合。 |
| 眼可见性 | 眼形完整留在画布内，不被刘海／装饰覆盖 | 包围盒只能排除一部分问题；遮挡和负空间还需渲染检查。 |
| 主体身份 | 主体参考的基本色、少量身份轮廓；参考角色与风格示例分别建记录 | 仅靠像素相似度无法保证身份正确；需用户确认关键特征。 |
| 裁切 | 左下头轮廓出框、右上背景留白、脸足够大 | 原文没有裁切量、脸占比或留白面积的精确阈值，不能把自行设值写成来源事实。 |
| 色块与层次 | 主色、有限阴影、有限亮面独立图层 | 原文没有精确调色板和色差阈值。它给的是限制复杂度的规则。 |
| 修改 | 对已命名部件／参数进行局部变更，留存旧版本 | 需要 Aikon 的版本及差分协议；网站只给出“改所需部分”的文字意图。 |

SVG 的形状、分组、变换和图层可以减少模型随意发挥，但只有实现后跨样例和跨模型验证，才能声称实际提高一致性。向模型重复同一自然语言提示词本身没有确定性保证。

### 必须防止的反模式

- 将“Grok bot”理解成必须调用 Grok，或把网页推荐 ChatGPT 当成跨模型性能结论。
- 按示例人物的肤发色污染新主体，或为无头发／机械主体补上人类刘海。
- 把源图中的人类眼睛、表情、嘴、鼻带入风格转换。
- 将竖胶囊单独旋转成与头部／双眼中心线不一致的形态。
- 用圆框、居中小头像、手势、粒子或文字补充“可爱感”。
- 以嵌入 PNG/JPEG 的 `<image>` 输出冒充可编辑矢量；来源样例本身是位图，并未提供可复用 SVG 路径。
- 因 XML 合法就宣称视觉风格通过；或因网站示例有某个元素就忽略其与规则的冲突。
- 为追求身份细节，让眼被刘海遮住，或使缩小后的发饰、机械线条变成噪点。

## 权利与分发记录

来源站点在许可页声明：提示词文本适用 **CC BY-NC 4.0**，发布或再分发原版和修改版需保留作者、来源、许可和修改标识；非商业范围不能仅按“个人／公司”身份判断。本文记录声明，没有替用户判定具体未来商业场景。

作者标识为 **X @multi_serio_ai（APG）**。页面列出许可初始生效日 2026-09-21、最近修订日 2026-09-22，并说明覆盖自 2026-09-18 起发布且被明确纳入的版本。取得的提示词响应没有单独版本号，因此证据身份采用获取时间与正文哈希。

许可页明确：站点代码、示例图、输入图、商标、字体、外部库和第三方材料不自动受该提示词许可覆盖。提示词的许可也不自动延伸至生成图。作者不因提供提示词而主张生成图版权、分成或必须署名，但输入素材、输出中的第三方权利及使用服务的条款仍需分别判断。

供引用原提示词或派生文字时使用的来源信息：

```text
Original prompt: Grokbot Icon — short / full
Author: X @multi_serio_ai (APG)
Original source: https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans
Prompt license notice: https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans/license
License: CC BY-NC 4.0
Changes: Technical paraphrase and comparison in Chinese; not an official translation.
```

本报告不授予对任何参考图的再分发权，不表示获得作者认可，也不替 Aikon 选定最终许可。完整源提示词目前仅为忽略目录的研究缓存。

## 尚待验证或决策

- 未核验作者关于 ChatGPT 免费版、Grok 或其他模型的效果陈述；当前没有对照试验。
- 未运行复制按钮、跳转后的 ChatGPT 页面或绘图模型；客户端分析不等于最终用户全流程已通过。
- 未访问社区图库图片或统计其完整数量；不得把首页十图推断为所有可能主体、肤色和非人实体覆盖。
- 未逐像素标定精确色号、裁切比例、眼距、脸占比。任何后续具体数值均须注明是测量、设计选择还是用户选择。
- 核心视觉基线、眼镜／机械主体／非人实体等边界、风格偏离的许可方式，仍需用户决策。
- Prompt 派生文本是否进入分发包，以及每张 `ref` 的研究／再分发状态，需要和仓库许可、目标使用范围分别登记。

## 本地证据索引

仅 `.local/` 内保留抓取缓存。持久报告不依赖该目录存在，关键判断已附公开一手链接。

- `.local/research/site/zh-hans.html`：入口 HTML。
- `.local/research/site/prompt-short-ko.txt`、`prompt-full-ko.txt`：两份完整韩文正文。
- `.local/research/site/request-prompt.js`、`copy-prompt.js`、`chatgpt-handoff.js`、`icon-gallery.js`：实际引用的客户端代码文本。
- `.local/research/site/license.html`、`license-text.txt`、`anysearch-license-extract.txt`：许可原页、文本解析、独立提取结果。
- `.local/research/site/coins.html`、`gallery.html`、`gallery-app.js`、`gallery-ui.json`：其余概念与边界证据。
- `.local/research/site/evidence.json`：获取路径、文件哈希与缓存时间。
- `.local/research/visuals/all-samples.jpg`：主 Agent 制作的十图联系表；本调查已通过图像查看工具核对。
