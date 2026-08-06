# Loaded-state 回读机制 · 实施合同

- 配套计划：`docs/plans/2026-08-06-loaded-state-readback-plan.md`
- 工作目录：`/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv`
- 基线：**起工时的 main HEAD**（动代码前记录于报告）。文中行号核实于 `bb641d0`；若因 `codex/global-agents-minimal-fix` 分支合入而漂移，按 §6 处置（行号漂移属可自行确认的小幅漂移，语义冲突才停）
- **前置**：`codex/global-agents-minimal-fix` 分支（AGENTS 修复，改了 `test_runner.py`）**必须先合入 main**再开工——本任务同样写 `test_runner.py`，并行必冲突
- 任务模式：`development`

## 0. 写集（仅限以下）

- `codex/hooks/harness_observer.py`（修改：新增 receipt 刷新）
- `scripts/sync_codex_home.sh`（修改：三段判定、schema 3、自举通道）
- `test_runner.py`（新增测试）
- `docs/HARNESS_RUNTIME.md`（更新 loaded-readback 章节）

**明确排除**：`codex/hooks/` 其它文件、`codex/hooks.json`、`codex/runtime/tool-policy.json`、`runtime-approvals/**`（**不得代 owner 追加 digest**）、其它 `scripts/**`、所有 `~/.codex/**`、automation controller、execution clone、ShipQ。

不 commit、不 push、不对真实 `~/.codex` 运行 sync、不做 runtime promotion。全部验证在临时 `HOME`/`CODEX_HOME` 内。

## 1. 实施要求（对应计划 R1–R3）

### R1 observer 侧

- receipt 路径 `${CODEX_HOME}/harness/loaded-receipt.json`；原子写（mkstemp → fsync → rename）、文件模式 0600、目录复用既有 `DIRECTORY_MODE`；
- `self_digest` 必须运行时读 `__file__` 字节现算 sha256，**禁止**读磁盘上"应该是自己"的路径；
- 字段：`schema_version=1`、`hook_path`、`self_digest`、`session_id`（缺则 null）、`event_kind`、`written_at`；
- `written_at` 必须为**带时区**的 ISO 字符串（建议 UTC）。注意现有 `now_iso()`(`:36-37`) 产出本地时区 ISO——带时区即可接受，但**不得**产出 naive 时间戳；
- **写失败不得抛出**：任何异常吞掉后继续正常 evidence 流程——fail-closed 的位置在 sync 门，不在用户操作路径；
- 每次调起都刷新（幂等覆盖）。

### R2 sync 门

替换 `:454-466` 的无条件拒绝为三段判定，**默认拒绝**：

| 顺序 | 条件 | reason_code |
| --- | --- | --- |
| 1 | receipt 缺失 / 不可解析 / schema≠1 / 字段缺失或类型不符 / `written_at` 为 naive 或不可解析 | `loaded_readback_unavailable` |
| 2 | `written_at` 时刻早于 manifest `synced_at` 时刻（**必须** `datetime.fromisoformat` 解析后比较，禁止字符串比较） | `loaded_readback_stale` |
| 3 | `self_digest` ≠ sha256(当前 `${CODEX_HOME}/hooks/harness_observer.py` 字节) | `loaded_readback_mismatch` |

**manifest/receipt 组合穷尽**：manifest 无 + receipt 无 → 仅自举可过；manifest 无 + receipt 有 → `loaded_readback_unavailable`（异常状态，人工调查）；manifest 有 → 三段判定。

三关全过才继续。manifest 升 schema 3，新增 `loaded_readback` 与 `loaded_receipt_digest` 字段；读取端接受 schema 2（旧代）与 3，写出必为 3。

### R3 自举通道

`--bootstrap-loaded-readback --operator-checkpoint <path>`：

1. 仅当 receipt 文件**不存在**时可用；存在 → `bootstrap_not_applicable`；
2. **仅当不存在含 `loaded_readback` 字段的 manifest（schema 3）时可用**；存在 → `bootstrap_not_applicable`。自举只能发生一次是**机制**：自举后若新 observer 不写 receipt，正门挡住且无法二次自举，异常强制暴露；
3. checkpoint 校验复用 `:367` 的四字段精确断言；
4. manifest 记 `loaded_readback: bootstrap_operator_attested`；
5. 未带 `--operator-checkpoint` 或校验失败 → `bootstrap_checkpoint_invalid`。

