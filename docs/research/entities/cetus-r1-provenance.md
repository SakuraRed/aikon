# CETUS-Desktop 中 r1 候选素材的来源调查

调查日期：2026-09-29。依据用户补充的 `cetus-desktop` 线索，仅检查上游 README、LICENSE、Git 树、资产路径提交记录与可达提交说明；没有 clone、构建、安装或下载发布包。本文件不替主线程作像素同源判定，也不修改 r1 或既有比较协议。

## 已确认的来源与高清线索

上游为 **[AvroraCL/CETUS-Desktop](https://github.com/AvroraCL/CETUS-Desktop)**，此次查询的 main 为 `7f14ea7819dfb025bafce2f0d088e4901aefead6`，对应 tree `ebacdfa57200352cf29fdeda91f1c161082ae648`。README 明确自述为独立社区项目，不能把它的头像直接称作 DeepSeek 官方角色。用户将其作为 DeepSeek 目标参考，是本项目中的明确绑定。[固定提交 README](https://github.com/AvroraCL/CETUS-Desktop/blob/7f14ea7819dfb025bafce2f0d088e4901aefead6/README.md)、[提交 API](https://api.github.com/repos/AvroraCL/CETUS-Desktop/commits/7f14ea7819dfb025bafce2f0d088e4901aefead6)

**4096px 源图已找到。** 2026-09-20 的资产更新提交说明：以更新后的4096px图像重新导出应用 ICO、启动图和公告页图像。该提交修改的源路径为 `docs/CETUS-ico.png`。主线程下载后，本调查读取了本地固定文件，确认4096×4096 RGBA、2,521,716 bytes、SHA-256 `4da172c683d7981e170fc90d8e7d1bd8b4e7107799cdc12338859c82e6fb44fd`，与采集记录一致。[资产更新提交 b7ac97a5](https://github.com/AvroraCL/CETUS-Desktop/commit/b7ac97a514c526726a92af51ec49eadce58be6ce)、[本地采集记录](../../../ref/subjects/deepseek/cetus-desktop/acquisition.json)

| 当前资产 | 大小 | Git blob 对象 SHA | 已知用途 |
|---|---:|---|---|
| [docs/CETUS-ico.png](https://github.com/AvroraCL/CETUS-Desktop/blob/7f14ea7819dfb025bafce2f0d088e4901aefead6/docs/CETUS-ico.png) | 2,521,716 bytes | `ca939dd35547b0b9723088ff6e57f381859e989f` | 本次图标更新的高清源路径 |
| [docs/site/CETUS-ico.png](https://github.com/AvroraCL/CETUS-Desktop/blob/7f14ea7819dfb025bafce2f0d088e4901aefead6/docs/site/CETUS-ico.png) | 340,262 bytes | `e2ef28155d80d715af164ecd643a8aefcf2d084d` | 公告页图标 |
| [Assets/cetus-splash.png](https://github.com/AvroraCL/CETUS-Desktop/blob/7f14ea7819dfb025bafce2f0d088e4901aefead6/src/Cetus.Desktop/Assets/cetus-splash.png) | 340,262 bytes | `e2ef28155d80d715af164ecd643a8aefcf2d084d` | 启动图，与公告页图标为同一个 blob |
| [Assets/cetus.ico](https://github.com/AvroraCL/CETUS-Desktop/blob/7f14ea7819dfb025bafce2f0d088e4901aefead6/src/Cetus.Desktop/Assets/cetus.ico) | 94,137 bytes | `945e1bad97546ce0b8460904c5cd5acbb8aaf76c` | 提交说明为16–256像素、7个尺寸 |
| [Assets/logo.png](https://github.com/AvroraCL/CETUS-Desktop/blob/7f14ea7819dfb025bafce2f0d088e4901aefead6/src/Cetus.Desktop/Assets/logo.png) | 55,177 bytes | `bbe9f0e39d898a420c4294aa50e78463026b663e` | 更早的品牌资产；不能仅按文件名认作 r1 原稿 |

表中大小和对象哈希来自[固定 Git 树 API](https://api.github.com/repos/AvroraCL/CETUS-Desktop/git/trees/ebacdfa57200352cf29fdeda91f1c161082ae648?recursive=1)，返回 `truncated:false`。这里的 SHA 是 Git blob 对象标识，不是本地文件 SHA-256。公告页确实在 `<img>` 中直接使用 `CETUS-ico.png`。[固定公告页源码](https://github.com/AvroraCL/CETUS-Desktop/blob/7f14ea7819dfb025bafce2f0d088e4901aefead6/docs/site/index.html)

## 资产提交链

`docs/CETUS-ico.png` 路径历史返回三次变更，均由 GitHub 账号 `AvroraCL` 提交，Git author 显示名为 `HelenaSG`。这些记录证明上传／提交身份，**不证明其是原画作者**。[路径历史 API](https://api.github.com/repos/AvroraCL/CETUS-Desktop/commits?path=docs%2FCETUS-ico.png&per_page=100)

| UTC 时间 | 提交 | 对本次调查的意义 |
|---|---|---|
| 2026-08-28 10:42:46 | [f5aaadd1](https://github.com/AvroraCL/CETUS-Desktop/commit/f5aaadd1b373a18226b2597352bfda664b024263) | 首次追踪 `docs/CETUS-ico.png`，描述为 README 品牌图标；blob `c77e8e7420ad8fd7c1248ba596915f17b0999118`。 |
| 2026-09-18 18:19:40 | [4d894cac](https://github.com/AvroraCL/CETUS-Desktop/commit/4d894cac71aa51ea1a54009b64a016860ab0dfbd) | 该 PNG 被修改为 blob `5c594edc33132f935805820216fee7aa0b0491ce`，提交主体是应用升级，没有说明图像创作过程。 |
| 2026-09-20 12:56:57 | [b7ac97a5](https://github.com/AvroraCL/CETUS-Desktop/commit/b7ac97a514c526726a92af51ec49eadce58be6ce) | 从更新后的4096px源图重生成 ICO、启动图和公告页版本，形成当前资产。 |

后续同日 [2cb79baa](https://github.com/AvroraCL/CETUS-Desktop/commit/2cb79baa167726200cc01ca387d31ce60f4ffc1b) 提到从更新图标生成安装器向导图，并刷新同色系 README 横幅。这是衍生导出说明，未说明图标原始绘画工具、模型或提示词。

### 三代源文件实查

额外下载早期两份小型PNG至忽略目录 `.local/cetus-research/`，各请求20秒网络时限、单文件5MB上限，实际合计不足100KB。实际看图确认两图是旧的抽象品牌标记，而不是 r1 人形头像，未发现1280×1280带水印的中间版本。

| 所在提交 | 尺寸／字节数 | 实测文件 SHA-256 | 视觉与元数据结论 |
|---|---|---|---|
| [f5aaadd1 原文件](https://raw.githubusercontent.com/AvroraCL/CETUS-Desktop/f5aaadd1b373a18226b2597352bfda664b024263/docs/CETUS-ico.png) | 1024×1024 RGBA；45,462 | `7b58c5cd9138c22fc520b8bf2d0af5247d122521b9f92f8f9644cea21463e0a4` | 抽象角形品牌标记与蓝点；XMP记为Photoshop27.0 Windows导出。 |
| [4d894cac 原文件](https://raw.githubusercontent.com/AvroraCL/CETUS-Desktop/4d894cac71aa51ea1a54009b64a016860ab0dfbd/docs/CETUS-ico.png) | 1024×1024 RGBA；46,897 | `2910ebe8e488eb0e0d4edb798440a8ee4027a83d1f1f325be2985286ee37f491` | 仍为旧品牌标记，不是r1；与上代XMP共享原文档标识。 |
| [b7ac97a5 原文件](https://raw.githubusercontent.com/AvroraCL/CETUS-Desktop/b7ac97a514c526726a92af51ec49eadce58be6ce/docs/CETUS-ico.png) | 4096×4096 RGBA；2,521,716 | `4da172c683d7981e170fc90d8e7d1bd8b4e7107799cdc12338859c82e6fb44fd` | 当前人形图标。主线程实际查看并完成下述同源比对。 |

当前4096px PNG自带XMP：`CreatorTool=Adobe Photoshop 27.0 (Windows)`，创建时间字段为 `2026-09-20T20:37:06+08:00`，最后保存字段为 `2026-09-20T20:54:23+08:00`，历史包含Photoshop格式转PNG的记录。它证明文件带有这条编辑／导出记录，**不能证明完整创作过程是手绘，也不能排除导入已有图像或模型辅助**；没有画师姓名、模型名、提示词或完整图层源文件。[固定源 PNG](https://raw.githubusercontent.com/AvroraCL/CETUS-Desktop/b7ac97a514c526726a92af51ec49eadce58be6ce/docs/CETUS-ico.png)

### 与用户 r1 的关系

主线程实际看图及随后alpha逐像素检查确认：当前4096图与r1为相同身份、同构图；上游自身已有圆角alpha，旧r1另外带水印及其alpha覆盖，二者不是字节相同文件。最初把透明展示误读为上游矩形背景的判断已纠正。4096→1280固定 LANCZOS 重采样没有移动或warp；在r1 alpha=255、原冻结水印区域以外的主体上，RGB MAE=0.1524848/255、RMSE=0.9220734/255、最大通道误差95分位=1，97.6918%主体像素最大通道误差≤2。[同源比对报告](../../../ref/subjects/deepseek/cetus-desktop/comparison-to-r1/report.json)

这些证据支持它们是同一图像内容的不同展示／导出版本，**不是 Skill 新绘制产物达到99%的证据**。已找到可直接研究水印下真实内容的高清文件，但该仓库路径历史没有记录1280带水印版本的具体传播或加工过程。当前工作采样只用上游RGBA，不能继承旧r1的水印alpha；两份原件均保留，旧冻结比较协议没有静默替换。详见 [当前参考合同](../../../ref/subjects/deepseek/cetus-desktop/reference-contract-v4.json)。

## 原始 SVG、设计源与生成方式

当前完整树未发现 `.svg`、`.psd`、`.ai`、`.xcf`、`.kra`、`.afdesign` 或 `.blend` 文件；现有 `scripts/` 为开发、运行、打包与烟测脚本，没有命名为图标创作／生成的脚本。此结论仅针对上述固定提交，不等于证明作者本地或其他仓库从未存在源文件。[固定完整树](https://api.github.com/repos/AvroraCL/CETUS-Desktop/git/trees/ebacdfa57200352cf29fdeda91f1c161082ae648?recursive=1)

历史确有鲸鱼标识 SVG 线索，但不得与 r1 混为一谈：

- [6241b218](https://github.com/AvroraCL/CETUS-Desktop/commit/6241b218b395f3948f9d248c729837c6f00532ef) 描述的是旧 **HECLM whale logo**，包括 `logo.svg` 以及未提交的 `docs/` 源文件。
- [202edb4e](https://github.com/AvroraCL/CETUS-Desktop/commit/202edb4ea8fc9000517d24404b3be50f08cf03dd) 明确改用 `CETUS-ico.png` 生成应用 ICO、用 `CETUS-ico-1.png` 生成标题栏图，并删除旧 `logo.svg/heclm-logo.svg`。
- [a5b2c2dc](https://github.com/AvroraCL/CETUS-Desktop/commit/a5b2c2dcca6d006068d71116b0bc2cb85bb546d2) 的 `scripts/make-banner.ps1` 是把既有图标排版为横幅的脚本；[aa93fa3a](https://github.com/AvroraCL/CETUS-Desktop/commit/aa93fa3aeca3224632ab9413303b3b16c6d48f36) 随后删除这套自动横幅，换成手工制作横幅。不能由“横幅生成”推断 r1 是代码生成，也不能由“手工横幅”推断头像绘画方法。

检索了此次 main 可达的184条提交说明（100+84条），并重点读了图标路径的提交详情。除上述PNG内的Photoshop导出元数据外，没有找到能确认 r1 绘画作者、原始 SVG/分层工程、绘图模型、完整提示词或创作参数的说明。[提交列表第1页](https://api.github.com/repos/AvroraCL/CETUS-Desktop/commits?sha=7f14ea7819dfb025bafce2f0d088e4901aefead6&per_page=100&page=1)、[第2页](https://api.github.com/repos/AvroraCL/CETUS-Desktop/commits?sha=7f14ea7819dfb025bafce2f0d088e4901aefead6&per_page=100&page=2)

## 许可证据与未知项

根目录 LICENSE 为 MIT，版权行署名 `Copyright (c) 2026 AvroraCL`；许可要求在软件副本或实质部分中保留版权及许可文本。本轮在当前树、README 和相关资产提交中未找到独立的头像作者署名、资产专属授权或第三方来源声明。[固定 LICENSE](https://github.com/AvroraCL/CETUS-Desktop/blob/7f14ea7819dfb025bafce2f0d088e4901aefead6/LICENSE)

因此当前可准确记录为“**MIT 仓库中公开提供的品牌 PNG；绘画作者与独立资产授权链未单独核实**”。根目录许可是明确的仓库声明，但不能仅凭提交账号推导原画版权归属，也不应将用户提供的带水印 r1 自动改标为 MIT。主线程的同源图像判定也不自动补足作者身份与原始绘图方式。

后续素材记录应绑定具体仓库提交、路径、下载文件 SHA-256 与实际尺寸，分别保存“上游原文件”和“为比较生成的派生图”；没有必要先修改水印或改动已冻结的 r1 检测区域来迎合新来源。
