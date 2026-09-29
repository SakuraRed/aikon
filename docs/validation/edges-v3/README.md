# 边缘像素门禁原型 v1

本原型检查 **同一份 SVG 在指定尺寸上的栅格边缘**：覆盖率阶梯、异色半透明边、材料边界失真以及独立的内部 alpha 缺口。它不判断角色、仰头、胶囊眼、高光自然度或风格相似度；旧六图的用户拒绝状态不会因检测器测试通过而改变。

## 接口与运行边界

```python
from tools.analyze_edge_quality import analyze_svg_edges, save_evidence, run_reference_audit

report, maps = analyze_svg_edges(svg_text, candidate=png_image, size=256)
save_evidence(output_directory, report, maps)

# repo 验证入口：13个已知正/负对照，返回control_suite_pass并写summary.json
controls = run_reference_audit(audit_directory)
```

`candidate=None` 检查该 SVG 的原生渲染；提供 PNG 时尺寸必须与 SVG 在指定 size 下的实际画布一致。没有自动对齐、改尺寸或裁掉困难区域。

```text
python tools/analyze_edge_quality.py --audit --output .local/edge-audit
python tools/analyze_edge_quality.py --svg icon.svg --candidate preview.png --size 256 --output .local/edge-one
python tools/analyze_edge_quality.py --png image.png --output .local/edge-advisory
```

CLI 单 worker 硬超时45秒，复用已存在的进程树回收器；API 调用方负责时限。最大目标边长1024、仅支持固定4倍超采样，原生后端最大4096；数值库限制为单线程。不安装依赖，不运行浏览器，不生成新艺术图。

退出码：0仅表示指定规则无失败；2表示检出失败；3表示只有单PNG建议或没有足够边缘证据；1为输入错误；124为超时。单PNG没有几何参考时绝不声称边缘合格。

## 像素比较方法

1. 原生目标图与4倍渲染串行执行。参考只将 `shape-rendering` 设为精确覆盖，几何和绘制内容保持原样。
2. 参考按**预乘alpha、编码sRGB**做BOX面积重建，分别积分alpha和颜色再还原直通颜色。不混入全透明RGB，不声称这是线性光物理仿真。
3. 从参考真实alpha变化确定外轮廓带；从真实颜色变化确定不透明材料边界。因此全不透明的两色阶梯也不能靠alpha恒255逃过检查。视口边界使用nearest邻域处理，合法裁切本身不是缺陷。
4. 分开报告覆盖率残差、alpha加权的直通RGB残差、深色底和浅色底合成残差。颜色残差取三通道最大绝对差，单位均为8位通道的`0–255`，不是审美分数。
5. 源SVG中应不透明的内部区域向内侵蚀2px，单独检查alpha损失。相同RGB并不代表没有锯齿或内部透明缺口。

没有使用原生resvg字节一致性作为质量判据。实际native像素即使可重复，也可能与超采样覆盖不同。

## 判据冻结与适用范围

全局规则在首次查看负例前固定：边缘平均绝对误差大于`8/255`，或误差大于`32/255`的样本超过`3%`，即提示对应通道不一致。内部alpha差大于`3/255`且超过3个像素单独失败。这是工程容差，不是研究得出的普适阈值。

先用5个合法SVG、128和256两种尺寸产生[正例校准](positive-calibration/summary.json)，再测试独立注入缺陷。正例覆盖正常AA/低频渐变、尖角/高曲率、合法裁切/深色轮廓、多材料边界和源SVG声明的半透明。观测最大覆盖率MAE为`1.8693/255`，颜色MAE为`1.1093/255`；大残差占比最大分别`0.4217%`、`0.0698%`。

为避免全图比例稀释局部彩边，随后**先重新统计上述正例局部连通残差，再构造短段负例**。局部大残差阈值仍为`32/255`，正例最大连通坏像素数为1，预先冻结容许3；仅连接1px间隙，计数仅含原始坏像素，不把膨胀区计入。之后才注入16像素局部彩边，未据其结果回调阈值。

已校准尺寸只有128、256；API允许32–1024是资源上限，**不代表全尺度已验证**。报告提供边缘采样像素数和部分覆盖像素数，不把它们冒称轮廓弧长。全局比例受轮廓复杂度影响；局部规则可以减少这种稀释，但仍可能漏掉低于32强度、少于4像素、透明度极低或断开的弱缺陷。

## 实际对照结果

[完整审计](audit/summary.json)中13项预期均满足；[新增测试](../../../tests/test_edge_quality.py)13项已实际通过。它们验证检测器，未验收六张图。

| 输入 | 实際结果 | 被检查的独立事实 |
|---|---|---|
| 5种合法几何/材质 | 无规则失败 | 尖角、深色轮廓、低频渐变、裁切不因存在而失败 |
| 全透明位置的洋红RGB | 无规则失败 | 不可见数据不被当作可见彩边 |
| 64px→256px最近邻放大 | coverage失败，MAE50.657/255 | 颜色干净仍存在明显阶梯 |
| alpha在128二值化 | coverage失败，MAE11.067/255 | 未改RGB也会破坏AA |
| 半透明边缘全圈注入洋红 | color失败，MAE20.363/255 | alpha没变也会产生彩边 |
| 只改短段16个像素 | 局部color失败，最大连通9像素 | 全局MAE0.960、坏比例0.740%均低于全局门槛，局部规则仍命中 |
| 30×30内部alpha255→239 | 独立alpha失败，900像素 | 外边缘和RGB仍正常，不归咎为锯齿 |
| 全不透明材料边界最近邻放大 | material/color失败 | alpha全255不是免检依据 |
| SVG显式crispEdges | coverage失败 | 与同几何精确面积覆盖直接比较 |

每个对照目录均保留实际candidate/reference、深浅底、边缘mask、误差图（显示增益×4）、report和局部放大。放大使用nearest仅为了显示原像素；计算在未放大的原始尺寸进行。局部彩边的[深浅底放大](audit/negative-local-16px-color-fringe/local-color-cluster-crop.png)直接展示实际注入像素。

## 旧图诊断及限制

旧DeepSeek round-002 short只读检查在256px发现顶部裁切附近4个连通颜色残差像素，因此[局部规则提示失败](audit/held-out-rejected-deepseek/report.json)。实际看图显示的是native与4倍面积重建的材料边缘差异，**不能据此断言确有用户所指的彩色污染**；保留定位图供复核，不放松阈值让旧图通过，也不把这一信号当作角色错误的证据。

同SVG比较不能发现两次渲染都包含的错误几何、源SVG有意画出的孔、错误色块、噪点、造型和姿态。候选与SVG内容不一致也可能触发同一错误码，所以名称明确保留“contamination_or_material_mismatch”。该原型不是有完备真实样本校准的美术验收器；应与纹理、主体特征及人类视觉检查组合使用。

实现与验证只改`tools/analyze_edge_quality.py`、`tests/test_edge_quality.py`和本目录。没有修改r1、任何角色产物或CI。
