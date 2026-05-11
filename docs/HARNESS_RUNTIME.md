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

## Infra Contract
- `Sandbox`: Codex sandboxing and approval rules remain the primary technical boundary.
- `Memory`: `docs/harness-state.md` is the repo-visible memory surface; subconscious output is local and advisory.
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

## Failure Modes
- missing state file: fail or warn at startup, then read repo AGENTS and README before acting.
- unknown lifecycle stage: default to restrictive read-only behavior.
- secret path access: deny unless the user explicitly requests and approves safe handling.
- remote operation: require `~/.codex/remote-access.md` review and approval.
- dynamic download execution: deny or require explicit approval.
- evidence write failure in observer hook: print a warning and allow the original tool result.
