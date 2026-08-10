# Harness 门禁改造实施计划

日期：2026-08-09
来源：非 Git 工作区（`~/Downloads/Job Application`）改简历被全局门禁阻止一事引出的完整分析。
代码基线：`claude/codex-hooks/hooks/` 下的 `harness_guard.py`（364 行）、`task_state.py`（273 行）、`harness_observer.py`、`dhf_preprompt.py`、`session_start_require_naming.py`。

---

## 一、问题清单

**P1 — 非 Git 工作区被误判，声明无法生效。**
`task_state.py` 的 `_resolve_transcript()`（243-252 行）先检查 `thread_source`，再比较 Git root，最后才解析声明。第 247 行 `if root_repo is None or current_repo is None or root_repo != current_repo` 把"两边都不在 Git repo 里"和"两边在不同 repo 里"塌缩成同一个 `ROOT_REPO_MISMATCH`。非 Git 目录下 `root_repo` 和 `current_repo` 都是 None，即使 transcript cwd 和当前 cwd 是同一目录、用户正确声明了 `task-mode: implementation`，`_declared_phase()`（249 行）也永远执行不到。结果 phase 回退 unknown，`repo_write` fail-closed。

**P2 — 守卫范围过大，且当前处于最差状态（全局禁用）。**
`hooks.json` 用 `matcher: "*"` 全局注册，Downloads 里的文档工作也被纳管。用户为了改简历临时禁用了整个 hook——所有真正的工程 repo 也因此失去保护。

**P3 — 门禁惰性触发，失败出现在任务中后段。**
PreToolUse 只在工具调用发生时评估，写入通常在分析工作之后，前期投入全部浪费。且现有守卫对 `read` 类静默放行（`harness_guard.py:338-339`），phase 解析结论从不外露，模型直到第一次写入被拒才知道规则。

**P4 — block 是死路，"自动新建任务"时灵时不灵。**
phase 生效要连续通过四道门：① `payload.phase` 或 `CODEX_HARNESS_PHASE` 环境变量直接注入（`harness_guard.py:123`）；② 根线程 `thread_source == "user"`（`task_state.py:243`）；③ Git root 匹配（247 行）；④ `phase_from_state_snapshot()` 的 repo 级快照兜底（`harness_guard.py:78-115`，只认 `docs/harness-state.md`）。任何一道失败都塌缩为 unknown + block，deny 消息不含修复路径，agent 只能停工等人。四道门的组合差异造成了"有时候能自动新建任务、有时候不能"的表象。

**P5 — 可观测性不足。**
对外只有 `marker_reason` 一个字段。四道门各自的判定结果没有记录，事后只能人肉逆向。

---

## 二、方案组件

### S1 — 修正 `task_state.py` 的资格检查语义（修 P1）

`_resolve_transcript()` 中 245-248 行改为：

```python
root_repo = _git_root_from_cwd(root_meta.get("cwd"))
current_repo = _git_root_from_cwd(current_cwd)
if root_repo is not None or current_repo is not None:
    if root_repo is None or current_repo is None or root_repo != current_repo:
        return None, "ROOT_REPO_MISMATCH"
else:
    root_cwd = _canonical_cwd(root_meta.get("cwd"))
    active_cwd = _canonical_cwd(current_cwd)
    if root_cwd is None or active_cwd is None or root_cwd != active_cwd:
        return None, "ROOT_WORKSPACE_MISMATCH"
```

新增 `_canonical_cwd()`：`Path(raw).expanduser().resolve(strict=False)`，与 `_git_root_from_cwd()`（197-211 行）的 canonical 化方式一致，覆盖 symlink 和 `..`（macOS 上 `/var` → `/private/var` 必须先 resolve）。

语义表：同一 Git repo → 继续解析；不同 Git repo → `ROOT_REPO_MISMATCH`；一边是 repo 一边不是 → `ROOT_REPO_MISMATCH`（fail-closed）；都不是 repo 且 canonical cwd 相同 → 继续解析；都不是 repo 且 cwd 不同 → `ROOT_WORKSPACE_MISMATCH`（fail-closed）。

### S2 — governed roots 范围治理（修 P2）

新增配置 `~/.codex/runtime/harness-scope.json`：

