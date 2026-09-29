# Round 003 / endministrator-male / masked / short / r001

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

## 本次实际生产指令
任务模式：新主体风格迁移；不复制r1的身份，不复用旧管理员SVG或女性几何。
Entity：男性 Endministrator。reference_basis=official illustration。
真实决策：male_mask 原生回答“两种都画”；本文件只实例化指定分支，非用户验收。
先构建男性自身偏心冠顶、向画面左侧弧扫的大束刘海、画面右侧长短不一的鬓束、短后颈外翘；不用女bob或女发卡。
脸域依据刘海/太阳穴/侧颊和下颌关系独立绘制，仰头由额发压缩、眼线和宽阔下脸的投影关系表达，不以rotate替代pitch。
使用1280×1280透明画布、无水印、无描边框、无文字。产物为可寻址路径、局部gradient和clip的真实SVG；不得嵌位图、滤镜、噪声、量化碎片或采样trace。
上色：深灰黑材料底，宽幅中性偏冷柔光随发流连续变化；有真实交叠才产生暗分界，不贴尖三角高光；奶油面部宽缓暖色场；腮红弱粉色平面。
来源青蓝眼色在本次创作中映射为低饱和深青黑capsule；映射色不是官方RGB。
透明只属于画布，主体材料底不透明。阴影/光泽支持区属于真实材质，禁止游离亮片。
验收：静态向量检查、实际resvg渲染、1280/128/48/24观察、深浅底alpha与男女身份边界；结果保持候选待用户审计，不宣称99%。

本分支正常佩戴Originium Suppressor，完整遮住两眼，上沿被刘海部分压住。中央硬质分面下探鼻梁，下部成对面板、上伸侧片、浅色连接和黄色小接点互相连接。不得上移为额冠、半透明露眼、画替代眼或简化为黑横条。此用户选择明确覆盖源两眼全露默认。

构图：超近景，从左下方探入，头/脸左缘和下缘裁切，右上留透明；顺时针约15°。仅头，不显示胸衣。以5–7个主要宽发流面表达男性偏扫短发、成组不等长外翻轮廓，不以等距尖齿形成锯齿圆环。下巴超出底边，但两枚可见眼或完整mask主体保持在画布内。

实看证据与哈希见本轮references.json。未通过项目必须保留，不因CI或导出成功而宣告视觉通过。


## r002：基于实际可见缺陷的局部修正
基础版本：r001，SVG SHA-256 f5f4b8719b498d3d71e8af8f5705f97a9bbc7462f5887262adaccc60a0844710。r001源码、prompt、SVG和预览均已保留。
保留实体、分支、透明背景、同源眼对、装置位置及连续上色。将过高三叉冠改为不等长低幅发顶束，取消发顶的内部尖三角亮面；打散右侧等距外翘轮廓。主扫发及下降鬓束保持身份。
扩大连续发束色场可辨范围而不新增局部白亮点、云纹或贴片。再次实际渲染后检查全部四图大图、小图和深浅底；保留尚未解决的限制。
