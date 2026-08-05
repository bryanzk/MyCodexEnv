# Phase 0-pre Source Guard Implementation Plan

| 字段 | 值 |
| --- | --- |
| 计划状态 | `PROPOSED`，source-stage only；不是 runtime 激活、execution clone 刷新、automation unpause 或 owner GO 授权 |
| 日期 | 2026-08-05，America/Toronto |
| repo anchor | `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv` |
| baseline HEAD | `ddd63a626ce3bc317ba4354c60e27c1aa7076580` |
| 上游设计 | `docs/decisions/2026-08-05-runtime-guard-two-month-top10-claude-review.md`（`REVIEWED_PASS_V6`，sha256 `282c99e4317b12e74d7f9f5a24bc7f64bfb307ee4707f5ae91014bf11a8a4e5c`） |
| 配套合同 | `docs/plans/2026-08-05-phase0-pre-source-guard-implementation-contract.md` |
| 本计划任务模式 | `plan` / document-only；本任务不实施任何 source guard |

## 1. Goal

在 `scripts/sync_codex_home.sh` 中建立一个**共享的、位于所有 runtime mutation 之前的** fail-before-write source attestation preflight，并把 control-plane promotion 从目录级 `rsync -a --delete` 收敛为 exact-allowlist、per-file 原子替换、可回滚的事务。

本阶段的交付边界严格限定为 **source_implemented + tests_verified**。完成后不得声称 execution clone 已刷新、runtime 已同步、host 已加载、automation 已 unpause、pilot 已启动或 owner 已 GO。

`REVIEWED_PASS_V6` 只代表设计评审闭环，不代表上述任何运行态事实。

## 2. Architecture

三个决定分离，本阶段只动第一个与第三个的 source 侧：

| 决定 | 位置 | 本阶段动作 |
| --- | --- | --- |
| source 是否可信 | `sync_codex_home.sh` 入口，所有 mutation 之前 | **新增** shared preflight，六类失败统一 `exit 78` |
| 单个文件如何被替换 | `rsync_runtime_dir()` 的替代实现 | **新增** exact-allowlist per-file 原子替换 + journal |
| host 是否真的加载了新版本 | 无一手 readback 接口 | **不实现**；标记为 blocker，见 §12 |

设计不新增 daemon、service、registry、policy engine 或第二套 source 记账；全部落在既有脚本、`test_runner.py` 与 Python stdlib（`fcntl`、`os.replace`、`hashlib`、`json`）内。

## 3. Fresh verified baseline

全部由本 planning task 在 `HEAD=ddd63a626ce3bc317ba4354c60e27c1aa7076580` 上只读核验。

| 项 | 值 | 状态 |
| --- | --- | --- |
| `git --no-optional-locks rev-parse --show-toplevel` | `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv` | VERIFIED |
| `git --no-optional-locks rev-parse HEAD` | `ddd63a626ce3bc317ba4354c60e27c1aa7076580` | VERIFIED |
| `git --no-optional-locks status --short --branch` | `## main...origin/main [ahead 1, behind 1]`；唯一变化为 `?? docs/decisions/2026-08-05-runtime-guard-two-month-top10-claude-review.md` | VERIFIED |
| 受保护设计报告 sha256 | `282c99e4317b12e74d7f9f5a24bc7f64bfb307ee4707f5ae91014bf11a8a4e5c` | VERIFIED |
| 设计报告状态行 | `REVIEWED_PASS_V6`，五轮 review 闭环，RES-4/5 `CLOSED` | VERIFIED |
| 首个 runtime mutation | `scripts/sync_codex_home.sh:286` `mkdir -p "${CODEX_HOME}"` | VERIFIED |
| backup 目录创建 | `:287` `RUNTIME_BACKUP_DIR=...`、`:288` `mkdir -p "${RUNTIME_BACKUP_DIR}"` | VERIFIED |
| `rsync_runtime_dir()` 定义 | `:290`；内部 `:294` `rsync -a --delete --backup --backup-dir=...` | VERIFIED |
| `rsync_runtime_dir` caller | **7 个**：`367`、`372`、`377`、`552`、`577`、`582`、`587` | VERIFIED（旧结论"五个"已作废） |
| `CODEX_HOME` 写入点总数 | **21** 处（含 `cp`、`mkdir`、重定向、`rsync_runtime_dir`） | VERIFIED |
| `--sync-agents-only` 分支 | `:36-37` 解析；`:346` 分支入口；分支内除 AGENTS 外还写 `hooks.json`、`hooks/`、`runtime/`、`zsh/`、`config.toml` | VERIFIED |
| `verify_codex_env.sh` loaded 能力 | `loaded|readback|hooks.state|trusted_hash` 命中 **0**；`:194-203` 为 `cmp -s` 磁盘 parity | VERIFIED |
| `harness_env_probe.py` loaded 能力 | 同类关键词命中 **0**；`:62` 只读 `config.toml` | VERIFIED |
| `test_runner.py` 注册点 | `TESTS = [` 位于 `:8965`；现有 `def test_*` 共 111 个 | VERIFIED |
| `check_surfaces.py` 对 `docs/plans` 的要求 | `docs/plans/` 下 28 个既有 `.md` 均未在 `docs/repo-index.md` 注册，且基线 `ok:true`；新增计划文档不破坏门禁 | VERIFIED |
| host loaded digest readback | 无任何一手接口 | **UNVERIFIED / 不存在** |

