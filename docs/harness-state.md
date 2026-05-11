# Harness State

This file is append-only evidence for the generic MyCodexEnv harness runtime.
Stable rules belong in `AGENTS.md`, `README.md`, `docs/repo-index.md`, or
`docs/HARNESS_RUNTIME.md`; session facts and phase transitions are appended here.

## Current Snapshot
- phase: development
- source_of_truth:
  - `AGENTS.md`
  - `docs/repo-index.md`
  - `README.md`
  - `docs/HARNESS_RUNTIME.md`
  - `codex/skills/project-lifecycle-harness/SKILL.md`
- blocked_sources: none
- unsafe_inputs: none
- next_safe_task: keep harness runtime docs, policy, hooks, evidence, sync, and verification tests consistent.
- required_commands:
  - `python3 test_runner.py`
  - `git diff --check`
  - `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"`
- latest_checkpoint: updated by `scripts/harness_checkpoint.py append`; helper records git status but never commits automatically.
- latest_verification: pending

## State Log

### 2026-05-11T15:07:21-04:00
- phase: planning
- event: harness runtime plan accepted for implementation.
- source_of_truth_read:
  - `AGENTS.md`
  - `README.md`
  - `codex/AGENTS.md`
  - `docs/handoffs/2026-05-11-project-lifecycle-harness.md`
  - `codex/skills/project-lifecycle-harness/SKILL.md`
  - `/Users/kezheng/Downloads/What Is the Agent Harness-.md`
- decision: implement generic MyCodexEnv harness runtime without project-specific business paths.

### 2026-05-11T15:25:00-04:00
- phase: development
- event: implementation started.
- scope:
  - repo index and append-only state
  - lifecycle router update
  - tool policy and permissions
  - local evidence schema and helper
  - thin hooks for guardrails and observability
  - checkpoint and subagent contracts
- privacy_boundary: runtime evidence stays in local `~/.codex/harness/evidence`; repo stores schema and helper only.
