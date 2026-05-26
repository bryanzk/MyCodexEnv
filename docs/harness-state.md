# Harness State

This file is append-only evidence for the generic MyCodexEnv harness runtime.
Stable rules belong in `AGENTS.md`, `README.md`, `docs/repo-index.md`, or
`docs/HARNESS_RUNTIME.md`; session facts and phase transitions are appended here.

## Current Snapshot
- phase: handoff
- source_of_truth:
  - `AGENTS.md`
  - `docs/repo-index.md`
  - `README.md`
  - `docs/HARNESS_RUNTIME.md`
  - `codex/skills/delivery-harness-framework/SKILL.md`
- blocked_sources: none
- unsafe_inputs: none
- next_safe_task: On the next daily refresh, rerun prepare first and then compare whether any new upstream specialized workflow needs explicit DHF routing boundaries.
- required_commands:
  - `python3 test_runner.py`
  - `git diff --check`
  - `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"`
- latest_checkpoint: 2026-05-26T09:07:09-04:00 daily refresh synced gstack 1.45.0.0 and recorded DHF no-op evaluation
- latest_verification: 2026-05-26T09:07:09-04:00 command=python3 test_runner.py; exit_code=0; key_output=[PASS] all tests

## State Log

### 2026-05-11T15:07:21-04:00
- phase: planning
- event: harness runtime plan accepted for implementation.
- source_of_truth_read:
  - `AGENTS.md`
  - `README.md`
  - `codex/AGENTS.md`
  - `docs/handoffs/2026-05-11-project-lifecycle-harness.md`
  - `codex/skills/delivery-harness-framework/SKILL.md`
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

### 2026-05-11T17:30:17-04:00
- phase: validation
- event: checkpoint
- summary: implemented requirements recovery and env probe harness closures
- git:
  - branch: main
  - latest_commit: 48be28f
  - dirty_status: dirty
  - dirty_count: 7
- changed_surfaces:
  - `docs/templates/harness-requirements.md`
  - `scripts/harness_requirements.py`
  - `scripts/harness_recover.py`
  - `scripts/harness_env_probe.py`
  - `test_runner.py`
  - `docs/HARNESS_RUNTIME.md`
  - `docs/AGENT_HARNESS_STATUS.md`
- verification:
  - command: `./scripts/verify_codex_env.sh --repo-root "/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv" --codex-home "/Users/kezheng/.codex" --claude-home "/Users/kezheng/.claude"`
  - exit_code: 0
  - key_output: Verification passed.
- blockers:
  - none
- next_safe_task: continue with source freshness scoring, orchestration integration, or visual evidence dashboard

### 2026-05-11T20:10:39-04:00
- phase: handoff
- event: checkpoint
- summary: generated current harness runtime handoff document
- git:
  - branch: main
  - latest_commit: 12b4ba6
  - dirty_status: dirty
  - dirty_count: 1
- changed_surfaces:
  - `docs/handoffs/2026-05-11-harness-runtime-current-state.md`
- verification:
  - command: `git diff --check`
  - exit_code: 0
  - key_output: No whitespace errors.
- blockers:
  - none
- next_safe_task: update delivery-harness-framework skill to route through latest runtime helpers and gstack decision points

### 2026-05-11T21:27:17-04:00
- phase: handoff
- event: checkpoint
- summary: documented lifecycle skill routing map
- git:
  - branch: main
  - latest_commit: 2c62d56
  - dirty_status: dirty
  - dirty_count: 6
- changed_surfaces:
  - `docs/LIFECYCLE_SKILL_ROUTING.md`
  - `README.md`
  - `docs/repo-index.md`
  - `docs/CODEX_ENV_REPRODUCTION.md`
  - `docs/HARNESS_RUNTIME.md`
  - `test_runner.py`
- verification:
  - command: `python3 test_runner.py`
  - exit_code: 0
  - key_output: [PASS] all tests
- blockers:
  - none
- next_safe_task: review and stage lifecycle skill routing documentation

### 2026-05-17T09:10:46-04:00
- phase: validation
- event: checkpoint
- summary: implemented cost-aware prompt model router hook
- git:
  - branch: main
  - latest_commit: 9c8d6ba
  - dirty_status: dirty
  - dirty_count: 10
- changed_surfaces:
  - `codex/hooks/model_router.py`
  - `codex/hooks.json`
  - `README.md`
  - `docs/HARNESS_RUNTIME.md`
  - `docs/repo-index.md`
  - `docs/AGENT_HARNESS_STATUS.md`
  - `docs/CODEX_ENV_REPRODUCTION.md`
  - `scripts/verify_codex_env.sh`
  - `scripts/install_prereqs.sh`
  - `test_runner.py`
- verification:
  - command: `./scripts/verify_codex_env.sh --repo-root "/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv" --codex-home "/Users/kezheng/.codex" --claude-home "/Users/kezheng/.claude"`
  - exit_code: 0
  - key_output: Verification passed.
