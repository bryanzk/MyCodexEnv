---
name: delivery-harness-framework
description: Use when starting, resuming, or taking over complex software work that needs durable repo state, lifecycle routing, execution lane classification, architecture alignment checkpoints, dirty worktree ownership, append-only state handling, external capture promotion, deployment readiness, verification evidence, or handoff checkpoints.
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
  plan review, backlog-ready spec or issue authoring, design review and mockup
  generation, browser QA, security review, fix-first diff review, ship,
  land/deploy, canary monitoring, release documentation, documentation
  generation, context save/restore, retrospective analytics, learning capture,
  optional gbrain-backed repo memory, brain-aware planning preflight inside
  planning skills, and question-tuning preferences.
- `committee-review-loop` owns explicit expert-committee/subagent loops where a
  review committee rates an output and a revision worker iterates until a target
  score such as `9.5/10` is reached. Do not use it for ordinary one-off review,
  QA, or polish requests.

## Runtime Surfaces

When a repo implements a harness runtime, prefer these surfaces after local
`AGENTS.md`:

- `docs/repo-index.md`: low-token map of source of truth, verification commands,
  runtime surfaces, and high-risk areas.
- `CONTEXT.md`: repo terminology contract for domain language and forbidden
  aliases.
- `docs/harness-state.md`: append-only current phase, blockers, next safe task,
  latest verification, and checkpoint notes.
- `docs/HARNESS_RUNTIME.md`: contract for workflow, infra, evidence,
  checkpoints, guardrails, and agent teams.
- `docs/templates/harness-requirements.md`: requirements artifact template for
  complex work.
- `codex/runtime/tool-policy.json`: lifecycle-stage tool and permission policy.
- `codex/runtime/evidence.schema.json`: structured local evidence contract.
- `codex/hooks.json` and `codex/hooks/*`: runtime guard and observer hooks.

## Prompt Dispatcher Boundary

The global `UserPromptSubmit` hook must register only the generic
`dhf_preprompt.py` dispatcher. The dispatcher may inject this generic skill for
non-repo-specific prompts only when the prompt explicitly signals complex,
resume, takeover, handoff, or state-conflict work. Ordinary non-project prompts
continue without `additionalContext`.

Opt-out phrases such as `no dhf`, `skip dhf`, and equivalent Chinese wording
must be evaluated before any route. Repo-specific adapters must stay lazy and
are loaded only after the dispatcher verifies that `cwd` is under the
corresponding project. Generic dispatcher output must not include project paths,
business terms, or private project rules.

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

1. Read local `AGENTS.md`, then `docs/repo-index.md` and `CONTEXT.md` if
   present.
2. Run recovery and environment probes when the helper files exist:

```bash
python3 scripts/harness_recover.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --json
python3 scripts/harness_env_probe.py --codex-home "$HOME/.codex" --json
git status --short --branch
```

3. Read the state and runtime files named by the repo index, especially
   append-only state logs and current handoff docs.
4. Classify dirty worktree ownership before editing. Treat untracked and
   modified files as owned by the user unless you created them in this turn.
5. If a helper is unavailable, run cheap manual probes:

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

## Dirty Worktree Gate

Before development, review, ship, or handoff, classify status and protect
mixed ownership:

- `clean`: no modified or untracked files.
- `user_owned`: existing modified or untracked files outside the current task.
- `agent_owned`: files created or changed by the current task.
- `generated_disposable`: regenerable local artifacts; commit only if promoted.
- `unknown_owner`: unclear ownership; avoid overwrites and ask only if blocked.

State the classification when it affects write, review, or ship scope. Never
clean, reset, delete, stage, or fold unrelated files into the task to make the
repo look tidy.

## Source Of Truth Order

Prefer durable project surfaces in this order:

1. Repo or subdirectory `AGENTS.md`.
2. Low-token repo index, usually `docs/repo-index.md`.
3. Repo terminology map, usually `CONTEXT.md` or `CONTEXT-MAP.md`.
4. Current state, recovery, and handoff surfaces such as `harness-state.md`,
   `handoff.md`, or `TODOS.md`.
5. Validated requirements artifacts, contracts, ADRs, test fixtures, and design
   docs.
6. Source code, scripts, tests, CI configs, and local evidence reports.
7. Chat history only as a hint, never as the sole source of truth.

