---
name: delivery-harness-framework
description: Use when starting, resuming, or taking over a complex software project task where Codex must inspect durable repo state or handoff files, classify the lifecycle stage, choose between generic, repo-specific, gstack, and verification workflows, or preserve checkpoint evidence.
---

# Delivery Harness Framework

## Overview

Use this as the generic lifecycle router before non-trivial project work. It
turns an ambiguous request into a staged workflow with explicit state, source of
truth, runtime probes, helper CLIs, verification evidence, and handoff rules.

If a repo-specific lifecycle harness exists, use this skill to confirm phase,
read shared runtime state, and then delegate. Keep this skill generic: do not
encode business repo paths, domain fixtures, private service names, or
project-only commands here.

## Lifecycle Ownership

- `delivery-harness-framework` owns cross-repo startup, state recovery, phase
  classification, helper routing, evidence requirements, and generic safety
  gates.
- A repo-specific lifecycle harness owns project paths, local commands, domain
  source-of-truth files, fixtures, deployment topology, and project-specific
  safety boundaries.
- gstack owns specialized lifecycle workflows: product critique, engineering
  plan review, design review, browser QA, security review, diff review, ship,
  land/deploy, canary monitoring, release documentation, retro, and learning
  capture.

## Runtime Surfaces

When a repo implements a harness runtime, prefer these surfaces after local
`AGENTS.md`:

- `docs/repo-index.md`: low-token map of source of truth, verification commands,
  runtime surfaces, and high-risk areas.
- `docs/harness-state.md`: append-only current phase, blockers, next safe task,
  latest verification, and checkpoint notes.
- `docs/HARNESS_RUNTIME.md`: contract for workflow, infra, evidence,
  checkpoints, guardrails, and agent teams.
- `docs/templates/harness-requirements.md`: requirements artifact template for
  complex work.
- `codex/runtime/tool-policy.json`: lifecycle-stage tool and permission policy.
- `codex/runtime/evidence.schema.json`: structured local evidence contract.
- `codex/hooks.json` and `codex/hooks/*`: runtime guard and observer hooks.

Runtime evidence should stay local by default, typically under a Codex home
evidence directory. Do not commit private transcripts, credentials, auth files,
or local evidence logs unless the user explicitly asks and the content is
sanitized.

## Helper Router

Prefer runtime helper CLIs when present. Fall back to manual inspection only
when a helper is missing, fails because its own required source is absent, or
the repo has not implemented the harness runtime.

| Need | Preferred Route | Use When |
| --- | --- | --- |
| Recover current phase and next safe task | `python3 scripts/harness_recover.py --repo-root "$(pwd)" --codex-home "$HOME/.codex"` | Starting or resuming complex work, after handoff, or when chat history conflicts with repo state. |
| Inspect observable Codex runtime config | `python3 scripts/harness_env_probe.py --codex-home "$HOME/.codex"` | Before relying on hooks, sandbox, approval, tool policy, or evidence schema behavior. |
| Validate requirements artifact | `python3 scripts/harness_requirements.py validate PATH` | Before treating requirements as source of truth for planning or development. |
| Summarize local evidence | `python3 scripts/harness_report.py` | During validation, review, handoff, or when deciding whether fresh evidence exists. |
| Validate parallel agent plan | `python3 scripts/harness_agent_team.py validate PLAN.json` | Before dispatching multiple workers or any scoped agent team with write sets. |
| Append checkpoint state | `python3 scripts/harness_checkpoint.py append` | At phase transitions, before handoff, before destructive/remote/release actions, or after a meaningful validated implementation slice. |

The exact helper contracts live in `docs/HARNESS_RUNTIME.md`. This skill routes
to helpers; it does not duplicate every helper option.

## Startup Sequence

For complex or resumed work:

1. Read local `AGENTS.md`, then `docs/repo-index.md` if present.
2. Run recovery and environment probes when the helper files exist:

```bash
python3 scripts/harness_recover.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --json
python3 scripts/harness_env_probe.py --codex-home "$HOME/.codex" --json
git status --short --branch
```

3. Read the state and runtime files named by the repo index, especially
   append-only state logs and current handoff docs.
4. If a helper is unavailable, run cheap manual probes:

```bash
pwd
git status --short --branch
git log --max-count=8 --pretty=format:'%h %ad %s' --date=short
test -f README.md && sed -n '1,180p' README.md
find . -maxdepth 3 \( -name '*harness-state.md' -o -name '*state.md' -o -name '*handoff*.md' -o -name 'TODOS.md' \) -print
```

