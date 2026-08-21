# MyCodexEnv Harness Runtime 能力验证最小修复计划

## 直接答案

当前最值得做的最小修复，不是修改 Codex runtime，而是让 MyCodexEnv 准确回答四个问题：

1. 请求实际走了哪条工具路径；
2. Hook 是否被观察到，以及返回了什么；
3. Sandbox 是否真正参与并阻断了写入；
4. 结论是否来自当前环境中的 fresh、可关联、可校验 receipt。

目标是消除：

```text
Hook 已注册
→ Hook 已执行
→ 写入已被阻止
→ Sandbox 已验证
```

这条未经证据支持的推断链。

最小方案保留现有 Hook 策略、公开 JSON 和 `test_runner.py --host-only` 入口。不解析 `functions.exec` JavaScript，不 fork Codex，不新增依赖，也不默认向 `~/.codex` 写持久状态。

---

## 一、冻结合同：先定义语义，再写实现

T1 必须先冻结以下合同，后续任务不得自行改变含义：

- capability/status schema；
- probe state machine；
- receipt schema；
- freshness 与环境匹配规则；
- gate profile；
- exit-code matrix；
- legacy JSON compatibility。

### 1. 状态集合

所有 capability 结论只能是：

```text
PASS
FAIL
UNSUPPORTED
UNVERIFIED
```

定义如下：

| 状态 | 严格定义 |
|---|---|
| `PASS` | 指定路径已由匹配协议的 fresh probe 实际执行，所有必需断言成立 |
| `FAIL` | probe 已实际执行，但必需断言失败，或发生了不应发生的写入 |
| `UNSUPPORTED` | capability detection 明确证明当前 Host/runtime 不提供该能力 |
| `UNVERIFIED` | 没有执行、Host driver 不可用、receipt 缺失/过期/外来、结果无法归因，或证据不足 |

以下情况不得标为 `UNSUPPORTED`：

- 没有 Host driver；
- 没有运行 probe；
- 超时；
- receipt 缺失；
- Hook 没有日志；
- 子进程或工具调用失败；
- Sandbox 拒绝了操作；
- 仅根据版本号猜测不支持。

这些情况默认都是 `UNVERIFIED`，除非 capability detection 返回明确、可记录的不支持结论。

### 2. 四层事实不得合并

```text
registered
≠
route_observed
≠
hook_result
≠
sandbox_result
≠
verified capability
```

`config.toml`、`hooks.json`、Hook 日志或一次 deny 都不能单独证明完整 enforcement。

### 3. Sandbox 语义

Managed sandbox 是架构指定的 authoritative security boundary，但其当前路径状态只有在主动 probe 和 fresh receipt 支持时才可标为 `PASS`。

因此必须区分：

```json
{
  "authoritative_boundary": {
    "type": "managed_sandbox",
    "designation": "authoritative",
    "status": "UNVERIFIED"
  }
}
```

不得因为配置中存在 `sandbox_mode`，或 Hook 返回 `DENY`，直接输出：

```json
"status": "PASS"
```

如果 Hook 先拒绝、请求未到达 sandbox，则：

```text
sandbox_result=NOT_REACHED
sandbox capability=UNVERIFIED
```

### 4. 观测量来源合同

可观测性是**观测量与 route 的组合**属性，不是观测量的整体属性：同一个观测量可能在 DENY 路径有权威生产者、在 ALLOW 路径没有。每个组合只允许一个权威生产者；某个组合没有生产者时，该观测量在该 route 上恒为 `not_observable`，对应 capability 若依赖它则为 `UNVERIFIED`，且该观测量不得出现在该 route 的任何 PASS 条件中。

| 观测量 | 唯一权威来源 | 可观测性 |
|---|---|---|
| `route_observed` | `harness_observer.py`（PostToolUse）写入的 evidence JSONL 记录，按 `session_id` + `tool_name` + `command_sha256_prefix` 匹配本次 probe | 条件可观测。该 hook 的 `command_sha256_prefix` 只覆盖落在 `command` / `cmd` 键上的文本；若本次 patch 落在 `tool_input.patch` 上而无法匹配，记 `route_observed=false`，对应 capability 记 `UNVERIFIED` |
| `hook_observed`（PreToolUse） | driver 观测到的工具结果中出现 `harness_guard.block()` 产生的 `[harness] ` 前缀 reason | **仅 DENY 路径可观测。** PreToolUse 放行时返回空对象且不产生任何记录，因此 ALLOW control 的 `hook_observed` 恒为 `not_observable` |
| `sandbox_result` | driver 观测到的 sandbox 拒绝信号 | 未触达时记 `NOT_REACHED` |

两条约束由此固定：

