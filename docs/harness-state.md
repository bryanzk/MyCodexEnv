# Harness State

This file is append-only evidence for the generic MyCodexEnv harness runtime.
Stable rules belong in `AGENTS.md`, `README.md`, `docs/repo-index.md`, or
`docs/HARNESS_RUNTIME.md`; session facts and phase transitions are appended here.

## Current Snapshot
- phase: validation
- source_of_truth:
  - `AGENTS.md`
  - `docs/repo-index.md`
  - `README.md`
  - `docs/HARNESS_RUNTIME.md`
  - `codex/skills/project-lifecycle-harness/SKILL.md`
- blocked_sources: none
- unsafe_inputs: none
- next_safe_task: continue with requirements artifact template, recovery smoke, or visual evidence dashboard
- required_commands:
  - `python3 test_runner.py`
  - `git diff --check`
  - `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"`
- latest_checkpoint: 2026-05-11T17:14:08-04:00 validated Harness Runtime top 3 helpers after checkpoint clean-status fix
- latest_verification: 2026-05-11T17:14:08-04:00 command=./scripts/verify_codex_env.sh --repo-root "/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv" --codex-home "/Users/kezheng/.codex" --claude-home "/Users/kezheng/.claude"; exit_code=0; key_output=Verification passed.

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

### 2026-05-11T17:12:33-04:00
- phase: validation
- event: checkpoint
- summary: implemented Harness Runtime top 3 helpers
- git:
  - branch: main
  - latest_commit: 07bdf4a
  - dirty_status: unknown
  - dirty_count: 0
- changed_surfaces:
  - `scripts/harness_report.py`
  - `scripts/harness_agent_team.py`
  - `scripts/harness_checkpoint.py`
  - `test_runner.py`
  - `docs/HARNESS_RUNTIME.md`
  - `docs/AGENT_HARNESS_STATUS.md`
- verification:
  - command: `./scripts/verify_codex_env.sh --repo-root "/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv" --codex-home "/Users/kezheng/.codex" --claude-home "/Users/kezheng/.claude"`
  - exit_code: 0
  - key_output: Verification passed.
- blockers:
  - none
- next_safe_task: continue with requirements artifact template, recovery smoke, or visual evidence dashboard

### 2026-05-11T17:14:08-04:00
- phase: validation
- event: checkpoint
- summary: validated Harness Runtime top 3 helpers after checkpoint clean-status fix
- git:
  - branch: main
  - latest_commit: 07bdf4a
  - dirty_status: dirty
  - dirty_count: 3
- changed_surfaces:
  - `scripts/harness_report.py`
  - `scripts/harness_agent_team.py`
  - `scripts/harness_checkpoint.py`
  - `test_runner.py`
  - `docs/HARNESS_RUNTIME.md`
  - `docs/AGENT_HARNESS_STATUS.md`
- verification:
  - command: `./scripts/verify_codex_env.sh --repo-root "/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv" --codex-home "/Users/kezheng/.codex" --claude-home "/Users/kezheng/.claude"`
  - exit_code: 0
  - key_output: Verification passed.
- blockers:
  - none
- next_safe_task: continue with requirements artifact template, recovery smoke, or visual evidence dashboard
