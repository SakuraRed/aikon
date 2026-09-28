# 独立 Skill 消费者上色试用

2026-09-29。实际链路已完成：读取 Skill 与参考 → 先保存中文 prompt → 独立写 short/full paint plan → 编译 SVG → 四尺寸渲染 → 全材料 masks 与像素检查 → 查看结果 → 一次有界修正 → 重跑与复看。

结论：当前 Skill 足以指导这一例的独立上色计划与可复核输出，并实际暴露、阻止了一个没有通过边界规则的阴影。但最终图仍需美术精修，不能标记整张验收通过。它验证固定几何的上色消费链路，没有验证新主体几何理解或跨模型/跨宿主一致性。

## 最终产物

| Profile | 实际 SVG | 实际预览 | 独立计划 |
| --- | --- | --- | --- |
| short / r002 | [icon.svg](short/r002/icon.svg) | [深底](short/r002/preview-dark.png) / [浅底](short/r002/preview-light.png) / [128、48、24 px](short/r002/small-sizes.png) | [paint.json](short/r002/paint.json) |
| full / r002 | [icon.svg](full/r002/icon.svg) | [深底](full/r002/preview-dark.png) / [浅底](full/r002/preview-light.png) / [128、48、24 px](full/r002/small-sizes.png) | [paint.json](full/r002/paint.json) |

完整可机读记录见 [report.json](report.json)。第一轮及其失败仍保存在各 profile 的 `r001`。每份 SVG 都有编译报告、真实命令、renderer 元数据、全部 owner mask、实际可见面 mask、像素证据与 revision 说明。

## 输入与计划的独立性

本试用读取当前 `skills/aikon/SKILL.md`、profiles、paint-plan、paint-antipatterns、validation、versions，并实际查看用户完整反馈图、红圈图和 r1。此前任务已读取完整 short/full 源译文与本地韩文原文。没有读取 `tests/fixtures` 的现成 paint plan，也没有调用 imagegen、搜索新图片或上传参考图。

[short prompt](short/prompt.zh-CN.md) 与 [full prompt](full/prompt.zh-CN.md) 在 plan 之前实际落盘；各 `input-record.json` 保存 prompt 哈希和先后时间。r002 也先保存 `revision-prompt.zh-CN.md`，再保存修改计划。主体为现有 illustration；DeepSeek=r1 作为已确定绑定单独通过路径/哈希检查，本轮没有据此生成 DeepSeek 图，也没有移植 r1 蓝发。

基础 SVG 为 `outputs/calibration/illustration/vector-study/semantic-study-v4.svg`，SHA-256：`bc296c212317b4ecffaedadab125e135f5bf9f063bd0e6ba67e1999a48e83b6f`。本轮冻结其中选中的主面、眼睛、腮红、装饰和裁切几何。沿用基础 SVG 的眼尺寸差异、约 2.3:1 眼比例和约 22.7° 各自旋转；这不是按源 profile 重建几何，不能宣称 short 的 3:1 / 15° 等规则已经满足。

short 采用四个纯色主要材料面；full 保留相同几何，但四个材料面使用端点较接近、从左上往右下的单向线性色场。两版均选择零高光、纯色眼和腮红、少量有 receiver/anchor 的不透明阴影；这种差异来源于实际计划，而非复制同一 SVG 改名。

## 真实失败、修正与再验证

| 运行 | 几何锁与结构 | owner 检查 | paint 像素规则 | 后续 |
| --- | --- | --- | --- | --- |
| short r001 | 通过 | `center-fold-shadow` 失败 | 无规则失败 | 保留失败版 |
| full r001 | 通过 | 相同层失败 | 无规则失败 | 保留失败版 |
| short r002 | 通过 | 无规则失败 | 无规则失败 | 已实际看图，待精修 |
| full r002 | 通过 | 无规则失败 | 无规则失败 | 已实际看图，待精修 |

失败阴影在 1024 px 下的显著连通块面积为 35,610 px，最短 receiver 边界距离为 3 px，而当前合同阈值是 2 px。这个量只证明违反当前规则，不是物理光照的真值。实际局部查看也发现该暗片上端有独立贴片感。一次有界修正仅删除这一已有阴影片，不改路径或颜色，也不放宽阈值。r001/r002 四次导出的主布局 signature 相同。

剩余 15 个可绘制层全部实际参与 masks 检查；并未选取避开问题的手工小 ROI。可见材料 mask 按真实 SVG 绘制顺序扣除后绘层。像素分析使用 API 的原有 `grain_rms_max=0.85`、`mottle_rms_max=0.50`、`interior_translucent_fraction_max=0.001`；没有根据此次结果调参。