If sources conflict, preserve the conflict in the output and ask only when the
choice affects architecture, data shape, public API, security, destructive
operations, or release behavior.

## State Snapshot Gate

For append-only state files, prefer a short current snapshot near the top of the
file when the repo provides one. A useful snapshot names active phase and
execution lane, branch or commit, dirty-state note, latest state-log headlines,
fresh verification, next safe task, and blockers. If absent or stale, read the
stable header and latest tail, report the debt, and only append or update the
repo-approved current snapshot area.

## Standard Runtime Stages

Use these normalized phase names when a runtime policy or state file needs a
stable value:

| Phase | Purpose | Default Permissions | Minimum Gate |
| --- | --- | --- | --- |
| `research` | Find and verify source context. | Read-only; network only if explicitly allowed. | Sources read and cited. |
| `requirements` | Lock goal, audience, success criteria, scope, constraints, and domain vocabulary. | Read-only. | Success criteria captured and, when artifact-based, validated. |
| `planning` | Decide architecture, interfaces, data flow, risks, vertical slices, and tests. | Read-only by default. | Decision-complete plan and validation gate. |
| `development` | Make scoped repo changes. | Scoped writes allowed; remote/network approval-gated. | Focused tests for touched behavior. |
| `validation` | Run tests, smoke checks, and evidence capture. | No repo edits by default. | Fresh evidence with command, exit code, key output, timestamp. |
| `review` | Inspect diff, risks, behavior, and test gaps. | Read-only by default. | Findings or explicit no-issue statement. |
| `ship` | Commit, push, PR, release, deploy, or production checks. | Requested release actions only. | Ship/deploy gates and rollback note. |
| `handoff` | Preserve state for next session. | Docs/state updates only. | State log and next safe task. |

## Execution Lane Gate

Classify execution lane separately from lifecycle phase whenever external
systems, credentials, customer data, provider captures, deploys, or demos are in
scope. Repo-specific harnesses may refine lane names, but they should map back
to:

| Lane | Meaning | Default boundary |
| --- | --- | --- |
| `local_dev` | Local-only development with fixtures, fake providers, local services, or browser checks. | No live external calls, secret reads, remote mutations, deploys, or customer data writes. |
| `operator_live_demo` | Temporary live demo or capture owned by the operator/developer. | Explicit opt-in, local secret source, temporary outputs, no production/customer authority. |
| `customer_or_production` | Customer-owned, production, or deployment-facing infrastructure and auth paths. | Requires owner/project, auth, IAM, secrets, data store, rollback, smoke/canary, and approval before mutation. |

At routing time, state the selected lane, allowed external systems, forbidden
actions, and the gate that would move the task to a higher-risk lane.

## Stage Classifier

Choose the first matching lifecycle stage. If multiple match, choose the
earliest stage that changes the decision.

