# MCE External gstack 与 Subagent Routing

## Objective

连续执行两个有序工作包，直到 external gstack runtime authority、AGENTS/ShipQ/DHF subagent routing、Identity、三目标 runtime promotion 与独立行为观察全部完成并留下 fresh receipts。

## Original Request

启用 Goal 模式执行已批准的 MCE External gstack authority + Subagent routing 计划，使用本地实时 GoalBuddy 看板，严格遵守最小写面、TDD、独立批准、备份、journal、rollback 和四条 evidence lane。

## Intake Summary

- Input shape: `existing_plan`
- Audience: 当前 MyCodexEnv / Codex runtime 的所有者与后续维护者
- Authority: `approved`，但每次 shared-runtime mutation 仍须先提交 fresh exact approval packet
- Proof type: `test`
- Completion proof: WP1/WP2 source gates 全绿；runtime parity/activity 均有 fresh receipts；external gstack 54/54；Identity A-D fresh；三 routing target 精确 promotion；用户新建任务完成 role/no-spawn/authority behavior observation；最终 Judge 记录 `full_outcome_complete: true`
- Likely misfire: 只完成计划或 source diff；把 disk parity 当成 loaded behavior；用 broad sync、setup 或手工命令绕过单一事务脚本；为追求角色使用率而自动 spawn；顺手修复范围外问题
- Blind spots considered: external gstack root 与 runtime layout 会漂移；shared runtime 需要 quiescence 与排他锁；macOS 目录切换存在短 gap；GoalBuddy 专用 agent 目前只有 bundled templates；最终计划在 committee 第 9 轮后按盲审 finding 修正但未再次评分
- Existing plan facts:
  - "WP1 必须先完成并冻结 baseline，WP2 才能开始。"
  - "WP1 的10个功能/文档文件会使 Identity C stale；三份已在总体范围内的 Identity 文件是 WP1/WP2 共享管理面，因此 WP1有效增量13文件、WP2仍对同三文件再刷新，累计唯一文件保持16个。"
  - "WP1 新增单一 scripts/external_gstack_runtime.py authority，status/apply/recover、共享 .phase0-sync.lock、journal/fsync/crash recovery 均走同一入口。"
  - "External gstack root /Users/kezheng/.gstack/repos/gstack 严格只读；禁止 setup、pull、reset、vendor sync 和网络安装。"
  - "WP2 只修改 AGENTS、ShipQ/DHF skills、test_runner 与三份 Identity 文件。"
  - "不 commit、不 push、不创建 issue/task/thread，不自动扩大用户授权。"

## Goal Kind

`existing_plan`

## Current Tranche

先由 Judge 对最终计划、当前 repo/runtime evidence、共享锁、精确文档范围和两包 allowlist 做执行前校验；随后连续完成 WP1 source、WP1 runtime、WP2 source、WP2 runtime、behavior observation 和最终审计。安全 Worker slice 可执行时不得停在“ready for implementation”。

## Non-Negotiable Constraints

- 只做目标明确要求的修改；范围外问题只在 receipt/final 中列出。
- 同时最多一个 write-capable Worker；所有 Worker 写面必须精确且互不重叠。
- Read-only/Report-only agent 永不写入；shared runtime mutation 只由 PM 在 fresh approval 后执行。
- 复用 `${CODEX_HOME}/.phase0-sync.lock`；ordinary sync、apply、recover 使用同一排他锁。
- 不运行 official gstack setup，不修改 external root 内容。
- 不使用 broad glob、broad sync、`--delete`、reset、checkout 回退或手工继续半完成 transaction。
- 每个完成/失败/rollback claim 都包含 `command`、`exit_code`、`key_output`、`timestamp`。
- Source、runtime parity、runtime activity、behavior observation 必须分开报告。
- Backup 和 journal 永久保留；未知或 nonempty staging 内容不删除。
- `docs/goals/mce-external-gstack-subagent-routing/` 是用户另行授权的 PM control surface，不计入 WP1/WP2 implementation allowlist；实现 gate 必须分别报告 control-file diff 与 product/runtime diff。

## Stop Rule

Stop only when a final audit proves the full original outcome is complete.

Do not stop after planning, discovery, Judge selection, WP1, source-only completion, or disk parity when safe required work remains.

If a runtime approval or user-created behavior task is missing, block that exact task with a receipt and continue every safe local task that remains.

## Canonical Board

Machine truth lives at:

`docs/goals/mce-external-gstack-subagent-routing/state.yaml`

If this charter and `state.yaml` disagree, `state.yaml` wins for status, active task, receipts, verification freshness, and completion truth.

## Run Command

```text
/goal Follow docs/goals/mce-external-gstack-subagent-routing/goal.md.
```

## PM Loop

1. Read this charter and `state.yaml`.
2. Work only on the active task.
3. Preserve the two-package order and exact allowlists.
4. Record a compact receipt before advancing the board.
5. Activate a safe Worker selected by Judge without asking to continue.
6. Keep runtime approvals and behavior observation as separate PM/Judge tasks.
7. Complete only after T999 maps all current receipts to the original outcome and records `full_outcome_complete: true`.
