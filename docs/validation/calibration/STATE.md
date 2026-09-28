# 当前校准状态

用户已拒绝前一批全部产物；技术检查与视觉验收脱节是本次必须修复的过程问题。停止扩大主体数量。

当前固定案例：用户提供的 `img_1.png`，与强模式参考 `r1.png/r2.png` 和官方short样例共同对照。源参考黑底与水印仅从分析mask和目标中排除，原文件不修改。

并行任务：像素结构与mask指标；视觉轮廓/身份差距；源译文/运行prompt/代码执行的因果审计。未完成前不把猜测指标写成合格门槛。

实际用户否定：完全不合格。后续目标是修复观察到的结构/身份/曲线与色阶差距，并通过单案例真实对照与反馈，再恢复其他主体测试。

## 2026-09-29 进展与未答状态

- 像素诊断完成：眼部比例、眼对位置、脸域截面、mask敏感性与失败有可复跑证据。见 `pixel-analysis.md`。
- 三个真实中文prompt PNG实验已执行并保存实际prompt/image hashes；没有声称它们是SVG或经过语言因果验证。
- 全图量化矢量化失败已保留并拆分误差；semantic v4 使用真实path/gradient重建，已实际渲染，不含嵌图。它仍是候选。
- 独立纯代码short/full实验完成两轮，改正了部分可观察问题，但形态仍弱；不以结构检查替代审美。
- 原生 request_user_input 的本轮方向问题返回 `answers: {}`。没有取得用户选择；`retain_refine/png_detail/rebuild_identity` 都未被用户选定。禁止将Jev85%或默认高亮项写成批准。
- 不恢复批量，不将skill标为稳定或基线通过；后续从这个未答的单例方向继续。

当前审阅入口：`outputs/calibration/illustration/comparison.png` 和 `vector-study/semantic-study-v4.svg`。其对诊断PNG的alpha IoU只证明同源轮廓近似，不是视觉合格率。

清理限制：删除可复现中间目录 `pixels-complete` 的动作被自动审批审查以 `blocked by policy` 拒绝，目录已保留并加入Git忽略；最新结果以 `pixels-final` 和 `pixels-svg-v4` 为准。
