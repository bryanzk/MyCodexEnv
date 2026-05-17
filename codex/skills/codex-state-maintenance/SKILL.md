---
name: codex-state-maintenance
description: Use when inspecting, pruning, archiving, or scheduling maintenance for local Codex state, session history, archived sessions, worktrees, logs, or GitHub-hosted maintenance skills.
---

# Codex State Maintenance

## Overview

Use this for local Codex hygiene. Start read-only, preserve backups, and never claim mutation happened when Codex.app or app-server blocked the write.

## Startup

```bash
cd /Users/kezheng/Codes/CursorDeveloper/MyCodexEnv
git status --short --branch
test -f AGENTS.md && sed -n '1,220p' AGENTS.md
ps aux | rg 'Codex.app|codex app-server|codex.*app' || true
```

Durable local state sources on this machine:

- `~/.codex/state_5.sqlite`
- `~/.codex/session_index.jsonl`
- `~/.codex/archived_sessions/`
- `~/.codex/archived_worktrees/`
- `~/.codex/archived_logs/`

## Workflow

1. If installing a GitHub-hosted maintenance skill, use the system installer rather than manual copying:

```bash
python3 /Users/kezheng/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo OWNER/REPO --path PATH --name SKILL_NAME
```

2. For hygiene runs, start with report-only mode. Inspect counts such as old sessions, worktree candidates, logs size, extended paths, and config-prune candidates.
3. Before any archive or `--apply`, check whether Codex.app or `codex app-server` is running. If it is, expect `apply_skipped_codex_running` or `abort_codex_running`; do not retry destructively.
4. If the user pasted exact session lines and says `archive`, scope archival to those selected sessions, not broad age-based cleanup.
5. Put custom backup artifacts under `~/.codex/backups/...` when `Documents/Codex/codex-backups` is not writable.
6. For reminders, create a report-only automation by default. Do not schedule mutating `--apply` unless explicitly requested.

## Verification

After report-only:

```bash
test -f ~/.codex/state_5.sqlite
test -f ~/.codex/session_index.jsonl
```

After a blocked apply, verify no accidental archive directories were created:

```bash
find ~/.codex/archived_sessions ~/.codex/archived_worktrees ~/.codex/archived_logs -maxdepth 1 -name 'keep-codex-fast-*' -print
```

Final answer must include `command`, `exit_code`, `key_output`, and `timestamp`.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Importing a maintenance script as Python app state | Run it as a subprocess or inspect statically. |
| Claiming cleanup ran when Codex was open | Report the exact running-process blocker. |
| Broad archiving after user selected exact sessions | Archive only the selected thread ids. |
| Mutating first | Start report-only unless the user explicitly asked for mutation. |
