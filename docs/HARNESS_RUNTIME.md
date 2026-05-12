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
| `handoff` | docs/state only | no | no | state log and next safe task |

Memory is a hint. Before acting, Codex must verify against repo files, git state,
tests, or runtime evidence.

Requirements artifacts use `docs/templates/harness-requirements.md`. Validate
them with `scripts/harness_requirements.py validate PATH` before treating them
as source of truth.

For the current project workflow and skill routing map, read
`docs/LIFECYCLE_SKILL_ROUTING.md`.

## Infra Contract
- `Sandbox`: Codex sandboxing and approval rules remain the primary technical boundary; `scripts/harness_env_probe.py` reports the observable runtime configuration.
- `Memory`: `docs/harness-state.md` is the repo-visible memory surface; `scripts/harness_recover.py` proves recovery from state, git, and local evidence.
- `Skills`: `codex/skills/*` is the source copied into runtime `~/.codex/skills/*`.
- `Session State`: `docs/harness-state.md` records durable phase and handoff facts.
- `Permissions`: `codex/runtime/tool-policy.json` declares stage-level tool permissions.
- `Hooks`: `codex/hooks/*` implements thin objective guardrails and evidence plumbing.
- `Observability`: local JSONL evidence records lifecycle and verification events.
- `Tool Router`: lifecycle stage determines allowed read/write/network/remote behavior.
- `Checkpoints`: use git commits, state log entries, and handoff docs as recovery points.
- `Guardrails`: destructive, secret, remote, and dynamic-execution actions are blocked or require approval.

## Evidence Contract
Evidence events are JSON objects that match `codex/runtime/evidence.schema.json`.
Runtime events are written to local files under `~/.codex/harness/evidence`.

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
  `--cwd`, `--since`, `--phase`, `--event-type`, `--limit`, and `--json`.
- empty evidence: report exits 0 with an explicit empty summary.
- malformed JSONL lines: report continues, increments `malformed_count`, and
  lists file and line.

## Recovery Contract
Fresh sessions should be able to recover the next safe task without chat
history. `scripts/harness_recover.py` reads repo index, harness state, git
status/log, and local evidence summary.

Recovery behavior:
- missing repo index or harness state: fail non-zero and print the missing path.
- no matching local evidence: exit 0 with `evidence_status=empty`.
- dirty repo: report `dirty_status=dirty` and `dirty_count`.
- JSON output: use `--json` for automation and visual reports.

## Environment Probe Contract
`scripts/harness_env_probe.py` reports what the repo can observe about the local
Codex runtime: config, hooks, tool policy, evidence schema, sandbox fields, and
approval fields.

Probe behavior:
- missing required runtime files: fail non-zero and name each missing file.
- sandbox fields absent from config: do not infer; report `observable=false`.
- global Desktop sandbox is outside repo control; the probe reports observable
  config only.

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
- write set: empty for read-only roles, disjoint for workers;
- verification command;
- report schema: changes, evidence, blockers, and risks.

Default permissions:
- planner: read-only;
- worker: scoped writes only;
- reviewer/security/qa: read-only;
- main agent: integration and final judgment.

Overlapping worker write sets block dispatch until the task is split again.

Agent team validator:
- `scripts/harness_agent_team.py validate PLAN.json` validates `agents[]`.
- every agent requires `id`, `role`, `scope`, `write_set`, and
  `verification_command`.
- planner, reviewer, security, and qa roles must have an empty `write_set`.
- worker roles must have a non-empty `write_set` and verification command.
- worker write sets are normalized to repo-relative paths and must be disjoint.
- empty paths, `..` traversal, and absolute paths outside the repo fail.

## Failure Modes
- missing state file: fail or warn at startup, then read repo AGENTS and README before acting.
- unknown lifecycle stage: default to restrictive read-only behavior.
- secret path access: deny unless the user explicitly requests and approves safe handling.
- remote operation: require `~/.codex/remote-access.md` review and approval.
- dynamic download execution: deny or require explicit approval.
- evidence write failure in observer hook: print a warning and allow the original tool result.
