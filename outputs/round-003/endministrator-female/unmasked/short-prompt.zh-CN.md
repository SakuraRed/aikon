# r004：主Agent实际看图反馈对应修改

Base=r002 / unmasked / short
Base SHA-256=44d5d664758391edde84847c2f3fd96f26c54fa3ff896d38f982d01977784fb6

主Agent已看overview-r002并对照官方B卡：
1. 顶冠与左上扫额束的材料不连续，读成闭合亮片，缺乏真实发流依据。
2. 横扣过粗，叠接金属发卡读成十字格栅；需按原图细金属异长条和小横扣收细。

限定修改：顶冠与扫额主束使用同一个宽连续解析色场，使根部亮度不在
人工分组边界跳变。保留实际发际轮廓，不新画高光片或涂白整片头发。
发卡保持异长长条、短条、横扣、叠接及厚度，横扣厚度从17收至9，缩短
少量横向外伸；长条暗面、窄亮边在其自身局部坐标声明金属场，避免将
头部坐标渐变误用于附件局部坐标而变成平白符号。
面罩中央浅棱线/侧板黄色连接保留，正常遮双眼；不扩大到额冠。

保留：脸/眼/全部头发路径、masked和unmasked互斥性、独立short/full取景、
full官方领口/环扣/肩片、透明SVG。只在新的revision修改，不覆盖旧版本。
再跑实际渲染与像素检查；失败继续明示，不调低3px局部簇阈值。

## 上一版完整实际提示

# 实际看图后的 r002 修改提示

Base: r001 / unmasked / short
Base SVG SHA-256: e4dc3fd479dd095043dfbfeeea5228f31059e51b0e1b8eb2a3c645650566f67e

已实际查看 overview-r001 及 full 无面具、short 面具的1280原生渲染。
可见问题：额发接触阴影是横跨额头的厚桃棕色带，与真实发际不贴合；
大块上发区域受光过少、近似单色；发卡正面偏平白。full的环扣层级偏单一。

目标修改：
1. 移除该过厚且脱离实际发际的额头影带，改由脸部已有宽缓色场承接，
   不用另一条装饰带替代；中央/侧发的真实遮挡仍由形状顺序表达。
2. 仅给大块扫额与前发场建立连续径向宽光域，亮度受限于灰黑材质，
   不添加尖三角、点状白光、grain或细碎分片；侧发轮廓和主色归属保持。
3. 金属发卡保留异长多片几何，正面增暗中心和窄亮边表达原图可见厚度。
4. full在现有领扣下增加可辨且相连的第二长环层，保留真实孔洞；领口、
   橙件和黄色肩片来源不变。short无衣领。

Preserve：所有头脸轮廓、capsule尺寸与眼对、mask正常佩戴、bob身份、
short/full独立取景、透明画布、已获答both选择。不把格式或图形通过记为人类验收。
后续须重新渲染并实看1280/128/48/24、深浅底；保存源图和实际检查结果。

## 原始本图实际绘图合同

# 女管理员实际绘图合同 — round-003

任务模式：新主体风格迁移。reference_basis=official illustration。
真实用户决定：female_mask=both，原生回答“两种都画”；并非用户视觉接受。
不读取、不复制被拒绝的旧管理员 SVG；用语义贝塞尔面重新创作。

实际看图记录：F02/F09 为女性正常佩戴形态与服装；F05 只取左下黑发女性，
F06 只取右侧女性。两张无面具官方插画均见青蓝/青绿色眼部且未见眼镜；
仅据此作暗青灰 capsule 材料映射，不断言当前3D精确眼色。
F04 只补装置分件，不把商品正视摆放投影替代正常佩戴。
r1 仅迁移自然解析色场、胶囊与柔和仰头投影，不移植其蓝发、褶边或蝴蝶结。
r2 仅支持 full 具有真实颈领与服饰范围，不取其帽子。

女性身份：宽窄不同的额发与包颊短 bob、方向不同的外翘末端、很小的冠顶翘束；
画面左上鬓侧保留异长金属长条、近同向短片与横向扣片的叠接、切角及暗厚度。
不把发卡画成任意平面 X，不把女性几何用作男性默认。

