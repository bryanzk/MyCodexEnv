# Phase 0-pre Source Guard Implementation Contract

配套计划：`docs/plans/2026-08-05-phase0-pre-source-guard-implementation-plan.md`

## 1. Contract status

| 字段 | 值 |
| --- | --- |
| 状态 | `PROPOSED` |
| 范围 | **source-stage only** |
| 授权性质 | **不是** runtime authorization；不授权 execution clone 刷新、runtime sync、runtime load、automation unpause、runtime pilot、ShipQ Level 2 或 owner GO |
| 上游设计 | `docs/decisions/2026-08-05-runtime-guard-two-month-top10-claude-review.md`，`REVIEWED_PASS_V6`，sha256 `282c99e4317b12e74d7f9f5a24bc7f64bfb307ee4707f5ae91014bf11a8a4e5c` |
| 设计状态含义 | `REVIEWED_PASS_V6` 仅代表设计评审闭环，**不**代表源码已实施、execution clone 已刷新、runtime 已同步、host 已加载、automation 已 unpause、pilot 已启动或 owner GO |

## 2. Authority

| 项 | 值 |
| --- | --- |
| exact repo anchor | `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv` |
| anchor provenance | 未来任务开始时必须 fresh 运行 `git --no-optional-locks rev-parse --show-toplevel` 并精确匹配 |
| baseline HEAD | `ddd63a626ce3bc317ba4354c60e27c1aa7076580` |
| 未来任务 mode_anchor | `implementation` |

### 2.1 Exact source write allowlist（未来 implementation task）

1. `scripts/sync_codex_home.sh`
2. `test_runner.py`
3. `docs/HARNESS_RUNTIME.md`

**仅此三项。** `scripts/verify_codex_env.sh` 与 `scripts/harness_env_probe.py` 已依证据删除出写集（前者仅 `cmp -s` 磁盘 parity，后者仅读 `config.toml`，二者对 `loaded|readback|hooks.state|trusted_hash` 命中均为 0，无法解除 loaded readback blocker）。不得以"以后可能有用"为由恢复。

### 2.2 Protected dirty files

- `docs/decisions/2026-08-05-runtime-guard-two-month-top10-claude-review.md`：user-owned untracked，byte-for-byte 保护；不得修改、移动、stage、覆盖或吸收进其它文档。实施前后 sha256 必须均为 `282c99e4317b12e74d7f9f5a24bc7f64bfb307ee4707f5ae91014bf11a8a4e5c`。
- 若发现其它未预期变化：**只报告并保护**，不得 reset、checkout、clean、stash 或覆盖。

### 2.3 Prohibited paths

`~/.codex/**`；`/Users/kezheng/.codex/automation-workspaces/gstack-dhf-daily-refresh/**`（controller）；`/Users/kezheng/.codex/automations/gstack-dhf-daily-refresh/**`（含 execution clone `repo/`）；ShipQ 仓库；任何外部系统。

### 2.4 Prohibited actions

runtime sync；automation prepare/apply/unpause；execution clone refresh；commit/push/PR/deploy/archive；reset/checkout/stash/clean/删除；任何写 Git index 的命令；任何真实 runtime-write 测试；清理 execution clone 的 `.git/index.lock`（属独立 owner 操作，不得折叠进实施）。

## 3. Preconditions

未来任务开始时必须 fresh 核验并逐条记录：

| 前置 | 期望值 |
| --- | --- |
| `git --no-optional-locks rev-parse --show-toplevel` | `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv` |
| `git --no-optional-locks rev-parse HEAD` | 记录实际值；与 `ddd63a626ce3bc317ba4354c60e27c1aa7076580` 不同则说明差异来源 |
| `git --no-optional-locks status --short --branch` | dirty-state 分类：`clean` / `user_owned` / `agent_owned` / `generated_disposable` / `unknown_owner` |
| 受保护设计报告 sha256 | `282c99e4317b12e74d7f9f5a24bc7f64bfb307ee4707f5ae91014bf11a8a4e5c` |
| automation 状态 | `status = "PAUSED"`，全程保持不变 |
| execution clone `.git/index.lock` | 若存在，**只报告**，不清理，不折叠进本实施 |

## 4. Source-role model

