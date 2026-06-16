# DHF Independent Project Evaluation / DHF 独立项目评估

Date / 日期: 2026-06-15
Repo / 仓库: `MyCodexEnv`
Phase / 阶段: `planning` -> `review`
Execution lane / 执行通道: `local_dev`

## Objective / 目标

Evaluate whether Delivery Harness Framework (DHF) should become an independent
GitHub project, and define the best invocation model that preserves harness
engineering correctness, runtime performance, and token efficiency.

评估 Delivery Harness Framework（DHF）是否应该拆成独立 GitHub 项目，并定义最佳调用方式：
既保证 harness engineering 的正确性和性能，又尽可能节省 token。

## Decision / 结论

Yes. DHF should become an independent GitHub project, but through staged
extraction rather than a hard fork of all current `MyCodexEnv` surfaces.

是。DHF 应该成为一个独立 GitHub 项目，但应采用分阶段抽取，而不是立刻把
`MyCodexEnv` 里的所有相关内容硬拆出去。

Recommended path / 推荐路径:

1. Create an independent `delivery-harness-framework` repository for the generic
   core.
   创建独立的 `delivery-harness-framework` 仓库，承载通用核心。
2. Keep `MyCodexEnv` as the reference implementation, integration test bed, and
   pinned consumer.
   保留 `MyCodexEnv` 作为参考实现、集成测试环境和 pinned consumer。
3. Keep repo-specific lifecycle adapters in their owning repos.
   项目专属 lifecycle adapter 留在各自项目仓库。
4. Keep personal runtime state, local evidence logs, active handoffs, secrets,
   and machine-specific sync rules outside the independent project.
   个人运行时状态、本地 evidence、活跃 handoff、密钥和机器专属同步规则不得进入独立项目。

This gives DHF a clean product boundary without breaking the current working
environment.

这样可以让 DHF 获得清晰产品边界，同时不破坏当前可用的本机工作环境。

## Public GitHub Project Contract / 公开 GitHub 项目合同

Target users / 目标用户:

- Agentic engineering operators who want reusable lifecycle, evidence, and
  handoff discipline for local repos.
  需要给本地仓库接入可复用生命周期、证据和交接纪律的 agentic engineering 操作者。
- Tech leads who want verification, handoff, and agent-team guardrails without
  adopting all of `MyCodexEnv`.
  想要 verification、handoff、agent-team guardrail，但不想整体采用 `MyCodexEnv` 的技术负责人。
- Skill authors who need a generic router plus eval pattern for complex work.
  需要通用 router 和 eval pattern 来治理复杂任务的 skill 作者。

Non-goals / 非目标:

- Do not become a full Codex/Claude environment reproduction repo.
  不成为完整 Codex/Claude 环境复现仓库。
- Do not vendor all gstack skills.
  不 vendor 全量 gstack skills。
- Do not own project-specific adapters, fixtures, deployment topology, or
  business safety rules.
  不承载项目专属 adapter、fixture、部署拓扑或业务安全边界。
- Do not publish local evidence logs, active handoffs, secrets, or customer data.
  不发布本地 evidence、活跃 handoff、密钥或客户数据。

Phase 1 supported platform / Phase 1 支持平台:

- Python 3.10+ on macOS and Linux.
  macOS 和 Linux 上的 Python 3.10+。
- POSIX shell examples.
  POSIX shell 示例。
- No Codex/Claude authentication required for the minimal example.
  最小示例不依赖 Codex/Claude 认证。
- Windows support is out of scope until helper paths and shell assumptions are
  tested separately.
  Windows 支持延后，直到 helper 路径和 shell 假设被单独验证。

Governance / 治理:

- License: MIT for Phase 1.
  许可证：Phase 1 使用 MIT。
- Add `CONTRIBUTING.md`, `SECURITY.md`, issue templates, and a PR template that
  requires verification evidence.
  增加 `CONTRIBUTING.md`、`SECURITY.md`、issue 模板，以及要求验证证据的 PR 模板。
- Support stance: best-effort public project, no SLA, no production support
  promise.
  支持承诺：best-effort 公开项目，不承诺 SLA 或生产支持。

Minimum viable public repo / 最小可用公开仓库:

- `README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`
- `.github/workflows/ci.yml`
- generic DHF skill / 通用 DHF skill
- runtime docs and schemas / runtime 文档与 schema
- helper CLI subset / helper CLI 子集
- packet schema / packet schema
- eval matrix / eval 矩阵
- one minimal consumer example / 一个最小 consumer 示例
- one adapter skeleton / 一个 adapter 骨架

