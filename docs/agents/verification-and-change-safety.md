# Verification and change safety

## Verification

- Select gates by task mode and changed layer:
  - For `plan`, `review`, and `report-only`, validate only the target artifact, its references, and the authorized write set. Do not run repository or runtime gates unless the task explicitly audits that gate.
  - For low-risk docs or visuals whose write set is limited to root `README.md`/`AGENTS.md` or Markdown, HTML, CSS, and image files under `docs/`, run targeted content/link checks, any relevant surface check, and write-set `git diff --check`; the existing CI owns the full gate. Do not run the public-nav surface gate when the public surface is unchanged.
  - For source, test, or shared-contract changes, run focused or domain tests during iteration, then run `python3 test_runner.py` exactly once after the final material change.
  - For source-only changes under `codex/`, do not run live runtime parity.
- Capture `command`, `exit_code`, `key_output`, and `timestamp` on the first invocation. Do not rerun an unchanged gate only to complete its receipt.
- A later change to relevant source, test, fixture, manifest, or runtime-target content invalidates the prior gate. A commit or push with unchanged tree content does not.
- After an authorized Codex runtime or configuration promotion, keep the final source gate, then rerun the repository gate, exact parity/readback, and:

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