```json
{
  "governed_roots": ["~/Codes"],
  "protected_roots": ["~/.codex"],
  "out_of_scope_mode": "allow"
}
```

`harness_guard.py` 的 `decision()` 在 phase 解析前加范围判定：

1. canonical 化 cwd 与 `candidate_paths()` 返回的所有目标路径；
2. cwd、任一目标路径、**或命令文本命中 protected-path 正则** → 走完整门禁（防止"范围外放行"被用来改写守卫自身）。注意 `candidate_paths()`（68-75 行）只提取结构化字段（path/file/cwd 等），bash 重定向和参数里的目标路径不在其中，所以必须同时对 `command_text()` 跑一组 protected-path 正则（如 `~/\.codex/|\$HOME/\.codex/|/Users/[^/]+/\.codex/`）。这是 best-effort 模式匹配，不是沙箱——绕过（变量拼路径、cd 后相对路径）是可能的，真正的硬边界仍是 `protected_roots` 内文件的属主与权限（0700/0600，见 `harness_observer.py` 的 `DIRECTORY_MODE`/`FILE_MODE` 先例）；
3. cwd 命中 `governed_roots` → 走现有完整流程，行为不变；
4. 都不命中 → **不早退**，仍执行 `classify()`，但把 phase policy 换成合成的宽松策略 `{"allow_repo_write": True, "allow_network": True, "allow_remote": False}`。

第 4 点是关键设计：现有 `decision()` 中 `secret`、`destructive`、`dynamic_exec` 三类没有 allow 分支（341-346 行只放行 `repo_write`/`network`/`remote`），落到最终 block。换 policy 而非早退，意味着范围外目录里 `rm -rf`、凭证泄露、`curl | sh` 仍然被拦，只免除 phase 声明义务。

默认即 `"allow"`，不设前置观察期（决策见第五节）。`"report"` 值保留在实现里，供未来想收紧时使用。无论哪种模式，observer（`harness_observer.py`）都持续记录范围外写入——观察从"上线前的门槛"变成"上线后的常态"，可回溯性不损失。不提供环境变量 bypass——不可审计且任何子进程都能自己 set。

配置为每次 hook 调用时读取（与 `load_policy()` 读 `tool-policy.json` 同模式，36-42 行），改 `governed_roots` 即时生效、无需重启会话；文件缺失或 JSON 损坏时视为"无范围配置"，一切目录按 governed 处理（fail-closed，行为等同现状）。

### S3 — `codex-task declare` 自助声明，即"自动新建任务"（修 P4）

这是用户要的"codex 自动新建任务"的实现载体：agent 被 block 时，deny 消息携带声明指引 → agent 自己执行 `codex-task declare` → 重试原写入 → 通过。全程一个回合、零人工。配合 S4 的启动期信号，模型还能在第一次写入前就主动声明，连这一个回合的撞墙都省掉。

**声明命令**（新文件 `~/.codex/bin/codex-task`，Python 脚本）：

```
codex-task declare implementation --reason "创建 Upwork CV" [--ttl 8h]
```

行为：canonical 化 cwd → workspace key = git root（在 repo 内）或 canonical cwd（不在）→ 写 `~/.codex/task-state/<sha256(key)>.json`，内容 `{phase, reason, workspace, created_at, expires_at, session_id}` → 追加审计日志 `~/.codex/task-state/audit.jsonl`（轮转策略复用 `harness_observer.py` 的 `MAX_FILE_BYTES` 32MB 上限做法，超限滚动到 `audit.<date>.jsonl`）。phase 参数复用 `task_state.DECLARABLE_PHASES`（16-25 行）做别名解析与校验，拒绝 `ship`。默认 TTL 8 小时，上限 24 小时。

**守卫集成**（`harness_guard.py` 三处改动）：

