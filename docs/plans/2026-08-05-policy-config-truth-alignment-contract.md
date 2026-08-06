# Policy Config Truth Alignment — Implementation Contract

- 合同 ID：`MCE-20260805-policy-config-truth-alignment`
- 配套计划：`docs/plans/2026-08-05-policy-config-truth-alignment-plan.md`
- 模式：development
- 基线：`98508f5`。工作树中另有本计划与本合同两个未跟踪文件（`docs/plans/2026-08-05-policy-config-truth-alignment-{plan,contract}.md`）；它们在 `codex/` 之外，不参与 `phase0_source_digest`，`codex/` 本身干净。**不得删除或改写这两个文件。**

## 0. 前提与红线

- 本合同**不新增**任何审批/ask 通道。宿主 ask 语义已被证明 fail-open（`harness_guard.py:305-313` 注释所载 2026-07-28 探针，codex-cli 0.144.1），实现它会降低 fail-closed 姿态。
- 本合同**不修改** `classify()` 的兜底行为，**不删除** `safe_read_command_patterns`。
- 本合同**不做** runtime promotion，不对真实 `~/.codex` 运行 sync，不 commit、不 push。
- 测试语料**一律合成**。禁止写入、读取或引用任何真实凭证、令牌、密钥或客户数据。

## 1. 写集（仅限以下四项）

- `codex/runtime/tool-policy.json`
- `codex/hooks/harness_guard.py`
- `test_runner.py`
- `docs/HARNESS_RUNTIME.md`

明确排除：`codex/hooks.json`、`codex/hooks/task_state.py`、`codex/hooks/harness_observer.py`、`scripts/**`、`runtime-approvals/**`、所有 `~/.codex/**`、automation controller、automation execution clone、ShipQ。

## 2. 要实现的行为

### 2.1 secret 规则：path / content 分离

**删除** `secret_path_patterns` 中的 `"(token|secret|credential|password)"`。

`secret_path_patterns` 改为**只匹配路径**，且全部锚定到文件名或扩展名：

```
(^|/)\.env(\.(?!example$|sample$|template$|dist$)[^/]*)?$
(^|/)auth\.json$
(^|/)id_rsa$
(^|/)\.netrc$
(^|/)\.aws/credentials$
(^|/)\.ssh/
\.(pem|key|p12|pfx|jks|keystore)$
```

第一条的否定前瞻是必需的：`codex/skills/gstack/.env.example` 是已跟踪的模板文件，不加前瞻会**引入一个新误报**——与本任务要修的正是同一类毛病。

**新增** `secret_command_patterns`，**只匹配命令文本**，针对真实凭证形状而非命名习惯：

```
-----BEGIN [A-Z ]*PRIVATE KEY-----
\bAKIA[0-9A-Z]{16}\b
\bghp_[A-Za-z0-9]{36}\b
\bgithub_pat_[A-Za-z0-9_]{22,}\b
\bxox[baprs]-[A-Za-z0-9-]{10,}\b
\bsk-[A-Za-z0-9]{20,}\b
\bBearer\s+[A-Za-z0-9._~+/-]{20,}={0,2}
\b(export|set)\s+[A-Za-z_]*(TOKEN|SECRET|PASSWORD|API_KEY)\s*=\s*["']?[A-Za-z0-9_\-./+]{8,}
--password=\S{4,}
```

两条易踩坑的设计约束：

- 赋值型模式**必须要求右值是字面量**（`["']?[A-Za-z0-9_\-./+]{8,}`）。若只写到 `\s*=` 为止，`export FOO_TOKEN="$MY_VAR"` 与 `export CI_SECRET=$(vault read …)` 会被硬拒——它们是间接引用、命令行里没有凭证，属误报。
- `--password` **只收 `=` 形式**。`--password[=\s]\S` 会把 `psql --password mydb` 判为凭证，而 psql 的 `--password` 是无参的交互提示开关，`mydb` 是库名。

**匹配标志**：`match_any`（`harness_guard.py:157-161`）使用 `re.search(..., flags=re.IGNORECASE)`。所有模式的验证与测试**必须在 IGNORECASE 下进行**，否则结论不成立。

`harness_guard.py:266` 拆为两次匹配，各自作用于正确的输入：

```python
if match_any(policy.get("secret_path_patterns", []), path_text):
    return "secret", "secret path"
if match_any(policy.get("secret_command_patterns", []), cmd):
    return "secret", "credential-shaped literal in command"
```

两者仍归入 `secret` 类别、仍为所有 phase 硬拒——**本合同只收窄判定，不放宽处置**。

未提供 `secret_command_patterns` 时按空列表处理（不回退到旧的合并匹配）。

### 2.2 `allow_subagents` 实现为真门禁

`decision()` 中 `agent_dispatch` 分支改为**先查 phase、后查 receipt**：