## 4. Corrected call graph

```
run-network-enabled.sh:7    WORKSPACE_ROOT="$CODEX_HOME_DIR/automation-workspaces/$AUTOMATION_ID"
run-network-enabled.sh:90   cd "$WORKSPACE_ROOT"            ← cwd = automation controller
run-network-enabled.sh:93   codex -C "$WORKSPACE_ROOT" …    ← 注入 automation.toml 的 prompt
        │
        │  【代码/配置可证链路到此为止】
        ▼
<controller>/scripts/prepare_gstack_dhf_daily_refresh.py
        :116 main()   :121 clone_root 解析   :161 is_standalone_clone 校验
        :98  make_payload(status=…, clone_root=…)   ← 返回 authorized clone root
        ╎
        ╎  【prompt-mediated edge：prepare 不调用 sync_codex_home.sh】
        ╎  automation.toml prompt step 3/8 要求后续操作只在 clone_root 内进行
        ▼
<execution clone>/scripts/sync_codex_home.sh
        :24/:61/:66   --repo-root 解析与存在性校验
        ★ :286        mkdir -p "${CODEX_HOME}"          ← 首个 runtime mutation
          :287-288    RUNTIME_BACKUP_DIR + mkdir
          :290        rsync_runtime_dir() { … :294 rsync -a --delete --backup … }
          :346        if SYNC_AGENTS_ONLY == "true" → 仍写 AGENTS/hooks.json/hooks/runtime/zsh/config
          :367 :372 :377            （full sync 分支）
          :552                      （workflow，--exclude 'memory/'）
          :577 :582 :587            （第二组 hooks/runtime/zsh）
        ▼
runtime targets: ~/.codex/hooks/*, ~/.codex/runtime/*, ~/.codex/zsh/*, ~/.codex/workflow/*, ~/.codex/config.toml, ~/.codex/AGENTS.md
```

**必须如实标注的两点**：

1. `prepare → execution clone → sync` 之间是 **prompt-mediated edge**，不是受保护的函数调用。计划与合同不得把它写成代码级保证。
2. controller 中存在同名 `scripts/sync_codex_home.sh`（当前 dirty `+93/-0`，与 execution clone 副本不同）。它**无 authority**，但仍是物理可执行副本。source-only 实施**不能**声称已消除该副本或达成所有运行路径 100% coverage。

## 5. Future implementation write allowlist

未来 implementation task 的 exact write allowlist **仅三个文件**：

1. `scripts/sync_codex_home.sh`
2. `test_runner.py`
3. `docs/HARNESS_RUNTIME.md`

### 5.1 从候选中删除的两个文件及其证据

| 文件 | 决定 | 证据 |
| --- | --- | --- |
| `scripts/verify_codex_env.sh` | **删除出写集** | 其 `:194-203` 的 `codex_*_runtime_matches_source` 全部是 `cmp -s` 磁盘比对；`loaded|readback|hooks.state|trusted_hash` 命中 0。它验证的契约（source↔target 字节一致）可由 temp-`CODEX_HOME` 事务测试在 §11 的 non-target invariant 断言中等价覆盖，无需改动该文件。 |
| `scripts/harness_env_probe.py` | **删除出写集** | 同类关键词命中 0；`:62` 仅读取 `config.toml`，属 disk/config observation，**不能**提供 host-loaded readback。它无法解除 §12 的 blocker，因此不构成保留理由。 |