- `harness_guard.py` 不写日志、不落盘，其 stdout 不构成独立的 `hook_observed` 证据；`harness_observer.py` 只挂在 PostToolUse，能证明工具调用被观测，不能证明 PreToolUse 是否执行。
- `harness_guard.block()` 产生的 `[harness] ` reason 前缀是本计划**被依赖的观测契约**。T1 冻结时必须一并记录当时的 reason 形状与 `guard_digest`；该前缀若在未来变化而合同未同步，`hook_observed` 会静默变为 `false`，所有 DENY probe 随之降级为 `UNVERIFIED`，而不是悄悄通过。
- 所有 probe 必须串行执行，禁止并发。`block()` 的 reason 不含目标路径，并发时无法把一次 deny 归因到某一次 invocation。

---

## 二、实施范围

预期最小修改面：

```text
scripts/harness_status_runtime.py
test_runner.py
现有测试位置
docs/agents/verification-and-change-safety.md
```

以下文档仅在对应公共合同或导航实际变化时更新：

```text
docs/HARNESS_RUNTIME.md
docs/repo-index.md
docs/CODEX_ENV_REPRODUCTION.md
```

条件如下：

- capability、receipt 或 gate 合同变化：更新 `docs/HARNESS_RUNTIME.md`；
- 新增或改变公开命令/runtime surface：更新 `docs/repo-index.md`；
- bootstrap、安装或环境复现步骤变化：更新 `docs/CODEX_ENV_REPRODUCTION.md`。

原则上不修改：

```text
codex/hooks/harness_guard.py
~/.codex/hooks.json
~/.codex/hooks/harness_guard.py
Codex App/runtime
```

只有 probe 证明 `harness_guard.py` 本身存在缺陷后，才另行提出最小修复；本计划不预先授权该修改。

---

## 三、Host driver feasibility gate

真实 E2E 的第一依赖不是 probe 代码，而是一个能够从 Codex Host 发起真实工具调用并返回结构化结果的 Host driver。

在任何 E2E 实现之前，先回答：

```text
能否由自动化入口真实触发：
1. direct apply_patch
2. functions.exec → tools.apply_patch
3. 对应 Hook 观测
4. 对应 sandbox 结果
```

### Feasibility gate 必须确认

- driver 的实际入口和协议；
- direct 与 nested route 是否都可发起；
- 是否能为一次执行绑定唯一 `correlation_id`；
- 是否能取得 route、Hook、sandbox 和 mutation 结果；
- 是否可使用隔离的临时目标；
- 是否需要人工操作、App 会话或额外授权；
- capability detection 如何明确表示“不支持”。

### Gate 结果

| 结果 | 后续动作 |
|---|---|
| Host driver 可用 | 进入 E2E probe 实现 |
| driver 明确报告某 route 不支持 | 对该 capability 记录 `UNSUPPORTED` |
| driver 缺失或无法自动控制 | 记录 `UNVERIFIED`，停止伪 E2E |
| 需要权限或 Host 外执行 | 停止并请求明确授权 |

Python 子进程调用、mock、直接调用 Guard 函数或解析静态配置只能算 unit/config checks，不能代替 Host E2E。

---

## 四、最小 probe protocol

每条受保护 probe 都必须有一个同 route、同工具协议的正常 `ALLOW` control。这样才能区分：

```text
工具链根本不能工作
```

与：

```text
保护策略正确拒绝了目标
```

每次 probe 必须分别记录：

```text
route_observed
hook_result
sandbox_result
target_pre_state
target_post_state
```

不得压缩为单个 `denied=true`。

`target_pre_state` / `target_post_state` 必须用 `os.lstat` 采集，不得用 `os.path.exists`：悬空符号链接会让 `exists()` 返回 `False`，从而把一次真实的受保护写入误判为未发生。每次采集必须记录目标自身的 `exists`、`mode_type`、`dev`、`ino`、`nlink`、`digest`，以及父目录的 `dev`、`ino` 与其条目名集合排序后的 digest。条目名集合必须排除 `__pycache__`：hook 运行会随时创建或改写该目录，否则会产生假阳性 mutation。父目录身份或（排除后的）条目集合在 pre 与 post 之间发生变化，即视为 mutation。

窗口内“创建后又被删除”的瞬时 mutation 不在本协议的检测能力内。这是已知盲区，必须在 receipt 中以 `transient_mutation_detection: "out_of_scope"` 显式标注；不得由 pre 与 post 相等推断窗口内未发生任何写入。

### Probe A：Direct ALLOW control

路径：

```text
Host driver
→ direct apply_patch
→ 唯一临时目录中的普通目标
```

要求：

- 使用随机或 correlation-bound 临时目录；
- `hook_observed == not_observable`（见 §一.4：PreToolUse 放行不产生任何可观测信号）；
- `raw_result == {}`，保留 Host/Hook 的原始空结果，不伪造 `ALLOW` 字段。该空对象同时是 `harness_guard.decision()` 无法解析 payload 时的返回值，因此它是必要不充分证据，不单独证明 Guard 评估过本次调用；
- ALLOW control 的 payload 形状必须同时满足两个可观测性前提：(a) 让 Guard 能够解析成功——单一 patch 源、单一路径键，不得同时提供内容冲突的 `patch` 与 `command`；(b) 让 `route_observed` 可匹配——patch 必须落在 `command` / `cmd` 键上，因为 `harness_observer.py` 的 `command_sha256_prefix` 只覆盖这两个键。若 Host wire 只能把 patch 放在 `tool_input.patch` 上，则该 route 的 ALLOW control 记 `UNVERIFIED`（`reason=route_not_observable`），不得改为 `PASS`，也不得据此把对应的 DENY probe 判为可信；
- 写入实际发生；
- 内容 digest 与预期一致；
- probe 后清理临时目录；
- 不接触 repo 文件和用户数据；
- 不得为了制造 `ALLOW` 字段或改变 control 输出而修改 `harness_guard.py`。

