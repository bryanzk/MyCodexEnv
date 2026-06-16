# First Five Active Chat Triage For Codex Maintenance

## Purpose

This document records the first-pass triage of the five highest-priority chats
from the maintenance backlog. The goal is to decide which chats still require a
dedicated handoff before any future manual Codex state apply.

## Triage Decisions

### 1. `Review Gmail intake plans`

- Decision: `safe_to_archive_after_parent_handoff`
- Why:
  - The raw session exists and is a read-only committee review sub-thread in
    `ShipQ`.
  - Its final output is a review result with `committee.rating=8.2/10` and a
    revision brief against a six-plan review set, not a standalone implementation
    lane.
  - The durable continuation surface should live in the parent ShipQ planning /
    remediation state, not in this review sub-thread alone.
- Needed before archive:
  - Ensure the parent ShipQ continuity surface captures the failing review,
    revision brief, and the specific plan files under review.

### 2. `Review ShipQ plan revisions`

- Decision: `safe_to_archive_after_parent_handoff`
- Why:
  - The raw session exists and is another read-only committee re-review
    sub-thread in the same ShipQ planning family.
  - Its final output declares the revised Slice A/B plans closed at
    `committee.rating=10/10`.
  - This is useful evidence, but not a separate active workstream if the parent
    ShipQ planning handoff captures “re-review passed” plus the exact plan scope.
- Needed before archive:
  - Parent ShipQ handoff should capture that the two-file re-review passed and
    name the specific slice files and verification anchors.

### 3. `Review Sea Cargo plans`

- Decision: `safe_to_archive_after_parent_handoff`
- Why:
  - The raw session exists and is the earlier review sub-thread for the same
    2026-06-11 sea-cargo planning chain.
  - Its final output contains concrete findings that were later tightened by the
    subsequent re-review threads.
  - Valuable reasoning remains, but it belongs in one parent ShipQ planning
    handoff rather than as a separately preserved active chat.
- Needed before archive:
  - Parent ShipQ handoff should preserve the main unresolved findings lineage:
    Decimal exactness, total-row dimension promotion, Slice B state/privacy
    checks, and generated-output determinism.

### 4. `MCE-20260614-committee-skill-integration`

- Decision: `handoff_exists_via_repo_state`
- Why:
  - The raw session exists and the final output already names modified files,
    runtime-copy sync, and fresh verification evidence.
  - The repo currently contains the resulting changes in
    `skill-creator/SKILL.md` and `skill-evaluator/SKILL.md` references, plus
    the general runtime and routing surfaces.
  - This thread is recoverable from repo state plus its completion summary, so
    it does not need another dedicated handoff for maintenance purposes.
- Needed before archive:
  - None beyond keeping the repo-native runtime surfaces and validation evidence.

### 5. `编写 codex-goalsmith skill`

- Decision: `handoff_exists_via_repo_local_skill`
- Why:
  - The actual source of truth is repo-local under
    `.agents/skills/codex-goalsmith/`, not under `codex/skills/`.
  - `skills-lock.json` still references `codex-goalsmith`, and the repo-local
    skill directory includes `SKILL.md`, README, manifest, evals, and helper
    files that make the outcome recoverable from current workspace state.
  - Matching archived raw sessions exist under `~/.codex/archived_sessions`,
    and the durable rollout summary in
    `~/.codex/memories/rollout_summaries/2026-06-14T01-49-14-xEEZ-rename_and_harden_goal_skill_to_codex_goalsmith.md`
    explicitly records the rename/hardening flow into `.agents/skills/codex-goalsmith`.
- Needed before archive:
  - Keep the dedicated source-of-truth handoff at
    `docs/handoffs/2026-06-15-codex-goalsmith-source-of-truth.md` with the repo
    path, archived raw sessions, and rollout-summary anchor.

## Consolidated Result

- Three ShipQ review threads can collapse into one parent ShipQ handoff rather
  than staying individually active.
- `MCE-20260614-committee-skill-integration` is already recoverable from repo
  state and fresh verification evidence.
- `编写 codex-goalsmith skill` is also recoverable from durable repo state plus
  archived/raw memory surfaces after correcting the source-of-truth path.

## Next Safe Task

The first five high-priority chats now all have durable continuation surfaces.
Before any manual apply, continue down the backlog and create the next missing
repo-native handoff for any remaining `needs_handoff` or `pending_review`
threads, with Codex fully closed before later manual state cleanup.
