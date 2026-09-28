# 同主体 short 上色执行提示词

本轮保留已认可的整体构图方向，geometry锁定为 semantic-study-v4.svg，SHA-256: bc296c212317b4ecffaedadab125e135f5bf9f063bd0e6ba67e1999a48e83b6f。整体认可不等于源PNG的颜色纹理合格。

读取原立绘与用户r1、圈注，区分geometry与paint。只改paint：连续材料底色，可选单向低幅smooth gradient；每个遮挡阴影必须说明receiver/anchor与形体原因。去掉星形、尖多边形悬浮亮片、云雾杂色、全图量化痕迹，不复制位图的颜色噪声或半透明主体。不要用blur隐藏缺陷，也不要把full解释为加更多高光。

先保存并执行short.paint.json，调用标准库paint_svg.py导出真实SVG。默认不生成独立highlight patches；本案例未发现必须补加的高光，不需要为满足预算凭空添加。源short/full的其他语义和用户覆盖保留：透明背景、无水印、同一主体双版。主体内部不透明，边缘交由renderer抗锯齿。

在1024、128、48、24 px实际渲染，检查owner内色场、真实alpha与附件层次。CI可以拒绝噪声、孤立亮片的越界画法和几何漂移，不能代替人类判断高光是否自然。失败时保留本次结果并局部修正，不扩量。
