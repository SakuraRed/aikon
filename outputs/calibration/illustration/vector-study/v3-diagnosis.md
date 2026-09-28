# v2 失真定位与语义重建 v3

本轮实际查看了两个 v2 的 SVG 重渲染图、重建的量化 RGBA，以及 v3 的来源分区图。没有把同源近似误差当成审美分数；v3 尚待主 Agent 实际渲染。

## 失真发生在哪一阶段

已按 v2 参数原样重放并保存：

- `diagnosis-simple-24-quantized-rgba.png` / `diagnosis-detail-48-quantized-rgba.png`：真正的 labels＋palette 颜色重建，保留源 alpha；阈值外的低 alpha 边缘仍用源颜色，单独观察颜色量化损失。
- `diagnosis-simple-24-vector-input-rgba.png` / `diagnosis-detail-48-vector-input-rgba.png`：再应用 v2 实际使用的眼部纯色替换、alpha 阈值轮廓和 253/255 主体 opacity。这是路径化前的栅格输入近似。
- 两份 `diagnosis-*-comparison.json`：以上中间图与原 PNG、实际 SVG 重渲染图的逐像素比较及局部 ROI。

数值是 sRGB 预乘 RGB 的通道平均绝对误差，范围 0–255。比较在各对图像的可见并集上计算；不同阶段的误差不可以直接相加，也不代表视觉好坏。

| 版本 | 源→颜色量化 MAE | 量化→路径输入准备 MAE | 路径输入→实际 SVG MAE | 源→实际 SVG MAE |
| --- | ---: | ---: | ---: | ---: |
| 24 色 v2 | 5.761 | 0.565 | 0.792 | 5.881 |
| 48 色 v2 | 3.518 | 0.443 | 0.672 | 3.803 |

24 色左腮红 ROI 的源→量化 MAE 为 **9.964**，路径输入→SVG 为 **0.566**。原像素 `(164,930)` 的颜色为 `(253,212,205)`，量化后已变成近肤色 `(252,238,229)`，SVG 重渲染沿用了后者。因此，腮红丢失首先是颜色分配问题，不是轮廓路径漏绘。

脸中央的硬白斑也已出现在 `quantized-rgba.png`，是把连续肤色变化分成少数硬色区造成的，不是 SVG 后续凭空添加的圆。

48 色发区异色有独立定位证据，见 `diagnosis-spurious-colors.json`：发区 `(801,567)` 原 RGB 为 `(139,123,134)`，高斯预处理后为 `(139,122,134)`，**未经 mode filter、连通域合并或路径化的 median-cut 结果已是 `(102,116,126)`**，之后仍保持该偏青颜色。该异常区域有 1,673 个匹配像素。当前全局调色板中最近颜色也是这个偏青色，说明该发色没有获得合适的色族表示；单纯检查路径方向不能修复它。

毛边和碎块同样大量存在于量化 RGBA。不过路径阶段并非无损：24 色有 18,235 个像素、48 色有 14,666 个像素的最大预乘 RGB 通道额外误差超过 20；这包含曲线简化、插值、重排、同色描边和重渲染抗锯齿的共同影响，尚未逐一分离。两版 alpha≥128 的轮廓 IoU 约 **0.999328**，只能说明阈值外形较接近，不能把内部色块的坏观感认证为合格。

结论：现有证据表明大白斑、丢腮红和主要异色首先来自全局量化；没有发现这些大块异常必须由轮廓转换 bug 才能解释。轮廓转换额外损失仍存在，不能据此宣称该算法完全正确。

## semantic-study-v3 的重建方式

新候选：[semantic-study-v3.svg](semantic-study-v3.svg)，247,013 bytes，19 个 compound path，另有 2 个独立眼部圆角矩形和 2 个腮红椭圆。19 是 XML path 数量，不是对象或独立轮廓数量。

这次没有增加全图调色板数量，而是将不同性质的区域分开处理：

1. **可见脸域**：从下半幅最大的浅暖色连通面提取实际可见区域，填回眼部孔洞，平滑边缘。结果为一个闭环、142 个曲线顶点，沿用了刘海、两颊发束和裁切形成的边界，没有换成大圆模板。
2. **脸色**：去掉全部皮肤量化色块，以很轻的真实 `radialGradient` 代替：中心 `#fdf4ec`、边缘 `#fdf2e8`。它是明确的平滑设计近似，不是逐像素复制肤色。
3. **双眼**：复用已经定位的两个深色组件，分别做 PCA 方向及投影范围拟合，生成独立 `eye-left` / `eye-right` capsule。采用 0.2–99.8 分位范围减少边缘噪点。两者中心约 `(323.63,810.65)`、`(709.38,988.51)`，共同纯色 `#25242d`。
4. **腮红**：在已知的本例局部窗口内提取偏红浅色组件，再以面积二阶矩拟合椭圆。`cheek-left` 中心约 `(172.97,920.61)`、半径 `(73.80,41.91)`；`cheek-right` 中心约 `(729.35,1125.35)`、半径 `(66.51,38.81)`。不再让腮红与全脸竞争全局 palette。
5. **头发、珊瑚束和青绿区域**：先按颜色家族分区，在各自内部选有限 4／5／4 阶，并按实际最近 RGB 重新分配，不允许全局 palette 把灰紫头发分到青绿家族。强一些的内部边界平滑和连通域门槛仅用于色阶面；外部 alpha 轮廓保留独立的高精度矢量 clip。

较大的色阶闭环数分别为头发 67、珊瑚 63、青绿 22；相较 v2 的数千量化环减少了大量碎片，但不等于每根发束已经独立建模。

## 不应过度解释的边界

- `semantic-study-v3-source-regions.png` 是来源分区调试图，已实际查看；它不是 SVG 的渲染证据。
- 这里的“语义”仍包含颜色规则和本例人工限定的腮红窗口，不是通用自动分割模型。青绿束发连接片与 halo 仍在同组，部分深色描边会归入头发。
- 脸色渐变、解析胶囊和椭圆是主动重建，不保证像素误差一定比所有 v2 指标更低。应分别检查形态平顺度、主体结构、同源误差，不能互相代替。
- 头发的长范围渐变、个别束发前后交叠，以及 halo 与束发连接片的独立编辑，可能仍需人工拆分／重画路径。没有宣称已获得生产级语义图层。
- 没有给 v3 伪造“像素通过”或“美术通过”。其 XML／真实矢量结构已检查，实际 SVG 画面等待主 Agent 重渲染。

## 复跑入口

```text
python tools/vectorize_calibration.py --input outputs/calibration/illustration/short-imagegen-v1.png --output outputs/calibration/illustration/vector-study/repro-diagnosis-24 --diagnose-log outputs/calibration/illustration/vector-study/vector-simple-24-v2.json --actual-render outputs/calibration/illustration/vector-study/vector-simple-24-v2-render.png --max-seconds 50

python tools/vectorize_calibration.py --input outputs/calibration/illustration/short-imagegen-v1.png --output outputs/calibration/illustration/vector-study/repro-semantic.svg --semantic-study --max-seconds 50
```

使用新输出名，避免覆盖。原有 v2 SVG／日志均未修改，原 PNG 未修改。本轮各工作有 55 秒调用方硬超时，内部预算 50 秒；v3 约 1.73 秒完成，没有浏览器、外部模型或新依赖。
