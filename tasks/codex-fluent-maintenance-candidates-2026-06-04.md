# Codex Fluent Maintenance Candidates - 2026-06-04

## Scope

This is the follow-up to the report-only `codex-fluent` diagnosis from 2026-06-04.

No active Codex state was archived, moved, rotated, normalized, deleted, or edited while producing this file. The purpose is to make the next maintenance pass safe: preserve valuable work with handoffs first, then archive only after backup and explicit confirmation.

## Definition of Done

- Identify active-session drag sources with fresh local evidence.
- Separate archive candidates from sessions that require handoff first.
- Identify stale or risky worktree candidates without deleting them.
- Capture automation hygiene issues that can be fixed before the next scheduled report.
- State the exact next action before any mutating maintenance.

## Fresh Snapshot

Captured at `2026-06-04T13:57:49Z`.

- Active sessions: `819`, `2.9 GiB`.
- Archived sessions: `477`.
- Top 20 active session files: `1.2 GiB`.
- Active sessions older than 90 days: `259`, `983.4 MiB`.
- Active sessions older than 60 days: `488`, `1.4 GiB`.
- Active metadata-bloat candidates over 20k chars in `title` / `preview` / `first_user_message`: `9`, `15.7 MiB`.
- Codex worktree roots scanned: top candidates total under `~/.codex/worktrees` remain about `650 MiB` from the prior report-only scan.
- Weekly maintenance automation still points at missing `~/.codex/skills/keep-codex-fast/scripts/keep_codex_fast.py`; `~/.codex/skills/codex-fluent` exists.

## Primary Findings

The largest drag is still active session state, not log files. The active path is more than 10x larger than archived session state, and nearly half of active sessions are older than 60 days.

The highest UI-risk issue is metadata bloat. A few thread rows have very large `title`, `preview`, and `first_user_message` fields even when the underlying JSONL file is small. These rows are likely to slow thread lists and search more than their file size suggests.

Worktrees are a secondary cleanup lane. Several detached worktrees look clean and old enough to archive later, but at least one MyCodexEnv worktree is dirty and several non-MyCodexEnv worktrees need repository-specific inspection before touching.

## Handoff Requirements

Before archiving any session that might be continued, create a repo-local handoff document with:

- Executive summary.
- Key decisions and rationale.
- Current codebase state.
- Commands and environment notes.
- Completed work.
- Prioritized next steps.
- Constraints and preferences.
- Copy-paste reactivation prompt.

Suggested handoff locations:

- ShipQ: its existing handoff or harness-state surface.
- MyCodexEnv: `docs/handoffs/` or `docs/harness-state.md`, depending on whether it is a one-off thread or a continuing runtime lane.
- Other project repos: `docs/codex-handoffs/YYYY-MM-DD-topic.md` when no project-specific convention exists.

## Active Session Candidate Groups

### Batch A - Metadata-Bloat Fix Candidates

These are high UI-value candidates because they have oversized metadata fields. Do not mutate SQLite in a live Codex session. If handled, do it after backup and Codex shutdown.

| Priority | Session | CWD | Age | File Size | Max Metadata Len | Required Gate |
|---|---|---|---:|---:|---:|---|
| A1 | `019c48ef-2eb2-7e63-94dc-f296f831db18` | `CallTraceSniffer` | 113d | 4.4 MiB | 120300 | Backup + inspect original first user message |
| A2 | `019e1740-4a8d-7032-bd81-f85f0df979f6` | `Transreader` | 24d | 309.6 KiB | 48426 | Handoff/owner decision |
| A3 | `019e08fb-2d3b-7f72-b9a8-21d824e2171e` | `MyCodexEnv` | 26d | 568.6 KiB | 45090 | MyCodexEnv handoff first |
| A4 | `019e18c9-d55b-7fb0-a0a3-9b92ba23f171` | `MyCodexEnv` | 23d | 267.7 KiB | 44715 | MyCodexEnv handoff first |
| A5 | `019e1706-d031-7b33-b0e0-ce72bd49f649` | `Transreader` | 24d | 254.7 KiB | 41766 | Handoff/owner decision |
| A6 | `019e1751-e9ca-7601-9641-81d9ee127c1b` | `MyCodexEnv` | 24d | 126.9 KiB | 39311 | MyCodexEnv handoff first |
| A7 | `019e1789-6bb5-77a2-99b2-2ee659f7cd00` | `RealEstateImage` | 23d | 167.6 KiB | 36910 | Handoff/owner decision |
| A8 | `019caec6-d556-7dd3-8b71-90d697899f09` | `WarRoom` | 93d | 9.2 MiB | 27167 | Likely archive after owner decision |
| A9 | `019df4eb-dc9e-7e22-b84b-f7b7d2241995` | `ShipQ` | 30d | 340.0 KiB | 20333 | ShipQ handoff first |

