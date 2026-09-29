# Cetus 提供的 r1 高清来源

用户于2026-09-29指明来源，已下载并实际看图核对。仓库固定提交为 `7f14ea7819dfb025bafce2f0d088e4901aefead6`；[原文件](https://github.com/AvroraCL/CETUS-Desktop/blob/7f14ea7819dfb025bafce2f0d088e4901aefead6/docs/CETUS-ico.png) 为4096×4096 RGBA PNG，无右下水印。`original` 表示下载原字节，不代表已取得画师分层母版。未找到该头像的 SVG 或 PSD。

`CETUS-ico.original.png` 保存4096文件；`CETUS-ico.site.png` 是网站1024圆角版本。实际文件与哈希见 acquisition.json。根目录仓库声明MIT，画师和独立资产授权链尚未核实；这是本项目研究参考，未纳入 Skill 分发素材。

对照 user-mode/r1.png：构图与主体一致，上游原件自身已有圆角展示alpha，旧r1另外含水印及其覆盖alpha。4096只按全画布比例缩到1280，不移动、不扭曲，在旧r1不透明主体及固定水印区外测得通道MAE 0.1525/255；详见 comparison-to-r1/。这个测量验证来源关系，不是新SVG或Skill达到99%。

## 当前校准输入

**当前只使用 `r1-clean-source-1280.png`（SHA `60c234f5…813da2`）**：所有RGBA均来自4096原文件的LANCZOS统一缩放。水印下内容与真实透明度来自上游，无生成补绘。normalize_reference.py可复现，reference-contract-v4.json冻结全部哈希。

保留的失败记录：v2把旧r1 alpha套到新RGB上，导致水印在原本透明处留下黑字形，已拒绝；v3尝试取两者alpha交集，但上游自身已有正确裁切，无需再次收紧，未用于新候选。`r1-clean-calibration-1280.png`、`…-v3.png`及对应合同只保留历史诊断，禁止用作当前真值。

旧r1原件和旧比较协议保持不变。新基准不再排除水印区，所有可见部位参与比较；不能把旧版排除区后的指标与新版全域指标直接当同一序列。源图黑底只用于参考观察，最终SVG仍须透明。

若该来源今后不可获取，用户已明确继续使用r1去水印工作版校准，不能因此搁置。当前已有同图真无水印源，无需执行该备用补绘路径。

完整来源调查：[cetus-r1-provenance](../../../../docs/research/entities/cetus-r1-provenance.md)。
