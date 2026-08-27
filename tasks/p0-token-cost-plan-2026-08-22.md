# MyCodexEnv token 成本 P0 修改计划 v5（+§8 P1 待办）

日期：2026-08-22 · 状态：计划，未改仓库、未改 `~/.codex`
`verification_receipt: verification_not_applicable`（本文件只是计划；文中仓库事实已用只读命令核对，见附录 A）

本计划自身的执行 profile：**governed**（P0-2 动 `hooks.json` 与本机 runtime）。单 Agent 顺序执行，不派子 Agent；每个切片合并前跑 `test_runner.py` + `verify_codex_env.sh`，合并后 `harness_checkpoint.py append`。

## 0.1 v3 相对 v2 的改动

1. 基线补上「后」：每个切片合并后，三组冻结任务各重跑 ≥3 次；governed 组每次跑的 token 预算先由 P0-1 改前那一次给出数字，owner 看了再决定是否 3 次。
2. `token_usage=unknown` 不是孤立字符串，是被测试和文档当合同的：`test_runner.py:7777` 逐字断言它，`docs/HARNESS_RUNTIME.md:472–473` 把它写成注入合同。P0-2 写集补这两处；改字符串必须和改测试、改文档同一 commit。
3. D1 只阻塞 P0-2。P0-1、P0-3 不等 D1。

## 0. v2 相对 v1 的改动

1. P0-2 改错了文件：「必须写 `unavailable`」那段在 `model_router.py`，而 `compaction_probe.py` 注入的是另一段 `token_usage=unknown; remaining_capacity=unknown`。两段都要删，但各归各的文件。
2. 写集补上 hook 的第二份源 `claude/codex-hooks/hooks/`。
3. 发现一颗地雷：`scripts/sync_codex_home.sh` 第 1108–1135 行会用 `codex/config.template.toml` 重新渲染并覆盖 `~/.codex/config.toml`（先备份）。模板写的是 `gpt-5.5`。**P0-2 第一步不是删 hook，是先修模板**，否则下一次 sync 会把本机模型降级。
4. `context_policy` 有了消费者：`harness_agent_team.py` 新增 `brief` 子命令，把计划渲染成 spawn 时实际粘贴的 brief 文本；validate 只负责拦，brief 负责落地。
5. 加了 Codex 配置键核对步骤（§3 P0-2 第 0 步）。在核对前，`[agents]`、`fork_turns` 这些名字在本计划里都只是「Codex 审计的说法」。
6. reporter 加每轮序列输出；A/B 加重复次数与冻结条件。
7. 加 owner 决策表、回滚路径、可机器验证的完成标准、`harness-state.md` 更新规则。

## 1. 对 Codex 审计的核验结论

Codex 的三条 P0 判断逐条核对过。**三条都成立，但有三处要修正。**

| Codex 说法 | 核对结果 |
|---|---|
| `model_router.py` 推荐 `gpt-5.4-mini / 5.4 / 5.5`，每条 prompt 都跑，只注入建议不切模型 | 属实。`MODEL_TIERS` 就是这三个型号；`hooks.json` 的 `UserPromptSubmit` 第二个 hook 就是它；输出只走 `additionalContext`。 |
| 它「只注入约 340 字符建议」 | **不完整**。它还要求「每次最终回复必须包含 telemetry：model、token 消耗、5 小时 limit」，而 `token_usage` 和 `five_hour_limit` 永远是 `unavailable`。每轮都在花 output token 写一段注定是「不可用」的话。 |
| DHF 输出 `token_usage=unknown` | 属实，来源是 `context_meter.ordinal_only_context()`，由 `compaction_probe.py` 每条 prompt 注入。`USAGE_FIELDS_PRESENT = False` 在第 12 行。 |
| Agent Team Gate 不校验 `fork_turns`、模型、reasoning、工具白名单 | 属实。`harness_agent_team.py` 只校验 role / scope / write_set / brief / task_demand / green_gate，且只有 `validate` 一个子命令。全仓 grep `fork_turns` 为 0。 |
| 当前模型是 `gpt-5.6-sol` | **无法核对**。`~/.codex` 不在本会话可读范围。仓库模板仍写 `gpt-5.5`。 |
| 可以直接删 model-router hook | **漏了两件事**。(a) `test_runner.py` 有 30 处引用，两个测试明文断言它「must remain globally registered」；(b) hook 源在 `codex/hooks/` 和 `claude/codex-hooks/hooks/` 各有一份。 |
| 「官方模型族是 Sol/Terra/Luna」「Codex 支持 `[agents]` 或 custom-agent 文件」 | **未核对**。本计划把它们当作待验证前提，不当作事实。 |

