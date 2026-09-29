# 女管理员 round-003：四张待审计 SVG

当前候选为 **无面具 short r004，其余三张 r005**，依据为 `official illustration`。用户原生 `female_mask` 的真实回答为“两种都画”；本目录没有把分支选择解释为视觉接受。新绘图没有读取或复制旧管理员 SVG。

| 分支 | 精简版 | 完整版 |
| --- | --- | --- |
| 无面具 | [SVG](unmasked/short.svg) / [预览](unmasked/short-preview.png) | [SVG](unmasked/full.svg) / [预览](unmasked/full-preview.png) |
| 正常佩戴 | [SVG](masked/short.svg) / [预览](masked/short-preview.png) | [SVG](masked/full.svg) / [预览](masked/full-preview.png) |

[四图及原生小尺寸总览](overview.png)；[四种底色检查](background-review.png)；[机器检查](checks.json)；[r005边缘修复与同位置对照](repair-r005-review.md)。当前状态是 `visually_reviewed_edge_checked`；四张 edge 检查已通过现有规则，完整 paint 域评估及用户验收仍未完成。

## 实际依据与内容

已实际查看：女性官网立绘、官方 B 卡、0212 左下女性、0305 右侧女性、独立抑制器展示，以及 r1-working/r2。来源哈希与观察范围在 [reference-evidence.json](reference-evidence.json)。本轮没有取得当前 3D 近景；青蓝眼部只映射成暗青灰 capsule，不能称为官方精确色值。

short 和 full 使用独立头发、脸域、下颌和取景路径。short 是左下裁切头部；full 露出依据 B 卡/官网立绘建立的暗内层、浅高领、橙色前件、叠接长环扣、深外领浅内面和黄色肩片。full 没有把 short 整体缩放后添加通用领子。两者均保留女性多片异长金属发卡；masked 为覆盖双眼、向鼻梁下探的真实遮挡分支，省略被遮眼形。

## 已执行的修改循环

- r001：四份实际完整 prompt 先保存，然后原创代码绘制并渲染。看图发现过厚的额头阴影带、上发光泽过弱、发卡偏平白和 full 环扣层级不足。
- r002：去掉错误横带，给宽发束连续低频色场，改发卡、增加第二长环；保留 r001 的实际 SVG、源码、prompt 和预览。
- r003：只改两张 full。消除右鬓因不同材料场产生的三角状亮面，为领扣声明自己局部坐标的金属场；short 未重画。保留全部旧版。
- r004：按主 Agent 实看反馈，让顶冠与左上扫额束共享同一个连续场，消除闭合亮片边界；收细横扣、缩短外伸并为发卡声明局部金属场，降低十字格栅观感。头脸、眼、面罩与服装路径未随此步骤重画。
- r005：针对三张的已知 edge 失败，给右领翼和面罩现有轮廓应用 shared clip 与内部不透明同材质支撑。首次有界实现将最大局部簇从6/11/17降到1/2/2；保留所有原路径与坐标链，整幅1280 alpha逐像素不变。无面具short继续r004。

每个真实 revision 在 `<branch>/<profile>/revisions/<revision>/` 保存实际源 SVG、完整实际 prompt、当时源码、1280/128/48/24 PNG 与生成记录。root 别名指向上述当前revision的同字节副本；历史机器证据在 `quality/` 和 `quality-r004/`，当前证据在 `quality-r005/`。

## 实际检查与未通过项

主绘图 Agent 实际查看了 r004 四张 1280 图、总览里的原生 128/48/24 图、四种底色图。观察到：两 profile 可明确区分，面罩在眼鼻位置，发卡和领口部件可辨；r004 已去掉前述额头横带、左上闭合亮面和右鬓三角亮面。24 px 时发卡的小叠接与金属环层数仍难分辨，不能声称细节在此尺寸完整保留。

- 静态 SVG 子集检查四张通过：没有 bitmap、外部图、滤镜或随机纹理。全部预览重渲染 RGBA 与缓存逐像素相等。
- 两张无面具图的实际路径隔离渲染后，左右眼均通过现有 capsule 规则；眼形是直侧壁和圆端帽，非 ellipse。实际完整图亦看过，双眼无遮挡。此项不评价仰头是否达到用户期望。
- 历史r004中，unmasked full / masked short / masked full 分别因局部簇 **6 / 11 / 17 px** 失败。r005局部结构修复后降为 **1 / 2 / 2 px**，四张当前候选均为 `no_rule_failure`，冻结上限保持3px。
- 已实际看过修复前后同位置 native/4×BOX 放大：full右领翼/肩片/头发接合及面罩下鼻尖。原多面重合边的材料采样残差减少，面罩真实金属折线和领翼外形保留。这不是纹理模型生成改良或人类审美验收。
- 未给新几何构建经人工核实的完整可见材质域，故未复用旧管理员/DeepSeek 的 paint mask 给新图背书。grain/mottle 自动域评估保持未完成；代码没有噪声构造不等于所有上色判断都已通过。
- 本轮对仰头使用投影关系和独立脸域设计，未推导唯一三维角度、未证明与 r1 的主观仰头效果等同。隐藏发卡结构、当前 3D 细节和用户最终审计仍未确认。

没有 `99%`、跨模型成功或用户接受声明。edge通过不代表完整grain/mottle材质域、主体相似和仰头效果均已通过。

## 当前 SVG SHA-256

本节及历史检查中 `svg_sha256` 是 universal-newline 读取后UTF-8文本的hash。源SVG末尾的一个CRLF使其与raw-byte文件hash不同，完整两种绑定见 [file-hash-binding.json](file-hash-binding.json)。源文件与各revision仍保持原字节，不用文本hash冒充文件hash。

| 文件 | SHA-256 |
| --- | --- |
| unmasked/short.svg | `969d0cc7551c1ff55e980fd2690a3dc6b1ca05e7a7d63be0506880a97a735e85` |
| unmasked/full.svg | `65677d780446e2e9d6a99173d0862b5271d4fdb00e58d5b85f73160462607e34` |
| masked/short.svg | `4c6790e08126f6335ea3ba22e3e3d9512e1efd7782d11dfc1f2f949de2bcc5ba` |
| masked/full.svg | `2460f7ac589b7a31fd2d24c89ec99faf666a63de7803b159d03869244173cb7b` |

resvg-py 0.5.0 / resvg 0.48.1。所有绘图和检查均为硬超时不超过 48 秒的一次性本地命令；结束时无 Python/resvg 临时进程遗留。未改变 CI、共享文档、Git 分支或提交。