两者均不因"以后可能有用"保留。若未来出现真实 loaded readback 接口，再单独立项评估承载位置。

## 6. Protected files

以下文件在未来 implementation task 中**只读**，不得修改、移动、stage、覆盖或吸收进新文档：

- `docs/decisions/2026-08-05-runtime-guard-two-month-top10-claude-review.md`（sha256 `282c99e4…a4e5c`，当前为 user-owned untracked）
- `scripts/verify_codex_env.sh`、`scripts/harness_env_probe.py`（已删除出写集）
- `~/.codex/**`（runtime）
- `/Users/kezheng/.codex/automation-workspaces/gstack-dhf-daily-refresh/**`（automation controller）
- `/Users/kezheng/.codex/automations/gstack-dhf-daily-refresh/**`（含 execution clone `repo/`）
- ShipQ 仓库全部内容
- 任何外部系统

## 7. Interfaces and stable reason codes

### 7.1 Preflight 接口（bash，位于 `sync_codex_home.sh` 内）

```
preflight_source_attestation
  输入（均已在脚本作用域内可得）：
    REPO_ROOT、CODEX_HOME、SYNC_AGENTS_ONLY
    PHASE0_APPROVED_DIGESTS_FILE   （批准集合来源，见合同 §6）
    PHASE0_PRODUCER_MANIFEST       （可选；automation 路径提供）
  行为：
    成功 → 返回 0，脚本继续
    失败 → 向 stderr 输出单行 JSON {status, reason_code, authorized_clone_root:null}
            并 exit 78，且此前未发生任何 CODEX_HOME 写入
```

### 7.2 冻结的六个 stable reason code

| # | reason_code | 触发条件 |
| --- | --- | --- |
| 1 | `source_required_file_missing` | source 缺 `codex/hooks/task_state.py` 等 expected file-set 成员 |
| 2 | `source_role_path_mismatch` | 声明的 `source_role` 与 `REPO_ROOT` 实际形态不符（含 controller/execution-clone 调换） |
| 3 | `source_dirty` | source 对 allowlist 路径 dirty，或 producer 的 executed prepare path dirty |
| 4 | `source_digest_unapproved` | source file-set digest 不在批准集合内 |
| 5 | `runtime_newer_than_source` | runtime disk digest 对应版本新于 source，方向不明或倒退 |
| 6 | `attestation_producer_dirty_or_unapproved` | producer manifest 缺失、未批准，或实际执行的 controller prepare dirty |

补充两个非 preflight 的稳定码：`lock_contended`（并发，exit 75）、`loaded_readback_unavailable`（事务阶段，见 §12）。

### 7.3 退出码约定

| exit code | 含义 |
| --- | --- |
| `0` | preflight 通过（不代表 promotion 成功） |
| `78` | 六类 source attestation 失败之一（`EX_CONFIG`） |
| `75` | 锁竞争（`EX_TEMPFAIL`） |
| 其他非零 | 事务阶段失败，已按 journal 回滚 |

## 8. Task-by-task TDD sequence

三个任务，每个独立可测、可 review、可回滚。**不为 setup/schema/helper 建空壳任务。**

RED 一律来自**行为不满足**（错误 exit code、发生了写入、reason code 不符），**不得**来自函数不存在、导入失败、未注册或 fixture 缺失。

## 9. 各 task 明细

### Task 1 — Shared preflight + 六 fixture 表驱动测试

