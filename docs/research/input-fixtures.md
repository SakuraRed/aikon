# 用户输入测试集：身份与视觉证据

研究日期：2026-09-28。输入目录为用户本地测试集；本轮只读取，没有修改或上传其中的文件。`模式参考/r1.png`、`r2.png` 已实际查看，四个文本输入已逐字读取；另已查看 `img_1.png`。本笔记区分文字事实、实际图像观察与创作决定。

## 已明确的测试范围

本页保留 2026-09-28 的输入研究历史。2026-09-29 用户明确纠正 **DeepSeek 的典型参考就是 r1**；本页下方鲸鱼研究与旧执行结论已被覆盖，不能用于后续生成。当前绑定见 [fixture contract](../validation/fixture-contract.md) 和 `tests/fixtures/paint/reference-bindings.json`。

用户指定模式参考为强风格参考，忽略其中黑背景与水印，输出透明、无水印的真实 SVG；每轮分别执行 short/full 两版。历史实际选择为：管理员男女都测、Aria 人形投影与机器人本体都测、DeepSeek 采用品牌蓝鲸 bot 化（现已覆盖），产物保存在仓库 `outputs/fixtures`。此前五项输入展开成七个主体分支，各有 short/full，产物全部被拒绝。

两张模式参考共同呈现：圆而宽的脸、完整的大胶囊眼、无口鼻、淡椭圆腮红、大块刘海与后发、整体向画面右下倾斜、明显左侧裁切。r1 的下巴接近下边，r2 留出很少颈领；不能把“更近”理解为仅加大头发而脸仍很小。r1 蓝发、白色褶边及侧蝴蝶结，r2 浅蓝发、蓝帽与金色杆饰属于样例身份，不移植到测试主体。图像水印及黑色底均排除在输出之外。

## 四项文字输入