只有以下全部成立才是 `PASS`：

```text
route_observed
AND raw_result == {}
AND mutation == expected
AND post_digest == expected_digest
```

ALLOW control 只证明“工具链可用且该 route 可达”，不证明“Hook 在链上”。后者只能由同 route 的 DENY probe 证明。

### Probe B：Direct protected mutation

路径：

```text
Host driver
→ direct apply_patch
→ 不存在的受保护 sentinel
```

建议目标：

```text
~/.codex/hooks/__harness_direct_probe_<correlation_id>__
```

要求：

```text
pre.exists == false
post.exists == false
route_observed == true
hook_observed == true
hook_result == DENY
sandbox_result 已记录
```

Hook enforcement 只有这些条件全部成立才是 `PASS`。此处的 `hook_observed == true` 按 §一.4 由 driver 观测到的 `[harness] ` 前缀 reason 提供，这是 PreToolUse 唯一可观测的正向信号。`sandbox_result` 即使为 `NOT_REACHED` 也必须记录，不得省略。

如果 Hook 拒绝导致请求未到达 sandbox：

```text
sandbox_result=NOT_REACHED
```

不得同时宣称 sandbox 已被验证。

### Probe C：Nested ALLOW control

路径：

```text
Host driver
→ functions.exec
→ tools.apply_patch
→ 唯一临时目录中的普通目标
```

要求与 Probe A 相同，并额外证明 nested route 的 correlation 可贯通；同样要求：

```text
hook_observed == not_observable
raw_result == {}
```

不得修改 Guard 来制造显式 `ALLOW` 返回值。本 probe 验证的 capability 是 `nested_route_reachable`，不是 `nested_hook_enforcement`；`hook_observed` 不进入它的 PASS 条件。

### Probe D：Nested protected mutation

路径：

```text
Host driver
→ functions.exec
→ tools.apply_patch
→ 不存在的受保护 sentinel
```

建议目标：

```text
~/.codex/hooks/__harness_nested_probe_<correlation_id>__
```

结果必须按实际证据分类：

- Hook 明确观察并拒绝，目标未变化：nested Hook enforcement `PASS`；
- capability detection 明确报告 nested Hook 不受支持：nested Hook enforcement `UNSUPPORTED`；
- Hook 未观察，但 sandbox 明确阻断且目标未变化：
  - nested Hook enforcement `UNVERIFIED`，除非 detection 明确证明不支持；
  - managed sandbox 对该 nested route 为 `PASS`；
- 请求完成并产生受保护写入：`FAIL`；
- driver、日志或 correlation 不足：`UNVERIFIED`。

### Sandbox 独立验证

Sandbox 只能在请求实际到达 sandbox 且阻断可归因时标为 `PASS`。

不得关闭 Hook、削弱策略或绕过 Guard 来制造测试路径。若现有安全链无法在不降低保护的情况下独立触达 sandbox，则保留：

```text
managed_sandbox.status=UNVERIFIED
```

而不是构造危险的旁路测试。

---

## 五、Receipt 合同

### 默认输出位置

默认只输出到 stdout。只有调用方显式提供 `--receipt-out` 时才允许创建 receipt artifact：

```text
--receipt-out <caller-owned-path>
```

`--receipt-out` 必须满足以下全部条件：

- 路径由 caller 明确给出，不使用隐式默认路径；
- 目标位于非 protected、非 runtime 区域；
- 目标是不存在的新文件；
- 拒绝 symlink 目标；
- 拒绝已有目标，包括普通文件、目录和特殊文件；
- 先以 `open(parent, O_RDONLY|O_DIRECTORY|O_NOFOLLOW)` 取得父目录 fd，再用 `openat(dirfd, leaf, O_CREAT|O_EXCL|O_WRONLY|O_NOFOLLOW, 0o600)` 创建。不得使用“先按路径检查父链、再按路径创建”的两步式：检查与创建是分离的系统调用，父目录可在两者之间被换成 symlink，而 `O_EXCL` 只保护最后一段；
- readback 必须在保留的 fd 上做（`fstat` + `pread`），不得按路径重新 `open`。重开会再走一遍同一条可被替换的路径，可能验证到另一个文件；
- readback 验证 bytes、schema 和 `artifact_digest`；
- 任一检查失败时非零退出，不写部分或替代目标；
- 创建成功之后的任何失败（序列化、写入、fsync、readback）必须用 `unlinkat(dirfd, leaf)` 删除本次刚创建的文件，且仅在其 inode 与本次创建的 inode 一致时才删除。否则残留的零字节或截断 receipt 会与上面“拒绝已有目标”一条共同作用，使同路径重试永久失败，只能人工介入。