1. `classify()` 前加显式判定，归类 `task_admin` 并在任何 phase 放行。**白名单判定必须是严格解析而非前缀正则**——`^\s*codex-task\s+declare\b` 这种前缀匹配会把 `codex-task declare x --reason y && rm -rf ~` 整条放行。正确做法：`shlex.split()` 整条命令；解析失败 → 不匹配；首 token 必须等于 `codex-task` 或其绝对路径 `~/.codex/bin/codex-task`（canonical 化后比较）；第二个 token 必须是 `declare`；命令文本不得含 `;`、`&&`、`||`、`|`、反引号、`$(`、`>`、换行（shlex 拆完后再对原文做元字符黑名单双保险）；参数只允许 `<phase>`、`--reason <str>`、`--ttl <dur>`。任何偏离 → 落回正常分类。另注：白名单匹配的是命令形状，不是二进制身份——PATH 劫持（工作区里放同名脚本）无法靠正则防住，缓解是 deny 指引中始终给绝对路径写法，且 `~/.codex/bin/` 位于 `protected_roots`，agent 改不了真身。
2. `_phase_resolution()` 加第五道门：transcript 解析失败后，查 snapshot store 中当前 workspace key 的未过期声明，命中则采用其 phase，`marker_reason = "SELF_DECLARED"`。
3. deny 消息按 risk tier 分层。`category_risk_tier()`（285-288 行）返回 low/medium 时，block reason 末尾追加：`To proceed: run ~/.codex/bin/codex-task declare <phase> --reason "<one line>" and retry.`——deny 消息是 host 唯一能回传给模型的通道（见约束 C1），模型读到指引后自己声明、自己重试，一个回合完成"自动新建任务"。high tier 不给指引，明确写 `requires human approval`。

**安全边界**：自助声明把 low/medium 风险的门禁从"阻止"降为"显式意图 + 留痕"，这是有意的取舍；high 风险（secret/destructive/dynamic_exec 及 policy 中标记 high 的类别）不受声明影响，照旧硬 block。声明过期自动失效；每次经 `SELF_DECLARED` 放行的写入都进 observer 日志。**会话绑定的取舍**：声明按 workspace key 而非 session 生效，TTL 内同 workspace 的其他会话也被解锁。这是刻意的——按 session 绑定会让并行会话各自撞墙再各自声明，重新制造摩擦；代价是解锁面变宽，靠 TTL（默认 8h）与审计日志中的 `session_id` 字段兜底。若日后需要收紧，snapshot 里已存 `session_id`，加一个 `"scope": "session"` 开关即可，不需要改数据结构。

### S4 — 早期信号（修 P3）

**约束 C1**：`harness_guard.py:306-314` 的注释记录了 2026-07-28 对 codex-cli 0.144.1 的隔离 probe 结论——PreToolUse 只有 legacy block 形状和 hookSpecificOutput deny 形状能拦截，ask 变体一律 fail-open。因此"放行时附带 warning"在 PreToolUse 通道上不可行。

改用 session 级通道，**扩展现有 `session_bearing.py`**——它已经挂在 SessionStart 上，用 `hookSpecificOutput.additionalContext` 注入文本（98-104 行，形状实测可用），但目前在非 Git 目录直接早退（93-94 行 `repo_root is None → return 0`），恰好是要改的地方。改造：无论是否在 repo 内，都跑一次范围判定 + phase 解析（复用 `phase_with_trace()` 与 S2 的 scope 逻辑），把结论注入上下文：

```
[harness] workspace=~/Downloads/Job Application (out-of-scope, writes allowed)
[harness] workspace=~/Codes/foo (governed, phase=unknown — declare before writing:
          codex-task declare <phase> --reason "...")
```

模型第一轮就知道边界，受管目录内会先声明再动手，而不是干到半路撞墙。

**预算约束**：`session_bearing.py` 有 0.18 秒硬预算（`BUDGET_SECONDS`，12 行），新增逻辑必须共享同一 deadline。范围判定是纯路径比较（微秒级）；phase 解析要读 transcript 文件（`SCAN_LINE_LIMIT=50` 行封顶）和查 snapshot store（单文件 stat+read），预算内可完成，但超时必须静默降级为不注入（沿用现有 `except Exception: return 0` 风格），绝不能拖慢会话启动。

**开放项 O1（已缩小）**：SessionStart 的事件名与输出形状已由 `session_bearing.py` 实测确认；剩余待确认项仅为 `~/.codex/hooks.json` 中 preprompt 类事件（`dhf_preprompt.py` 挂载的那个）的确切名称，供每轮 prompt 级刷新使用——若不可用，仅 SessionStart 一次性注入也足够。

### S5 — 门级可观测性（修 P5）

