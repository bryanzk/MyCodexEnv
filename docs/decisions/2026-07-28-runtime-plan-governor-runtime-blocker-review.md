# Runtime Plan Governor：为什么当前不能在 Runtime 实现 Ask 闭环

Status: Claude review complete (PASS_WITH_FINDINGS)，findings 已回写本文  
Decision status: Production NO-GO（维持）  
Evidence refreshed: 2026-07-28（初稿 04:09Z；probe v3 与 runtime 状态更新 20:49Z–2026-07-29T03:21Z）  
Repository: `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv`  
Current Codex runtimes（session_meta 实测，非单值）:  
- CLI `codex-cli 0.144.1`（originator=codex_exec）  
- Desktop `0.146.0-alpha.3.1`（originator=Codex Desktop / codex_work_desktop，本机主力）

## 1. 文档目的

本文为 Claude 独立评审提供完整上下文，回答以下问题：

1. Runtime Plan Governor 想解决什么业务问题？
2. 为什么治理结果需要 `Ask`，而不能统一使用 `Allow` 或 `Deny`？
3. 仓库中已经实现了什么？
4. 为什么这些 source-stage 成果目前仍不能成为真实 runtime 控制？
5. 阻塞来自本项目实现、runtime 未同步，还是 Codex 宿主能力？
6. 什么条件满足后，才可以从 Shadow 进入 Ask，再进入 narrow Enforce？
7. 如果 Codex 继续不支持 `Ask`，有哪些诚实且可落地的替代架构？

本文是问题说明和决策评审材料，不是激活授权。创建本文时没有同步
`~/.codex`、修改全局配置、激活 hook enforcement、提交或推送代码。

## 2. 一句话结论

Runtime Plan Governor 的 source implementation 已经存在，但当前不能宣称
runtime 可运行，因为 Codex `0.144.1` 对
`PreToolUse permissionDecision: "ask"` 的真实语义仍是：

> 字段可以被解析，但不会暂停工具调用；Codex 将 hook 标记为失败、报告错误，
> 然后继续执行原工具调用。

因此，Governor 当前最多可以：

- 冻结范围并生成结构化决策；
- 评估 finding、复杂度预算与 receipt；
- 在 Shadow 模式记录“这里本应 Ask”；
- 对明确禁止的行为使用真正受支持的 `Deny`——注意：Deny 仅在官方 wire shape 下受支持
  （`hookSpecificOutput` 形状、legacy `{"decision":"block"}`、exit 2 + stderr）。
  2026-07-28 隔离 probe 证实旧 guard 的顶层 `{"permissionDecision":"deny"}` 形状同样
  fail-open；guard 已于同日改用 legacy block 形状并完成定向 runtime 同步（见 §23 Receipt H/I）。

它当前不能：

- 把一个原本无需审批的 `spawn_agent` 调用提升为审批请求；
- 在工具执行前暂停；
- 等待用户选择；
- 根据用户选择继续或取消同一个工具调用。

Production 结论必须保持 **NO-GO**。把失败后继续执行称为 Ask，或者把所有
Ask 改成 Deny，都不是 Runtime Plan Governor 的可运行实现。

## 3. 业务问题：Governor 为什么存在

复杂计划和多轮 committee review 容易出现一种治理失败：

1. 用户已经给出明确的 v1 范围；
2. reviewer 提出新的风险或理想化架构；
3. speculative finding 被当成已证实要求；
4. 每一轮都加入新服务、状态机、信任根或运维角色；
5. 计划不断扩大，但没有一个明确的责任人决定是否接受范围变化；
6. 最终交付成本、时间和风险都偏离用户原始目标。

Runtime Plan Governor v1 的目标不是替用户判断产品方向，也不是禁止所有复杂度。
它的目标是在一个可观察的工具边界上发现：

- 当前 dispatch 是否绑定到已冻结的范围；
- finding 是否具备足够证据；
- 是否发生 scope rebase；
- 是否超过 complexity budget；
- 是否出现重复不收敛；
- 是否需要责任人明确选择。

Governor 输出的关键动作并不只有“允许”和“阻止”，还必须有“请业务责任人
决定”。这个第三种动作就是 `Ask`。

## 4. 业务语言 5 Why：为什么必须调用 Ask

### Why 1：为什么发现风险后需要 Ask？

因为系统已经发现风险，但仅凭自动规则无法确定这次范围变化是否符合用户的
真实业务意图。最终取舍涉及交付日期、成本、风险偏好和责任归属，需要用户或
指定责任人决定。

### Why 2：为什么不能自动 Allow？

自动 Allow 会让未确认的范围扩张、弱证据架构和高成本操作继续发生。Governor
就只剩审计记录，无法在风险发生前形成控制。

### Why 3：为什么不能统一 Deny？

被标记的操作不一定错误。用户可能愿意接受新增复杂度，也可能已经掌握 hook
看不到的业务信息。统一 Deny 会把“需要授权”误判为“绝对禁止”，阻断正常
工作，并诱发绕过治理。