默认不得创建：

```text
~/.codex/state/harness-capabilities.json
```

如未来确需 runtime cache，必须单独获得对准确路径、生命周期、清理策略和隐私边界的授权。

### 最小 receipt 字段

```json
{
  "schema_version": 1,
  "probe_id": "uuid",
  "correlation_id": "uuid",
  "gate_profile": "host-only",
  "capability": "nested_protected_mutation",
  "status": "PASS",
  "started_at": "2026-08-20T18:35:40Z",
  "finished_at": "2026-08-20T18:35:41Z",
  "expires_at": "2026-08-20T19:35:41Z",
  "driver": {
    "name": "actual-host-driver",
    "version": "..."
  },
  "environment": {
    "codex_runtime": "...",
    "codex_app_build": "...",
    "os": "...",
    "sandbox_profile": "...",
    "hooks_digest": "sha256:...",
    "guard_digest": "sha256:...",
    "policy_digest": "sha256:...",
    "host_session_id": "...",
    "probe_pid": 0
  },
  "route_observed": {
    "route": "functions.exec->tools.apply_patch",
    "observed": true,
    "reason": null
  },
  "hook_result": {
    "observed": "true | false | not_observable",
    "status": "DENY",
    "reason": "[harness] active_control_plane_mutation",
    "correlation_id": "uuid"
  },
  "sandbox_result": {
    "status": "NOT_REACHED",
    "reason": "hook denied before sandbox"
  },
  "target": {
    "path_class": "protected_missing_sentinel",
    "transient_mutation_detection": "out_of_scope",
    "pre": {
      "exists": false,
      "mode_type": null,
      "dev": null,
      "ino": null,
      "nlink": null,
      "digest": null,
      "parent": { "dev": 0, "ino": 0, "entries_digest": "sha256:..." }
    },
    "post": {
      "exists": false,
      "mode_type": null,
      "dev": null,
      "ino": null,
      "nlink": null,
      "digest": null,
      "parent": { "dev": 0, "ino": 0, "entries_digest": "sha256:..." }
    }
  },
  "artifact_digest": "sha256:..."
}
```

`hook_result.observed` 承载 §一.4 的 `hook_observed`：DENY 路径取 `true` / `false`，ALLOW control 恒为 `not_observable`。`route_observed.reason` 在 `observed=false` 时必须给出原因（例如 `route_not_observable`），`observed=true` 时为 `null`。`target.*.parent.entries_digest` 是排除 `__pycache__` 后的条目名集合排序 digest。

`hooks_digest` / `guard_digest` / `policy_digest` 必须逐文件、按字节计算，并显式排除 `__pycache__`（`~/.codex/hooks/` 实际含该目录，对目录整体取 digest 不稳定）。若改为复用仓库既有的 `runtime-approvals/approved-source-digests.txt` 约定，必须在合同中写明复用哪一条，不得两套并存。

`expires_at` 的 TTL 上限固定为 1 小时；消费端必须同时校验 `finished_at <= expires_at <= finished_at + 1h`，防止生产者自选远期过期时间。时钟偏移不在处理范围内——系统时钟被视为可信，这一点必须出现在 receipt 消费失败的报错文本中。

`host_session_id` 取自 `harness_observer.py` 记录的 `session_id`（其来源为 payload `session_id` 或 `CODEX_SESSION_ID`）。它与 `probe_pid` 一起，把 receipt 绑定到具体的 Host session 与 probe invocation；仅靠 environment fingerprint 无法区分同机不同 session 的 receipt。

实际 schema 可以更紧凑，但不得删除：

- freshness；
- environment fingerprint；
- relevant source/config digests；
- probe/correlation identity；
- route observation；
- Hook result；
- sandbox result；
- pre/post mutation evidence；
- 每个观测量在本 route 上的可观测性状态；
- Host session 与 probe invocation 绑定；
- receipt/artifact digest。

### `artifact_digest` 规范

`artifact_digest` 必须定义为以下表达式的 SHA-256：

```python
json.dumps(
    receipt_without_artifact_digest,
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")
```

即：

```text
artifact_digest = SHA-256(canonical JSON of receipt excluding artifact_digest)
```

计算时先移除顶层 `artifact_digest` 字段，再对上述 canonical bytes 计算 SHA-256；校验端必须执行完全相同的步骤。不得对包含 `artifact_digest` 自身的 JSON 计算 digest，也不得依赖缩进、键插入顺序、平台默认编码或非标准 NaN/Infinity 值。

### 信任边界

`artifact_digest` 只是完整性校验，不是来源认证。它无密钥、无签名，且由写 receipt 的同一个工具计算；任何能在本机写文件的主体都能重算出一个合法值，而同机的 `hooks_digest`、`guard_digest`、`policy_digest`、`codex_app_build`、`os`、`sandbox_profile` 天然全部匹配，因此 environment fingerprint 无法识别同机伪造。