`_phase_resolution()` 内部扩展为携带 gate trace（env 注入/thread_source/git root/快照/自助声明五道门各自的判定与原因），`harness_observer.py` 落盘。**签名稳定性约束**：`current_phase()` 和 `load_policy()`、`git_root()` 被 `harness_observer.py` 以 `from harness_guard import` 方式导入（observer 顶部 13-18 行，导入失败会静默降级），这三个公开签名不得变更；gate trace 通过新增函数（如 `phase_with_trace()`）暴露，`current_phase()` 内部转调它。deny 消息保持单行不变，细节只进日志。下次"时灵时不灵"直接查日志，不再逆向。

---

## 三、实施阶段

**总成功指标**（全部 Phase 完成后一个月内）：
1. 因门禁误判或无法自救而需要人工重开任务的次数 → 0（当前：每次非 Git 工作区写入必中）；
2. hook 处于全局禁用状态的时长 → 0，Phase 1 完成当天即恢复启用（当前：已禁用数日）；
3. 受管 repo 内 secret/destructive/dynamic_exec 拦截率与改造前持平（用 observer 日志对比）；
4. 每次 `SELF_DECLARED` 放行都能在 audit.jsonl 中回溯到 phase、reason、workspace、session。

**Phase 0 — 前置（半天）**
把 `~/.codex/hooks.json` 与 `~/.codex/runtime/tool-policy.json` 拷入本目录（解决 O1，并确认 `repo_write_command_patterns`、`categories.*.risk_tier`、`phases` 的真实配置）；确认 pytest 环境（`hooks/tests/` 已有 `test_payload_probe.py` 先例）。

**Phase 1 — S1 + S2 一次落地，当天重新启用 hook（1-2 天）**
不设前置观察期，两个组件一起上，测试绿了当天启用。

S1 测试至少覆盖：① 同 repo 不同子目录；② 两个不同 repo；③ root 是 repo、当前非 repo；④ 同一非 Git 目录（应继续解析并成功声明 `implementation` → `development`）；⑤ 两个不同非 Git 目录；⑥ 非 Git 目录 symlink vs 真实路径；⑦ 非 Git 目录声明 `task-mode: implementation` 解析为 `development`；⑧ 非 Git 目录无 marker 仍 fail-closed。
S2 测试至少覆盖：范围外 repo_write 放行；范围外 `rm -rf` / secret / `curl | sh` 仍被拦；命令文本含 `~/.codex` 目标从任何 cwd 发起都走完整门禁；scope 文件缺失/损坏时全部按 governed 处理；范围外 agent_dispatch 无 receipt 仍 block。

**启用前检查单**：跑一次 `find ~ -type d -name .git 2>/dev/null`（全盘扫描；嫌慢可先 `-maxdepth 4` 粗扫，但结论以全盘为准）盘点所有 Git repo，确认 `governed_roots` 覆盖了每一个你在意的工程目录——**宁宽勿漏**，漏掉的 repo 会落入范围外宽松策略。

**窗口期 deny 指引**：Phase 1 启用后 `codex-task` 尚不存在（Phase 2 才落地），受管 repo 里的 block 不能是死路。Phase 1 就给 `block()` 的 reason 加临时指引（low/medium tier）：`To proceed: start a new task whose first line is 'task-mode: implementation'.`——S1 修好后这条 transcript 路径在受管 repo 与非 Git 目录都真实可用。Phase 2 上线 `codex-task` 后把指引替换为自助声明命令，才达到"不重开任务"的目标形态。
**启用与强制力实测**：改回 `hooks.json` → 新开会话验证三件事：受管 repo 内 unknown phase 写入被 block；范围外目录写入放行；范围外 `rm -rf` 仍被 block。hooks.json 是否需要重启 Codex 本体由此实测确认，不靠推断（R1 教训）。
**回滚开关**（清晰且即时）：删除或清空 `harness-scope.json` → 所有目录按 governed fail-closed（回到改造前行为）；或从 `hooks.json` 撤掉注册（回到当前禁用状态）。
验收：全部测试绿；原始场景（非 Git 目录改简历）零摩擦通过；hook 处于启用状态。