### Why 4：为什么必须在工具执行前询问？

因为执行后告警不能撤销已经发生的副作用。对于 dispatch 而言，子任务一旦
启动，计算、上下文传播和后续写入就可能已经发生。Ask 必须实现：

`识别风险 -> 暂停原调用 -> 展示原因 -> 用户选择 -> 恢复或取消原调用`

### Why 5：为什么这对业务治理重要？

因为有效治理要同时满足效率与责任：

- 低风险、范围内的工作自动流转；
- 明确禁止的行为确定性阻断；
- 有合理争议的高风险变化由责任人确认；
- 决策与对应的范围、计划、finding 和轮次可追溯。

因此：

- `Allow` 是系统代替用户承担风险；
- `Deny` 是系统代替用户否决业务；
- `Ask` 是系统识别风险、保留用户决策权。

## 5. 预期的 Runtime 状态机

完整 Ask 闭环需要宿主提供以下状态机：

```text
pending tool call
       |
       v
PreToolUse receives trusted payload
       |
       v
Governor evaluates frozen scope + receipt + budget
       |
       +------------------ safe -----------------> execute
       |
       +---------------- forbidden --------------> deny
       |
       +---------------- decision required ------> suspend
                                                       |
                                                       v
                                                show approval UI
                                                       |
                                  +--------------------+--------------------+
                                  |                                         |
                               approve                                    reject
                                  |                                         |
                                  v                                         v
                        resume same tool call                       cancel tool call
                                  |
                                  v
                         persist decision receipt
```

这里的关键不是 JSON 中出现 `"ask"` 字符串，而是宿主必须具备：

1. 挂起 pending tool call；
2. 创建与该调用关联的 approval request；
3. 将原因展示给用户；
4. 保存用户选择；
5. 对同一个调用执行 resume 或 cancel；
6. 让 hook/runtime 获得可审计结果。

当前 Codex 的 `PreToolUse` 并未为 `ask` 实现这条状态机。

## 6. 当前真实行为

Codex 官方 Hooks 文档对 `PreToolUse` 的说明是：

- `permissionDecision: "deny"`：阻止受支持的工具调用；
- `permissionDecision: "allow"` + `updatedInput`：允许并重写受支持调用；
- `permissionDecision: "ask"`：**parsed but not supported yet**；
- 返回 unsupported 字段时：hook 被标记为失败、错误被报告、工具调用继续。

这构成以下真实状态转换：

```text
pending tool call
       |
       v
PreToolUse returns permissionDecision: "ask"
       |
       v
hook result validation fails
       |
       v
error is reported
       |
       v
original tool call continues
```

这不是“Ask 的降级模式”，而是 **fail-open**。

官方依据：

