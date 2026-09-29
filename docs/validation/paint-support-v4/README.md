# 材料支持域审计 v4

## 结论

旧 paint gate 没有足够依据把所有 mottle / island 报警解释为图像污染。本次补丁只补充可审计的支持域证据，**没有改冻结阈值、原 issues、原 status，也没有宣布 v004 通过材质或艺术验收**。

实际查看了 CETUS 4096 原图、v004 SVG 栅格，以及本目录的源图合同叠图。当前原图控制绑定 `ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png`，文件 SHA256 为 `60c234f594ad81319fa74bb4fa8392f10a125127d46bf1d3b47e618b25813da2`；与历史 `reference-paint-control.json` 的 decoded RGBA hash 一致。最初检查误用了 geometry 中遗留的 `r1-clean-calibration-1280.png`；该文件已弃用，现有报告全部重跑了正确 source，不以弃用文件作为结论依据。

## 已证实的机制

1. 全图 Gaussian 在不同材料之间借色。sigma=6、truncate=4 的真实有限核半径是 24px；旧算法 3px 区域内缩和内容相关的 12px 梯度排除，不能证明整核留在材料内。仅替换材料外颜色，64px 宽的相同线性场旧 mottle 从 0.15047 变为 0.18644；整核处的值两次均为 0.10137。
2. `near_edge` 由被测图片决定。面内异色岛、强噪声也会改变检测样点；32px 窄面注入噪点时旧算法只报证据不足，新支持域 grain 仍可测得 6.79291。新增证据不使用图像梯度排除面内缺陷。
3. 二次趋势不是任意合法 radial 的模型。独立的两端点、径向线性渐变会产生旧 island 和 mottle 报警。该控制仅证明模型适用范围，不能据此放行所有高对比高光；其局部弯曲本来就会产生带通能量。
4. 源图和候选的材料分割不能混用为独立真值。源图的 ahoge 根部、鳍与蝴蝶结交界、侧发边界等 residual 位置含有合法接缝／不同色场；候选 mask 没有完整遵循这些界面。见 [源图合同叠图](reference/contract-islands-overlay.png)：黄线是候选材料界限，红色只标出声明为 smooth 且发生报警的岛；不能把其解读为原图坏点。
5. 三条细折缝经 3px 内缩消失，属于缺乏不透明内区证据，不是已证实透明污染。没有通过删除部件、放宽 alpha 门槛或输出“干净”解决。

## v004 中三个 mottle 报警的定位

|材料|旧样点中缺少完整 49×49 支持的数量|完整支持处 mottle 样点|结果|
|---|---:|---:|---|
|whale-side-fin-rim|491|0|该尺度未评估；不能称干净|
|frill-white-03|1752|3|少于 64 样点；该尺度未评估|
|frill-white-05|4243|924|局部 RMS 0.1884，低于冻结 0.50；只支持这 924 个内部样点|

不能从这张表推断所有边界像素干净，或者把 v004 的原 fail 改成 pass。完整报告保留所有材料、所有不足范围和原失败，不重新抽取漂亮 ROI。

## 补丁与验证

`tools/analyze_paint_fields.py` 新增 `texture_support_evidence`：在当前分析网格上按真实 Gaussian 有限核检验支持，返回 grain / mottle 的样点数、材料覆盖率、旧样点越界数和未评估状态。两种尺度分别采用半径 6 / 24；阈值沿用当前合同。`maps.texture_support` 与 `save_evidence` 导出实际样点图。它是附加诊断，API 原有参数、判定和字段兼容。其有限核保证适用于已缩放的分析图；不声称重采样前任意参考几何的像素都准确，也不替代边缘、alpha、形状检查。

冻结规则文件 SHA256：`d35cd3475013a7e96d956cb6b268297f0bb0c3a8780886b19899e6b57496c71d`。`reference/report.json` 和 `candidate/report.json` 的 `legacy_rules_unchanged` / `legacy_issues_unchanged` 均为 true；两个 decoded source hash 均与各自历史报告一致。历史 v004 文件没有改写。

12 个独立控制覆盖宽／窄 solid、linear、radial、细面、grain、mottle、色岛、alpha；见 [控制板](controls/controls-board.png) 和 [实测数据](controls/report.json)。窄 radial 的 mottle、6px 细面的两个尺度都保持明确未评估。噪点、云纹、色岛及 alpha 注入均被相应证据捕获。

实际命令：

```text
python -B -m unittest tests.test_paint_fields tests.test_paint_field_support tests.test_paint_svg -v
```

34 项通过，10.915 秒；外层 subprocess 硬超时 45 秒，结束码 0。包含八张既有真实参考回归；此前冻结正负预期保持不变。

独立重现（脚本每次自带 45 秒硬超时；按模式串行）：

```text
python -B docs/validation/paint-support-v4/run_audit.py --mode controls
python -B docs/validation/paint-support-v4/run_audit.py --mode reference
python -B docs/validation/paint-support-v4/run_audit.py --mode candidate
```

## 尚未解决

- 窄材料的低频污染不能用无样点的二维核认证；需要另行验证的沿材料方向测量或更高分辨率证据，并保留污染注入敏感性。
- 任意 radial、自然光泽与“不自然高光”之间没有自动审美分类器。已知模型无法解释的结果需要明确模型假设及人工视觉检查。
- 原图材料 mask 不是独立金标准；需先修正语义界面，再讨论 source 对照的部位结论。不能照候选改 source 真值，也不能用“source 也失败”删除 candidate 的真实缺陷。
- 本次不增加 CI 平台，也不把上述诊断替代图像验收门禁。
