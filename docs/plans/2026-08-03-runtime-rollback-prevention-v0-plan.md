# Runtime Rollback Prevention v0 计划

- 日期：2026-08-03
- 状态：executable v0 plan
- 生命周期：plan
- 实施合同：[`2026-08-03-runtime-rollback-prevention-v0-contract.md`](./2026-08-03-runtime-rollback-prevention-v0-contract.md)

## A. 威胁模型 v1

- 唯一防御对象：过时的源覆盖新的 runtime；对手是“过时的自己”。
- 恶意本地 agent、凭证被盗和供应链攻击均为 out-of-scope residual risk。
- 升级前置条件：出现第二信任域，或操作员正式接受扩大的威胁模型；届时另立计划，v0 不隐式扩权。

## B. 主体模型

- **操作员（人）：**负责 push、批准、恢复与降级；批准的唯一含义是操作员在场执行，并用 `scripts/harness_checkpoint.py append` 保存 `command / exit_code / key_output / timestamp`。
- **automation（launchd 任务）：**只读 + report-only；不得修复、同步、push、rebase、merge、降级或写 live runtime。

## C. 保留件

### C1. Source transition matrix

| fresh `remote_tip` / manifest `old` / requested `new` | 唯一 verdict |
|---|---|
| `old == new == remote_tip` | `equal`，只走 `NOOP_COMMITTED` |
| `old == new != remote_tip` | `stale_equal`，STOP，不把落后状态当 NOOP |
| `old` 是 `new` 严格祖先且 `new == remote_tip` | `forward`，要求 manifest expected-old CAS |
| `new` 是 `old` 严格祖先，且两者均为 `remote_tip` 可达的已发布 immutable commit | 仅可走独立批准的 `downgrade` |
| fresh remote 在任一相邻 readback 间 advance，或 publish 后状态未完成验证 | publish 前 STOP；publish 后进入 `SOURCE_PUBLISHED_UNVERIFIED`/incident reconciliation |
| expected-old mismatch、rewrite/unreachable、diverged/unknown、任一 object missing | STOP；禁止 normal/force fallback |

- v0 中 `NOOP_COMMITTED` 是四字段 checkpoint，不新增控制系统；`downgrade` 只接受 `--force-downgrade` 与同次操作员 checkpoint。
- 已发布 remote `refs/heads/main` 永不倒退、永不 force-push；优先从当前 remote tip 创建并正常发布 forward revert，再走普通 `forward`。

### C2. Manifest schema v2

路径：`~/.codex/harness/sync-manifest.json`

```json
{
  "schema_version": 2,
  "repo_identity_version": 1,
  "repo_identity": "<pinned host/owner/repo identity>",
  "source_commit": "<40-char lowercase sha>",
  "managed_surface_digest_version": 1,
  "managed_surface_digest": "sha256:<64 lowercase hex>",
  "synced_at": "<RFC3339 UTC>"
}
```

### C3. W6a 15-path allowlist v1

下表冻结于 baseline commit `010e894e1b2e63ac00aded2c749e68b649f0ac74`。source 相对 repo，target 相对 `/Users/kezheng/.codex`；全部为 `regular-file`、mode `0644`。最终 `SOURCE_SHA` 必须在这些 source paths 保留相同 OID 与 content hash。

