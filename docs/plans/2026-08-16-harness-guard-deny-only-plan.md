# Harness Guard Structured-Only 收缩实施计划

- 计划编号：`MCE-20260816-harness-guard-deny-only`
- 日期：2026-08-17
- 状态：`isolated_runtime_verified`
- Implementation entry Guard SHA-256：`6f6ce571e11adb44808bcd8135b962e36584e269232de0d2bc3ad7344f22a029`
- Source candidate Guard SHA-256：`eaff608b4d63aa8e64a4e62525124a83206ddaf3f732d1fe223b1230dc55dd74`
- 目标：把 Codex `PreToolUse` Guard 收缩为只检查结构化 target 的极小 deny-only 系统安全内核。

## 1. 决策

Guard 仅处理 host 已结构化提供的 tool kind、patch header 和 target path，不解释 shell command text。

Guard 只返回：

```text
deny(reason_code) | no_match
```

- `deny` 保留现有 `{"decision":"block","reason":...}` wire。
- `no_match` 返回 `{}`，交由 native execpolicy、sandbox 和 approval 决策。
- phase、cwd scope、task state、skill、receipt、session lineage 和 integrity state 不进入 verdict。
- cwd 只用于机械解析结构化相对 target，不作为授权信号。

## 2. 三类 structured hard deny

### SD-01 — Credential target access

已知结构化 read/write/edit/delete 工具直接访问：

- `<CODEX_HOME>/auth.json`
- `~/.ssh/id_*`，排除 `.pub`
- `~/.aws/credentials`
- `~/.netrc`

普通项目 `.env`、`cert.pem`、generic `.key`、示例文本和 shell 字符串不属于本类；不得仅根据扩展名推断 credential。

### SD-02 — Active control-plane mutation

已知结构化 mutation 工具直接修改：

- `<CODEX_HOME>/hooks.json`
- `<CODEX_HOME>/hooks/**`
- `<CODEX_HOME>/rules/**`
- `<CODEX_HOME>/runtime/tool-policy.json`
- `<CODEX_HOME>/runtime/harness-scope.json`
- `<CODEX_HOME>/runtime/harness-guard-targets.json`
- `<CODEX_HOME>/harness/deployed-manifest.json`

以下明确排除：

- `config.toml`
- `skills/**`
- `plugins/**`
- `memories/**`
- `state*.sqlite`
- `generated_images/**`
- `visualizations/**`
- 普通 evidence/output

不得扩大为整个 `<CODEX_HOME>`。

### SD-03 — OS persistence mutation

已知结构化 mutation 工具直接写入：

- 用户下的 `.zshenv`、`.zprofile`、`.zshrc`、`.zlogin`、`.bash_profile`、`.bash_login`、`.bashrc`、`.profile`；
- `/etc` 下的 `zshenv`、`zprofile`、`zshrc`、`zlogin`、`profile`、`bashrc`、`bash.bashrc`；
- 用户 `~/Library/LaunchAgents`；
- 系统 `/Library`、`/System/Library` 下的 LaunchAgents/LaunchDaemons paths。

只读结构化工具返回 `no_match`。

## 3. Native shell boundary

所有 shell command 均由 Guard 返回 `no_match`，包括：

- broad destruction；
- download-and-execute；
- shell redirection、pipeline、wrapper 和 process substitution；
- package manager、network、SSH、SCP、rsync 和 deploy；
- shell 形式的 credential/control-plane/persistence access；
- runtime promotion command。

这些行为必须由 Codex native execpolicy、sandbox、approval、用户授权及对应 entrypoint preflight 承担。

本计划不自建 shell parser，也不维护命令语法 allow/deny matrix。新增 shell 变体不构成 Guard 修改理由。

## 4. Normal workflow matrix

以下全部 `no_match`：

| 行为 | 承接层 |
| --- | --- |
| 普通 repo write、Git、tmp/build | workspace sandbox、AGENTS |
| network、package install、普通下载 | native network policy/approval |
| shell execution 与 destructive argv | native execpolicy/sandbox/approval |
| skill/plugin CRUD 与安装 | sandbox、skill validator |
| subagent、receipt、worker count | workflow/skill |
| phase、review-only、handoff | AGENTS、DHF lifecycle |
| integrity/source-runtime mismatch | SessionStart、doctor、verifier |
| 业务或客户副作用 | typed consumer、owner confirmation |
| unknown tool 或 malformed/partial input | native boundary |

## 5. Structured normalization

Guard 仅识别：

- `read`、`read_file`、`list_dir`、`list_directory`；
- `write`、`edit`、`multi_edit`、`delete`、`delete_file`；
- `apply_patch` 的 dict 或 freeform input；
- patch 的 Add、Update、Delete 和 Move-to headers。