另外：PDF 的「50%–65%」是分项数据反推，作者自己承认没做端到端 A/B。Codex 转述准确。所以**本计划不承诺任何百分比**。Codex 提的「子 Agent 默认 `gpt-5.6-terra low`」只能做 A/B 实验臂，不能做默认值。

## 2. Owner 决策

| 编号 | 决策 | 默认 | 为什么要你拍板 |
|---|---|---|---|
| D1 | `config.template.toml` 的 `model` 写成什么 | **已拍板 2026-08-22**：`model = "gpt-5.6-sol"`、`model_context_window = 1000000`、`model_auto_compact_token_limit = 900000`、`model_reasoning_effort = "medium"`、`personality = "pragmatic"` | 核对后发现模板缺 `model_context_window` 和 `model_auto_compact_token_limit` 两行——sync 不只会降级型号，还会把这两项丢掉。P0-2 第 1 步五行全补。 |
| D3 | 已拍板：主 Agent 不变；子 Agent 臂 = {`gpt-5.6-sol low`, Codex 建议的轻量型号 `low`} | — | 轻量型号的确切名字在 P0-2 第 0 步核对后填 |
| D4 | governed 冻结任务每轮跑 3 次的预算 | **已拍板：走默认**——P0-1 改前先跑 1 次出数，owner 看数后决定是否补到 3 次 | 一次 governed 任务可能就是几十万 input token |
| D2 | 三个切片是一个 PR 三个 commit，还是三个 PR | 三个 PR，按 P0-1 → P0-2 → P0-3 合并 | P0-2 会动 `hooks.json` 和本机 runtime，单独回滚更干净 |

## 3. 三条 P0 的顺序

Codex 把「删 model router」排第一。我把它排第二：**没有尺子，改完任何东西都不知道有没有变好。**

| 顺序 | 切片 | 一句话 |
|---|---|---|
| P0-1 | rollout 成本 reporter + 基线存档 | 先有尺子 |
| P0-2 | 修模板 → 拆 router → 删两段废话注入 → 真实 subagent 配置 | 去掉每轮固定浪费 |
| P0-3 | Agent Team Gate 加 `context_policy`，并有 `brief` 消费它 | 子 Agent 不再重新加载一遍世界 |

三个切片写集互不重叠（见附录 B）。

## 4. 完成标准（每条都能用命令验）

1. `python3 scripts/harness_cost_report.py --session <id> --json` 输出含 `totals.{input,cached_input,output}`、`turns[]`（每轮 input/cached/output）、`tool_calls{name:count}`、`wall_seconds`；`totals` 与该 rollout 最后一条 `token_count` 逐字段相等（测试断言）。
2. `docs/harness/cost-baseline/` 下存在三组冻结任务的 JSON：改前各 ≥3 次（governed 组按 D4），每个切片合并后各 ≥3 次；文件名含 `before|after-p0-1|after-p0-2|after-p0-3` 与 HEAD 短 SHA。
3. `jq '.hooks.UserPromptSubmit[0].hooks[].command' codex/hooks.json | grep -c model_router` = 0；`codex/hooks/model_router.py` 与 `claude/codex-hooks/hooks/model_router.py` 均不存在。
4. `grep -rn "unavailable\|token_usage=unknown" codex/hooks/ claude/codex-hooks/hooks/` = 0。
5. `grep -c "gpt-5.6-sol\|model_context_window = 1000000\|model_auto_compact_token_limit = 900000" codex/config.template.toml` = 3；`python3 test_runner.py` 全绿；`bash scripts/verify_codex_env.sh` 全绿；sync 后 `diff <(grep ^model ~/.codex/config.toml) <(grep ^model ~/.codex/config.toml.backup.*最新)` 为空。
6. `harness_agent_team.py validate` 对缺 `context_policy` 的非 planner 角色报 `ERROR[context_policy_missing]`；对 reviewer 写 `fork_turns=last:2` 报 `ERROR[context_policy_fork]`；对 `tests/fixtures/agent-team/valid-*.json` 全部通过。
7. `harness_agent_team.py brief PLAN.json --agent <id>` 输出的文本里含该 agent 的 `fork_turns`、`allowed_skills`、`upstream_inputs`，且不含未列出的 skill 名。
8. `docs/harness-state.md` 的 next action 指向 P0 下一切片，不再是 8 月 19 日的 Wave 4。

