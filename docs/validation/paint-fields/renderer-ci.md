# 固定 SVG 渲染器与 CI 来源记录

日期：2026-09-29。此文记录验证基础设施，不能充当图标的视觉验收结论。

## 选择与边界

采用 `resvg-py==0.5.0`，其源码 manifest 要求 Rust `resvg` 的 `0.48.0` 兼容系列，固定 wheel 本地运行实际返回 `resvg==0.48.1`。它是 `baseplate-admin` 维护的 Python binding，并非把 Linebender 与 binding 的维护者混为一谈。AnySearch 的 `code.doc` 检索用于发现候选，最终 API 与安装依据是 [binding 官方文档](https://resvg-py.readthedocs.io/en/latest/api.html)、[发布包](https://pypi.org/project/resvg-py/0.5.0/)和 [binding 源码仓库](https://github.com/baseplate-admin/resvg-py)。

选择这个验证适配器的原因是：发布包具备 Windows 与 Linux 的预编译 wheel，不要求本机安装 Rust 或系统 Cairo；一个 API 接收 SVG 字符串并返回 PNG。写 SVG 本身仍可只用 Python 标准库或直接写文本，`requirements-ci.txt` 是仓库的可选验证环境，不是分发技能的宿主依赖。SVG 创作与渲染过程都不需要绘图模型、Jev、API key 或在线图片服务。

从 PyPI 版本 JSON 取得并校验 0.5.0 源码包 SHA-256：`6d3bf8e866b4e129524d9432a809138b2d100931d8d635bc81294002abcdfd46`。本地仅在内存中读取归档的 `Cargo.toml`、`pyproject.toml` 和 `src/rust/lib.rs`，没有执行源码构建。审计发现该版本设置 `allow_dtd: true`，并使用默认 image href resolver。因此不能把渲染库本身当作输入安全边界；相关版本材料可从[版本固定的 PyPI JSON](https://pypi.org/pypi/resvg-py/0.5.0/json)复核。

`tools/render_svg.py` 在调用 native binding 前检查并重序列化 SVG：

- 允许图形、路径、分组、本地 `linearGradient` / `radialGradient` / `clipPath` / `mask` 及有限的 inline style。
- 拒绝 DTD、实体声明、非 XML 声明的 processing instruction、脚本、事件属性、动画、外部资源引用、CSS 转义与导入、嵌入图片（包括 data URL）、foreignObject、字体文本、filter 与 pattern。
- 渐变可以用本地 `href` / `xlink:href` 继承；`url(#id)` 必须能解析到本 SVG 中唯一的 ID。任意网络、本地文件和相对文件 href 都不进入 backend。
- 限制 2 MB 输入、10,000 个元素、64 层嵌套和 1–4096 像素输出尺寸；调用者另行设置硬超时。

这些是本项目的受限静态图标合同，不声称支持所有合法 SVG，也不声称是通用 SVG 安全清洗器。`use`、富文本和任意 CSS 样式表暂不在合同内。避免纹理噪声和不自然高光还需要上层 paint-field 合同与像素诊断，不能仅依靠这里的标签检查。

## 调用合同

```text
python -B tools/render_svg.py INPUT.svg --output OUTPUT.png --size 512
```

`--size` 是最大包围框；保持输入纵横比，正方形图标输出 512×512。使用 `background=None` 保留源透明度，并关闭系统字体加载；不会自动去掉源 SVG 内明确绘制的背景。

可编程接口：`render_svg_text(svg_text, size=512)` 返回 PNG bytes；`render_svg_file(input_path, output_path, size=512)` 写 PNG 并返回 backend 版本、尺寸、源与 PNG SHA-256 等元数据。PNG 头必须为 8-bit RGBA；实际 alpha 与颜色使用 Pillow 读取验证。图像渲染成功不会自动标记视觉验收通过。

## 固定依赖

`requirements-ci.txt` 固定以下版本及官方下载 wheel 哈希，CI 使用 `--require-hashes --only-binary=:all:`。锁文件覆盖 CPython 3.13 的 Windows x86_64 和 Linux x86_64；其他 Python 版本或架构必须补充核对对应 wheel，不能宣称本锁文件已经覆盖。

| 包 | 固定版本 | 用途 | 官方发行证据 |
| --- | --- | --- | --- |
| resvg-py | 0.5.0 | 确定性矢量栅格化 | [版本 JSON](https://pypi.org/pypi/resvg-py/0.5.0/json) |
| Pillow | 12.1.1 | RGBA 读取、输出与可视证据 | [版本 JSON](https://pypi.org/pypi/Pillow/12.1.1/json) |
| numpy | 2.4.3 | 像素矩阵诊断 | [版本 JSON](https://pypi.org/pypi/numpy/2.4.3/json) |
| scipy | 1.17.1 | 空间滤波和连通区诊断 | [版本 JSON](https://pypi.org/pypi/scipy/1.17.1/json) |

Pillow、numpy 和 scipy 沿用本轮诊断使用的固定版本。SciPy 1.17.1 声明 `numpy>=1.26.4,<2.7`，锁定的 2.4.3 满足。没有加入 matplotlib；小型证据图可通过 Pillow 制作。固定哈希控制获取到的构件版本，不等同于对上游全部源码或 wheel 的完整安全审计。

## GitHub Actions

`.github/workflows/visual-quality.yml` 使用 Ubuntu 24.04 与 Windows 2022 的 x64 矩阵，`max-parallel: 1`。权限仅 `contents: read`，checkout 不保留凭据。人工触发、PR 及 main 上影响技能、工具、测试、依赖或 paint-fields 资料的路径变更会运行；纯无关文档修改不会触发。

以下官方 repository tag 已通过 GitHub REST `git/ref/tags/...` 核对到 commit，再读取固定 commit 的 `action.yml`。workflow 使用完整 SHA，不使用可移动 tag：

| Action | 已核对 tag | 固定 commit |
| --- | --- | --- |
| actions/checkout | v5.0.0 | [08c6903cd8c0fde910a37f88322edcfb5dd907a8](https://github.com/actions/checkout/blob/08c6903cd8c0fde910a37f88322edcfb5dd907a8/action.yml) |
| actions/setup-python | v6.0.0 | [e797f83bcb11b83ae66e0230d6156d7c80228e7c](https://github.com/actions/setup-python/blob/e797f83bcb11b83ae66e0230d6156d7c80228e7c/action.yml) |
| actions/upload-artifact | v4.6.2 | [ea165f8d65b6e75b540449e92b4886f43607fa02](https://github.com/actions/upload-artifact/blob/ea165f8d65b6e75b540449e92b4886f43607fa02/action.yml) |

安装、unittest 通过 `run_bounded` 设置50秒进程树硬超时，E2E使用内部50秒worker加最多8秒回收预算，步骤与 job 另有宿主超时；数值库线程均设为 1。不调用 live imagegen/Jev，不访问开发者机器上的私有绝对路径。先运行 `unittest discover`，再运行 `python -B tools/run_visual_e2e.py --output .local/e2e`；依赖安装成功后，即使 unittest 失败也继续收集 E2E 诊断。最后无论成功失败都尝试上传 `.local/e2e/` 的小型证据，保留 7 天。依赖安装或 runner 初始化失败时可能没有图像，不能据此伪造渲染报告。

## 已完成验证与未完成范围

- Windows 本地 Python 3.13.3，隔离安装到 `.local/ci-venv`；4 个包均使用 hash-locked binary wheel 安装成功。
- `test_render_svg.py` 的 9 个测试通过，耗时约 0.33 秒；真实像素检查包括线性/径向渐变、本地继承、clipPath、透明与约 50% alpha、保持纵横比、同机同输入 PNG bytes 一致，以及 CLI 路径含空格。
- 恶意或不支持的资源输入在渲染前失败；失败 CLI 保留原来存在的输出文件，不以空输出覆盖。
- 安装前读取现有 Python/Node/Chrome 进程的 PID、父 PID、命令和开始时间；操作系统查询未提供其工作目录，不编造。安装与测试均为限时一次性进程，没有启动新服务或终止现有进程。
- Linux 运行、GitHub workflow 实际成功和跨平台像素一致性尚待主线程在一次正式推送后监控。本文件编写时未 push 或 dispatch。固定后端降低环境差异，不能证明任意模型会生成同一几何或保证艺术验收。

## 离线 paint E2E 实现与首轮结果

入口 `tools/run_visual_e2e.py` 已接入真实 compiler、固定 resvg 与 `analyze_paint_fields.analyze_image(..., region_masks=...)`。每版先重复编译验证 bytes/report 稳定，再独立核对所选几何与 canvas；保存 1024、128、48、24 像素 PNG。检测用的每个 layer mask 都从实际 SVG 白化目标形状后渲染取得，保留原 defs、clip 与 transform，不由手选好看的 ROI 替代。材料可见区域扣除 SVG 中后绘制层，逐层公开 raw/visible 像素量、阴影排除量和所有遮挡排除量；另以全主体几何 mask 检查内部 alpha。

机械 shadow 规则在 1024 像素尺度下要求：不漏出 receiver；面积至少 12 像素的每个连通分量距离 receiver 真实边界不超过 2 像素。这个规则只测边界连接，不证明阴影原因或高光自然性。`highlight_naturalness` 始终为 `not_automatically_assessed`，不将机器 pass 转为视觉 pass。

首轮执行约 9.98 秒，small artifact 集约 1.54 MB：两版完整材料像素检查均无规则失败，但 `center-fold-shadow` 的一个 35,610 像素连通区离边界 3.0 像素，超过已定 2 像素，故总结果为 fail；该失败交回主线程调整计划，检测侧没有放宽阈值。报告同时保留细窄 `halo-inner-shadow` 纹理 sample 不足事实；该层只声明 opacity 与 anchor 检查，不声称测得纹理合格。

10 项控制均符合预期：合法平滑 gradient 和抗锯齿不过度报警；固定 seed 颗粒、alpha=249 的轻微内部透明、小亮片均分别触发对应规则；额外未声明形状、filter、源 hash 或冻结 canvas 篡改、缺少 full、两版相同 bytes 均失败。DeepSeek binding 会校验 `ref/user-mode/r1.png`、文件 hash、subject/style 双角色；旧鲸鱼默认不进入此 fixture 测试。

`test_visual_e2e.py` 8 项独立集成测试通过，包括真实 SVG 的遮挡、transform/clip mask、浮离/漏出阴影、空 mask 失败、绑定与双版合同、上述正负控制，以及超时子进程树回收。E2E worker 上限为 50 秒并预留最多 8 秒清理预算；Windows 回收本任务 process tree，POSIX 回收独立 process group。测试使用延迟写文件的 grandchild 证明超时后没有残留子进程继续写入。首轮结果不是最终修正版本结果，后续结果应以对应 run 的 `report.json` 为准。

## 本地最终集成

最终75项测试全部通过（12.063秒），包含11项renderer测试、13项paint compiler测试、14项paint诊断测试及其他scene/E2E合同检查。CLI中文输出已用ASCII兼容JSON修复，报告文件保持UTF-8。最终E2E见 [e2e-final.json](e2e-final.json)，16.695秒：双版及10项注入控制、8张真实参考/缺陷观察均符合预期。真实坏例依然被拒绝，short纹理局限仍保留。超时清理失败时单独报告cleanup_failed，不再声称已回收进程。
