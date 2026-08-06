# Loaded-state 回读机制 · 实施计划

- 状态：`plan_only` — 无代码变更；本文与配套合同是唯一产出
- 日期：2026-08-06
- 基线：`HEAD=bb641d0`（工作树 clean，与 origin/main 同步）
- 阻塞对象：`scripts/sync_codex_home.sh` 的 `loaded_readback_unavailable` 门（`:454-466`，对非临时 `CODEX_HOME` 无条件拒绝）
- 证据等级：行号断言均已读源码核实；标 `[判断]` 为设计取舍

## 0. 问题与为什么磁盘 digest 不算数

`docs/HARNESS_RUNTIME.md:127-129` 的既定纪律：

> Unknown or unavailable loaded-state readback fails closed with `loaded_readback_unavailable` before runtime mutation. **Disk digest must never be reported as loaded digest.**

这不是洁癖。hooks 以 `/usr/bin/python3 ~/.codex/hooks/<file>.py` **每事件起新进程**执行（`codex/hooks.json`），而宿主的 `config.toml [hooks.state] trusted_hash` 是 TOFU 信任——**hooks.json 变更后新条目会被宿主静默跳过**。本项目实际发生过：文件在磁盘上是新的，但从未被执行（UPS 类事件 `unproven` 即由此而来）。

因此"loaded"的唯一诚实定义是：**这份字节内容真的被宿主调起执行过，且有它自己写下的凭据**。

## 1. 机制设计：执行时自证

### 1.1 谁来写

`harness_observer.py`（注册于 **PostToolUse**，`codex/hooks.json:54-63`，会话中高频执行且已被 evidence 存在性证实确实触发）在**每次被调起时**刷新一份 loaded receipt。选它而非新增独立 hook 的理由：**[判断]** 新 hook 条目会踩 TOFU 陷阱（注册了也可能被静默跳过），而 observer 已被证实在执行——把自证挂在已被证实执行的载体上，机制自身不引入新的"未被执行"风险。

### 1.2 写什么

`${CODEX_HOME}/harness/loaded-receipt.json`（原子写：mkstemp → fsync → rename，模式 0600，复用 sync 脚本 `:426-431` 与 observer `append_event` 的既有模式）：

```
schema_version        1
hook_path             执行文件的绝对路径
self_digest           sha256(执行文件自身字节)——运行时读 __file__ 现算，非磁盘扫描
session_id            payload 中的会话标识（若有）
event_kind            触发本次刷新的事件类型
written_at            UTC ISO 时间戳
```

**self_digest 是核心**：它由**正在执行的进程**对**自己正在执行的文件**计算——这就是"执行过"的证明。磁盘上有什么无关紧要。

### 1.3 sync 门禁怎么改

`:454-466` 的无条件拒绝改为三段判定（**默认仍拒绝**）。

**时间戳可比性（第 1 轮评审发现的缺陷）**：observer 现有 `now_iso()`（`:36-37`）产出**本地时区** ISO，而 manifest `synced_at` 是 UTC "Z" 结尾——两者**不得做字符串比较**。规定：receipt `written_at` 必须为**带时区**的 ISO 字符串；门禁判定必须 `datetime.fromisoformat` 解析后按**时刻**比较；无时区（naive）或不可解析的时间戳一律按 `loaded_readback_unavailable` 拒绝。

**manifest 缺失的三种组合必须穷尽**：

| manifest | receipt | 处置 |
| --- | --- | --- |
| 无 | 无 | 正门不可用；仅自举通道可过（全新目标的合法起点） |
| 无 | 有 | `loaded_readback_unavailable` 拒绝——无 manifest 则新鲜度不可判，且"有 receipt 却无 manifest"本身是异常状态，应人工调查 |
| 有 | 无/异常 | 按三段判定拒绝 |

| 判定 | reason_code | 语义 |
| --- | --- | --- |
| receipt 不存在 / 无法解析 / schema 不符 | `loaded_readback_unavailable`（沿用） | 无凭据，拒绝 |
| `written_at` 早于 manifest `synced_at` | `loaded_readback_stale` | 凭据来自上一代，不能证明当前代已加载 |
| `self_digest` ≠ 当前 runtime 对应文件的 sha256 | `loaded_readback_mismatch` | 磁盘与实际执行的内容不一致——**这正是 TOFU 陷阱现形的样子**，最有价值的一种拒绝 |
| 三关全过 | 继续后续流程 | 当前代已被证实加载，允许覆盖 |