规则：

- patch body、文档、搜索 pattern、stdout/stderr 不参与 verdict；
- 每个 target 独立 canonicalize，任一命中即 deny；
- 现有 symlink 解析后的目标参与判断；
- protected target identity 使用保守 case-insensitive 比较，大小写别名必须得到相同 verdict；
- 每个 target 保留 lexical、parent-resolved entry、referent 三个 identity；
- direct tools 映射为 read/write/delete touch；patch Add=`write`、Update=`read+write`、Delete=`read+delete`、Move=`read(source)+delete(source)+write(destination)`；
- SD-01 对所有 touch 检查 lexical/entry，read/write 另检查 referent；SD-02/03 的 write 检查 referent、delete 检查 entry；
- 只展开 exact HOME/CODEX_HOME 前缀；其他 `$` 与 path whitespace 保持字面 identity；
- 冲突 tool identity、多个 input container 或 structured payload 顶层 `command`/`cmd` 返回 `no_match`；
- direct structured tool minimum shape 不完整时返回 `no_match`；
- `apply_patch` 只做 native-normalized conservative header scan：忽略 Environment ID/body，trim marker/header target，protected header 即 deny，不复制完整 native grammar；
- existing multi-link read/write targets 仅在 `st_nlink>1` 时按需比较 protected exact paths/roots 的 `(st_dev, st_ino)`；delete 仍只判断 entry；
- 未知 tool、缺失 target、非法 path 或未知 payload 返回 `no_match`；
- policy/scope 文件缺失或非法不影响三类内建 deny。

## 6. Implementation scope

本次 source write set：

```text
codex/hooks/harness_guard.py
codex/hooks/harness_observer.py
codex/hooks/session_bearing.py
test_runner.py
```

另新增本计划文件。用户另行授权 `docs/harness-state.md` append-only checkpoint；它不属于 source artifact。不得修改其他计划、policy、scope、`hooks.json`、promotion script、Claude copy 或 live runtime。

### harness_guard.py

- 只保留 payload extraction、structured target normalization、三类 matcher 和 wire adapter。
- 只用 Python 标准库。
- 不读取 Git、transcript、task state、receipt、policy、scope、manifest、WAL 或 evidence。
- 不解析 shell command。

### harness_observer.py

- 不 import Guard。
- phase 仅作为 `payload_or_environment` telemetry，并标记 `authoritative=false`。
- evidence/loaded receipt 继续 best-effort；malformed JSON 与 stdin `OSError` 不阻断。

### session_bearing.py

- 不 import Guard。
- 只保留 bounded repo-local recovery context。
- 不注入 phase/scope/integrity Guard policy。

## 7. Tests

`test_runner.py` 使用一个 structured truth table 覆盖：

- SD-01 至 SD-03 正例；
- benign `.pem/.key` counterexamples；
- credential symlink；
- SD-01/02/03 大小写别名与大写 SSH `.PUB` counterexample；
- 固定 zsh/bash startup inventory；
- delete/Move 与 read/write 的双向 control-plane/persistence symlink identity；
- `auth.json`、`.netrc`、`.aws/credentials`、`.ssh/id_*` credential leaf symlink operation matrix；
- credential ancestor symlink、真实 Move/Add destination referent 与 Delete/Move source read；
- POSIX 字面 `$`、path whitespace、partial tool shape 与 malformed patch；
- native-valid Environment ID、marker whitespace 与 trimmed patch target；
- credential/control-plane/persistence hard-link read/write/delete/patch operation matrix；
- 冲突 identity/container 与 structured 顶层 command malformed payload；
- mixed target 正反顺序；
- dict/freeform patch 与 Move-to；
- patch prose inert；
- control/persistence read `no_match`；
- excluded application surfaces `no_match`；
- phase/subagent/unknown input `no_match`；
- representative shell command 全部 `no_match`；
- missing/invalid legacy policy 与 scope 不影响内建 deny；
- observer/bearing poisoned Guard import fixture；
- observer stdin error best-effort；
- legacy block wire。

旧 phase/scope/integrity/receipt/shell-classification decision tests删除，不作为 compatibility requirement。

## 8. Performance

Entry 每类使用 30 个、candidate 每类使用 90 个 fresh Python subprocess：

- structured ordinary `no_match`；
- structured SD-02 deny；
- structured SD-02 hard-link deny。

Gate：

- worst `<= 0.10s`；
- p95 `<= 0.05s`；
- 同 host median 相对 entry baseline 至少下降 30%。

Fresh receipt：

