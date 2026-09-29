# Round 003：八张管理员 SVG 的 paint 域审计

**结论：取得可追溯的局部材料证据，八张原 paint gate 均保持 fail。没有全图通过、没有调阈值，也没有改作品。**

最终输入是男 r004 与女当前 r005 修复别名（女 unmasked short 保持 r004）；以每个文件的 `read_bytes()` SHA-256 绑定，见 [总表](summary.json)。这里的 mask 来自对应 SVG 的实际可见绘制归属，绝不借用旧角色 mask，也不是独立于候选的参考金标准。

## 可完成的范围

每个可见填充叶片分别渲染为白色，其余可见叶片黑色；保持真实绘制顺序、父级变换、clip、填充孔洞、stroke。`defs/clipPath` 的轮廓不是可见叶片；shared clip 内的 support 也必须先被后续叶片遮挡，才计算剩余可见域。颜色家族仅供看图索引，不能把各束头发或各个金属转面合并成一个 smooth field。

检测直接使用最终 SVG 的 1024 px 原生渲染，mask 与色图同网格，不额外进行 1280→1024 缩放。逐域调用现有 `analyze_paint_fields.py`，规则来自未修改的 `docs/validation/paint-fields/frozen-rules.json`：grain 0.8276688、mottle 0.50；原 alpha、island 规则同样不变。每图硬超时 45 秒，实际运行约 5–14 秒，串行执行。

独立合成控制核对了后绘制遮挡、组合变换、clip、孔洞露出下层、排除 defs、拒绝非不透明 paint，见 [ownership-controls.json](ownership-controls.json)。非不透明 gradient/shape、SVG mask 和未知 CSS 不会被当作不透明叶片强行盖色。

## 没有达成的 alpha 等价假设

首次强制逐字节 alpha 相同立即失败，诊断保留在 [alpha-recolor-diagnosis.json](alpha-recolor-diagnosis.json)：男 short 有一个外边界像素 alpha 207→206。八图完整结果为每图 **1–12 个外轮廓 AA 像素差 1 LSB**，原图向内 3 px 的不透明域差异为零。

因此报告全部保留 `ownership_alpha_equality_all_leaves=false`。后续仅纳入原图与重色图都完全不透明、重色结果完全白色的像素，并排除所有差异点的 49×49 邻域。任何不透明内区差异仍立即停止。这个保守排除使部分宽域可以继续提供证据，但没有把失败的 exact-alpha 检查改称通过，也不能认证被排除的边界。

## 覆盖与真实结果

分母为当前图完全不透明像素。后两列只统计单一 fill 色场、完整有限 Gaussian 核且至少 64 个样点；13×13 是 grain 支持，49×49 是 mottle 支持。数值不是相似度或审美分数。

|候选|逐形单一色场覆盖|可测 grain 覆盖|可测 mottle 覆盖|原 gate 问题数|
|---|---:|---:|---:|---:|
|female/masked/full|95.28%|60.89%|19.79%|46|
|female/masked/short|96.75%|75.67%|39.03%|25|
|female/unmasked/full|92.55%|63.04%|25.31%|33|
|female/unmasked/short|93.11%|76.55%|43.60%|13|
|male/masked/full|91.03%|55.84%|13.62%|24|
|male/masked/short|94.10%|68.20%|27.69%|10|
|male/unmasked/full|92.04%|61.22%|21.74%|16|
|male/unmasked/short|95.21%|74.88%|39.55%|2|

这些可测完整支持域内，grain/mottle 均未超过冻结阈值，已测内区的透明像素为零。八个脸域原 gate 均无规则失败。男性四枚无面具眼是单 fill 色场，其完整支持检查有样点；女性眼包含不同颜色的 fill 与 stroke，尚未拆成独立域，**不纳入严格单色场结论**。男性 full 两个长环也有 fill/stroke，按同样原则排除；其既有叶片诊断仍完整保留，不隐藏。

原 gate 的 fail 包含：发束/面罩部分 mottle 超线、发束/细金属/领部的二次残差色岛，以及细小件的 texture/opacity 样点不足。没有把全支持处的低 RMS 反推到缺乏支持的发尖、亮缘、细扣件。二次趋势也不是任意合法 radial 的完备模型，但本轮没有以此理由删除任何 island 失败。

## 实际看图

逐一实际查看了八张 `inspection-board.png`：原图、叶片边界/家族、完整核支持并排。脸域正确排除眼、腮红、头发和真实面具；发束边界随相应可见块面；full 服饰域遵循头、内外领、前扣与胸片遮挡；clip 内 support 没有作为漂浮矩形显现。

另实际查看男 unmasked short、男 masked short、女 unmasked short、女 masked full 的 `islands-overlay.png`。已见红色位置集中于发束收尖或搭接、薄金属和面具边缘；这只是位置观察，没有逐个证明为假阳性，也没有用视觉印象覆盖原失败。

每图目录保留：`candidate-1024.png`、`inspection-board.png`、`ownership-overlay.png`、`masks/`、`full-support-overlay.png`、`paint-report.json`、`summary.json`。总表绑定输入、renderer、分析器和冻结规则哈希，并记录未覆盖范围。

## 剩余限制

- 未认证边界混合像素、重色差异邻域、没有完整过滤核的窄域，以及 fill/stroke 未拆分的域。
- 面具、发卡、扣件等大量细部保持不足；不能据此称不存在噪声或污染。
- 身份、仰头、光泽的形体合理性和用户视觉接受不在统计门槛证明范围内。
- 本次只写 `outputs/round-003/paint-audit/`。八张原 SVG、提示词、CI 配置和检测器均未修改。未尝试清理此前被策略拒绝的缓存。
