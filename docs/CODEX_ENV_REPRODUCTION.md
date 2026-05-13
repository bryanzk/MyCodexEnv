# Codex + Claude Environment Reproduction (Git Clone + One Command)

## Scope
- Target OS: macOS ARM (Apple Silicon)
- One command after clone:
  - `./bootstrap.sh`

## What This Repository Syncs
- `codex/config.template.toml` -> `~/.codex/config.toml`
- `codex/AGENTS.md` -> `~/.codex/AGENTS.md`
- `codex/remote-access.md` -> `~/.codex/remote-access.md`
- `codex/remote-hosts.md` -> `~/.codex/remote-hosts.md`
- `codex/skills/*` -> `~/.codex/skills/*`
- `codex/hooks.json` and `codex/hooks/*` -> `~/.codex/hooks.json` and `~/.codex/hooks/*`
- `codex/runtime/*` -> `~/.codex/runtime/*`
- `codex/workflow/*` -> `~/.codex/workflow/*`（排除 `workflow/memory/`）
- `claude/workflow/*` -> `~/.claude/workflow/*`（排除 `workflow/memory/`）
- `claude/CLAUDE_INTEGRATION_BLOCK.md` -> 注入 `~/.claude/CLAUDE.md`（不覆盖既有内容）
- `~/.codex/superpowers` pinned by `locks/superpowers.lock`
- `scripts/install_prereqs.sh` installs pinned `chrome-devtools-mcp@0.20.0` globally via npm
- `chrome-devtools-mcp` is rendered into `~/.codex/config.toml` with `--no-usage-statistics` and `--no-performance-crux`
- EigenPhi MCP server is kept as a commented template block and is disabled by default.
- If Google Chrome is missing, bootstrap installs `google-chrome`
- Harness runtime policy and evidence schema are synced into `~/.codex/runtime/*`; local evidence logs are written under `~/.codex/harness/evidence/*` and are not committed.

## Skills Source of Truth
- Repository source of truth is `codex/skills/*`.
- Bootstrap/sync scripts only read `codex/skills/*` when populating `~/.codex/skills/*`.
- Claude workflow source of truth is `claude/workflow/*`.
- `delivery-harness-framework` is a generic lifecycle router; repo-specific lifecycle skills should stay as adapters that add project paths, commands, safety boundaries, and smoke matrices.
- The repository includes Codex-adapted short-name imports of selected `gstack` skills: `plan-ceo-review`, `plan-eng-review`, `review`, `ship`, `retro`, `browse`, `qa`, and `setup-browser-cookies`.
- The repository also vendors the complete global `gstack` skill set under `codex/skills/gstack` and `codex/skills/gstack-*`, so different machines and projects can use the same namespaced skills after a normal bootstrap/sync.
- `codex/skills/gstack/setup` is intentionally repository-local: it builds support binaries inside `~/.codex/skills/gstack` and does not recreate symlinks to `/Users/kezheng/gstack`.
- `browse` includes supporting code under `codex/skills/browse/*`; first use requires `./setup` in that directory after sync so Bun can build the local binary and install Playwright Chromium.
- The lifecycle-to-skill routing guide is `docs/LIFECYCLE_SKILL_ROUTING.md`; it maps current project workflows and runtime stages to the relevant generic, repo-specific, gstack, validation, review, QA, ship, and documentation skills.

