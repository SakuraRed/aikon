# 千夏 Sunna 生产提示词

Round / Profile：fixture-sunna / short

主体（Subject）：用户输入“绝区零的千夏”。采用HoYoverse官方公示图上的Sunna基准形态。中文名对应关系由研究Agent核对官网，绘图Agent已亲自查看官方图片；不借用其他动漫人物外观。

主体证据：官方来源 https://zenless.hoyoverse.com/fr-fr/news/162458 ，本地只读参考 `.local/fixtures/research/sunna-official.jpg`。实际可见浅鼠尾草绿头顶发色、较深青绿下层、淡紫卷曲发梢；头部右侧高马尾，根部有高而尖的薄荷绿几何蝴蝶结；额前黑/粉色发夹和交叉细条组成不对称识别组。主色是目视估计，不冒充官方精确HEX。发夹的微小符号不够清楚，不猜文字或图案。

风格参考（Style reference）：实际查看用户r1.png/r2.png；采用其extreme close-up、大块curved silhouette、完整而偏低的capsule eyes和左/下脸部cropping。只将其黑底/水印从风格目标排除；蓝发、女仆头饰和帽子属于参考人物身份，不能移植。

## 本profile完整中文源规则

以下源文用于可读溯源；背景和单图工作流由后面的Aikon覆盖明确替换。

将一同提供的图像重新诠释为极简 2D 机器人脸。原图中只保留发色、发型轮廓（hair silhouette）和代表性装饰。脸要大而圆，呈奶油色，脸颊带浅淡的椭圆形腮红。眼睛是两个大小相同、平行排列的黑色纯色竖向胶囊眼（capsule eyes），长度与粗细之比为 3:1。不画虹膜、眼白、反光、睫毛、眉毛、嘴或鼻子。画布为 1:1 正方形，使用纯色炭灰（charcoal）背景。采用从左下方探头窥入的超近景（extreme close-up）构图，头部顺时针倾斜 15°。脸和头发在左侧及下方画布边缘裁切（cropping），双眼完整露出，右上方保留背景留白。头发用大块形状表现，采用粉彩平涂（pastel flat color），将阴影和细节减至最少。不画躯干、手、武器、圆形边框、文字、标志（logo）或粒子。相比重现原图，优先保证胶囊眼和无嘴的机器人脸。生成一张图像。

## Aikon覆盖与本次参数

当前round必须有short和full两版，本指令生成short.svg。最终为自包含真实矢量SVG，background:null；不画背景矩形、棋盘格或白底，不嵌入raster。不要卡面框、名称文字、商标、署名、水印、武器、身体、手、服装或卡片上的贴纸。

奶油色脸#FFF0E0，柔化的sage/mint粉彩配色，整头15°，眼32×96（3:1），发夹只保留大形和交叉条，不画小凹槽。

采用全新为Sunna画的Bézier发型/脸/马尾路径，而非其他角色头像换色。512×512；眼中心(108,375)/(278,375)，与头部共同旋转，保持同尺寸同色、两眼中心连线垂直于胶囊长轴。双眼不带虹膜、瞳孔、眉、睫毛或高光，脸无口鼻。大脸实际穿过左侧与底部边界；视图右上保留连通透明空间，高马尾和几何蝴蝶结不能挤掉双眼。

保留（Preserve）：sage发型与单侧高马尾（含青绿下层/淡紫发梢）；高薄荷绿几何蝴蝶结；不对称发夹组，共三类身份线索。

变化（Change）：从官方卡面角色转成无口鼻机器人头像，删除人类眼睛及非头部内容；把发丝、渐变和反射重构为少量flat color大块，保留辨识轮廓。本轮尚无用户局部修改或审美批准。

验收：两版分别helper check，随后真实渲染并检查alpha、浅/深展示底、24/48/128/512px眼部和身份可读性、真实脸部cropping、发夹不似眉毛、无水印。未渲染前visual与raster alpha均unverified，user acceptance=pending。用户已选outputs/fixtures，以profile分开保存不可覆盖revision；不改写本地原图。

## 提示词译改来源

Original author: X @multi_serio_ai (APG). Original source: https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans . Prompt license notice: https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans/license . License: CC BY-NC 4.0, https://creativecommons.org/licenses/by-nc/4.0/ . Changes: Full Chinese source translation with English terminology, Aikon transparent dual-profile overrides, and the official-reference Sunna production brief. Unofficial derivative prompt, not an independent MIT text. 官方参考图片的再分发权限未确认，原图不进入输出目录。
