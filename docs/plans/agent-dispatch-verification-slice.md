# Harness Requirements — Agent Dispatch Residual Verification Note

## Goal

Keep the post-PR #5/#6 dispatch-gate record narrow and current. The main
agent-dispatch gate has landed and is covered by `test_runner.py`; the only
remaining optional regression is that a legacy evidence event without
`evidence_kind` or `metadata` must not satisfy the gate and should return `ask`.

## Audience

- Operators checking whether more agent-dispatch work is still required.
- Future workers deciding whether to add the small legacy-evidence regression.

## Scope

- Document the residual requirement only; do not revive the old long verification
  plan.
- Optional future code work: add or confirm one regression for legacy evidence
  events lacking `evidence_kind` and `metadata`, expecting `permissionDecision:
  "ask"`.
- Current branch context: freeze-policy follow-up.

## Non-Goals

- Reworking the dispatch gate design shipped after PR #5/#6.
- Reclaiming obsolete pre-merge assertions as current facts.
- Editing runtime, tests, `docs/harness-state.md`, or code as part of this note.

## Constraints

- Treat this file as a residual-only requirements note.
- Keep future implementation, if any, local/demo first and backed by fresh
  evidence.
- Treat full-suite baseline claims as environment-dependent: `test_runner.py`
  includes runtime checks that shell out to the real `codex` CLI. In a sandbox
  where `codex` is not installed, a `test_verify_after_full_sync` failure is an
  environment gap, not an agent-dispatch regression.
- Preserve existing user and worker changes outside this file.

## Task Demand (D_task)

- estimated_level: low
- L (reasoning/action steps): confirm existing dispatch coverage, add one focused
  legacy-event case only if absent, run focused and full validation.
- H_tool (tool-selection ambiguity): low, because the existing test runner and
  guard subprocess helpers are the expected entrypoints.
- S_state (cross-module state tracking): low, limited to evidence event shape and
  guard receipt matching.
- N_obs (observation/external noise): low, using deterministic fixture data in a
  temporary evidence directory.

## Source Of Truth

- `test_runner.py` dispatch-gate coverage after PR #5/#6.
- `codex/hooks/harness_guard.py` receipt matching behavior.
- `scripts/harness_agent_team.py` and `scripts/harness_evidence.py` evidence
  emission contracts.
- Baseline facts for this revision on the operator machine where `codex` is
  installed: `python3 test_runner.py` green,
  `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex"
  --claude-home "$HOME/.claude" --skip-check app_google_chrome` green, branch
  `codex/mce-20260608-freeze-review-policy`.

## Acceptance Criteria

- [ ] This note treats the main dispatch gate as already landed and verified by
      the current suite.
- [ ] The residual requirement is limited to legacy evidence without
      `evidence_kind` or `metadata` returning `ask`.
- [ ] If implemented later, the regression uses a temporary evidence directory,
      exits 0, returns valid JSON, and asserts `permissionDecision: "ask"`.
- [ ] A sandbox missing the real `codex` CLI is treated as an environment caveat
      for full-suite/runtime verification, not as evidence against this residual
      dispatch note.
- [ ] Requirements validation passes for this file.

## Verification Gate

- `python3 scripts/harness_requirements.py validate docs/plans/agent-dispatch-verification-slice.md`
- `python3 test_runner.py`
- `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome`

## Risks

- Re-expanding this note into the old plan would reintroduce stale claims and
  obscure the actual remaining work.
- Treating a legacy evidence event as valid would weaken the dispatch gate if a
  future regression is introduced.

## Handoff Notes

- Next safe action, if this residual is prioritized: add the single legacy-event
  regression to the existing dispatch-gate test and prove it with focused plus
  full test evidence.
- Otherwise, keep this as context only; do not block unrelated freeze-policy
  follow-up work on it.
- When reporting full-suite evidence from another sandbox, include whether the
  real `codex` CLI was available.
