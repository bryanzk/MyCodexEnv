# Harness Runtime

## Purpose
MyCodexEnv treats the model as only one part of the agent system. The harness
runtime provides the surrounding workflow and infrastructure: state, tool
routing, permissions, evidence, verification, checkpoints, and recoverable
handoffs.

## Workflow Contract
The lifecycle router uses these stages:

| Stage | Write Access | Network | Subagents | Minimum Gate |
| --- | --- | --- | --- | --- |
| `research` | no | only if explicitly allowed | optional read-only | source files read and cited |
| `requirements` | no | no by default | no | success criteria captured |
| `planning` | no | no by default | optional read-only | implementation plan and validation gate |
| `development` | yes, scoped | no by default | optional scoped workers | focused tests for touched behavior |
| `validation` | no repo edits by default | browser/test-only if needed | optional review/qa | fresh verification evidence |
| `review` | no by default | no by default | optional read-only reviewers | findings or no-issue statement |
| `ship` | yes, only requested release actions | yes if release requires it | optional | ship/deploy gates |
| `handoff` | ask-gated docs/state only | no | no | state log and next safe task |

Memory is a hint. Before acting, Codex must verify against repo files, git state,
tests, or runtime evidence.

Requirements artifacts use `docs/templates/harness-requirements.md`. Validate
them with `scripts/harness_requirements.py validate PATH` before treating them
as source of truth.

Validated requirements artifacts must include `## Task Demand (D_task)`.
The validator requires `estimated_level` to be exactly `low`, `medium`, or
`high`, and requires non-empty `L`, `H_tool`, `S_state`, and `N_obs` fields.
It does not score, infer, or deeply validate the semantic quality of those
values; they remain operator or agent estimates that can be refined in later
planning.

When a repo has domain docs, use `CONTEXT.md`, `CONTEXT-MAP.md`, and relevant
ADRs as planning inputs. They sharpen domain vocabulary, surface ADR conflicts,
and keep plans from inventing inconsistent terms.

For the current project workflow and skill routing map, read
`docs/LIFECYCLE_SKILL_ROUTING.md`.

