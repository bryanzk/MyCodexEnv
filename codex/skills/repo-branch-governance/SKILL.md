---
name: repo-branch-governance
description: Git branch governance workflow for repositories that need safe branch auditing, synchronization with main, fast-forward merge or rebase decisions, merged-branch cleanup (including worktrees), and post-action verification. Use when users ask to check branch status, sync branches, merge eligible branches, clean stale branches, or provide ahead/behind-based update recommendations.
---

# Repo Branch Governance

## Overview

Use this skill to execute branch governance tasks safely and consistently:
- audit local and remote branch health,
- converge valuable work into `main`,
- keep active branches fresh with `rebase` or `merge`,
- clean merged branches and dangling worktrees,
- provide a decision-complete status report.

## Quick Start

- Snapshot:
  - `scripts/branch_snapshot.sh`
- One-click main converge (dry-run):
  - `scripts/converge_main_branches.sh`
- One-click main converge (apply):
  - `scripts/converge_main_branches.sh --apply`
- Clean merged branches (dry-run):
  - `scripts/cleanup_merged_branches.sh`
- Clean merged branches (apply):
  - `scripts/cleanup_merged_branches.sh --apply`

## Workflow

1. Synchronize and take a snapshot
- Run `git fetch --all --prune`.
- Run `scripts/branch_snapshot.sh` for a standard report.
- Capture:
  - `git branch -vv --no-abbrev`
  - `git rev-list --left-right --count main...<branch>`
  - `git branch --merged main`
  - `git branch --no-merged main`
  - `git worktree list`
  - `git remote show origin`

2. Classify branches
- Mark each branch as one of:
  - `synced`: `main...branch = 0/0`
  - `ahead_only`: `0/N` (candidate to merge)
  - `behind_only`: `N/0` (needs refresh)
  - `diverged`: `N/M` (needs rebase or merge decision)
  - `merged_stale`: branch fully contained in `main` and safe to delete

3. Stabilize workspace before risky operations
- If working tree is dirty or has untracked files, freeze with:
  - `git stash push -u -m "freeze: <reason>-<date>"`
- Never proceed with destructive branch operations on an ambiguous worktree.

4. Converge `main`
- Prefer script execution:
  - `scripts/converge_main_branches.sh` (plan)
  - `scripts/converge_main_branches.sh --apply` (execute)
- The script merges only ahead-only branches (`0/N`) and skips behind/diverged branches.

5. Refresh diverged branches
- Rebase feature branches onto latest `main`:
  - `git -C <worktree_path> rebase main`
  - resolve conflicts minimally,
  - rerun target tests,
  - `git -C <worktree_path> push --force-with-lease`
- Use `--force-with-lease` only after successful local verification.

6. Clean merged branches
- Use `scripts/cleanup_merged_branches.sh --main main --remote origin --apply`.
- The cleanup script removes linked worktrees first, then local and remote merged branches.
- Never delete branches listed in `git branch --no-merged main`.

7. Verify and report
- Re-run:
  - `git status -sb`
  - `git branch -vv --no-abbrev`
  - `git worktree list`
  - `git remote show origin`
- Report:
  - branch states (ahead/behind),
  - actions performed,
  - final remaining branches,
  - unresolved risks (for example, pending stash entries).

## Safety Rules

- Prefer `--ff-only` merges for predictable history in governance tasks.
- Do not run destructive commands (`reset --hard`, forced deletes without checks).
- Remove worktree before deleting its branch.
- Keep commit history rewrites explicit and auditable.
- If branch state changed unexpectedly during operation, stop and re-snapshot before continuing.

## Output Contract

Return results in this order:
1. current state summary,
2. actions executed,
3. verification evidence,
4. remaining risks and optional next steps.

## Resources

- `scripts/branch_snapshot.sh`: produce a standard non-mutating branch health report.
- `scripts/converge_main_branches.sh`: one-click converge of ahead-only branches into `main` (dry-run by default).
- `scripts/cleanup_merged_branches.sh`: safely clean merged branches and associated worktrees.
- `references/decision-rules.md`: concise decision matrix and command playbook.
