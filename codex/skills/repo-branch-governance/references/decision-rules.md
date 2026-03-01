# Branch Governance Decision Rules

## 1) Classification

Use `git rev-list --left-right --count main...<branch>`:
- `0 0`: synced
- `0 N`: ahead_only (candidate to merge)
- `N 0`: behind_only (needs refresh)
- `N M`: diverged (needs rebase or merge decision)

## 2) Merge Rules

- Prefer fast-forward merge:
  - `git checkout main`
  - `git pull --ff-only origin main`
  - `git merge --ff-only <branch>`
  - `git push origin main`
- For batch converge, use:
  - dry-run: `scripts/converge_main_branches.sh`
  - apply: `scripts/converge_main_branches.sh --apply`
- If `--ff-only` fails, choose explicit rebase flow instead of accidental merge commits.

## 3) Rebase Rules

- Rebase branch onto latest `main`.
- Resolve conflicts minimally and run relevant tests.
- Push with `--force-with-lease`, never `--force`.

## 4) Cleanup Rules

- Delete only branches returned by `git branch --merged main`.
- If a branch is attached to a worktree, remove worktree first.
- Delete local branch first, then remote branch.

## 5) Freeze Rules

- If there are unstaged or untracked changes before governance actions, freeze first:
  - `git stash push -u -m "freeze: <reason>-<date>"`
- Include stash status in final report so pending work is not forgotten.

## 6) Verification Checklist

- `git status -sb`
- `git branch -vv --no-abbrev`
- `git worktree list`
- `git remote show origin`
- target `main...<branch>` counts after operation
