# Lifecycle And Skill Routing

## Purpose

This document explains which workflows MyCodexEnv covers, how the Harness
Runtime maps work to lifecycle stages, and which Codex/gstack skills should be
used at each stage.

MyCodexEnv has three layers:

- Runtime layer: `AGENTS.md`, hooks, tool policy, evidence schema, verification
  scripts, and checkpoint helpers.
- Router layer: `project-lifecycle-harness`, which reads durable state,
  classifies the lifecycle stage, and selects the next workflow.
- Specialist layer: repo-specific lifecycle adapters, gstack skills, local
  planning/testing/review skills, and deterministic helper scripts.

The generic lifecycle skill should stay generic. Project-only paths, fixtures,
commands, smoke matrices, and business safety boundaries belong in repo-specific
adapter skills.

## Visual Guides

- `docs/index.html`: Delivery Harness public landing page for GitHub Pages.
- `docs/delivery-harness-beginner-guide-cn.html`: 中文 beginner guide，用一句话定义、三层架构、五步流程、例子和术语表解释 Delivery Harness。
- `docs/project-lifecycle-harness-flow-cn.html`: 中文纵向主流程图，帮助用户从入口、状态恢复、阶段分类一路看到验证、发布和交接。
- `docs/project-lifecycle-harness-flow-skills.html`: 中文 skill/helper 路由速查页，帮助用户理解每个生命周期阶段应使用哪个 skill，以及 helper 的执行职责。
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`: 新版中文 Delivery Harness skill/helper 路由图，使用和 LinkedIn 素材一致的状态风格。
- `docs/project-lifecycle-harness-flow-skills-en-status-style.html`: English status-style Delivery Harness flow map for public sharing.

## Related Documentation

- `README.md`: top-level quick start and Harness Runtime overview.
- `docs/repo-index.md`: low-token repo navigation and runtime surface index.
- `docs/index.html`: public Delivery Harness docs entry.
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
| Skill synchronization | Keep `codex/skills/*` as source of truth and copy managed skills into `~/.codex/skills/*`. | `scripts/sync_codex_home.sh` |
| Harness lifecycle routing | Recover state, classify phase, choose generic/repo-specific/gstack workflow, define gates. | `project-lifecycle-harness` |
| Requirements and planning | Capture success criteria, scope, constraints, risks, and validation gates before implementation. | `planner`, `req-to-dev`, `task-flow-orchestrator`, `scripts/harness_requirements.py` |
| Development execution | Make scoped repo changes, use tests first when behavior changes, preserve unrelated user work. | `tdd-guide`, `atdd-guide`, repo-local workflow |
| Validation and evidence | Run fresh tests/checks and record `command`, `exit_code`, `key_output`, `timestamp`. | `verification-loop`, `scripts/harness_evidence.py`, `scripts/harness_report.py` |
| Review and QA | Inspect diffs, browser behavior, security/privacy boundaries, and user-visible regressions. | `gstack-review`, `code-reviewer`, `gstack-qa`, `security-reviewer` |
| Ship and deployment | Commit/PR/release/deploy/canary only when explicitly requested and verified. | `gstack-ship`, `gstack-land-and-deploy`, `gstack-canary` |
| Handoff and recovery | Append state, preserve next safe task, recover without chat history. | `scripts/harness_checkpoint.py`, `scripts/harness_recover.py` |
| Documentation release | Keep README/docs aligned with shipped behavior and skill/runtime changes. | `gstack-document-release`, `doc-updater` |

## Lifecycle Stage Map

| Stage | Signals | Default Permission | Skill Or Helper | Purpose |
| --- | --- | --- | --- | --- |
| `research` | Unknown repo, stale handoff, unclear source ownership, missing context. | Read-only. | `project-lifecycle-harness`, `scripts/harness_recover.py`, `scripts/harness_env_probe.py` | Read durable sources and recover the next safe task before acting. |
| `requirements` | Goal, audience, acceptance criteria, scope, or constraints are unclear. | Read-only. | `planner`, `req-to-dev`, `scripts/harness_requirements.py` | Turn ambiguity into success criteria and validate requirements artifacts before treating them as source of truth. |
| `planning` | Architecture, API shape, migration, runtime, data flow, or cross-module decisions. | Read-only by default. | `gstack-plan-eng-review`, `planner`, `task-flow-orchestrator` | Produce an implementation plan, risk list, and validation gate before edits. |
| `development` | Acceptance criteria are clear and touched files/modules are bounded. | Scoped writes. | `tdd-guide`, `atdd-guide`, repo workflow, scoped worker agents | Implement the change with tests appropriate to the risk. |
| `validation` | Work is implemented or docs/config changed and needs fresh evidence. | Tests/checks by default. | `verification-loop`, `scripts/harness_report.py`, `scripts/verify_codex_env.sh` | Prove the result with fresh command output and required evidence fields. |
| `review` | Diff exists, work is near handoff/PR/landing, or user asks for review. | Read-only by default. | `gstack-review`, `code-reviewer`, `review-swarm`, `security-reviewer` | Find bugs, regressions, security risks, and missing tests before shipping. |
| `ship` | User requests commit, push, PR, merge, release, deploy, or production verification. | Requested release actions only. | `gstack-ship`, `gstack-land-and-deploy`, `gstack-canary` | Complete release steps, verify deployment, and preserve rollback context. |
| `handoff` | Session is ending, task crosses phases, work spans sessions, or next safe task must survive. | Docs/state only. | `scripts/harness_checkpoint.py`, `gstack-retro`, `gstack-learn` | Append checkpoint state, capture blockers, and leave a recoverable next step. |

## Specialist Skill Map

| Skill | Use For | Notes |
| --- | --- | --- |
| `project-lifecycle-harness` | Generic startup/resume routing, durable state reads, phase classification, helper selection, evidence expectations. | Use first for complex or resumed work; delegate after phase selection. |
| repo-specific lifecycle harnesses | Project paths, local commands, business fixtures, deployment topology, smoke matrices. | These adapters take over after the generic router identifies a repo-specific boundary. |
| `gstack-plan-ceo-review` | Product framing, user value, scope, demo boundaries, strategic tradeoffs. | Use when product judgment is the work. |
| `gstack-office-hours` | Founder-style pressure testing, market/user/business clarity. | Useful before committing to a product direction. |
| `gstack-plan-eng-review` | Architecture, data model, API contract, migration, performance, test strategy. | Use before implementation on complex engineering plans. |
| `gstack-plan-design-review` | UX structure, visual direction, responsive behavior, design acceptance. | Use before UI implementation or major design changes. |
| `gstack-qa` | Browser QA, screenshots, console/network checks, responsiveness, accessibility smoke. | Use for user-facing web behavior. |
| `gstack-qa-only` | Report-only QA when fixes should not be applied automatically. | Keeps QA read-only. |
| `gstack-cso` | Infrastructure-first security and privacy review. | Use for auth, tokens, secrets, PII, or public/private boundaries. |
| `security-reviewer` | Code-level security review for validation, auth, injection, secret leakage, error disclosure. | Good for narrower security audits. |
| `gstack-review` | Pre-landing diff review and risk scan. | Use near PR, handoff, or ship. |
| `code-reviewer` | Local code review of staged or unstaged changes. | Use for focused findings with file/line references. |
| `review-swarm` | Parallel read-only review across behavioral/security/performance/test risks. | Use when the user asks for multi-agent review. |
| `gstack-ship` | Opinionated release workflow before PR/landing. | Only use when user asks to ship. |
| `gstack-land-and-deploy` | Merge and deploy workflow with post-deploy checks. | Requires explicit release/deploy intent. |
| `gstack-canary` | Post-deploy canary monitoring. | Use after deploy when live behavior must be watched. |
| `gstack-document-release` | Post-ship documentation update across README/docs/CHANGELOG/TODOS/VERSION. | Use when docs must reflect shipped behavior. |
| `doc-updater` | Targeted docs/codemap/README updates for feature, API, or structure changes. | Use for repo-local documentation maintenance. |
| `verification-loop` | Build/static/test/coverage/security verification before completion. | Use when a full validation loop is required. |
| `tdd-guide` | Test-first implementation for behavior changes and bug fixes. | Use before writing production code. |
| `atdd-guide` | Acceptance-test-first workflow for business-facing criteria. | Use when external behavior and acceptance scenarios matter. |
| `planner` | Requirement analysis, architecture sorting, task decomposition, risk detection. | Use for complex features and refactors. |
| `task-flow-orchestrator` | Ordered execution across Karpathy, Planner, TDD, and verification workflows. | Use when the task needs workflow sequencing. |
| `skill-evaluator` | Skill existence, routing, eval matrix, baseline comparison, off-target load diagnosis. | Use before expanding or revising critical skills. |
| `visual-explainer` | Self-contained HTML diagrams, flowcharts, architecture views, tables, and visual explanations. | Use for visual documentation and system explanations. |

## Runtime Helper Map

| Helper | Lifecycle Slot | Purpose |
| --- | --- | --- |
| `scripts/harness_recover.py` | `research`, `handoff` | Read repo index, harness state, git status/log, and local evidence summary to recover current phase and next safe task. |
| `scripts/harness_env_probe.py` | `research`, `validation` | Report observable Codex runtime config, hooks, tool policy, evidence schema, sandbox fields, and approval fields. |
| `scripts/harness_requirements.py` | `requirements` | Validate requirements artifacts before planning or development treats them as source of truth. |
| `scripts/harness_agent_team.py` | `planning`, `development` | Validate agent role, scope, write set, and verification command before parallel worker dispatch. |
| `scripts/harness_evidence.py` | `validation` | Validate and append structured local evidence events. |
| `scripts/harness_report.py` | `validation`, `review`, `handoff` | Summarize local JSONL evidence by phase, event type, time window, or JSON output. |
| `scripts/harness_checkpoint.py` | `handoff`, phase transitions | Append checkpoint entries to `docs/harness-state.md` with changed surfaces, verification, blockers, and next safe task. |
| `scripts/verify_codex_env.sh` | `validation` | Verify Codex/Claude runtime sync, managed skills, hooks, runtime policies, and supported Codex CLI version. |
| `python3 test_runner.py` | `validation` | Main repo regression suite for sync, hooks, runtime helpers, skill boundaries, eval fixtures, and docs/config behavior. |

## Routing Rules

- Start with `project-lifecycle-harness` when work is complex, resumed,
  cross-session, security-sensitive, release-facing, or ambiguous.
- Prefer repo-specific lifecycle harnesses when a known project adapter owns the
  business domain.
- Prefer gstack skills when the task is product review, engineering review,
  design review, browser QA, security review, ship, deploy, canary, release
  documentation, retro, or learning capture.
- Prefer deterministic helper scripts when the runtime already provides one;
  do not reimplement their parsing or validation manually.
- Use `verification-loop` or repo-native commands before any completion claim.
- Use `harness_checkpoint.py append` before ending long-running work, after a
  meaningful validated slice, or before risky remote/release actions.

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
