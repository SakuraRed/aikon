# Round-003：已执行验证及未通过项

## 真实用户决定

男女管理员各自选择masked/unmasked两分支，每支short/full；R1选择严格B像素合同，并再次明确透明SVG、背景RGB不计分；DeepSeek full选A蓝白女仆衣装。这些是原生工具取得的真实回答，与Jev条件概率、机器门禁和作品接受分别记录。

## 代码与检测器

- 在现有固定本地venv运行122项图像质量相关测试，全部通过，无skip，17.513s。新增14项B合同检查包含主体/局部独立命中率、边界与透明污染、背景RGB排除、合同/源图/mask篡改拒绝、worker状态码与模拟超时。测试中的timeout消息来自mock控制，不是实际作业超时。
- 独立读取审查确认用户B含义、输入绑定及背景排除；发现CLI超时返回码不统一后已修复为124，并加入控制。
- 真实来源/旧拒绝样本的capsule、edge、paint detector审计通过，12.922s；其含义是正负控符合预期，旧round-002六图仍被用户拒绝。
- 输入上下文hash：`9b766772ce80c88d2bc9087b220c29b3729b12a7160f6d94137f7fca73d1e398`。本地完整日志位于忽略目录`.local/round3-final-quality/`；选定合同与检查代码保存在仓库。
- skill-creator `quick_validate.py skills/aikon`通过。没有其他harness或模型的实测，也没有新增CI系统矩阵。

## 作品实际检查

十张SVG及其真实预览已生成；主线程实际看过三组总览、十图棋盘格对照和官方身份图，生成Agent逐图看过1280及128/48/24、深浅展示底，并保存修改前后。

管理员8图已执行的冻结edge均无规则失败；无面具4图的8枚capsule通过。女版有旧文本hash与raw-byte差异，已在[文件绑定](../../outputs/round-003/file-bindings.json)中逐项说明，没有改原SVG或以文本hash冒充raw。

R1 B真实结果在[DeepSeek short报告](../../outputs/round-003/deepseek/numeric-b-r002/report.json)：主体命中率91.8729%，侧鳍80.8709%，蝴蝶结79.0932%；全主体MAE3.2746、RMSE14.9065。尚未达到B，且有既有edge10px失败。透明域单独检查未检出远离主体的非零alpha；未计背景颜色得分。

DeepSeek full后续由root补跑edge，首次发现4px内部alpha缺口和19px色边簇，已交回定位修订；最终修订与复验另见其目录记录。不能把“已生成十图”写成“十图已通过质量门禁”。

两次定点修订后，当前full审计别名采用r006，raw SHA `ff3197cd7d083ff4e8a697bf5e3437bf4af7600259ce3276ba638928c1dc950d`。内部alpha异常归零，最大局部簇19→10px仍fail；可见及隔离眼形均通过、覆盖完整。root实际查看r006完整图后选为改善后的draft；没有把更新别名称作验收，r004/r005仍在。[详细报告](../../outputs/round-003/deepseek/full-edge-repair-report.md)。

管理员逐材料审计见[paint-audit](../../outputs/round-003/paint-audit/)：只在真实绘制顺序/clip核出的可见材料域上测量，宽域和完整核支持分别报告。重色仪器引起的AA差异、薄面不足和旧模型警报保留，不据局部无超限推断全图无grain/mottle。

八图审计已经完成：原paint gate全保持fail；完整grain核覆盖55.84%–76.55%、mottle核覆盖13.62%–43.60%，这些有支持区域没有超冻结阈值。每图重色AA有1–12个像素差1LSB，真实不透明内区零差；其49×49邻域被保守排除并明示，未称alpha完全相同。主线程实际查看男无面具short的island叠图、女masked full的可见归属叠图，未凭肉眼将原失败全部判成误报。

## CI与状态

唯一CI环境继续为Ubuntu24.04 + CPython3.13.3。除detector正负控外，当前R1 short的B合同加入实际阻断步骤；候选不达标时该步骤必须失败。上传artifact配额可能独立失败，完整数字仍写入执行日志。CI最终运行状态须核对具体commit/run，不以旧绿色运行代替。

所有作品仍为draft，未获用户视觉接受；严格B和完整材质审查有剩余工作。临时Python缓存删除曾被自动审批拒绝（返回“blocked by policy”），该ignored缓存保留，未绕过。
