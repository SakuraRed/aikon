# 决策索引

## 用户已明确的约束 — 2026-09-28

- 仓库为 private GitHub repo `SakuraRed/aikon`，本地根目录为当前仓库。
- 分发物是脱离特定环境的标准技能；输出为 SVG；鼓励使用代码绘制。
- 研发先研究网页及前置事实，再 grilling；用 Jev 辅助当前研发决策，使用原生提问。
- 创建、测试、视觉验证、反馈、修正形成可继续的循环，合理利用子 Agent。

这些记录来自用户原始任务，不是访谈推测。后续决策详情存 GitHub ticket 的 resolution comment，本文件只维护简短索引，避免双重状态来源。

## 已完成调查与访谈

- [网页与提示词研究](https://github.com/SakuraRed/aikon/issues/2#issuecomment-5871113358)：完整提示词证据、样例偏差与来源许可。
- [可移植性与 SVG 验证研究](https://github.com/SakuraRed/aikon/issues/3#issuecomment-5871114901)：格式、工具能力和验收证据分层。
- [两轮产品决策](https://github.com/SakuraRed/aikon/issues/4#issuecomment-5871118157)：真实用户回答及独立列明的工程取舍。

当前待验收：[首版技能与原创 SVG 参考](https://github.com/SakuraRed/aikon/issues/5)。

- [首次视觉反馈后的双版本/全模态覆盖与测试分支](https://github.com/SakuraRed/aikon/issues/4#issuecomment-5872211140)：透明无水印、更强近景、完整中文提示词、七个主体分支和已选存放位置。

- [用户全批否决与单例校准](https://github.com/SakuraRed/aikon/issues/5#issuecomment-5873241375)：旧14图不合格；当时的方向问题未取得答案。该空答案不会变成批准，后续由2026-09-29新反馈给出继续方向。

## 2026-09-29 明确反馈与工程执行

用户肯定当时单例整体构图，拒绝纹理和不自然高光；DeepSeek明确改绑r1的主体/模式，不能再用通用鲸鱼logo替代该人物。r1中的鲸鱼形态特征仍须提取并保留。该阶段保留主几何、以解析paint重建色场、建立反模式及真实像素CI，停止扩量。属于用户明确反馈，无需重投票。

工程取舍与Jev原始条件概率、真实失败及修正见[上色迭代](validation/paint-fields/iteration.md)。[双版本创作闭环](https://github.com/SakuraRed/aikon/issues/5)保持开放，因为单例的发束层次仍需视觉精修，未取得最终接受，也未做跨模型/跨harness实测。

## 同日新反馈：恢复自然光泽和可见profile差异

用户明确认为当前版本完全扁平、双版无区分度；r1中的自然渐变、头发高光和眼缘光泽应保留，full整体采用新附件。当前运行覆盖见[natural-gloss-v2](../skills/aikon/references/natural-gloss-v2.md)，研究与像素剖面见[参考复核](research/natural-gloss-profile-v2.md)。旧窄色差/纯色眼/默认零高光不再约束这一配置，源译文未改。

Jev当次实际条件判断支持 `direct_vector_fields=1.0` 与 `field_and_visual=1.0`；其他候选各为0，原始请求/响应保存在 `validation/gloss-v2/decision-*.json`。这是已委托工程选择，不是成功率、质量评分或用户投票。该阶段执行的三个主体六份图随后被用户全部拒绝，不代表当前接受状态。

## 当前未答与参考状态

原生问题先前空答历史保留于[首轮摘要](validation/2026-09-29-current-user-decisions.md)。重新逐题呈现后，女、男管理员各自实际选择“两种都画”，分别展开 masked/unmasked × short/full，共八张；[工具原始结果及Jev绑定](validation/2026-09-29-live-native-answers.json)。R1 的99%验收含义表单仍空答，标准保持待定。管理员分支、数值验收标准、视觉接受分别记录，不能互相替代。

后续合并表单已收到[真实答复](validation/2026-09-29-batched-native-answers.json)：R1先建立明确数值合同，具体阈值下一轮定标；DeepSeek full先选服饰参考，再绘制衣装。用户要求合并独立问题、尽量多采集；按原生schema当前每轮最多3题，直接阻塞调用、不附加Agent计时，宿主等待限制未被关闭。以上均不构成对现有图片的接受。

下一轮合并表单已选[严格B数值合同与A蓝白女仆衣装](validation/2026-09-29-contract-outfit-answers.json)。B要求主体及每个关键局部99%像素的RGB最大通道误差≤5/255，并同时通过整体/局部误差和轮廓门槛；背景RGB不计分，所有最终图必须透明可编辑SVG。选定A仅给DeepSeek full提供白褶胸片、深蓝领结和肩带；r1头部身份保持，不把替代衣装称为r1已确认原作设定。分支与合同已经确定，作品仍待检测及用户审计。

已核实Cetus同图高清无水印源；新工作入口为[r1-working.png](../ref/user-mode/r1-working.png)，原r1保留。具体作品和未完成任务继续由[双版本创作闭环](https://github.com/SakuraRed/aikon/issues/5)追踪。
