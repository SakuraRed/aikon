# 男性 Endministrator：条件式分支 prompt

状态：`both-branches-authorized`。`entity_id=endministrator-male`；`question_id=male_mask`；`answer_status=answered`；`chosen_branch=both`；[answer_evidence](../../validation/2026-09-29-live-native-answers.json)：原生回答“两种都画”。先读 [index.md](index.md)；分别实例化 masked/unmasked，各有 short/full；不将分支选择记为视觉接受。

## 1. 独立实体绑定与本次看图

证据主档：[男性实体研究](../../research/entities/endministrator-male-evidence.md)。本次直接查看下列原图，独立核对偏扫短发、mask 遮挡和颈领，不以女版减去发卡构造男版。

| ID | 实际查看的本地原图 / 原始来源 | 绑定角色与使用范围 |
| --- | --- | --- |
| M01 | [男性官网立绘](../../../ref/subjects/endministrator/research-male/official-male-full.png) / [官方 CDN](https://web-static.hg-cdn.com/endfield/official-v4/_next/static/media/endministrator2.1ec20a16.png) | 当前官网 `endministrator2`；男性正常佩戴、头发与衣装主依据。 |
| M02 | [官方 A 人物卡](../../../ref/subjects/endministrator/research-male/official-profile-a-male.jpg) / [官方帖子](https://www.taptap.cn/moment/733759398467338301) | 实看卡面 A 为男性；较大头颈区域可核发流与领口层次。卡面注明开发中版本。 |
| M03 | [0305 原图](../../../ref/subjects/endministrator/research-male/official-campaign-unmasked-duo.jpg) / [官方 CDN](https://web-static.hg-cdn.com/endfield/special/over-the-frontier/assets/imgs/0305.c08e09.jpg) | 男性在画面左侧，为朝画面右方的侧脸；可见一眼、额发、后颈短束和领口。 |
| M04 | [0212 原图](../../../ref/subjects/endministrator/research-female/official-gallery-0212.jpg) / [官方 CDN](https://web-static.hg-cdn.com/endfield/special/over-the-frontier/assets/imgs/0212.cb69d9.jpg) | 男性位于画面中央，偏正面，两眼可见；无面具发眼关系及服装交叉依据。 |
| M05 | [抑制器展示原图](../../../ref/subjects/endministrator/research-male/official-suppressor-display.jpg) / [官方商店](https://store.gryphline.com/products/arknights-endfield-light-up-table-display-powercore-series-originium-suppressor) | 此文件与本次已看的女性研究目录装置图 SHA-256 相同；用于中央/侧片搭接，不采用底座、纹理、宣传文字。 |
| M09 | [女性 B 对照卡](../../../ref/subjects/endministrator/research-male/official-profile-b-female-comparison.jpg) / [官方帖子](https://www.taptap.cn/moment/733768935786154113) | 只用于确认 A/B 和发型/银色发卡差异；任何女性零件均不进入男性形态表。 |

装置名称与稳定生命体征用途沿用[已保存 M05 文字证据](../../research/entities/endministrator-male-evidence.md#可确定的结论与边界)，本次未重新联网。原始 URL、时间、哈希与权利见[男性 provenance](../../../ref/subjects/endministrator/research-male/provenance.json)，M04 见[女性 provenance](../../../ref/subjects/endministrator/research-female/provenance.json)。

## 2. 男性特征、可简化处与 unknown

全部左右指各原图画面坐标；新姿态须重新投影，不把此坐标直接当角色解剖侧别。

| 特征 id | 必须保留的可见关系 / 来源 | 可简化 | unknown / 不得写成已证事实 |
| --- | --- | --- | --- |
| M-hair-crown | 深灰黑短发；蓬松冠顶偏心汇聚，顶部与两侧存在成组外翻短尖束，后颈仍是短束而非齐颈 bob。[M01/M02；M03 补侧后观察] | 合并同向细发丝；保留长短不一的轮廓群 | 后脑全周结构与完整发根布局未知；不编造成均匀圆球或等距锯齿环 |
| M-hair-front | M02 一大组弧形刘海向画面左侧扫落，另一组较长尖束沿画面右侧太阳穴下落；分流与遮挡不对称。[M02/M01；M04 交叉] | 用几个宽主面表达扫束及交叠 | 不能把 M03 侧脸投影直接贴到正面；不以女性 bob 减一片或剪短冒充 |
| M-accessory-boundary | 已查看 M01/M02/M03/M04 未见女性那组银白多片发卡；M09 仅为女性对照。[M01–M04/M09] | 不新增无证据附件 | 不推断所有时期绝无附件；耳旁暗连接的完整归属/隐藏结构未核，不命名成自创耳饰 |
| M-mask | 暗色硬质面罩完整覆盖双眼、中央下探鼻梁区；向额部延伸的两侧长片、黄色线/连接和浅色小连接段；刘海遮住部分上缘。[M01/M02；M05 补结构] | 省掉密集面板线与商品织纹；保持中心脊/侧片/接点 | 图上眼睛被遮住，眼色未知；不由商品展示断言实际材质或游戏摘除条件 |
| M-face-eye | M03 可见一只青蓝/青色眼，M04 两眼青蓝；未见眼镜；偏扫刘海和眼位共同界定脸域。[M03/M04] | 风格化为无嘴鼻圆润脸域与暗色 capsule | 当前游戏 3D 精确 sRGB、瞳孔细节、全时期稳定眼色未知；不写“官方纯黑眼” |
| M-collar-inner | 下巴后方暗色高领，外侧灰白立领/罗纹领带前方拉链；浅色内搭上胸有结构缝。[M01/M02；M03/M04 交叉] | 罗纹以少量连续起伏概括，保留领口开合 | 隐藏接缝与真实面料未知；不换成任意衬衫白领或领带 |
| M-collar-fastener | M01/M02 领前偏画面左侧有银灰环状扣件及下垂长环/连接，位置低于内高领，并与外领形成前后关系。[M01/M02] | 概括环的孔洞与搭接、接点，不复制小螺丝 | 隐藏锁扣机构未知；不把环压成通用胸章；不复制女性前橙块作为男性事实 |
| M-collar-outer | 深色外套领翼向两侧上翻；画面右侧较大的黄色折角肩胸部件带固定件，压在黑灰外层之上，内侧为浅色内搭；左右不同形不同色。[M01/M02] | full 只留取景内领翼、黄折角与接点，省略腰部/手/武器 | 隐藏肩背结构未知；黄色不是任意点缀，背景长黄带不是衣片 |

## 3. 分支前提与条件式增量

### `masked`：只有真实答案选中本分支后生效

前提：`male_mask` 的真实答案为“保留面具”，或“两种都对照”中的 masked 子分支。以 M01 为当前形象主依据、M02 补头颈细节；M05 只补分件。生产 prompt 登记对源“两眼全露”的明确例外，不能为了眼形规则改抑制器佩戴位置。

```text
主体为男性 Endministrator，以 M-hair-crown 和 M-hair-front 独立建立男性短发。
保留偏扫主刘海、长短不同的冠顶/鬓侧外翻组和后颈短束；不复制女性 bob 或发卡。
Originium Suppressor 正常覆盖双眼并下探鼻梁区，主中央分面、向上侧片、浅色
连接段与小黄连接互相搭接；额发压住其部分上缘，侧片不是漂在额头上的 M 符号。
装置不透明；被挡眼睛不露出，不把装置上移/压薄/镂空，也不在面具表面另画眼。
本分支因真实用户选择覆盖源两眼可见默认；仍不画嘴鼻或从商品图带入织纹。
```

### `unmasked`：只有真实答案选中本分支后生效

前提：`male_mask` 的真实答案为“不戴面具”，或“两种都对照”中的 unmasked 子分支。`reference_basis` 当前未实例化：M04 提供偏正面双眼，M03 提供侧面发眼关系；若目标为当前游戏 3D，需先补可定位的官方帧与版本。既有官方视频入口没有已查看帧，不能写成完成核验。

```text
主体为男性 Endministrator；完全移除抑制器及其额部延伸件，不转成额饰。
按已绑定的官方无面具参考建立偏扫额发、两侧短束、可见眼位与下颌关系。
M04 只取画面中央男性，M03 只取画面左侧男性；不能取女性发卡/齐颈轮廓。
记录 M03/M04 所见青蓝/青色眼部，再映射为深色低饱和 capsule 材料，底色和
边缘色在 paint plan 单独保存为创作值。不得从 M01/M02 遮眼图或图库标签猜色。
眼形使用 index 的 capsule 侧边/端帽/眼对规则；不画虹膜、眼白、独立反光点。
已查两幅无面具图未见眼镜，故不新增眼镜来补辨识度；不推广为所有版本事实。
```

### `both`：只负责展开，不混合两种佩戴状态

真实选择“两种都对照”后，分别保存 masked 与 unmasked 合同，每份各有 short/full。共同沿用独立男性发型和同一已绑定服装版本；面具遮挡是明确变量。无面具证据缺口不能借 masked 资料填平，也不能借双分支名称自动开始 4 图。

## 4. 每个已选分支的 short / full 增量

| profile | 要写入生产 prompt 的具体内容 | 与另一版的实际差异 |
| --- | --- | --- |
| short | 紧裁切头像，保留冠顶偏心体积、向画面左侧扫落的大组弧形刘海、另一侧太阳穴长尖束和侧后短外翘；概括细发丝。masked 保留装置中心/侧片关系；unmasked 保留 capsule 完整轮廓与脸域。 | 靠男性自己的发流/轮廓及获答分支表现识别，不借女性发卡或新增眼镜。 |
| full | 同尺寸重构头—颈—上胸取景，实际露出 M-collar-inner、M-collar-fastener、M-collar-outer：暗内高领、灰白有前拉链的立领、前部相连金属环扣、两侧上翻外领、画面右侧黄色折角肩胸片及固定点。使下巴/后颈短发遮挡高领、高领连接前扣、前扣位于外套层之前的关系可辨。 | 新增来自男性官方图的服饰范围与连接，改变布局和底缘裁切；不能把 short 缩小后补通用领口或只增加几束头发。 |

full 的领翼、前扣和黄色折角来自 M01/M02；与 M03/M04 对照同类服装关系。为 pitch/roll 改投影时重新安置连接，不能对称复制外领、把黄色胸片换到任意空位，或把女性领前橙色构件照搬进男性 prompt。自然光泽随冠顶和扫束曲率连贯变化，短发不能变成均匀尖三角亮片。

## 5. 逐项交接与仍待补证

生产记录须将 `M-hair-crown / M-hair-front / M-mask 或 M-face-eye / M-collar-*` 对应实际 SVG 部件与渲染局部。short/full 都独立核发型，full 再核领口层次、前扣接合和黄色折角的部件归属。

仍未知：完整后脑/发根多角度、耳旁连接归属、当前游戏无面具 3D 近景与精确眼部、隐藏锁扣。没有成功观看的视频帧或完整动图不计证据；现存候选图不作为男性身份金标准。任何精确依赖这些未知内容的条款，先补资料后实例化。
