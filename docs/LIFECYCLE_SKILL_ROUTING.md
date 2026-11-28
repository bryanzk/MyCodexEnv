<!-- 修改本文件后需重新生成 HTML 版 -->
# Lifecycle And Skill Routing

> **DHF_PUBLIC_STATUS_V1 · 2026-08-22:** This router documents the current
> profile-aware source architecture. Source availability does not prove runtime
> activation or publication. See the canonical status in
> [English](./dhf-architecture-status-en.html) or
> [中文](./dhf-architecture-status-cn.html). The source and local managed runtime
> implement light/standard/governed profiles; local runtime promotion was freshly observed at 2026-08-22T01:06:20Z and does not prove production enforcement.

## Purpose

This document explains which workflows MyCodexEnv covers, how the Harness
Runtime maps work to lifecycle stages, and which Codex skills should be used at
each stage.

MyCodexEnv has three layers:

- Runtime layer: `AGENTS.md`, hooks, tool policy, evidence schema, verification
  scripts, and checkpoint helpers.
- Router layer: `delivery-harness-framework`, which reads durable state,
  classifies the lifecycle stage, and selects the next workflow.
- Specialist layer: repo-specific lifecycle adapters, local
  planning/testing/review skills, and deterministic helper scripts.

The generic lifecycle skill should stay generic. Project-only paths, fixtures,
commands, smoke matrices, and business safety boundaries belong in repo-specific
adapter skills.

## DHF Source-Stage Contract Mirror

Canonical profile and Result Invariant semantics live in
`codex/skills/delivery-harness-framework/SKILL.md`; routing and rollout-switch
behavior live in `codex/hooks/dhf_preprompt.py`.

- Governance profiles are `light`, `standard`, and `governed`.
- Generic injection requires explicit generic activation; an ordinary
  non-project prompt stays continue-only. opt-out is evaluated before every
  route. The dispatcher recognizes the ShipQ project boundary and directly lazy-delegates
  (lazy delegation);
  generic DHF must not recover, read shared state, or pre-classify before the ShipQ adapter
  owns the task.
- Every completion preserves exactly `result`, `scope_and_constraints`,
  `verification_receipt`, and `remaining_risk_or_next_action`; profile-specific
  ceremony is conditional rather than repeated by default.
- The source simplified route uses the exact enabled value
  `DHF_PREPROMPT_SIMPLIFIED_PROFILES=1`; the repo-source default is `simplified`
  after the second final-fix gate. Values `0`, `false`, `off`,
  and `legacy` explicitly roll back. Runtime state is evidence-dependent: the
  live boundary accepts either a source-stage unsynced state or an exact
  promoted state and rejects drift. `source_stage_unsynced` proves source
  acceptance without runtime activation; `runtime_promoted` is required before
  claiming managed runtime activation.

## Visual Guides