### Batch B - Old Active Session Archive Candidates

These are the best bulk cleanup candidates after handoff review:

| Group | Active Count | Size | Notes |
|---|---:|---:|---|
| Older than 90 days | 259 | 983.4 MiB | Best first archive batch after owner review |
| Older than 60 days | 488 | 1.4 GiB | Larger second batch after validating active projects |

High-impact old project groups:

| CWD | Active Count | Size | Old Count | Initial Classification |
|---|---:|---:|---:|---|
| `eigenphi-cli-arb-mvp` | 55 | 362.8 MiB | 55 | Good archive candidate after repo continuity check |
| `fp-detector` | 90 | 288.7 MiB | 90 | Good archive candidate after repo continuity check |
| `MEVScan` | 95 | 248.4 MiB | 95 | Good archive candidate after repo continuity check |
| `CallTraceSniffer` | 44 | 151.9 MiB | 44 | Good archive candidate; includes metadata-bloat row |
| `MEVAL` | 54 | 114.7 MiB | 54 | Good archive candidate after owner decision |
| `RetirementCalculator` | 5 | 134.6 MiB | 5 | One large session dominates; likely archive after handoff decision |
| `WarRoom` | 9 | 47.7 MiB | 9 | Includes metadata-bloat row |
| `cleanprice` | 5 | 40.8 MiB | 5 | Likely archive after owner decision |

### Batch C - Largest Active Session Files

These 20 files alone account for `1.2 GiB`. They should be reviewed before broad archival because some belong to current or recent project lanes.

| Session | CWD | Age | Size | Gate |
|---|---|---:|---:|---|
| `019e20f5-eb24-7a32-aee3-1e437f0be7f5` | `startup4chinese-website` | 20d | 274.0 MiB | Handoff first if still active |
| `019dad5d-a726-7241-af6d-49481862bfb3` | `RetirementCalculator` | 37d | 132.9 MiB | Owner decision |
| `019e1a17-73cc-7ee3-8f87-d6e874d46079` | `MyCodexEnv` | 22d | 124.6 MiB | MyCodexEnv handoff first |
| `019b9921-f9e6-72d0-bff9-b6481c3992d6` | `CallTraceSniffer` | 143d | 94.4 MiB | Likely archive after owner decision |
| `019e884c-d369-75f0-9a7f-71ad9e013f4c` | `ShipQ` | 0d | 67.5 MiB | Do not archive without current ShipQ handoff |
| `019dff05-0df0-7701-b08d-716973155c5a` | `Transreader` | 27d | 67.4 MiB | Handoff first if still active |
| `019dd40c-efc3-7b21-ac67-9157568c3271` | `Downloads/Startup4Chinese` | 29d | 64.5 MiB | Owner decision |
| `019e4597-2942-7503-a85a-8d147957bb85` | `Downloads/Startup4Chinese` | 4d | 40.2 MiB | Recent; handoff first |
| `019e55c1-9ab4-7543-afec-c7e85d7d8afb` | `ShipQ` | 9d | 38.1 MiB | Do not archive without current ShipQ handoff |
| `019c9017-87be-7581-8bce-b73025f83a8b` | `eigenphi-cli-arb-mvp` | 99d | 35.8 MiB | Good archive candidate after repo continuity check |

## Active Project Handoff Priority

Do not archive these groups until their repo-local continuation surface is current:

| Project | Active Count | Size | Reason |
|---|---:|---:|---|
| `ShipQ` | 112 | 415.9 MiB | Current high-frequency project; needs exact slice/harness handoff |
| `MyCodexEnv` | 111 | 227.7 MiB | Current runtime/harness maintenance repo |
| `startup4chinese-website` | 16 | 343.4 MiB | Recent large session dominates |
| `Transreader` | 42 | 166.2 MiB | Recent work plus metadata-bloat rows |
| `RealEstateImage` | 12 | 26.6 MiB | Has a metadata-bloat row; handoff before archive if still valuable |

## Worktree Candidates

### Likely Archive Candidates After Backup

These appeared detached and clean in the fresh scan:

