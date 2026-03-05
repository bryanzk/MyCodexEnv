<!-- ccwf:integration:start -->
## Claude-Code-Workflow Integration (Managed by MyCodexEnv)

### P0 门禁（Verification Gate）
- 任何完成声明前必须提供验证证据：
  - `command`
  - `exit_code`
  - `key_output`
  - `timestamp`
- 无证据不得宣称“已完成/已修复/已通过”。
- 项目类型检查清单：`~/.claude/workflow/docs/verification-checklist.md`

### 自动加载规则
- `Read ~/.claude/workflow/rules/behaviors.md`
- `Read ~/.claude/workflow/rules/skill-triggers.md`
- `Read ~/.claude/workflow/rules/memory-flush.md`

### 四条主回路
- 计划回路：`~/.claude/workflow/skills/planning-with-files/SKILL.md`
- 调试回路：`~/.claude/workflow/skills/systematic-debugging/SKILL.md`
- 交付回路：`~/.claude/workflow/skills/verification-before-completion/SKILL.md`
- 记忆回路：`~/.claude/workflow/skills/session-end/SKILL.md`

### Skill 安全扫描（引入第三方 skill/MCP 前）
- `~/.claude/workflow/scripts/scan_skill_security.sh <path>`

### 每周健康检查（建议周日）
- `~/.claude/workflow/scripts/workflow_health_check.sh --repo-root ~/.claude/workflow --mode claude`
<!-- ccwf:integration:end -->