**Phase 2 — S3 自助声明（2 天）**
`codex-task` 脚本 + 守卫三处集成 + TTL/审计。测试：声明生效、过期失效、`ship` 被拒、high tier 不给指引、`task_admin` 类别在 unknown phase 放行、声明无法解锁 protected_roots 写入、workspace key 在 repo 内取 git root 而 repo 外取 canonical cwd。白名单对抗测试单列：`declare ... && rm -rf`、`declare ... ; curl`、`declare ... | sh`、`$(...)` 与反引号、重定向、换行拼接、伪装路径 `./codex-task`、多余参数——全部必须落回正常分类而非放行。
验收：在受管 repo 的 unknown phase 下，agent 仅凭 deny 消息指引即可声明并完成写入，全程无人工；audit.jsonl 有完整记录。

**Phase 3 — S4 早期信号 + S5 门级日志（1-2 天）**
SessionStart 部分无外部依赖（形状已实测）；preprompt 部分依赖 Phase 0 确认的事件名，不可用则降级为仅 SessionStart。验收：新会话首轮上下文即含 workspace/phase 结论；构造五道门各自失败的场景，日志能区分。

每个 Phase 独立可回滚：S1 是纯语义修正，S2-S4 各自有配置开关（scope 文件缺失 = 行为同现状；snapshot store 为空 = 行为同现状；bearing hook 未注册 = 行为同现状）。

---

## 四、风险与已知边界

**R1 — host fail-open 特性。** 约束 C1 意味着 hook 输出形状错误时工具调用会继续执行。所有新增输出必须沿用 `block()`（306-314 行）的既验证形状；新 hook 上线前先用 `payload_probe.py` 的方式隔离验证。

**R2 — 自助声明可被注入型 agent 滥用。** 提示注入的 agent 也能跑 `codex-task declare`。缓解：high 风险类别不受声明影响、protected_roots 硬边界、TTL、全量审计。剩余风险是范围内 low/medium 写入被恶意声明解锁——与"效率优先"的目标是同一枚硬币的两面，接受并靠日志兜底。

**R3 — `CODEX_HARNESS_PHASE` 环境变量是既存的更大后门。** 第一道门允许任何能设置环境变量的进程直接注入 phase（`harness_guard.py:123`），强度超过本计划新增的任何通道。本计划不动它（可能有合法上游用途），但 S5 的 gate trace 会记录 phase 来源，使其可见。后续可议：限制为仅 governed_roots 外生效，或要求与审计日志联动。

**R4 — 快照兜底与自助声明并存。** `phase_from_state_snapshot()` 与 S3 store 是两套来源，优先级定为：env/payload 注入 > transcript 声明 > 自助声明 > repo 快照。写入 gate trace，冲突时可查。

**R5 — 取消前置观察期的暴露。** 直接以 `allow` 模式启用，意味着 `governed_roots` 清单的完整性没有经过一周实证就 enforce——漏配的工程目录会直接落入范围外宽松策略（repo_write/network 放行，secret/destructive/dynamic_exec 仍拦）。缓解：启用前检查单强制盘点全部 Git repo、宁宽勿漏；observer 对范围外写入持续记日志，第一周建议每天扫一眼（非阻塞、不推迟启用）；回滚只需删 scope 文件。参照系：当前基线是 hook 全局禁用，立即启用的任何配置都严格优于现状。

---

## 五、决策记录（本次会话已定）

- 范围治理用配置文件白名单，不用环境变量 bypass（不可审计）。
- 范围外不早退，换合成宽松策略，保留 secret/destructive/dynamic_exec 拦截。
- 自助声明按 risk tier 分层：low/medium 可自助，high 必须人工。
- deny 消息是模型可见的唯一回传通道，修复指引直接写进 block reason。
- **不设前置观察期，直接 enforce**（用户 2026-08-09 决定，推翻此前"report 先行"的默认）：当前基线是 hook 全局禁用，任何启用状态都严格更安全，前置观察期的真实代价是 hook 多禁用一周；observer 的持续日志提供事后可回溯性，替代事前观察。`out_of_scope_mode: "report"` 保留在实现中作为未来收紧的选项。
- 范围外的 `agent_dispatch` 保持现状（合成策略不设 `allow_subagents`，无 validation receipt 仍 block）：多 agent 分派的风险与目录性质无关，不随范围豁免。
- S4 复用 `session_bearing.py` 而非新建 hook：SessionStart 事件名、注入形状、预算模式都已实测，新建文件只会引入第二套未验证的输出形状（违反 R1 的教训）。
