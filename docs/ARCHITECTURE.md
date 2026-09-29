# ARCHITECTURE — Aikon

当前处于单例校准与上色约束实验。产品边界见 PRD，兼容性研究与实测结果分别记录。

## 稳定边界

风格参考与主体参考 → 澄清约束 → SVG 创作 → 渲染检查 → 用户反馈 → 新版本。

- 技能入口：标准 SKILL.md 与相对路径资源，提供必要操作知识。
- 视觉知识：从来源样例提炼的概念、观察和可验证约束，明确来源原话与 Agent 推导。
- 交互适配：按能力发现宿主的原生提问和图像显示工具；不假设统一工具名称或问题数量限制。
- SVG 创作与验证：代码生成或编辑可读矢量结构，分别检查文件结构和真实渲染。
- 版本记录：保存约束、产物、反馈、父版本关系；默认目录方案待研究与访谈收敛。

## 当前代码路径

`skills/aikon/` 为自包含分发目录。可选 Python 标准库 helper `aikon.py` 接受版本化 scene 数据；它是一个基础几何子集，旧示例不是审美 gold。主体由自定义路径和图层表达，不能用同一脸盘套所有主体。没有 Python 时可直接编写 SVG，明确减少了哪些自动检查。

`paint_svg.py` 是另一个独立入口：已确认 geometry + 绑定源哈希的 paint plan → 静态 SVG。它保留选定物体的 path/transform，移除旧 paint，生成不透明底色、有限平滑色场及有 receiver 的阴影。对阴影/腮红在共同父坐标系施加 clip，防止旋转 overlay 连带错误旋转 receiver。编译器只依赖标准库，不联网、不调用绘图模型。相同 geometry、plan 和编译器版本应导出相同 bytes；从任意原图建立好 geometry 仍需 Agent 的观察和绘制能力。

研发验证工具与分发包分离：`tools/render_svg.py` 用固定 resvg 渲染；`tools/paint_checks.py` 从全部选中图层生成真实掩膜并按遮挡次序分配可见材料；`tools/analyze_paint_fields.py` 测量材料内部 grain/mottling/alpha/色岛；`tools/run_visual_e2e.py` 重放 short/full 并记录正负控制。依赖在 `requirements-ci.txt` 锁版本和 wheel hashes，不进入核心 Skill 强依赖。

新项目未提供存放方式时先原生提问，helper 只接收已选项目路径。snapshot 创建新版本，不推断用户偏好，不自动创建或推送 Git。

输入研究层把概念、名称、图像、URL及可读取的其他模态归并为主体资料；再将同一round分别映射到short/full profile。每个profile保存实际生产提示词、scene、SVG和revision。`background: null`是透明导出，纯色背景仅兼容显式请求。忠实源译文与运行覆盖分开，禁止将源charcoal/单图要求重新覆盖用户透明/双版指令。

`ref/` 与 `docs/research/` 是仓库研究资料；分发参考位于 `skills/aikon/assets/examples/`，由原创场景生成，两者不混包。

## 可移植性

核心工作流不强制 Jev、AnySearch、某个图像 API 或本机脚本路径。研发使用这些工具不代表终端用户必须拥有它们。增强工具应当有能力探测及明确降级边界。

## 验证分层

当前 `natural-gloss-v2` 由各主体的标准库源码直接生成带linear/radial材质的SVG，绕开不能表达该风格的旧paint-v1子集。`tools/review_gloss_pairs.py` 对实际六份图作静态结构、透明内部、眼睛可见、缓存PNG来源和两版几何区别检查，并输出24份真实渲染及哈希。合法gloss和有不透明底层的透明glaze保留，纹理high-pass仅作advisory；不把旧窄色差阈值套到新图。正常画布边缘AA与内部漏缝分开记录，有独立正负控制。

技能结构检查只能证明包的基本格式。行为测试观察是否尊重输入、问答与修改边界。视觉测试必须实际渲染并查看。跨模型或跨 harness 的声明必须基于相应实测，不能从同模型多个子 Agent 推广。

像素检查排除明确材料边界并公开排除比例；窄区域无足够纹理样本时标记不足，不能冒称全覆盖通过。声明为 smooth field 的区域才禁止意外色岛；官方合法高光不能因有色岛被全局拒绝。轮廓抗锯齿与主体内部透明分开。CI 报告 `no_rule_failure`，高光自然性、身份与用户验收保持独立状态。