| Path | Size | Age | Head |
|---|---:|---:|---|
| `~/.codex/worktrees/4b76/Transreader` | 82.4 MiB | 32d | `266549c` |
| `~/.codex/worktrees/06ec/gstack-dhf-daily-refresh` | 55.1 MiB | 13d | `c860eb8` |
| `~/.codex/worktrees/f91f/gstack-dhf-daily-refresh` | 55.1 MiB | 13d | `1deb94b` |
| `~/.codex/worktrees/a19b/gstack-dhf-daily-refresh` | 17.7 MiB | 14d | `090727a` |
| `~/.codex/worktrees/fdbd/gstack-dhf-daily-refresh` | 17.7 MiB | 14d | `2387f82` |
| `~/.codex/worktrees/4798/gstack-dhf-daily-refresh` | 17.7 MiB | 14d | `2387f82` |
| `~/.codex/worktrees/6bcf/gstack-dhf-daily-refresh` | 17.7 MiB | 14d | `8f1573c` |
| `~/.codex/worktrees/29a1/gstack-dhf-daily-refresh` | 17.7 MiB | 14d | `7c52e7c` |
| `~/.codex/worktrees/f18a/gstack-dhf-daily-refresh` | 17.6 MiB | 15d | `2fcc1cc` |
| `~/.codex/worktrees/*/MyCodexEnv` at `a5c391d` | about 46 MiB total | 58d | clean detached duplicates |

### Blocked Worktree Candidates

Do not archive these until individually inspected:

| Path | Reason |
|---|---|
| `~/.codex/worktrees/a649/MyCodexEnv` | Dirty: `README.md`, DHF skill/docs/harness files modified |
| `~/.codex/worktrees/f6ea/eigenphi-cli-arb-mvp` | Git status unresolved in scan; 89.4 MiB |
| `~/.codex/worktrees/b6fb/eigenphi-cli-arb-mvp` | Git status unresolved in scan; 89.4 MiB |
| `~/.codex/worktrees/7372/eigenphi-cli-arb-mvp` | Git status unresolved in scan; 89.4 MiB |
| `~/.codex/worktrees/stash-recovery/fp-detector` | Git status unresolved in scan; likely intentional recovery state |
| `~/.codex/worktrees/Transreader-gh-pages/pdfs` | Not a repo root in scan; inspect manually |
| `~/.codex/worktrees/0402/out` | Not a repo root in scan; inspect manually |

## Automation Hygiene Candidate

Initial finding: the weekly report-only automation referenced the old `keep-codex-fast` path:

```text
/Users/kezheng/.codex/skills/keep-codex-fast/scripts/keep_codex_fast.py
```

That script does not exist. The current skill is `codex-fluent`.

Applied follow-up at `2026-06-04T14:03:21Z`:

- Backed up the original automation config to `~/.codex/backups/codex-fluent-20260604-100321/weekly-codex-maintenance-report/automation.toml`.
- Updated `~/.codex/automations/weekly-codex-maintenance-report/automation.toml` to invoke the `codex-fluent` skill for report-only diagnosis.
- Preserved the non-mutating boundary: no `--apply`, no archive, no move, no prune, no rotate, no normalize, no delete, and no mutating fallback after failure.
- Added `potential thread metadata bloat` to the weekly report fields.

## Proposed Maintenance Sequence

1. Create or refresh handoffs for `ShipQ`, `MyCodexEnv`, `startup4chinese-website`, and any other session group the user wants to continue.
2. Keep the weekly maintenance automation on report-only `codex-fluent` diagnosis.
3. Prepare a timestamped backup of `~/.codex/state_5.sqlite`, `~/.codex/sessions`, `~/.codex/archived_sessions`, and `~/.codex/worktrees`.
4. Close Codex, or explicitly choose a maintenance mode that waits for Codex to exit.
5. Archive Batch B old active sessions first, excluding the active-project handoff-protected list.
6. Archive clean detached worktrees only after confirming no active branch/work is attached.
7. Re-run `codex-fluent` diagnosis and compare before/after active-session size, thread metadata, worktree size, and Codex startup/session-switching feel.

## Next Safe Action

Create handoffs for `ShipQ` and `MyCodexEnv` before any session archival. These are the highest-risk active-project groups because they are current continuation surfaces, and archiving their heavy sessions without a repo-local handoff would make future work harder to resume.

## Verification Evidence

- `date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'`
  - exit_code: `0`
  - key_output: `timestamp=2026-06-04T13:57:49Z`
- read-only Codex state scanner
  - exit_code: `0`
  - key_output: active `819 / 2.9 GiB`; top20 active `1.2 GiB`; old90 `259 / 983.4 MiB`; metadata-bloat `9 / 15.7 MiB`
- `git status --short`
  - exit_code: `0`
  - key_output: no output before this file was written by Codex in this turn
- `python3 - <<'PY' ... tomllib validation ... PY`
  - exit_code: `0`
  - key_output: `automation_toml_valid=true`; `prompt_uses_codex_fluent=true`; `missing_keep_codex_fast_reference=false`; `non_mutating_boundary=true`