- [OpenAI Codex Hooks — PreToolUse](https://learn.chatgpt.com/docs/hooks#pretooluse)
- [OpenAI Codex Hooks — Tool coverage](https://learn.chatgpt.com/docs/hooks#tool-coverage)
- [OpenAI Codex Hooks — PermissionRequest](https://learn.chatgpt.com/docs/hooks#permissionrequest)
- [OpenAI Codex source tag rust-v0.144.1](https://github.com/openai/codex/tree/rust-v0.144.1)

源码级与本机行为级补强（2026-07-28 Claude review + probe v3）：

- 源码四 tag（rust-v0.144.1 / 0.145.0 / 0.146.0-alpha.3.1 / 0.146.0-alpha.9）中
  `output_parser.rs` 对 Ask 一律返回 "unsupported permissionDecision:ask"；
  `PreToolUseHookResult` 枚举仅有 `Continue`/`Blocked`，宿主类型系统无挂起状态；
  hook timeout 与 crash 同样落入 Failed → 继续执行。
- Tool coverage 关键事实：`spawn_agent` 的 matcher 别名为 `Agent`；`write_stdin`
  不会对已通过 PreToolUse 的 unified-exec 会话重新触发 hook；官方原文
  "Some specialized tool paths can opt out of the default hook path. Treat tool
  hooks as a useful guardrail, not a complete enforcement boundary."
- 本机隔离 probe（CLI 0.144.1，14 轮，执行计数判据）：S2 嵌套 deny、S3 legacy block、
  S4 exit-2 均真实拦截（executed_delta=0）；S1 顶层 permissionDecision 形状与
  S5/S6 两种 ask 形状均 fail-open（hook 触发但命令照常执行）。

## 7. “解析但不支持”具体是什么意思

“解析”只说明：

- JSON shape 能被反序列化；
- enum 或 schema 认识 `"ask"` 这个值；
- hook output 不会因为未知 JSON token 在最外层直接崩溃。

“支持”则要求：

- runtime validator 接受该动作；
- permission subsystem 创建 approval request；
- agent loop 暂停；
- UI 或调用方可以接收并回复；
- reply 与原 tool call 相关联；
- runtime 根据回复继续或取消；
- timeout、session end、compaction 和并发调用都有确定语义。

当前实现只有前一组，没有后一组。因此“schema 接受”不能推导为“runtime
可执行”。

## 8. 为什么 PermissionRequest 不能补上这个缺口

Codex 还有一个 `PermissionRequest` hook，但它与 `PreToolUse Ask` 不是同一个
控制阶段。

官方文档说明：

- `PermissionRequest` 只在 **Codex 本来就准备发起审批** 时运行；
- 它可以 allow、deny，或不做决定，让原审批 UI 继续；
- 对本来不需要审批的调用，它不会运行。

因此，不能使用下面这条推理：

```text
PreToolUse sees risky spawn_agent
  -> return allow
  -> PermissionRequest will ask user later
```

如果 `spawn_agent` 在当前 permission policy 下本来无需审批，
`PermissionRequest` 根本不会触发。`PreToolUse` 也没有一个受支持的动作将
该调用“升级”为 permission request。

换句话说：

- `PreToolUse` 可以在调用前看见并阻断部分工具；
- `PermissionRequest` 可以处理已经存在的审批；
- 当前缺少的是“把 Governor 的 decision-required 结果转换为一个新的审批”。

## 9. 为什么 Deny 不能冒充 Ask

用 `Deny` 代替 `Ask` 在技术上可能阻止工具，但会改变业务合同：

| 业务语义 | 用户是否能继续 | 责任主体 | 适用场景 |
|---|---:|---|---|
| Allow | 是 | 系统自动决定 | 明确安全且范围内 |
| Ask | 用户决定 | 用户/责任人 | 风险真实但存在合理取舍 |
| Deny | 否 | 政策预先决定 | 明确禁止、无例外 |

如果将所有 decision-required 情况改成 Deny：

- 用户无法在当前调用中明确批准；
- 合法的范围调整被错误阻断；
- 团队会通过关 hook、改 matcher 或绕过 dispatch 来继续工作；
- receipt 记录的是“政策拒绝”，不是“用户选择”；
- 产品从 human-in-the-loop governor 变成硬编码 deny list。

只有本来就属于不可协商红线的情况，才能使用 Deny。Deny 是一个有效控制，
但不是 Ask 的实现。

## 10. 为什么 fail-open 不能称为可运行

如果 Governor 返回 Ask，而宿主继续执行：

1. 用户没有看到真正的选择界面；
2. 用户没有作出批准；
3. 工具调用已经发生；
4. receipt 无法证明授权；
5. 后续观察只能记录“本应询问”；
6. 治理控制没有改变业务执行路径。

这最多是 Shadow observation。把它称为 runtime active 会产生更高风险：
使用者会误以为高风险 dispatch 已被拦截，实际却仍会执行。

## 11. 当前仓库已经实现了什么

PR #12 已将 Governor 的 source-stage 资产合并到仓库，当前 HEAD 为：

`6b28e549131d8e092e3661c5ea391faae1ffbc92`

主要 source-of-truth 包括：

- [`scripts/plan_governor.py`](../../scripts/plan_governor.py)
  - `freeze`
  - `evaluate-round`
  - `status`
  - `verify-receipt`
- [`plan-scope-envelope.schema.json`](../../codex/runtime/evidence/plan-scope-envelope.schema.json)
- [`plan-finding-decision.schema.json`](../../codex/runtime/evidence/plan-finding-decision.schema.json)
- [`plan-governor-receipt.schema.json`](../../codex/runtime/evidence/plan-governor-receipt.schema.json)
- [`codex/runtime/tool-policy.json`](../../codex/runtime/tool-policy.json)
- [`codex/skills/planner/SKILL.md`](../../codex/skills/planner/SKILL.md)
- [`codex/skills/committee-review-loop/SKILL.md`](../../codex/skills/committee-review-loop/SKILL.md)
- [`docs/plans/2026-07-26-runtime-plan-governor-v1.md`](../plans/2026-07-26-runtime-plan-governor-v1.md)
- [`test_runner.py`](../../test_runner.py)

Source policy 明确写着：

```json
{
  "plan_governor": {
    "version": 1,
    "payload_capable": false,
    "mode": "shadow",
    "production_status": "no_go",
    "reason": "dispatch command is observable but PreToolUse permissionDecision ask is unsupported and fails open"
  }
}
```

这个配置不是未完成标记，而是正确的能力门禁：只要 Ask 不能强制暂停，
`payload_capable` 就不得设置为 `true`。

## 12. Source-stage 能力与 Runtime 控制的区别

当前已经具备的能力：

- 对 ScopeEnvelope、FindingDecision、Receipt 做结构化校验；
- 将 receipt 绑定到 session、repo、scope、plan、finding set 和 round；
- 识别 speculative evidence；
- 识别复杂度预算超限；
- 区分 terminal 与 non-terminal disposition；
- 保留 `MANUAL_CONTROL`、`ACCEPTED_RISK`、`DEFERRED`、
  `UNSUPPORTED` 等合法结果；
- 在 Shadow 分支中不覆盖已有安全决策；
- 通过 skill 引导 planner 和 committee 使用 Governor 合同。

这些能力证明的是“决策逻辑可以运行”，不是“宿主会执行 Ask”。

缺失的 runtime 控制能力：

- 在 `PreToolUse` 中将 decision-required 结果转成真实 approval；
- 挂起并恢复同一个 `spawn_agent` 调用；
- 获取语义明确的用户审批 receipt；
- 在 Ask unsupported 时 fail closed 到“等待用户”，而不是 fail open；
- 覆盖所有可能绕过受支持 local function tool path 的 dispatch 路径。

## 13. 当前 Runtime 同步状态

状态经历了三个时间点（本节按最后一次刷新为准）：

1. **2026-07-28T04:09Z 快照（本文初稿）**：`~/.codex/runtime/tool-policy.json` 无
   `plan_governor` 段、缺三份 Governor schema、`planner` 与 `committee-review-loop`
   skill 存在 drift。
2. **2026-07-28T13:00:49Z**：定向 sync 完成。plan_governor 段、三份 schema、两个 skill
   与 source 全部 hash 一致（Claude review 只读复核，见 Receipt G）。
3. **2026-07-29T03:21:38Z**：guard wire-shape 修复后，`harness_guard.py` 单文件定向
   同步并行为验证，source/runtime hash 一致（72d33879…，旧文件留 .bak，见 Receipt I）。

当前生命周期状态：

| 里程碑 | 当前值 | 含义 |
|---|---:|---|
| `source_implemented` | true | 仓库中有 CLI、schema、skills、policy 合同和测试 |
| `runtime_synced` | true | Governor 资产集（policy/schema/skills/guard/hooks.json）已 parity；全面 parity 以 verify_codex_env.sh 为准 |
| `rollout_observed` | false | 尚无本次真实 runtime rollout 的有效样本 |
| `runtime_active` | false | 没有 Ask/Enforce 闭环 |
| Production | NO-GO | 不得声称生产治理已生效 |

sync 完成后状态如预测：

```text
source_implemented=true
runtime_synced=true
rollout_observed=false
runtime_active=false
mode=shadow
production_status=no_go
```

Runtime sync 可以解决文件漂移，不能实现宿主缺失的 Ask 状态机——该论断已被同日事实
验证：sync 前后，probe 证实 ask 的 fail-open 行为完全不变。

## 14. 为什么不能“在 hook 脚本里自己等待用户输入”

一个看似可行的方案是：PreToolUse hook 判断需要 Ask 后，自己读取终端输入。
该方案不应作为默认生产架构，原因包括：

- hook 不拥有 Codex UI 的 approval surface；
- Desktop、CLI、IDE、非交互模式的 stdin/TTY 语义不同；
- 多个匹配 hook 可能并发启动；
- 阻塞 hook 可能超时，超时后的 fail behavior 必须明确；
- 无法可靠绑定 UI 回答与原始 `tool_use_id`；
- compaction、session cancellation 和 app restart 会留下悬挂状态；
- hook 读取 stdin 可能与 Codex 自身输入争用；
- 无法复用宿主已有的 permission policy、approval history 和审计模型。

如果未来引入独立 broker，它必须被当成新的产品与信任边界，而不能伪装成
几行 hook 脚本。

## 15. 当前正确运行模式：Shadow

在宿主 Ask 不可用时，Shadow 是唯一不会虚报能力的默认模式。

Shadow 可以：

- 运行相同的 Governor 判定；
- 记录 `would_allow`、`would_ask`、`would_deny`；
- 采集误报、漏报、finding 类别与复杂度漂移；
- 验证 payload 中是否有稳定的 tool name、args、session、turn、cwd；
- 不改变真实工具执行结果；
- 不覆盖其他现有安全 hook 的 Deny。

Shadow 不可以被描述为：

- approval enabled；
- enforcement enabled；
- user confirmed；
- production protected；
- runtime active。

## 16. 解锁 Runtime Ask 的最低能力条件

只有新的 Codex 版本或新的受支持接口同时满足以下条件，才可重新评估：

1. `spawn_agent` 等目标 dispatch 稳定触发 `PreToolUse`；
2. payload 含稳定且可信的：
   - `session_id`
   - `turn_id`
   - `tool_use_id`
   - `cwd`
   - `tool_name`
   - 完整 tool input；
3. `permissionDecision: "ask"` 被官方支持；
4. 返回 Ask 后，工具在用户回答前不执行；
5. 用户批准后只执行一次原调用；
6. 用户拒绝后原调用不执行；
7. timeout、hook crash、session cancel 和 UI unavailable 的行为明确；
8. Ask 的 fail behavior 满足既定安全合同；
9. approval reason 可被用户看到；
10. approval 结果可与原 scope/receipt/tool call 绑定。

任何一项缺失，都不能进入 Ask rollout。

## 17. Phase 0 Capability Probe

Phase 0 是 kill gate，不是上线演练。

### 隔离要求

- 使用临时 `CODEX_HOME` 或等价的隔离 config root；
- 使用临时 Git repo；
- hook 只写临时 evidence directory；
- 使用无业务价值、无外部副作用的 probe tool；
- 不读取或修改真实 `~/.codex`；
- 不使用真实项目凭据；
- 不触发外部业务系统；
- probe 结束后只保留脱敏回执；
- **显式处理 hook trust**：未 trust 的 hook 会被 Codex 静默跳过（2026-07-28 v2 probe
  实测假阴性），隔离环境须使用 `--dangerously-bypass-hook-trust`（仅作用于该次调用，
  且临时 home 中只含 probe 自己的 hook）或等价的显式 trust 步骤；
- 临时 `CODEX_HOME` 需只读复制 `auth.json`，否则内层调用 401，模型不运行、hook 不触发
  （v1 probe 实测假阴性）。

### Probe cases

1. **Payload probe**
   - 验证目标工具是否触发 `PreToolUse`；
   - 验证 tool name、input、session、turn、tool-use binding。
2. **Allow probe**
   - 返回 Allow；
   - 证明工具恰好执行一次。
3. **Deny probe**
   - 返回 Deny；
   - 证明工具零次执行。
4. **Ask-approve probe**
   - 返回 Ask；
   - 在批准前验证零次执行；
   - 批准后验证恰好一次执行。
5. **Ask-reject probe**
   - 返回 Ask；
   - 拒绝后验证零次执行。
6. **Failure probe**
   - hook crash、invalid output、timeout；
   - 记录每种情况是 fail-open 还是 fail-closed。
7. **Concurrency probe**
   - 两个并发 pending call；
   - 证明回答不会串到错误 tool call。
8. **Wire-shape conformance probe**（2026-07-28 已对 CLI 0.144.1 完成，14 轮）
   - 同一 deny/ask 语义分别以顶层形状、hookSpecificOutput 形状、legacy block、
     exit-2+stderr 输出；
   - 判据只认执行计数；结论：S2/S3/S4 拦截，顶层形状与一切 ask 形状 fail-open。
9. **Matcher alias probe**
   - 分别以 `spawn_agent` 与 `Agent` 作 matcher，记录 payload 实际 tool_name。
10. **write_stdin 旁路 probe**
    - 确认已通过 PreToolUse 的 unified-exec 会话追加输入不再触发 hook，列入旁路清单。
11. **Subagent 绑定 probe**
    - 从 subagent 发起目标调用，验证 payload session_id 为 parent id 时
      receipt binding 是否错绑。
12. **Per-frontend 矩阵**
    - CLI 与 Desktop 各自完整执行以上 cases；结论不得跨 frontend 迁移。
      当前 Desktop 0.146.0-alpha.3.1 线尚未行为验证（not_covered，源码 schema 与
      0.144.1 一致）。

### Pass condition

Ask-approve 与 Ask-reject 两条路径均满足预期，并且没有未绑定、重复执行或
提前执行。只证明字段被解析、UI 出现警告、或 hook 输出包含 `"ask"`，均不算
通过。

### Fail condition

以下任意一个出现即为 Phase 0 fail：

- Ask 被报告为 unsupported；
- Ask 后工具继续执行；
- approval UI 不出现；
- 回答不能绑定到原调用；
- approve 导致重复执行；
- reject 后仍执行；
- 目标 dispatch 不触发 hook；
- 关键 payload 字段不稳定或不可验证。

### 回滚

Phase 0 使用隔离环境，不需要修改真实 runtime。失败后：

- 删除或弃用临时 config root；
- 保持 source `payload_capable=false`；
- 保持 `mode=shadow`；
- 保持 `production_status=no_go`；
- 不运行 runtime sync 或 activation。

## 18. 通过 Phase 0 后的条件式 rollout

本节不是当前执行授权。只有 Phase 0 通过才适用。

### Stage 1：Shadow

入口：

- runtime source/parity gate 通过；
- Governor 仍不改变 dispatch；
- 对目标 plan/review dispatch 记录 would-decision。

建议样本：

- 至少 50 个目标 dispatch；
- 至少覆盖 10 个真实 planning/review task；
- 至少包含 10 个 `would_ask`；
- 连续观察不少于 5 个工作日。

指标：

- payload completeness；
- scope/receipt binding success rate；
- would-ask rate；
- reviewer-confirmed false-positive rate；
- missed-decision rate；
- hook latency p50/p95；
- hook failure rate；
- 对其他安全决策的覆盖/冲突次数。

停止条件：

- payload binding failure > 0；
- hook failure > 1%；
- p95 延迟超过团队接受阈值；
- 覆盖已有 Deny；
- 发现可绕过的主要 dispatch 路径；
- reviewer-confirmed false positive > 5%。

### Stage 2：Ask

入口：

- Phase 0 通过；
- Shadow 样本达标；
- 业务 owner、runtime owner、安全 reviewer 共同确认；
- Ask 仅覆盖目标 planning/review dispatch。

建议样本：

- 先执行 20 个真实 Ask；
- 至少覆盖 approve 和 reject 各 5 个；
- 每个结果都核对 tool execution count；
- 连续 3 个工作日无提前执行、错绑或重复执行。

硬停止条件：

- 任意一次 Ask 前工具已执行；
- 任意一次 reject 后仍执行；
- 任意一次 approve 重复执行；
- 任意 approval 绑定错误；
- Ask unsupported 或降级 fail-open；
- 用户无法理解 prompt 与后果；
- 现有安全 Deny 被弱化。

回滚：

- 将 Governor mode 恢复为 Shadow；
- 不移除原有 Deny；
- 保留脱敏 evidence；
- 将 incident 标记为 rollout failure，而不是普通误报。

### Stage 3：Narrow Enforce

入口：

- Ask 样本全部满足执行一致性；
- false-positive rate <= 2%；
- false-negative review 未发现可重复的高风险漏判；
- runtime owner 与业务 owner 签字确认；
- rollback 已演练。

范围：

- 只覆盖明确的 planning/review dispatch；
- 只对 receipt 缺失、binding mismatch、scope rebase、complexity breach 等
  已定义 predicate 生效；
- 不扩展到所有工具、所有文本输出或所有仓库。

验收：

- Allow、Ask、Deny 三条路径可区分；
- Ask 是真实暂停，而不是错误后继续；
- receipt 与 decision、scope、tool call 可追溯；
- Shadow、Ask、Enforce 可单独切换；
- rollback 不依赖改代码或紧急发布。

## 19. 如果 Ask 继续不受支持：正确结论与架构选择

### 选择 A：保持 Shadow + 人工流程

Governor 生成结构化结果和 `would_ask` evidence，由 planner 在 dispatch 前通过
正常对话向用户提问。用户明确回答后，再发起新的 dispatch。

优点：

- 不伪造 runtime enforcement；
- 无新服务和新信任根；
- 与现有 source 资产兼容。

限制：

- 属于 workflow/skill soft gate；
- 无法阻止模型绕过流程直接调用工具；
- `runtime_active` 必须保持 false。

### 选择 B：两步式显式 dispatch

不尝试暂停已有调用，而是重新设计入口：

1. `prepare-dispatch` 只生成不可变 proposal/receipt；
2. 用户通过独立受支持入口批准；
3. `execute-dispatch` 必须携带有效 approval token。

优点：

- 避免“暂停并恢复同一调用”的宿主要求；
- approval 成为执行前置条件；
- 可以 fail closed。

成本：

- 改变调用协议和用户体验；
- 需要新的 approval token 生命周期；
- 需要确保所有 dispatch 都只能走新入口；
- 超出 Governor v1 当前最小 source scope，需要重新评审。

### 选择 C：独立 approval broker

建立本地 broker/UI 管理 pending operation、用户选择和一次性 token，实际工具
只接受 broker 签发的批准。

优点：

- 可实现真正的人机决策闭环；
- 不依赖 `PreToolUse Ask`。

成本和风险：

- 新 daemon、状态机、UI、IPC 和信任边界；
- crash recovery、并发、超时、身份绑定和审计复杂；
- 明显超过 v1 的复杂度 ceiling；
- 必须作为新产品立项，不能作为小型 hook 修补。

### 选择 D：只使用硬 Deny

仅对不可协商红线使用 Codex 已支持的 Deny。

优点：

- 当前宿主可强制执行；
- 行为简单、可测试。

限制：

- 不解决需要业务选择的 finding；
- 不能称为 Ask；
- 不构成完整 Runtime Plan Governor。

### 当前推荐

在 Codex Ask 仍 unsupported 时：

1. Governor 保持 Shadow；
2. 明确红线继续使用独立 Deny（2026-07-28 起 guard 已改用 probe 证实可拦截的
   legacy block 形状；原 ask 三类因任何形状均 fail-open 已升级为 block）；
3. 需要业务判断的事项通过正常对话显式确认；
4. 若必须要硬 runtime human-in-the-loop，单独评审“两步式显式 dispatch”，
   不在 v1 中偷偷引入 broker。

## 20. 不能接受的伪实现

Claude review 应明确拒绝以下说法或实现：

- “JSON 能解析 `ask`，所以 Ask 已支持”；
- “hook 报错后工具继续，是 Ask 的兼容降级”；
- “把 Ask 全部改成 Deny，功能等价”；
- “先 Allow，后面的 PermissionRequest 会自动询问”；
- “source tests 通过，所以 runtime active”；
- “runtime 文件同步完成，所以 enforcement 生效”；
- “出现 approval 风格文案，所以工具被暂停”；
- “PostToolUse 可以在执行后撤销副作用”；
- “skill 要求用户确认，因此构成硬 runtime gate”；
- “Shadow 记录了 would_ask，因此用户已经授权”。

## 21. 生命周期声明标准

后续所有交付必须分别报告：

### `source_implemented`

只表示仓库中已有代码、schema、配置合同、skills 和测试。

### `runtime_synced`

只表示预期 source 资产已同步到目标 `CODEX_HOME`，且 parity 验证通过。

### `rollout_observed`

只表示在真实目标 runtime 中采集了满足样本要求的行为证据。

### `runtime_active`

只表示目标控制在真实 runtime 中改变了执行路径，并通过允许、拒绝、询问和
回滚验收。

四者不可互相替代。尤其：

```text
source_implemented != runtime_synced
runtime_synced != rollout_observed
rollout_observed != runtime_active
```

在 `payload_capable=false` 时，`runtime_active=true` 是逻辑上不允许的声明。

## 22. Claude 评审请求

请 Claude 独立判断，不沿用本文结论作为默认前提。建议逐项回答：

1. 本文是否正确区分了“输出字段可解析”和“runtime 支持该语义”？
2. 官方文档是否足以证明 Codex `0.144.1` 的 Ask 为 fail-open？
3. `PermissionRequest` 是否存在一种本文遗漏的、可把普通 `spawn_agent`
   提升为审批请求的官方路径？
4. 是否存在受支持的 Codex API，可暂停并恢复同一个 local function tool call？
5. 两步式显式 dispatch 是否能在不引入 daemon 的前提下提供 fail-closed
   human-in-the-loop？
6. Phase 0 的 pass/fail 条件能否排除“UI 看起来像 Ask、工具实际已执行”的
   假阳性？
7. Shadow、Ask、narrow Enforce 的样本量和停止阈值是否足够保守？
8. 当前 `payload_capable=false`、`mode=shadow`、Production NO-GO 是否为
   唯一诚实结论？
9. 是否还有其他绕过点、并发风险、receipt binding 风险或 rollback 风险？
10. 如果建议替代架构，请明确它改变了哪些 source-of-truth、runtime surface、
    信任边界和 Definition of Done。

Claude 的 review 结论建议使用：

- `PASS`：现状判断与门禁完整；
- `PASS_WITH_FINDINGS`：结论成立，但需补充非阻塞问题；
- `BLOCKED`：缺少关键证据，不能判断；
- `REJECT`：存在可运行的官方 Ask 路径，或本文核心推理错误。

任何 `REJECT` 都应给出可复现的官方接口、最小 probe 和预期执行次数证据，
而不是仅引用 schema 类型或其他产品的 hook 行为。

## 23. Fresh Evidence Receipts

### Receipt A：Repository anchor 与 source revision

```text
command:
  git rev-parse --show-toplevel
  git log -1 --format='%H %cI %s'
exit_code: 0
key_output:
  /Users/kezheng/Codes/CursorDeveloper/MyCodexEnv
  6b28e549131d8e092e3661c5ea391faae1ffbc92
  feat: publish plan governor and environment docs (#12)
timestamp: 2026-07-28T04:09:23Z
```

### Receipt B：Current Codex capability surface

```text
command:
  codex --version
  codex features list | rg '^hooks\\s'
exit_code: 0
key_output:
  codex-cli 0.144.1
  hooks stable true
timestamp: 2026-07-28T04:09:23Z
note: 仅覆盖 CLI 线。session_meta 显示本机另有 Desktop 0.146.0-alpha.3.1 主力线
  （Receipt J）；后续 receipts 须按 frontend 分别记录。
```

注意：`hooks stable=true` 只证明 hooks feature 已启用，不证明每个 output action
都已实现。

### Receipt C：Source policy boundary

```text
command:
  sed -n '1,20p' codex/runtime/tool-policy.json
exit_code: 0
key_output:
  payload_capable=false
  mode=shadow
  production_status=no_go
  reason=PreToolUse permissionDecision ask is unsupported and fails open
timestamp: 2026-07-28T04:09:23Z
```

### Receipt D：Runtime policy drift

```text
command:
  inspect ~/.codex/runtime/tool-policy.json and compare plan_governor section
exit_code: 0
key_output:
  source contains plan_governor
  runtime contains no plan_governor section
timestamp: 2026-07-28T04:09:23Z
superseded_by: Receipt G（13:00:49Z 后 runtime 已含 plan_governor 且与 source 一致）
```

### Receipt E：Runtime artifact parity

```text
command:
  compare SHA-256 for source/runtime guard, skills, and Governor schemas
exit_code: 0
key_output:
  harness_guard.py: parity
  runtime plan-scope-envelope.schema.json: missing
  runtime plan-finding-decision.schema.json: missing
  runtime plan-governor-receipt.schema.json: missing
  runtime planner skill: drift
  runtime committee-review-loop skill: drift
timestamp: 2026-07-28T04:09:23Z
superseded_by: Receipt G（13:00:49Z 后 schema 与 skill 全部 parity）与 Receipt I（guard 新 hash）
```

### Receipt F：Official Ask semantics

```text
source:
  OpenAI Codex Hooks documentation, PreToolUse section
key_output:
  permissionDecision:"ask" is parsed but not supported yet;
  Codex marks the hook run as failed, reports the error,
  and continues the tool call
observed_at: 2026-07-28
```

### Receipt F2：Official PermissionRequest boundary

```text
source:
  OpenAI Codex Hooks documentation, PermissionRequest section
key_output:
  PermissionRequest runs when Codex is about to ask for approval;
  it does not run for commands that do not need approval
observed_at: 2026-07-28
```

### Receipt G：Runtime sync completed（取代 Receipt D/E 的 drift 结论）

```text
command:
  sha256 对比 source/runtime 的 tool-policy plan_governor 段、三份 Governor schema、
  planner 与 committee-review-loop skill 目录、hooks.json
exit_code: 0
key_output:
  plan_governor: parity（payload_capable=false / mode=shadow / no_go）
  三份 schema hash 逐一相同（ca3127fa… / 08aaa1cf… / 8a37b1b0…）
  两个 skill 目录 diff -rq 无差异；hooks.json parity
  上述文件 mtime = 2026-07-28T13:00:49Z
timestamp: 2026-07-28T17:53:57Z（Claude review 只读复核）
```

### Receipt H：Wire-shape probe v3（CLI 0.144.1，隔离 CODEX_HOME，14 轮）

```text
command: /tmp/deny_wire_shape_probe_v3.sh
exit_code: 0
key_output:
  判据 = 执行计数（executions.log），非 UI 文案；每轮 hook_delta=1（hook 均触发）
  S0 控制组：executed_delta=1 ×2（计数器可信）
  S1 顶层 {"permissionDecision":"deny"}：executed_delta=1 ×2 → fail-open（旧 guard 形状）
  S2 hookSpecificOutput deny：executed_delta=0 ×2 → 拦截
  S3 legacy {"decision":"block"}：executed_delta=0 ×2 → 拦截
  S4 exit 2 + stderr：executed_delta=0 ×2 → 拦截
  S5/S6 ask（两种形状）：executed_delta=1 ×4 → fail-open（复证 Ask 不构成 runtime 闭环）
  方法论：v1 败于隔离 home 无 auth.json（401 假阴性）；v2 败于未 trust hook 被静默跳过
timestamp: 2026-07-28T20:49:32Z–20:52:10Z
coverage: 仅 CLI 0.144.1；Desktop 0.146.0-alpha.3.1 not_covered
```

### Receipt I：Guard wire-shape 修复与定向 runtime 同步

```text
command:
  修改 codex/hooks/harness_guard.py（全部决策改 legacy block 形状；原 ask 三类升级 block）
  更新 test_runner.py 17 处断言；python3 test_runner.py
  备份 → 定向复制 → sha256 比对 → runtime 副本行为验证
exit_code: 0
key_output:
  test_runner: ran=91 passed=86 skipped=5 failed=0
  source/runtime harness_guard.py hash 一致 = 72d33879…
  旧文件备份 = ~/.codex/hooks/harness_guard.py.bak.20260729032138（hash 47d8da05…）
  runtime 行为：dynamic_exec → {"decision":"block",…}；无 receipt spawn_agent →
  {"decision":"block",…}；安全读取 → {}
timestamp: 2026-07-29T03:21:38Z
```

### Receipt J：本机双 runtime 版本证据

```text
command: 遍历 ~/.codex/sessions/2026/07/24–28 session_meta 的 originator 与 cli_version
exit_code: 0
key_output:
  codex_exec → 0.144.1（每日 1 会话）
  Codex Desktop / codex_work_desktop → 0.146.0-alpha.3.1（每日 5–56 会话，主力）
  ~/.codex/version.json: latest_version=0.145.0（checked 2026-07-25）
timestamp: 2026-07-28T17:4xZ
```

## 24. 当前最终决策

```text
source_implemented = true
runtime_synced = true   # Governor 资产集 parity（Receipt G/I）；全面 parity 以 verify_codex_env.sh 为准
rollout_observed = false
runtime_active = false
payload_capable = false
mode = shadow
production_status = no_go
```

当前不能在 runtime 实现完整 Governor，不是因为 finding evaluator、schema 或
CLI 不存在，而是因为 Governor 所需的第三种业务决策 `Ask` 缺少宿主级
“暂停—询问—恢复/取消”执行语义。该结论已在 2026-07-28 由源码（四 tag）与本机
隔离 probe（Receipt H）双重证实；同日发现并修复了 guard 自身的 wire-shape
fail-open（Receipt I），Deny 兜底自此真实生效（CLI 线已行为验证）。

下一条安全任务不是激活 Governor，而是按序：

> 1. 在真机运行 `python3 test_runner.py` 复核 live-guard smoke 与 parity 合同；
> 2. Desktop 0.146.0-alpha.3.1 线在可隔离 `CODEX_HOME` 时补做 wire-shape probe
>    （§17 case 8/12），在此之前 Desktop 结论仅有源码级证据；
> 3. 当出现声称支持 `PreToolUse permissionDecision: "ask"` 的新 Codex 版本时，
>    在隔离 `CODEX_HOME` 中执行完整 Phase 0 capability probe（含 hook trust 与
>    auth 处理，见 §17 隔离要求）；只有 probe 证明 Ask 在批准前零执行、批准后
>    恰好一次执行、拒绝后零执行，才允许规划 Ask rollout。