## 5. 实施切片

### P0-1：rollout 成本 reporter

写集：`scripts/harness_cost_report.py`（新）、`tests/fixtures/rollout/`（新）、`test_runner.py`（只加测试）、`docs/harness/cost-baseline/`（新）。

0. 先 dump 一条真实 `token_count` 事件进 fixture（脱敏），字段名以文件为准，不凭 Codex 的描述写。
1. 只读解析 `~/.codex/sessions/**/rollout-*.jsonl`。只读，不写 `~/.codex` 任何东西。
2. 按 session 聚合：累计 input / cached input / output、缓存命中率、轮次、工具调用按名计数、首尾时间差；**另输出 `turns[]` 每轮序列**，因为 Codex 的核心发现是「轮次 × 越来越大的上下文」，总量看不出来，曲线才看得出来。`turns[]` 每项带 `compaction_ordinal`（来自 `~/.codex/harness/` 的计数器或 rollout 里的 compaction 事件），否则 input 突然掉一截你分不清是压缩还是改动生效。
3. 父子会话：若 rollout 能区分（独立文件或 parent 字段），按 parent/subagent 分行；分不出来就在 JSON 里写 `"subagent_attribution": "not_available"`，不猜。
4. 三组冻结任务写进 `docs/harness/cost-baseline/tasks.md`：(a) light：只读文件回答问题；(b) standard：改一个脚本加一个测试；(c) governed：两个 worker 的 agent team 任务。每组**改前跑 ≥3 次**存档。冻结条件：同一 `git rev-parse HEAD`、同一 `skills-lock.json`、同一 `~/.codex/config.toml` sha256，三者写进每份 JSON。
5. 比较口径固定：input、cached input、uncached input（= input − cached）、output、轮次、工具调用、wall time、失败/重试。质量门禁（现有 `test_runner.py` 和各任务自带验证）不下降才算数。

停止条件：rollout 找不到 `token_count`，或字段形状与 Codex 描述不符——先报告，不硬写。

### P0-2：修模板 → 拆 router → 删废话注入 → 真实分层

写集：`codex/config.template.toml`、`codex/hooks.json`、`codex/hooks/{model_router.py,context_meter.py,compaction_probe.py}`、`claude/codex-hooks/hooks/{同三文件}`、`claude/codex-hooks/hooks/tests/`（已 grep：不含 `token_usage=unknown` 断言，只需随源文件同步）、`test_runner.py`（router 的 30 处 + 第 7732–7777 行 context meter 断言）、`docs/HARNESS_RUNTIME.md` 第 451–473 行、`codex/agents/`（新，模板）、`docs/harness/model-tiers.md`（新，一页）。`~/.codex/` 只在本机手动改，不进仓库写集。

前置：D1 已拍板。

