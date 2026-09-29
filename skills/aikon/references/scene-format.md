# Aikon scene v1 与可选 Python helper

**适用范围：历史平色子集。** 本格式不支持当前自然光泽所需的任意局部梯度、裁切和真实参考投影；固定head旋转也不构成仰头。当前默认应走自包含直接SVG路径，见[自然光泽](natural-gloss-v2.md)。不要把工具限制当作原作者或用户的美术要求。以下规则保留用于已有scene v1的重放。

这是代码优先路径的确定性场景格式；只需要 Python 3.9+ 标准库，不安装依赖，不联网。其他 Agent 仍可直接编写符合技能要求的 SVG。helper 的检查只是结构检查，不是视觉通过，也无法核实某条用户批准是否真实发生。

## 最小示例

```json
{
  "schema": "aikon.scene.v1",
  "title": "Example character",
  "background": null,
  "variant": {"round_id": "round-001", "profile": "short"},
  "head": {"angle": 15, "pivot": [256, 256]},
  "eyes": {
    "centers": [[115, 305], [270, 305]],
    "width": 30,
    "height": 90,
    "fill": "#18191b"
  },
  "layers": [
    {"id": "hair-back", "shapes": [
      {"tag": "path", "attrs": {"d": "M-40 120 Q190 0 420 120 L420 512 L-40 512 Z", "fill": "#382921"}}
    ]},
    {"id": "face", "shapes": [
      {"tag": "ellipse", "attrs": {"cx": 190, "cy": 325, "rx": 220, "ry": 245, "fill": "#fff1e5"}}
    ]},
    {"id": "eyes"}
  ]
}
```

上例只演示数据与图层，尚未经风格或视觉验收，不作为审美合格样例。

## 字段契约

- `schema` 必须是 `aikon.scene.v1`；`title` 为 XML 可表示的字符串，渲染时自动转义。
- `background` 必须显式填写，默认使用 `null`，表示不绘制任何背景形状。不能用白色、棋盘格或其他填充假装透明。旧场景的 `#RRGGBB` 仍可读取，但新场景仅在用户特别要求纯色背景时使用；颜色字段本身不能证明已取得用户批准。
- 画布固定 `viewBox="0 0 512 512"`。若显式设置纯色背景，它不旋转；所有 `layers` 按顺序放入同一 `head` 分组，使用 `head.angle` 和 `[x, y]` pivot 旋转。
- `variant` 是可选对象，提供时必须同时含 `round_id` 与 `profile`。round_id 为 1–64 个 ASCII 字母、数字、下划线或连字符，首字符是字母或数字；profile 只能是 `short` 或 `full`。它们是来源标签，不改变绘制几何或代替实际分支创作。
- `eyes.centers` 恰好两个 `[x, y]`；两者 y 必须相同，x 必须严格递增。`width`、`height` 为正的有限数，生成两个相同大小的圆角矩形，以中心坐标定位、以宽度一半设置圆角。默认高度/宽度必须在 2.5–3，角度在 15–20 度，均包含端点。
- `layers` 至少含一个且只含一个 `{"id":"eyes"}`；该层只能省略 `shapes` 或提供空数组，实际眼睛由 helper 注入，不能混入自定义五官。其他层有唯一 ID 与 `shapes` 数组；ID 使用小写字母开头及小写字母、数字、连字符，最多 64 字符，不能用保留 ID `head`、`background`、`eye-left` 或 `eye-right`。
- 普通 shape 是 `{"tag": "path", "attrs": {...}}`。允许 `path/rect/circle/ellipse/polygon/polyline/line`。任意属性均不自动透传，未知字段会被拒绝。
- 所有数值必须为 JSON 数字且有限；不接受布尔值冒充坐标，不接受 NaN、Infinity 或溢出数字。图形可以超出画布，实际裁切需视觉检查；helper 不将边界合法等同于构图合格。

| shape | 必需属性 | 可选几何属性 |
| --- | --- | --- |
| `path` | `d` | 无 |
| `rect` | `width`, `height`（正数） | `x`, `y`, `rx`, `ry`（圆角非负） |
| `circle` | `r`（正数） | `cx`, `cy` |
| `ellipse` | `rx`, `ry`（正数） | `cx`, `cy` |
| `polygon` | `points`，至少三对有限坐标 | 无 |
| `polyline` | `points`，至少两对有限坐标 | 无 |
| `line` | `x1`, `y1`, `x2`, `y2` | 无 |

公共绘制属性：`fill/stroke` 为 `#RRGGBB` 或 `none`；`stroke-width` 非负；`opacity/fill-opacity/stroke-opacity` 为 0–1；`fill-rule` 为 `nonzero/evenodd`；`stroke-linecap` 为 `butt/round/square`；`stroke-linejoin` 为 `miter/round/bevel`；`stroke-miterlimit` 至少 1。省略 fill 时采用 SVG 自身默认填充。所有 shape 属性按固定顺序序列化。

`points` 为 SVG 数字字符串，例如 `"10,20 30,40 50,20"`；数字之间使用空白或单个逗号。`d` 仅接受 SVG 路径命令、ASCII 数字、有限数值及路径分隔符，必须从 moveto 开始；**这不是完整的路径语法验证器**，仍需实际渲染发现参数数量、弧线标记等错误。单条路径最多 65,536 字符，整个输入文件最多 2 MiB。

