# 显式材料编译器

`scripts/compose_materials.py` 是可选的 Python 3.9+ 标准库工具，将材料计划应用到已经选定的静态 SVG 几何。它沿用 `archive_svg.validate_svg` 的静态子集校验，不研究参考、不拟合位图、不重新决定主体或构图，也不渲染或作视觉验收。

此工具保留所有原有 shape 的几何属性值、完整 transform 链和相对顺序；只修改指定 ID 的材料。未选中的 shape、已有 gradients 和 clips 保留。XML 排版和前缀可能重新序列化，输入字节哈希与输出字节哈希分别记录。编译计划绑定原 SVG 的 SHA-256，局部修色应继续使用该几何源和修订后的计划。多层产物中的目标 shape 已成为 clip 的组成部分，不应把编译产物直接当作下一次编译的原始可见目标。

## 调用

```text
python scripts/compose_materials.py --geometry geometry.svg --plan full.materials.json --output compiled.svg --report material-report.json
```

四个路径都必须明确指定，输出父目录必须已经存在。脚本不选择存储根目录、不自动建版本、不联网、不操作 Git；已有输出或报告不覆盖。版本归档另按已选存储策略处理。

输出失败时，只回收本次独占创建且文件身份仍匹配的文件。首次身份查询失败会改查同一个打开的文件句柄后回收；若两种句柄查询均不可用，无法可靠确认归属的那个新文件会保留，并在错误中明确列出路径，不按路径猜测归属后删除。

## `aikon.material-plan.v1`

```json
{
  "schema": "aikon.material-plan.v1",
  "geometry_sha256": "替换为实际geometry.svg字节的SHA-256",
  "profile": "full",
  "materials": [
    {
      "target": "main-surface",
      "role": "warm fabric",
      "reason": "参考中该材料的连续暖色与宽缓受光",
      "support": [-4, -4, 108, 108],
      "glaze_reasons": ["左上方宽缓受光，保持基础材料可见"],
      "field": {
        "kind": "layered",
        "base": {
          "kind": "linear",
          "from": [0, 0],
          "to": [70, 95],
          "stops": [
            {"offset": 0, "color": "#e8b599"},
            {"offset": 1, "color": "#8c5361"}
          ]
        },
        "glazes": [
          {
            "kind": "radial",
            "center": [24, 28],
            "radii": [70, 52],
            "stops": [
              {"offset": 0, "color": "#fff5db", "opacity": 0.28},
              {"offset": 1, "color": "#fff5db", "opacity": 0}
            ]
          }
        ]
      }
    }
  ]
}
```

`materials` 为 1–256 项，每个 `target` 必须是唯一的、现有可见 shape ID，不能指向 group、gradient、defs 或 clip 内的 shape。顶层可加非空 `notes`。每项都须有非空 `role` 和 `reason`，由调用方声明材料语义及依据；没有固定角色调色板、眼部比例、姿态或亮度差阈值。工具不会核实理由与参考是否相符。

目标必须用于填充面；`line` 和 `fill=none` 且带 stroke 的纯描边图形被拒绝。普通 path/polyline 仍按 SVG 的填充语义隐式闭合，调用方须确认它确实表示所需的面。原 stroke 会被显式材料替换，工具不支持描边上色；它也不判断退化路径是否有面积。

支持以下 field：

| kind | 必填参数 | 含义 |
| --- | --- | --- |
| `solid` | `color` | 明确的 `#RRGGBB`；可选 `opacity`，直接材料只能为 1 |
| `linear` | `from`, `to`, `stops` | 两个不同的二维端点 |
| `radial` | `center`, `radii`, `stops` | 二维中心、两个正半径；椭圆解析色场 |
| `layered` | `base`, `glazes` | 一个不透明 simple base 加 1–2 个 simple glaze，不允许嵌套 layered |

所有坐标与 `support` 均采用 **target 的本地用户坐标空间，即应用原 target.transform 之前**。祖先与 target 自身 transform 原样保留；编译器不平移、缩放或重新猜测 shape。没有 objectBoundingBox 自动换算。数值须为有限 JSON number，布尔值、数字字符串和非有限值不接受。

渐变有 2–5 个 stops，每项为 `offset`、`color` 及可选 `opacity`。offset 必须从 0 到 1 严格递增；opacity 在 0–1。颜色只接受六位 hex；颜色自身不携带 alpha。直接材料与 base 的全部 alpha 必须为 1，透明 stop 只用于 glaze。所有色场采用 sRGB、userSpaceOnUse 和默认 pad 延展。不存在滤镜、noise、mesh、pattern、位图或外部资源入口。

`layered` 项必须另外提供 `support: [x, y, width, height]` 和与 glazes 一一对应的非空 `glaze_reasons`。support 是调用方已知的材料覆盖域，应完整包住 target 的填充边界并留出边缘余量；glaze 的宽度、方向及理由也由调用方决定。编译器只检查有限值、正宽高与合法结构，不求路径 bbox，不测量是否为宽高光。**支持域过小仍可生成有效 SVG，却会截断材料；报告始终将 support coverage 标为 unverified，必须渲染检查。**

## 一次采样边界与 owner

多层材料把原 target（保留原 ID 与几何）移入本地 `clipPath`。一组 support 矩形承载不透明 base 与最多两层 glaze，整个组只应用一次 target clip。矩形沿用 target 的自身 transform；因此原 ID 仍直接控制真实可见轮廓，且不会反复绘制轮廓边缘累加 alpha。目标的 fill/stroke/opacity 被材料定义替换，不生成描边来冒充自然性证据。原 `clip-rule` 与实际 `fill-rule` 冲突时拒绝 layered 转换；缺失时补入有效 fill-rule。

每项可加 `owner: "existing-shape-id"`，将材料限制在该现有 shape 的填充轮廓内。owner 不必与 target 属于同一 parent，但两者完整 transform 链必须逐项相同；不能用未证明等价的坐标链猜测对齐。owner 须是不同的可见 shape，且没有自身或继承的 clip-path。owner 的几何仅用于额外裁切，不会改写 owner 材料。这是轮廓快照；修改 owner 几何后需重新编译。

target 自身 opacity/fill-opacity 由显式材料替换为 1；若任一祖先 group/root 的 opacity 小于 1 则拒绝编译，避免把半透明主体称为不透明材料。祖先 fill-opacity 可由目标或矩形的显式 fill-opacity 覆盖。既有裁切、额外 owner 裁切、抗锯齿边缘和支持域仍可能影响最终像素 alpha。

## 证据范围

报告包含输入 SVG、规范化计划、原几何记录及输出 SVG 的 SHA-256，并列出选定目标与材料依据。`original_geometry_preserved` 证明原属性、坐标链与顺序的结构不变量；`opaque_material_construction` 仅证明计划含不透明基础材料且祖先 opacity 未使它半透明。它不证明像素覆盖足够、轮廓抗锯齿正确、材质自然、主体相似或用户接受。

尤其是 owner 裁切、support 覆盖不足或目标原 stroke 的替换都可能改变可见范围；保留原 `d`/尺寸/变换等属性，不等于保持整图像素 alpha。

`support_coverage`、`raster_alpha`、`visual` 均为 `unverified`，`user_acceptance` 为 `unassessed`。按视觉验证流程实际渲染大图与小尺寸、查看深浅展示底、核对主体边界与局部修改。研究中验证的共享 clip 构造可复用，但单例的颜色、坐标与观察结论不能泛化为所有角色的风格标准。