| role | exact path | 分类 | authority |
| --- | --- | --- | --- |
| `git_head` | 仓库 HEAD 提交树 | source of truth（版本） | 可作 sync source（需 approved digest） |
| `caller_worktree` | `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv` | manual helper 的取源端 | 可作 sync source（需 clean + approved digest） |
| `automation_controller` | `/Users/kezheng/.codex/automation-workspaces/gstack-dhf-daily-refresh` | **producer**（launcher cwd、执行 prepare） | **不是** sync source；其 producer 三件套须 approved 且 prepare path clean |
| `automation_execution_clone` | `/Users/kezheng/.codex/automations/gstack-dhf-daily-refresh/repo` | **历史 sync consumer / sync source** | 可作 sync source（需 clean + approved digest） |
| `runtime_disk` | `~/.codex` 磁盘态 | 目标端 | 只读比对；**不得**充当 loaded 证据 |
| `runtime_loaded` | host 加载态 | 目标端 | **无一手 readback 接口**；unknown/unavailable 即 fail closed |

**Producer set 仅三项**：launcher `run-network-enabled.sh`、`automation.toml`、controller 中**实际执行的** `prepare_gstack_dhf_daily_refresh.py`。

**只读记录、无 authority**：controller 中同名 `scripts/sync_codex_home.sh`（当前 dirty `+93/-0`，与 execution clone 副本不同）；controller 其它 unrelated dirty paths。**不得**为它们建立 authority state。同时如实记载：该同名副本仍是物理可执行旁路，source-only 实施**不能**声称已消除它或达成所有运行路径 100% coverage。

`prepare → execution clone → sync` 之间为 **prompt-mediated edge**（`prepare` 不直接调用 `sync_codex_home.sh`），不得写成受保护的函数调用。

## 5. Shared preflight contract

| 项 | 约定 |
| --- | --- |
| exact placement | `scripts/sync_codex_home.sh` 中，参数校验（`:61`/`:66`）之后、**首个 runtime mutation `:286 mkdir -p "${CODEX_HOME}"` 之前**。必须覆盖全部 21 处 `CODEX_HOME` 写入点，包括 backup 目录创建（`:287-288`）、`cp`、config 修改、七个 `rsync_runtime_dir` caller（`367/372/377/552/577/582/587`）、manifest 写入与 plugin 安装/注册 |
| inputs | `REPO_ROOT`、`CODEX_HOME`、`SYNC_AGENTS_ONLY`、批准集合文件、可选 producer manifest |
| validations | expected file-set 存在性；source role/path 一致性；source clean/dirty；file-set digest ∈ 批准集合；drift direction（runtime 是否更新于 source）；producer manifest 存在/批准/prepare path clean |
| stable reason codes | `source_required_file_missing`、`source_role_path_mismatch`、`source_dirty`、`source_digest_unapproved`、`runtime_newer_than_source`、`attestation_producer_dirty_or_unapproved` |
| exits | 失败 `78`；锁竞争 `75`（`lock_contended`）；通过 `0`（不代表 promotion 成功） |
| zero-write semantics | 任一失败均 nonzero、`status=blocked`、`authorized_clone_root=null`、目标零字节变化、不创建 backup/manifest/receipt |
| 实现约束 | **单一共享入口**，不得在七个 caller 分别补 guard |

## 6. Approved-digest authority

- **调用者不得自报 `approved=true`**。preflight 只接受来自独立批准集合的判定。
- 批准集合来源：仓库内受版本控制的批准清单文件（由未来 implementation task 在写集内创建于 `scripts/sync_codex_home.sh` 可读的仓库路径），其内容变更须经正常 review 流程。
- **当前状态：`BLOCKED / UNRESOLVED`。** 本合同签署时尚不存在独立于调用者的 approved-digest authority；未来 implementation task 必须把该缺口作为显式 blocker 报告，在批准集合的产生与变更流程确定前，preflight 对 digest 项一律按 `source_digest_unapproved` fail closed。
- **不得**为解决该问题新增 service、registry、daemon 或中央授权组件。

## 7. Mode contracts

| 模式 | 收缩后的 exact responsibility |
| --- | --- |
| `--sync-agents-only` | **仅** AGENTS 与 remote docs。`hooks.json`、`hooks/`、`runtime/`、`zsh/`、`config.toml` 移出该分支（当前 `:346` 分支确实写入这五类，属名称与行为不符）。**不保留可重新开启的 legacy bypass**，不新增等效开关 |
| full sync | control-plane promotion 路径；经 preflight 后走 exact-allowlist 事务 |
| bootstrap | 首次装配；同样必经 preflight；不得因"首次"跳过 attestation |
| manual | 取源 `caller_worktree`；需 clean + approved digest |
| automation | 取源 `automation_execution_clone`；额外要求 producer manifest 批准且 executed prepare path clean |

