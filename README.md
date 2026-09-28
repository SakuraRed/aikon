# Aikon

通过可移植的 Agent Skill，把风格参考与角色、IP 或实体信息转成可精确修改、可追溯的 Grok bot 风格 SVG 图标。

## 当前状态

2026-09-28：首轮14份SVG已被用户明确全部拒绝，当前原型不合格，不应当作可用基线或稳定技能。正在针对一个主体进行像素对照、身份特征和提示词效果校准；跨模型视觉一致性未验证。

目标使用环境包括 Codex、Claude Code、Zcode、OpenCode 等支持技能或指令资源的 agent harness。核心说明不依赖某个模型、绘图 API、绝对安装路径或特定提问工具名称。

每次新增参考的绘图请求生成精简版与完整版，默认透明背景、无水印；输入可为概念、名称、图片、wiki/URL或宿主能够读取的其他模态。先研究与确认主体，再用代码SVG创作并精调。

## 技能入口与本地使用

[skills/aikon/SKILL.md](skills/aikon/SKILL.md) 是标准入口。将整个 `skills/aikon` 目录复制到目标 harness 支持的技能目录，保持相对资源完整；也可先让 Agent 读取该入口试用。加载位置与问答能力差异见[兼容性研究](docs/research/portability-svg.md)，文档支持不等于本仓库已经实测。

可选辅助工具仅需 Python 3.9+ 标准库：

```text
python skills/aikon/scripts/aikon.py render --scene design.json --output icon.svg
python skills/aikon/scripts/aikon.py check --svg icon.svg
python skills/aikon/scripts/aikon.py snapshot --scene design.json --root <已选择的profile目录> --revision r001 --note "initial draft"
```

精确格式见[scene合同](skills/aikon/references/scene-format.md)。没有Python也可直接写SVG，必须如实标明哪些检查未执行。

中文源提示词译文保留 CC BY-NC 4.0 派生许可；[来源说明](skills/aikon/THIRD_PARTY_NOTICES.md)是包的一部分，不能把整包宣称为无限制商用许可。私有研究原图与测试立绘不混入技能分发目录。

## 文档导航

- [产品目标与已知边界](docs/PRD.md)
- [结构与验证边界](docs/ARCHITECTURE.md)
- [决策记录](docs/DECISIONS.md)
- [领域术语](CONTEXT.md)
- [研究与决策地图](docs/wayfinding.md)
- [技能行为验收草案](docs/specs/skill-contract.md)
- [参考图索引](ref/README.md)
- [真实输入集双版本预览](outputs/fixtures/index.html)
- [真实测试合同](docs/validation/fixture-contract.md)

代码优先生成真实矢量 SVG；模型可以辅助理解、构图和视觉评审。兼容性和质量声明必须附实际验证范围。