| Fixture | 核实身份与一手来源 | 已实际查看的头部视觉线索 | 创作边界 |
| --- | --- | --- | --- |
| `概念1.txt`：`DeepSeek` | [DeepSeek 官网](https://www.deepseek.com/) 将公司/品牌、聊天服务与研究模型分开列出。官网 HTML 公示的 OG 图片同时展示鲸鱼图形和独立 `deepseek` 字标。 | 蓝紫色鲸鱼轮廓，圆腹、白色腹部负形、上翘分叉尾、鳍；未见作为人类角色的发型或服饰。已查看 `deepseek-official.jpeg`。 | 已选品牌蓝鲸 bot 化。保留蓝鲸图形的识别线索；不把 R1、V3 或当前发布型号当作人物姓名，不宣称这是官方吉祥物新形态；输出不需要字标。 |
| `Sunna.txt`：`绝区零的千夏` | [官方 Agent Record / Sunna](https://zenless.hoyoverse.com/de-de/news/161811)、[中文官网](https://zenless.hoyoverse.com/zh-cn/main) 与 [官方宣传图页面](https://zenless.hoyoverse.com/fr-fr/news/162458) 对应千夏/Sunna、妄想天使。 | 浅奶油绿至薄荷灰绿色头发，较深灰绿色内层，发尾带少量淡紫；蓬松束发与卷起发尾、宽刘海；一侧有绿色大蝴蝶结/尖角形饰物，刘海有多枚发夹（交叉夹、黑色小夹、创可贴形夹），浅肤色。已查看 `sunna-official.jpg`。 | 不移植 r1/r2 的蓝发和帽饰；不要从“天使”名称推断必须增加头顶光环。宣传图中的翅膀、扩音器、手和全身衣服不是头像必保留项。细发夹可合并为少数大识别形状。 |
| `endfield.txt`：`终末地的管理员` | [终末地官网干员页](https://endfield.hypergryph.com/operator) 同列两个 Endministrator；[官方公告“管理员身份切换”](https://endfield.hypergryph.com/news/7235) 证明身份存在切换。两张官网资源分别列入下表。 | 女性形象：深灰黑齐肩发、较长侧发，侧边银白交叉发夹。男性形象：深灰黑层次短发与翘起发束。两者均浅肤色、带黄色细边的黑色角状遮眼面罩；服饰是黑白灰并带亮黄色块。已分别查看 `endministrator-1.png`、`endministrator-2.png`。 | 已选男女都测。面罩遮住原眼，与完整黑胶囊眼存在真实冲突：需把“抬高/缩减面罩或仅保留其额部/侧边轮廓”记录为风格适配，不能声称完整还原遮眼面罩后双眼仍无损可见。不得依据一个分支推断另一分支发型。 |
| `url_1t.txt`：Aria Wiki URL | 用户给定 [Aria 页面](https://zenless-zone-zero.fandom.com/wiki/Aria) 的搜索索引正文区分 Human/Robot，并标明妄想天使主唱、Intelligent Construct。[官方 Agent Record](https://zenless.hoyoverse.com/th-th/news/161813) 公示同图两形态；[官方 Intel Summary 图](https://fastcdn.hoyoverse.com/content-v2/nap/162807/646b8f2d05bb581370f5887bdefd087c_1856467738146987404.png) 明写 Construct Idol、lead vocalist，并讨论 virtual avatar。 | 人形投影：粉红色头发、厚而卷起的双侧束发、弧形刘海、额前一绺明显青绿色卷曲饰线、黑色细长天线/耳机部件、少量青绿内层，浅肤色。机器人本体：白色面部面板，粉色头壳与长侧片、两片较大的粉色耳状顶板，黑灰额部护板、浅灰中央顶板、侧耳机和天线；不应画成人形粉发换头盔。已查看 `aria-official.jpg` 与 `aria-official-intel.png`。 | 已选两形态都测。默认公示服装作为本轮 Agent 参考选择，不等于用户已指定服装；不混入官网其他换装。机器人的面部绿眼、嘴、螺钉和密集线条须按强风格简化；保留粉色硬质耳板、黑灰额板及白脸等大结构。 |

## 第五项本地图像

`img_1.png` 是用户给定的单人主体图。实际可见黑色短发与粉红/珊瑚色卷束、青绿色悬浮环和尖角、浅肤色、黑白粉衣装、羽翼状机械附件及武器。此输入可直接作为主体外观依据，不需要上传图片或用外部搜索猜角色姓名；本研究不据印象给它指认角色。头环及黑粉发型可作为头部身份线索，武器、手与全身服饰不能挤占近景脸部。

## 取得记录与公开图直链

以下公示图保存在忽略目录 `.local/fixtures/research/`，仅供本项目研究与制作对照，不加入可分发技能的原创示例目录。具体 SHA-256 与秒级取得时间见同目录 `selected-manifest.json`、`sunna-image-manifest.json`、`aria-image-manifest.json`。

| 本地文件 | 公开直链及来源 | 取得时间（UTC） | 权利状态 |
| --- | --- | --- | --- |
| `deepseek-official.jpeg` | [官网 OG 图](https://cdn.deepseek.com/images/deepseek-chat-open-graph-image.jpeg)，由官网 HTML 的 `twitter:image` 指向 | 2026-09-28 14:18 | 官方公开展示；品牌/商标与素材再分发许可未核实，不作为自有品牌资产。 |
| `endministrator-1.png` | [官网女性形象资源](https://web.hycdn.cn/endfield/official-v4/_next/static/media/endministrator1.c391b13d.png)，来自官方干员列表的 `endministrator1` 项 | 2026-09-28 14:18 | 官方公开展示；未核实素材再分发许可。 |
| `endministrator-2.png` | [官网男性形象资源](https://web.hycdn.cn/endfield/official-v4/_next/static/media/endministrator2.5ccb44a8.png)，来自官方干员列表的 `endministrator2` 项 | 2026-09-28 14:18 | 官方公开展示；未核实素材再分发许可。 |
| `sunna-official.jpg` | [官方 Sunna 宣传图](https://fastcdn.hoyoverse.com/content-v2/nap/162458/602ac606a731adcf956138553d842a82_4195420698196405542.jpg) | 2026-09-28 14:21 | HoYoverse 官方公示角色图；未核实再分发许可。 |
| `aria-official.jpg` | [官方 Aria 双形态档案图](https://fastcdn.hoyoverse.com/content-v2/nap/161813/e2b54a9cc44d5d4c0af1b105696c8b0a_4372999720764701032.jpg) | 2026-09-28 14:28 | HoYoverse 官方公示角色图；未核实再分发许可。 |
| `aria-official-intel.png` | [官方 Aria 情报摘要图](https://fastcdn.hoyoverse.com/content-v2/nap/162807/646b8f2d05bb581370f5887bdefd087c_1856467738146987404.png) | 2026-09-28 14:28 | HoYoverse 官方公示角色图；未核实再分发许可。 |

## 方法、访问限制与未决事项

已使用 anysearch 的领域能力发现及批量检索，并按 research 工作流追溯到官方页面与其公示资源。gaming 的现有垂直入口为电竞数据和 Steam 商店，不适合角色视觉核对，故使用普通检索。AnySearch 本身成功返回搜索结果；用户 Wiki 的直接打开被访问限制阻止，AnySearch extract 同样失败，已保存 `aria-wiki.json`。之后读取到该 URL 的搜索索引正文，并用官方档案图及情报摘要交叉确认身份与形态，不把索引缓存当作完整当前 Wiki。

HoYoverse 页面通过普通 HTTP 返回客户端壳，正文/图片由搜索索引与官方 CDN 资源补足；未使用二手图库图片作为最终外观依据。视觉描述来自实际 `view_image`，不是图片搜索生成的摘要。没有从压缩宣传图测量精确颜色，也没有声称身份还原、透明度、SVG 结构或视觉验收已经通过。

性别、Aria 形态、DeepSeek 表达层次及存放位置的原始歧义已由用户后续选择解决。本轮仍需通过真实成图和用户反馈确认近景程度、局部识别特征取舍及管理员面罩适配是否满意；这些不是尚未回答的性别/形态问题，不应重复询问已经选定的分支。