| Stage | Signals | Route |
| --- | --- | --- |
| Research | Unknown repo, stale handoff, unclear source ownership, missing context. | Read durable sources, run recovery/env probes, then classify again. |
| Requirements | Goal, audience, success criteria, constraints, scope, domain terms, or acceptance criteria are unclear. | Route through `grilling` first unless the user already provided complete acceptance criteria; then use planner or `req-to-dev` to structure the artifact, read `CONTEXT.md`, `CONTEXT-MAP.md`, and relevant `docs/adr` files when present, use domain vocabulary and flag conflicts, and validate artifacts with `scripts/harness_requirements.py validate PATH` when used. |
| Backlog/spec authoring | The user wants to turn a fuzzy request into a backlog-ready issue, ticket, or executable spec before implementation starts. | Route to vendored gstack `spec`; preserve DHF source-of-truth reads, execution-lane classification, and validation gates so the resulting issue or spec inherits the right boundaries. |
| Product boundary | What to build, who it is for, positioning, pricing, demo scope, or product tradeoff. | Route to `gstack-plan-ceo-review` or `gstack-office-hours` when product judgment is the core work. Prefer `gstack-office-hours` when the problem statement, demand signal, or wedge is still fluid. If gbrain is already configured, let the gstack planning skill run its own brain-aware preflight; do not make the generic harness read or sync gbrain directly. |
| Architecture alignment checkpoint | Durable sources disagree or appear stale; competing product surfaces or architecture branches exist; execution lane, deployment topology, or parallel slice boundaries conflict; current slices are blocked by unresolved business/application architecture decisions; or the user explicitly asks to establish a unified decision surface before implementation or subagent dispatch. Do not use this route for ordinary architecture planning when there is no durable-source conflict, stale state, branch conflict, lane ambiguity, blocked slice boundary, or explicit alignment-checkpoint request. | Read durable sources in source-of-truth order, preserve conflicts, capture a decision-focused ADR/checkpoint, create a stakeholder-readable architecture view when useful, recut vertical slices around business outcomes, run product/engineering/security review as needed, append checkpoint state, then validate any agent-team plan before dispatch. Keep repo-specific file names and commands in the repo harness or checkpoint artifact. |
| Engineering plan | Architecture, data model, API contract, migration, runtime, cross-module workflow, exception taxonomy, or deep module shape. | Route to `gstack-plan-eng-review` or a repo engineering planning skill; for multi-step work, decompose into vertical slice units and mark each slice `AFK` or `HITL`. When the change introduces new artifacts or infrastructure, ensure the plan includes distribution/publish paths rather than code-only scope. If gbrain is already configured, let the delegated planning skill consume cached product, goal, developer-persona, brand, competitive-intel, skill-run, user-profile, or take digests; the harness still owns durable repo state and execution-lane boundaries. |
| Prototype | A data model, state machine, module interface, or UI direction needs fast learning before production work. | Build only a clearly marked throwaway prototype that answers one named question; delete it or capture the durable decision in an ADR, issue, checkpoint, or notes before handoff. |
| Design plan | UX direction, information architecture, visual system, responsive behavior, or design acceptance. | Route to `gstack-plan-design-review` or a repo design skill. When visual UI is in scope and a design binary/mockup workflow exists, prefer mockup-first review over prose-only design critique. If gbrain is already configured, treat its planning preflight as specialist context, not as a replacement for repo instructions, state logs, or fresh validation. |
| Committee loop | User explicitly asks for a committee, expert panel, subagent reviewer/worker split, rating loop, or to keep improving until a score such as `9.5/10`. | Route to `committee-review-loop`; preserve DHF agent-team validation and verification gates. Ordinary design, code, QA, or read-only reviews keep their specialized routes. |
| Implementation | Clear acceptance criteria and bounded files/modules. | Use repo workflow, TDD skill, or scoped worker agents after source context is read. |
| Debug/investigation | Failing tests, wrong output, 401/500, broken UI flow, data mismatch, unclear root cause. | Establish a runnable feedback loop before hypotheses or fixes, then use investigation/debugging workflow. |
| QA/browser/device | User-facing page, browser smoke, console/network errors, screenshots, accessibility, responsive checks, read-only page data extraction, or real-device iOS app testing/design audit. | Route to `gstack-qa`, `gstack-qa-only`, browser QA skill, `gstack-ios-qa`, `gstack-ios-design-review`, or `gstack-ios-fix` as appropriate. Use vendored gstack `scrape`/`skillify` when the work is extracting and codifying browser data flows rather than testing behavior, and `gstack-ios-sync` / `gstack-ios-clean` only when the request is specifically about maintaining the iOS debug bridge or removing debug-only instrumentation before release. |
| Security/privacy | Auth, tokens, credentials, public/private boundary, PII, approvals, audit trail, data leak risk. | Route to `gstack-cso` or security review before implementation. |
| Review | Diff exists and work is near handoff, PR, or landing. | Route to `gstack-review` or code review workflow. Prefer fix-first review flows when the review surface is narrow enough to auto-fix mechanical issues without changing product intent. |
| Ship/deploy | Commit, push, PR, merge, release, deploy, production verification, or version-slot queue visibility. | Route to `gstack-ship`, `gstack-land-and-deploy`, `gstack-canary`, `gstack-landing-report`, and rollback docs as appropriate. |
| Documentation/release notes | Public docs, release notes, shipped behavior summary, missing docs for a module/feature, polished PDF artifacts, or post-ship documentation. | Route to `gstack-document-release`, vendored gstack `document-generate`/`make-pdf`, or doc-updater workflow. Treat discoverability gaps, stale architecture diagrams, missing how-to/tutorial coverage, and publication-quality artifacts as first-class documentation debt. |
| Handoff/learning | Save state, restore state, summarize, update docs, capture operational learning, prepare next session, tune repeated planning questions, or refresh persistent repo memory. | Use `scripts/harness_checkpoint.py append` for repo-local harness state; use vendored gstack `context-save`/`context-restore` for user-facing session continuity; route to `gstack-retro` for time-windowed or cross-project retrospective analysis, `gstack-learn` when reusable learnings must be searched/exported/pruned, `gstack-plan-tune` when the user asks to tune repeated questions or developer profile preferences, and vendored gstack `setup-gbrain`/`sync-gbrain` only when the user explicitly wants gbrain setup or repo re-indexing. |

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

