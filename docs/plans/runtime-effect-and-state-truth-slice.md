# Harness Requirements — Observer Phase Parity Slice

## Goal

Make `codex/hooks/harness_observer.py` resolve lifecycle phase with the same
state-snapshot fallback used by `codex/hooks/harness_guard.py`. The current narrow
gap is observer parity: the guard can derive phase through
`phase_from_state_snapshot` and repo-root resolution, while the observer still
uses only `payload.phase`, `tool_input.phase`, `CODEX_HARNESS_PHASE`, then
`unknown`.

## Audience

- Operators relying on observer evidence to explain what phase a tool event
  happened in.
- Future workers extending hook phase resolution without duplicating logic.

## Scope

- Update `codex/hooks/harness_observer.py` in a later implementation slice so it
  reuses the guard's repo-root phase resolution path, including
  `phase_from_state_snapshot`.
- Add or update a focused observer parity regression that proves a repo
  `docs/harness-state.md` snapshot phase is logged by the observer when no
  payload or environment phase exists.
- Keep deferred runtime sync visible as a separate follow-up: observer parity can
  make repo code correct, but live enforcement in `~/.codex` is not current until
  the approved sync step runs.
- Current branch context: freeze-policy follow-up.

## Non-Goals

- Performing the runtime sync into `~/.codex` inside this slice. That sync remains
  a gated follow-up after the freeze-review policy, not an abandoned task.
- Updating `docs/harness-state.md`.
- Reintroducing obsolete pre-merge task assumptions about tests, runtime sync,
  PR state, or dispatch evidence.
- Redesigning the phase policy or changing `harness_guard.py` behavior.

## Constraints

- Observer must remain non-blocking: resolver import or snapshot failures degrade
  to `phase="unknown"` and still append evidence.
- Prefer reusing `harness_guard.py` helpers over copying phase parsing logic.
- Keep the implementation slice small: observer, focused test, and docs only if
  directly needed by that later change.
- Treat full-suite baseline claims as environment-dependent: `test_runner.py`
  includes runtime checks that shell out to the real `codex` CLI. In a sandbox
  where `codex` is not installed, a `test_verify_after_full_sync` failure is an
  environment gap, not an observer-parity regression.
- This revision updates only the requirements note.

## Task Demand (D_task)

- estimated_level: medium
- L (reasoning/action steps): inspect guard resolver, wire observer to the same
  repo-root snapshot path, add parity and fallback checks, run focused and full
  verification.
- H_tool (tool-selection ambiguity): low, because hook subprocess tests and the
  existing requirements/test runner are the intended tools.
- S_state (cross-module state tracking): medium, because observer output must
  match guard phase semantics across payload, environment, repo root, and state
  snapshot.
- N_obs (observation/external noise): low, using deterministic temporary repos and
  evidence directories.

## Source Of Truth

- `codex/hooks/harness_guard.py` for `phase_from_state_snapshot` and repo-root
  phase resolution.
- `codex/hooks/harness_observer.py` current observer phase construction.
- `test_runner.py` hook subprocess conventions.
- Baseline facts for this revision on the operator machine where `codex` is
  installed: `python3 test_runner.py` green,
  `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex"
  --claude-home "$HOME/.claude" --skip-check app_google_chrome` green, branch
  `codex/mce-20260608-freeze-review-policy`.

## Acceptance Criteria

- [ ] This note identifies observer phase parity as the current code gap while
      keeping deferred runtime sync visible as a separate follow-up before live
      enforcement claims.
- [ ] The future implementation proves observer phase matches guard state-snapshot
      resolution when payload and environment phase are absent.
- [ ] Observer fallback remains non-blocking and logs `unknown` if resolver import
      or snapshot lookup fails.
- [ ] The note uses current post-merge baseline facts and does not revive old task
      assumptions.
- [ ] A sandbox missing the real `codex` CLI is treated as an environment caveat
      for full-suite/runtime verification, not as evidence against this slice.
- [ ] Requirements validation passes for this file.

## Verification Gate

- `python3 scripts/harness_requirements.py validate docs/plans/runtime-effect-and-state-truth-slice.md`
- `python3 test_runner.py`
- `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome`

## Risks

- Duplicating guard phase parsing inside the observer would create future drift.
- Making observer imports strict could block tool calls; observability must remain
  best-effort.
- Letting deferred runtime sync fall off the board would leave repo-side
  enforcement correct but not live in `~/.codex`.
- Broadening this slice into runtime sync or state checkpoint work would violate
  the intended narrow implementation boundary.

## Handoff Notes

- Next safe action, if prioritized: implement observer parity only, then capture
  focused hook test evidence and full suite evidence.
- Do not edit `docs/harness-state.md`, runtime copies, or unrelated tests as part
  of this requirements-note revision.
- After freeze-review policy and observer parity are handled, run the separate
  approved runtime sync before saying the new guard/observer enforcement is live.
- When reporting full-suite evidence from another sandbox, include whether the
  real `codex` CLI was available.
