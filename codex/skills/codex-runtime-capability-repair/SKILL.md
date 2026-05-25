---
name: codex-runtime-capability-repair
description: Use when Codex tools or plugins appear installed but unavailable, including browser/computer-use/GitHub capability loss, missing MCP tools, plugin enablement drift, ~/.codex/config.toml rewrite issues, marketplace state loss, or MyCodexEnv sync automation regressions.
---

# Codex Runtime Capability Repair

## Overview

Use this for recurring Codex runtime capability loss on this machine. Diagnose the active runtime state and the write-back path before reinstalling plugins or changing broad configuration.

## Startup

Start read-only and collect both live state and repo source:

```bash
cd /Users/kezheng/Codes/CursorDeveloper/MyCodexEnv
git status --short --branch
test -f AGENTS.md && sed -n '1,220p' AGENTS.md
test -f ~/.codex/config.toml && sed -n '1,260p' ~/.codex/config.toml
ls -1t ~/.codex/config.toml.backup.* 2>/dev/null | head
codex plugin list
codex mcp list
codex doctor
```

If the failure involves SSH, remote hosts, tunnels, or remote services, read `~/.codex/remote-access.md` before any remote operation.

## Diagnosis

1. Do not assume missing tools mean packages are absent. Compare active `~/.codex/config.toml`, latest backups, plugin cache, marketplace entries, and MCP state.
2. Check whether a repo sync or scheduled automation rewrote runtime-owned state:

```bash
rg -n "preserve_table|plugins\.|marketplaces\.|mcp_servers.node_repl|desktop|memories" scripts/sync_codex_home.sh test_runner.py
test -d ~/.codex/automation-workspaces/gstack-dhf-daily-refresh && rg -n "preserve_table|plugins\.|marketplaces\.|mcp_servers.node_repl" ~/.codex/automation-workspaces/gstack-dhf-daily-refresh -g 'sync_codex_home.sh'
```

3. Preserve runtime-owned tables and keys when rendering config from template:
   - `plugins.*`
   - `marketplaces.*`
   - `projects.*`
   - `hooks.state*`
   - `desktop*`
   - `memories`
   - `mcp_servers.node_repl`
   - `mcp_servers.node_repl.env`
4. If automation caused the regression, patch both the repo script and the automation-workspace copy, or document why the workspace copy is absent or intentionally unchanged.
5. Update version policy only after checking the local CLI version and the script's accepted prefixes.

## Repair Rules

- Prefer merge/preserve fixes over one-off plugin reinstall.
- Do not copy `auth.json`, sessions, sqlite, usage data, or caches into the repo.
- Do not overwrite user-edited runtime state without backing it up.
- Treat backup files as evidence, not as a target to blindly restore.
- Keep changes scoped to `scripts/sync_codex_home.sh`, validation scripts, tests, and documented runtime policy unless the observed failure proves another path.

## Verification

Use fresh checks before claiming the capability is fixed:

```bash
python3 test_runner.py
./scripts/verify_codex_env.sh
codex plugin list
codex mcp list
codex doctor
```

For sync regressions, run a temp-home sync through the existing tests rather than experimenting against the live runtime first. If a first verification run fails `skills_managed_present`, rerun the repaired sync before concluding the install is still broken.

Final answers that claim completion must include `command`, `exit_code`, `key_output`, and `timestamp`.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Reinstalling plugins before checking active enablement tables | Inspect config, backups, plugin list, MCP list, and doctor output first. |
| Preserving only missing tables | Merge table contents so extra keys inside existing tables survive. |
| Patching only the repo copy when automation rewrites the runtime | Patch or explicitly account for the automation-workspace copy. |
| Claiming repair from package cache presence | Validate enabled plugin state and MCP visibility. |
