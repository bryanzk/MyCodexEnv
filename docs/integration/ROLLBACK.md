# Rollback Guide

## Baseline
- Upstream locked commit: `7bcf8d2b60b7c8cd6f06803d87441bf0c2c9f5ed`
- Local mirror: `vendor/claude-code-workflow/`

## Rollback Steps
1. Restore previous branch state:
   - `git checkout <known-good-commit>`
2. Re-run sync:
   - `./bootstrap.sh --eigenphi-backend-root <path>`
3. Verify both homes:
   - `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"`

## Emergency Local Rollback
- `scripts/sync_claude_home.sh` automatically creates `~/.claude/CLAUDE.md.backup.<timestamp>`
- `scripts/sync_codex_home.sh` automatically creates `~/.codex/config.toml.backup.<timestamp>`
