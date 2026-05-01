# Codex Meta Terms

Use these terms when designing, reviewing, or changing Codex behavior for this environment.

## Required Terms

- `Codex surface`: a concrete place where behavior is defined, such as `AGENTS.md`, a skill, hook, subagent, automation, config, MCP tool, or programmatic Codex entrypoint.
- `surface choice`: the decision about which Codex surface should own a behavior.
- `prompt-only change`: an edit that changes only model-facing task instructions.
- `skill`: reusable local instructions stored under `~/.codex/skills/` or a repo skill directory.
- `hook`: lifecycle plumbing or terse guardrail, not a hidden planner.
- `automation`: a recurring or scheduled Codex job with its own prompt, schedule, workspace, and execution environment.
- `heartbeat automation`: a thread-attached follow-up.
- `cron automation`: a detached recurring workspace job.
- `state store`: where an automation or companion persists run state.
- `dedupe key`: the stable identifier used to avoid repeating prior work.
- `blocker evidence`: exact command, error, missing access path, or inaccessible resource that stopped progress.
- `verification gate`: the required completion evidence: `command`, `exit_code`, `key_output`, and `timestamp`.
- `private local evidence`: facts derived from local `~/.codex` state, sessions, logs, SQLite, or private automation outputs.
- `public-bound guidance`: durable guidance intended for reusable skills, docs, or repo-level behavior.

## Do Not Use As Substitutes

- Do not say `workflow` when the precise owner is a hook, skill, automation, config, or `AGENTS.md`.
- Do not say `memory` when the precise source is a rollout summary, `MEMORY.md`, archived session, SQLite inbox row, or automation state directory.
- Do not say `background agent` when the concrete implementation is a cron automation, heartbeat automation, script, or subagent.
- Do not say `fixed` unless the verification gate is satisfied.
- Do not promote private local evidence into public-bound guidance without explicit user approval.
- Do not call a hook a planner; hooks stay thin.

## Preferred Output Phrases

- `The smallest durable Codex surface is ...`
- `This is a prompt-only change; it does not alter schedule, workspace, or execution environment.`
- `The automation needs a state store, dedupe key, output artifact, blocker evidence, and verification gate.`
- `This recommendation is based on private local evidence and should not be promoted into public-bound guidance without approval.`
