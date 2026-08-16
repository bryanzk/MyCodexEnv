# DHF Runtime Hook 所有权与抽取计划

- 计划编号：`MCE-20260816-dhf-runtime-hook-extraction`
- 日期：2026-08-16
- 状态：`plan_only`
- 记录基线：`97487293150b67ff3e40bdc9e3b099e63c950960`
- 目标：把可复用 DHF 行为移交给未来独立 DHF 仓库，同时让 MyCodexEnv 继续唯一控制 Codex runtime 的组合、安装、promotion 与回读。

## 1. 决策

不迁移 `codex/hooks/` 整个目录，也不把任何现有 hook 原样称为 portable DHF Core。

采用三层所有权：

1. **DHF Core**：只拥有纯治理规则、合同、schema 和 repo-local helper。
2. **Codex adapter**：把 Codex payload、session/transcript 和 hook response 映射到 Core interface；第一阶段仍由 MyCodexEnv 持有，出现第二个独立 Codex consumer 后才评估上游化。
3. **MyCodexEnv deployment**：唯一拥有 `hooks.json`、active policy/scope、runtime 路径、sync、原子 promotion、attestation、loaded readback 和 live `<CODEX_HOME>`。

独立 DHF checkout、分支、installer 或 release 不得直接写 `<CODEX_HOME>`。DHF release、MyCodexEnv pin-bump、source integration、runtime promotion 和 loaded readback 是五个独立状态；前一状态不授权后一状态。

## 2. 本计划范围

### 2.1 当前产出

本任务只新增本计划文件：

- `docs/plans/2026-08-16-dhf-runtime-hook-extraction-plan.md`

### 2.2 非目标

本任务不：

- 修改任何 hook、runtime config、测试、现有计划或 CI；
- 修复当前 bootstrap pin、guard、observer、session bearing 或 compatibility checker；
- 创建独立仓库、release、tag、commit、PR 或 push；
- 修改 ShipQ；
- 同步、promotion 或探测 live `<CODEX_HOME>`；
- 拆分 `test_runner.py` 或迁移 simplification corpus；
- 引入 package manager、plugin framework、自动 updater 或新的后台进程。

## 3. 当前事实

`codex/hooks.json` 当前注册：

- `SessionStart`：`session_start_require_naming.py`、`session_bearing.py`；
- `UserPromptSubmit`：`compaction_probe.py`、`model_router.py`、`dhf_preprompt.py`；
- `PreToolUse`：`harness_guard.py`；
- `PostToolUse`：`harness_observer.py`。

当前抽取要求存在两个需要在未来 Phase 0 修订的所有权问题：

- `docs/plans/2026-06-15-dhf-independent-core-requirements.md` 把 guard、observer、model router 一起列入 adapt set；`model_router.py` 不属于 DHF 生命周期治理。
- 同一 adapt set 漏掉最直接承载 DHF prompt policy 的 `dhf_preprompt.py`，也没有完整表达 `task_state.py`、session bearing、promotion manifest 与 loaded readback 的依赖闭包。

当前 runtime 约束：

- guard 的 policy 来自 `<CODEX_HOME>/runtime/tool-policy.json`；缺失或非法时当前实现返回空 policy，`decision()` 随后放行。
- guard promotion 由 `codex/runtime/harness-guard-targets.json` 固定为恰好七个目标；`tool-policy.json` 被明确排除。
- `harness_observer.py` 写入 `loaded-receipt.json`，sync 用其运行中 `__file__` digest 做 loaded readback。
- `session_bearing.py` 会在全局 `SessionStart` 中执行当前 repo 的 `scripts/harness_recover.py`，目前只检查文件是否存在。

以上事实是迁移顺序约束，不在本计划编写任务中修复。

## 4. 目标所有权

