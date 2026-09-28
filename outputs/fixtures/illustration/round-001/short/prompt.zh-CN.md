# 立绘图标生产提示词（内部草稿）

Round / Profile：fixture-illustration / short

主体（Subject）：用户本地立绘中唯一的女孩；名字、IP与官方身份未知，本次不联网识别。以当前立绘形态为准。

主体证据：已经实际查看 `D:\Downloads\aikon ref\img_1.png` 及只供观察的头部裁剪。可见深灰短bob、偏分的大块刘海；珊瑚粉大型侧束/花瓣状饰结与另一侧较小同色束；头顶青绿色椭圆环状halo，带明显尖角。珊瑚粉区域究竟是头发、独立饰物还是二者组合，未核实，因此只忠实保留可见轮廓，不给其编造材质与设定。

风格参考（Style reference）：已实际查看用户强模式 `r1.png`、`r2.png`。提取占满画面的极近脸部、左/下真实脸部cropping、大块流畅刘海、无口鼻的round bot face、低一些的完整capsule eyes、轻腮红与少量宽色面。风格参考的黑底与水印明确不进入产物；蓝发、女仆头饰和帽子属于参考对象身份，不移植给主体。

## 本profile的中文源规则

以下保留完整源译文作为可读基础；其中背景和单图交付由紧接其后的Aikon覆盖条款替换，不修改来源原文。

将一同提供的图像重新诠释为极简 2D 机器人脸。原图中只保留发色、发型轮廓（hair silhouette）和代表性装饰。脸要大而圆，呈奶油色，脸颊带浅淡的椭圆形腮红。眼睛是两个大小相同、平行排列的黑色纯色竖向胶囊眼（capsule eyes），长度与粗细之比为 3:1。不画虹膜、眼白、反光、睫毛、眉毛、嘴或鼻子。画布为 1:1 正方形，使用纯色炭灰（charcoal）背景。采用从左下方探头窥入的超近景（extreme close-up）构图，头部顺时针倾斜 15°。脸和头发在左侧及下方画布边缘裁切（cropping），双眼完整露出，右上方保留背景留白。头发用大块形状表现，采用粉彩平涂（pastel flat color），将阴影和细节减至最少。不画躯干、手、武器、圆形边框、文字、标志（logo）或粒子。相比重现原图，优先保证胶囊眼和无嘴的机器人脸。生成一张图像。

## Aikon覆盖与本次实际参数

生成一份自包含的真实矢量SVG作为本profile的作品，同时由同round的另一份生产指令产生另一profile；不可只交一版。`background:null`，不绘制背景矩形，halo内孔与右上negative space也必须为alpha透明。不要白底、黑底、内嵌棋盘格、位图或任何可见文字/署名/logo/watermark。

用自定义Bézier paths绘制此主体的bob、大珊瑚侧束和尖角halo，不套用其他角色模板换色。奶油色脸 #FFF0E0、柔和粉彩；深灰发色保持身份。胶囊眼 32×96，ratio=3:1，整头顺时针15°；比full更少的高光和花瓣细节。

512×512 viewBox。脸形局部范围约x=-94…421、y=144…589，实际左边和下边需出框；眼中心局部坐标为(98,374)、(270,374)。脸、头发、饰件、halo与双眼统一放在同一个head旋转组内。双眼等大且完整，不被刘海或halo遮住。眼位已下移，避免下半脸出现大块无意义空白。

保留（Preserve）：深灰短bob silhouette、珊瑚粉大侧束/饰结与青绿尖角椭圆halo三类身份线索；同一女孩、同一轮参考；短版/完整版各自真实规则。

变化（Change）：将原写实动漫人类眼口鼻转换为两枚solid dark capsule eyes及无口鼻圆脸。去掉身体、手、武器和服装装备；不是把这些物件误认成头部饰物。允许为眼部可见性与close-up调整头发/饰件的大轮廓位置，不新增身份特征。

验收：helper结构检查；两版分别真实渲染；在浅底/深底核对alpha；在24/48/128/512px查看眼形、眼遮挡、实际脸部左下裁切、halo内孔、三类身份线索和无水印。没有渲染前保持visual:unverified，用户接受为pending。内部过程保留在.local；用户已通过主线程选择仓库outputs/fixtures，最终两版按profile保存到outputs/fixtures/illustration/round-001。

## 原提示词译改来源

Original author: X @multi_serio_ai (APG). Original source: https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans . Source license notice: https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans/license . Prompt license: CC BY-NC 4.0, https://creativecommons.org/licenses/by-nc/4.0/ . Changes: Chinese source translation with English terminology, Aikon transparent dual-profile workflow overrides, and this local subject-specific production brief. This is an unofficial derivative prompt, not an independent MIT text. 用户本地图片未上传，也未复制进分发资源。