## Source Evidence / 来源证据

Inspected sources / 已检查来源:

- `README.md`: defines `MyCodexEnv` as Codex + Claude environment reproduction
  and documents DHF as a generic lifecycle router plus runtime system.
  定义 `MyCodexEnv` 是 Codex + Claude 环境复现仓库，并说明 DHF 是通用生命周期 router
  加 runtime system。
- `docs/repo-index.md`: low-token navigation surface and runtime surface index.
  低 token 导航面和 runtime surface 索引。
- `docs/HARNESS_RUNTIME.md`: lifecycle, evidence, recovery, env probe, model
  router, checkpoint, and agent-team contracts.
  定义 lifecycle、evidence、recovery、env probe、model router、checkpoint 和
  agent-team 合同。
- `docs/LIFECYCLE_SKILL_ROUTING.md`: runtime / router / specialist layering.
  定义 runtime、router、specialist 三层结构。
- `docs/AGENT_HARNESS_STATUS.md`: current workflow and infra status map.
  当前 workflow 与 infra 状态图。
- `codex/skills/delivery-harness-framework/SKILL.md`: generic lifecycle router
  source.
  通用 lifecycle router 的 skill 源。
- `codex/skills/delivery-harness-framework/evals/evals.json`: routing boundary
  eval matrix.
  routing boundary eval 矩阵。
- `.github/workflows/ci.yml`: portable green gate.
  portable green gate。

Current source receipts / 当前来源证据:

- command: `rg -n "Research|Validation|Model Router|Checkpoints|Guardrails|Skills|Observability" docs/AGENT_HARNESS_STATUS.md`
  - exit_code: 0
  - key_output: Research, Validation, Skills, Observability, Model Router,
    Checkpoints, and Guardrails rows are present.
  - timestamp: `2026-06-15T17:57:35-04:00`
- command: `python3 -c "import json, collections; data=json.load(open('codex/skills/delivery-harness-framework/evals/evals.json')); cats=collections.Counter(e['category'] for e in data['evals']); print('skill_name', data['skill_name']); print('eval_count', len(data['evals'])); print('categories', dict(sorted(cats.items())))"`
  - exit_code: 0
  - key_output: `skill_name delivery-harness-framework`; `eval_count 22`;
    categories include `positive_routing`, `negative_routing`,
    `forbidden_load`, `progressive_loading`, and `end_to_end`.
  - timestamp: `2026-06-15T17:57:35-04:00`

## Current Shape / 当前形态

DHF is already bigger than a single skill. It includes public docs, a generic
lifecycle router, routing evals, runtime schemas, hooks, helper CLIs, visual
guides, CI gates, and tests.

DHF 已经不只是一个 skill。它包含公开文档、通用 lifecycle router、routing eval、runtime
schema、hooks、helper CLI、可视化指南、CI gate 和测试。

This is enough to justify an independent project: DHF already has a product
boundary, runtime contract, source code, docs, evals, and verification story.

这足以支撑独立项目：DHF 已经具备产品边界、runtime 合同、源码、文档、eval 和验证故事。

Do not split everything immediately because `MyCodexEnv` still owns local
environment reproduction, Codex/Claude sync, runtime-home copy behavior, gstack
vendor refresh, active handoff backlog, and machine-specific policy.

不要立刻全量拆分，因为 `MyCodexEnv` 仍然负责本机环境复现、Codex/Claude 同步、runtime
home 副本行为、gstack vendor refresh、活跃 handoff backlog 和机器专属策略。

## What "Best" Means / “最佳”的定义

For DHF, best means correctness first, then token efficiency and runtime
performance.

对 DHF 来说，最佳首先是正确性，其次才是 token 效率和 runtime 性能。

1. Correctness / 正确性: never bypass source-of-truth reads, dirty-worktree
   ownership, lane classification, evidence, or safety gates.
   不绕过 source-of-truth、dirty worktree ownership、lane 分类、evidence 或 safety gate。
2. Token efficiency / Token 效率: load the smallest source that can make the next
   decision.
   只加载足以做出下一步决策的最小上下文。
3. Runtime performance / 运行性能: use deterministic helpers for parsing,
   validation, recovery, and evidence summaries.
   解析、验证、恢复和 evidence summary 优先交给确定性 helper。