| Surface | DHF Core | Codex adapter | MyCodexEnv / consumer |
| --- | --- | --- | --- |
| `dhf_preprompt.py` | activation、profile selection、escalation signals、profile contract | payload 解析、response envelope、skill text 注入 | hook 注册、ShipQ 选择与 runtime 路径 |
| `harness_guard.py` | category/risk/phase-policy/verdict 的确定性规则 | Codex tool payload、phase source 和 legacy block envelope | protected roots、active policy、integrity watch、恢复命令、promotion |
| `harness_observer.py` | evidence event shaping、最小化、hash、截断 | PostToolUse payload 到 observation 的映射 | JSONL sink、权限、rotation、loaded receipt/readback |
| `task_state.py` / `codex-task` | phase vocabulary 与 declaration record contract | Codex transcript/session/TTL resolver | 实际 task-state 路径、CLI 安装与审计 |
| `session_bearing.py` | recovery/bearing 输出合同 | 仅在 verified helper 安装合同成立后再评估 | 当前整个 hook 留在 MyCodexEnv |
| `model_router.py` | 不属于 DHF | 不进入第一版 DHF adapter | 留在 MyCodexEnv |
| compaction probe/counter/meter | 不属于 DHF | 不进入第一版 DHF adapter | 留在 MyCodexEnv |
| session naming | 不属于 DHF | 不进入 DHF adapter | 留在 MyCodexEnv |
| `shipq_dhf_preprompt.py` | 不属于 DHF Core | ShipQ adapter | 源码最终归 ShipQ；MyCodexEnv 最多负责已审计安装 |
| `hooks.json` | 不拥有 | 不拥有 | MyCodexEnv 唯一拥有组合与执行顺序 |
| `tool-policy.json` | portable schema/default template | host tool-name mapping | active policy 值和 evidence 路径由 MyCodexEnv 拥有 |
| `harness-scope.json`、guard targets | 不拥有 | 不拥有 | MyCodexEnv 机器治理与 promotion 合同 |

## 5. Core interface

只使用 Python 标准库和普通函数；本计划不引入 class hierarchy、plugin registry 或 IPC。

### 5.1 Prompt policy

```text
profile_state := absent | valid(active_profile) | malformed
rollout_state := enabled | legacy | invalid

evaluate_prompt(prompt_text, profile_state, rollout_state)
  -> activated, activation_reason, profile,
     escalation_signals, mandatory_helpers,
     required_output_fields, authoritative_gates
```

Adapter 必须保留 `profile_state` 的三个 tag，不得把 `malformed` 降级为 `absent`；`valid` 只携带已验证的 `active_profile`。`DHF_PREPROMPT_SIMPLIFIED_PROFILES` 的 raw env value 与 rollout authority 唯一属于 MyCodexEnv deployment；Adapter 只把精确 `1` 标记为 `enabled`、把 `0|false|off|legacy` 标记为 `legacy`、其余标记为 `invalid`，不得决定 policy。Core 接收 tagged `rollout_state` 并决定 profile/legacy 语义与 invalid diagnostic，本计划不退役该 switch。Core 不接收 `cwd`、ShipQ 路径、skill 文件路径或 Codex response shape。Adapter 负责 host payload 提取、consumer 选择、skill text 读取和 `hookSpecificOutput`；显式 opt-out 在 consumer routing、profile retention 和激活之前生效。

### 5.2 Guard policy

```text
evaluate_tool_call(normalized_call, phase_context, policy_context)
  -> decision, reason_code, risk_tier
```

`normalized_call` 必须保留全部 raw targets、command text、cwd 和解析状态，不能把 protected/mixed-target 判断压缩成调用者可伪造的单一布尔值。Core 负责确定性分类与 policy verdict；Codex adapter 负责取得可信 phase source、integrity status、receipt status 和 host response envelope。

Core 只产出语义 verdict；Codex adapter 是唯一 host enforcement point，且不得把 Core 的 block 降级为 allow/continue。完整的 scope、policy 和每个 target 的 parsing status（包括 missing、invalid、partial 或 unknown）必须进入同一次 Core 判定，Adapter 不得在判定前丢弃或修复失败状态。

Guard interface 在 Phase 3S 的独立 security review 前不冻结成 Python import，也不允许现有 guard 增加新 runtime dependency。

### 5.3 Evidence policy

```text
build_evidence_event(observation)
  -> bounded schema-valid event
```

Core 负责字段、hash、最小化、截断和大小上限。Adapter/sink 负责 timestamp/source discovery、目录、文件权限、rotation、append、fsync 和 loaded receipt。

## 6. 版本与 runtime 组合

未来独立 DHF release 必须提供 immutable tag、40 位 revision 和 release manifest。MyCodexEnv 只消费 manifest 中选定的 exact Core artifact：

- upstream Core artifact 进入 `docs/dhf-core-pin.json` 的 release mapping；
- MyCodexEnv-owned wrapper、`hooks.json`、scope 和 promotion 文件不伪装成 upstream exact copy；
- 如果未来 MyCodexEnv exact-copy 上游 Codex adapter，该 adapter 也必须进入 release manifest 和 consumer pin；
- runtime 永远执行已经进入 MyCodexEnv、通过 source integration 并获明确 promotion 授权的字节；不得从开发 checkout 或网络动态 import。

