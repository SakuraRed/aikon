# 男管理员 Round 003

当前候选为 **r004**，未获用户视觉接受。四张均为代码原创、自包含透明 SVG；身份依据是 **official illustration**，并非已核验的当前游戏 3D 模型。男女独立，未读取或复用旧管理员候选 SVG、女性代理几何。

| 分支 | 精简 | 完整 |
| --- | --- | --- |
| 不戴面具 | [SVG](unmasked/short.svg) · [PNG](unmasked/short.png) | [SVG](unmasked/full.svg) · [PNG](unmasked/full.png) |
| 正常佩戴 | [SVG](masked/short.svg) · [PNG](masked/short.png) | [SVG](masked/full.svg) · [PNG](masked/full.png) |

[同浅底总览（含真实 128/48/24 px）](overview-r004.png) · [深底复核](dark-review-r004.png) · [文件哈希与版本索引](current.json) · [质量报告](quality-summary-r004.json)

## 实际读取、观看与制作

完整读取 Aikon SKILL、short/full 两份源提示词、profiles、natural-gloss-v2、管理员分支 index 与 male 文件。实际查看官方男性立绘、A 卡、0305 中左侧男性、0212 中央男性、独立抑制器图、r1-working、r2；另看 A 卡头部裁切，明确源鼻梁与侧片关系。[references.json](references.json) 保存来源路径、哈希及逐图观察；裁切 `reference-mask-detail.png` 来自 A 卡 bbox `[380,230,710,565]`，仅用于放大检查。

四份实际生产 prompt 在 SVG 前保存，每次修改也先保存 revision prompt。代码在 [draw.py](draw.py)，各 `branch/profile/revisions/r00N/` 同时保留当次实际源码、prompt、SVG、PNG 和 generation 记录。`sourcecode.py` 是当次作者脚本的字节快照，记录的是原作者脚本目录的运行语义；不是独立安装包。最终 SVG 本身不依赖 Python 或参考图片。

short 为只有头的紧裁切；full 单独绘制头部控制点、下颌范围与衣装拓扑，新增暗内高领、灰白拉链立领、相连长环扣、两侧不同外领和黄色折角胸肩片。full 不是整个 short 的缩放组。无面具眼色从官方插画所见青蓝色映射为深青黑材料；所用 RGB 是创作值。

## 实看后的修订

- **r001 → r002**：实际看图发现 full 双眼和 short 右眼部分被刘海遮挡、三叉冠过高、侧发尖束过于均匀、接触投影过宽。修短向内尖端、调整 full 眼对、降低并打散冠顶轮廓，用真实发边裁切的窄接触阴影替代宽粉色月牙。初稿和失败记录保留。
- **r002 → r003**：再次看 A 卡及主线程审查后，加强抑制器中央下探、弯折脊线与上扬侧片；下移 full 灰白外领，使暗内高领可见。无面具 short 本轮像素不变，如实记录。
- **r003 → r004**：戴面具 short/full 的冻结边缘检查出现 9/8 像素局部坏簇。实际查看差分局部，定位于脸—窄黑缘—浅金属缘的近邻覆盖。中央材料和浅缘改为共用原轮廓 clip；修的是 SVG 色场支持与采样关系，未改 PNG、未调门槛。当前坏簇为 0/1。无面具两图本轮像素不变。

## 当前验证及局限

已实看四图大图、同浅底总览中的实际 128/48/24 px、深底总览；最终 masked 两图额外各看 1280 px。无面具两个 SVG 与已看 r003 完全相同。

四图通过静态允许 SVG 子集检查；每张 1280/128/48/24 重渲染与保存 PNG 的 RGBA 完全一致。当前冻结 256 px、4× 面积参照 edge 检查均 `no_rule_failure`，无内部 alpha deficit。无面具四枚眼从**最终图真实暗连通域**提取，胶囊轮廓检查均 `no_rule_failure`；masked 不生成眼，记录正常遮眼例外。

这些结果不等于完整美术验收：本轮没有独立金标准材质区域掩膜，paint-field 自动判据保持 **not assessed**；无噪声构造和肉眼未见斑纹不能代替该项。发顶/发流仍是较强的图标化概括，面具脊线和衣领也是简化后的结构表达；自然仰头观感、身份接近程度、光泽是否达到用户目标仍待人工审计。未声称 99%、无瑕或跨模型一致。

哈希分清原始 SVG 文件字节与 Windows 文本读取后的换行标准化文本：generation/current 的 SHA-256 是原文件；edge 的 source_sha256 是归一化文本。质量摘要同时记录两者，禁止混用。

官方素材仅作私有研究，未宣称额外再分发许可。完整 prompt 中保留 APG / @multi_serio_ai 的 CC BY-NC 4.0 原始研究译文归属。