0. **核对 Codex 配置键**。读 Codex 当前版本文档或 `codex --help` / 配置 schema，确认：custom-agent 文件的路径与 frontmatter 字段；`[agents]` 是否存在；`fork_turns` 是否是 spawn 参数及其取值。把结果写进 `docs/harness/model-tiers.md` 顶部，带日期和版本号。**核不到就退回只做第 1–4 步。**
1. 改 `config.template.toml` 前三行为 D1 的五行：`model`、`model_context_window`、`model_auto_compact_token_limit`、`model_reasoning_effort`、`personality`。这一步先于一切，因为 sync 会覆盖本机 config；补测试：`test_runner.py` 断言模板含这五个键且 `model` 不再是 `gpt-5.5`。
2. 从 `hooks.json` 移除 `model_router.py`；删两份源文件。
3. `test_runner.py`：`test_shipq_dhf_prompt_hook_auto_invokes_skill` 和 `test_dhf_dispatcher_global_registration_and_hook_order` 改成断言 router **不在** 列表；删 `MODEL_ROUTER` 常量和第 1497 行「model router hook should be copied」等引用，共 30 处。
4. `context_meter.ordinal_only_context()`：`additional_context` 只留 `compaction_ordinal=N (host-observed); context_pressure_signal=ordinal-only`，删 `token_usage=unknown; remaining_capacity=unknown`。返回 dict 里的 `signal`/`token_usage` 字段不动（`test_runner.py:7732` 和 `harness_eval.py` 读的是 dict 不是字符串）。同一 commit 改 `test_runner.py:7777` 的字符串断言和 `docs/HARNESS_RUNTIME.md:472–473` 的合同描述。`USAGE_FIELDS_PRESENT` 保留，注释改为「描述 hook payload，不描述 rollout；rollout 侧见 `harness_cost_report.py`」。两份源同步改。
5. 按第 0 步结果，在 `codex/agents/` 放三个 custom-agent 模板：`explorer`（只读、低 reasoning）、`reviewer`（只读、高 reasoning）、`worker`（可写、中 reasoning）。型号字段留 `<<D3>>` 占位，由 P0-1 的 A/B 决定后再填。`sync_codex_home.sh` 增加把它们同步到 `~/.codex/agents/` 的步骤（先备份）。
6. 本机：跑 `sync_codex_home.sh`，再跑 `verify_codex_env.sh`；对照 sync 的备份文件确认 `config.toml` 的 `model` 没变。

回滚：仓库侧 `git revert` 该 PR；runtime 侧 `sync_codex_home.sh` 每次都留 `hooks.json.backup.*` 和 `config.toml.backup.*`，`cp` 回去即可。`codex/agents/` 是新增目录，删掉即回滚。

停止条件：第 0 步核不到 custom-agent / `[agents]`——只做 1–4，第 5 步改成 issue 记录。

### P0-3：Agent Team Gate 最小上下文约束

写集：`scripts/harness_agent_team.py`、`codex/skills/delivery-harness-framework/SKILL.md` 的「Agent Team Gate」一节（≤6 行增量）、`codex/skills/delivery-harness-framework/references/agent-team-context-policy.md`（新）、`docs/templates/harness-agent-brief.md`、`tests/fixtures/agent-team/`（新）、`test_runner.py`。

依赖：P0-2 第 0 步的核对结果。若 `fork_turns` 不是 Codex 真实参数，字段改名为 `history`（取值 `none | last:N`），语义不变，brief 里用自然语言表达。

1. plan schema 新增 `context_policy`：`fork_turns`（`none | last:N`）、`model_tier`（`explorer | reviewer | worker | custom`）、`allowed_skills`（列表，默认空）、`allowed_mcp`（列表，默认空）、`upstream_inputs`（列表，指向上游 Agent 产出的结构化摘要路径）。
2. 规则：planner / reviewer / security / qa 默认且只能 `fork_turns=none`；worker 写 `last:N` 时 N ≤ 3 且必须有 `reason`。
3. 规则：`upstream_inputs` 非空时，`allowed_skills` 不得含上游 Agent 已列出的 skill；违者 `ERROR[context_policy_reload]`。
4. **消费者**：新增 `brief` 子命令，按 `docs/templates/harness-agent-brief.md` 把单个 agent 渲染成 spawn 时粘贴的 brief：目标、精确文件、输出结构、验证命令、`context_policy` 四项。主 Agent 派工只允许用这个输出，不手写。
5. SKILL.md 加 6 行：`context_policy` 必填、默认值、`brief` 子命令；示例和字段说明进 `references/`。
6. 现有 governed 任务的 plan fixture 全部补 `context_policy` 并通过。

回滚：`git revert`；无 runtime 改动。

停止条件：现有 fixture 全部因新规则失败——默认值定错了，回到第 2 步重定，不放宽规则。

## 6. 收尾（每个切片合并后）

- `python3 scripts/harness_checkpoint.py append` 一条，含验证收据。
- `docs/harness-state.md` 的 next action 改成下一切片；P0-3 合并后改成「跑 A/B，填 D3」。

## 7. 不修改

- 不装 Graphify，不接 rtk，不动 observer 降噪，不拆 SKILL.md（P1）。
- 不批量删 skill。
- 不把任何百分比写进文档。
- 不动 `harness_guard.py`。

## 8. P1 待办（P0 执行中发现，按数据优先级排）

