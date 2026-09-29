# v6 局部语义几何修正：实际执行 brief

本次只研究无水印 CETUS 源图的真实材质边界。基准为 `ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png`，SHA-256 `60c234f594ad81319fa74bb4fa8392f10a125127d46bf1d3b47e618b25813da2`；比较对象为 `revisions/v004/short.svg`，其几何来自 v5。

先放大对照右脸侧发缝、右内折、主发束分界和鳍浅边。只修正能在源图中连续追踪的实际边界；大面积亮暗渐变交给 paint-field 研究，不能通过新增亮针、调色板块或碎片掩盖色场误差。

保留原画布、脸部投影、眼位、真实胶囊形状及整体外轮廓；原始参考不作修改。交付完整 masks、五个 underpaint、geometry manifest、局部路径叠图和逐项差值。未解决项如实记录；这个源辅助的几何研究不证明独立 Skill 的泛化效果，也不宣称满足用户的 99% 相似要求。