**避免误称 runtime promotion**：source-only 实施完成后，只能声称脚本与测试已就绪；任何"已同步/已加载/已生效"表述均不成立，除非另有 runtime-write 授权并提供 promotion receipt。

## 8. Exact transaction contract

| 项 | 约定 |
| --- | --- |
| allowlist | exact file 列表；非列表内文件不得被写入或删除 |
| backup manifest | 事务开始前记录每个目标的 pre-digest 与 metadata |
| metadata | `lstat` 拒绝 symlink/非普通文件；保留并校验 `uid`、`gid`、`mode` |
| per-file atomic replacement | 同目录 temp file → file `fsync` → `os.replace` → parent directory `fsync` |
| journal | 追加记录已替换路径与 pre/post digest，支持崩溃后恢复 |
| recovery | partial copy、disk digest mismatch、self-test failure 均按 journal 恢复 pre-state 并重算 digest |
| non-target invariants | 非 allowlist 目标 hash **完全不变** |
| lock semantics | `fcntl.flock(LOCK_EX\|LOCK_NB)`；竞争失败方 exit `75`、`reason_code=lock_contended`、零 target 写入；不新增锁服务 |
| atomicity boundary | **可声称**单文件同目录原子替换与 crash-recoverable transaction；**不得声称**整个多文件集合对 host loader 原子可见 |
| loaded readback | `unknown`/`unavailable` 时必须在**真实 target mutation 之前**停止，`reason_code=loaded_readback_unavailable` |

## 9. Fixture contract

单一表驱动测试 `test_sync_phase0_pre_preflight_matrix()` 承载六项；六个名称逐一保留。

| # | fixture | setup | reason_code | exit | authorized_clone_root | before/after hash | rollback assertion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | source-missing | source 缺 `codex/hooks/task_state.py` | `source_required_file_missing` | `78` | `null` | temp `CODEX_HOME` 完整快照不变 | 无 backup/manifest/receipt |
| 2 | controller/execution-clone swapped | 声明 role 与实际 `REPO_ROOT` 形态不符 | `source_role_path_mismatch` | `78` | `null` | 不变 | 同上 |
| 3 | dirty | source 对 allowlist 路径 dirty | `source_dirty` | `78` | `null` | 不变 | 同上；输出 exact dirty paths |
| 4 | unapproved digest | file-set digest 不在批准集合 | `source_digest_unapproved` | `78` | `null` | 不变 | 同上 |
| 5 | runtime-newer | temp `CODEX_HOME` 目标新于 source | `runtime_newer_than_source` | `78` | `null` | 不变 | 同上；不得自动 mirror |
| 6 | attestation_producer_dirty_or_unapproved | producer manifest 缺失/未批准/prepare path dirty | `attestation_producer_dirty_or_unapproved` | `78` | `null` | 不变 | 同上；未执行同名 helper 不进 authority |

六项共同：`status=blocked`；不接触真实 `~/.codex`。

## 10. Receipt schemas

### 10.1 Producer manifest
```
schema_version
verified_at
result
reason_code
producers[]:
  role            # launcher | automation_manifest | executed_prepare
  path
  sha256
  git_clean
  dirty_paths[]
```

### 10.2 Promotion receipt
```
schema_version
transaction_id
started_at
finished_at
producer_manifest_digest
source: { path, role, commit, clean, file_set_digest }
allowlist_digest
backup_manifest_digest
runtime_disk_digest_before
runtime_disk_digest_after
loaded_digest_before
loaded_digest_after
non_allowlist_unchanged
policy_result
self_test_result
outcome
reason_code
```

### 10.3 Controlled-unpause receipt
```
schema_version
unpause_timestamp
producer_manifest_digest
promotion_receipt_digest
current_checkout_digest
controller_digest
execution_clone_digest
runtime_disk_digest
loaded_digest
prepare_to_sync_order
policy_result
self_test_result
outcome
reason_code
```

### 10.4 去重与 fail-closed 规则

- unpause receipt **引用** producer/promotion receipt 的 digest，不复制其完整内容。
- promotion receipt **不复制** unpause 字段。
- `unknown`、`missing`、`unavailable`、disk/loaded mismatch 或任一 `*_result` 非通过 → `outcome=blocked`。
- **不允许**把 disk digest 填入 `loaded_digest`。

## 11. Verification contract

所有执行 future implementation test 的命令必须使用 temp `HOME`/`CODEX_HOME` 或 fixture clone。**不得**对真实 `~/.codex` 运行 `sync_codex_home.sh` 或 `verify_codex_env.sh`。

