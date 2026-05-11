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

## Source Of Truth
- `AGENTS.md`
- `docs/repo-index.md`
- `docs/harness-state.md`
- `docs/HARNESS_RUNTIME.md`
- `docs/AGENT_HARNESS_STATUS.md`

## Acceptance Criteria
- [ ] Define at least one concrete acceptance criterion.

## Verification Gate
- `python3 test_runner.py`
- `git diff --check`
- `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"`

## Risks
- Runtime docs and scripts can drift if tests do not cover the contract.

## Handoff Notes
- Record phase, verification evidence, blockers, and next safe task in `docs/harness-state.md`.
