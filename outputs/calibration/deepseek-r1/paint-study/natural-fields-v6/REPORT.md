# 自然材料 v6 交接

最终参数：`final-fit/fields.json`，SHA-256 `2576456f0b4a034898b40f10979fd254e1d9bc0a2fd403136dc566ce1de7ab0d`。
它实际重新拟合、绑定并完整快照 `geometry-study/v6/final/geometry.json`，SHA-256 `8c251ff7add8cefd0737b4e2d0586b8e961b17de33e83051d4b0b364a5bbfebd`；源图 SHA-256 `60c234f594ad81319fa74bb4fa8392f10a125127d46bf1d3b47e618b25813da2`。最终拟合用时 4.87 秒。

## 实际变化及边界

已查看源图、v004、最终实际 resvg 预览及局部放大。修正几何后，右前发和主前发用一个底场与两层宽径向罩染，恢复更连续的横向光照变化；每层峰值 alpha 0.35，半径不小于材料 bbox 对应方向的 70%。其余面保持单场，面部和白瓣没有强加新光斑。眼缘沿用已有 v004 逻辑；此研究未解决眼缘的全部观感差异。

右脸侧折面必须重拟合：旧浅色字段套到正确的大暗折会形成不真实亮片。实际源色重拟合后，它的薄边与尖端预测 RGB 范围为 `[48.40,68.48,142.49]` 至 `[72.58,97.38,171.97]`，没有旧的青白色亮针。

在**相同最终 v6 mask**上比较旧 v004 字段与本次字段的全部可见像素解析 RMSE（0–255，不是相似度百分比）：

| 材料面 | 旧字段 | 最终字段 |
|---|---:|---:|
| 主前发 | 5.372 | 4.651 |
| 右前发 | 7.294 | 6.445 |
| 右内折 | 9.242 | 5.228 |
| 右脸侧折 | 19.093 | 10.301 |

不能用此表宣称所有材料全面改善。例如主前发重拟合的**无约束单场**内区 RMSE 2.920，而最终有界复合场为 3.465；代价是保住全部可见尖端的合理范围。无约束单场在全可见支撑上的最大 RGB 为 `[129.35,161.85,222.95]`，最终薄边/尖端最大为 `[117.17,147.97,215.30]`。这个取舍已记录，没有隐去更小的无约束误差。

## 全可见范围与实际 SVG 检查

全部 43 面均报告完整可见 mask、薄边、拟合内区、所有字段预测最小/最大值。新拟合字段没有超出预先取得的各材料有界范围。4 个保留的旧字段仍有范围警示：bow-knot 49px、hair-back 782px、bow-crease-left 25px、frill-fold-04 23px。这些警示未偷偷清除，不能据此声称整个图像的所有材料问题已关闭。

实际 SVG 在 `final-fit/actual-field-study.svg`；实际渲染及视觉对照在 `actual-field-study.png`、`actual-comparison.png`、`material-crops.png`。主线程的最终合成 SVG 才是交付候选，本目录预览用于字段审查。

`actual-render-field-equivalence.json` 保留一次**失败**检查：自设 2.1 RGB/通道容差下，40 个单场通过，1 个极细面无足够不透明内区（not_assessed），2 个复合场超出容差。右前发最大差 3.811、平均绝对差 0.915；主前发最大 3.415、平均 0.577。没有调高阈值伪装通过。

随后对实际每个图层分别渲染并读取 RGBA，结果在 `premultiplied-quantization-diagnosis.json`。例如右前发 `(954.5,770.5)`：解析第一层 alpha 0.076693，实际为 20/255；其不透明颜料 RGB 117/159/217 在低 alpha 独立 PNG 中反预乘后为 128/166/217，对应实际预乘通道比浮点预期约高 1 级。第二层出现相同整数预乘/合成差异；叠加后解析预测与实际 PNG 有数级偏差。因此解析数值是近似诊断，图像质量与参考差值必须以**最终 SVG 的实际渲染**测量。

一次白 alpha mask 导出实验减少偏差但仍未通过 2.1 容差；失败另存 `actual-render-field-equivalence-alpha-mask.json`，实验代码为 `svg_fields-mask-experiment.py`。没有推广这份额外复杂度；正式 `svg_fields.py` 已恢复为普通渐变导出，且与 `final-fit/svg_fields.py` 相同。没有修改渲染器，没有新增噪声或调整艺术门禁。

## 参数接口及重现

`svg_fields.py` 仅用标准库。普通字段仍为 `solid|linear|radial`。复合字段为：

```json
{"kind":"layered","base":{"kind":"linear","from":[0,0],"to":[0,1280],"stops":[]},"glazes":[{"kind":"radial","center":[0,0],"radii":[600,600],"peak_opacity":0.35,"stops":[{"offset":0,"rgb":[117,159,217],"opacity":0.35},{"offset":1,"rgb":[117,159,217],"opacity":0}]}]}
```

示例只说明结构；生产必须读取实际数值。每个复合面共用一个语义路径 clip，底场和罩染用该 clip 内的矩形支持，避免叠加面轮廓的抗锯齿覆盖。`paint()` 返回 definitions、底场 fill、overlay attributes；`surface()` 返回 definitions 和完整语义面 group。

研发拟合需要当前已有的 NumPy/SciPy/Pillow；导出无需这些包。拟合前冻结了真值、几何、全部 mask。旧几何两次小模型比较保存在 `pilot-v5`、`pilot-support-correction`；第一份冻结几何的主拟合为 `main-fit`；几何作者确认细尖端修正后仅实际重跑一次，保存在 `final-fit`。没有覆盖历史试验，没有安装包、修改 Git/CI 或终止其他任务进程。

本轮依然是同图来源辅助校准。它没有证明独立 Agent 只用 Skill 即可生成相同图案，没有达到已验证的 99%，也没有用户视觉接受记录。