If a state file is append-only, read both the header and the latest tail:

```bash
sed -n '1,220p' PATH_TO_STATE_FILE
tail -n 220 PATH_TO_STATE_FILE
```

Do not rely on chat history when durable state exists.

## Source Of Truth Order

Prefer durable project surfaces in this order:

1. Repo or subdirectory `AGENTS.md`.
2. Low-token repo index, usually `docs/repo-index.md`.
3. Current state, recovery, and handoff surfaces such as `harness-state.md`,
   `handoff.md`, or `TODOS.md`.
4. Validated requirements artifacts, contracts, ADRs, test fixtures, and design
   docs.
5. Source code, scripts, tests, CI configs, and local evidence reports.
6. Chat history only as a hint, never as the sole source of truth.

If sources conflict, preserve the conflict in the output and ask only when the
choice affects architecture, data shape, public API, security, destructive
operations, or release behavior.

## Standard Runtime Stages

Use these normalized phase names when a runtime policy or state file needs a
stable value:

| Phase | Purpose | Default Permissions | Minimum Gate |
| --- | --- | --- | --- |
| `research` | Find and verify source context. | Read-only; network only if explicitly allowed. | Sources read and cited. |
| `requirements` | Lock goal, audience, success criteria, scope, and constraints. | Read-only. | Success criteria captured and, when artifact-based, validated. |
| `planning` | Decide architecture, interfaces, data flow, risks, and tests. | Read-only by default. | Decision-complete plan and validation gate. |
| `development` | Make scoped repo changes. | Scoped writes allowed; remote/network approval-gated. | Focused tests for touched behavior. |
| `validation` | Run tests, smoke checks, and evidence capture. | No repo edits by default. | Fresh evidence with command, exit code, key output, timestamp. |
| `review` | Inspect diff, risks, behavior, and test gaps. | Read-only by default. | Findings or explicit no-issue statement. |
| `ship` | Commit, push, PR, release, deploy, or production checks. | Requested release actions only. | Ship/deploy gates and rollback note. |
| `handoff` | Preserve state for next session. | Docs/state updates only. | State log and next safe task. |

## Stage Classifier

Choose the first matching lifecycle stage. If multiple match, choose the
earliest stage that changes the decision.

| Stage | Signals | Route |
| --- | --- | --- |
| Research | Unknown repo, stale handoff, unclear source ownership, missing context. | Read durable sources, run recovery/env probes, then classify again. |
| Requirements | Goal, audience, success criteria, constraints, scope, or acceptance criteria are unclear. | Capture requirements; validate artifacts with `scripts/harness_requirements.py validate PATH` when used. |
| Product boundary | What to build, who it is for, positioning, pricing, demo scope, or product tradeoff. | Route to `gstack-plan-ceo-review` or `gstack-office-hours` when product judgment is the core work. |
| Engineering plan | Architecture, data model, API contract, migration, runtime, cross-module workflow, exception taxonomy. | Route to `gstack-plan-eng-review` or a repo engineering planning skill. |
| Design plan | UX direction, information architecture, visual system, responsive behavior, or design acceptance. | Route to `gstack-plan-design-review` or a repo design skill. |
| Implementation | Clear acceptance criteria and bounded files/modules. | Use repo workflow, TDD skill, or scoped worker agents after source context is read. |
| Debug/investigation | Failing tests, wrong output, 401/500, broken UI flow, data mismatch, unclear root cause. | Use investigation/debugging workflow before patching. |
| QA/browser | User-facing page, browser smoke, console/network errors, screenshots, accessibility, responsive checks. | Route to `gstack-qa`, `gstack-qa-only`, or browser QA skill. |
| Security/privacy | Auth, tokens, credentials, public/private boundary, PII, approvals, audit trail, data leak risk. | Route to `gstack-cso` or security review before implementation. |
| Review | Diff exists and work is near handoff, PR, or landing. | Route to `gstack-review` or code review workflow. |
| Ship/deploy | Commit, push, PR, merge, release, deploy, or production verification. | Route to `gstack-ship`, `gstack-land-and-deploy`, `gstack-canary`, and rollback docs as appropriate. |
| Documentation/release notes | Public docs, release notes, shipped behavior summary, or post-ship documentation. | Route to `gstack-document-release` or doc-updater workflow. |
| Handoff/learning | Save state, summarize, update docs, capture operational learning, prepare next session. | Use `scripts/harness_checkpoint.py append`; route to `gstack-retro` or `gstack-learn` when retrospective knowledge is requested. |