| # | target | source | type | mode | Git SHA-1 blob OID | content SHA-256 |
|---:|---|---|---|---|---|---|
| 1 | `AGENTS.md` | `codex/AGENTS.md` | `regular-file` | `0644` | `656edb79cdbc3e66a9773b1a3439a9fcb1c5a189` | `fe620ec9044772208f9ace38d583babbd0652b28cffd5d22fd138fb312694f2e` |
| 2 | `hooks.json` | `codex/hooks.json` | `regular-file` | `0644` | `90779059a393c1fc7a87e3efa94342f72e7350ca` | `d9f7d167f4f5c6f554cfd56625c8391dfc75c790951184cb340bac45cde9b911` |
| 3 | `hooks/compaction_counter.py` | `codex/hooks/compaction_counter.py` | `regular-file` | `0644` | `f125bf0abf99c73966c71666d2fac24f9b701632` | `832b2d2c5c84c479fd6eb71798899c53af642942f593f60cbd3d569218d6024e` |
| 4 | `hooks/compaction_probe.py` | `codex/hooks/compaction_probe.py` | `regular-file` | `0644` | `b32f237d10928c294948f3168e46cceeddf35be5` | `06ff601544027bbad8f45ec275b79c0818ed57003c324e2c814f7f1244da8b39` |
| 5 | `hooks/context_meter.py` | `codex/hooks/context_meter.py` | `regular-file` | `0644` | `2ae38112872a9eaf3acdd91fcb88ea5aef99f871` | `1edbb0b2976aaa6e5cac8b5bfc673deb2808b1e7786c95d5f7a6a693238b9e77` |
| 6 | `hooks/dhf_preprompt.py` | `codex/hooks/dhf_preprompt.py` | `regular-file` | `0644` | `23ee9ee163b75d2515acdbe639063e45dd15f347` | `be0f0f9372cdacd5f03beb60df8269629ecdd07991814ca8dd912b97b4effbb9` |
| 7 | `hooks/harness_guard.py` | `codex/hooks/harness_guard.py` | `regular-file` | `0644` | `76f42b14bc625d070a354ab295b52cb28b6573c3` | `e4090058176ee2cf8595d7b9be3c40693b22fd4ccb4e33b83cbd5c788c88dca1` |
| 8 | `hooks/session_bearing.py` | `codex/hooks/session_bearing.py` | `regular-file` | `0644` | `511f90b4bb0aea4a1775da65e8023c9cfd9de5fd` | `2bc923ce4f31eda81489896c34c73a8c02a121a4f663c2663abd8533b2fbe7f3` |
| 9 | `runtime/evidence.schema.json` | `codex/runtime/evidence.schema.json` | `regular-file` | `0644` | `d7cc85e740b9339fd632106f7a1bb3617481373d` | `3a2db2c32a4cd5bb72f22938a221fa00980ed9c01ae200d95bf97b2b4e888474` |
| 10 | `runtime/evidence/decision-evidence.schema.json` | `codex/runtime/evidence/decision-evidence.schema.json` | `regular-file` | `0644` | `33125d53622231fc7e932209c5169fa03a9bc496` | `47d720f71bd774416cf9fa8f2e03fbec8464aac2724d9b201d4e4f601747c4dc` |
| 11 | `runtime/tool-policy.json` | `codex/runtime/tool-policy.json` | `regular-file` | `0644` | `50d0286327f459a40ade755a297412063850eba7` | `e4a6cee94e9e659d190ce01d44abf77e54666f55fe4f113d5eea5729345769b2` |
| 12 | `skills/codex-fluent/references/maintenance-checklist.md` | `codex/skills/codex-fluent/references/maintenance-checklist.md` | `regular-file` | `0644` | `27a74f97612ec7391722c9b0cb7405a54b91bc2b` | `e774d13c227fe715053cd986249415356f0c02986df5136030fd797550eb3920` |
| 13 | `skills/codex-fluent/scripts/report_active_sessions.py` | `codex/skills/codex-fluent/scripts/report_active_sessions.py` | `regular-file` | `0644` | `b5f451b3a003bc7d4de86534a349472c4ac63fa1` | `ca06a6de34173cfaa353180a455b1f1580bf1deca13cf53cf094e15858c1e571` |
| 14 | `skills/delivery-harness-framework/SKILL.md` | `codex/skills/delivery-harness-framework/SKILL.md` | `regular-file` | `0644` | `6ab8c6e918574e0b0fdc5cdd27022f766233ca3d` | `18148ab8885fd0920df72a248cef23ff3fa1b73a60b3370098542efb4cfdcd00` |
| 15 | `skills/delivery-harness-framework/evals/evals.json` | `codex/skills/delivery-harness-framework/evals/evals.json` | `regular-file` | `0644` | `e86bef72614e54890b31223ea1c81a9d21ad57e6` | `651cfe21377981dad9eadc7c6d264935512a9fcce50638ea0545fe4235348f02` |

