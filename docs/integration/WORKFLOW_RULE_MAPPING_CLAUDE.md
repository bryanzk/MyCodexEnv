# Claude 规则映射（上游 -> 本地）

## 基线
- 上游仓库：`runesleo/claude-code-workflow`
- 锁定提交：`7bcf8d2b60b7c8cd6f06803d87441bf0c2c9f5ed`
- 本地镜像：`vendor/claude-code-workflow/`

## 冲突优先级
1. 本地 ALWAYS 安全/验证规则
2. 上游 workflow 规则
3. 效率优化规则

## 规则映射

| 上游文件 | 本地落点 | 状态 | 说明 |
|---|---|---|---|
| `rules/behaviors.md` | `~/.claude/workflow/rules/behaviors.md` | 采用 | 作为 Claude 侧默认行为规范 |
| `rules/skill-triggers.md` | `~/.claude/workflow/rules/skill-triggers.md` | 采用+扩展 | 增加 third-party skill 安全扫描命令 |
| `rules/memory-flush.md` | `~/.claude/workflow/rules/memory-flush.md` | 采用 | 会话收尾自动写回 |
| `docs/task-routing.md` | `~/.claude/workflow/docs/task-routing.md` | 采用 | 任务分级路由与成本策略 |
| `docs/agents.md` | `~/.claude/workflow/docs/agents.md` | 采用 | 多模型协作契约 |
| `docs/content-safety.md` | `~/.claude/workflow/docs/content-safety.md` | 采用 | 外部内容来源标注与污染隔离 |

## 技能映射

| 上游技能 | 本地落点 | 触发事件 | 必要证据 |
|---|---|---|---|
| `planning-with-files` | `~/.claude/workflow/skills/planning-with-files` | 复杂任务/跨模块改动 | `task_plan.md` + 验收标准 |
| `systematic-debugging` | `~/.claude/workflow/skills/systematic-debugging` | 构建/测试/运行失败 | 根因链路（根因-假设-验证） |
| `verification-before-completion` | `~/.claude/workflow/skills/verification-before-completion` | 完成声明前 | `command/exit_code/key_output/timestamp` |
| `session-end` | `~/.claude/workflow/skills/session-end` | 退出信号 | today/projects/goals/active-tasks 写回记录 |
| `experience-evolution` | `~/.claude/workflow/skills/experience-evolution` | 卡顿/复盘 | 可复用经验摘要 |

## 弃用/替代说明
- 无弃用；保持上游五个核心技能完整引入。
