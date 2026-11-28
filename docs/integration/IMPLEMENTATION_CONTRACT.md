# Claude-Code-Workflow × Codex Implementation Contract

> Codex 侧已于 2026-11-27 退役（SHI-637）：`codex/workflow/` 和 `ccwf-*` skill 已从仓库删除，同步不再部署。下面的 Codex 条目只作历史记录；Claude 侧不变。

## 1. Trigger Contract

统一事件映射：`event -> skill -> required evidence -> writeback target`

| Event | Skill | Required Evidence | Writeback Target |
|---|---|---|---|
| `bug_or_ci_failure` | `systematic-debugging` / `ccwf-systematic-debugging` | `root_cause -> hypothesis -> verification` | `today.md` |
| `before_completion_claim` | `verification-before-completion` / `ccwf-verification-before-completion` | `command, exit_code, key_output, timestamp` | `active-tasks.json` |

## 2. Evidence Interface

任何完成声明前，必须记录以下结构化证据：

```json
{
  "command": "npm test",
  "exit_code": 0,
  "key_output": "34 passed, 0 failed",
  "timestamp": "2026-03-05T10:30:00-05:00"
}
```

## 3. Memory Writeback Interface

仅在相应持久化写回已获授权时使用以下接口；Codex 文件规划优先复用现有计划，不自动创建 memory 记录。

写回顺序固定为：
1. `today.md`（进行中）
2. `active-tasks.json`（跨会话任务）
3. `goals.md`（周/月/季度目标）
4. `projects.md`（项目摘要与指标）

## 4. Skill Security Audit Interface

第三方 skill/MCP 引入前必须执行扫描：

- Claude: `~/.claude/workflow/scripts/scan_skill_security.sh <path>`
- Codex: `~/.codex/workflow/scripts/scan_skill_security.sh <path>`

命中以下红旗必须阻断：
- URL/网络调用（含上传语义）
- 动态执行（`eval`/`exec`/`base64`）
- 破坏性命令（`rm -rf`/`shred`/`encrypt`）

## 5. Weekly Health Check Interface

- Claude: `~/.claude/workflow/scripts/workflow_health_check.sh --repo-root ~/.claude/workflow --mode claude`
- Codex: `~/.codex/workflow/scripts/workflow_health_check.sh --repo-root ~/.codex/workflow --mode codex`
