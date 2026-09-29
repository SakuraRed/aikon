# v5：统一使用上游 RGBA 的有界重跑

实际工作源为 `ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png`，SHA-256 `60c234f594ad81319fa74bb4fa8392f10a125127d46bf1d3b47e618b25813da2`；RGB 与 alpha 均来自上游 4096 方图的统一缩放，不继承旧截图 alpha。

几何线程按同算法实际重新提取 v5：manifest SHA-256 `8105b2e6d66b4ff7339302b59bd419df883cf033c0b0a663123989d404443769`。本次保存完整 PNG 来源快照、几何与全部 masks、拟合代码后，仅重新运行一次原参数拟合：白瓣 0.05、其他材料 0.35 简单模型选择容差；每面最多 5 色标；真实单条薄发缝按已记录的 solid-only 特例处理，完整报告误差。

无水印排除、无补绘、无验收阈值变化。不复用 v4 参数或预览 alpha，v4 的错误和局限继续保留。