由此确定消费边界：

```text
只有本次运行经 stdin 管道直接传入的 receipt，才可用于产出 PASS / FAIL / UNSUPPORTED。
任何从文件路径读入的 receipt 一律封顶 UNVERIFIED，
reason=file_sourced_receipt_not_authenticated。
```

管道本身不提供认证：消费端无法区分上游是真的 probe 还是 `cat forged.json |`。因此信任锚不是管道，而是**调用方编排**——`test_runner.py` 在同一次调用中先运行 probe、再把它的 stdout 直接喂给消费端，中间不落盘、不经用户输入。任何在该编排之外手工构造的输入都不在保护范围内，这一点必须写进合同，否则“只信管道”本身就成为新的 false assurance。

`--receipt-out` 写出的 artifact 是给人和外部工具看的留档，不是本流程的可信输入。同机伪造不在本计划的威胁模型内，也不被 digest 机制覆盖；不得在任何输出中暗示 digest 校验通过等于来源可信。

回归 fixture 至少包含：

- canonical receipt digest 匹配；
- 同一对象仅改变格式或键顺序时 digest 不变；
- 含非 ASCII `reason` 与 `path` 的 receipt 可按 UTF-8 稳定计算并验证；
- 非 ASCII `reason` 或 `path` 中任一字段被单字段篡改时 digest mismatch，并拒绝 receipt；
- NaN 或 Infinity 输入因 `allow_nan=False` 被拒绝。

### Freshness 与 stale-receipt rejection

以下条件是消费 receipt 的必要条件，且只适用于经 stdin 管道传入的 receipt（见上文“信任边界”）。文件来源的 receipt 无论是否满足这些条件，都封顶 `UNVERIFIED`。

Receipt 只有同时满足以下条件才可消费：

```text
schema valid
AND artifact digest valid
AND current time <= expires_at
AND current Host/runtime fingerprint matches
AND hooks/guard/policy digests match
AND expected gate_profile matches
AND expected route/capability matches
AND correlation fields are internally consistent
```

任一条件不满足：

```text
status=UNVERIFIED
reason=stale_or_mismatched_receipt
```

不得沿用历史 green、不同 App build、不同 Hook、不同 sandbox profile 或不同 probe protocol 的 receipt。

---

## 六、Runtime status 集成与兼容性

`scripts/harness_status_runtime.py --json` 当前的：

```text
config
hooks
runtime
```

是公开 JSON surface。修复不得静默删除、改名或改变旧字段的数据类型。

最小兼容策略：

1. 保留现有 `config`、`hooks`、`runtime`；
2. 将旧字段明确解释为 config/registration observation；
3. 新增版本化的 `capabilities`、`evidence` 和 `overall`；
4. 为 legacy unified consumer 增加回归 fixture；
5. `scripts/harness_env_probe.py` 等现有 wrapper 必须继续工作；
6. `scripts/harness_status_runtime.py` 的 `main()` 退出码语义冻结为 `0` = 成功产出 probe 输出、`1` = 无法产出。§七 的 `2` / `3` 只属于 focused capability command，不得出现在本脚本或其任何 wrapper 上；
7. 受该退出码语义保护的调用面必须逐一加回归 fixture：`scripts/harness_env_probe.py`（DHF governed escalation contract 的强制 helper，且被 `docs/dhf-consumer-compatibility.json` 的 `helpers` 列为跨消费者契约）与 `scripts/harness_status.py status --runtime`（`docs/repo-index.md` 承诺其保留既有 env-probe JSON 契约）。两者都直接透传 `main()` 的返回值，退出码一旦改变会在正常机器上把 governed 路由打成非零；
8. `harness_status_runtime.render_markdown()` 是默认（无 `--json`）的人类输出面。本节后文的词汇要求作用于它，因此它同样需要兼容性 fixture，不得只保护 JSON 面。

### Receipt 输入通道

`scripts/harness_status_runtime.py` 当前只接受 `--codex-home` 与 `--json`，只读 CODEX_HOME 下的静态文件，没有任何 receipt 入口。本计划为它增加且只增加一个参数：

```text
--receipt-in -
```

规则：

- 只接受 `-`（stdin 管道）。本进程从不自行搜索 receipt，也不接受 receipt 文件路径（见 §五“信任边界”）；
- 未提供 `--receipt-in` 时，`capabilities.*` 一律输出 `UNVERIFIED`，并附 `reason: no_receipt_supplied`。这是正常状态，不改变退出码；
- `capabilities.<name>.receipt` 字段的值定义为该 receipt 的 `artifact_digest` 字符串，既不是路径，也不是内联对象；
- `scripts/harness_env_probe.py` 通过 `from harness_status_runtime import *` 自动继承该参数，这是可接受的。但 wrapper 在**不传任何新参数**时的行为必须逐字节不变——这正是 DHF governed escalation contract 调用它的方式，也是第 7 条兼容性 fixture 要锁住的形状。

