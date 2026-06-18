# Codex Goalsmith Source Of Truth

## Purpose

This note resolves the remaining maintenance question around the
`编写 codex-goalsmith skill` thread: the source of truth is not missing.

## Confirmed Source Of Truth

- 2026-06-17 update: `codex-goalsmith` was promoted into the repo-managed global
  skill tree at [`codex/skills/codex-goalsmith/SKILL.md`](/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/codex/skills/codex-goalsmith/SKILL.md), which syncs to `~/.codex/skills/codex-goalsmith/`.
- Repo-local skill path:
  - [`.agents/skills/codex-goalsmith/SKILL.md`](/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/.agents/skills/codex-goalsmith/SKILL.md)
- Supporting repo-local surfaces:
  - [`.agents/skills/codex-goalsmith/README.md`](/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/.agents/skills/codex-goalsmith/README.md)
  - [`.agents/skills/codex-goalsmith/evals/evals.json`](/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/.agents/skills/codex-goalsmith/evals/evals.json)
  - [`/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/skills-lock.json`](/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/skills-lock.json)
- Archived raw session:
  - `~/.codex/archived_sessions/rollout-2026-06-14T11-42-20-019ec6cc-53b6-75a3-95fd-50974676ef66.jsonl`
- Durable rollout summary:
  - `~/.codex/memories/rollout_summaries/2026-06-14T01-49-14-xEEZ-rename_and_harden_goal_skill_to_codex_goalsmith.md`

## What The Thread Actually Represents

The `编写 codex-goalsmith skill` thread is not an orphaned chat with unknown
state. It is part of a known MyCodexEnv repo-local skill lifecycle:

1. install `qiaomu-goal-meta-skill` into workspace `.agents/skills/`
2. run evaluator-style review and repo gates
3. harden the skill through committee review to `10/10`
4. rename the local skill to `codex-goalsmith`

The rollout summary explicitly records:

- repo-local install path under `.agents/skills/`
- committee hardening to `committee.rating: 10/10`
- rename from `qiaomu-goal-meta-skill` to `codex-goalsmith`
- final validation and lockfile update

## Maintenance Decision

- `编写 codex-goalsmith skill` is **not** blocked on missing source material.
- It is recoverable from repo-local `.agents/skills/codex-goalsmith/` plus the
  archived raw session and rollout summary.
- `Review qiaomu-goal-meta-skill` is not a separate active maintenance lane; it
  is the earlier evaluator/review phase inside the same install -> harden ->
  rename lifecycle captured by this handoff and the rollout summary.
- For maintenance triage, this is sufficient to treat the thread as
  `handoff_exists` and to treat the review thread as effectively
  `safe_to_archive` once this note is accepted as the durable continuation
  surface.

## Reactivation Prompt

```text
We are recovering the codex-goalsmith skill history for maintenance review.

Read:
- docs/handoffs/2026-06-15-codex-goalsmith-source-of-truth.md
- .agents/skills/codex-goalsmith/SKILL.md
- skills-lock.json

If deeper historical rationale is needed, consult:
- ~/.codex/memories/rollout_summaries/2026-06-14T01-49-14-xEEZ-rename_and_harden_goal_skill_to_codex_goalsmith.md

Treat codex/skills/codex-goalsmith as the global runtime source of truth.
Use .agents/skills/codex-goalsmith only as the original imported source snapshot.
```
