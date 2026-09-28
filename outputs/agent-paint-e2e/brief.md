# 独立 Skill 消费者试用

执行日期：2026-09-29。任务来源为主线程对本轮用户反馈的有界委派：读取当前 Skill，独立计划并执行固定几何的 short/full 上色，随后实际渲染、像素检查、视觉检查。只写本目录，不改技能、工具、CI 或 Git。

本轮主体是用户认可整体方向的 illustration，不是 DeepSeek；DeepSeek 明确绑定 `ref/user-mode/r1.png` 的主体与风格，这一结论已确定。本轮查看 r1 以理解干净主面与宽缓色调，不移植它的蓝发、白褶边或蝴蝶结到 illustration。

实际查看：本轮完整反馈图、圈注缺陷图、r1；此前研究中也实际查看了官网四个指定示例。完整图片承担整体正向、局部上色反例的双重角色，红圈图是人类注释，不是生成指令。

基础 SVG：`outputs/calibration/illustration/vector-study/semantic-study-v4.svg`。保持所有选中几何的 path、形状、位置、transform；删除旧 paint layers 不等于改变 geometry 数据。选中几何与源图的差距仍须如实列出，不能用一次 paint 试用证明从原图创作的能力。

约束：不调用 imagegen、不上传图片、不读取 `tests/fixtures` 的 paint plan。先保存本轮 prompt，再制定 plan 和编译；工具 stdout 与实际命令另存日志。最多新建一次修正版本，不覆盖任何已生成 SVG。

进程预检：未发现已有 Python/resvg 测试进程；存在 Adobe Node、Codex node_repl、其他仓库 Node 与用户 Chrome，均非本任务所有，不终止。工作进程采用一次性 bounded runner，内部 subprocess 单步 45 秒、总体 watchdog 180 秒；数值线程上限为 1。开发服务和浏览器不启动。
