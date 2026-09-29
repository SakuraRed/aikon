# 管理员条件式 prompt 包

状态：`both-branches-authorized`。整理日期：2026-09-29；原始审阅基线：`05aed2d8e9b74e56190d85210d5382306cdf6866`。用户在两次独立原生问题中均选“两种都画”，详见[真实答复](../../validation/2026-09-29-live-native-answers.json)。本包供实例化八张管理员生产 prompt，作品仍需验证和用户审计。

男女是两个独立 entity。女管理员用 [female.md](female.md)，男管理员用 [male.md](male.md)。每个实体均有独立真实答复，不重复询问面具选择，也不登记视觉验收通过。

## 1. 真实答复门槛

历史[纠偏计划](../../plans/2026-09-29-correction-plan.md#3-面具问题状态)及首轮空答案保留。当前状态来自后续单题表单的真实回答，历史推荐和 Jev 判断不构成选择。

```json
{
  "status": "both-branches-authorized",
  "entities": {
    "endministrator-female": {
      "question_id": "female_mask",
      "answer_status": "answered",
      "chosen_branch": "both",
      "answer_evidence": "../../validation/2026-09-29-live-native-answers.json#female_mask"
    },
    "endministrator-male": {
      "question_id": "male_mask",
      "answer_status": "answered",
      "chosen_branch": "both",
      "answer_evidence": "../../validation/2026-09-29-live-native-answers.json#male_mask"
    }
  }
}
```

以下只定义允许映射，不含推荐、默认或预选项。

| branch id | 对应历史题选项 | 获得该实体真实回答后的展开 | 尚未回答时 |
| --- | --- | --- | --- |
| `masked` | 保留面具 | 正常佩戴分支的 short / full，共 2 图 | 不展开、不绘制 |
| `unmasked` | 不戴面具 | 完全移除面具分支的 short / full，共 2 图 | 不展开、不绘制 |
| `both` | 两种都画（历史草案称“两种都对照”） | 两份独立分支合同，各有 short / full，共 4 图 | 不把“准备两套模板”解释为选择两套 |

执行前逐实体检查：真实答案能指向该 `question_id` → `chosen_branch` 对应答案 → `answer_evidence` 记录原话与可追溯位置 → 该分支证据前提满足 → 分别保存 short/full 生产 prompt。任一值仍为 `null`、答案仍为空、来源只有 Agent 建议或 Jev 输出时，保留阻塞状态。不要以 `masked`、`both` 或历史产物填空。

此状态是输入证据快照，不是另建项目状态来源；Issue 生命周期仍由[项目地图](../../wayfinding.md)管理。本包不自动关闭任何决策 ticket。

## 2. 组装顺序与来源边界

仅在上述条件满足后组装：对应完整源译文 + 当前共同覆盖 + 单一实体事实 + 获答面具分支 + 对应 profile 条款 + 当次几何/上色/验证计划。`both` 应分别组装 masked、unmasked，不能把互斥条款拼成一段。

源文件保持原样，并需在执行时实际读取全文：

- [source-short.zh-CN.md](../../../skills/aikon/references/prompts/source-short.zh-CN.md)：原作者精简版完整研究译文。
- [source-full.zh-CN.md](../../../skills/aikon/references/prompts/source-full.zh-CN.md)：原作者完整版完整研究译文。
- [profiles.md](../../../skills/aikon/references/profiles.md)、[natural-gloss-v2.md](../../../skills/aikon/references/natural-gloss-v2.md)：当前运行覆盖。
- [规则差异表](../../plans/2026-09-29-prompt-rule-reconciliation.md)：纠正历史错误的依据；旧产物和旧 prompt 不是身份参考。

两份源译文来自 APG / @multi_serio_ai，保留其 CC BY-NC 4.0 与[第三方说明](../../../skills/aikon/THIRD_PARTY_NOTICES.md)。本包是分支补充，不冒称忠实译文；组合使用时不取消源文本许可。官方图片仅作私有研究，未核实再分发许可。

| 项目 | 源 prompt 基线，不能改写成作者原意 | 当前执行覆盖与来源 |
| --- | --- | --- |
| 背景与输出 | 炭灰背景、单 profile 单图 | 用户已要求透明、无水印、真实矢量 SVG；每个获答分支同轮 short/full。[profiles](../../../skills/aikon/references/profiles.md) |
| short | 奶油脸、粉彩概括、约 3:1 等形平行胶囊眼、顺时针约 15°、紧裁切、无躯干 | 保留实体原色识别；依 r1 观察建立脸域和自然色场，不移植 r1 的蓝发/褶边/蝴蝶结。管理员没有获得 DeepSeek 的“r1 身份”绑定。[差异表](../../plans/2026-09-29-prompt-rule-reconciliation.md) |
| full | 主体原色、约 2.5–3:1 胶囊眼、顺时针约 15–20°；身份元素约最多三项；必要时少量领口 | 同尺寸内增加有官方依据的颈领与服饰范围，以 r2 取景为参照；相应改变内容与几何，不能只缩小 short。[profiles](../../../skills/aikon/references/profiles.md) |
| 眼睛可见性 | 双眼完整可见，眼形和风格优先 | **仅在用户实际选择 masked / both 中 masked 子分支后**，正常遮眼装置成为对“两眼全露”的明确例外；此时不显示被遮住的眼睛，也不在面具上画替代眼。[纠偏计划](../../plans/2026-09-29-correction-plan.md#3-面具问题状态) |
| 眼色与光泽 | 近黑纯色、不画眼内渐变或反光 | 无面具资料保留来源眼色；另记为暗色 capsule 材料映射，允许微弱连续色场/一体边缘光泽，不加虹膜、眼白或独立白点。[natural-gloss-v2](../../../skills/aikon/references/natural-gloss-v2.md) |
| 倾斜与仰头 | 规定画面内顺时针倾斜 | roll 与 pitch 分开；由脸域、发际、眼线、颊/下巴关系构建自然仰头观感，`rotate()` 不等于完成 pitch。单图不推导唯一真实 3D 角度。[差异表](../../plans/2026-09-29-prompt-rule-reconciliation.md) |

## 3. 两分支共同的条件式执行段

下面是组装材料，不能独立越过答复门槛。

```text
Round / Entity / Branch / Profile：<保存实际 round> / <独立 entity> /
  <来自真实答案的 masked 或 unmasked 子分支> / <short 或 full>
Decision evidence：<该实体真实答案；没有则停止，不得继续填模板>
Reference basis：<实际选用的图片、版本类别、内容哈希与本次看图记录>
Source prompt：读取并保留本 profile 完整源译文；以下列出冲突覆盖，不修改译文。

主体身份仅取本实体事实表；风格参考 r1/r2 只提供构图、capsule 和色场规律。
先列实际可见脸域、发根/主发束/侧束/后发、配件连接与遮挡，再构建 SVG 路径。
不要复制被拒绝的管理员 SVG，或套同一个头部模板后增删附件。
佩戴与不佩戴是互斥合同；正常遮眼的面具不能上移为额饰，也不能半透明以露眼。
无面具分支完全移除抑制器，不保留虚构额冠；眼镜只能来自所选图明确可见的证据。

未被面具遮挡的眼睛必须是两枚同源、等形、平行的竖向 capsule：局部正置时为
近直侧边接圆滑端帽，而非普通 ellipse。short 约 3:1，full 约 2.5–3:1 是源基线。
若强参考投影确需改变，单独记录此实体、本 profile 的依据及投影映射；不得把
r1 在 DeepSeek 案的观察值抄成所有管理员的默认比例。先检查端帽/侧边，再检查眼对。
源眼色是观察，暗 capsule 色值是创作映射；两者分别记录，不能称映射色为官方色值。
脸域圆润、无嘴鼻；不因省略嘴鼻就用通用圆盘替代该实体的发眼与下颌关系。

以不透明材料为底，用 linear/radial gradients、顺形宽受光和有真实接触依据的
遮挡阴影表达自然光泽。头发软曲面与抑制器/发卡硬质转面分别处理。
禁止云斑、grain、纹理滤镜、量化碎片、塑料亮心、悬空亮片和独立白眼点。
透明的是画布，不是整个主体；不把位图嵌进 SVG，不带外部图片依赖。

short 与 full 使用相同画布尺寸、同一实体/面具选择/服装版本；full 须实际显示
本实体官方颈部—内领—前扣—外领/肩领的连接。头部布局、下缘裁切及新增部件
共同改变，禁止“缩小 short + 任意领子”、只加发束、只改色或换文件名。
保存实际 prompt 后才绘制；任何可见几何/上色修正先记入 revision prompt。
```

## 4. 证据前提与未证字段

本次实际 `view_image` 查看：男女官网完整立绘、A/B 人物卡、0212/0305 无面具专题图、抑制器独立展示图，以及 r1/r2。各实体文件记录具体部位与来源；未读取新网络资料、未取得官方 3D 视频帧。

官方专题无面具图可以证明这些插画中的脸域、眼色范围、发型和共存配件；不能证明当前 3D 模型的精确色值、瞳孔构造或所有剧情状态。实例化时必须填写 `reference_basis`：优先遵循用户已指定的版本；未指定时，Agent可把已有官方专题插画登记为工作依据，并明确其证据范围，无需额外制造一轮版本投票。只有任务明确要求当前实机/3D一致时，才须补可定位的官方帧和版本，缺失则保持该项未满足。不能把插画默认为实机资料。

同理，已有图支持女性发卡可见多片结构，不支持隐藏锁扣工程图；清晰 B 卡可作为本轮可见结构近景，但不解除隐藏构件未知。图像存在并被查看不等于几何已被绘对。

## 5. 反向审查清单

生产前先对组装文本逐项反查；目前只审文本，不声称已运行下列作品检查。

- 若 `chosen_branch` 空缺却出现“用户选择戴/不戴”“开始绘制”或预选目录，退回阻塞状态。
- 若戴面具仍要求完整露出两眼、面具上移、薄黑条/额冠替代、在面具表面画眼，合同冲突，不能执行。
- 若不戴面具仍引用 masked 图断言眼色、加无证据眼镜、加写实虹膜，退回来源核对。
- 若女性任一分支只写“X 发卡”或只剩两根等宽平面条，未保留已见多片叠接；若男性继承此发卡或女 bob 几何，实体串用。
- 若 capsule 由普通 ellipse 冒充，或只核长宽比不核端帽/侧边/眼对，眼形未通过。
- 若 full 没有自己的取景条款与实体服饰来源，或只整体缩小 short 后加通用领子，双版差异未通过。
- 若自然仰头仅由整体旋转解释，或把本包完成、结构检查通过记为用户接受，证据越界。

真实生产后仍需实际渲染、深浅底 alpha 检查、128/48/24 px 与大图看图、头发/配件/眼部/颈领局部对照、short/full 同尺寸并排，以及用户反馈。masked 的眼可见性检查标记为“已获答遮挡例外”，不能为了让检测器通过而改坏装置。