| 项 | 内容 |
| --- | --- |
| exact files | `scripts/sync_codex_home.sh`、`test_runner.py` |
| exact symbols / line anchors | 插入点：`sync_codex_home.sh:286` 之前（`mkdir -p "${CODEX_HOME}"` 之前，参数校验 `:61`/`:66` 之后）；测试注册点 `test_runner.py:8965` `TESTS = [` |
| RED | 先在 `test_runner.py` 写入**真实存在**的 `test_sync_phase0_pre_preflight_matrix()`，表驱动覆盖六个 fixture，在 temp `HOME`/`CODEX_HOME` 中调用当前脚本 |
| expected RED failure | 当前脚本无 preflight，六个 fixture 均会继续执行到 `:286` 之后：断言失败信息为 `expected exit 78, got 0`（或非 78）与 `temp CODEX_HOME snapshot changed`。**这是行为性 RED，不是 AttributeError** |
| minimal GREEN | 在 `:286` 之前新增 `preflight_source_attestation` 并调用一次；实现六个 reason code 判定；失败即 `exit 78` 且不触碰 `CODEX_HOME` |
| targeted verification | `PYTHONDONTWRITEBYTECODE=1 python3 -c 'import test_runner as t; t.test_sync_phase0_pre_preflight_matrix()'` → exit `0` |
| rollback proof | 六个 fixture 各自断言 temp `CODEX_HOME` 的完整快照 hash 前后一致、未创建 backup 目录、未生成 manifest 或 receipt |
| task-local DoD | 六 fixture 全绿；`bash -n scripts/sync_codex_home.sh` exit `0`；真实 `~/.codex` 未被触碰；七个 `rsync_runtime_dir` caller 均在 preflight 之后，无需逐个改动 |

### Task 2 — Exact-allowlist 事务 + 并发锁

| 项 | 内容 |
| --- | --- |
| exact files | `scripts/sync_codex_home.sh`、`test_runner.py` |
| exact symbols / line anchors | `rsync_runtime_dir()` 定义 `:290`（内部 `:294` 为现役 `rsync -a --delete --backup`）；七个 caller `367/372/377/552/577/582/587` |
| RED | 新增 `test_sync_runtime_transaction_rollback_and_locking()`，在 temp `CODEX_HOME` 中断言 per-file 原子替换、metadata 保留、journal 存在、失败回滚与锁竞争 exit `75` |
| expected RED failure | 现役目录级 `rsync --delete` 无 journal、无 per-file temp+replace、无 lock：断言失败为 `journal missing`、`non-target file deleted`、`expected exit 75, got 0` |
| minimal GREEN | 为 `rsync_runtime_dir` 增加 `--allowlist-only` 事务路径：`fcntl.flock(LOCK_EX\|LOCK_NB)` → `lstat` 拒绝 symlink/非普通文件 → 同目录 temp → file `fsync` → 保留 uid/gid/mode → `os.replace` → parent dir `fsync` → journal 记录已替换路径。旧路径保留但默认关闭 |
| targeted verification | `PYTHONDONTWRITEBYTECODE=1 python3 -c 'import test_runner as t; t.test_sync_phase0_pre_preflight_matrix(); t.test_sync_runtime_transaction_rollback_and_locking()'` → exit `0` |
| rollback proof | 注入 partial copy、disk digest mismatch、self-test failure 三类失败，各自断言：按 journal 恢复 pre-state；non-target hash 完全不变；返回 next-safe action |
| task-local DoD | 事务与锁测试全绿；non-target invariant 成立；`--allowlist-only` 覆盖七个 caller 的全部目标；**不声称多文件集合对 host loader 原子可见** |

### Task 3 — `--sync-agents-only` 职责收缩 + 契约文档

| 项 | 内容 |
| --- | --- |
| exact files | `scripts/sync_codex_home.sh`、`test_runner.py`、`docs/HARNESS_RUNTIME.md` |
| exact symbols / line anchors | 参数解析 `:36-37`；分支入口 `:346`；分支内现写入 AGENTS、`hooks.json`、`hooks/`、`runtime/`、`zsh/`、`config.toml` |
| RED | 扩展表驱动测试新增一行 case：以 `--sync-agents-only` 运行，断言 `hooks/`、`runtime/`、`zsh/`、`config.toml` 在 temp `CODEX_HOME` 中**未被写入** |
| expected RED failure | 当前分支确实写入上述四类目标：断言失败为 `unexpected write to hooks/` 等 |
| minimal GREEN | 将 `:346` 分支收缩为**仅** AGENTS 与 remote docs；`hooks.json`/`hooks/`/`runtime/`/`zsh/`/`config.toml` 移出该分支，只保留在 full sync 路径。**不保留可重新开启的 legacy bypass**（不新增 `--legacy-agents-only` 之类开关） |
| targeted verification | 同 Task 2 的 targeted 命令；另加 `bash -n scripts/sync_codex_home.sh` |
| rollback proof | 收缩后以 `--sync-agents-only` 运行 temp fixture，断言仅 AGENTS/remote docs 变化，其余目标 hash 不变 |
| task-local DoD | 名称与行为一致；无 legacy bypass；`docs/HARNESS_RUNTIME.md` 记录 producer set、四类 source role、preflight 语义、六 reason code 与三份 receipt schema |

