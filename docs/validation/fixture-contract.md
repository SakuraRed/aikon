# 真实输入测试合同

创建：2026-09-28；主体纠正：2026-09-29。此文记录当前测试输入、实际用户选择和验收要求；不表示已经完成各项。首批全部被拒绝，当前仅推进单例校准。

输入来自用户指定的 `D:\Downloads\aikon ref`。原始目录只读，不传给外部识图服务。两张 `模式参考` 已实际查看，作为强模式参考；其中的水印和黑底明确不进入产物。输入哈希清单保存在本地研究证据目录。

| Round | 入口 | 用户确认的主体 | 目标 |
| --- | --- | --- | --- |
| deepseek | 概念1.txt + r1.png | 用户指定 r1 形象：蓝发、白色褶边、侧蝴蝶结 | short + full（旧鲸鱼作废） |
| sunna | Sunna.txt | 绝区零千夏，核对官方公示外观 | short + full |
| endministrator-female | endfield.txt | 女管理员 | short + full |
| endministrator-male | endfield.txt | 男管理员 | short + full |
| aria-human | url_1t.txt | Aria人形投影 | short + full |
| aria-robot | url_1t.txt | Aria机器人本体 | short + full |
| illustration | img_1.png | 图中唯一女孩，姓名保持未知 | short + full |

实际原生回答：管理员男女都测、Aria两种都测、存 `outputs/fixtures`。2026-09-29 用户明确将 DeepSeek 绑定 r1，覆盖此前蓝鲸路线；旧版产物保留为失败历史，不静默改成新版本。存放路径不是Agent代选。先前“2–3候选”被每round必须两种profile覆盖，额外候选只能在profile内部产生。

## 验收

- 每round同一已确认主体，精简/完整各有中文生产提示词、scene或源码、真实SVG、版本来源。
- profile差异与源提示词对应；透明/无水印/交互/双版本是显式运行覆盖。
- 未查看的URL或图片不标已查看；受阻记录事实，替代来源与原输入分清。
- 真实透明像素或可见底色透出；无黑底残块、水印、文字、位图包装、外链及脚本。
- 更强近景、双胶囊眼完整、主体特征由本轮证据而来；深浅底和24/48/128px实际查看。
- 结构检查、视觉审查、用户验收、跨模型测试分别记录。当前仍未运行其他harness/模型。
