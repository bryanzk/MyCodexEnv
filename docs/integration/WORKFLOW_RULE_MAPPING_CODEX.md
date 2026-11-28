# Codex 规则映射（上游 -> 本地）

> 已退役（2026-11-27，SHI-637）：`codex/workflow/` 和 `ccwf-*` skill 已从仓库删除，同步不再部署。本文件只作历史记录。

## 基线
- 上游仓库：`runesleo/claude-code-workflow`
- 锁定提交：`7bcf8d2b60b7c8cd6f06803d87441bf0c2c9f5ed`
- 本地镜像：`vendor/claude-code-workflow/`

## 冲突优先级
1. 本地 ALWAYS 安全/验证规则
2. `codex/AGENTS.md` 强制门禁
3. `~/.codex/workflow/*` 细节规则

## 规则映射

| 上游文件 | Codex 落点 | 状态 | 说明 |
|---|---|---|---|
| `rules/behaviors.md` | `~/.codex/workflow/rules/behaviors.md` | 采用 | 来源标注、幻觉隔离、攻击面审查与原子提交 |
| `rules/skill-triggers.md` | `~/.codex/workflow/rules/skill-triggers.md` | 采用+扩展 | 连接本地安全扫描脚本 |

## 技能映射（命名空间化避免冲突）

| 上游技能 | Codex 技能目录 | 触发事件 | 必要证据 |
|---|---|---|---|
| `systematic-debugging` | `~/.codex/skills/ccwf-systematic-debugging` | 原因不明的错误 | 根因证据链 |
| `verification-before-completion` | `~/.codex/skills/ccwf-verification-before-completion` | 完成声明前 | fresh verification output |
| `experience-evolution` | `~/.codex/skills/ccwf-experience-evolution` | 按需调用 | 跨任务可复用经验 |