```python
if category == "agent_dispatch":
    if phase_policy.get("allow_subagents") is False:
        return block(f"[harness] subagent dispatch is disabled during phase '{phase}'.", risk_tier)
    if has_fresh_validation_receipt(payload, policy, root):
        return {}
    return block(...)
```

判定用 `is False`：键缺失或非布尔值时**不**禁用（保持既有行为），避免因配置缺失产生意料外的新拒绝。受影响 phase 为 `requirements` 与 `handoff`。

### 2.3 死键处置

- **删除**全部 8 处 `require_approval`。
- **保留** `minimum_gate`，但在 `docs/HARNESS_RUNTIME.md` 写明它是人读的验收描述、不参与判定。
- **保留** `plan_governor` 原样，并在文档中写明它是状态记录（`mode: shadow` / `production_status: no_go`），不是可执行配置。
- **保留** `version`、`safe_read_command_patterns` 原样。

### 2.4 防复发：未读键漂移测试

新增测试，断言 `tool-policy.json` 中不存在"既不被 `harness_guard.py` 读取、又未登记为已知非执行键"的键。

已知非执行键白名单**写在测试内**并各带一行理由：`version`（元数据）、`minimum_gate`（文档性验收描述）、`plan_governor`（状态记录）、`safe_read_command_patterns`（待决独立议题，见计划 §2.5）。

判定方式：以 `harness_guard.py` 源码中是否出现该键名字符串为准。这是**近似**判据——它能抓住"完全没被引用"，抓不住"被引用但未真正消费"（`require_approval` 此前正属后者）。因此测试须**额外**断言白名单逐字相等：新增键必须显式登记，删除键必须同步更新，否则 FAIL。此限制须写入测试注释，不得声称该测试能证明"所有键都被消费"。

### 2.5 文档

`docs/HARNESS_RUNTIME.md` 增补，必须包含：

1. secret 判定的两条路径（路径锚定 / 命令内凭证字面量）及其**不覆盖文件内容**的诚实边界——分类器只读 `tool_input.command`/`cmd` 与路径类字段，载荷中的文件内容从不参与判定，因此该门禁不能阻止把凭证写进普通命名的文件。
2. 不存在审批/ask 通道；`secret`、`destructive`、`dynamic_exec` 在所有 phase 下均为硬拒。
3. `minimum_gate` 与 `plan_governor` 的非执行性质。
4. `allow_subagents` 现已生效，以及受影响的两个 phase。

不得出现"防凭证泄漏""已实现审批门禁"一类表述。

## 3. 测试要求

RED 必须来自行为不满足，不得以函数不存在或 ImportError 制造 RED。扩展 `test_harness_guard_policy_decisions`（`:3744`）与 `test_agent_dispatch_gate`（`:6111`），或新增表驱动函数。

### 3.1 secret 正反语料

