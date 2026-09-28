# Aikon

通过可移植的 Agent Skill，把风格参考与角色、IP 或实体信息转成可精确修改、可追溯的 Grok bot 风格 SVG 图标。

## 当前状态

2026-09-28：私有仓库初始化与前置研究阶段。尚未发布技能，尚未验证跨模型视觉一致性。当前没有安装或运行步骤。

目标使用环境包括 Codex、Claude Code、Zcode、OpenCode 等支持技能或指令资源的 agent harness。核心说明不依赖某个模型、绘图 API、绝对安装路径或特定提问工具名称。

## 文档导航

- [产品目标与已知边界](docs/PRD.md)
- [结构与验证边界](docs/ARCHITECTURE.md)
- [决策记录](docs/DECISIONS.md)
- [领域术语](CONTEXT.md)
- [研究与决策地图](docs/wayfinding.md)
- [技能行为验收草案](docs/specs/skill-contract.md)
- [参考图索引](ref/README.md)

代码优先生成真实矢量 SVG；模型可以辅助理解、构图和视觉评审。兼容性和质量声明必须附实际验证范围。