## 10. Fixture matrix

单一表驱动测试函数 `test_sync_phase0_pre_preflight_matrix()` 承载全部六项。**不为每个 fixture 单独建测试函数。**

| # | fixture | setup（temp `CODEX_HOME` + fixture repo root） | expected exit | expected reason_code | authorized_clone_root | temp CODEX_HOME hash | 其他断言 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **source-missing** | fixture source 删除 `codex/hooks/task_state.py` | `78` | `source_required_file_missing` | `null` | 不变 | 无 backup、无 manifest、无 receipt |
| 2 | **controller/execution-clone swapped** | `source_role` 声明为 `automation_execution_clone`，实际 `REPO_ROOT` 为 controller 形态（dirty、缺 `task_state.py`） | `78` | `source_role_path_mismatch` | `null` | 不变 | 同上 |
| 3 | **dirty** | fixture source 对 allowlist 路径制造未提交改动 | `78` | `source_dirty` | `null` | 不变 | 同上；stderr 列出 exact dirty paths |
| 4 | **unapproved digest** | file-set digest 不在批准集合文件内 | `78` | `source_digest_unapproved` | `null` | 不变 | 同上 |
| 5 | **runtime-newer** | temp `CODEX_HOME` 目标较 source 更新 | `78` | `runtime_newer_than_source` | `null` | 不变 | 同上；不得自动 mirror |
| 6 | **attestation_producer_dirty_or_unapproved** | producer manifest 缺失／未批准／executed prepare path dirty | `78` | `attestation_producer_dirty_or_unapproved` | `null` | 不变 | 同上；未执行同名 helper 只记录不进 authority |

**六项共同 acceptance**：exit `78`；`status=blocked`；`authorized_clone_root=null`；temp `CODEX_HOME` 完整 snapshot/hash 不变；不创建 backup、sync manifest 或 promotion receipt；**不接触真实 `~/.codex`**。

## 11. Transaction and concurrency design

### 11.1 并发

- `fcntl.flock(fd, LOCK_EX | LOCK_NB)`，锁文件位于目标 `CODEX_HOME` 内。
- 竞争失败方：exit `75`、`reason_code=lock_contended`、**零 target 写入**。
- 不新增锁服务或守护进程。

### 11.2 每文件原子替换

按 allowlist 逐文件执行：

1. `lstat` 目标与源，**拒绝** symlink 与非普通文件；
2. 在**目标同目录**创建 temp file；
3. 写入后对 temp file `fsync`；
4. 保留并校验 `uid`、`gid`、`mode`；
5. `os.replace(temp, target)`；
6. 对 **parent directory** `fsync`；
7. 向 journal 追加已替换路径与 pre/post digest。

### 11.3 原子性边界（必须如实表述）

- **可声称**：单文件替换对同目录观察者原子可见；崩溃后可依 journal 恢复（crash-recoverable transaction）。
- **不得声称**：整个多文件集合对 host loader 原子可见。普通 `cp`/`os.replace` 无法提供集合级可见性。
- 失败恢复：按 backup manifest/journal 逐文件恢复 pre-state；恢复后重算 disk digest；断言 non-target hash 完全不变。

## 12. Loaded-readback blocker

**当前没有经验证的一手 `loaded_digest` readback。** 证据：`scripts/verify_codex_env.sh` 与 `scripts/harness_env_probe.py` 对 `loaded|readback|hooks.state|trusted_hash` 命中均为 **0**；后者 `:62` 仅读取 `config.toml`（disk/config observation）。

由此确定：

1. **runtime disk digest 不能替代 loaded digest**；
2. `loaded_digest` 为 `unknown`/`unavailable` 时必须 **fail closed**，在任何真实 target mutation 之前停止，reason `loaded_readback_unavailable`；
3. 该 blocker **阻塞 runtime promotion**，但**不阻塞** source-only guard 与 negative fixtures 的实现——Task 1–3 全部在 temp `CODEX_HOME` 内完成，不需要 loaded readback；
4. **不得**为绕过该 blocker 新建伪 loader、daemon、service、registry 或 self-reported loaded receipt。