## Related Documentation
- `README.md`: top-level quick start and Harness Runtime overview.
- `docs/repo-index.md`: low-token repo navigation and runtime surface index.
- `docs/HARNESS_RUNTIME.md`: lifecycle, evidence, checkpoint, permission, and subagent contracts.
- `docs/AGENT_HARNESS_STATUS.md`: Agent Harness workflow/infra status map.
- `docs/LIFECYCLE_SKILL_ROUTING.md`: lifecycle stage, workflow, skill, and helper routing.
- `docs/project-lifecycle-harness-flow-cn.html`: Chinese vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-skills.html`: Chinese lifecycle skill/helper routing visual guide.

## AGENTS Source of Truth
- Codex 通用层入口源码是 `codex/AGENTS.md`。
- Remote 访问流程细则拆在 `codex/remote-access.md`；具体主机登记表拆在 `codex/remote-hosts.md`。
- `scripts/sync_codex_home.sh --sync-agents-only` 会同步 `codex/AGENTS.md`、`codex/remote-access.md`、`codex/remote-hosts.md` 到 `~/.codex/`，不会改写 config / skills / workflow。
- 多仓库 repo 级 `AGENTS.md` 的批量管理入口是 `python3 scripts/manage_agents.py`。
- 批量更新前会将现存多级 `AGENTS.md` 备份到 `/Users/kezheng/Codes/CursorDeveloper/.agents-backups/<backup_id>/`。

## Security Rules
- Never commit `~/.codex/auth.json`
- Never commit API keys or tokens
- Authentication is machine-local via `codex login`
- Third-party MCP defaults must avoid `@latest` dynamic execution in committed config; pin versions and disable unnecessary outbound telemetry by default when possible

## Quick Start
```bash
git clone https://github.com/bryanzk/MyCodexEnv.git
cd MyCodexEnv
./bootstrap.sh
```

## Verification
```bash
./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"
```

Verification evidence is appended to `TEST_VERIFICATION.md`.
`TEST_VERIFICATION.md` 属于本地验证证据，默认不提交到 Git。

Repo 级 / 多仓库 `AGENTS.md` 验证：

```bash
python3 scripts/manage_agents.py verify
```

Harness runtime evidence helper:

```bash
python3 scripts/harness_evidence.py append \
  --event-type verification_result \
  --phase validation \
  --command "python3 test_runner.py" \
  --exit-code 0 \
  --key-output "[PASS] all tests"
```

Harness runtime report and checkpoint helpers:

```bash
python3 scripts/harness_report.py --phase validation
python3 scripts/harness_report.py --json --limit 20
python3 scripts/harness_agent_team.py validate PLAN.json
python3 scripts/harness_requirements.py validate docs/templates/harness-requirements.md
python3 scripts/harness_recover.py --repo-root "$(pwd)" --codex-home "$HOME/.codex"
python3 scripts/harness_env_probe.py --codex-home "$HOME/.codex"
python3 scripts/harness_checkpoint.py append \
  --phase validation \
  --summary "validated runtime slice" \
  --changed-surface "scripts/harness_report.py" \
  --verification-command "python3 test_runner.py" \
  --verification-exit-code 0 \
  --verification-key-output "[PASS] all tests" \
  --next-safe-task "continue with handoff"
```

## Idempotency
- Running `bootstrap.sh` multiple times is supported.
- Existing `~/.codex/config.toml` is backed up before overwrite.
- Existing `~/.codex/AGENTS.md` is backed up before `--sync-agents-only` overwrite.
- Existing `~/.claude/CLAUDE.md` is backed up before integration block update.

## Troubleshooting
1. `Homebrew not found`
- Run interactive bootstrap without `--non-interactive`, or install Homebrew manually.

2. `Need EigenPhi MCP locally`
- Uncomment the `eigenphi-blockchain` block in `codex/config.template.toml`, set the backend path, then rerun sync.

3. `codex login status` not authenticated
- Run `codex login`.

4. `chrome-devtools-mcp` not found
- Run `./scripts/install_prereqs.sh` and verify `command -v chrome-devtools-mcp`.

5. `Error starting chat` / `EPERM: operation not permitted, mkdir '/Users/<user>/Documents/...`
- 这是 macOS 对 `Documents` / `Desktop` 等受保护目录的 TCC 权限拦截，不是仓库配置本身报错。
- 先把 Codex Desktop 的新会话目标目录改到 `~/Codes/Codex`、`~/Downloads` 或 `~/.codex/worktrees` 这类非受保护路径。
- 如果必须落到 `Documents` / `Desktop`，在 macOS `系统设置 -> 隐私与安全性 -> 文件与文件夹` 或 `完全磁盘访问权限` 中给 `Codex` 授权后重试。