| # | 项 | 依据 | 写集预估 |
|---|---|---|---|
| P1-1 | 拆 DHF `SKILL.md` 为 L2/L3；skill 目录去重 | light-b 基线：每会话进门费 31.9K uncached，其中 skill 目录 68K 字符，是唯一的大头 | `codex/skills/delivery-harness-framework/`、`references/` |
| P1-2 | **一条命令刷新全部 managed-source 身份**：`dhf_simplification_evidence` 的 BASE_COMMIT、`approved-source-digests.txt`、paired gate 的 transition / promotion_candidate_manifest / base_expected_runtime_manifest | P0-2、P0-3 各撞三层冻结哈希，为过自家门禁多花 ≥7 个 commit 和三轮往返；门禁有效但维护成本已是真实 token 开销 | `scripts/`（新脚本或并入 `sync_codex_home.sh` 预检）、`test_runner.py` |
| P1-3 | `model_auto_compact_token_limit` A/B（300000 / 500000 臂） | governed run 1：压缩在 67.5 万触发，每次 `exec` 重发全上下文 | `~/.codex/config.toml`（本机）、基线 JSON |
| P1-4 | observer 降噪：只留 decision / verification / failure / deny，只读调用计数聚合 | Codex 审计：evidence 114 MB，954/963 条为无 kind 的 tool_call | `codex/hooks/harness_observer.py` |
| P1-5 | `BASE_COMMIT` 跟随最近一次提升，或删除 `source_stage_unsynced` 状态 | P0-3 发现：首次提升后该状态不可达 | `scripts/dhf_simplification_evidence.py` |
| P1-6 | D3 子 Agent 轻量型号臂（型号名待核实） | 计划 D3 | `codex/agents/*.toml` |

顺序建议：P1-2 先做——它不省 token，但它让 P1-1 和后面每一次 skill 改动少掉三轮往返。然后 P1-1，因为数据只指向它。

## 附录 A：2026-08-22 只读核对记录

- `git status --short --branch` → `## main...origin/main`，干净。
- `codex/hooks/model_router.py`：第 11–15 行 `MODEL_TIERS` = gpt-5.4-mini / gpt-5.4 / gpt-5.5；`build_response()` 的 additionalContext 含「若 hook payload 未提供真实 token 或 limit 字段，必须写 `unavailable`」。
- `codex/hooks.json`：`UserPromptSubmit` 顺序 compaction_probe → model_router → dhf_preprompt。
- `codex/hooks/context_meter.py`：第 12 行 `USAGE_FIELDS_PRESENT = False`；`ordinal_only_context()` 第 75–78 行注入 `token_usage=unknown; remaining_capacity=unknown`；唯一调用方 `compaction_probe.py` 第 19、315 行。
- `claude/codex-hooks/hooks/`：含 `model_router.py`、`context_meter.py`、`compaction_probe.py` 的第二份源。
- `scripts/sync_codex_home.sh` 第 1108–1135 行：备份后用 `codex/config.template.toml` 渲染覆盖 `~/.codex/config.toml`；第 1265–1271 行同样方式覆盖 `hooks.json`。
- `codex/config.template.toml` 第 1–2 行：`model = "gpt-5.5"`、`model_reasoning_effort = "medium"`；无 `[agents]`。
- `test_runner.py`：30 处引用 model_router；第 2666–2673、2762–2769 行两个测试断言其必须注册且先于 dhf_preprompt；第 1497 行断言它被复制到 `~/.codex/hooks/`。
- `scripts/harness_agent_team.py`：只有 `validate` 子命令；校验 role / scope / write_set / brief / task_demand / green_gate。
- 全仓 grep `fork_turns`：0。
- grep `token_usage=unknown`：`test_runner.py:7777`（逐字断言）、`docs/HARNESS_RUNTIME.md:453,473`（合同描述）；`scripts/harness_eval.py` 不按该字符串断言。
- `~/.codex/`：本会话不可读。`config.toml` 前五行由 owner 2026-08-22 提供（见 D1）；rollout `token_count` 字段形状、`agents/` 是否存在仍未独立核对。

## 附录 B：写集重叠检查

| 文件 | P0-1 | P0-2 | P0-3 |
|---|---|---|---|
| `test_runner.py` | 加测试 | 改/删 router 测试 | 加测试 |
| 其余 | 各自独立 | 各自独立 | 各自独立 |

`test_runner.py` 三个切片都碰，但各碰不同函数；按 D2 顺序合并即可，不会冲突。
