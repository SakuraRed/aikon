# v5 来源纠正执行 brief

在真实重新执行前保存。本轮仅更换为上游完整原始RGBA统一缩放的工作源 `ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png`，SHA-256 `60c234f594ad81319fa74bb4fa8392f10a125127d46bf1d3b47e618b25813da2`。v4算法保持不变；重新计算全部语义mask、父层支撑与路径，不仅替换metadata/hash。

不继承旧r1 alpha，不引入水印排除、局部补绘或隐式ROI。v4使用旧展示alpha的工作源已弃用，保留作历史记录。只新增v5，不新增设计轮次。