| # | 输入 | 期望 |
| --- | --- | --- |
| 1 | 路径 `config/.env` | `secret`，blocked |
| 2 | 路径 `secrets/app.pem` | `secret`，blocked |
| 3 | 路径 `~/.aws/credentials` | `secret`，blocked |
| 4 | 路径 `codex/skills/gstack/browse/src/token-registry.ts` | **不是** `secret` |
| 5 | 路径 `docs/delivery/phase1-customer/13-configuration-and-secret-register.md` | **不是** `secret` |
| 6 | 命令 `pytest tests/test_password_reset.py` | **不是** `secret` |
| 7 | 命令 `rg 'secret' docs/` | **不是** `secret` |
| 8 | 命令含 `AKIAIOSFODNN7EXAMPLE` | `secret`，blocked |
| 9 | 命令含 `-----BEGIN RSA PRIVATE KEY-----` | `secret`，blocked |
| 10 | 命令 `export GITHUB_TOKEN=ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | `secret`，blocked |
| 11 | 命令 `curl -H 'Authorization: Bearer abcdefghijklmnopqrstuvwxyz012345'` | `secret`，blocked |
| 12 | 路径 `data/AKIAIOSFODNN7EXAMPLE.txt` | **不是** `secret`（证明 command 模式未外溢到路径判定） |
| 13 | 路径 `codex/skills/gstack/.env.example` | **不是** `secret`（模板文件，已跟踪） |
| 14 | 路径 `.env.local` | `secret`，blocked（证明否定前瞻未把真 `.env` 变体一起放过） |
| 15 | 命令 `export FOO_TOKEN="$MY_VAR"` | **不是** `secret`（间接引用，无字面量） |
| 16 | 命令 `export CI_SECRET=$(vault read -field=v x)` | **不是** `secret` |
| 17 | 命令 `psql --password mydb` | **不是** `secret`（无参交互开关） |
| 18 | 命令 `mysql --password=hunter2xy db` | `secret`，blocked |

第 8–11、18 项的语料必须是**公开文档中的示例值或明显合成串**（如 AWS 官方示例 `AKIAIOSFODNN7EXAMPLE`），不得使用任何真实凭证。

**注意右值长度**：赋值型模式要求右值至少 8 个字符，因此 `export GITHUB_TOKEN=xxxxx` 这类短占位**不会**命中。语料必须用足够长的合成串，否则测试会以"规则没生效"的假象失败。

**全仓库零误报断言**：另加一条测试，对 `git ls-files` 列出的全部已跟踪路径套用新的 `secret_path_patterns`，断言命中数为 **0**。实测基线：MyCodexEnv 0/2607、ShipQ 0/745（ShipQ 不在本仓测试范围，仅作设计佐证）。该断言会在有人新增凭证命名文件时失败，属预期行为——届时应确认该文件是否真的该进仓库。

### 3.2 `allow_subagents`

| # | 场景 | 期望 |
| --- | --- | --- |
| 19 | phase=`requirements`，agent_dispatch，**持有新鲜 receipt** | **仍 blocked**（证明 phase 检查先于 receipt 短路） |
| 20 | phase=`handoff`，agent_dispatch，无 receipt | blocked |
| 21 | phase=`development`，agent_dispatch，持有新鲜 receipt | 放行 |
| 22 | phase=`development`，agent_dispatch，无 receipt | blocked（既有行为不变） |
| 23 | phase 配置中缺失 `allow_subagents` 键 | 按既有行为处理，不因缺失产生新拒绝 |

第 19 项是本节关键验收：若把 phase 检查写在 receipt 短路之后，该用例必然失败。

### 3.3 死键与漂移

| # | 场景 | 期望 |
| --- | --- | --- |
| 24 | `require_approval` 在 policy 中的出现次数 | 0 |
| 25 | 向 policy 注入一个未登记的新键 | 漂移测试 FAIL，输出该键名 |
| 26 | 从白名单删除一项但 policy 中仍存在 | FAIL |
| 27 | `plan_governor`、`minimum_gate`、`safe_read_command_patterns`、`version` | 仍存在且未被修改 |

第 25、26 项在临时副本上构造，不得改动仓库内的 `tool-policy.json`。

## 4. 验证命令

```bash
cd /Users/kezheng/Codes/CursorDeveloper/MyCodexEnv
python3 -c 'import json;json.load(open("codex/runtime/tool-policy.json"));print("policy json ok")'
python3 -c 'import re,json;p=json.load(open("codex/runtime/tool-policy.json"));[re.compile(x) for k in ("secret_path_patterns","secret_command_patterns","destructive_command_patterns","dynamic_exec_patterns","remote_command_patterns","network_command_patterns","repo_write_command_patterns") for x in p.get(k,[])];print("all regexes compile")'
PYTHONDONTWRITEBYTECODE=1 python3 -c 'import test_runner as t; t.test_harness_guard_policy_decisions(); t.test_agent_dispatch_gate()'
tmp_root="$(mktemp -d)"; HOME="$tmp_root/home" PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py
python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav --json
git diff --check
git --no-optional-locks status --short
```

全部在临时 `HOME`/`CODEX_HOME` 内。不得硬编码全量套件的测试总数。

## 5. 完成标准

1. `secret_path_patterns` 中无无锚定子串；`secret_command_patterns` 已新增；两者在 `classify()` 中作用于各自正确的输入。
2. §3.1 的 18 条正反语料全绿：第 4–7、12–13、15–17 项证明误报已消除，第 8–11、18 项证明真凭证形状仍被拦截，另加全仓库零误报断言。
3. `allow_subagents` 生效，且第 19 项证明 phase 检查前置于 receipt 短路。
4. `require_approval` 在 policy 中出现次数为 0；`harness_guard.py` 中的默认字典亦同步移除该键。
5. `plan_governor`、`minimum_gate`、`safe_read_command_patterns`、`version` 均保留未改。
6. 漂移测试存在，白名单四项各带理由，且测试注释写明其判据是"键名是否被引用"这一近似，不能证明键已被真正消费。
7. `docs/HARNESS_RUNTIME.md` 含 §2.5 的四项，且无"防凭证泄漏""已实现审批门禁"表述。
8. 全量测试无回归；写集限于四个文件。
9. 报告须给出**改动后**的 `phase0_source_digest` 新值，并说明旧值 `sha256:7a8821850f3d461e66ead41cdc4d2202595bd6bf94a85768dfaa57da72f8071f` 已作废、owner 应改为审批新值。
10. 结论只声称 `source_implemented=true` + `tests_verified=true`；`runtime_synced` / `runtime_loaded` / `rollout_observed` / `runtime_active` / `automation_unpaused` / `runtime_pilot` / ShipQ Level 2 / `owner_go` 维持既有未授权值。

## 6. 非目标

不实现 ask/审批通道；不修改 `classify()` 兜底或 `safe_read_command_patterns`；不改 `hooks.json`、`task_state.py`、`harness_observer.py`；不做 runtime promotion；不 commit/push；不 unpause automation；不触碰 ShipQ 或 `~/.codex`；不新增 daemon/service/框架；不向批准清单写入任何 digest。
