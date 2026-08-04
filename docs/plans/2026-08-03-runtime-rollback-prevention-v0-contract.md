# Runtime Rollback Prevention v0 Requirements

## Goal
交付一份不实施 live 操作的 v0 执行计划：仅防止过时源覆盖新 runtime，并把未来实现限制为五个顺序 commit。

## Audience
- MyCodexEnv 操作员
- 未来执行 V1–V5 的实现 agent

## Scope
- `docs/plans/2026-08-03-runtime-rollback-prevention-v0-plan.md`
- 未来 V1–V5 对 `scripts/sync_codex_home.sh`、daily refresh 脚本、`docs/HARNESS_RUNTIME.md` 与 `test_runner.py` 的明确变更。
- Manifest schema v2、冻结 15-path allowlist、source transition matrix、backup retention 与 report-only automation。

## Non-Goals
- 本任务不实施 runtime sync、live recovery、automation 变更、push 或任何 `~/.codex` 写入。
- 不防御恶意本地 agent、凭证被盗或供应链攻击。
- 不引入签名、密钥、root 权限、第二控制系统或新增二进制依赖。

## Constraints
- 当前文档任务只写两个 v0 文件，并只在 archive 计划开头增加状态注记。
- 保留所有现有 tracked dirty 与 untracked DHF 文件，不覆盖、不回退、不暂存。
- 未来实现仅使用 Python 标准库、git、rsync 与 launchd；测试必须在 Linux CI 可运行。
- 不修改 `codex/AGENTS.md`、`README.md` 或 golden fixture。
- v0 计划不超过 150 行，gate 不超过 12 个。

## Task Demand (D_task)
- estimated_level: high
- L (reasoning/action steps): 三个文档交付、五个顺序工作项、保留件逐字校验与多项结构门禁。
- H_tool (tool-selection ambiguity): 使用现有 Markdown、requirements validator、Python 标准库与 diff；无外部工具选择。
- S_state (cross-module state tracking): 必须保持 archive、v0 plan、requirements contract、15-path 表和 dirty ownership 一致。
- N_obs (observation/external noise): 仅本地确定性文档验证；不观察或修改 live runtime、scheduler、remote。

## Source Of Truth
- `AGENTS.md`
- `docs/plans/2026-08-03-gstack-dhf-runtime-rollback-prevention-plan.md` 的 transition matrix、manifest、15-path 表、report-only 流程与 remote 不倒退原则
- `docs/plans/2026-08-03-runtime-rollback-prevention-v0-plan.md`
- 本 requirements contract

## Acceptance Criteria
- [ ] 原计划仅在开头增加 design-archive 状态注记，其余 bytes 不变。
- [ ] v0 计划严格使用 A–G 固定结构，且不超过 150 行。
- [ ] v0 计划只有操作员和 automation 两个身份。
- [ ] transition matrix、manifest schema v2、15-path 表、report-only 两行流程和 remote 不倒退原则均被保留。
- [ ] 15-path 表与 archive 原计划逐字节一致，golden digest 不变。
- [ ] V1–V5 各对应一个 commit，并覆盖所有指定行为与 Linux CI 测试。
- [ ] gate 总数不超过 12，且每项有一行可执行命令。
- [ ] 本文件通过 `harness_requirements.py validate`。
- [ ] 本任务没有 runtime、sync、push、stage、commit 或 remote mutation。

## open_questions_resolved
- question: v0 防御哪类对手？
  answer: 仅防御过时的源覆盖新的 runtime；恶意行为是明确 residual risk。
- question: v0 如何批准恢复或降级？
  answer: 仅由操作员在场执行，并保存 harness checkpoint 四字段记录。
- question: 复杂密码学设计如何处置？
  answer: 原计划保留为 design-archive，只在未来威胁模型升级时重新评估。

## Verification Gate
- `python3 scripts/harness_requirements.py validate docs/plans/2026-08-03-runtime-rollback-prevention-v0-contract.md`
- `python3` structural checks for line count, gate count, forbidden mechanisms, fixed headings and work-item order
- `python3` byte comparison for the 15-path table extracted from archive and v0 plan
- `git diff --check` over the three authorized paths

## Risks
- `mv` 与尽力而为的 `fsync` 存在 crash window。
- 恶意 agent 不在 v0 威胁模型内。
- backup 与 live runtime 存在单文件系统容量竞争。

## Handoff Notes
- 当前阶段只交付文档；下一安全任务是另立 implementation 会话，按 `V1 -> V5` 顺序先写失败测试，再做最小实现。
- 任一 live/runtime/push 操作都需要后续明确授权和 fresh 四字段 receipt。