4. Portability / 可移植性: a repo can adopt DHF without inheriting personal
   state or unrelated skills.
   新仓库可采用 DHF，而不继承个人状态或无关 skill。
5. Distribution clarity / 分发清晰度: users can install, pin, verify, and upgrade
   a versioned core.
   用户可以安装、pin、验证和升级版本化 core。
6. Drift control / 漂移控制: evals and CI catch routing, docs, helper, and schema
   drift.
   用 eval 和 CI 捕捉 routing、docs、helper、schema 漂移。
7. Least privilege / 最小权限: remote, secret, customer, production, destructive,
   and live-demo actions stay approval-gated.
   remote、secret、customer、production、destructive、live-demo 操作保持 approval-gated。
8. Recovery / 可恢复性: every meaningful slice leaves a compact next-safe-task
   and verification bundle.
   每个有意义切片都留下 compact next-safe-task 和验证包。

Token saving is a constraint under the correctness floor, not the primary
objective.

节省 token 是正确性底线之下的约束，不是首要目标。

## Repository Boundary / 仓库边界

| Current Surface / 当前面 | Independent DHF Action / 独立 DHF 动作 | Rationale / 理由 |
| --- | --- | --- |
| `docs/HARNESS_RUNTIME.md` | adapt to `docs/runtime-contract.md` / 改造成 `docs/runtime-contract.md` | Generic contract belongs in public core; remove MyCodexEnv wording. 通用合同属于 public core；移除 MyCodexEnv 表述。 |
| `docs/LIFECYCLE_SKILL_ROUTING.md` | adapt to `docs/lifecycle-skill-routing.md` / 改造成 `docs/lifecycle-skill-routing.md` | Generic routing map; gstack/local skill refs become extension points. 通用 routing map；gstack/local skill 引用变成扩展点。 |
| `docs/repo-index.md` | adapt to template and example / 改造成模板和示例 | The pattern is portable; current file is repo-specific. 模式可移植，当前文件是仓库专属。 |
| `docs/surfaces.json` | adapt and keep / 改造并保留 | Core drift-control contract. 核心漂移控制合同。 |
| `scripts/check_surfaces.py` | move and generalize / 移动并泛化 | Validates surface manifest and public nav. 验证 surface manifest 和 public nav。 |
| `codex/skills/delivery-harness-framework/` | adapt to `skills/delivery-harness-framework/` / 改造成 `skills/delivery-harness-framework/` | Core router artifact. 核心 router artifact。 |
| `codex/skills/delivery-harness-framework/evals/evals.json` | move to `evals/` or stay under skill / 移动到 `evals/` 或保留在 skill 下 | Required for routing boundary protection. 保护 routing boundary 必需。 |
| `codex/runtime/evidence*.json` | move to `runtime/` / 移动到 `runtime/` | Generic evidence schemas. 通用 evidence schema。 |
| `codex/runtime/tool-policy.json` | adapt to `runtime/tool-policy.json` / 改造成 `runtime/tool-policy.json` | Generic stage policy; tool names configurable. 通用阶段策略；工具名可配置。 |
| `codex/hooks/harness_guard.py` | adapt to `hooks/harness_guard.py` / 改造成 `hooks/harness_guard.py` | Generic guard; dispatch shapes data-driven. 通用 guard；dispatch shape 数据驱动。 |
| `codex/hooks/harness_observer.py` | adapt to `hooks/harness_observer.py` / 改造成 `hooks/harness_observer.py` | Generic observer; evidence stays local. 通用 observer；evidence 保持本地。 |
| `codex/hooks/model_router.py` | move to `hooks/model_router.py` / 移动到 `hooks/model_router.py` | Generic quality-floor-first router. 通用 quality-floor-first router。 |
| `scripts/harness_feedback.py` | move and generalize / 移动并泛化 | Conversion-health is part of report/recover contract. conversion-health 属于 report/recover 合同。 |
| `scripts/harness_report.py`, `harness_recover.py`, `harness_env_probe.py`, `harness_requirements.py`, `harness_agent_team.py`, `harness_checkpoint.py`, `harness_evidence.py` | move and generalize / 移动并泛化 | Generic helpers. 通用 helpers。 |
| `scripts/headroom_filter.py` | move as optional helper / 作为可选 helper 移动 | Useful for large output compression; never required. 用于大输出压缩；不作为硬依赖。 |
| `docs/templates/*` | move to `templates/` / 移动到 `templates/` | Public adoption artifacts. 公开采用 artifact。 |
| public DHF HTML pages | adapt under `docs/` / 改造后放入 `docs/` | Public docs belong in project; remove publisher-specific references if needed. 公开文档属于项目；必要时移除发布方专属引用。 |
| `test_runner.py` | split / 拆分 | Generic DHF tests move; MyCodexEnv sync tests stay. 通用 DHF 测试移动；MyCodexEnv sync 测试保留。 |
| `.github/workflows/ci.yml` | adapt / 改造 | New repo needs its own portable green gate. 新仓库需要自己的 portable green gate。 |
| `docs/harness-state.md` | exclude history, provide template only / 排除历史，仅提供模板 | Current state is local session evidence. 当前 state 是本地会话 evidence。 |
| `docs/handoffs/*` | exclude / 排除 | Local maintenance artifacts. 本地维护 artifact。 |
| `scripts/sync_codex_home.sh`, `scripts/verify_codex_env.sh` | stay in MyCodexEnv / 留在 MyCodexEnv | They verify/sync this environment, not portable DHF. 它们验证/同步当前环境，不是 portable DHF。 |
| `codex/AGENTS.md`, `codex/remote-access.md`, `codex/remote-hosts.md` | stay in MyCodexEnv / 留在 MyCodexEnv | Global/personal environment rules. 全局/个人环境规则。 |
| `codex/skills/gstack/` and refresh scripts | stay in MyCodexEnv / 留在 MyCodexEnv | DHF routes to gstack but should not vendor all gstack. DHF 路由到 gstack，但不应 vendor 全量 gstack。 |
| `~/.codex/harness/evidence` | exclude / 排除 | Local/private evidence. 本地/私有 evidence。 |