If success is defined as a subjective committee score and the user explicitly
requests subagents or a committee, record the score as the loop target and route
to `committee-review-loop` before development.

## Engineering Planning Gate

For multi-step work, prefer vertical slice decomposition over layer-by-layer
tasks. Each slice should be independently demoable or verifiable, list blocking
dependencies, and be marked `AFK` when an agent can implement it from durable
context or `HITL` when human judgment, credentials, design approval, or external
access is required.

Each slice contract should capture:

- `task_demand`: `low | medium | high`, justified by:
  - `L` - estimated minimum reasoning/action steps
  - `H_tool` - tool-selection ambiguity
  - `S_state` - cross-module state-tracking demand
  - `N_obs` - observation or external-noise demand
- execution lane
- scope and allowed files, modules, or surfaces
- out-of-scope actions
- first failing test, feedback loop, or observable check
- focused green gate
- full or release gate
- docs, state, or checkpoint update
- handoff expectations and next safe task

The minimum gate and chosen next-safe-task should scale with `task_demand`: low
demand must not be forced through an unnecessary full regression, while high
demand requires more than the default gate.

When planning module changes, prefer deep module opportunities: keep the public
interface small, put meaningful behavior behind that interface, and treat the
interface as the test surface. Use the repo's domain vocabulary when naming
modules and seams.

## Architecture Alignment Checkpoint Gate

Use this gate before implementation or parallel dispatch when durable sources no
longer provide one coherent decision surface. Common triggers include competing
product surfaces, stale handoffs, architecture branches, unclear local/live lane
boundaries, slices that mix technical layers instead of business outcomes, or a
user asking to align business architecture and application architecture before
cutting work.

The checkpoint should be decision-focused, not a second long-form requirements
document. Keep project-specific paths, file names, commands, customer names, and
domain fixtures in the repo-specific harness or in the resulting checkpoint
artifact, not in this generic skill.

Minimum workflow:

1. Read durable sources in the source-of-truth order: repo instructions, repo
   index, state/handoff surfaces, requirements/contracts/ADRs, architecture and
   slice plans, then source/tests only as needed.
2. Run a conflict scan across product surface, business process, application
   components, data ownership, execution lanes, deployment readiness, security
   boundary, current slices, and latest handoff state.
3. Capture the decision in an ADR or checkpoint: chosen path, rejected options,
   open decisions, lane boundary, blockers, validation gate, and owner for the
   next decision.
4. Create a stakeholder-readable architecture view when the decision affects
   product, business, engineering, security, or rollout coordination. This can be
   a diagram, HTML explainer, slide, or concise document, depending on the repo.
5. Recut work into vertical slices that begin with a user/business event and end
   in an independently observable result. Avoid layer-only slices unless the
   layer itself is the product of the checkpoint.
6. Review the checkpoint from the necessary perspectives, typically product
   boundary, engineering architecture, and security/privacy. Use a committee loop
   only when the user explicitly asks for committee/subagent review or a target
   score.
7. Append or update the repo-approved state surface with the decision, fresh
   verification or review evidence, dirty-state classification, next safe task,
   blockers, and any agent-team dispatch rules.

Do not treat the checkpoint as approval to mutate remote systems, read secrets,
deploy, promote external captures, or write customer data. Those still require
their own lane and readiness gates.

Before subagent dispatch after an alignment checkpoint, validate that each worker
has a durable task contract, disjoint write set, first feedback loop, green gate,
and handoff expectations. The integrator should own the final state append.

## Debug Feedback Gate

Do not patch a hard bug from inspection alone. First build or identify a
feedback loop such as a failing test, CLI fixture, curl script, browser check,
trace replay, throwaway harness, fuzz loop, or differential run. If no loop can
be built, report the missing artifact or access needed before hypothesizing.

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

## External Capture Promotion Gate

