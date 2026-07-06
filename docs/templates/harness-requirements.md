# Harness Requirements

## Goal
Define the concrete outcome this Harness Runtime slice must deliver.

## Audience
- Codex operator
- Future agent resuming this repo

## Scope
- Describe the files, scripts, docs, or runtime surfaces in scope.

## Non-Goals
- Describe related work that is intentionally out of scope.

## Constraints
- Use Python standard library only unless the repo already provides a dependency.
- Do not commit local evidence logs, credentials, auth files, or transcripts.
- Preserve append-only state and unrelated user changes.

## Task Demand (D_task)
- estimated_level: medium
- L (reasoning/action steps): Estimate the concrete reasoning and action steps required.
- H_tool (tool-selection ambiguity): Describe tool choice uncertainty.
- S_state (cross-module state tracking): Describe state or cross-surface coordination demand.
- N_obs (observation/external noise): Describe external observation or noise demand.

## Source Of Truth
- `AGENTS.md`
- `docs/repo-index.md`
- `docs/harness-state.md`
- `docs/HARNESS_RUNTIME.md`
- `docs/AGENT_HARNESS_STATUS.md`

## Acceptance Criteria
- [ ] Define at least one concrete acceptance criterion.

## open_questions_resolved
- question: Describe any user-facing or architecture ambiguity resolved through grilling.
  answer: Record the confirmed answer or cite the repo source that resolved it.

## Verification Gate
- `python3 test_runner.py`
- `git diff --check`
- `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"`

## Risks
- Runtime docs and scripts can drift if tests do not cover the contract.

## Handoff Notes
- Record phase, verification evidence, blockers, and next safe task in `docs/harness-state.md`.