- blockers:
  - none
- next_safe_task: review and stage model router hook changes

### 2026-05-17T09:17:56-04:00
- phase: validation
- event: checkpoint
- summary: hardened model router eval boundaries
- git:
  - branch: main
  - latest_commit: 9c8d6ba
  - dirty_status: dirty
  - dirty_count: 12
- changed_surfaces:
  - `codex/hooks/model_router.py`
  - `docs/MODEL_ROUTER_EVAL_MATRIX.md`
  - `test_runner.py`
  - `docs/HARNESS_RUNTIME.md`
  - `docs/repo-index.md`
  - `README.md`
- verification:
  - command: `python3 test_runner.py`
  - exit_code: 0
  - key_output: [PASS] all tests
- blockers:
  - none
- next_safe_task: review and stage model router hook and eval matrix

### 2026-05-17T10:11:13-04:00
- phase: validation
- event: checkpoint
- summary: added model router response telemetry contract
- git:
  - branch: main
  - latest_commit: 612f829
  - dirty_status: dirty
  - dirty_count: 9
- changed_surfaces:
  - `codex/hooks/model_router.py`
  - `test_runner.py`
  - `README.md`
  - `docs/HARNESS_RUNTIME.md`
  - `docs/MODEL_ROUTER_EVAL_MATRIX.md`
- verification:
  - command: `python3 test_runner.py`
  - exit_code: 0
  - key_output: [PASS] all tests
- blockers:
  - none
- next_safe_task: review and stage model router telemetry changes

### 2026-05-21T11:00:47-04:00
- phase: handoff
- event: checkpoint
- summary: daily refresh synced gstack 1.42.2.0 and recorded DHF no-op evaluation
- git:
  - branch: main
  - latest_commit: c860eb8
  - dirty_status: dirty
  - dirty_count: 7
- changed_surfaces:
  - `codex/skills/gstack`
  - `tasks/gstack-dhf-daily-refresh-2026-05-21.md`
- verification:
  - command: `python3 test_runner.py`
  - exit_code: 0
  - key_output: [PASS] all tests
- blockers:
  - none
- next_safe_task: install bun if runtime gstack setup build is required, then rerun ~/.codex/skills/gstack/setup

### 2026-05-22T09:08:22-04:00
- phase: handoff
- event: checkpoint
- summary: daily refresh synced gstack 1.43.3.0, expanded DHF routing for live-device iOS workflows, and fixed Codex 0.133.0 verification drift
- git:
  - branch: main
  - latest_commit: b527651
  - dirty_status: dirty
  - dirty_count: 91
- changed_surfaces:
  - `codex/skills/gstack`
  - `codex/skills/delivery-harness-framework/SKILL.md`
  - `codex/skills/delivery-harness-framework/evals/evals.json`
  - `docs/LIFECYCLE_SKILL_ROUTING.md`
  - `scripts/verify_codex_env.sh`
  - `scripts/install_prereqs.sh`
  - `test_runner.py`
  - `tasks/gstack-dhf-daily-refresh-2026-05-22.md`
- verification:
  - command: `python3 test_runner.py`
  - exit_code: 0
  - key_output: [PASS] all tests
- blockers:
  - none
- next_safe_task: On the next daily refresh, rerun prepare first and then compare whether any new upstream specialized workflow needs explicit DHF routing boundaries.

### 2026-05-25T09:04:03-04:00
- phase: handoff
- event: checkpoint
- summary: daily refresh confirmed gstack 1.44.0.0 remains aligned and recorded DHF no-op evaluation
- git:
  - branch: main
  - latest_commit: 19d9ab7
  - dirty_status: dirty
  - dirty_count: 1
- changed_surfaces:
  - `tasks/gstack-dhf-daily-refresh-2026-05-25.md`
- verification:
  - command: `python3 test_runner.py`
  - exit_code: 0
  - key_output: [PASS] all tests
- blockers:
  - none
- next_safe_task: On the next daily refresh, rerun prepare first and then compare whether any new upstream specialized workflow needs explicit DHF routing boundaries.

### 2026-05-26T09:07:09-04:00
- phase: handoff
- event: checkpoint
- summary: daily refresh synced gstack 1.45.0.0 and recorded DHF no-op evaluation
- git:
  - branch: main
  - latest_commit: 0f9bcc5
  - dirty_status: dirty
  - dirty_count: 48
- changed_surfaces:
  - `codex/skills/gstack`
  - `tasks/gstack-dhf-daily-refresh-2026-05-26.md`
- verification:
  - command: `python3 test_runner.py`
  - exit_code: 0
  - key_output: [PASS] all tests
- blockers:
  - none
- next_safe_task: On the next daily refresh, rerun prepare first and then compare whether any new upstream specialized workflow needs explicit DHF routing boundaries.