| Fixture | Entry median | Candidate median | Reduction |
| --- | ---: | ---: | ---: |
| structured `no_match` | 59.57ms | 32.18ms | 45.98% |
| structured SD-02 deny | 59.00ms | 32.47ms | 44.95% |
| structured SD-02 hard-link deny | 58.97ms | 32.76ms | 44.44% |

Entry 与 candidate 使用同一 host、同一 payload 于 `2026-08-18T03:13:01Z` 成对测量。

## 9. Verification lifecycle

### Source and isolated

必须通过：

```text
python3 -m py_compile <four implementation files>
focused structured Guard/observer/bearing/performance tests
python3 test_runner.py
python3 scripts/check_surfaces.py --repo-root "$(pwd)"
git diff --check
exact write-set audit
```

随后使用 approved temporary source snapshot 和 isolated `<CODEX_HOME>`：

- promotion transaction；
- harness-only verifier；
- loaded observer receipt；
- structured hook-process probe `[block, no_match]`；
- failure-injection rollback；
- isolated full test runner。

成功状态：

```text
source_green
isolated_runtime_verified
live_runtime_not_authorized
```

Fresh isolated receipt：`PYTHONDONTWRITEBYTECODE=1 python3 -c 'import test_runner; test_runner.test_harness_scope_and_seven_target_manifests(); test_runner.test_harness_seven_target_promotion_wal_and_deployed_manifest()'`，`exit_code=0`，`key_output=[PASS] isolated promotion, verifier, loaded receipt, hook-process probe [block, no_match], rollback, and manifest`，`timestamp=2026-08-18T02:54:02Z`。Codex CLI 0.147.0 的实际 host shape 仅由既有 2026-08-10 18/18 receipt 支持；本候选未做新的 native host execution，live promotion 前必须重跑。

Fresh source gate receipts：

| Gate | Command | Exit | Key output | UTC timestamp |
| --- | --- | ---: | --- | --- |
| compile | `PYTHONPYCACHEPREFIX=/private/tmp/MCE-20260817-harness-guard-pycache python3 -m py_compile codex/hooks/harness_guard.py codex/hooks/harness_observer.py codex/hooks/session_bearing.py test_runner.py` | 0 | four implementation files compiled | `2026-08-18T02:53:21Z` |
| focused + performance | `PYTHONDONTWRITEBYTECODE=1 python3 -c 'import test_runner; test_runner.test_harness_guard_policy_decisions(); test_runner.test_harness_observer_and_bearing_do_not_import_guard(); test_runner.test_session_bearing_hook(); test_runner.test_canonical_harness_hook_performance_budgets()'` | 0 | structured/observer/bearing/SessionStart pass; hard-link p95 36.25ms, worst 42.51ms, improvement 45.91% | `2026-08-18T03:11:43Z` |
| full | `PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py` | 0 | ran=118 passed=117 skipped=1 failed=0; hard-link p95 36.00ms, worst 36.95ms, improvement 44.44% | `2026-08-18T03:13:01Z` |
| surfaces | `python3 scripts/check_surfaces.py --repo-root "$(pwd)"` | 0 | surfaces manifest consistent | `2026-08-18T03:26:24Z` |
| diff | `git diff --check` | 0 | no output | `2026-08-18T03:26:24Z` |
| exact scope | `git status --porcelain=v1` plus exact allowlist assertion | 0 | exact_write_set=6/6: five source artifact paths plus authorized WAL | `2026-08-18T03:26:36Z` |

Source recovery anchors are the implementation-entry and candidate Guard SHA-256 values at the top of this plan. No source rollback mutation is authorized before commit; isolated rollback is verified above, and live rollback belongs to a separately authorized promotion task.

### Live runtime

Live promotion 必须在新的独立任务中获得用户明确授权，并重新执行 persisted-rule/native capability audit、generation transaction、loaded readback、host probe 和 full gate。

本计划不授权 live promotion。

## 10. Stop conditions

任一条件成立即停止：

- 需要扩大 write set；
- 结构化 mixed target 依赖顺序；
- patch body 或 shell command text 影响 verdict；
- 普通 repo/network/skill/subagent 被 Guard block；
- Guard 重新读取 phase、policy、Git、receipt 或 manifest；
- source/isolated gate、rollback 或 readback 不通过；
- 需要修改 native policy 或 live runtime但没有独立授权。

## 11. Acceptance criteria

- [x] Guard 只有 structured target normalization 与三类 deny。
- [x] 所有 shell command 无条件 defer native。
- [x] Phase、cwd authorization、skill、receipt 不影响 verdict。
- [x] Observer 与 bearing 不 import Guard。
- [x] Source、isolated、live 与 loaded identity 分离。
- [x] Focused/full/performance/isolated/surface gates有 fresh receipts。
- [x] Source artifact 只有四个实现文件和本计划；working tree 另含授权的 append-only WAL checkpoint。
- [x] 候选验证阶段无 live promotion、commit、push 或范围外修改。

