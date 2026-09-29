# v6：源图结构边界修正

最终输入是 **`final/geometry.json`**，SHA-256 `8c251ff7add8cefd0737b4e2d0586b8e961b17de33e83051d4b0b364a5bbfebd`。完整拟合 masks 与五个不透明 underpaint 位于 `final/masks/`。绑定的源图 SHA-256 仍是 `60c234f594ad81319fa74bb4fa8392f10a125127d46bf1d3b47e618b25813da2`，源图未修改。

## 实际观察与修改

- 主发束与右发的分界弧线在 v5 中过早向左收缩；按源图 `(x,y)≈(579,300)、(633,350)、(668,400)、(696,450)、(719,500)、(738,550)` 修正。源图在 y600 后逐渐减弱为色场过渡，不能沿该曲线加描边或新增亮条。
- 右脸侧折缝原始 v5 手工曲线从 y740 开始，源图实际约 y672；恢复长而连续的暗折面。这里旧的浅色色场必须重拟合。
- 右内折恢复源图两条连续曲线。y980 以下左侧边缘跟随真实脸部遮挡，不把潜在完整发束画过皮肤缺口。
- 中央右折缝延伸至源图脸部交界。鳍浅边只移动两个内折面间的边界，共 77 个 mask 像素，外侧浅边轮廓未改。

43 个语义面中改动 7 个：`hair-front-main`、`hair-right-fringe`、`hair-center-right-crease`、`hair-right-face-crease`、`hair-right-underfold`、`whale-side-fin-rim`、`whale-fin-rim-left-fold`。脸、双眼、整体 subject 及五个 underpaint 的路径与 masks 保持原样。没有新增面、调色板分块、模糊或高光碎片。

## 验证与实际限制

已观看源图与 v004 局部对照，以及实际 SVG 路径叠在源图上的 `final/source-path-overlay.png`。`final/rendered-boundary-measurements.json` 对真实 SVG 光栅边界进行测量，保留 subpixel 尖端的覆盖率阈值为 8/255，不做画布变换或配准。

| 局部源观察点到实际渲染边界 | v5 平均 / 最大距离 | v6 平均 / 最大距离 |
| --- | --- | --- |
| 右脸侧折缝，13 点 | 24.78 / 75.00 px | 0.49 / 1.41 px |
| 右内折，21 点 | 3.30 / 11.00 px | 1.02 / 2.24 px |

这是离散源观察点的局部边界距离，不是整个画面的相似度、独立验证集或用户接受标准。源观察点和边界模型同属源辅助研究，因此该数值不能证明技能泛化。

`final/*-geometry-ab.png` 和 `final/geometry-only-old-paint.svg` 固定沿用 v004 旧色场，只隔离几何修改的影响。右缝的大面积暗面之前被错识为浅细线，所以旧色场套在修正几何上会出现不自然亮面；这组诊断图不得作为新版图标交付。旧色场下部分 RGB 误差上升已如实保留在 `refinement-evidence.json`，不伪装成总体改善。

未解决：大面自然光泽、右发侧光、眼缘的色场、整体相似度，以及独立 Skill 出图效果均需后续拟合/渲染/用户审查。鳍浅边仍有低幅亮缘，此处属于 paint 模型，不用添加几何碎片补偿。

## 快照与执行记录

首次交接的 manifest SHA-256 `7772af7a8301b53d2bb024b0929e306ec43c38d5bcd81004bee4f4052b61f43b` 已完整保存在 `attempt-01/`；它与 paint 的 `natural-fields-v6/main-fit/geometry-input/` 相同。其二值 mask 再拟合吞掉了窄折缝尖端，之后撤回，未冒充最终冻结版本。`snapshot-index.json` 记录两者关系。

实际执行程序是本目录根部 `refine_geometry.py`、`measure_paths.py`；每次由 `tools.run_visual_e2e.run_bounded(..., timeout=48)` 外部监督，几何内限 43 秒，实际均在约 3 秒内退出。`final/` 中同名脚本只是当时执行代码的证据副本，不应直接从快照目录重新运行。最终 snapshot 数据不会原地修改。
