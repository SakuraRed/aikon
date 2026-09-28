# 独立上色计划

上色器 `scripts/paint_svg.py` 仅需Python标准库。它在已有可编辑vector geometry上选择确定的表面及遮挡层，移除旧的绘图纹理/叠色，再导出解析色场。它不读取图片、不调用绘图模型、不自动认定造型和阴影自然。

## 输入与运行

先实际观察参考并保存生产prompt，然后写plan；不要在导出后才补prompt。

```text
python scripts/paint_svg.py --geometry geometry.svg --plan full.paint.json --output full.svg --report full.paint-report.json
```

已有输出不覆盖。geometry由当前任务决定，不能用统一头像替代主体。输入SHA-256必须与plan匹配。只有plan选择的绘制元素保留；其path、尺寸与transform保持不变。形体修改应另建geometry版本。

冻结前先检查这份SVG是否保留了参考中的主要发束/材料分组。若前轮重建把数束头发合成一个大面，删除坏高光可能暴露出整块平涂；几何未变化的检查不能证明分组完好。此时把paint清理记录为局部进展，将丢失的分组列为geometry不足。后续新建几何修正版，用实际发流/遮挡边界重建必要主面，同时保留获肯定的外轮廓、眼位和配件连接；不能靠换更多颜色、加回悬浮亮片或放宽阈值掩盖。

```json
{
  "schema": "aikon.paint-plan.v1",
  "geometry_sha256": "<实际源文件SHA-256>",
  "profile": "full",
  "layers": [
    {
      "id": "hair-base",
      "role": "surface",
      "paint": {"type": "linear", "from": [0,0], "to": [0,512], "colors": ["#53505D","#494653"]}
    },
    {
      "id": "hair-overlap",
      "role": "occlusion-shadow",
      "owner": "hair-base",
      "anchor": "receiver-boundary",
      "reason": "后发被前发遮挡，暗面连接同一发束边缘。",
      "paint": {"type": "solid", "color": "#403D49"}
    }
  ]
}
```

示例中的ID必须替换为实际存在的几何ID，不是可直接绘图的模板。

## 当前可执行子集

- `surface`：不透明solid或双色端点的单向linear field。方向必须非零、数值有限；当前保守预算为端点luma差≤24/255、任一RGB通道差≤40/255。这是工程预算，不是从官方倒推的普适美学阈值。
- `eye` / `underpaint`：不透明solid。
- `blush`：不透明solid，并声明脸部owner；在共同父坐标系内clip，不能因自身旋转把脸部clip一起转错。
- `occlusion-shadow`：不透明solid、实际owner、receiver-boundary及具体原因。必须比接收面暗但不能超过24/255的luma差；实际边界连接仍需渲染像素检查，文字声明不是证明。
- 默认没有任意独立highlight primitive。此案例不需要高光时不添加。若另一主体确有一两块顺形受光面，应先明确其形体依据、建立相应规则与测试，不能把它伪装成shadow绕过合同。此子集不是禁止所有合法SVG高光。

compiler移除旧的全局opacity、透明叠色与未选的paint layers，保留透明画布；抗锯齿由renderer产生。主体内部的非预期alpha不会被作为“质感”复用。合法平滑gradient与位图云纹是不同来源，不能混为一谈。

CLI stdout是ASCII兼容JSON（Unicode使用转义），报告文件是UTF-8。调用方按JSON解码，不依据Windows当前控制台代码页猜测中文字节；stdout故障与已写出的SVG状态要分别核实。

## 检查与局限

报告中geometry signature保持不变，只证明选中几何未被上色器篡改；它不是造型分数。结构通过后要实际渲染，对材料内部、已声明边界、透明外缘分别检查，并查看完整图和局部。像素CI可拦某些grain、mottling、透明度泄漏与脱离边界的阴影片，但自然性及IP辨识仍不能自动宣布通过。

新建主体的geometry理解依旧需要Agent的视觉和研究能力；已有geometry+plan的编译可以跨模型重复。单次重放稳定不等于所有模型都能从任意原图提取同样geometry。