## Requirements Gate

For complex, ambiguous, cross-session, data-sensitive, or release-facing work,
capture success criteria before planning or development. A requirements artifact
is source of truth only after it validates:

```bash
python3 scripts/harness_requirements.py validate PATH
```

If no artifact exists, the plan or state log must still capture definition of
done, scope, constraints, verification commands, user-visible behavior, and
known blockers.

## Tool Router Defaults

If a repo provides `codex/runtime/tool-policy.json`, use it as the runtime policy
source. If no runtime policy exists, use these conservative defaults:

- research, requirements, planning, review: read-only.
- development: scoped repo writes allowed after source context is read.
- validation: tests, static checks, and browser smoke allowed; repo edits only
  when fixing a discovered issue.
- ship: commit, push, PR, merge, remote, or deploy actions only when explicitly
  requested and verified.
- handoff: docs/state updates only.

Secret paths, destructive commands, remote operations, and dynamic download
execution require an explicit safety check regardless of phase.

## Agent Team Gate

Before dispatching multiple agents or parallel workers, create a small plan with
`agents[]` and validate it:

```bash
python3 scripts/harness_agent_team.py validate PLAN.json
```

Each agent needs role, scope, write set, verification command, and report
expectations. Planner, reviewer, security, and QA roles are read-only by
default. Worker write sets must be non-empty, repo-relative, and disjoint.
Overlapping worker write sets block dispatch until the task is split again.

## Evidence And Report Gate

Before claiming completion, identify the narrowest fresh gate and include
verification evidence with `command`, `exit_code`, `key_output`, and
`timestamp`. Do not reuse stale verification as fresh evidence.

Use the report helper when local evidence can inform validation or handoff:

```bash
python3 scripts/harness_report.py --limit 20
python3 scripts/harness_report.py --phase validation --json
```

Common gates:

| Work type | Minimum gate |
| --- | --- |
| Any repo change | `git diff --check` plus repo status. |
| Code behavior | Existing unit/integration tests for touched modules. |
| CLI/script/harness | Success case, missing input, malformed input, forbidden input, and no partial write. |
| API boundary | Auth success, auth failure, bad request, server error path if practical. |
| Browser/UI | Local server, network/console checks, key interactions, visible error state. |
| Data/public artifact | Allowlist, denylist, count parity, source hash or provenance metadata. |
| Docs/config only | Link/path/command consistency plus `git diff --check`. |

## Checkpoint Gate

Create or update a checkpoint when work crosses a major phase boundary, before a
destructive/remote/release action, after a meaningful validated slice, or before
ending a long-running task.

Preferred route:

```bash
python3 scripts/harness_checkpoint.py append \
  --phase handoff \
  --summary "SUMMARY" \
  --changed-surface "PATH_OR_SURFACE" \
  --verification-command "COMMAND" \
  --verification-exit-code "0" \
  --verification-key-output "KEY_OUTPUT" \
  --next-safe-task "NEXT_TASK"
```

The checkpoint helper appends state; it does not commit or push.

## Exception Handling Principles

For every planned codepath or harness command, name the expected failure mode and
the required behavior.

Prefer these defaults:

- Missing source artifact: fail non-zero, print the missing path, do not write
  partial output.
- Malformed input: fail non-zero, print the parser/field error, do not guess.
- Forbidden field/string: fail non-zero, print the exact offender and location.
- Empty dataset where data is required: fail non-zero with a clear count.
- Auth-required endpoint without token: return or expect `401`, never silently
  fall back to privileged mode.
- Public/private boundary breach: block the output and report the leaking field.
- External service unavailable: surface retryable status, preserve local state,
  and avoid destructive cleanup.
- Partial write risk: write to a temp path first, validate, then promote only
  after success.

If an error can affect users, define what the user sees: clear recovery message,
retry path, fallback, or explicit unavailable state. Silent failure is a critical
gap.

## Output Contract

After routing, state:

1. Lifecycle stage selected.
2. State files, source-of-truth files, recovery output, and env probe output
   read.
3. Existing repo-specific lifecycle harness or skill to delegate to, if any.
4. Required gstack/skill/tool workflow for this stage.
5. Required helper CLIs, probes, and verification gates.
6. Failure modes that must be handled.
7. Any user decision, credential, approval, or external dependency blocking safe
   execution.

Do not start substantial implementation before this routing step when the task
is ambiguous, cross-module, security-sensitive, data-sensitive, release-facing,
or likely to span multiple sessions.