| 最终主面指标 | short r002 | full r002 |
| --- | --- | --- |
| 头发 grain / mottle，0–255 单位 | 0.00039 / 0.16185 | 0.05129 / 0.17625 |
| 青环 grain / mottle | 0 / 0.49824 | 0.06728 / 0.48528 |
| 全局支撑内部低于 alpha 254 的像素 | 409 / 783,662 | 409 / 783,662 |
| 全局该类像素占比 | 约 0.0522% | 约 0.0522% |
| 外缘疑似杂色像素，仅 advisory | 833 | 819 |

主面进入纹理统计的内部覆盖率约 44%–79%；其余主要因边界与后绘层排除，具体计数逐面保存。青环的纯色 short mottle 仍接近上限，说明这个诊断不是“真实噪声量”的无偏估计，几何/边界会影响残差。409 个低 alpha 支撑像素没有触发当前 0.1% 规则，并不意味着主体所有内部像素均完全不透明。没有将这些事实隐藏成“零缺陷”。

## 实际视觉审查

已查看 r001 大图与发区；r002 两版 1024 px 深浅底、透明展示、128/48/24 px 拼图及 full 发区局部。改善是清楚的：用户圈出的星状/尖碎高光与斑驳观感没有被沿用，灰发主面连续，双眼与整体近景仍可辨认，主要身份配色保留。

仍有下列可见问题，因此记录为 `completed_refinement_needed`：

- 中央暗片删除后，大刘海趋于整块，内部发束分组弱于用户认可的完整图。仅删除坏高光不够，下一步需要以真实发束边界重建必要层次。
- 青环保留的少数短阴影仍显拼片；“连接 receiver 边界”没有证明明暗自然。部分珊瑚回卷区域的细窄亮色带也需结合曲线关系再判断。
- v4 基础外发轮廓存在局部折点，环与侧束关系未重新校正。冻结几何可控制修改范围，同时保留了这些既有缺陷。
- 128 px 下双眼及主要配色较清楚，48 px 可读主要形状，24 px 中细部发流与环尖难以分辨；没有对小尺寸给出完美可读的结论。

原附件本身的造型优势没有被当前 v4 完整表达，本轮没有借 clean paint 的技术检查掩盖这一差距。主体身份尚无正式命名，本次只报告保留可见形态线索，不宣称 IP 精确还原。

## 执行命令、工具与资源

消费者入口为 [run_trial.py](run_trial.py)。以下步骤真实执行，全部在仓库根目录运行，Python 解释器为本地隔离的 `.local/ci-venv/Scripts/python.exe`：

```text
python -B -u outputs/agent-paint-e2e/run_trial.py prepare
python -B -u outputs/agent-paint-e2e/run_trial.py run --profile short --revision r001
python -B -u outputs/agent-paint-e2e/run_trial.py run --profile full --revision r001
python -B -u outputs/agent-paint-e2e/run_trial.py revise
python -B -u outputs/agent-paint-e2e/run_trial.py run --profile short --revision r002
python -B -u outputs/agent-paint-e2e/run_trial.py run --profile full --revision r002
python -B -u outputs/agent-paint-e2e/run_trial.py finalize
```

每次 run 实际调用 `skills/aikon/scripts/paint_svg.py`，随后调用 `tools/render_svg.py` 四次；完整 argv、cwd、退出码、stdout/stderr 保存在各版 `*.command.json`。渲染后实际调用 `paint_checks.check_geometry_lock`、`check_compiled_structure`、`raster_masks`、`ownership_checks`、`visible_material_contract`，并将真实 PNG 与可见 masks 传给 `analyze_paint_fields.analyze_image`。最终调用 `check_profile_pair` 与 `check_reference_binding`。

上色器版本为 0.2.0；固定 renderer 版本与工具源文件哈希见各版 `run.json`。四次完整编译/渲染/分析约各 5 秒。每个子命令硬超时 45 秒，外层隐藏进程受 180 秒 watchdog 约束；数值计算单线程，四次绘制串行运行。所有一次性子进程已退出，[收尾进程清单](process-inventory-after.json)为空，没有启动或保留服务，没有终止其他工作进程。

工具事件：short r001 的编译 stdout 因 Windows 子进程输出编码与 UTF-8 reader 不一致丢失，记录为 `null`，原 stderr 保留。实际 SVG 和 `compile.json` 已写入，随后结构、渲染和像素检查有独立结果。消费者 runner 增加 `PYTHONIOENCODING=utf-8`、`PYTHONUTF8=1` 后，后三次命令日志完整；没有覆盖首轮证据。

## 尚未证明

没有证明从任意原图自动得到正确 geometry；没有运行其他 harness/模型；没有进行韩文与中文 prompt 的受控对照；没有证明当前阈值覆盖所有纹理与高光问题；没有用户最终验收。本轮可确认的是技能消费、独立计划、实际编译和验证链路能够运行，并能将一次有证据的失败带入有限修正。