现有 `loaded-receipt.json` 只证明运行中的 observer wrapper `__file__` digest，不证明它 import 的 Core artifact 已加载执行。每个 runtime-executed Core 必须由 deployed-manifest digest、对应 release/pin identity，以及可归因于该 identity 的 post-promotion hook probe 建立执行身份链；三者缺一时不得声明 `runtime_verified`。Promotion 与 rollback 两个方向都必须生成完整 generation receipt；rollback 必须绑定恢复后的旧 deployed-manifest digest、旧 release/pin revision、fresh loaded readback 和 attributable host probe，缺一不得声明 `rollback_verified`。如果需要扩展 receipt 或其 promotion targets，必须在独立任务中冻结单独的精确 write set，不得作为 Core 抽取的顺手改动。

一个 DHF release tag/revision 足够，不新增独立的 hook version、自动更新通道或第二份可编辑源码。

## 7. 实施阶段

每个阶段是独立任务；完成前一阶段不自动授权下一阶段。

每个 phase 任务开始前必须冻结：精确最小文件 write set、明确 deletion set（没有删除时写 `[]`）、non-goals、entry state 和唯一 exit state；任务中不得扩大。只列当时已存在且已验证的路径；独立 DHF 仓库或路径尚不存在时，只描述 owner/artifact，不虚构 upstream 路径。最小 exit states 为：

- Phase 0：`contract_frozen`；
- Phase 1S：`consumer_source_green/runtime_not_authorized`；可选 Phase 1D 仅能以 `runtime_verified` 退出；
- Phase 2S：`consumer_source_green/runtime_not_authorized`；可选 Phase 2D 仅能以 `runtime_verified` 退出；
- Phase 3S：`consumer_source_green/runtime_not_authorized`；可选 Phase 3D 仅能以 `runtime_verified` 退出；
- Phase 4：没有第二个 consumer 时 `adapter_deferred`，满足进入条件并形成可验证 immutable artifact 时 `release_ready`。

`S` 是 source-only task，绝不自动触发 `D`；每个 `D` 都是需要新的独立明确授权的 deployment task。精简转换如下，artifact 只以 owner/name 表达：

| Transition | Artifact generation | Entry | Exit |
| --- | --- | --- | --- |
| 1S → 1D | DHF-owned prompt Core + MyCodexEnv-owned prompt wrapper/manifest | 1S source green + deployment 授权 | `runtime_verified` |
| 2S → 2D | DHF-owned evidence Core + MyCodexEnv-owned observer wrapper/manifest | 2S source green + deployment 授权 | `runtime_verified` |
| 3S → 3D | DHF-owned guard Core + MyCodexEnv-owned guard wrapper/scope/targets/manifest + active-policy preservation | 3S source green + deployment 授权 | `runtime_verified` |

每个 `D` entry 必须冻结完整 target generation：本次改变的 wrapper、Core、deployed manifest，以及已部署的上一代完整集合。任何 changed canonical hook/Core 未进入同一 transaction，或任一 non-target 的 source/runtime parity 不为零，立即停止。当前七目标 promotion path 不能原样用于 prompt/evidence 迁移，也不得用 broad sync 绕过 generation transaction。

### Phase 0 — 重冻结抽取合同；不改 runtime

目标：先让抽取合同与当前依赖闭包一致。

允许范围：

- 修订 independent-core requirements 中的 copy/adapt/exclude、Core/adapter/deployment 所有权与 pin 规则；
- 让 bootstrap/release pin prerequisite 和 canonical CI gate 可发现 drift；
- 冻结 prompt、guard、evidence 三组现有输入输出 contract vectors；prompt vectors 至少覆盖 `profile_state=absent`、`valid(active_profile)`、`malformed`、retained higher profile、opt-out 对激活/retention/consumer routing 的优先级，以及 rollout raw value `1`、`0`、`false`、`off`、`legacy`、invalid 的 tagged mapping 与 Core 语义。

停止条件：现有 dedicated prerequisite 不绿、pin 无法可信重建、compatibility 仍以 consumer 级全局豁免接受未知 drift，或需要修改 live runtime。

### Phase 1S — Prompt policy Core；非阻断 source 路径

目标：先抽取 `dhf_preprompt.py` 中的纯 activation/profile/contract 逻辑。

要求：