示例：

```json
{
  "config": {
    "sandbox_mode": "workspace-write",
    "approval_policy": "...",
    "observable": true
  },
  "hooks": {
    "enabled": true,
    "pre_tool_use": true
  },
  "runtime": {
    "policy_phases_present": true
  },
  "capability_schema_version": 1,
  "capabilities": {
    "direct_hook_enforcement": {
      "status": "PASS",
      "receipt": "..."
    },
    "nested_hook_enforcement": {
      "status": "UNSUPPORTED",
      "receipt": "..."
    },
    "managed_sandbox": {
      "status": "UNVERIFIED",
      "receipt": null
    }
  },
  "authoritative_boundary": {
    "type": "managed_sandbox",
    "designation": "authoritative",
    "status": "UNVERIFIED"
  },
  "overall": {
    "hook_enforcement": "PARTIAL",
    "security_boundary": "UNVERIFIED"
  }
}
```

其中旧字段：

```json
"hooks": {
  "enabled": true,
  "pre_tool_use": true
}
```

只能表示配置与 registration observation，不表示 capability `PASS`。

Human-readable 输出也必须使用：

```text
registered
configured
observed
verified
unverified
unsupported
```

不得继续使用含义不明的：

```text
enabled → protected
looks okay
mostly working
```

---

## 七、Gate profiles 与 exit matrix

不新增一个与现有入口竞争的顶级测试入口。Capability probe 接入现有：

```bash
python3 test_runner.py
python3 test_runner.py --host-only
```

### Profile 定义

| Profile | 用途 |
|---|---|
| default | 仓库完整 gate；缺少 Host capability 时允许明确 skip，但不得生成 E2E PASS |
| `--host-only` | 在真实 Host 环境执行 required host gates、Host driver feasibility、probe/receipt 验证；不得静默 skip |

`--require-security-boundary` 是可与上述任一 profile 组合的**修饰参数**，不是第三个 profile。它唯一的作用是把 `managed_sandbox` 从 optional 升级为 required；不传时 `managed_sandbox` 为 `UNVERIFIED` 不影响退出码。

Focused probe/helper 若存在，只作为 `test_runner.py` 调用的内部或诊断入口，不取代公开 gate。

### Capability policy

| Capability | Profile 要求 |
|---|---|
| Hook registration/config parsing | required，必须 `PASS` |
| Guard policy unit | required，必须 `PASS` |
| Direct ALLOW control | required，必须 `PASS` |
| Direct protected deny | required，必须 `PASS` |
| `nested_route_reachable`（nested ALLOW control） | required when driver declares nested route available；PASS 条件不含 `hook_observed` |
| `nested_hook_enforcement`（nested PreToolUse 在链上） | optional upstream capability；允许明确 `UNSUPPORTED` |
| `managed_sandbox`（sandbox protected boundary） | conditional-required：默认 optional，允许 `UNVERIFIED` 且不影响退出码；仅当调用方传入 `--require-security-boundary` 时升级为 required |

`nested_route_reachable` 与 `nested_hook_enforcement` 必须是两个独立 capability。nested route 本身可达（code-mode 工具链能工作）与 nested PreToolUse 是否在链上，是两件不同的事。合并它们会让“nested 可达但 PreToolUse 缺席”这一已观测状态无法表达，并使 `--host-only` 恒为 exit `1`——一个恒红的 gate 会被放宽或绕过，那正是本计划要消除的失败模式。

### Exit matrix

Focused capability command如需暴露状态，使用：

| Capability result | Exit code |
|---|---:|
| `PASS` | `0` |
| `FAIL` | `1` |
| `UNVERIFIED` | `2` |
| `UNSUPPORTED` | `3` |

### 进程分层与 exit code 映射

三个进程各自的退出码语义互不覆盖，必须分开读：

| 进程 | 退出码语义 |
|---|---|
| `scripts/harness_status_runtime.py`（及其 wrapper） | 只有 `0` = 成功产出输出、`1` = 无法产出。capability 结论只体现在 payload 字段里；`capabilities.*` 全为 `UNVERIFIED` 是正常状态，仍然 exit `0` |
| focused capability command | 使用上表的 `0/1/2/3` |
| `test_runner.py --host-only` | 只有 `0` / `1`，由下面的聚合规则决定 |

包裹 focused command 的测试函数必须按下表转换，不得让原始退出码直接冒泡：

| focused exit | required capability | optional upstream capability |
|---|---|---|
| `0`（PASS） | 通过 | 通过 |
| `1`（FAIL） | `require()` 失败 | `require()` 失败 |
| `2`（UNVERIFIED） | `require()` 失败 | `require()` 失败 |
| `3`（UNSUPPORTED） | `require()` 失败 | 打印 `[UNSUPPORTED] <capability>` 后正常返回；**不得抛 `SkipTest`**，否则会被 `--host-only` 的 `require_no_skips` 判为 required skip 而 exit `1` |

`--require-security-boundary` 是 `test_runner.py` 的参数，不是 focused command 的参数；它只改变 `managed_sandbox` 在下面聚合规则中的 required/optional 归属。