- `docs/dhf-architecture-status-en.html`: canonical English source/runtime/publication status.
- `docs/dhf-architecture-status-cn.html`: canonical Chinese source/runtime/publication status.
- `docs/index.html`: English canonical Delivery Harness Framework public landing page for GitHub Pages.
- `docs/index-zh.html`: 中文 Delivery Harness Framework 公开文档首页。
- `docs/index-en.html`: English Delivery Harness Framework public landing page for English readers.
- `docs/dhf-workflow-skills-cn.html`: 中文 DHF workflow skills matrix，逐步列出每个阶段使用的 skill、职责说明和 GitHub 源码链接。
- `docs/dhf-workflow-skills-en.html`: English DHF workflow skills matrix with stage-by-stage skill explanations and GitHub source links.
- `docs/delivery-harness-beginner-guide-cn.html`: 中文 beginner guide，用一句话定义、三层架构、五步流程、例子和术语表解释 Delivery Harness Framework。
- `docs/dhf-memory-map.html`: 中文 DHF 航空运营记忆地图，用一条航线串联 CAP、BRIDGE、AIRCRAFT、SAFE、PROTECT、RECOVER 与 TRUST。
- `docs/dhf-memory-map-en.html`: English DHF airline-operations memory map covering CAP, BRIDGE, AIRCRAFT, SAFE, PROTECT, RECOVER, and TRUST.
- `docs/dhf-social-card.html`: reproducible 1200×630 public sharing-card source; rendered output is `docs/dhf-social-card.png`.
- `docs/dhf-engineering-notes-cn.html`: 中文工程笔记，覆盖会话容量治理、版本转移与可执行政策文本。
- `docs/dhf-engineering-notes-en.html`: English engineering notes on compaction governance, version transitions, and executable policy text.
- `docs/dhf-for-product-and-field-cn.html`: 中文产品与现场交付视角，用图解说明交付保证。
- `docs/dhf-for-product-and-field-en.html`: English product and field-engineering view of the delivery guarantees, diagram-first.
- `docs/delivery-harness-beginner-guide-en.html`: English beginner guide covering completion evidence and handoff basics.
- `docs/lifecycle-skill-routing-en.html`: published HTML rendering of this routing contract.
- `docs/project-lifecycle-harness-flow-skills-en.html`: archived English skill/helper routing visual; the status-style map is the current path.
- `docs/dhf-governance-decision-flow-cn.html`: 中文治理判定流程图，展示单次工具调用的 lane 门禁、阶段能力判定、拒绝边与验证失败回边。
- `docs/dhf-governance-decision-flow-en.html`: English governance decision flow for a single tool call: lane gate, phase capability check, refusal edges, and the verification back-edge.
- `docs/dhf-spec-cn.html` / `docs/dhf-spec-en.html`: DHF 规范的中英文公开页面；权威来源是 `docs/dhf-spec.md`，英文页是译本。
- `docs/project-lifecycle-harness-flow-cn.html`: 中文纵向主流程图，帮助用户从入口、状态恢复、阶段分类一路看到验证、发布和交接。
- `docs/project-lifecycle-harness-flow-en.html`: English lightweight vertical lifecycle flow; the fuller English equivalent of the Chinese main flow is the status-style skill routing map.
- `docs/project-lifecycle-harness-flow-skills.html`: 中文 skill/helper 路由速查页，帮助用户理解每个生命周期阶段应使用哪个 skill，以及 helper 的执行职责。
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`: 新版中文 Delivery Harness Framework skill/helper 路由图，使用和 LinkedIn 素材一致的状态风格。
- `docs/project-lifecycle-harness-flow-skills-en-status-style.html`: English status-style Delivery Harness Framework flow map for public sharing.
- `docs/dhf-context-engineering-cn.html`: 中文 DHF 上下文工程指南，讲清受治理的上下文供应链。
- `docs/dhf-context-engineering-en.html`: English guide to the governed DHF context supply chain.
- `docs/dhf-protect-seven-components-cn.html`: 中文 PROTECT 图，逐个说明七个受 WAL 保护的运行时晋升目标。
- `docs/dhf-protect-seven-components-en.html`: English PROTECT map for the seven WAL-protected runtime promotion targets.
- `docs/dhf-value-evidence-en.html` / `docs/dhf-value-evidence-cn.html`: 中英文 Evidence 总入口，按客户价值、证据成熟度、演进、控制、案例、恢复和当前边界组织内容。
- `docs/dhf-best-care-recover-en.html` / `docs/dhf-best-care-recover.html`: 中英文 BEST / CARE / RECOVER 记忆与恢复辅助页，不再承担站点 Hub。
- `docs/dhf-data-business-value-explainer-en.html` / `docs/dhf-data-business-value-explainer.html`: 中英文 SAFE → TRUST 通用控制与客户价值页面。
- `docs/dhf-safe-data-ai-comparison-en.html` / `docs/dhf-safe-data-ai-comparison.html`: 中英文辅助分析页，对比数据与 AI 架构和 DHF 如何复用 SAFE；不构成生产或采用证明。
- `docs/dhf-shipq-development-history-en.html` / `docs/dhf-shipq-development-history.html`: 中英文 DHF 演进证据，从 ShipQ 业务阻塞讲到受治理 enforcement。
- `docs/dhf-case-safe-mapping-en.html` / `docs/dhf-case-safe-mapping.html`: 中英文真实案例 SAFE 控制映射。
- `docs/dhf-examples-three-lenses-en.html` / `docs/dhf-examples-three-lenses.html`: 中英文十案例三种讲法。
- `docs/dhf-examples-three-lenses-safe-en.html` / `docs/dhf-examples-three-lenses-safe.html`: 中英文三镜头案例与 SAFE 控制叠加页。
- `docs/shipq-dhf-safe-controlled-recovery-en.html` / `docs/shipq-dhf-safe-controlled-recovery.html`: 中英文 ShipQ Google Docs 受控恢复证据页。
- `docs/shipq-dhf-incident-recovery-memory-map-en.html` / `docs/shipq-dhf-incident-recovery-memory-map.html`: 中英文 ShipQ 事故恢复记忆图。

Evidence 语言边界：英文 Hub 和普通相关链接只进入英文页面，中文 Hub 和普通相关链接只进入中文页面；每个页面只通过显式语言切换进入另一语言 twin。Evidence 解释耐久价值与证明，Architecture Status 负责带日期的当前状态。

Evidence 记忆合同：Hub 使用 `CAP → BRIDGE × SAFE → TRUST` 作为主记忆脊柱，并把 `RECOVER` 表达为失败后的条件分支。`BEST` 是系统、架构和演进视角；`CARE` 是实践、案例和恢复视角。普通子页面只突出与职责相关的最多三个核心词，中英文 twin 的关键词和视角组合必须一致。

## Related Documentation

- `README.md`: top-level quick start and Harness Runtime overview.
- `docs/repo-index.md`: low-token repo navigation and runtime surface index.
- `docs/index.html`: Chinese public Delivery Harness Framework docs entry.
- `docs/index-en.html`: English public Delivery Harness Framework docs entry.
- `docs/dhf-workflow-skills-cn.html`: Chinese workflow skill inventory with GitHub links.
- `docs/dhf-workflow-skills-en.html`: English workflow skill inventory with GitHub links.
- `docs/delivery-harness-beginner-guide-cn.html`: beginner-oriented Chinese explanation.
- `docs/HARNESS_RUNTIME.md`: lifecycle, evidence, checkpoint, permission, and subagent contracts.
- `docs/AGENT_HARNESS_STATUS.md`: Agent Harness workflow/infra status map.
- `docs/CODEX_ENV_REPRODUCTION.md`: Codex + Claude environment reproduction guide.
- `docs/project-lifecycle-harness-flow-cn.html`: Chinese vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-skills.html`: Chinese lifecycle skill/helper routing visual guide.
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`: current styled Chinese lifecycle skill/helper routing visual guide.

## Covered Workflows

| Workflow | What It Covers | Primary Entry |
| --- | --- | --- |
| Environment reproduction | Clone, bootstrap, sync Codex/Claude homes, install pinned prerequisites, verify local setup. | `README.md`, `bootstrap.sh`, `scripts/verify_codex_env.sh` |
| Global rules and repo routing | Keep cross-repo Codex rules in one source and route repo-local constraints through `AGENTS.md`. | `codex/AGENTS.md`, root `AGENTS.md`, `scripts/manage_agents.py` |
| Skill synchronization | Copy ordinary repo-managed skills into `~/.codex/skills/`. Skill families retired on 2026-11-27 (SHI-637) are no longer deployed; their runtime copies are left in place and disabled in `config.toml`. | `scripts/sync_codex_home.sh` |
| Harness lifecycle routing | Recover state, classify phase, choose generic or repo-specific workflow, define gates. | `delivery-harness-framework` |
| Requirements and planning | Capture success criteria, scope, constraints, domain docs, ADR conflicts, vertical slices, risks, and validation gates before implementation. | `planner`, `req-to-dev`, `task-flow-orchestrator`, `scripts/harness_requirements.py` |
| Backlog-ready issue/spec authoring | Turn vague implementation intent into a bounded issue or executable spec before coding starts. | `to-spec`, `to-tickets`, `delivery-harness-framework` |
| Development execution | Make scoped repo changes, use tests first when behavior changes, preserve unrelated user work. | `tdd-guide`, `atdd-guide`, repo-local workflow |
| Validation and evidence | Run fresh tests/checks and record `command`, `exit_code`, `key_output`, `timestamp`. | `verification-loop`, `scripts/harness_evidence.py`, `scripts/harness_report.py` |
| Review and QA | Inspect diffs, browser behavior, security/privacy boundaries, and user-visible regressions. | `code-review`, `review-swarm`, `chrome-devtools-browser`, `playwright`, `security-reviewer` |
| Committee review loop | Run an explicit expert-committee scoring loop with a separate revision worker until a target rating is met. | `committee-review-loop` |
| Ship and deployment | Commit/PR/release/deploy only when explicitly requested and verified. | repo release workflow, `pr` |
| Handoff and recovery | Append state, preserve next safe task, recover without chat history, and hand off user-facing context. | `scripts/harness_checkpoint.py`, `scripts/harness_recover.py`, `handoff` |
| Documentation release | Keep README/docs aligned with shipped behavior and skill/runtime changes; generate missing docs when requested. | `doc-updater` |

## Lifecycle Stage Map

| Stage | Signals | Default Permission | Skill Or Helper | Purpose |
| --- | --- | --- | --- | --- |
| `research` | Unknown repo, stale handoff, unclear source ownership, missing context. | Read-only. | `delivery-harness-framework`, `scripts/harness_recover.py`, `scripts/harness_env_probe.py` | Read durable sources and recover the next safe task before acting. |
| `requirements` | Goal, audience, acceptance criteria, scope, constraints, or domain language are unclear. | Read-only. | `planner`, `req-to-dev`, `scripts/harness_requirements.py` | Turn ambiguity into success criteria, read `CONTEXT.md` / `CONTEXT-MAP.md` and relevant ADRs when present, then validate requirements artifacts before treating them as source of truth. |
| `planning` | The user wants a backlog-ready GitHub issue, ticket, or executable spec before implementation begins. | Read-only by default. | `to-spec`, `to-tickets`, `delivery-harness-framework` | Preserve runtime state, lane boundaries, and validation gates while turning vague intent into a bounded spec or issue. |
| `planning` | Architecture, API shape, migration, runtime, data flow, cross-module decisions, or multi-step work breakdown. | Read-only by default. | `planner`, `codebase-design`, `task-flow-orchestrator` | Produce an implementation plan, vertical slice breakdown, risk list, and validation gate before edits. |
| `development` | Acceptance criteria are clear and touched files/modules are bounded. | Scoped writes. | `tdd-guide`, `atdd-guide`, repo workflow, scoped worker agents | Implement the change with tests appropriate to the risk. |
| `validation` | Work is implemented or docs/config changed and needs fresh evidence. | Tests/checks by default. | `verification-loop`, `scripts/harness_report.py`, `scripts/verify_codex_env.sh` | Prove the result with fresh command output and required evidence fields. |
| `review` | Diff exists, work is near handoff/PR/landing, or user asks for review. | Read-only by default. | `code-review`, `review-swarm`, `security-reviewer` | Find bugs, regressions, security risks, and missing tests before shipping. |
| `review` | User explicitly asks for a committee, expert panel, subagent reviewer/worker split, rating loop, or improvement until a score such as `9.5/10`. | Committee read-only; revision worker scoped writes. | `committee-review-loop`, `scripts/harness_agent_team.py` | Keep ordinary review routes separate while iterating committee findings into bounded, verified revisions. |
| `ship` | User requests commit, push, PR, merge, release, deploy, or production verification. | Requested release actions only. | repo release workflow, `pr` | Complete release steps, verify deployment, and preserve rollback context. |
| `handoff` | Session is ending, task crosses phases, work spans sessions, next safe task must survive, or the user asks to save/restore working context. | Docs/state only. | `scripts/harness_checkpoint.py`, `handoff`, `codex-retrospective` | Append harness checkpoint state, capture blockers, preserve resumable user context, and leave a recoverable next step. |

## Specialist Skill Map

| Skill | Use For | Notes |
| --- | --- | --- |
| `delivery-harness-framework` | Generic startup/resume routing, durable state reads, phase classification, helper selection, evidence expectations. | For generic activation only; it directly delegates at the project boundary before generic recovery, shared-state reads, or phase selection. |
| repo-specific lifecycle harnesses | Project paths, local commands, business fixtures, deployment topology, smoke matrices. | The dispatcher directly lazy-delegates at the recognized project boundary; the adapter owns all project phase and state classification. |
| `grilling` | Product framing, user value, scope, and requirement interrogation. | Use when product judgment is the work and the problem statement is still fluid. |
| `to-spec` / `to-tickets` | Backlog-ready specs and tracer-bullet tickets with explicit acceptance criteria before implementation begins. | Use when the work needs a durable spec artifact rather than immediate coding. |
| `codebase-design` | Deep-module interface design and seams. | Use with `planner` on engineering plans. |
| `critique` / `frontend-design` | UX structure, visual direction, and design acceptance. | Use before UI implementation or major design changes. |
| `chrome-devtools-browser` / `playwright` | Browser QA, screenshots, console/network checks, and multi-step page flows. | Use for user-facing web behavior. |
| `code-review` | Review of the changes since a fixed point along standards and spec axes. | Use near PR, handoff, or ship. |
| `pr` | PR body writing. | Release actions themselves follow the repo's own workflow. |
| `handoff` | Compact the session into a handoff document. | Use alongside, not instead of, `scripts/harness_checkpoint.py`. |
| `codex-retrospective` | Evidence-backed review of recent Codex history. | Use for time-windowed retrospectives. |
| `security-reviewer` | Code-level security review for validation, auth, injection, secret leakage, error disclosure. | Good for narrower security audits. |
| `review-swarm` | Parallel read-only review across behavioral/security/performance/test risks. | Use when the user asks for multi-agent review. |
| `committee-review-loop` | Explicit expert-committee/subagent loops with scoring, revision briefs, and a target rating such as `9.5/10`. | Do not use for one-off design/code/QA review; preserve read-only committee roles and bounded revision-worker write sets. |
| `doc-updater` | Targeted docs/codemap/README updates for feature, API, or structure changes. | Use for repo-local documentation maintenance. |
| `verification-loop` | Build/static/test/coverage/security verification before completion. | Use when a full validation loop is required. |
| `tdd-guide` | Test-first implementation for behavior changes and bug fixes. | Use before writing production code. |
| `atdd-guide` | Acceptance-test-first workflow for business-facing criteria. | Use when external behavior and acceptance scenarios matter. |
| `planner` | Requirement analysis, architecture sorting, task decomposition, risk detection. | Use for complex features and refactors. |
| `task-flow-orchestrator` | Ordered execution across Karpathy, Planner, TDD, and verification workflows. | Use when the task needs workflow sequencing. |
| `skill-evaluator` | Skill existence, routing, eval matrix, baseline comparison, off-target load diagnosis. | Use before expanding or revising critical skills, especially when upstream workflow text changed and routing precision may drift. |
| `visual-explainer` | Self-contained HTML diagrams, flowcharts, architecture views, tables, and visual explanations. | Use for visual documentation and system explanations. |

## Skillset Gap Routes

| Pattern | Lifecycle Slot | Harness Rule |
| --- | --- | --- |
| Domain docs and ADRs | `requirements`, `planning` | Read `CONTEXT.md`, `CONTEXT-MAP.md`, and relevant ADR files when present; use their domain vocabulary and flag conflicts instead of inventing terms. |
| Vertical slices | `planning`, `development` | Break multi-step work into independently verifiable vertical slice units; mark each unit `AFK` when a worker can proceed from durable context or `HITL` when human judgment is required. |
| Feedback loop first | `debug/investigation` | Establish a runnable feedback loop before hypotheses or fixes: failing test, CLI fixture, curl script, browser check, trace replay, throwaway harness, fuzz loop, or differential run. |
| Prototype learning | `planning` | Use a throwaway prototype only to answer one named logic, state, interface, or UI question; delete it or capture the durable decision before handoff. |
| Durable agent brief | `planning`, `development`, `handoff` | Use `docs/templates/harness-agent-brief.md` for a durable agent brief when worker contracts need current behavior, desired behavior, key interfaces, acceptance criteria, and out of scope. |
| Expert committee rating loop | `review`, `development` | Route only explicit committee/subagent rating loops to `committee-review-loop`; capture expert domains, target rating, revision worker scope, verification gate, and stopping condition. |
| Deep module review | `planning`, `review` | Prefer a deep module shape with small public interfaces and meaningful behavior behind them; use the interface as the test surface and preserve locality/leverage. |

**Writing Skill Routing**

User-invoked writing routes use the explicit `$skill-name` form. Automatic routes are evaluated as direct task prompts in fresh sessions; never wrap them in a meta-prompt that asks the model to predict its route.

| User intent | Primary route | Composition or boundary |
| --- | --- | --- |
| New technical article, blog post, professional announcement, ticket, postmortem, or ordinary professional prose | No writing skill | Write directly from the supplied facts; do not invent specifics. |
| Diagnose AI-writing patterns without editing | No writing skill | Report only; no edits. |
| Minimally revise an existing draft | No writing skill; `humanizer` only when explicitly requested | Preserve facts, structure, voice, and intent. |
| Explicit `humanizer` request | `humanizer` | User-invoked legacy fallback for minimal surface editing; never an automatic prose route. |
| Explore raw material | `writing-fragments` | User-invoked workshop stage; do not interrupt it. |
| Shape a fixed fragment pile into an argument | `writing-shape` | User-invoked workshop stage. |
| Build an article beat by beat | `writing-beats` | Preserve its interactive sequence. |
| Explicit Guanshiyin four-dimension Chinese writing | `guanshiyin-writing` | This explicit method wins. |
| Job posting plus application package | `job-application-packager` | It owns intake, evidence, artifacts, and PDF workflow. |
| Customer-facing agent reliability case study | Evidence/domain skill | Evidence boundaries stay authoritative; prose cannot enlarge claims. |
| Code, debugging, review, data analysis, or another non-writing task using “write” | Existing non-writing skill | Do not load a writing skill merely because the prompt says “write”. |

## Runtime Helper Map

| Helper | Lifecycle Slot | Purpose |
| --- | --- | --- |
| `scripts/harness_recover.py` | `research`, `handoff` | Read repo index, harness state, git status/log, and local evidence summary to recover current phase and next safe task. |
| `scripts/harness_env_probe.py` | `research`, `validation` | Report observable Codex runtime config, hooks, tool policy, evidence schema, sandbox fields, and approval fields. |
| `scripts/harness_requirements.py` | `requirements` | Validate requirements artifacts before planning or development treats them as source of truth. |
| `scripts/harness_agent_team.py` | `planning`, `development` | Validate agent role, scope, write set, verification command, protected harness-state boundaries, and optional durable worker brief before parallel worker dispatch. |
| `scripts/harness_evidence.py` | `validation` | Validate and append structured local evidence events. |
| `scripts/harness_report.py` | `validation`, `review`, `handoff` | Summarize local JSONL evidence by phase, event type, time window, or JSON output. |
| `scripts/harness_checkpoint.py` | `handoff`, phase transitions | Append checkpoint entries to `docs/harness-state.md` with changed surfaces, verification, blockers, and next safe task. |
| `scripts/verify_codex_env.sh` | `validation` | Verify Codex/Claude runtime sync, managed skills, hooks, runtime policies, and supported Codex CLI version. |
| `python3 test_runner.py` | `validation` | Main repo regression suite for sync, hooks, runtime helpers, skill boundaries, eval fixtures, and docs/config behavior. |

## Routing Rules

- Activate `delivery-harness-framework` only through the explicit generic
  activation boundary or a matching repo adapter; ordinary prompts continue.
- Prefer repo-specific lifecycle harnesses when a known project adapter owns the
  business domain.
- Prefer the specialist skills in the map above for product review, spec
  authoring, engineering and design planning, browser QA, security review,
  diff review, documentation, handoff, and retrospectives. DHF still owns repo
  state, lane, checkpoint, and validation boundaries. gstack was retired on
  2026-11-27 (SHI-637); do not route to it.
- Prefer deterministic helper scripts when the runtime already provides one;
  do not reimplement their parsing or validation manually.
- Use `verification-loop` or repo-native commands before any completion claim.
- Keep `docs/harness-state.md` as an integrator-owned checkpoint surface for
  delegated worker plans; workers should report or write slice-local handoff
  artifacts instead. Single-line main-agent tasks may still append verified
  checkpoints directly.
- Use `harness_checkpoint.py append` only for a matching governed escalation,
  such as resume/handoff, ownership conflict, private data, remote/release,
  multi-agent, architecture conflict, or malformed/retained governed state.

## Evidence Standard

Any claim that work is complete, fixed, or passing must include fresh evidence:

```text
command
exit_code
key_output
timestamp
```

If a command is blocked by credentials, network, remote approval, sandbox, or an
external dependency, report the exact blocker and the safest next command.
