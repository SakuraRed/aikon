# 实际SVG材料表示往返

输入是第二次独立Skill消费的真实最终SVG，不是为编译器特制的矩形。选择其 `face-parent`，把既有径向色场转成显式 `aikon.material-plan.v1`，由通用标准库编译器输出SVG，再分别用同一resvg渲染1280px。

`actual-render-evidence.json` 记录实际RGBA完全一致、最大通道差0；`compile-report.json` 记录原几何属性/坐标链、来源与输出哈希。`geometry.svg`、`plan.json`、`compiled.svg` 可审查并重现。旧渐变定义保留，未重排或猜测主体结构。

这证明该实际色场可经通用材料计划执行并保持显示，不证明图标更接近r1，不是新绘制候选，也不证明所有SVG和harness均兼容。多层边界与非默认transform另有真实渲染正负测试；support覆盖和最终视觉仍需单独验证。