画布1280×1280，透明、无水印、真实可编辑SVG。自然仰头由宽的下半脸、
上方收束发际及投影中的额发—眼线—下颌关系共同表达，roll约13度只负责
画面内倾斜，不能宣称测得唯一3D pitch。
脸为独立不对称轮廓，奶油暖白色宽缓径向场；不画鼻嘴、眉毛或写实眼眶。
头发是不透明底材上的少量连续 linear/radial 场，宽受光沿大束弧度分布。
不使用grain、滤镜、pattern、碎片量化描摹、位图、独立尖三角高光或云斑。
硬件可以有真实硬质转面，头发不借用金属切面。边界抗锯齿与材质内部区分。

先保存本提示词，再绘制。保存源码、原SVG、1280/128/48/24真实渲染，
检查深浅底和透明。看图后在新revision先保存修改提示，再修正。
格式/几何通过不等于审美接受，不标99%，所有最终候选等待用户审计。

Entity=endministrator-female / Branch=unmasked / Profile=short

完全移除抑制器及其侧件，独立保留女性多片发卡。两眼同源等形、互相平行；使用近直侧壁与半圆端帽的真正 capsule，short比约2.8:1、full约2.7:1。色相依据F05/F06映射为暗青灰，允许微弱连续眼材渐变和细窄一体边缘，不加虹膜、白点、瞳孔或眼镜。

short：头部和脸部大幅进入画面，左侧和下方自然裁切；脸域下半宽阔、下巴延伸出画布，右上透明。主要宽额发、两侧短bob、异长外翘端及身份硬件可辨，完全不画身体与领子。

## 完整源译文与许可（冲突按上述运行覆盖）

# Grokbot Icon 原始精简版提示词：简体中文完整研究译文

本文件是网页韩文原始提示词的忠实完整译文，不是功能摘要，也不是 Aikon 的独立生产指令。英文括注仅用于明确关键术语；未修改原文的奶油色脸、炭灰背景、15° 倾斜或单图输出要求。

生产执行前必须加载 Aikon 的[运行配置（runtime profiles）](../profiles.md)，由运行配置处理当前用户要求与源规则的差异。不得把本研究译文直接当作完整生产工作流。

## 来源与许可

- Original prompt: Grokbot Icon — short.
- Author: X [@multi_serio_ai](https://x.com/Multi_Serio_Ai) (APG).
- Original source: [Grokbot Icon Studio](https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans).
- Source license notice: [Prompt License and Notice on Rights in Generated Images](https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans/license).
- License: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
- Changes: Full Chinese translation of the original Korean short prompt, with English glosses for key terms and a separate research/runtime notice; no source rules intentionally changed.
- Translation status: Aikon 非官方研究译文，不表示原作者认可或背书。
- Source retrieved: 2026-09-28.
- Source SHA-256: `cb8b0ff7fd103eec7e4ec9ba8d2fa77106e0a73197257d09a8e666b4ee50dac2`.

本文件中的源提示词译文属于派生文本，按 CC BY-NC 4.0 使用；不得将其宣称为独立 MIT 许可文本。此提示词许可不自动覆盖示例图或其他第三方素材。

## 完整中文译文

将一同提供的图像重新诠释为极简 2D 机器人脸。原图中只保留发色、发型轮廓（hair silhouette）和代表性装饰。脸要大而圆，呈奶油色，脸颊带浅淡的椭圆形腮红。眼睛是两个大小相同、平行排列的黑色纯色竖向胶囊眼（capsule eyes），长度与粗细之比为 3:1。不画虹膜、眼白、反光、睫毛、眉毛、嘴或鼻子。画布为 1:1 正方形，使用纯色炭灰（charcoal）背景。采用从左下方探头窥入的超近景（extreme close-up）构图，头部顺时针倾斜 15°。脸和头发在左侧及下方画布边缘裁切（cropping），双眼完整露出，右上方保留背景留白。头发用大块形状表现，采用粉彩平涂（pastel flat color），将阴影和细节减至最少。不画躯干、手、武器、圆形边框、文字、标志（logo）或粒子。相比重现原图，优先保证胶囊眼和无嘴的机器人脸。生成一张图像。
