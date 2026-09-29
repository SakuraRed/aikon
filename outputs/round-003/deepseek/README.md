# DeepSeek round-003

当前候选pair为 `short.svg` 与 `full.svg`。用户先选择固定full服饰参考，随后真实选择 **A蓝白女仆衣装**，本目录据此完成full。`layout/`仍保留当时的未定版构图研究，不能把它当正式full。

short从本Agent的独立校准r004监督修订派生，不是新盲测。r001试验删除了原subject clip，实测多露出22,661个像素，改变参考投影，因此未采用。r002恢复原裁切，1280 RGBA与独立r004完全相同；该clip只裁主体边界，不绘制炭黑背景。输出无背景填充，右上alpha为0。原r1-working、r2与full-imagegen构图均实际查看；纹理未继承。

- 正式候选：`short.svg`、`short-1280.png`、`short-128.png`、`short-48.png`、`short-24.png`。
- 深浅底与尺寸总览：`short-inspection-board.png`。
- 真实prompt/source/SVG与PNG：`revisions/r001/`、`revisions/r002/`；根目录脚本分别是`draw.py`和`short-finalize.py`。
- 自检记录：`short-validation.json`；去clip差异：`unclip-diagnosis.json`。
- full当前审计稿：`full.svg`、`full-1280.png`、`full-128.png`、`full-48.png`、`full-24.png`，当前full revision为r006，未通过全部门禁、未获用户验收。
- pair大图：`pair-overview.png`；128/48/24深浅底对照：`pair-small-sizes.png`；full单独深浅底：`full-inspection-board.png`。
- full服饰研究：[候选证据](../../../docs/research/entities/deepseek-outfit-candidates.md)；用户后续已选A。研究文档保存研究时未选状态，不由本绘制任务改写。

已完成静态原语验证与四尺寸真实渲染，实际查看1280和128/48/24深浅底。没有运行全套重型检查。既有r004边缘门禁的10像素局部失败未被此次标题/描述变更修复，不能声明门禁全通过。身份保留包括弯钩顶发、蓝发、白头褶、侧鲸鳍浅缘及蓝结，一体暗色眼缘保留；无嘴鼻、背景、水印、位图、filter或noise。

没有用户美术接受、99%达成或新数值合同通过声明。short的严格B99%合同由主线程独立推进，本full工作未改动short。所有自有生成进程均为45秒硬超时一次性命令，正常退出；未终止盘点中已有Chrome/Node/Adobe进程。

## Full实际结构与来源

头部基于独立r004，保持r1的弯钩宽呆毛、白头褶、蓝侧結、鲸鳍浅缘、前景发束、完整暗色胶囊眼与原投影。full在同一1280画布中有完整下颌连接、短颈、倾斜衣领、白褶胸片、深蓝领結和双肩带；与short的区别不只是颜色和路径数量。

衣装只取用户选定A图的可见颈领/上胸关系。没有移植A的圆虹膜、嘴、手臂、全裙、鲸鱼图案或独立尾巴，也没有将衣装称作官方r1设定。原r1裁切之外的下颌、颈部姿态、后发延续及把正视衣装适配到r1倾斜投影，均为明确创作适配；不能冒称原图直接观察。

`full-revisions/`保存每轮真实prompt、执行源码、SVG、1280/128/48/24渲染和验证记录：r001为首稿；r002根据实际查看拉开颈领并调整后发；r003去掉旧头像后层的水平裁切尾部；r004补齐侧鳍根部下的不透明后发父层，消除修补引出的透明缺口。最终首要身份路径d与独立r004一致，记录见`full-validation.json`。每轮均实际查看，而非只读取分数。

full的上胸与领結在128/48px可辨，24px只能保留领口的整体深浅关系。后发延续和下颌没有同姿态gold参考，造型仍待用户审计；本任务只运行通用静态原语验证及轻量真实渲染，没有运行全套重型质量门禁。预览衬底仅在PNG检查板中，SVG内没有背景填充、位图、filter或noise。

## Full边缘复修状态

后续冻结edge实测发现r004内部alpha异常4px、局部色差簇19px。新增r005/r006各进行一次有界修复与同门禁复查：r005为3px/7px，r006为0px/10px；两者仍因局部色差超过3px失败。主线程实际查看r006后，选择将其作为当前draft别名，保留“alpha修复、局部色差仍失败”状态；这不是机器合格或用户验收。r004/r005/r006均保留，四尺寸与pair总览已同步到r006。两版新候选的隔离与实际可见眼形均无规则失败，所有尺寸和深浅底已查看。完整未解决位置、根因分析与原始SHA见[复修报告](full-edge-repair-report.md)。
