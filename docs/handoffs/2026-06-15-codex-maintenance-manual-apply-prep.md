# Codex Maintenance Manual Apply Prep

**Project / Ticket:** Weekly Codex Maintenance Report  
**Date of Handoff:** 2026-06-15  
**Previous Session Context (optional):** report-only `codex-fluent` diagnosis plus DHF checkpoint append  
**Handoff Author:** Codex

## Executive Summary

This handoff prepares a future manual Codex local-state maintenance pass without
changing any live Codex state today. The report-only diagnosis found that the
main drag is active session volume, not logs or config drift: `~/.codex/sessions`
is about `3.23 GB` across `877` active session files, while
`~/.codex/archived_sessions` is about `241.6 MB` across `479` files.

The next safe action is still preparation, not cleanup. Before any human-run
archive or prune step, active repo chats that may need continuity must get a
durable handoff doc and a copy-paste reactivation prompt, and detached
`~/.codex/worktrees/*` candidates must be reviewed with Codex fully closed.

## Key Decisions & Rationale

- Decision: keep this slice strictly report-only for Codex local state.
  - Rationale: the user explicitly prohibited mutating flags and asked for a
    safe diagnosis flow.
  - Tradeoffs considered: skipping manual apply leaves the bloat in place, but
    preserves recoverability and avoids archiving valuable threads without
    handoffs.

- Decision: store the maintenance-prep continuity note in the repo under
  `docs/handoffs/`.
  - Rationale: MyCodexEnv uses repo-native state and handoff artifacts as the
    durable restart surface.
  - Tradeoffs considered: a chat-only summary is cheaper, but less recoverable
    and easier to lose before the actual maintenance pass.

- Decision: treat large active sessions and detached worktrees as review
  candidates, not auto-archive candidates.
  - Rationale: age and size show drag risk, but not business value.
  - Tradeoffs considered: immediate cleanup would reduce state quickly, but can
    break continuity for ongoing repo work.

## Current Codebase State

- `docs/harness-state.md`: append-only DHF state; now records the weekly
  maintenance diagnosis and the current next-safe-task.
- `docs/handoffs/2026-06-15-codex-maintenance-manual-apply-prep.md`: this
  maintenance-prep handoff for a future manual apply pass.
- `scripts/harness_recover.py`: recovery surface confirming the repo is in
  `handoff` phase and currently points to maintenance preparation.
- `scripts/harness_checkpoint.py`: repo-approved way to append state after this
  prep slice.

## Environment & Commands

- Recovery:
  - `python3 scripts/harness_recover.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --json`
- Runtime probe:
  - `python3 scripts/harness_env_probe.py --codex-home "$HOME/.codex" --json`
- Minimal repo gate for this prep slice:
  - `git diff --check`
- Manual review commands for the future apply session should stay read-only
  until handoffs are confirmed and Codex is closed.

## What Has Been Completed

- [x] Ran a report-only `codex-fluent` diagnosis.
- [x] Confirmed the main drag source is active-session size, not logs.
- [x] Identified large active-session candidates by size and age.
- [x] Identified detached worktree candidates under `~/.codex/worktrees/`.
- [x] Appended the diagnosis result to `docs/harness-state.md`.
- [x] Created this durable handoff for the future manual apply pass.

## Open Questions & Next Steps (Prioritized)

1. **High** — Create comprehensive handoff docs for any active repo chat that
   might still matter after archive, with one reactivation prompt per chat.
2. **High** — Review the largest active sessions first, especially the
   `2026-05-13` session (`287.3 MB`) and the `2026-04-20` /
   `2026-05-11` sessions (`139.4 MB` / `130.6 MB`), and decide whether each is
   keep-active, handoff-then-archive, or already obsolete.
3. **High** — Review detached worktree candidates under
   `~/.codex/worktrees/*/MyCodexEnv` and
   `~/.codex/worktrees/*/gstack-dhf-daily-refresh`, especially the ones around
   `69-70` days old and `25-26` days old.
4. **Medium** — Confirm whether `/private/tmp/gstack-sync-fix` is intentionally
   retained or should be handled as a stale detached worktree in the eventual
   manual apply pass.
5. **Medium** — Only after all of the above is confirmed, run the eventual
   maintenance session with Codex fully closed and with explicit human approval
   for archive/prune actions.

## Constraints & Preferences (Very Important)

- Do not touch: live `~/.codex` sessions, worktrees, logs, or config during
  this prep slice.
- User style notes: prefers evidence-first, repo-native artifacts, and a clear
  next safe task rather than chat-only advice.
- Things we deliberately avoided and why:
  - No `--apply`, archive, prune, move, delete, or normalize actions because
    the task boundary was report-only.
  - No guessing about thread value from size/age alone because large does not
    imply obsolete.

## Reactivation Prompt (Copy-Paste Ready)

```text
We are continuing the Codex local-state maintenance preparation work in MyCodexEnv.

Read these files first:
- docs/handoffs/2026-06-15-codex-maintenance-manual-apply-prep.md
- docs/harness-state.md

Then:
1. Verify the repo state with `python3 scripts/harness_recover.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --json`.
2. Do not mutate `~/.codex` yet.
3. Prepare or review comprehensive handoff docs and reactivation prompts for the active repo chats that may be archived later.
4. Only after handoffs are confirmed, review the largest old active sessions and detached `~/.codex/worktrees` candidates.
5. Treat any eventual manual apply as a separate step that must happen only after Codex is fully closed.

Start by summarizing the current maintenance boundary, the candidates that need human review, and the exact next safe task.
```

## Additional Notes for Future You

- The current DHF state already points to this same next-safe-task, so this
  handoff should stay aligned with `docs/harness-state.md`.
- `session_index.jsonl` currently exposed only lightweight thread metadata in
  the diagnostic slice, so repo/worktree inference for active sessions remained
  limited. Do not overclaim per-thread certainty without a fresh read in the
  future maintenance session.