## 2. 测试矩阵（表驱动，全部在临时 CODEX_HOME）

| # | 场景 | 期望 |
| --- | --- | --- |
| 1 | 调用 observer（模拟 payload） | receipt 出现；0600；字段齐全；`self_digest` == 文件字节 sha256 |
| 2 | receipt 目标目录不可写 | observer 正常完成 evidence 写入，无异常抛出 |
| 3 | 无 receipt、无 bootstrap flag | `loaded_readback_unavailable` |
| 4 | receipt schema_version=0 / 字段缺失 | `loaded_readback_unavailable` |
| 5 | receipt `written_at` 早于 manifest `synced_at` | `loaded_readback_stale` |
| 6 | receipt digest 与 runtime observer 文件不符 | `loaded_readback_mismatch` |
| 7 | receipt 三关全过 | sync 继续（走到后续既有校验）；成功 manifest 为 schema 3、`loaded_readback=verified`、含 `loaded_receipt_digest` |
| 8 | bootstrap + 合法 checkpoint + 无 receipt | 通过；manifest `loaded_readback=bootstrap_operator_attested` |
| 9 | bootstrap 但 receipt 已存在 | `bootstrap_not_applicable` |
| 10 | bootstrap 无 checkpoint / 字段不符 | `bootstrap_checkpoint_invalid` |
| 11 | 旧 schema 2 manifest 存在时走正门 | 判定 2 以 schema 2 的 `synced_at` 为准，可通过 |
| 12 | 成功 sync 后再读 manifest | schema 3 校验通过；schema 2 写出路径已不存在 |
| 13 | receipt `written_at` 为本地时区 ISO（如 `+08:00`）、manifest 为 UTC "Z"，时刻上 receipt 更新 | 判定 2 通过——证明按时刻而非字符串比较 |
| 14 | receipt `written_at` 为 naive 时间戳 | `loaded_readback_unavailable` |
| 15 | 自举成功后删除 receipt、再次自举 | `bootstrap_not_applicable`（schema 3 manifest 已存在）——证明自举不可重入 |
| 16 | manifest 缺失但 receipt 存在 | `loaded_readback_unavailable` |

RED 必须来自行为不满足，不得以函数不存在、ImportError 或 fixture 缺失制造 RED。不得硬编码全量测试总数。

## 3. 验证命令

```bash
cd /Users/kezheng/Codes/CursorDeveloper/MyCodexEnv
bash -n scripts/sync_codex_home.sh
tmp_root="$(mktemp -d)"; HOME="$tmp_root/home" PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py
python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav --json
git diff --check
git --no-optional-locks status --short
```

动代码前先捕获基线（全量 test_runner 通过数、未跟踪文件清单），写入报告。

## 4. 完成标准

1. 写集仅四个文件；`runtime-approvals/**` 与 `codex/hooks.json` 零改动。
2. 三段判定顺序与 reason_code 精确匹配 §1-R2；默认路径全部拒绝；manifest/receipt 三种组合行为与穷尽表一致（用例 3、16）。
3. 时间戳按时刻比较且拒绝 naive（用例 13、14）。
4. 自举五条约束逐一可证伪，**含不可重入**（用例 8、9、10、15）。
5. observer 写失败不影响 evidence 主流程（用例 2）。
6. schema 2 manifest 向后兼容可读（用例 11）。
7. 全量 test_runner 无回归；`bash -n`、`check_surfaces`、`git diff --check` 通过。
8. 报告输出实施后的**新源码 digest**（改了 `codex/` 必然变值）供 owner 批准，**不得自行写入清单**。
9. 报告含计划 §5 的 owner 操作序列。
10. 结论只声称 `source_implemented=true` + `tests_verified=true`；`runtime_synced` / `runtime_loaded` / `rollout_observed` / `runtime_active` / `owner_go` 维持既有未授权值。**不得**声称回读门已在真实 runtime 生效。

## 5. 非目标

不给其它 hook 加自证；不改 trusted_hash / config.toml；不对真实 `~/.codex` 做任何操作；不追加 approved digest；不改 transition 门与 digest 门语义；不新增 daemon / service / framework；不 commit / push。

## 6. 冲突处置

实现中若发现本合同与代码现实冲突（行号漂移、字段名不符、既有测试依赖被破坏），**停下并精确报告**；不得放宽三段判定或自举约束来"跑通"。