## Related Documentation
- `README.md`: top-level quick start and Harness Runtime overview.
- `docs/repo-index.md`: low-token repo navigation and runtime surface index.
- `docs/surfaces.json`: canonical machine-readable runtime surface inventory.
- `docs/LIFECYCLE_SKILL_ROUTING.md`: lifecycle stage, workflow, skill, and helper routing.
- `docs/MODEL_ROUTER_EVAL_MATRIX.md`: prompt/subtask model router eval matrix.
- `docs/index.html`: Chinese public Delivery Harness Framework docs entry for GitHub Pages.
- `docs/index-en.html`: English public Delivery Harness Framework docs entry for GitHub Pages.
- `docs/delivery-harness-beginner-guide-cn.html`: beginner-oriented Chinese explanation of what Delivery Harness Framework does.
- `docs/delivery-harness-beginner-guide-en.html`: beginner-oriented English explanation of what Delivery Harness Framework does.
- `docs/AGENT_HARNESS_STATUS.md`: Agent Harness workflow/infra status map.
- `docs/CODEX_ENV_REPRODUCTION.md`: Codex + Claude environment reproduction guide.
- `docs/project-lifecycle-harness-flow-cn.html`: Chinese vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-en.html`: English vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-skills.html`: Chinese lifecycle skill/helper routing visual guide.
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`: current styled Chinese Delivery Harness Framework skill/helper routing visual guide.
- `docs/project-lifecycle-harness-flow-skills-en-status-style.html`: current styled English Delivery Harness Framework skill/helper routing visual guide.

## Infra Contract
- `Sandbox`: Codex sandboxing and approval rules remain the primary technical boundary; `scripts/harness_env_probe.py` reports the observable runtime configuration.
- `Memory`: `docs/harness-state.md` is the repo-visible memory surface; `scripts/harness_recover.py` proves recovery from state, git, and local evidence.
- `Skills`: `codex/skills/*` is the source copied into runtime `~/.codex/skills/*`.
- `Session State`: `docs/harness-state.md` records durable phase and handoff facts.
- `Permissions`: `codex/runtime/tool-policy.json` declares stage-level tool permissions; unknown phases fall back to read-only, and `handoff` repo writes require approval because the guard is category-level, not path-scoped.
- `Hooks`: `codex/hooks/*` implements thin objective guardrails, prompt model routing recommendations, and evidence plumbing.
- `Observability`: local JSONL evidence records lifecycle and verification events.
- `Surface Inventory`: `docs/surfaces.json` is the canonical runtime surface inventory; `scripts/check_surfaces.py` keeps it consistent with files on disk, the `docs/repo-index.md` `## Runtime Surfaces` mirror, and opt-in public landing nav links declared with `public_nav`.
- `Tool Router`: lifecycle stage determines allowed read/write/network/remote behavior. The guard resolves phase in order from top-level payload, `tool_input.phase`, `CODEX_HARNESS_PHASE`, `docs/harness-state.md` `## Current Snapshot`, then `unknown`.
- `Model Router`: `codex/hooks/model_router.py` classifies each prompt or subtask as `simple`, `medium`, or `complex` and recommends the cheapest quality-safe model tier. It intentionally stays non-blocking; runtimes or wrapper scripts that can switch models may consume the JSON `routing` object, while plain Codex hooks inject the recommendation and response telemetry requirement as additional context.
- `Checkpoints`: use git commits, state log entries, and handoff docs as recovery points.
- `Guardrails`: repo-write phase violations, destructive commands, secret access, remote operations, and dynamic-execution actions are blocked or require approval.

## Evidence Contract
Evidence events are JSON objects that match `codex/runtime/evidence.schema.json`.
That file remains the compatibility entrypoint. Focused schemas live under
`codex/runtime/evidence/`:
- `decision-evidence.schema.json`
- `routine-gate-receipt.schema.json`

Runtime events are written to local files under `~/.codex/harness/evidence`.
Local logs are not migrated when the schema evolves. Old events that do not
carry `evidence_kind` are read as `unknown`.

Evidence kinds:
- `decision`: state, handoff, approvals, guardrails, sandbox failures, agent-team
  validation receipts, and durable recovery decisions.
- `routine`: test receipts, browser smoke, startup probes, ordinary tool calls,
  and non-decision subagent reports.
- `unknown`: legacy read-only normalization for old local JSONL events; new
  appends must use or infer `decision` or `routine`.

Required verification evidence fields:
- `command`
- `exit_code`
- `key_output`
- `timestamp`

Evidence helper behavior:
- malformed event: fail non-zero and do not write.
- missing required verification fields: fail non-zero and do not write.
- partial write risk: validate before append.
- observer hook failure: warn and continue so observability does not block normal work.
- report view: `scripts/harness_report.py` summarizes local JSONL evidence with
  `--cwd`, `--since`, `--phase`, `--event-type`, `--evidence-kind`, `--limit`,
  and `--json`.
- conversion health: `scripts/harness_feedback.py` computes a local advisory
  `conversion_health` signal from already-filtered evidence events; report and
  recover outputs include status, reason, productive event counts, repeated
  command counts, and low-conversion signals.
- stalled conversion health is advisory for planning and recovery, not an
  automatic failure gate.
- empty evidence: report exits 0 with an explicit empty summary.
- malformed JSONL lines: report continues, increments `malformed_count`, and
  lists file and line.
- state logs should promote compact decision evidence summaries instead of
  copying every routine gate receipt into handoff state.

## Recovery Contract
Fresh sessions should be able to recover the next safe task without chat
history. `scripts/harness_recover.py` reads repo index, harness state, git
status/log, and local evidence summary.

Recovery behavior:
- missing repo index or harness state: fail non-zero and print the missing path.
- no matching local evidence: exit 0 with `evidence_status=empty`.
- dirty repo: report `dirty_status=dirty` and `dirty_count`.
- evidence kind summary: JSON and markdown output include counts for
  `decision`, `routine`, and `unknown` evidence matching the repo cwd.
- latest decision evidence: JSON and markdown output include a compact
  `latest_decision_evidence` summary so routine receipts do not bury durable
  handoff and guardrail decisions.
- conversion health: JSON and markdown output include the advisory
  `conversion_health` status and reason for matching local evidence.
- JSON output: use `--json` for automation and visual reports.

## Environment Probe Contract
`scripts/harness_env_probe.py` reports what the repo can observe about the local
Codex runtime: config, hooks, tool policy, compatibility evidence schema, split
evidence schemas, sandbox fields, and approval fields.

Probe behavior:
- missing required runtime files: fail non-zero and name each missing file.
- split evidence schemas must exist at
  `runtime/evidence/decision-evidence.schema.json` and
  `runtime/evidence/routine-gate-receipt.schema.json`.
- sandbox fields absent from config: do not infer; report `observable=false`.
- global Desktop sandbox is outside repo control; the probe reports observable
  config only.

## Model Routing Contract
`codex/hooks/model_router.py` is the pre-task prompt router. It reads hook JSON
from stdin and exits 0 in all normal cases so routing cannot block task intake.

Routing behavior:
- missing or malformed prompt: recommend balanced fallback `gpt-5.4` with low
  confidence;
- very short harmless prompts: recommend `gpt-5.4-mini` with low reasoning;
- simple formatting, translation, README, and documentation subtasks: recommend
  `gpt-5.4-mini` with low reasoning;
- ordinary implementation, tests, scripts, and refactors: recommend `gpt-5.4`
  with medium reasoning;
- architecture, auth, security, migrations, deploys, destructive operations, or
  long cross-module tasks: recommend `gpt-5.5` with high reasoning;
- review phase: recommend `gpt-5.5` with high reasoning;
- validation phase without high-risk signals: recommend `gpt-5.4-mini` with low
  reasoning for evidence collection and summarization;
- when `subtask` is present, classify the subtask instead of anchoring on the
  parent prompt, allowing complex tasks to downshift for cheap subtasks and
  upgrade again for planning, security, review, or release steps.

The hook output includes `routing.switch_points` for complex prompts so an
orchestrator can re-run or apply routing at research, planning, development,
validation, and review boundaries. The hook does not claim to force a model
change in Codex versions that only accept additional prompt context.

Response telemetry behavior:
- output includes `telemetry.models_used`, `telemetry.token_usage`, and
  `telemetry.five_hour_limit`;
- actual model names are read from payload fields such as `model`,
  `current_model`, `selected_model`, or `active_model`, then combined with the
  routed recommendation;
- token usage is read from payload `usage` / `token_usage` fields such as
  `input_tokens`, `output_tokens`, and `total_tokens`;
- five-hour limit data is read from payload `limits` / `quota` / `rate_limit`
  fields or from `CODEX_5H_LIMIT_REMAINING` and `CODEX_5H_LIMIT_RESET_AT`;
- unavailable telemetry must be reported as `unavailable`; the hook and final
  response instructions must not estimate or invent token usage or limits.

## Checkpoint Contract
Create a checkpoint when a task crosses any of these boundaries:
- before destructive, remote, or release actions;
- after a major phase transition;
- before ending a long-running or cross-session task;
- after validation passes for a meaningful implementation slice.

A checkpoint must record:
- phase;
- files or surfaces changed;
- validation evidence;
- blockers;
- next safe task;
- whether a git commit exists.

Checkpoint helper:
- `scripts/harness_checkpoint.py append` updates `docs/harness-state.md` and
  appends a checkpoint entry.
- it records git branch, latest commit, dirty status, changed surfaces, blockers,
  latest verification, and next safe task.
- it does not create git commits or push changes.
- missing verification fields fail non-zero before writing.
- `--allow-unverified` is only valid for `handoff` checkpoints with an explicit
  blocker.

## Subagent Contract
Each delegated agent must receive:
- role: planner, worker, reviewer, security, or qa;
- scope: exact task and owned files or modules;
- write set: empty for read-only roles, disjoint for workers, and no protected
  integrator state surfaces such as `docs/harness-state.md`;
- verification command;
- report schema: changes, evidence, blockers, and risks.

Worker agents may also receive a durable brief using
`docs/templates/harness-agent-brief.md`. A brief records category, summary,
current behavior, desired behavior, key interfaces, acceptance criteria, and out
of scope. Use behavior and interfaces as the task contract; line numbers and
file-path-only instructions are not durable enough.

Worker JSON plans must include `task_demand` and `green_gate` objects:
- `task_demand`: `level` (`low`, `medium`, or `high`), `L`, `H_tool`,
  `S_state`, and `N_obs`.
- `green_gate`: `gate_scope` (`worker` or `integrator`), `command`, and
  `rationale`.
- medium and high demand require `focused_gate_command`.
- high demand also requires `full_gate_command` and `new_probe`.
- when `gate_scope=worker`, `verification_command` must match
  `green_gate.command`.
- when `gate_scope=integrator`, `integrator_gate_command` must match
  `verification_command`.

Read-only roles must not carry `task_demand` or `green_gate`; demand gates are
for scoped workers only. Demand gates do not replace disjoint write-set checks
or the required `verification_command`.

Default permissions:
- planner: read-only;
- worker: scoped writes only;
- reviewer/security/qa: read-only;
- main agent: integration, final judgment, and verified checkpoint updates.

Overlapping worker write sets block dispatch until the task is split again.
Delegated workers must not claim `docs/harness-state.md`, or a parent path such
as `docs/`, in their write set. Worker handoff belongs in a slice-local artifact
or report; the main agent appends the consolidated harness checkpoint after
integration and fresh verification. Single-line tasks executed directly by the
main agent are not worker plans and may still use `scripts/harness_checkpoint.py
append` after the usual verification gate.

Agent team validator:
- `scripts/harness_agent_team.py validate PLAN.json` validates `agents[]`.
- `scripts/harness_agent_team.py validate PLAN.json --emit-evidence` also appends
  one local `agent_team_validated` decision receipt on success, with
  `metadata.plan_sha256`, `agent_count`, `worker_count`, and `repo_root`.
- every agent requires `id`, `role`, `scope`, `write_set`, and
  `verification_command`.
- optional worker `brief` objects are validated when present and are backward
  compatible when omitted.
- worker roles require `task_demand` and `green_gate`; the gate must match the
  declared demand level.
- read-only roles reject `task_demand` and `green_gate`.
- planner, reviewer, security, and qa roles must have an empty `write_set`.
- worker roles must have a non-empty `write_set` and verification command.
- worker write sets are normalized to repo-relative paths and must be disjoint.
- worker write sets must not overlap protected integrator state surfaces,
  currently `docs/harness-state.md`.
- empty paths, `..` traversal, and absolute paths outside the repo fail.
- configured dispatch tool names and command patterns are ask-gated by
  `codex/hooks/harness_guard.py` unless the payload includes `plan_sha256` and a
  matching local receipt less than 10 minutes old.
- this is an honest configured-shape gate: runtime dispatch paths not exposed to
  `PreToolUse` or not named in `tool-policy.json` cannot be intercepted by this
  repo hook.

## Failure Modes
- missing state file: fail or warn at startup, then read repo AGENTS and README before acting.
- unknown lifecycle stage: default to restrictive read-only behavior.
- missing or malformed `## Current Snapshot` phase: treat the phase as unknown and require approval for repo writes.
- secret path access: deny unless the user explicitly requests and approves safe handling.
- remote operation: require `~/.codex/remote-access.md` review and approval.
- dynamic download execution: deny or require explicit approval.
- evidence write failure in observer hook: print a warning and allow the original tool result.
- missing, stale, cross-repo, worker-count-mismatched, or malformed agent-team
  validation receipt: ask before configured multi-agent dispatch.
