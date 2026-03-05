# Codex 规则映射（上游 -> 本地）

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
| `rules/behaviors.md` | `~/.codex/workflow/rules/behaviors.md` | 采用 | 统一行为与路由原则 |
| `rules/skill-triggers.md` | `~/.codex/workflow/rules/skill-triggers.md` | 采用+扩展 | 连接本地安全扫描脚本 |
| `rules/memory-flush.md` | `~/.codex/workflow/rules/memory-flush.md` | 采用 | 强制会话热数据写回 |

## 技能映射（命名空间化避免冲突）

| 上游技能 | Codex 技能目录 | 触发事件 | 必要证据 |
|---|---|---|---|
| `planning-with-files` | `~/.codex/skills/ccwf-planning-with-files` | 复杂任务 | 计划文件 + 阶段验收 |
| `systematic-debugging` | `~/.codex/skills/ccwf-systematic-debugging` | Bug/CI 失败 | 根因证据链 |
| `verification-before-completion` | `~/.codex/skills/ccwf-verification-before-completion` | 完成声明前 | fresh verification output |
| `session-end` | `~/.codex/skills/ccwf-session-end` | 退出信号 | 4 类写回同步 |
| `experience-evolution` | `~/.codex/skills/ccwf-experience-evolution` | 复盘触发 | 跨任务可复用经验 |

## 写回接口
- `~/.codex/workflow/memory/today.md`
- `~/.codex/workflow/memory/projects.md`
- `~/.codex/workflow/memory/goals.md`
- `~/.codex/workflow/memory/active-tasks.json`