Project repos own their own adapters, fixtures, smoke matrices, deployment
topology, business safety boundaries, `AGENTS.md`, source-of-truth docs, and
verification gates.

项目仓库自己负责 adapter、fixture、smoke matrix、部署拓扑、业务安全边界、`AGENTS.md`、
source-of-truth 文档和验证 gate。

## Fresh Repo Self-Test / 全新 DHF 仓库自测

```bash
git clone https://github.com/<owner>/delivery-harness-framework.git
cd delivery-harness-framework
python3 test_runner.py
git diff --check
python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav
python3 scripts/validate_dhf_packet.py examples/packets/basic.json
```

Expected key output / 期望关键输出:

- `test_runner.py`: `[PASS] all tests`
- `git diff --check`: no output / 无输出
- `check_surfaces.py`: `surfaces manifest consistent`
- `validate_dhf_packet.py`: `dhf packet valid`

`validate_dhf_packet.py` does not exist yet in `MyCodexEnv`; it is a Phase 1
target.

`validate_dhf_packet.py` 当前尚不存在于 `MyCodexEnv`；它是 Phase 1 目标。

## Fresh Consumer Adoption / 全新 Consumer 采用路径

Use a source checkout installer first, not a package-registry release. This
keeps Phase 1 focused on boundary correctness.

先使用 source checkout installer，而不是 package registry 发布；这样 Phase 1 聚焦边界正确性。

Target command shape / 目标命令形态:

```bash
git clone https://github.com/<owner>/delivery-harness-framework.git /tmp/delivery-harness-framework
git init /tmp/dhf-consumer
cd /tmp/dhf-consumer
python3 /tmp/delivery-harness-framework/scripts/dhf_install.py \
  --source /tmp/delivery-harness-framework \
  --target "$(pwd)" \
  --profile minimal \
  --no-overwrite
python3 .dhf/scripts/dhf_doctor.py --repo-root "$(pwd)" --json
python3 .dhf/scripts/validate_dhf_packet.py .dhf/examples/packets/minimal.json
git diff --check
```

Files written by `--profile minimal` / `--profile minimal` 写入文件:

- `.dhf/manifest.json`
- `.dhf/schemas/dhf-packet.schema.json`
- `.dhf/runtime/evidence.schema.json`
- `.dhf/runtime/evidence/decision-evidence.schema.json`
- `.dhf/runtime/evidence/routine-gate-receipt.schema.json`
- `.dhf/scripts/harness_recover.py`
- `.dhf/scripts/harness_env_probe.py`
- `.dhf/scripts/validate_dhf_packet.py`
- `.dhf/scripts/dhf_doctor.py`
- `.dhf/examples/packets/minimal.json`
- `docs/templates/harness-requirements.md`
- `docs/templates/harness-agent-brief.md`

