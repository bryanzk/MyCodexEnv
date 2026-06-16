# Active Chat Handoff Backlog For Codex Maintenance

## Purpose

This file is the preparation backlog for any future manual Codex local-state
apply. It does **not** mean the listed chats are safe to archive yet. It only
means they appeared active or recently relevant in the local session index and
should be reviewed for handoff coverage before any manual archive or prune
action.

## How To Use This Backlog

1. Pick one chat at a time.
2. Confirm whether it is still valuable.
3. If valuable and likely to be archived later, create a comprehensive handoff
   doc plus a copy-paste reactivation prompt.
4. Mark its status below.
5. Only after all important chats are covered should a human consider any
   manual apply with Codex fully closed.

Status legend:
- `pending_review`
- `handoff_needed`
- `handoff_exists`
- `keep_active`
- `safe_to_archive`
- `obsolete`

## MyCodexEnv Candidates

| Thread | Updated | Why It Matters | Status |
| --- | --- | --- | --- |
| `Weekly Codex Maintenance Report` | 2026-06-15 | Current maintenance thread; should remain the anchor until manual apply is complete. | `keep_active` |
| `MCE-20260614-committee-skill-integration` | 2026-06-14 | Triage completed: repo state and verification already provide a sufficient continuation surface. | `handoff_exists` |
| `MCE-20260614-dual-committee-review-loop` | 2026-06-14 | Collapsed into `2026-06-15-dual-committee-parent-handoff.md`. | `handoff_exists` |
| `MCE-20260614-committee-review-goal` | 2026-06-14 | Collapsed into `2026-06-15-dual-committee-parent-handoff.md`. | `handoff_exists` |
| `编写跨模型复审Skill` | 2026-06-14 | Treated as overlapping with the same dual-committee parent handoff unless later evidence shows distinct scope. | `handoff_exists` |
| `编写 codex-goalsmith skill` | 2026-06-14 | Source of truth confirmed in `.agents/skills/codex-goalsmith/` plus archived session and rollout summary. | `handoff_exists` |
| `Review qiaomu-goal-meta-skill` | 2026-06-14 | Earlier evaluator/review phase now absorbed by `2026-06-15-codex-goalsmith-source-of-truth.md`. | `safe_to_archive` |
| `Review x-made-easy skill evals` | 2026-06-11 | Collapsed into `2026-06-15-x-made-easy-parent-handoff.md`. | `handoff_exists` |
| `MCE-20260611-install-x-made-easy-skill` | 2026-06-11 | Collapsed into `2026-06-15-x-made-easy-parent-handoff.md`. | `handoff_exists` |
| `MCE-20260609-dhf-manual-outline` | 2026-06-09 | DHF manual work; may already be recoverable from repo docs and state. | `pending_review` |
| DHF manual review threads on 2026-06-09 | 2026-06-09 | Several review-only threads likely collapse to final doc state; inspect for any missing rationale worth preserving. | `pending_review` |

## ShipQ Candidates

| Thread | Updated | Why It Matters | Status |
| --- | --- | --- | --- |
| `Review Gmail intake plans` | 2026-06-11 | Collapsed into `2026-06-15-shipq-parent-handoff-for-2026-06-11-review-subthreads.md`. | `safe_to_archive` |
| `Review ShipQ plan revisions` | 2026-06-11 | Collapsed into `2026-06-15-shipq-parent-handoff-for-2026-06-11-review-subthreads.md`. | `safe_to_archive` |
| `Review Sea Cargo plans` | 2026-06-11 | Collapsed into `2026-06-15-shipq-parent-handoff-for-2026-06-11-review-subthreads.md`. | `safe_to_archive` |
| `SQ-20260604-gmail-fixture-capture` | 2026-06-04 | Fixture capture work often carries exact boundaries that should not be lost. | `handoff_needed` |
| `SQ-20260603-cargo-sidebar-ui` | 2026-06-03 | UI thread may already be superseded; confirm whether repo/native docs are enough. | `pending_review` |
| ShipQ doc/review threads on 2026-06-01 to 2026-06-06 | 2026-06-01..11 | Multiple review threads may collapse into a few durable handoffs if decisions are already captured. | `pending_review` |
| `SQ-20260530-gmail-intake-adr-review` | 2026-05-30 | ADR review may still matter if rationale is not fully in the ADR/harness state. | `pending_review` |

## Review Heuristics

- Prefer `keep_active` for threads that are still the live working surface.
- Prefer `handoff_needed` when the chat likely contains exact reasoning,
  boundaries, or next steps not guaranteed to exist in repo docs.
- Prefer `pending_review` when there may be overlap or duplication and the
  thread could collapse into another handoff.
- Prefer `safe_to_archive` only after a durable handoff doc exists or the repo
  already fully captures the continuation surface.
- Prefer `obsolete` only when both the code/doc state and the future task value
  are clearly gone.

## Immediate Next Pass

Start with these five:

1. `Review Gmail intake plans`
2. `Review ShipQ plan revisions`
3. `Review Sea Cargo plans`
4. `MCE-20260614-committee-skill-integration`
5. `编写 codex-goalsmith skill`

For each one, decide:
- Is it still valuable?
- Is there already a repo-native handoff?
- If not, what exact handoff doc path should be created before manual apply?
