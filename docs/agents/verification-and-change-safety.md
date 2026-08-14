# Verification and change safety

## Verification

- Run `python3 test_runner.py` as the canonical repository gate.
- For documentation or configuration changes, verify referenced paths, links, and command names.
- After changing Codex runtime or configuration synchronization, also run:

  ```bash
  ./scripts/verify_codex_env.sh \
    --repo-root "$(pwd)" \
    --codex-home "<codex-home>" \
    --claude-home "<claude-home>"
  ```

- When plugin or MCP state is in scope, also inspect `codex plugin list` and `codex mcp list`.

## Change boundaries

- Treat scripts that synchronize, batch-update, or write runtime state as high risk.
- Codex state and maintenance tasks are report-only unless the user explicitly authorizes mutation; do not delete, archive, move, or clean worktrees, sessions, or local state by default.
- When changing an entry command, directory structure, or public interface, update the corresponding README, documentation, and tests.
- Ask before changing a public interface, deployment method, configuration default, or data format, and before deleting or renaming a key path or bypassing an existing verification entry point.