聚合算法：表中 Git OID 与 content SHA-256 的值本体仍为裸 lowercase hex；canonical serialization 时，分别给裸值添加固定 ASCII 前缀 `sha1:` 与 `sha256:`，形成 `git_oid` 与 `content_sha` 字段。随后按 target UTF-8 byte order 排序；每行依次拼接 `target`、`source`、`object_type`、`mode`、带前缀的 `git_oid`、带前缀的 `content_sha` 六字段，每字段 UTF-8 bytes 后跟单个 NUL，无额外分隔。golden digest 为 `sha256:254e37a4dd40991b93954caf9dea8baddb4c3525a44078f005c607232d441c19`。discovery 的 count/path/type/mode/OID/content/digest 任一不一致即 STOP、修订计划并重新评审，不得临时决定第 16 项。

### C4. Daily refresh report-only

```text
standalone clone -> empty temporary Codex home -> reproduction verification
live ~/.codex    -> read-only parity audit -> blocker/evidence
```

## D. v0 工作项

- **V1 `fix: guard runtime source transitions`：**`sync_codex_home.sh` 读取 manifest；以 `git merge-base --is-ancestor <old> <new>` 验证新源包含旧源。首次无 manifest 放行 bootstrap；`equal` no-op；`forward` 允许；`stale_equal`、diverged、unknown、普通 downgrade 全部非零拒绝。只有 `--force-downgrade` + 同次操作员 checkpoint 可越过。成功后以同目录 temp、`mv` 和尽力而为的 file/parent `fsync` 原子更新 manifest。
- **V2 `fix: retain deleted runtime files in backups`：**所有使用 `rsync --delete` 的目录同步增加 `--backup --backup-dir="$HOME/.codex/runtime-backups/<UTC timestamp>/"`；失败保留 backup，不宣称完成。
- **V3 `fix: make daily refresh report-only`：**删除 runtime sync；只执行 C4 两行流程。脚本内校验旧 definition digest denylist，命中或无法解析均非零退出并输出 blocker evidence。
- **V4 `docs: require runtime-surface publication`：**凡触碰 `codex/` runtime 面的 commit，推送 `origin/main` 属于完成定义；把同一规则写入 `docs/HARNESS_RUNTIME.md` 的 `Infra Contract`。push 只由操作员在场执行。
- **V5 `test: cover rollback prevention v0`：**V1–V3 契约测试加入 `test_runner.py`，覆盖 downgrade 拒绝、首次无 manifest 放行、force 越过、损坏 manifest fail-closed、backup-dir 恢复删除文件、denylist 命中拒绝。测试只用 Linux CI 可用行为；macOS 专属行为不进入 `test_runner.py`。

每项恰好一个 non-empty commit，顺序固定为 `V1 -> V2 -> V3 -> V4 -> V5`；失败只回退当前 clean-checkout change，不修改 canonical dirty worktree。

## E. Gate 清单

1. `python3 scripts/harness_requirements.py validate docs/plans/2026-08-03-runtime-rollback-prevention-v0-contract.md`
2. `python3 -c "from pathlib import Path; p=Path('docs/plans/2026-08-03-runtime-rollback-prevention-v0-plan.md'); assert len(p.read_text().splitlines()) <= 150"`
3. `python3 -c "import test_runner; test_runner.test_sync_transition_matrix_v0()"`
4. `python3 -c "import test_runner; test_runner.test_sync_backup_dir_v0()"`
5. `python3 -c "import test_runner; test_runner.test_daily_refresh_report_only_v0()"`
6. `PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py`
7. `git diff --check -- docs/plans/2026-08-03-gstack-dhf-runtime-rollback-prevention-plan.md docs/plans/2026-08-03-runtime-rollback-prevention-v0-plan.md docs/plans/2026-08-03-runtime-rollback-prevention-v0-contract.md`

## F. 恢复时限

v0 的 V1–V5 全部 commit 落地当天，daily refresh 以 report-only 模式恢复运行；任一 gate 未通过则保持停用。

## G. Residual risks

- Crash window：`mv` 与尽力而为 `fsync` 不提供全序 durability。
- 恶意 agent：out-of-scope；满足 A 节升级前置条件后另立威胁模型。
- 单文件系统容量竞争：backup 与 live runtime 竞争空间，ENOSPC 时 fail closed 并保留可读 evidence。
