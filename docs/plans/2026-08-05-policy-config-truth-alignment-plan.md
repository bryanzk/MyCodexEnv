# Policy Config Truth Alignment — Plan

- 计划 ID：`MCE-20260805-policy-config-truth-alignment`
- 状态：plan（未实施）
- 前置：`98508f5 Enforce tracked approval manifest authority for runtime sync` 已提交，工作树干净
- 排序约束：**必须在 owner 向 `runtime-approvals/approved-source-digests.txt` 写入任何 digest 之前完成**

## 1. 为什么现在做

`codex/` 下的任何改动都会改变 `phase0_source_digest`。当前待审值为
`sha256:7a8821850f3d461e66ead41cdc4d2202595bd6bf94a85768dfaa57da72f8071f`，清单已跟踪、已提交、**digest 行数为 0**（尚未批准）。

若 owner 先批准该 digest、再做本计划的 `codex/` 改动，批准立即作废、需重走一次 code review。因此本计划应在批准之前完成，使 owner 只需批准一个稳定状态。

## 2. 问题清单（全部经源码核验）

### 2.1 D5：secret 规则过宽，且语义错位

`codex/runtime/tool-policy.json:100-106` 的 `secret_path_patterns` 末条为无锚定子串：

```
"(token|secret|credential|password)"
```

`codex/hooks/harness_guard.py:266` 把该模式集**同时**匹配命令文本与路径：

```python
if match_any(policy.get("secret_path_patterns", []), f"{cmd}\n{path_text}"):
    return "secret", "secret path or token-like string"
```

`secret` 类别在 `decision()` 中**没有任何 `allow_*` 分支**，因此在所有 phase 下一律 `block()`——是硬拒，不是提示。

实测误报面：

| 范围 | 命中 | 其中真凭证 |
| --- | --- | --- |
| MyCodexEnv 已跟踪文件 | 9 / 2606 | 0 |
| ShipQ 已跟踪文件 | 3 / 745 | 0 |

命令侧同样误伤，以下日常命令全部被硬拒：

```
pytest tests/test_password_reset.py
grep -rn credential src/
npm test -- session-tokens
rg 'secret' docs/
git log --oneline -- codex/skills/gstack/browse/src/token-registry.ts
```

这正是此前 Codex 无法创建测试 fixture 的直接原因：被拒的是**文件名**，不是内容。

### 2.2 该门禁从不检查文件内容（诚实边界）

`command_text()`（`:57-65`）只读取 `tool_input.command` / `cmd`；`candidate_paths()`（`:68-75`）只读取 `path`/`file`/`file_path`/`filename`/`cwd`/`workdir`。**载荷中的文件内容从不参与分类。**

因此 `secret` 门禁能做的是：拦截触碰凭证**命名**路径、以及命令行中出现凭证**字面量**。它**不能**阻止把凭证写进一个普通命名的文件。文档中不得把它表述为"防凭证泄漏"。

### 2.3 D1 扩展：6 个键从不被 guard 读取

| 键 | 出现位置 | guard 是否读取 | 真实影响 |
| --- | --- | --- | --- |
| `require_approval` | 8 个 phase 各一份 | 否（`:153` 仅为默认字典字面量） | **误导**：暗示存在审批层 |
| `allow_subagents` | 8 个 phase | 否 | **门禁失效**（见 2.4） |
| `minimum_gate` | 8 个 phase | 否 | 自然语言文本混在可执行策略中 |
| `plan_governor` | 顶层 | 否 | 实为状态记录，非配置 |
| `safe_read_command_patterns` | 顶层 | 否 | 见 2.5，**本计划不处理** |
| `version` | 顶层 | 否 | 无害元数据 |

`require_approval` 的处置由既有证据决定，无需新调查：`block()` 的注释记录了 2026-07-28 在 codex-cli 0.144.1 上的隔离探针结论——

