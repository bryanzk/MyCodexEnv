# Codex + Claude Environment Reproduction (Git Clone + One Command)

## Scope
- Target OS: macOS ARM (Apple Silicon)
- One command after clone:
  - `./bootstrap.sh --eigenphi-backend-root <path>`

## What This Repository Syncs
- `codex/config.template.toml` -> `~/.codex/config.toml`
- `codex/AGENTS.md` -> `~/.codex/AGENTS.md`
- `codex/skills/*` -> `~/.codex/skills/*`
- `codex/workflow/*` -> `~/.codex/workflow/*`
- `claude/workflow/*` -> `~/.claude/workflow/*`
- `claude/CLAUDE_INTEGRATION_BLOCK.md` -> 注入 `~/.claude/CLAUDE.md`（不覆盖既有内容）
- `~/.codex/superpowers` pinned by `locks/superpowers.lock`

## Skills Source of Truth
- Repository source of truth is `codex/skills/*`.
- Bootstrap/sync scripts only read `codex/skills/*` when populating `~/.codex/skills/*`.
- Claude workflow source of truth is `claude/workflow/*`.
- The repository now includes Codex-adapted imports of the `gstack` skills: `plan-ceo-review`, `plan-eng-review`, `review`, `ship`, `retro`, `browse`, `qa`, and `setup-browser-cookies`.
- `browse` includes supporting code under `codex/skills/browse/*`; first use requires `./setup` in that directory after sync so Bun can build the local binary and install Playwright Chromium.

## AGENTS Source of Truth
- Codex 通用层 `AGENTS.md` 的唯一源码是 `codex/AGENTS.md`。
- `scripts/sync_codex_home.sh --sync-agents-only` 只同步 `codex/AGENTS.md` 到 `~/.codex/AGENTS.md`，不会改写 config / skills / workflow。
- 多仓库 repo 级 `AGENTS.md` 的批量管理入口是 `python3 scripts/manage_agents.py`。
- 批量更新前会将现存多级 `AGENTS.md` 备份到 `/Users/kezheng/Codes/CursorDeveloper/.agents-backups/<backup_id>/`。

## Security Rules
- Never commit `~/.codex/auth.json`
- Never commit API keys or tokens
- Authentication is machine-local via `codex login`

## Quick Start
```bash
git clone https://github.com/bryanzk/MyCodexEnv.git
cd MyCodexEnv
./bootstrap.sh --eigenphi-backend-root /absolute/path/to/eigenphi-backend-go
```

## Verification
```bash
./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"
```

Verification evidence is appended to `TEST_VERIFICATION.md`.

Repo 级 / 多仓库 `AGENTS.md` 验证：

```bash
python3 scripts/manage_agents.py verify
```

## Idempotency
- Running `bootstrap.sh` multiple times is supported.
- Existing `~/.codex/config.toml` is backed up before overwrite.
- Existing `~/.codex/AGENTS.md` is backed up before `--sync-agents-only` overwrite.
- Existing `~/.claude/CLAUDE.md` is backed up before integration block update.

## Troubleshooting
1. `Homebrew not found`
- Run interactive bootstrap without `--non-interactive`, or install Homebrew manually.

2. `Missing MCP server entrypoint`
- Ensure `--eigenphi-backend-root` points to a repo containing `cmd/mcp-server/main.go`.

3. `codex login status` not authenticated
- Run `codex login`.
