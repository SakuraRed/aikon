# 女性 Endministrator：条件式分支 prompt

状态：`both-branches-authorized`。`entity_id=endministrator-female`；`question_id=female_mask`；`answer_status=answered`；`chosen_branch=both`；[answer_evidence](../../validation/2026-09-29-live-native-answers.json)：原生回答“两种都画”。先读 [index.md](index.md)；分别实例化 masked/unmasked，各有 short/full；不将分支选择记为视觉接受。

## 1. 独立实体绑定与本次看图

证据主档：[女性实体研究](../../research/entities/endministrator-female-evidence.md)。本次直接查看下列保存原图，并核对发卡、遮眼关系及颈领细节；编号沿用主档。

| ID | 实际查看的本地原图 / 原始来源 | 绑定角色与使用范围 |
| --- | --- | --- |
| F02 | [女性官网立绘](../../../ref/subjects/endministrator/research-female/female-official-full.png) / [官方 CDN](https://web-static.hg-cdn.com/endfield/official-v4/_next/static/media/endministrator1.ec409283.png) | 当前官网 `endministrator1`；主形态、正常佩戴、服装。海报背景和持物不迁入 icon。 |
| F09 | [官方 B 人物卡](../../../ref/subjects/endministrator/research-male/official-profile-b-female-comparison.jpg) / [官方帖子](https://www.taptap.cn/moment/733768935786154113) | 实看卡面为女性 B；头颈范围更清晰，支持多片发卡与领扣近景。文件在男性研究目录不改变其内容身份；卡面注明开发中版本。 |
| F05 | [0212 原图](../../../ref/subjects/endministrator/research-female/official-gallery-0212.jpg) / [官方 CDN](https://web-static.hg-cdn.com/endfield/special/over-the-frontier/assets/imgs/0212.cb69d9.jpg) | 女性是画面左下方、黑发带银色发卡的人物；不是右侧大幅灰发佩丽卡。无面具两眼、bob 与衣领依据。 |
| F06 | [0305 原图](../../../ref/subjects/endministrator/research-male/official-campaign-unmasked-duo.jpg) / [官方 CDN](https://web-static.hg-cdn.com/endfield/special/over-the-frontier/assets/imgs/0305.c08e09.jpg) | 女性在画面右侧；无面具眼部与服装交叉观察。此图发卡受遮挡/画法影响，不能据其不清晰删除发卡。 |
| F04 | [独立抑制器展示](../../../ref/subjects/endministrator/research-female/suppressor-official-front.jpg) / [官方商店](https://store.gryphline.com/products/arknights-endfield-light-up-table-display-powercore-series-originium-suppressor) | 分件关系补充；不能用商品摆放视角替代 F02 的佩戴投影，不带底座、logo 或织纹。 |

F03 官方文字称装置为 Originium Suppressor，并说明稳定生命体征用途；本次沿用[已保存文字证据](../../research/entities/endministrator-female-evidence.md#可立即纠正的事实)，未重新联网。精确 URL、获取时间、SHA-256、权利记录见[女性 provenance](../../../ref/subjects/endministrator/research-female/provenance.json)及[共享图片 provenance](../../../ref/subjects/endministrator/research-male/provenance.json)。

## 2. 身份特征、可简化处与 unknown

全部方向指各原图画面坐标；换姿态须重建投影，不擅自认作角色解剖左右。

| 特征 id | 必须保留的可见关系 / 来源 | 可简化 | unknown / 不得写成已证事实 |
| --- | --- | --- | --- |
| F-hair | 暗灰黑 bob 基础，长度到脸颊/颈侧；刘海有宽窄不同的分组，两侧带方向不同的外翘束，头顶轻微翘束。[F02/F09/F05] | 合并同方向细发丝；保留额发、包颊侧束、外翻末端的层级 | 背面完整发型、不可见发根位置、真实 pitch 角未知；不得从男版延长两束得到女版 |
| F-clip | F02/F09 画面左侧鬓侧上方；一条较长金属条，近同向较短层片，横向扣片相互叠接；异长端头、收束/切角、暗侧厚度与窄亮边。[F09 为细节主参，F02/F05 交叉] | 小螺丝和不可辨纹样可省；用少量相连面表达厚度 | 隐藏扣接结构、全部片数与工程比例未核；不得写确定三视图、任意平面 X 或两根等宽棒 |
| F-mask | 深色硬质装置横跨双眼，上缘受刘海遮挡；中央下探鼻梁区域，浅灰棱边与小黄连接件，侧部有向上延伸长片。[F02/F09；F04 补分件] | 去掉商品织纹、密集面板线；保留中心分面、侧片、连接与遮挡 | 带面具图不给眼色；展示商品不证明游戏材质配方或摘除机制 |
| F-face-eye | 无面具专题图有两眼与由刘海/包颊短发围出的脸域；眼部视觉色域青绿至青蓝；两幅均未见眼镜。[F05/F06] | 依风格转为圆润无口鼻脸域和暗色 capsule；保留源色相证据 | 当前游戏 3D 精确眼色、特殊瞳孔、所有时期是否戴眼镜未知；“未见眼镜”只限定这两图 |
| F-collar-inner | 暗色颈圈样内层、浅灰白有竖向起伏的高领、领前小橙色块与拉链/连接；浅色内搭胸前有结构缝和块面。[F02/F09；F05/F06 交叉] | 罗纹概括为起伏色面，不复制细密纹理 | 真实材质、不可见内层接缝未知；不能替换成通用白三角领或领带 |
| F-collar-fastener | F02/F09 画面右侧领前为多层银灰长环/椭圆扣具，连接高领前缘，和橙色小块是不同部件。[F02/F09] | 保留环的孔洞、相叠关系与接点，略去螺纹 | 隐藏开合机构与精确金属种类未知；不得压成一颗圆胸针 |
| F-collar-outer | 深色展开外领/兜帽，内面浅灰；F02/F09 画面右侧有黄色肩领片及小金属连接件，覆在浅内搭之外。[F02/F09/F05/F06] | 只保留进入 full 取景的领翼、黄片及接合；不加手、武器或海报线条 | 隐藏肩背剪裁未知；源图大范围黄色背景不是衣片 |

## 3. 分支前提与条件式增量

### `masked`：只有真实答案选中本分支后生效

前提：`female_mask` 的真实答案为“保留面具”，或“两种都对照”中的 masked 子分支；在生产 prompt 显式记录对源“两眼全露”的覆盖。以 F02 正常佩戴为主，F09 补可见头部细节，F04 仅补装置分件；本次已查看这些图，可见结构可用于风格化，未知内部件继续留空。

```text
主体为女性 Endministrator；保留 F-hair 与 F-clip，不移植男性短发。
按 F02/F09 正常佩戴 Originium Suppressor：硬质主体覆盖两眼并延伸到鼻梁区，
与刘海和侧发相互遮挡；保留中央分面、两侧长片、银灰边和小黄色连接。
它是具有体积的装置，不能抬到额头、压成黑条、变成 M 形额冠或普通墨镜。
面具不透明，被遮眼睛不画成外露 capsule，也不在面具表面补两只眼。
源 prompt 的双眼完整可见条款在本获答分支明确例外；圆润无嘴鼻仍适用。
女性银白多片发卡在本分支保留，按 F09 的可见叠接/厚度独立于面具构建。
```

### `unmasked`：只有真实答案选中本分支后生效

前提：`female_mask` 的真实答案为“不戴面具”，或“两种都对照”中的 unmasked 子分支。`reference_basis` 当前未实例化：F05 为较平静、双眼可见的官方插画主候选，F06 交叉观察；如目标要求当前游戏 3D，应先补带版本、场景和时间戳的官方近景。不能从 F02/F09 的遮眼像素填补该缺口。

```text
主体为女性 Endministrator；完全移除抑制器，不留下额饰或侧翼残片。
用已绑定无面具官方参考中的刘海、短 bob 包颊关系与下颌范围建立可见脸域；
F05 中只提取画面左下女性，不取佩丽卡的灰发、耳形或服饰。
女性 F-clip 仍保留，不因去面具而删除或退化为 X。
记录参考中的青绿至青蓝眼部观察，再将其映射成深色、低饱和的 capsule 材料；
实际底色与边缘色在 paint plan 保存，标记为风格化选择，不声称官方精确色值。
眼形遵循 index 的 capsule 几何，不保留插画虹膜、夸张睁眼表情或白色眼点。
F05/F06 未见眼镜，不新增眼镜；这不等于断言所有官方版本从不戴眼镜。
```

### `both`：只负责展开，不混合两种佩戴状态

真实选择“两种都对照”后，分别保存上述 masked 与 unmasked 合同，并各自生成 short/full。两套使用相同女性身份、发卡和已绑定服装版本；眼睛可见性和面具层不同。无面具证据前提仍独立成立，不因 masked 可执行而被跳过。

## 4. 每个已选分支的 short / full 增量

| profile | 要写入生产 prompt 的具体内容 | 与另一版的实际差异 |
| --- | --- | --- |
| short | 紧裁切脸域与女性 bob；宽主刘海、包颊侧束、外翘末端概括。保留发卡异长多片与厚度，在画面内留下可辨的叠接处；masked 时面具核心分面亦完整可识别。下缘以脸/侧发裁切为主，不靠任意领子补身份。 | 主内容为头部与关键配件；细发丝、服饰不占主要空间。 |
| full | 同尺寸重新设计头—颈—上胸取景，底部实际露出 F-collar-inner、F-collar-fastener 与 F-collar-outer：暗颈内层、浅罗纹领/前橙块、相叠长环扣、深外领浅内面、相接黄色肩领片；按 F02/F09 的连接关系投影。对应增加后发与颈领遮挡，发卡呈现相连转面。 | 增加完整可识别颈领结构与其接合，改变底缘裁切和内容范围；不能只缩小同一头像再画一片白三角。 |

full 的衣片左右以所绑定 F02/F09 投影为起点；为仰头/roll 改投影时仍保留部件归属，不机械照抄屏幕坐标。F05/F06 用于验证无面具与同类领装共存，不拼接另一人物的领口。金属扣/发卡可有硬质转面；头发采用连续柔和色场，不能借金属高光把头发画成亮片。

## 5. 逐项交接与仍待补证

生产记录必须将 `F-hair / F-clip / F-mask 或 F-face-eye / F-collar-*` 映射到实际 SVG 部件和渲染局部。short/full 都要检查 F-clip；full 另看领扣是否真的连在高领上、黄肩领片是否属于外套而非悬空三角。

仍未知：完整背发和发卡隐藏连接、精确发卡工程比例、当前版本无面具 3D 眼部与细节。缺失项不写成负面存在断言，也不拿官方专题插画升级为实机证明。任何当次要求涉及这些精确内容时，先补该项证据再实例化对应条款。