For live provider output, browser exports, API captures, model responses,
customer files, or other external data, keep raw capture temporary until
promoted. Promotion requires: local-only raw storage, contract/schema/count
validation, secret and private-data leak scan, policy or human review, sanitized
fixture/artifact promotion only, and fresh evidence of the decision. If any step
fails, preserve useful local state, do not commit raw capture, and report the
blocker.

## Deployment Readiness Gate

Before remote mutation, customer-owned infrastructure, production auth, OAuth
install, database migration, deploy, or live cutover, require readiness for
owner/project/environment, auth actor, minimum IAM, secret handling, data store
and rollback, public/private and audit boundaries, smoke/canary check, and
explicit approval or blocker. Missing readiness keeps the task in planning or
local validation; never convert a local demo into a live deployment by
implication.

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
Delegated workers must not include the repo's global harness state file
(`docs/harness-state.md`) or a parent path such as `docs/` in their write set.
Worker handoff should be reported or written to slice-local artifacts; the
integrating main agent appends the consolidated harness checkpoint after merge
or integration and fresh verification. Single-line tasks executed directly by
the main agent are not worker plans and may still use
`scripts/harness_checkpoint.py append` after validation.
If the requested agent team is a review committee plus a revision worker with a
numeric rating target, route to `committee-review-loop` after validating the
team shape and write-set boundaries.
When a worker needs a durable task contract, use
`docs/templates/harness-agent-brief.md`. The optional `brief` object in an agent
team plan should capture category, summary, current behavior, desired behavior,
key interfaces, acceptance criteria, and out of scope. Do not use line numbers
or file-path-only instructions as the task contract.
If the planned workers depend on an unresolved product surface, runtime topology,
execution lane, or shared state file, run the Architecture Alignment Checkpoint
Gate before validating the agent team. Do not use parallel workers to resolve an
architecture conflict implicitly through competing implementations.

## Evidence And Report Gate

Before claiming completion, identify the narrowest fresh gate and include
verification evidence with `command`, `exit_code`, `key_output`, and
`timestamp`. Do not reuse stale verification as fresh evidence.

Effective-feedback check: before claiming completion, the feedback loops spent
on the task must be classifiable as informative, valid, non-redundant, and
retained. Any segment that consumed budget without producing retained,
task-relevant feedback, such as re-running an already-green gate or repeating
information already present in the trajectory, must be flagged as
low-conversion in the handoff.

Use this stable shape:

```text
effective_feedback_check:
- informative:
- valid:
- non_redundant:
- retained:
- low_conversion_segments:
```

Use the report helper when local evidence can inform validation or handoff:

```bash
python3 scripts/harness_report.py --limit 20
python3 scripts/harness_report.py --phase validation --json
```

When local evidence exists, use `scripts/harness_report.py --json` or
`scripts/harness_recover.py --json` to surface `conversion_health.status` and
its reason in handoff or final routing output. Treat `stalled` as a
planning/recovery warning, not an automatic failure.

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
2. Execution lane selected, allowed external systems, and forbidden actions.
3. Dirty worktree classification and any unrelated user-owned files.
4. State snapshot status, state files, source-of-truth files, recovery output, and env probe output
   read.
5. Existing repo-specific lifecycle harness or skill to delegate to, if any.
6. Required gstack/skill/tool workflow for this stage.
7. Required helper CLIs, probes, and verification gates.
8. Failure modes that must be handled.
9. Any user decision, credential, approval, or external dependency blocking safe
   execution.
10. For `committee-review-loop`, the three expert domains, target rating,
   revision worker scope, verification gate, and stopping condition.
11. For `Architecture alignment checkpoint`, the durable sources compared,
    conflicts found, decision artifact to create or update, stakeholder-readable
    view requirement, vertical slice recut rule, review perspectives, state
    append path, and agent-team dispatch gate.
12. Selected `task_demand`, demand-matched gate actually used, and the result of
    `effective_feedback_check`, including any `low_conversion_segments`.
13. `conversion_health` status and whether any stall or low-conversion signals
    are present when local evidence exists.

When gstack is the delegated specialist, also note which advanced posture is
expected: product interrogation, mockup-first design review, fix-first review,
distribution-aware ship planning, documentation-debt audit, or retrospective
analytics. This keeps the router aligned with newer gstack workflows without
hard-coding repo-specific commands.

Do not start substantial implementation before this routing step when the task
is ambiguous, cross-module, security-sensitive, data-sensitive, release-facing,
or likely to span multiple sessions.
