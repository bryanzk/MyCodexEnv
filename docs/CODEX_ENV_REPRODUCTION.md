# Codex Environment Reproduction (Git Clone + One Command)

## Scope
- Target OS: macOS ARM (Apple Silicon)
- One command after clone:
  - `./bootstrap.sh --eigenphi-backend-root <path>`

## What This Repository Syncs
- `codex/config.template.toml` -> `~/.codex/config.toml`
- `codex/AGENTS.md` -> `~/.codex/AGENTS.md`
- `codex/skills/*` -> `~/.codex/skills/*`
- `~/.codex/superpowers` pinned by `locks/superpowers.lock`

## Skills Source of Truth
- Repository source of truth is `codex/skills/*`.
- Bootstrap/sync scripts only read `codex/skills/*` when populating `~/.codex/skills/*`.

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
./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex"
```

Verification evidence is appended to `TEST_VERIFICATION.md`.

## Idempotency
- Running `bootstrap.sh` multiple times is supported.
- Existing `~/.codex/config.toml` is backed up before overwrite.

## Troubleshooting
1. `Homebrew not found`
- Run interactive bootstrap without `--non-interactive`, or install Homebrew manually.

2. `Missing MCP server entrypoint`
- Ensure `--eigenphi-backend-root` points to a repo containing `cmd/mcp-server/main.go`.

3. `codex login status` not authenticated
- Run `codex login`.
