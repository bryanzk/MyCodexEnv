# Dual Committee Parent Handoff

## Purpose

This handoff collapses three related MyCodexEnv chats from 2026-06-14 into one
durable continuation surface for Codex maintenance triage:

- `MCE-20260614-dual-committee-review-loop`
- `MCE-20260614-committee-review-goal`
- `编写跨模型复审Skill`

These threads belong to the same repo-local workflow family: define the
Codex<->Claude bounded review goal, harden the `dual-committee-review-loop`
skill, and preserve the Claude-read protocol plus verification contract.

## Confirmed Source Of Truth

- Repo-tracked skill source:
  - [`codex/skills/dual-committee-review-loop/SKILL.md`](/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/codex/skills/dual-committee-review-loop/SKILL.md)
- Supporting repo-tracked surfaces:
  - [`codex/skills/dual-committee-review-loop/references/claude-cli-protocol.md`](/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/codex/skills/dual-committee-review-loop/references/claude-cli-protocol.md)
  - [`codex/skills/dual-committee-review-loop/evals/evals.json`](/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/codex/skills/dual-committee-review-loop/evals/evals.json)
  - [`codex/skills/skill-evaluator/SKILL.md`](/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/codex/skills/skill-evaluator/SKILL.md)
  - [`docs/harness-state.md`](/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/docs/harness-state.md)
- Durable memory anchors:
  - `~/.codex/memories/MEMORY.md` task group for `dual-committee-review-loop`
  - Chronicle rollout summaries referenced there for the goal draft, Claude CLI
    auth blocker, hardening loop, and final verification bundle

## What This Thread Family Actually Represents

This is one continuous workflow, not three unrelated chats:

1. draft a copy-ready `/goal` for a bounded Codex<->Claude review loop
2. harden `dual-committee-review-loop` so Codex review, Claude re-review, and
   Codex re-review all use explicit stop conditions and real verification
3. preserve the Claude-side protocol:
   - `command -v claude`
   - `claude --version`
   - `CLAUDE_READY` probe
   - explicit `committee_skill_access`
   - read-only Claude tool boundary
4. validate the result with repo gates and committee-oriented coverage

The Chinese thread `编写跨模型复审Skill` appears to be an overlapping title for
the same skill-creation/hardening family, not a separate maintenance lane.

## Retained Decisions

- `dual-committee-review-loop` is a repo-tracked managed skill under
  `codex/skills/`, not a missing runtime-only artifact.
- The durable verification contract for this family is concrete:
  - Claude CLI presence and readiness checks
  - repo-local gate(s) such as `python3 test_runner.py`
  - `git diff --check`
  - real recorded Claude round-trip evidence with `command`, `exit_code`,
    `key_output`, and `timestamp`
- The skill became reusable only after two hardening decisions were retained:
  - the Claude-side committee skill path switched to
    `$HOME/.claude/skills/committee-review-loop/SKILL.md`
  - `committee_skill_access` became part of the response contract and eval
    coverage
- The workflow must keep the write boundary narrow and avoid broad config sync
  or unrelated skill changes.

## Maintenance Decision

- `MCE-20260614-dual-committee-review-loop` is recoverable from repo state plus
  durable memory anchors.
- `MCE-20260614-committee-review-goal` is not an independent active lane once
  this parent handoff preserves the `/goal` contract and verification shape.
- `编写跨模型复审Skill` can be treated as overlapping with this same parent
  skill family unless a future raw transcript reveals materially different
  scope.

For maintenance triage, this parent handoff is sufficient to mark all three as
`handoff_exists`.

## Constraints

- This handoff does **not** claim current Claude CLI authentication is valid
  today; that must always be rechecked fresh.
- It does **not** replace repo verification or current runtime sync checks.
- It preserves only the minimum reasoning needed so future manual archive/apply
  work does not depend on old chat transcripts.

## Reactivation Prompt

```text
We are recovering the dual-committee review workflow family for maintenance.

Read:
- docs/handoffs/2026-06-15-dual-committee-parent-handoff.md
- codex/skills/dual-committee-review-loop/SKILL.md
- codex/skills/dual-committee-review-loop/references/claude-cli-protocol.md

Use the repo-tracked codex/skills/dual-committee-review-loop directory as the
source of truth.
Do not treat the three 2026-06-14 chats as separate active workstreams unless
new evidence shows materially different scope.
Revalidate Claude CLI auth/readiness fresh before any real dual-committee run.
```
