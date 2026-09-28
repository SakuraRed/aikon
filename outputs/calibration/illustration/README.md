# 立绘单例校准实验

前批SVG已被用户完全拒绝。本目录只处理 `img_1.png` 这一个主体，停止扩大批量；参考仍为用户r1/r2及原站示例。

## 实际图像提示词实验

| 产物 | 实际条件 | 不能声称的结论 |
| --- | --- | --- |
| `short-faithful-v1.png` | 忠实中文short正文，加参考角色说明和透明/无水印覆盖 | 不能从一次随机结果断言中文优劣；该图有可见的面部噪点/灰色污染，不是合格目标 |
| `short-imagegen-v1.png` | 同一主体/模式参考，short语义加连接、脸域、曲线等校准说明 | 是待评诊断参考，不是SVG，不是用户gold，也不保证遵循所有数字 |
| `full-imagegen-v1.png` | 完整中文full正文，加同一主体形态说明与运行覆盖 | 与short并非严格单变量实验；出现衣领等内容仍需对照用户目标 |

工具：内置 `imagegen`，`transparent_background=true`，三个本地参考按 Subject / Style / Style 指定。工具没有开放固定seed。实际提示词分别存对应`.prompt.txt`。没有声称进行韩文/中文对照，因为这次未运行韩文条件。

源提示词译改保留原作者 @multi_serio_ai(APG)、[原站](https://grokbot-icon-studio.serio-ai.chatgpt.site/zh-hans)和[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)来源条件。用户立绘仅用于本次指定创作，不宣称角色或原图权利归项目所有。

## 代码路径实验

`vector-study/` 是将short校准PNG转为真实路径的受控近似实验，目的是检查代码能否保住已经可见的轮廓与色面关系。粗细档位不是short/full两种profile，不得改名冒充。最终可编辑性、矢量化误差和视觉效果分别记录。

该实验依赖一次imagegen参考，不能据此宣称技能已脱离绘图模型或任意模型效果相同。只有实际SVG的渲染与用户反馈可决定后续采用何种生产路径。