Files created only if absent / 仅在不存在时创建:

- `docs/repo-index.md`
- `docs/harness-state.md`

If either file already exists and is not marked as DHF-managed, the installer
must refuse overwrite and emit `.dhf/install-report.md`.

如果上述文件已存在且未标记为 DHF-managed，installer 必须拒绝覆盖，并生成
`.dhf/install-report.md`。

Consumer-side expected output / Consumer 侧期望输出:

- `dhf_doctor.py`: `dhf_consumer_ok=true`, `managed_files_ok=true`
- `validate_dhf_packet.py`: `dhf packet valid`
- `git diff --check`: no output / 无输出

`dhf_install.py`, `dhf_doctor.py`, and consumer packet validation are Phase 1
acceptance targets.

`dhf_install.py`、`dhf_doctor.py` 和 consumer packet validation 都是 Phase 1
验收目标。

## Release And Consumption / 发布与消费合同

Recommended tag format / 推荐 tag 格式: `dhf-core-vYYYY.MM.DD.N`

Each release should include / 每个 release 应包含:

- source archive digest / source archive 摘要
- changelog entry / changelog
- compatible packet schema version / 兼容 packet schema 版本
- compatible evidence schema version / 兼容 evidence schema 版本
- helper CLI list / helper CLI 列表
- routing eval summary / routing eval 摘要
- migration notes / 迁移说明

MyCodexEnv consumer gate / MyCodexEnv consumer gate:

```bash
python3 scripts/compare_dhf_core_snapshot.py \
  --source ../delivery-harness-framework \
  --consumer "$(pwd)" \
  --manifest docs/dhf-core-pin.json
python3 test_runner.py
./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome
```

This gate is intentionally MyCodexEnv-specific. Other repos should use
`.dhf/scripts/dhf_doctor.py` and packet validation.

这个 gate 明确是 MyCodexEnv 专属。其他仓库应使用 `.dhf/scripts/dhf_doctor.py`
和 packet validation。

`compare_dhf_core_snapshot.py` and `docs/dhf-core-pin.json` are target artifacts,
not existing files.

`compare_dhf_core_snapshot.py` 和 `docs/dhf-core-pin.json` 是目标 artifact，不是现有文件。

## Best Invocation Model / 最佳调用模型

Default model: cheap DHF preflight packet first, lazy deep loading only when
required.

默认模型：先生成低成本 DHF preflight packet，仅在必要时 lazy deep load。

### Level 0: Skip DHF / 跳过 DHF

Use for typo fixes, one-file formatting, simple translation, direct command
requests, or clearly low-risk local questions.

适用于 typo、单文件格式、简单翻译、直接命令请求或明确低风险本地问题。

Proof / 证明方式: narrow repo-native command evidence / 最小 repo-native 命令证据。

### Level 1: Light DHF Preflight / 轻量 DHF 预检

Use for non-trivial local work where a small state read is enough to choose the
next step.

适用于非平凡本地任务：只需少量 state 读取即可决定下一步。

Portable inputs / 可移植输入:

- root `AGENTS.md`
- `docs/repo-index.md`
- `git status --short --branch`
- `python3 .dhf/scripts/harness_recover.py --repo-root "$(pwd)" --json`
- `python3 .dhf/scripts/harness_env_probe.py --json`

For MyCodexEnv only, add `--codex-home "$HOME/.codex"` when probing the local
Codex runtime. Independent DHF must treat Codex home as optional context.

仅对 MyCodexEnv，当目标是探测本机 Codex runtime 时追加 `--codex-home "$HOME/.codex"`。
独立 DHF 必须把 Codex home 视为可选上下文。

Packet fields / Packet 字段:

```text
stage:
lane:
dirty_state:
source_of_truth:
allowed_writes:
forbidden_actions:
helper_or_skill_route:
verification_gate:
next_safe_task:
```

### Level 2: Standard DHF Routing / 标准 DHF 路由

Use when work spans files, skills, workers, handoff state, runtime helpers, or
review loops.

适用于跨文件、skill、worker、handoff state、runtime helper 或 review loop 的任务。

Read Level 1 inputs plus relevant runtime sections, current state snapshot and
tail, relevant skill `SKILL.md`, and relevant tests or CI gates.

读取 Level 1 输入，再加相关 runtime 章节、当前 state snapshot/tail、相关 skill
`SKILL.md`、相关测试或 CI gate。

### Level 3: Deep DHF Alignment / 深度 DHF 对齐