```
# RED
PYTHONDONTWRITEBYTECODE=1 python3 -c \
  'import test_runner as t; t.test_sync_phase0_pre_preflight_matrix()'

# Syntax
bash -n scripts/sync_codex_home.sh

# Targeted
PYTHONDONTWRITEBYTECODE=1 python3 -c \
  'import test_runner as t; t.test_sync_phase0_pre_preflight_matrix(); t.test_sync_runtime_transaction_rollback_and_locking()'

# Full isolated gate
tmp_root="$(mktemp -d)"
HOME="$tmp_root/home" PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py

# Repo gates
python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav --json
git diff --check
git --no-optional-locks status --short
```

RED 必须来自**行为不满足**（错误 exit code、发生写入、reason code 不符、transaction behavior mismatch）；**不得**以 `AttributeError`、`ImportError`、函数未注册或 fixture 不存在作为目标 RED。不得硬编码 full suite 总测试数。

## 12. Claims contract

future implementation 完成后**最多**允许声称：

- `source_implemented=true`
- `tests_verified=true`

必须同时保持：

| 字段 | 必须值 |
| --- | --- |
| `source_committed/published` | `not_authorized` |
| `execution_clone_refreshed` | `false` / `not_authorized` |
| `runtime_synced` | `false` / `not_authorized` |
| `runtime_loaded` | `unknown` / `blocked` |
| `rollout_observed` | `false` |
| `automation_unpaused` | `false` |
| `runtime_pilot` | `false` |
| ShipQ Level 2 | `NO-GO` |
| `owner_go` | `false` |

## 13. Definition of Done

1. 六 fixture 全绿，reason code 一一对应；共同 acceptance 全部满足。
2. preflight 位于 `:286` 之前，单一入口覆盖 21 处写入点与七个 caller。
3. producer 与 source 两类失败由同一入口拦截。
4. 事务：per-file 原子替换 + metadata 保留 + journal + 回滚；non-target hash 完全不变。
5. 锁竞争 exit `75` / `lock_contended` / 零写入。
6. `--sync-agents-only` 收缩为 AGENTS + remote docs，无 legacy bypass。
7. `loaded_digest` unavailable 时在真实 target mutation 前 fail closed。
8. 全部验证在 temp `HOME`/`CODEX_HOME` 完成；真实 `~/.codex` 未被触碰。
9. 写集严格限于三个文件；受保护设计报告 sha256 未变。
10. 交付结论包含 `command`/`exit_code`/`key_output`/带时区 `timestamp`；claims 严格遵守 §12。

## 14. Explicit non-goals

不实施 runtime promotion；不刷新 execution clone；不 unpause；不 pilot；不 commit/push/PR/deploy/archive；不 reset/checkout/stash/clean/删除；不写 Git index；不清理 execution clone 的 `.git/index.lock`；不新增 daemon、service、registry、policy engine、package registry 或框架；不为未执行的同名 helper 建立 authority state；不消除 controller 中的物理副本（超出 source-only 范围）。

## 15. Required future authorizations

以下每项均需 owner 单独授权，本合同不予提供：

1. source commit / push / publication；
2. execution clone refresh；
3. runtime promotion（且以 loaded readback 接口存在为前提）；
4. automation unpause（须先有完整 controlled-unpause receipt）；
5. runtime pilot；
6. ShipQ Level 2 任何动作；
7. 既有 runtime evidence 的读取、导出、清理或迁移；
8. execution clone `.git/index.lock` 的清理。

## 16. Failure/rollback state machine

| 状态 | 触发 | 动作 | 下一安全动作 |
| --- | --- | --- | --- |
| `preflight_blocked` | 六 reason code 之一 | 零写入，exit `78` | 修正 source/producer 后重跑；automation 保持 `PAUSED` |
| `lock_contended` | flock 失败 | 零写入，exit `75` | 等待持锁方结束后重试 |
| `backup_failed` | backup manifest 创建失败 | 中止，零写入 | 检查目标可写性 |
| `partial_copy` | 事务中断 | 按 journal 逐文件恢复 pre-state | 报告 partial-write，保持 `blocked` |
| `disk_digest_mismatch` | 写后 digest 与批准不符 | 全量恢复 + 重算 digest | 视为 unapproved source，拒绝 |
| `loaded_readback_unavailable` | 无一手 loaded 接口 | 在真实 target mutation 前停止 | 阻塞 runtime promotion；source-only 工作不受阻 |
| `self_test_failed` | policy/self-test 非通过 | 全量恢复 + 双 digest 复核 | 保留失败证据，进入 `blocked` |

任一状态均不得自动升级为 `promoted`、`loaded`、`observed`、`active` 或 `owner_go`。
