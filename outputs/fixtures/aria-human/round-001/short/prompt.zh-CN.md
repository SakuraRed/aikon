# Aria 爱芮：human / short

Round: fixture-aria-human。用户已选人形投影和机器人本体都测，分别执行short/full，存入outputs/fixtures；本轮没有用户审美接受。

主体证据：官方档案 https://zenless.hoyoverse.com/th-th/news/161813 ，已实际查看 `.local/fixtures/research/aria-official.jpg` 及官方情报图 `aria-official-intel.png`。本形态保留：粉红色卷双束发、青绿色额前卷绺和内层、黑色细长耳机天线；浅暖肤色。发丝化成有方向的大弧面。 原色HEX为目视设计值，不冒充官方色表。

强风格参考：已实际查看用户r1/r2；保留其大而偏低的胶囊眼、大块发/头壳、无口鼻圆脸、从左下探入的超近景。禁止移植参考角色的蓝发、帽子、女仆头饰；参考图黑底及水印按用户要求排除。

## 本profile完整中文源规则

将一同提供的图像重新诠释为极简 2D 机器人脸。原图中只保留发色、发型轮廓（hair silhouette）和代表性装饰。脸要大而圆，呈奶油色，脸颊带浅淡的椭圆形腮红。眼睛是两个大小相同、平行排列的黑色纯色竖向胶囊眼（capsule eyes），长度与粗细之比为 3:1。不画虹膜、眼白、反光、睫毛、眉毛、嘴或鼻子。画布为 1:1 正方形，使用纯色炭灰（charcoal）背景。采用从左下方探头窥入的超近景（extreme close-up）构图，头部顺时针倾斜 15°。脸和头发在左侧及下方画布边缘裁切（cropping），双眼完整露出，右上方保留背景留白。头发用大块形状表现，采用粉彩平涂（pastel flat color），将阴影和细节减至最少。不画躯干、手、武器、圆形边框、文字、标志（logo）或粒子。相比重现原图，优先保证胶囊眼和无嘴的机器人脸。生成一张图像。

## 用户要求与本次执行覆盖

输出自包含真实矢量SVG，512×512，background:null，透明区域不使用白底或棋盘格冒充；无水印、可见文字、logo、身体、手、武器。每round的另一profile须另行执行，不能仅复制标签。

short：15°，眼36×108，较少阴影与硬件细节；人形使用奶油浅脸，机器人保持浅色面板以免把机器人材质当肤色。 眼中心(102,373)/(284,373)，局部同y，随整个头部旋转；不画虹膜、眼白、反光、眉睫、口鼻。脸的左侧和下侧实际出框，右上保留连续透明空间。

Aria官方眼睛和表情按源规则替换为胶囊眼；机器人额板被重构到双眼上方，不能遮住胶囊眼。仅保留额板、耳片、天线与侧耳机的大连接，不复制卡面文字及背景。两形态使用不同的主体路径，不能把人形发色替换成白色后宣称机器人。

验收：helper结构检查后仍需真实渲染看近景、头发/硬壳辨识、双眼完整、透明度及小尺寸效果。结构通过不是视觉接受；user_acceptance保持pending。

## 提示词译改来源

Original author: X @multi_serio_ai (APG). Source: https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans . License notice: https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans/license . License: CC BY-NC 4.0, https://creativecommons.org/licenses/by-nc/4.0/ . Changes: Chinese translation, transparent dual-profile overrides, and Aria identity brief. Unofficial derivative prompt. 官方角色图仅研究对照，未宣称素材再分发许可，不复制到输出目录。