- upstream Core 成为该逻辑唯一源码；
- MyCodexEnv wrapper 只处理 Codex payload/response、skill text 和 consumer dispatch；
- opt-out、missing/invalid cwd、malformed payload、ShipQ lazy delegation、profile retention 与 diagnostic 行为保持 contract-equivalent；
- 不改 `hooks.json` 的注册命令或顺序；
- 不执行 runtime promotion。

### Phase 2S — Evidence policy Core；best-effort source 路径

目标：抽取 observer 的纯 event builder，保持实际 sink 与 loaded readback 在 MyCodexEnv。

要求：

- command/output 最小化、hash、截断、record 上限与 schema 行为等价；
- `loaded-receipt.json` 的字段、observer wrapper 自身 digest、原子写与 sync readback 语义不变，且不得将其解释为 imported Core 的 loaded identity；
- observer 失败继续 best-effort，不阻断原工具调用；
- 不把本地 evidence、session id、路径或 receipt 发布到 DHF repo。

### Phase 3S — Guard policy Core；最后且高风险的 source 路径

目标：只在独立 security review 通过后抽取 guard 的确定性 policy evaluator。

进入条件：

- policy 缺失/非法的迁移语义已明确并有 fail-close contract；
- Core artifact、adapter、`task_state.py`、`codex-task`、scope、guard targets 与 deployed manifest 的原子安装集合已冻结；
- 当前七目标 WAL、rollback、tool-policy-preservation 与 verifier 已扩展到完整依赖集合；
- protected-root、Skill 读取、mixed targets、transcript/TTL、agent-dispatch receipt 和 legacy block wire 有 adversarial vectors；
- Core import failure、exception、timeout、invalid verdict、unknown reason、serialization failure 和 wire mismatch 均有 fail-close vectors：Adapter 必须使用独立的最小 canonical block fallback，且不得因诊断或编码失败继续工具调用；
- scope、policy 和全部 targets 的完整 parsing status 在同一次 verdict 中覆盖 missing/invalid/partial/unknown，任何一项不可验证都 fail-close；
- source-stage、isolated runtime 和 host-level probe 三类证据互不替代。

禁止先让现有 guard import 一个未纳入同一 promotion transaction 的 Core 文件。

### Phase 4 — 可选 Codex adapter 上游化

只有第二个独立 Codex consumer 需要同一 adapter interface 时才启动。否则 MyCodexEnv wrapper 保持唯一实现，不创建 hypothetical adapter framework。

`session_bearing.py` 只有在 repo helper 具备显式 opt-in、manifest/digest 验证和 bounded execution contract 后才可进入本阶段；不得作为默认全局 adapter 发布。

## 8. 测试与证据所有权

### DHF upstream

- prompt policy contract/golden vectors；
- generic guard category、phase-policy 和 verdict matrix；
- evidence minimization、hash、truncation 和 schema tests；
- release manifest 与 artifact digest checks；
- 不读取真实 `<CODEX_HOME>`、ShipQ、transcript 或 runtime evidence。

### MyCodexEnv

- hook 注册顺序与 Codex wire shape；
- ShipQ lazy delegation/no-leak；
- transcript、TTL、snapshot phase resolution；
- protected roots、scope、integrity watch、loaded readback；
- sync/WAL rollback、runtime parity、host smoke；
- pin comparator 与轻量 contract replay。

MyCodexEnv 不重复运行全部 upstream unit/corpus suite；在 Core interface coverage 已替代旧内部测试后，测试迁移和删除必须作为对应 phase 的明确 write set，不能顺手清理。

每条 material verification receipt 必须包含：

```text
command
exit_code
key_output
timestamp
```

## 9. 每阶段门禁

每个 implementation phase 至少依次通过：

1. upstream focused contract tests；
2. upstream full gate 与 release manifest verification；
3. MyCodexEnv pin comparator；
4. MyCodexEnv focused adapter/integration tests；
5. `python3 test_runner.py`；
6. `python3 scripts/check_surfaces.py --repo-root "$(pwd)"`；
7. `git diff --check`；
8. source/runtime write-set audit。

只有 runtime wiring 在明确授权的独立任务中变更时，才继续：

9. isolated `CODEX_HOME` promotion/rollback；
10. `scripts/verify_codex_env.sh --repo-root "<repo-root>" --codex-home "<isolated-codex-home>" --harness-only`；
11. operator-authorized live promotion；
12. fresh loaded readback 与 attributable host probe。

Source green、pin parity 或磁盘 digest 都不能单独证明 live hook 已加载执行。

## 10. 回退