Use only for architecture conflicts, stale durable sources, live/customer lane
questions, parallel worker dispatch, release, security/privacy, or major
framework changes.

仅用于架构冲突、durable source 过期、live/customer lane、parallel worker dispatch、
release、安全/隐私或重大框架变更。

## DHF Packet Target / DHF Packet 目标

```json
{
  "schema_version": 1,
  "repo_root": "/absolute/path",
  "stage": "planning",
  "lane": "local_dev",
  "dirty_state": {
    "status": "clean|dirty",
    "user_owned": [],
    "agent_owned": [],
    "unknown_owner": []
  },
  "source_of_truth": [
    {"path": "AGENTS.md", "purpose": "repo rules", "freshness": "read_this_turn"}
  ],
  "allowed_writes": [],
  "forbidden_actions": ["remote", "secret", "deploy", "destructive"],
  "helper_or_skill_route": ["delivery-harness-framework"],
  "verification_gate": [
    {
      "command": "git diff --check",
      "expected_key_output": "no output"
    }
  ],
  "next_safe_task": "string",
  "telemetry_requirement": {
    "token_usage": "real_or_unavailable",
    "five_hour_limit": "real_or_unavailable"
  }
}
```

Target validator / 目标校验器:

```bash
python3 scripts/validate_dhf_packet.py PATH_TO_PACKET.json
```

Required failure behavior / 必需失败行为: non-zero exit, name the invalid field,
and do not write partial output / 非零退出、指出无效字段、不写入部分输出。

## Invocation Budgets / 调用预算

These are planning targets until `measure_dhf_invocation.py` exists. They become
hard gates only after packet telemetry and helper timing are implemented.

在 `measure_dhf_invocation.py` 存在前，这些只是规划目标。只有 packet telemetry 和
helper timing 实现后，它们才成为 hard gate。

| Level / 级别 | Context budget / 上下文预算 | Helper budget / Helper 预算 | Gate / Gate |
| --- | --- | --- | --- |
| 0 | 0 DHF-specific docs; ideally under 300 tokens / 0 DHF 专属文档，理想低于 300 tokens | none / 无 | no DHF load for negative-routing evals / negative-routing eval 不加载 DHF |
| 1 | <= 1,500 added tokens / 新增 <= 1,500 tokens | <= 3 helpers, p95 <= 5s / <= 3 个 helper，p95 <= 5s | packet validates; no raw logs / packet 通过；无 raw log |
| 2 | <= 4,000 added tokens / 新增 <= 4,000 tokens | <= 8 reads/helpers, p95 <= 15s / <= 8 次读取/helper，p95 <= 15s | selected gate named / 明确验证 gate |
| 3 | <= 10,000 added tokens unless justified / 未说明理由时 <= 10,000 tokens | bounded by plan / 由计划约束 | written justification plus handoff gate / 书面理由加 handoff gate |

Target measurement command / 目标测量命令:

```bash
python3 scripts/measure_dhf_invocation.py \
  --scenario evals/invocation-levels.json \
  --assert-budget
```

## Token-Saving Rules / Token 节省规则

1. Prefer `docs/repo-index.md` over broad `docs/` reads.
   优先读 `docs/repo-index.md`，避免宽泛读取 `docs/`。
2. Prefer current snapshot plus latest tail over full append-only state logs.
   优先读 current snapshot 加 latest tail，不读完整 append-only state log。
3. Prefer helper JSON summaries over raw logs.
   优先使用 helper JSON summary，而不是 raw log。
4. Prefer `docs/surfaces.json` for inventory questions.
   inventory 问题优先使用 `docs/surfaces.json`。
5. Prefer targeted `rg` over opening public HTML pages.
   优先 targeted `rg`，不要默认打开 public HTML。
6. Use `headroom_filter.py` only as optional context compression.
   `headroom_filter.py` 仅作为可选上下文压缩工具。
7. Pass a DHF packet to specialist skills instead of the full manual.
   给 specialist skill 传 DHF packet，而不是整本文档。
8. Re-run model routing at stage boundaries.
   在阶段边界重新跑 model routing。
9. Keep evidence receipts compact.
   evidence receipt 保持紧凑。
10. Reserve committee loops for explicit rating/revision targets.
    committee loop 只用于明确评分/修订目标。

Headroom constraints / Headroom 约束:

- Detect dependency first; fall back to `rg`, `sed`, `tail`, or helper JSON.
  先检测依赖；缺失时回退到 `rg`、`sed`、`tail` 或 helper JSON。