## 12. Committee review gate

最终 artifact 由系统安全、Codex runtime/DevEx、迁移/测试/运维三个独立专家域审查。只有 iterative closure 与 fresh blind final 均无 open material finding、required evidence 完整且 residual risks 明确时，才能声明 committee pass。

Rubric v3 amendment：direct structured path 保留 whitespace；patch marker/header target 按 Codex 0.147.0 native normalization trim。`apply_patch` 只要求 native-valid protected headers 不得绕过；native-invalid protected patch 可被保守 deny，不要求 Guard 复制 native parser。lexical identity 允许先归一化已知 HOME/CODEX_HOME 根别名，再保留其余 symlink 未解析；HG016 记为 `ACCEPTED_RISK`，没有已知 deny bypass。委员会 `max_rounds=7`，第 6 轮用于 closure、第 7 轮用于 blind final。

Scope rulings：native-valid hunk context 若形如 protected header，保守 false block 记为 `ACCEPTED_RISK`；`~/Library/LaunchDaemons` 记为 `UNSUPPORTED`。两项已记录到 MyCodexEnv Linear issue `SHI-41` comment `2cee0e57-6ad6-4aad-9a1a-e655de13c121`。不再创建新的 HG；只有 native-valid structured payload 对 SD-01/02/03 的可执行 false allow 才重新打开 blocker。

Hard-link closure：existing regular-file aliases 只在 multi-link read/write touch 上执行有限 inode matching；真实 native Update probe证明 outside alias 现在 `block`，direct/patch Delete 仍按 outside entry 语义 `no_match`。recursive protected scan仅在 `st_nlink>1` 时触发。

Fresh native hard-link receipts：Update alias `Guard=block` 且 native mutation 证明同 inode，`exit_code=0`、`timestamp=2026-08-18T02:52:55Z`；Delete/Move source alias `Guard=no_match`、native 仅移除 outside entry、protected 内容保持 `original`，`exit_code=0`、`timestamp=2026-08-18T03:12:19Z`。

Native `apply_patch` wire closure：Codex 0.147.0 `tool_input.command` protected patch 于 `2026-08-18T03:30:38Z` 重现 `no_match` RED；最小 extractor 修复后 structured contract 于 `2026-08-18T03:31:13Z` GREEN，native-shape probe 于 `2026-08-18T03:31:36Z` 返回 `block`。同时存在 `patch` 与 `command` 时仍 defer native。

Acceptance ledger：

| ID | Disposition | Closure |
| --- | --- | --- |
| HG001 | CLOSED | APFS case aliases covered for SD-01/02/03 |
| HG002 | CLOSED | Exact zsh/bash startup inventory frozen |
| HG003 | CLOSED | Isolated promotion/verifier/receipt/probe/rollback receipt |
| HG004 | CLOSED | Shell commands defer native |
| HG005 | CLOSED | Observer/bearing do not import Guard |
| HG006 | CLOSED | Fresh worst/p95/median-improvement gates |
| HG007 | CLOSED | Five-file source artifact plus authorized WAL |
| HG008 | CLOSED | Operation-aware symlink entry/referent identity |
| HG009 | CLOSED | Ambiguous identity/input containers defer |
| HG010 | CLOSED | POSIX literal `$` retained |
| HG011 | CLOSED | Native Move composite touch semantics |
| HG012 | CLOSED | Credential ancestor symlink identity |
| HG013 | CLOSED | Direct tool minimum shape; native-invalid patch parity non-goal |
| HG014 | CLOSED | Direct whitespace preserved; patch header native-trimmed |
| HG015 | CLOSED | Native-valid Environment ID/marker/target dialect cannot bypass |
| HG016 | ACCEPTED_RISK | Known HOME/CODEX_HOME root alias normalization; no known false allow |

## 13. Non-goals and deferred findings

- 不修改 native execpolicy、sandbox、approval 或 persisted rules；其当前承接能力是 live promotion 前必须重新验证的依赖。
- 不修改 `hooks.json` matcher。
- 不复制或版本化维护完整 native `apply_patch` parser。
- 不修改 Claude hook 副本。
- 不清理 legacy policy/scope 文件。
- 不更新其他文档；`docs/repo-index.md` 仍描述旧 phase/scope/integrity Guard，该 drift 明确延期，不得声称其已反映 source candidate。
- 不创建 DHF Core、独立 repo 或 release。
- 不修改 ShipQ 或业务 consumer。