- Upstream 错误：发布新的修复 release，或由 MyCodexEnv reviewed pin-bump 回到上一 immutable tag；不 retag、不改写历史。
- MyCodexEnv source integration 错误：在未 promotion 时回退 consumer pin/wrapper；不得借此修改 live runtime。
- Runtime 错误：只使用 MyCodexEnv 已验证的完整 generation WAL/rollback，并要求单独 operator 授权；恢复旧 generation 后以其 deployed-manifest digest、release/pin revision、fresh loaded readback 和 attributable host probe 生成 receipt，缺一不得声明 rollback verified。
- Guard Phase 3D 失败：保持或恢复完整旧 guard transaction；禁止只回退 wrapper 或只回退 Core 形成混合代际。
- ShipQ adapter 回退归 ShipQ 自身 task；不由 DHF 或本计划自动修改。

## 11. 停止条件

任一条件成立立即停止当前 phase：

- scope、owner、release revision、artifact digest 或 write set 不明确；
- prerequisite、contract vector、pin comparator 或 canonical gate 不绿；
- upstream 与 MyCodexEnv 出现两个可编辑 source of truth；
- guard 的依赖没有进入同一原子 promotion/rollback 集合；
- 任一 changed canonical hook/Core 未进入完整 generation transaction，或 non-target source/runtime parity 不为零；
- policy 缺失/非法仍可能在切换窗口 fail-open；
- loaded readback 不可用、stale 或 mismatch；
- 需要修改 ShipQ、live runtime、remote repo 或公开 release，但当前任务没有对应授权；
- 同一失败连续两轮没有新证据。

## 12. 验收清单

- [ ] Core、Codex adapter、MyCodexEnv deployment 和 consumer ownership 唯一且无重叠编辑权。
- [ ] `model_router`、compaction、session naming、ShipQ adapter、hooks registration 和 runtime promotion 未进入 DHF Core。
- [ ] `dhf_preprompt` 的通用策略被列为第一批，guard 被列为最后一批。
- [ ] Prompt/guard/evidence Core interface 小且覆盖调用者需要的行为，没有 plugin framework。
- [ ] release manifest、consumer pin、source integration、runtime promotion 和 loaded readback 分离。
- [ ] 每个 Core phase 的 source task 与可选 deployment task 分离；后者有独立授权、完整 generation targets，且未用七目标 path 或 broad sync 绕过。
- [ ] runtime-executed Core 的 deployed-manifest digest、release/pin identity 和 attributable post-promotion probe 构成完整身份链；旧 observer receipt 未被扩大解释。
- [ ] promotion/rollback 均有完整 generation receipt，rollback receipt 绑定恢复后的旧 manifest、旧 revision、fresh readback 和 attributable probe。
- [ ] rollout switch 的 raw value/authority、tag validation 和语义判定分别唯一归属 deployment、Adapter 和 Prompt Core，且现有 switch 未被顺手退役。
- [ ] guard 新依赖不会绕过完整 promotion transaction。
- [ ] observer loaded receipt 与 session bearing 风险有明确进入条件。
- [ ] upstream 与 MyCodexEnv 测试分别覆盖 Core interface 和 adapter/runtime integration，不重复全量 suite。
- [ ] 每阶段有门禁、停止条件和完整代际回退。
- [ ] 每阶段任务开始前冻结精确 write set、deletion set、non-goals、entry/exit state，且未虚构不存在的 upstream 路径。
- [ ] 本计划不构成独立仓库创建、runtime sync、promotion、ShipQ mutation、commit 或 push 授权。

## 13. Known unknowns 与 residual risks

### Known unknowns

- 独立 DHF 仓库、首个 immutable release 和最终 upstream 路径尚不存在。
- Codex host 未来是否提供稳定的 typed hook payload、真实 approval channel 或 loaded-hook identity 未知。
- 是否会出现第二个需要同一 Codex adapter 的独立 consumer 未知；此前不创建 adapter framework。

### Residual risks

- 同 UID runtime tampering 仍是现有 integrity-watch 模型的已知上限。
- Codex host response shape 变化可能使 guard fail-open；需要每次相关 release 的 isolated host probe。
- Source/runtime parity 不证明 host 已执行新 hook；必须保留 loaded readback。
- 多仓 pin-bump 增加协调成本；通过 upstream-first immutable release 和单向 consumer pin 控制，不建立双向同步。
- 历史 simplification corpus 仍绑定 MyCodexEnv 路径/commit/self-hash；它的迁移是后续独立计划，不由本计划顺手处理。