上表是**实现手段**（测试函数如何转换 focused command 的退出码），下面的聚合规则是**结果契约**（`--host-only` 最终给出什么）。两者必须一致；冲突时以聚合规则为准，并修正映射表。

`test_runner.py --host-only` 聚合规则：

- required capability 出现 `FAIL`、`UNVERIFIED` 或 `UNSUPPORTED`：exit `1`；
- optional upstream capability 为明确 `UNSUPPORTED`，且其补偿控制满足 profile 要求：可以保持 overall exit `0`，但必须打印 `UNSUPPORTED`；
- `managed_sandbox` 为 `UNVERIFIED` 且未传 `--require-security-boundary`：overall exit `0`，但 `overall.security_boundary` 必须打印 `UNVERIFIED`；
- 任何 stale、digest mismatch、environment mismatch 或 correlation mismatch receipt：exit `1`；
- 文件来源的 receipt 一律封顶 `UNVERIFIED`；若它属于 required capability，按上面第一条 exit `1`；
- `UNSUPPORTED` 不得由普通 skip、异常或超时产生；
- `UNVERIFIED` 不得被聚合成 `PASS`。

示例：

```text
Harness Runtime Compatibility

[PASS] hook registration
[PASS] direct protocol-matched ALLOW control
[PASS] direct protected mutation denied
[PASS] direct protected target unchanged
[PASS] nested_route_reachable (protocol-matched ALLOW control)
[UNSUPPORTED] nested_hook_enforcement (nested PreToolUse)
[PASS] managed sandbox blocked nested protected mutation
[PASS] receipt freshness and environment match

HOOK_ENFORCEMENT=PARTIAL
SECURITY_BOUNDARY=VERIFIED
```

如果 sandbox 没有被实际触达：

```text
[UNVERIFIED] managed sandbox boundary
SECURITY_BOUNDARY=UNVERIFIED
```

---

## 八、任务顺序

| Task | 内容 | 依赖 | 风险 |
|---|---|---|---:|
| T1 | 冻结 schema、状态、receipt、freshness、profile、exit matrix 和 compatibility 合同 | 无 | 中 |
| T2 | Host driver feasibility gate | T1 | 高 |
| T3 | 保留 legacy JSON，修正 status 语义并加入 capability/evidence 层 | T1 | 中 |
| T4 | Direct ALLOW + protected E2E probes | T2 | 高 |
| T5 | Nested ALLOW + protected E2E probes | T2 | 高 |
| T6 | 生成 stdout/显式临时 receipt，并验证 digest、freshness、environment、correlation | T4、T5 | 中 |
| T7 | 将 receipt 消费接入 runtime status | T3、T6 | 中 |
| T8 | 接入现有 `--host-only` profile 与 exit matrix；新增的 required capability probe 必须同时登记进 `test_runner.py` 的 `TESTS` 与 `HOST_INTEGRATION_TESTS` | T6 | 中 |
| T9 | 按实际 surface 变化条件更新文档 | T3、T8 | 低 |
| T10 | focused gate、完整 repo gate、必要时 Host gate | 全部 | 中 |

T2 若不能证明 Host driver 可用，T4–T8 中依赖真实 E2E 的部分停止为 `UNVERIFIED`；不得用 mock 补成 PASS。此时本计划的实际交付面收缩为仅 T3 与 T9。**启动 T1 之前必须先确认：在该情形下是否仍值得为一份不会执行的 E2E 合同支付冻结成本。**

T8 的两条硬性要求：

- `select_registered_tests(host_only=True)` 只返回 `HOST_INTEGRATION_TESTS`。probe 若只加进 `TESTS`，`--host-only` 会完全不执行它并输出 exit `0`——即在本计划要消除 false assurance 的那条命令上制造一次新的。
- 现有的 `test_runner_host_only_profile_contract` 把选中集合与 `HOST_INTEGRATION_TESTS` 自身相比，属同义反复，拦不住上一条。T8 必须把它改为对显式名字白名单的断言。

---

## 九、明确排除

本次不做：

- 不修改 Codex App/runtime；
- 不 fork `openai/codex`；
- 不 cherry-pick upstream patch；
- 不解析 `functions.exec` JavaScript；
- 不用 regex 推断 nested operation；
- 不给每个项目复制 Hook；
- 不新增第三方依赖；
- 不新增抽象 driver framework；
- 不默认写 `~/.codex/state`；
- 不把配置、注册或 Hook deny 推断成 sandbox verified；
- 不把 driver 缺失、超时或普通失败标为 `UNSUPPORTED`；
- 不把 unsupported capability mock 成 `PASS`；
- 不为追求全绿绕过 Guard 或降低 sandbox；
- 不修改范围外文档和 runtime state。

---

## 十、风险分级与控制

### 高风险

真实 Host E2E 会尝试访问受保护 runtime sentinel。

控制：

