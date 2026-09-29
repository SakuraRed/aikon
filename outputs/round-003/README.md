# 第三轮：十张透明 SVG 审计候选

[打开本地审阅页](index.html)，可切换浅底、深底、棋盘格、大小和profile。展示底只属于预览，十张源SVG均为透明输出。

| 主体与分支 | 精简版 | 完整版 | 记录 |
|---|---|---|---|
| DeepSeek / R1 | [SVG](deepseek/short.svg) | [SVG](deepseek/full.svg) | [来源及修订](deepseek/README.md) |
| 女管理员 / 无面具 | [SVG](endministrator-female/unmasked/short.svg) | [SVG](endministrator-female/unmasked/full.svg) | [四图审查](endministrator-female/README.md) |
| 女管理员 / 正常戴面具 | [SVG](endministrator-female/masked/short.svg) | [SVG](endministrator-female/masked/full.svg) | 同上 |
| 男管理员 / 无面具 | [SVG](endministrator-male/unmasked/short.svg) | [SVG](endministrator-male/unmasked/full.svg) | [四图审查](endministrator-male/README.md) |
| 男管理员 / 正常戴面具 | [SVG](endministrator-male/masked/short.svg) | [SVG](endministrator-male/masked/full.svg) | 同上 |

## 真实选择与实际变化

男女各自实际选择“两种都画”，每个分支都有short/full。女性保留异长多片金属发卡及bob，男性使用偏扫短发和侧后短束；masked正常遮住双眼及鼻梁，不绘制替代眼或把装置上移。无面具眼形依据已核官方插画映射为暗青灰capsule，不把创作色称官方精确sRGB。

DeepSeek full按用户选定的A女仆图提取白胸褶、深蓝领结及肩带，r1头部身份保留；不可见下颌、颈部投影及后发延续是明确的创作适配。该衣装参考不是已确认的r1官方服装。full新增实际头颈/服饰范围，不能将其与r1纯头像作整图同像评分。

根目录别名供当前审阅；真正生成过的每个版本prompt、源码、SVG和渲染均在各主体revision目录保留，未追认覆盖旧稿。主线程实际查看DeepSeek双版、男女四图及官方来源，生成Agent分别查看1280及128/48/24和深浅底。此记录不构成用户接受。

## 已知结果

- 管理员8图当前冻结edge检查均无规则失败，无面具4图的实际左右capsule均通过；分面重合边通过shared clip和不透明内部支撑修复，未放宽阈值。
- DeepSeek short仍来自第三轮独立稿监督修订，不是新盲测。严格B结果见[numeric-b-r002/report.json](deepseek/numeric-b-r002/report.json)：主体命中率91.8729%，侧鳍80.8709%，蝴蝶结79.0932%，都未达到99%；整体MAE3.2746、RMSE14.9065和边界距离也有失败。
- B只评分主体及固定局部，背景RGB完全不计分；该稿远离主体的透明域未检出非零alpha。其旧边缘10px报警未因改标题或新数值合同而消失。
- DeepSeek full当前r006修复内部alpha异常4→0px，最大局部色边簇19→10px仍超3px门槛；可见双眼capsule通过。它是改进的审计稿，不是通过全部门禁的成品；r004/r005均保留。
- per-material grain/mottle/island审计单独记录，域不足或报警不等于pass。机器检查、自然光泽、身份/姿态、完整技能可重复性和用户审计不得互相替代。
- [八图逐材料审计](paint-audit/README.md)现已完成：八张原paint gate仍为fail；完整支持域内grain/mottle未超线，覆盖分别55.84%–76.55%和13.62%–43.60%，薄面与原island/mottle报警继续未解决，不宣称整图干净。
- 新数值门禁已经加入唯一Ubuntu CI；当前候选未达标时应真实失败，不能拿detector正负控通过冒称作品通过。

状态：**draft / 用户未验收 / R1严格B未达标**。

文件归档使用[十图raw-byte绑定](file-bindings.json)。女性历史检测报告的 `svg_sha256` 实为读取文本后规范化LF的哈希，源文件末尾含一个CRLF；[独立对应关系](endministrator-female/file-hash-binding.json)分别列真实文件hash与文本hash。原文件与revision字节相同，未为对齐hash重写历史，不能把两种hash混用。