- Never compress source files, diffs, security-sensitive output, or evidence
  needing exact review.
  不压缩需要精确审查的源码、diff、安全敏感输出或 evidence。
- Never use Headroom to hide failures.
  不用 Headroom 掩盖失败。

## Model Router Protocol / Model Router 协议

Preserve current behavior / 保持当前行为:

- `validation` without high-risk signals -> `gpt-5.4-mini`, low reasoning.
  无高风险信号的 `validation` -> `gpt-5.4-mini`，low reasoning。
- `review` -> `gpt-5.5`, high reasoning.
  `review` -> `gpt-5.5`，high reasoning。
- security/deploy/migration/production signals raise to frontier tier.
  security/deploy/migration/production 信号升级到 frontier tier。
- complex prompts expose `switch_points`.
  复杂 prompt 输出 `switch_points`。
- telemetry reports real token/limit fields or `unavailable`; never estimate.
  telemetry 报真实 token/limit 或 `unavailable`；不得估算。

Example checks / 示例检查:

```bash
printf '%s\n' '{"prompt":"run validation and summarize test evidence","phase":"validation"}' \
  | python3 hooks/model_router.py

printf '%s\n' '{"prompt":"review this architecture migration plan","phase":"review"}' \
  | python3 hooks/model_router.py
```

## Extraction Plan / 抽取计划

### Phase 1: Public Core Repo / Phase 1：公开核心仓库

Create `delivery-harness-framework` with public project files, generic skill,
runtime docs, schemas, helper scripts, templates, evals, `DHF_PACKET` schema,
validator, CI, and example adapter.

创建 `delivery-harness-framework`，包含公开项目文件、通用 skill、runtime 文档、schema、
helper scripts、templates、eval、`DHF_PACKET` schema、validator、CI 和 adapter 示例。

Phase 1 gate / Phase 1 gate:

```bash
python3 test_runner.py
git diff --check
python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav
python3 scripts/validate_dhf_packet.py examples/packets/basic.json
```

### Phase 2: Pinned Consumer / Phase 2：Pinned Consumer

Make `MyCodexEnv` consume a pinned DHF release or source snapshot and run parity,
eval, public-nav, runtime-sync, and rollback gates.

让 `MyCodexEnv` 消费 pinned DHF release 或 source snapshot，并运行 parity、eval、
public-nav、runtime-sync 和 rollback gate。

### Phase 3: Adapter Contract / Phase 3：Adapter 合同

Define how project repos add `AGENTS.md`, repo-specific lifecycle skill,
source-of-truth docs, verification gates, lane safety boundaries, and optional
public docs.

定义项目仓库如何添加 `AGENTS.md`、repo-specific lifecycle skill、source-of-truth docs、
verification gates、lane safety boundaries 和可选 public docs。

### Phase 4: Installer And Upgrade / Phase 4：安装与升级

Provide one idempotent install/update path that prints changed surfaces, refuses
unknown overwrites, and emits a verification command.

提供一个幂等 install/update 路径：打印 changed surfaces、拒绝未知覆盖、输出验证命令。

## Risks And Controls / 风险与控制

Risks / 风险:

- Version drift between independent DHF and `MyCodexEnv`.
  独立 DHF 和 `MyCodexEnv` 之间版本漂移。
- Over-generalizing adapters until the core becomes abstract but unusable.
  adapter 过度泛化，导致 core 抽象但不好用。
- Duplicating gstack responsibilities instead of routing to specialist skills.
  重复 gstack 职责，而不是路由给 specialist skill。
- Token regressions from loading the full framework too often.
  频繁加载完整框架导致 token 回归。
- Security regressions from public examples normalizing secrets or live systems.
  公开示例错误地正常化 secret 或 live system。
- CI mismatch with MyCodexEnv-only runtime checks.
  独立仓库与 MyCodexEnv 专属 runtime 检查不匹配。

Controls / 控制:

- Keep the core generic and adapter-free.
  core 保持通用，不内置 adapter。
- Use evals to enforce negative routing and forbidden-load boundaries.
  用 eval 强制 negative routing 和 forbidden-load boundary。
- Keep `MyCodexEnv` as pinned reference consumer until extraction is boring.
  在抽取稳定前，`MyCodexEnv` 保持 pinned reference consumer。
- Add `DHF_PACKET` schema before public installer.
  公开 installer 前先添加 `DHF_PACKET` schema。
