# 单例 PNG → 可编辑 SVG 技术实验

输入为上一层的 `short-imagegen-v1.png`，1254×1254 RGBA。该图是生成式绘图得到的诊断目标，不是用户验收的 gold，也不是 SVG 成品。此实验检验代码能否更忠实地保留其轮廓和色阶，不评价 IP 还原是否已合格。

原 PNG 未修改，SHA-256：`1980caf7a44e71f01316cc4db54e1cb72add25cb315bd09a117c2231b7a78126`。

## 本轮候选

| 近似级别 | 文件 | 调色板 | 小色区合并阈值 | 边界容差 | Compound paths | 曲线顶点总数 | 文件大小 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 较简 | [vector-simple-24-v2.svg](vector-simple-24-v2.svg) | 24 | 64 px | 0.85 px | 28 | 23,834 | 796,345 bytes |
| 较细 | [vector-detail-48-v2.svg](vector-detail-48-v2.svg) | 48 | 24 px | 0.55 px | 52 | 71,826 | 2,443,964 bytes |

这两级不是 Aikon 的 short/full profile。每个颜色 path 可以包含多个不相连的闭合子路径：较简包含 912 个调色板轮廓环，较细包含 2,795 个。它们具备实际矢量节点和独立眼部 ID，但不能把“28／52 个 path”误说成只有那么多个简洁物件。

尚未在本子任务渲染；实际渲染、对同一 PNG 的像素比较和美术判断由主 Agent 进行。当前只完成 XML／纯矢量结构及轮廓原始有向面积检查。

## 方法与实际参数

环境中未找到 vtracer、potrace、Inkscape 的已有命令／对应 Python 模块；没有安装新工具。实际使用现有 NumPy、SciPy 和 Pillow。

处理顺序：

1. 将 alpha≥128 作为主要可见轮廓。保留 halo 内孔；本图没有因 alpha 小连通域阈值而丢弃像素。
2. 对 RGB 做 alpha 加权 Gaussian 平滑，较简 sigma=0.95，较细=0.7；透明背景的黑色不会直接混入颜色平均。
3. Pillow median-cut 无抖动量化为 24／48 色。
4. 使用 3×3 标签 mode filter 减少像素噪声，再将小于阈值的 4 连通色块并入最近的保留色区。只合并颜色，不改变主要 alpha 轮廓。
5. 对像素单元边界构建有向闭环，外环／内孔一起提取；简化前检查环的有向面积与源 mask 像素面积严格相等。
6. 对闭环做循环平滑和 Ramer–Douglas–Peucker 简化；使用保留尖角、限制手柄长度的 cubic Bézier 插值，避免保留逐像素阶梯。不是把原 PNG 包装进 SVG。
7. 用真实矢量 `clipPath` 限定 alpha 外形和孔洞。主体原 PNG 的内部 alpha 中位数是 253，因此 `artwork` 组使用 `opacity=253/255`。这近似保留其接近不透明的主体，而非逐像素复刻全部 alpha。
8. 同色微小 stroke（较简 0.55 px、较细 0.35 px）和被 clip 限定的底绘减少独立色区之间的细缝。它们可能改变局部边界像素，应由真实重渲染衡量。

较简的 mode filter 改动 47,401 个标签像素，小色区后续合并 63,747 个；较细分别为 73,213 和 70,532。两类计数可重叠，不能相加当成总失真面积。

参数、色值、每色路径数量、源哈希、运行库版本和限制分别记录于同名 JSON；总索引为 [study-summary.json](study-summary.json)。

## 眼部与语义分组

两个眼睛用独立深色连通域推断：组件位于下半幅，长宽比在启发式范围内，外周主要为浅暖色，且成对的面积和间距合理。实际识别结果：

- `eyes/eye-left`：bbox `[265,722,383,900]`，中心约 `(323.50,810.75)`。
- `eyes/eye-right`：bbox `[652,903,766,1075]`，中心约 `(709.09,988.90)`。

它们从其他调色板 mask 中排除后独立绘制，便于定位编辑；没有把全部深色头发合并为眼睛。此判断仍是启发式，需要查看实际渲染确认。

其他组为颜色规则，而非可靠的对象分割：

- `face`：浅暖色，也可能包含腮红或别处的浅色高光。
- `hair`：暗／中性颜色，已排除推断的眼部区域。
- `coral`：显著偏红的颜色。
- `halo`：青绿颜色；也会包含同色束发连接处。
- `other`：其余色块。

同色但不同对象的片段仍可能处于同一个 compound path。局部精调可能需要先按子路径拆分；不能直接把整个 `halo` 组平移而假定只有环被移动。自动语义分组没有被认证为正确。

## 可复跑

工具：[tools/vectorize_calibration.py](../../../../tools/vectorize_calibration.py)。从仓库根执行以下命令，使用新输出名；工具拒绝覆盖已有 SVG 或参数日志。

```text
python tools/vectorize_calibration.py --input outputs/calibration/illustration/short-imagegen-v1.png --output outputs/calibration/illustration/vector-study/repro-simple.svg --colors 24 --min-area 64 --mode-filter 3 --tolerance 0.85 --smooth 0.8 --rgb-blur 0.95 --stroke-width 0.55 --max-seconds 50

python tools/vectorize_calibration.py --input outputs/calibration/illustration/short-imagegen-v1.png --output outputs/calibration/illustration/vector-study/repro-detail.svg --colors 48 --min-area 24 --mode-filter 3 --alpha-min-area 4 --tolerance 0.55 --smooth 0.6 --rgb-blur 0.7 --stroke-width 0.35 --max-seconds 50
```

调用方另设了单任务 55 秒硬超时，程序内部限 50 秒，并把数值库线程数限制为 1。两个 v2 工作分别约 1.68 秒、3.03 秒，退出码均为 0；未启动子进程、浏览器或常驻服务，未联网。

## 早期试验与未通过项

不带 `-v2` 的 24／48 色 SVG 与日志保留为早期诊断证据：没有标签 mode filter，48 色产生 6,643 个轮廓环、约 4.64 MB，细碎程度过高。因此本轮主对照使用上面的两个 v2 候选。

仍未验证：实际像素色差、alpha 边界误差、细发／回卷的保留程度、局部曲线是否产生过冲、halo 内孔的重渲染效果、肉眼是否存在色带或碎块。没有声称美术通过、用户接受、跨模型一致或已获得比原图更正确的角色造型。
