# 上色修正与验收证据

## 用户反馈与执行取舍

用户肯定整体构图、否定纹理与不自然高光，明确 DeepSeek 以 r1 为典型。本轮直接记录这些选择，没有重新提问。保留历史全批拒绝，停止扩量。

工程取舍采用冻结geometry、显式paint plan、确定性编译与分层检查。Jev实际结果保存在[请求](decision-request.json)与[响应](decision-result.json)：`paint_backend.analytic_plan=1.0`、`ci_gate.layered_evidence=1.0`，其他各选项为0。其含义是给定当时上下文的条件选择分布，既不是成功率也不是质量分数；模型同时返回的confidence不代替该分布，更不代替用户选择。代价是必须先整理语义几何和材料，且还需实际视觉检查。

调用时尚未完成后续真实full纹理定位；请求中的“轻纹理不能可靠区分”描述后来被收窄为首张short图。后续发现full圈注两个平滑区域可被冻结阈值检出，未重写原始请求记录。

## 实际创建、失败与修正

1. 在保存中文执行prompt后，基于semantic v4几何创建v5 short/full plan，用标准库编译得到SVG，再用固定resvg实际渲染。
2. 首轮[失败报告](e2e-initial-failure.json)抓到中央阴影离receiver边界3px，超过固定2px；其余材料像素无规则失败。保留失败产物与检测证据。
3. v6删除无依据中央阴影，未降低门槛、未改主要几何，双版重新编译及真实渲染。
4. 独立审计额外发现并修复检查器的既有clip几何和gradient计划核对缺口；各有真实篡改回归用例。
5. 按同一冻结规则加入6张真实正参考、已圈注full缺陷及short已知检测局限。正例允许渐变/抗锯齿，负例保留具体失败代码，不能只用合成噪声证明缺陷已解决。

本轮未调用绘图模型。此结论仅覆盖上色与验证路径；源geometry仍继承前轮模型辅助的诊断及矢量重建。

## 证据分层

- 结构：绑定源哈希，选定geometry、已有clip与canvas冻结；实际solid/gradient与plan一致；无未规划绘制形状、图像或filter。
- 像素：全部选中层以实际transform/clip渲染mask，按遮挡次序检查可见材料；检查内部纹理、alpha、意外色岛及阴影边界归属。公开排除区域和窄区域样本不足。
- 回归：真实参考和缺陷、10项独立注入正负控制、损坏合同和超时进程树回收。
- 视觉：主线程实际查看真实SVG渲染；干净程度改善，但中央发束较平，不宣称高光自然性自动通过或最终用户接受。
- 泛化：独立Agent消费当前Skill测试同一几何的新paint方案；仍属于同一宿主/模型家族，跨harness、跨模型和新几何生成保持未验证。

本地最终结果见[e2e-final.json](e2e-final.json)：16.695秒，short/full、10项注入控制及8个真实图像回归符合预期。JSON中的运行内相对路径对应 `.local/e2e-final/`，可通过E2E入口重建；历史完整真实参考证据保存在本目录 `evidence/`。

75项测试在本地Windows/Python3.13.3上通过，用时12.063秒；skill-creator quick_validate通过。独立消费者[报告](../../../outputs/agent-paint-e2e/report.md)保留实际prompt、两轮产物、失败、像素mask和视觉反证。其试用暴露Windows stdout编码差异；编译器随后改用ASCII兼容JSON stdout、UTF-8报告文件，并以中文reason在ASCII控制台下的真实CLI测试验证。

GitHub CI 状态以本次实际run为准；本地通过不代替远端运行。高光自然性及最终艺术质量从未由这些绿灯宣布通过。

独立试用的视觉反证已回写Skill：paint-only冻结前先核对发束分组；缺失分组的geometry不能借删除高光获得整体通过。后续只在新几何版本内重建必要材料边界，保留已有构图。远端首次验证已完成但Artifact配额失败，处理见[CI记录](renderer-ci.md#实际远端失败与证据保存修正)。