- Require compact verification evidence before completion claims.
  完成声明前必须有紧凑验证证据。
- Keep local evidence logs out of Git.
  本地 evidence log 不进 Git。
- Publish "what this project does not own".
  发布“本项目不负责什么”说明。

## Recommended Next Slice / 推荐下一切片

Write:

`docs/plans/2026-06-15-dhf-independent-core-requirements.md`

编写：

`docs/plans/2026-06-15-dhf-independent-core-requirements.md`

It should define / 它应定义:

- exact files to copy, adapt, and exclude / 要复制、改造、排除的精确文件
- source checkout installer contract / source checkout installer 合同
- consumer-side `dhf_doctor.py` / consumer 侧 `dhf_doctor.py`
- `validate_dhf_packet.py` / `validate_dhf_packet.py`
- `compare_dhf_core_snapshot.py` / `compare_dhf_core_snapshot.py`
- `docs/dhf-core-pin.json` / `docs/dhf-core-pin.json`
- CI gate / CI gate
- rollback plan / rollback plan

Validation / 验证:

```bash
python3 scripts/harness_requirements.py validate docs/plans/2026-06-15-dhf-independent-core-requirements.md
git diff --check
```

Do not create the GitHub repo until that requirements artifact validates and the
split boundary survives review.

在该 requirements artifact 通过验证且拆分边界经受 review 前，不创建 GitHub repo。

## Review Results / 评审结果

Codex committee round 1 / Codex 委员会第一轮:

- Result / 结果: fail at target `10/10` / 未达 `10/10`
- Ratings / 评分: three domains all `8/10` / 三个领域均 `8/10`
- Revisions applied / 已应用修订:
  public project contract, boundary matrix, fresh repo self-test, consumer
  adoption path, pinned-consumer contract, `DHF_PACKET`, budgets, model-router
  protocol, Headroom constraints, Phase 1 gates.
  公开项目合同、边界矩阵、全新仓库自测、consumer 采用路径、pinned-consumer 合同、
  `DHF_PACKET`、预算、model-router 协议、Headroom 约束、Phase 1 gates。

Claude CLI review / Claude CLI 评审:

- Result / 结果: `continue`, `9/10`, threshold fail / `continue`，`9/10`，未达阈值
- Skill access / skill 访问:
  read `/Users/kezheng/.claude/skills/committee-review-loop/SKILL.md`
  and this artifact read-only.
  只读读取 `/Users/kezheng/.claude/skills/committee-review-loop/SKILL.md` 和本文档。
- Must-fix findings / 必修问题:
  broken consumer path, budget numbers without measurement instrumentation,
  and generic Level 1 coupling to `--codex-home`.
  consumer 路径错误、预算数字缺测量工具、generic Level 1 耦合 `--codex-home`。
- Revisions applied / 已应用修订:
  absolute `/tmp/delivery-harness-framework` source path, budget measurement
  caveat and `measure_dhf_invocation.py` target, portable Level 1 `.dhf/scripts`
  examples, and MyCodexEnv-only `verify_codex_env.sh` scope.
  绝对 `/tmp/delivery-harness-framework` source path、预算测量说明和
  `measure_dhf_invocation.py` 目标、portable Level 1 `.dhf/scripts` 示例，以及
  `verify_codex_env.sh` 仅限 MyCodexEnv。

Codex post-Claude re-review / Codex 对 Claude 反馈后的复审:

- Open-source product strategy / 开源产品策略: `10/10`, pass, stop
- Harness engineering correctness / Harness engineering 正确性: `10/10`, pass, stop
- Token efficiency and runtime performance / Token 效率与 runtime 性能: `10/10`, pass, stop

## Verification Receipts / 验证记录

- command: `python3 test_runner.py`
  - exit_code: 0
  - key_output: `ran=58 passed=58 skipped=0 failed=0`; `[PASS] all tests`
  - timestamp: `2026-06-15T18:13:33-04:00`
  - 中文：完整仓库测试通过，58 项通过，0 项失败。
- command: `git diff --check`
  - exit_code: 0
  - key_output: no whitespace errors
  - timestamp: `2026-06-15T18:12:50-04:00`
  - 中文：未发现 whitespace 或 conflict marker 问题。
- command: `python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav`
  - exit_code: 0
  - key_output: `surfaces manifest consistent`
  - timestamp: `2026-06-15T18:12:50-04:00`
  - 中文：runtime surface manifest 与 public nav 检查一致。