- 只使用不存在且带唯一 correlation ID 的目标；
- probe 前后都验证目标不存在；
- 禁止使用现有文件；
- 禁止覆盖、删除或恢复用户数据；
- 所有正常 ALLOW control 只在独立临时目录中执行；
- 运行前需要准确 Host/runtime 写范围授权；
- 任一意外 mutation 立即 `FAIL` 并停止后续 probe；
- 意外 mutation 的残留按以下合同处理：`harness_guard.decision()` 对 control plane 内的 delete 同样返回 block，因此 `~/.codex/hooks/` 下的 probe 残留**无法通过受控工具删除**。probe 必须打印精确残留路径、声明“只能由 owner 带外删除”，并把该残留登记为后续 gate 的显式 blocker，避免它静默污染 `sync_codex_home.sh` 的 parity/drift 检查。

### 中风险

公开 JSON、receipt schema、`test_runner.py --host-only` 属于共享接口。

控制：

- 保留 legacy 字段和类型；
- 增加 compatibility fixture；
- schema 版本化；
- stale / environment mismatch receipt fail closed，文件来源 receipt 封顶 `UNVERIFIED`；
- 不新增竞争入口。

### 低风险

文档同步。

控制：

- 只更新实际受影响的合同和索引；
- 不重复全局规则；
- 不把计划描述成已实现事实。

---

## 十一、完成定义

只有以下条件全部满足，才能宣称本次修复完成：

1. capability/status、receipt、freshness、profile 和 exit matrix 已冻结；
2. 现有公开 JSON 字段和 legacy unified consumer 兼容；
3. `registered` 不再被解释成 `enforced` 或 `verified`；
4. Host driver feasibility 有明确结果；
5. direct route 有 protocol-matched `ALLOW` control；
6. direct protected mutation 有 fresh、可关联的 deny + unchanged receipt；
7. `nested_route_reachable` 已实际探测；`nested_hook_enforcement` 已实际探测，或由明确 capability detection 标为 `UNSUPPORTED`；
8. 每条 probe 分别记录 route、Hook、sandbox、pre 和 post，且 pre/post 用 `os.lstat` 采集并含父目录身份；瞬时 mutation 的检测盲区已显式标注；
9. sandbox 只有在请求实际到达并被阻断时才标为 `PASS`；
10. stale、digest mismatch、environment mismatch 和 correlation mismatch receipt 均被拒绝；文件来源的 receipt 一律封顶 `UNVERIFIED`（同机伪造不在威胁模型内，见 §五“信任边界”）；
11. receipt 默认只走 stdout；显式 `--receipt-out` 以 `openat` + `O_CREAT|O_EXCL|O_NOFOLLOW` 写入 caller 指定的非 protected、非 runtime 新文件，readback 在保留 fd 上完成，创建后的任何失败都以 `unlinkat` 清除本次残留；
12. `artifact_digest` 使用排除自身字段后的 UTF-8 canonical JSON SHA-256，固定 `ensure_ascii=False`、`allow_nan=False`、`sort_keys=True`、紧凑 separators，且非 ASCII 单字段篡改 fixture 被拒绝；
13. 没有未经授权写入 `~/.codex/state`；
14. 正常 control 保留 Host 原始 `{}` 结果且不修改 Guard 制造 `ALLOW`，同时明确记录 `hook_observed=not_observable`，未把 `{}` 当作 Guard 已评估本次调用的证据；
15. 正常 control 只写隔离临时目录并完成清理；
16. `--host-only` 遵守 required/optional capability 和 exit matrix；
17. docs 只按真实 public surface 变化更新，但 `docs/agents/verification-and-change-safety.md` 中枚举两个 host gate 并写明“both tests must pass with zero skips”的表述属事实错误修正，必须随 `HOST_INTEGRATION_TESTS` 扩展一并改为不枚举个数的写法，不受本条限制；
18. 每个观测量都有 §一.4 指定的权威生产者，没有生产者的观测量未出现在任何 PASS 条件中，且全部 probe 串行执行；
19. `harness_status_runtime.py` 的退出码语义未变，`harness_env_probe.py` 与 `harness_status.py status --runtime` 的回归 fixture 已就位；三个进程的退出码分层与 focused-exit 映射表已实现，`UNSUPPORTED` 未经由 `SkipTest` 表达；
20. 未修改 Codex runtime，未新增 repo-specific Hook dependency；
21. 最终验证附 fresh `command`、`exit_code`、`key_output` 和 `timestamp`。

最终状态示例必须与证据一致：

```text
GLOBAL HOOK
registered: yes

DIRECT HOOK ENFORCEMENT
status: PASS

NESTED HOOK ENFORCEMENT
status: UNSUPPORTED
basis: explicit capability detection

AUTHORITATIVE SECURITY BOUNDARY
type: managed sandbox
status: PASS
basis: fresh route-matched blocking receipt

OVERALL
hook enforcement: PARTIAL
security boundary: VERIFIED
false assurance: removed
```

如果缺少 sandbox 主动证据，则必须诚实输出：

```text
security boundary: UNVERIFIED
```

而不是 `VERIFIED`。
