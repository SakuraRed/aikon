# 当前校准状态

用户已拒绝前一批全部产物；技术检查与视觉验收脱节是本次必须修复的过程问题。停止扩大主体数量。

当前固定案例：用户提供的 `img_1.png`，与强模式参考 `r1.png/r2.png` 和官方short样例共同对照。源参考黑底与水印仅从分析mask和目标中排除，原文件不修改。

并行任务：像素结构与mask指标；视觉轮廓/身份差距；源译文/运行prompt/代码执行的因果审计。未完成前不把猜测指标写成合格门槛。

实际用户否定：完全不合格。后续目标是修复观察到的结构/身份/曲线与色阶差距，并通过单案例真实对照与反馈，再恢复其他主体测试。

## 上一轮探索与提问历史

- 像素诊断完成：眼部比例、眼对位置、脸域截面、mask敏感性与失败有可复跑证据。见 `pixel-analysis.md`。
- 三个真实中文prompt PNG实验已执行并保存实际prompt/image hashes；没有声称它们是SVG或经过语言因果验证。
- 全图量化矢量化失败已保留并拆分误差；semantic v4 使用真实path/gradient重建，已实际渲染，不含嵌图。它仍是候选。
- 独立纯代码short/full实验完成两轮，改正了部分可观察问题，但形态仍弱；不以结构检查替代审美。
- 原生 request_user_input 的本轮方向问题返回 `answers: {}`。没有取得用户选择；`retain_refine/png_detail/rebuild_identity` 都未被用户选定。禁止将Jev85%或默认高亮项写成批准。
- 当时未恢复批量，未将skill标为稳定或基线通过。以下新反馈已给出继续方向，不再等待那道历史空答案问题。

当前审阅入口：`outputs/calibration/illustration/comparison.png` 和 `vector-study/semantic-study-v4.svg`。其对诊断PNG的alpha IoU只证明同源轮廓近似，不是视觉合格率。

## 2026-09-29 用户新反馈与上色迭代

- 用户明确认为后续图的整体是很好的典型，同时拒绝纹理和不自然高光；无需再次询问是否保留方向。获肯定的是整体构图，尚未认可最终 paint。
- DeepSeek 明确绑定 `ref/user-mode/r1.png` 的形象和模式，覆盖旧鲸鱼解释。
- 对照圈注、r1 和来源图建立 [反模式与像素证据](../paint-fields/README.md)，圈注实际对应 full 诊断图；保留 short 轻纹理尚不能可靠检出的局限。
- 上色器在 semantic v4 几何上重建显式色场。本轮没有调用绘图模型；几何仍继承前轮的模型辅助诊断与手工矢量重建，不能称全新几何生成已经脱离模型。
- v5 首次 E2E 抓到中央阴影距 receiver 边界 3px，超过固定 2px。v6 删除该无依据阴影，未放宽阈值；双版复测无机械规则失败，见 `outputs/paint-v6/illustration/`。中央发束因此偏平，仍需视觉校准。
- 不恢复其他主体批量；最终用户验收及跨 harness / 跨模型测试仍待完成。

清理限制：删除可复现中间目录 `pixels-complete` 的动作被自动审批审查以 `blocked by policy` 拒绝，目录已保留并加入Git忽略；最新结果以 `pixels-final` 和 `pixels-svg-v4` 为准。