## 13. Source/clone/runtime lifecycle separation

repo source 的修改**不会**自动影响 automation controller、execution clone 或 `~/.codex` runtime。以下阶段必须分别声明，不得合并或跳级：

| 阶段 | 本计划完成后的允许值 |
| --- | --- |
| `source_implemented` | `true`（Task 1–3 完成后） |
| `tests_verified` | `true`（isolated gate 通过后） |
| `source_committed/published` | **本合同不授权**；`not_authorized` |
| `execution_clone_refreshed` | `false` / `not_authorized` |
| `runtime_promoted` | `false` / `not_authorized` |
| `runtime_loaded` | `unknown` / `blocked`（见 §12） |
| `rollout_observed` | `false` |
| `automation_unpaused` | `false`（automation 保持 `PAUSED`） |
| `pilot_started` | `false` |
| `owner_go` | `false` |

## 14. Full isolated verification commands

未来 implementation task 使用以下命令；**全部在 temp `HOME`/`CODEX_HOME` 或 fixture clone 内**。

**1. RED**
```
PYTHONDONTWRITEBYTECODE=1 python3 -c \
  'import test_runner as t; t.test_sync_phase0_pre_preflight_matrix()'
```

**2. Syntax**
```
bash -n scripts/sync_codex_home.sh
```

**3. Targeted**
```
PYTHONDONTWRITEBYTECODE=1 python3 -c \
  'import test_runner as t; t.test_sync_phase0_pre_preflight_matrix(); t.test_sync_runtime_transaction_rollback_and_locking()'
```

**4. Full isolated gate**
```
tmp_root="$(mktemp -d)"
HOME="$tmp_root/home" PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py
```

**5. Repo gates**
```
python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav --json
git diff --check
git --no-optional-locks status --short
```

**测试计数约定**：断言"新增测试全绿且既有测试无回归"，**不得**硬编码 full suite 总数为 `117` 或任何固定值。

## 15. Explicit non-goals

未来 implementation task **不得**执行：

- 对真实 `~/.codex` 运行 `sync_codex_home.sh`；
- 对真实 `~/.codex` 运行 `verify_codex_env.sh`；
- automation `prepare` / `apply` / `unpause`；
- execution clone 刷新（fetch/pull/rebase/checkout）；
- runtime promotion 或 runtime pilot；
- commit、push、PR、deploy、archive；
- reset、checkout 覆盖、stash、clean、删除；
- 任何写 Git index 的命令；
- 任何 ShipQ Level 2 动作；
- 清理 execution clone 中的 `.git/index.lock`（该项属独立的 owner 操作，**不得**折叠进本实施）。

所有 rollback proof 在 temp `CODEX_HOME` 内完成。

## 16. Final source-stage Definition of Done

1. 六个 fixture 在单一表驱动测试中全部通过，reason code 与 §7.2 一一对应。
2. preflight 位于 `:286` 之前，覆盖全部 21 处 `CODEX_HOME` 写入点与七个 `rsync_runtime_dir` caller；**未**在各 caller 分别补 guard。
3. producer 与 source 两类失败由**同一**入口拦截。
4. 事务实现 per-file 原子替换 + journal + 回滚，non-target hash 完全不变；未声称集合级原子可见性。
5. 锁竞争 exit `75`、`reason_code=lock_contended`、零 target 写入。
6. `--sync-agents-only` 职责收缩为 AGENTS + remote docs，无 legacy bypass。
7. `loaded_digest` unavailable 时在真实 target mutation 前 fail closed。
8. 全部验证在 temp `HOME`/`CODEX_HOME` 完成；真实 `~/.codex` 未被触碰。
9. 写集严格限于三个文件；受保护设计报告 sha256 保持 `282c99e4…a4e5c`。
10. 最终仅声称 `source_implemented=true` 与 `tests_verified=true`；§13 其余阶段保持未授权值。

## 17. Bounded implementation handoff

下一任务的执行边界见配套合同 `docs/plans/2026-08-05-phase0-pre-source-guard-implementation-contract.md`。该合同为 `PROPOSED` / source-stage only，不构成 runtime、execution clone、automation 或 ShipQ Level 2 的任何授权。