> every "ask" variant are parsed as invalid/unsupported, the hook run is marked failed, and the tool call continues (fail-open). Former ask categories are therefore upgraded to block until the host supports a real ask.

即：ask 语义在宿主上不可用且会 fail-open。**实现 `require_approval` 会降低现有 fail-closed 姿态**，属红线。正确处置是删除该键，并在文档中写明"这些类别是硬拒，不存在审批通道"。

### 2.4 `allow_subagents` 门禁失效（owner 已裁决：实现）

当前 8 个 phase 中 `requirements` 与 `handoff` 声明 `allow_subagents: false`，其余为 `true`。但 `decision()` 对 `agent_dispatch` 的处理与 phase 完全无关：

```python
if category == "agent_dispatch":
    if has_fresh_validation_receipt(payload, policy, root):
        return {}
    return block(...)
```

只要有新鲜的 validation receipt 就放行，**声明禁用 subagent 的两个 phase 实际不禁用**。

owner 裁决：本任务实现为真门禁。

**关键实现顺序**：phase 检查必须**先于** receipt 短路。若放在其后，持有新鲜 receipt 即可绕过 phase 禁令，等于没修。

### 2.5 明确不在本计划范围：unmatched 命令 default-allow

`classify()` 的兜底是 `return "read"`，而 `decision()` 对 `read` 直接 `return {}`。因此**任何不匹配已知模式的命令一律放行**，与 phase 无关。

顶层存在一份从未被读取的 `safe_read_command_patterns` allowlist：

```
^\s*(pwd|ls|find|rg|sed\s+-n|tail|head|wc|git\s+(status|log|show|diff)|test\s+-f|cat)\b
```

它的存在说明设计意图可能是"读操作限于 allowlist"，而实现是"默认放行"。把兜底改为 default-deny 是高回归风险的架构级变更，**不在本计划内**，仅记录为独立议题待 owner 决定。本计划不得顺手修改它，也不得删除该键（删除会掩盖这个待决问题）。

## 3. 处置决定汇总

| 项 | 决定 | 依据 |
| --- | --- | --- |
| D5 secret 规则 | path / content 分离重设计 | owner 裁决；实测 12 误报 0 真阳 |
| `require_approval` | 删除 8 处 + 文档写明无审批通道 | ask 不可用且 fail-open（`block()` 注释所载探针） |
| `allow_subagents` | 实现为真门禁，phase 检查前置于 receipt | owner 裁决 |
| `minimum_gate` | 保留但标注为文档性字段 | 是人读的验收描述，删除会丢信息 |
| `plan_governor` | 保留并标注为状态记录 | 自述 `mode: shadow` / `production_status: no_go`，是诚实记录不是死配置 |
| `safe_read_command_patterns` | **不动** | 见 2.5，独立议题 |
| `version` | 保留 | 无害 |
| 防复发 | 新增"未读键漂移"测试 | 防止本类问题再次积累 |

## 4. 风险

| 风险 | 缓解 |
| --- | --- |
| secret 规则收窄过头，放过真凭证 | 正反语料测试：一组合成凭证形状**必须仍被拦**，一组真实仓库路径**必须放行**；语料一律合成，禁止使用任何真实凭证 |
| `allow_subagents` 上线后打断 requirements/handoff 工作流 | 该行为变更由 owner 明确裁决；报告须列出受影响的两个 phase 及其含义 |
| 改动 `codex/` 使待审 digest 失效 | 正是本计划要求排在批准之前的原因 |
| 误把 `plan_governor` 当死配置删除 | 合同显式列为保留项 |

## 5. 状态边界

本计划完成后可声称的最高状态为 `source_implemented` + `tests_verified`。
`runtime_synced` / `runtime_loaded` / `rollout_observed` / `runtime_active` / `automation_unpaused` / `owner_go` 一律维持既有未授权值——本计划不做 runtime promotion，不对真实 `~/.codex` 运行 sync。