不支持 `image`、脚本、事件、URL、外部引用、字体、`style`、CSS、任意 `transform` 或命名空间属性。生成器只设置固定 head 旋转。这避免“以 SVG 包装位图”，但不能证明风格与角色辨识度。

默认禁止水印，只有用户特别要求才可加入相应设计。helper 不插入署名、商标或可见文字；`title` 是非绘制的 SVG 标题，不是水印。任意路径仍可能画出文字或标志，因此结构检查不能认证“画面无水印”，仍须实际查看。

## 每轮 short / full 双版本

每次新增参考绘图 round 都要生成两份独立场景：相同 `round_id`，分别指定 `profile: "short"` 与 `profile: "full"`，并分别保存 SVG。标签不能把同一份未执行分支的图标伪装成两种结果。具体提示词分支、候选绘制与双版本完整性由技能工作流管理；helper 不自动创建 round，也不自动生成缺失的另一版本。

例如 `round-001-short.json` 和 `round-001-full.json` 可分别快照到用户所选 root 的 `r001`、`r002`。同一 round 的并列候选不必互为 parent；parent 表示真实修改来源。旧场景可省略 variant，快照会明确记录 `round_id: null`、`profile: null`，不会猜测它属于 short 或 full。

## 显式风格例外

仅在已经取得并记录用户明确批准时，才在场景添加：

```json
"style_overrides": {
  "reason": "User approved a 12 degree tilt in decision tilt-02.",
  "angle": true,
  "eye_ratio": false
}
```

`reason` 必须非空。`angle: true` 只放宽角度范围；`eye_ratio: true` 只放宽高宽比范围。其他约束（有限数字、正尺寸、两个等大眼睛、同 y、x 递增等）继续生效。false 或省略表示不放宽。helper 不生成 reason，不寻找理由绕过风格约束，也不把调用者填入 reason 当作用户批准的证明。

## CLI

以下命令从技能目录执行；将路径替换为当前用户指定的位置。

```text
python scripts/aikon.py render --scene scene.json --output draft.svg
python scripts/aikon.py render --scene scene.json --output draft.svg --replace
python scripts/aikon.py check --svg draft.svg
python scripts/aikon.py snapshot --scene scene.json --root ./my-icons --revision r001 --note "First review draft"
python scripts/aikon.py snapshot --scene revised.json --root ./my-icons --revision r002 --parent r001 --note "User requested wider eye spacing"
```

`render` 默认拒绝覆盖；只有显式 `--replace` 才替换临时草稿。默认发布使用同文件系统硬链接以保证不覆盖；若存储设备不支持，命令会明确失败，不能自动转为覆盖。`check` 输出 JSON，退出码 0 表示结构检查通过，1 表示失败；始终保留 `visual: "unverified"`。未知元素、外部资源、事件处理器、DTD、任意变换等会失败；唯一变换例外是根 SVG 的直接子分组 `id="head"` 上的有限数 `rotate(angle x y)`。检查器接受 helper 使用的静态子集，不能作为任意合法 SVG 的通用合规验证器。

`check.background` 另行报告根 SVG 直接子节点中覆盖画布、没有圆角的 rect 及其 fill/声明 alpha。`structural_status: "opaque_canvas_rect"` 表示存在不透明画布背景，不能交付为透明背景；它不自动使结构检查失败，因为用户可能显式选择纯色。`translucent_canvas_rect` 表示检测到半透明画布 rect；`no_painted_canvas_rect_detected` 仅表示未检测到这种背景，不能保证其他路径没有覆盖整张画布。所有情况的 `raster_alpha` 均为 `"unverified"`，实际像素透明度需要渲染后另查。

`snapshot` 必须显式传入用户选择的 `--root`，从不推测目录、不使用 Git、不自动推送。revision 和 parent 必须为 `r` 加至少三位数字，总长不超过 32 字符。parent 若提供，必须是 root 中已完成的有效快照，不能指向自身。已有 revision 永不覆盖。

```text
<root>/revisions/r001/
  scene.json
  icon.svg
  revision.json
```

manifest 记录 schema、revision、parent、note、helper_version、scene/SVG 的 SHA-256、从 scene 取得的 round_id/profile、背景结构事实，以及 `checks: {"structural": "passed", "visual": "unverified"}`；不含伪造的视觉或 raster alpha 通过结论。相同场景在相同 helper 版本下导出相同 SVG 字节；manifest 不记录当前时间，因此同输入、同 revision 元数据也可重建。

输出路径的既有目录不能是符号链接、Windows junction 或其他 reparse point；输出文件也不接受链接。路径中不允许 `..`，请提供明确的相对路径或绝对路径。快照先写入本次临时目录，再独占创建 revision 目录并提交文件，manifest 最后写入。普通写入失败会清理本次临时目录和本次新建的未完成 revision；不会删除已有版本。强制断电/杀进程可能留下无 manifest 的未完成目录，应检查后人工处理；它不能作为有效 parent。该 helper 不是对抗拥有同目录写权限的恶意并发进程的安全沙箱。
