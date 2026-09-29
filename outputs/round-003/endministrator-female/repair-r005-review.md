# r005 边缘修复：首次有界尝试通过

输入是三张实际 r004 SVG；prompt 已在执行前保存。没有修改冻结阈值、绘图模型、底色或角色几何。修复采用 [显式材料编译器](../../../skills/aikon/references/material-composer.md) 的一次采样原则，但本轮处理多面硬件的精确联合轮廓，所以使用本目录 [repair_r005.py](repair_r005.py) 对实际 SVG 作结构变换，没有套用角色模板。

| 候选 | r004 最大局部簇 | r005 最大局部簇 | 当前结果 | 1280 RGBA变化像素 | 1280 alpha |
| --- | ---: | ---: | --- | ---: | --- |
| unmasked full | 6 | 1 | no_rule_failure | 334 | 全部相同 |
| masked short | 11 | 2 | no_rule_failure | 1588 | 全部相同 |
| masked full | 17 | 2 | no_rule_failure | 1760 | 全部相同 |

规则仍是颜色残差大于32/255的局部簇最多3个原始坏像素，一像素间隔连接。比较仍为256px原生SVG与同一SVG的4×精确渲染、预乘sRGB BOX面积积分。数值不表达相似度百分比。

## 结构与因果范围

面罩的原始多边形顶点不变，只统一绕行方向，将同向子路径写成一个 nonzero 联合外轮廓 clip。局部不透明同材质支撑完全受这个clip限制；原硬质分面、浅色折线、黄色连接件及先后关系保留。外部覆盖仅采样一次，内部小面积边缘误差混合本材料，而不再次混入下方浅色皮肤。

右外领使用原 `outer-collar-right-face` 的真实路径作clip，内部支撑使用原外领材料，随后绘制原face/fold。新支撑仅存在于原外领内部。原语义路径的 `d`、尺寸及transform属性逐一核对不变；新增包装组没有引入transform，整幅alpha在1280逐像素相同。没有背景矩形或未裁切的支撑层。

这次受控变换和同位置残差下降支持“重复边缘采样是这些失败的重要原因”，不证明所有其他作品的失败均有同一原因。未修改全局检测器。

## 实际视觉证据

以下每张左到右为 r004 native、r004 4×BOX、r005 native、r005 4×BOX；第一排浅底、第二排深底，裁切坐标固定为 r004 原失败位置。绘图Agent已实际查看三张局部和三张修复后的1280大图：

- [无面具full领翼对照](unmasked/full/revisions/r005/quality/same-location-before-after.png)
- [戴面具short鼻尖对照](masked/short/revisions/r005/quality/same-location-before-after.png)
- [戴面具full鼻尖对照](masked/full/revisions/r005/quality/same-location-before-after.png)

目视未见造型/光泽组织变化；原生鼻尖和领翼边缘较贴近面积参考。未重画已经通过的 unmasked short，它仍为r004。最终四张1280/128/48/24预览重渲染RGBA均与缓存相同，两张无面具的实际capsule隔离检查继续通过。总览和四底色检查已经同步当前SVG。

完整机器结果见 [repair-r005-report.json](repair-r005-report.json) 与 [checks.json](checks.json)。历史 r004 的真实失败仍保留在 `quality-r004/` 和 `checks-review-r004.json`。

状态限于本次结构、边缘与目视核对；grain/mottle完整人工材质域评估未完成，用户审计及99%目标仍未获结论。