比对对象：**[判断]** 只比对 observer 自身一个文件。它是唯一自证载体；其它 hook 文件的加载证明属后续扩展（每个 hook 各自写 receipt），本任务不做——**一个可信的窄门优于一个宽而假的门**。

### 1.4 成功后的 manifest 与 receipt 字段

sync 成功输出与 manifest（schema 2，`:416-423`）增加：

- `loaded_readback`: `verified` | `bootstrap_operator_attested`
- `loaded_receipt_digest`: 所读 receipt 文件自身的 sha256（事后可审计凭据是否被替换）

manifest `schema_version` 升为 3；读取端校验（`:284-299`）同步扩展，**schema 2 的旧 manifest 仍可读**（EXPECTED_OLD 的来源），但写出的必为 schema 3。

## 2. 自举：第一次怎么过门

死结：当前 runtime 的 observer 是旧版，不写 receipt → 门永远不开。

**解法：一次性 owner 亲证通道**，复用既有 `--operator-checkpoint` 模式（`--force-downgrade` 已用，四字段 receipt 校验在 `:367`）：

```
bash scripts/sync_codex_home.sh --repo-root <path> \
  --bootstrap-loaded-readback --operator-checkpoint <四字段 JSON>
```

**严格约束，缺一即拒**：

1. 仅当 `loaded-receipt.json` **不存在**时可用；存在则拒绝（`bootstrap_not_applicable`）——receipt 一旦出现过，永远走正门；
2. **仅当目标从未跨入回读时代时可用**：若已存在含 `loaded_readback` 字段的 manifest（schema 3），无论 receipt 是否存在，自举一律拒绝（`bootstrap_not_applicable`）。这使"自举只能发生一次"成为**机制**而非愿望——自举后若新 observer 不写 receipt，下次 sync 会被正门挡住且无法再自举，异常被强制暴露为事故；
3. checkpoint 必须恰好含 `command`/`exit_code`/`key_output`/`timestamp` 四字段（同 `:367` 的既有校验），且为 owner 手工提供——agent 不得代填；
4. 本次 sync 的 manifest 记 `loaded_readback: bootstrap_operator_attested`，与 `verified` 永久可区分。

**[判断]** 这与 approved-digest 的哲学一致：把无法机械验证的第一步变成**有记录的 owner 动作**，而非静默放宽。

## 3. 失败语义

- observer 写 receipt 失败：**不阻断工具流**（evidence 支线故障不应拒绝用户操作），但当次不刷新 → 后果自然传导为下次 sync 时 stale/unavailable，**fail-closed 落在 sync 处**而非用户操作处；
- receipt 被手工篡改：`loaded_receipt_digest` 留痕 + 下次 observer 执行覆盖；本机制是**漂移/失误控制，不是对抗有 `~/.codex` 写权限者的隔离**——与 digest authority 的诚实边界一致，写入文档；
- 时钟回拨导致 stale 误判：拒绝即安全方向，owner 可等下一次 observer 刷新后重试。

## 4. 分步与验收

| 步 | 内容 | 验收 | 
| --- | --- | --- |
| R1 | observer 写 receipt（原子、0600、字段齐全、self_digest 现算） | 临时 HOME 下调用 observer，receipt 出现且 digest 与文件字节一致；写失败不抛异常 |
| R2 | sync 三段判定 + schema 3 manifest + 两个新 reason_code | 表驱动测试矩阵（见合同）；schema 2 manifest 仍可读 |
| R3 | 自举通道 | 四条约束逐一可证伪 |

R1/R2/R3 均仅在临时 `CODEX_HOME` 验证；对真实 `~/.codex` 的推进是实施后的 **owner 操作**，不属本任务。

## 5. 实施后的 owner 操作序列（写进报告，非本任务执行）

1. 批准新源码 digest（改了 `codex/hooks/` 必然变值）并 commit + push；
2. 首次 sync 用自举通道（当前 runtime 无 receipt）；
3. 正常使用一段时间（observer 开始写 receipt）；
4. 下一次任意 sync 走正门 —— **走通即为 `runtime_loaded` 的首次机械证明**；
5. 此后 `loaded_readback_mismatch` 一旦出现即为 TOFU 或篡改现形，按事故处理。

## 6. 明确不做的事

- 不给 observer 之外的 hook 加自证（后续扩展）；
- 不改 `config.toml` / trusted_hash 机制本身；
- 不做 runtime promotion，不对真实 `~/.codex` 运行 sync；
- 不新增 daemon / service / framework；
- 不 commit / push（实施任务同样如此，落地由 owner 决定）；
- 不改 approved-digest 门与 transition 门的任何语义。
