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
- `~/.codex/superpowers` pinned by `locks/superpowers.lock`, then registered as marketplace `superpowers-dev` and installed as `superpowers@superpowers-dev`
- `scripts/install_prereqs.sh` installs pinned `chrome-devtools-mcp@0.20.0` globally via npm
- `chrome-devtools-mcp` is rendered into `~/.codex/config.toml` with `--no-usage-statistics` and `--no-performance-crux`
- EigenPhi MCP server is kept as a commented template block and is disabled by default.
- If Google Chrome is missing, bootstrap installs `google-chrome`
- Harness runtime policy, compatibility evidence schema, and split evidence schemas are synced into `~/.codex/runtime/*`; local evidence logs are written under `~/.codex/harness/evidence/*` and are not committed.
- `codex/runtime/resolve_codex_cli.sh` validates every candidate with `--version` before use, prefers a functional npm global CLI, and then falls back across the current ChatGPT/Codex app bundle paths, so stale npm/Homebrew shims do not satisfy automation checks.
- `codex/hooks/model_router.py` is synced as the prompt/subtask model router. It emits a non-blocking JSON recommendation for `gpt-5.4-mini`, `gpt-5.4`, or `gpt-5.5` based on complexity and quality-floor signals; runtimes or wrapper scripts that can switch models may consume the recommendation directly.
- `codex/hooks/dhf_preprompt.py` is the only global DHF `UserPromptSubmit` dispatcher. It treats malformed, non-dict, or missing-cwd payloads as continue-only, applies `no dhf` / `skip dhf` and Chinese equivalents before any routing, injects generic DHF context only for explicit non-ShipQ activation such as complex/resume/takeover/handoff/state-conflict prompts, and lazily loads the ShipQ adapter only when `cwd` is under the configured ShipQ root.
- `codex/hooks/shipq_dhf_preprompt.py` remains a synced adapter file for ShipQ cwd only; it is not registered directly in `codex/hooks.json`, and ordinary non-ShipQ prompts must not import, read, execute, or leak adapter-specific context.

## Skills Source of Truth
- Repository source of truth is `codex/skills/*`.
- Bootstrap/sync scripts only read `codex/skills/*` when populating `~/.codex/skills/*`.
- Superpowers uses the plugin-first startup path on current pins: `scripts/sync_codex_home.sh` checks out the locked `~/.codex/superpowers`, registers the local `superpowers-dev` marketplace, installs `superpowers@superpowers-dev`, and new Codex sessions should use exposed `superpowers:*` skills. The legacy `~/.codex/superpowers/.codex/superpowers-codex` binary is only a conditional fallback when an older checkout still contains it.
- Claude workflow source of truth is `claude/workflow/*`.
- `delivery-harness-framework` is a generic lifecycle router; repo-specific lifecycle skills should stay as adapters that add project paths, commands, safety boundaries, and smoke matrices.
- The repository includes Codex-adapted short-name imports of selected `gstack` skills: `plan-ceo-review`, `plan-eng-review`, `review`, `ship`, `retro`, `browse`, `qa`, and `setup-browser-cookies`.
- The repository also vendors the complete global `gstack` skill set under `codex/skills/gstack` and `codex/skills/gstack-*`, so different machines and projects can use the same namespaced skills after a normal bootstrap/sync.
- `codex/skills/gstack/setup` is intentionally repository-local: it builds support binaries inside `~/.codex/skills/gstack` and does not recreate symlinks to `/Users/kezheng/gstack`.
- `scripts/prepare_gstack_dhf_daily_refresh.py` is the daily refresh automation preflight entry; it requires a standalone clone, retries GitHub DNS probes for about two minutes before deferring, checks out the dedicated `automation/gstack-dhf-daily-refresh` branch rebased on `origin/main`, and returns fresh dry-run evidence before any repo mutation. Automation commits first push that branch.
- `scripts/merge_gstack_refresh_if_safe.py` is the only supported unattended path from the automation branch into `main`; it requires a clean standalone clone, `--verified`, and an ahead-only branch state before it fast-forwards `main`.
- `scripts/sync_local_main_if_safe.py` is the optional post-merge local sync helper; it fast-forwards a local `main` worktree only when the worktree is already on `main`, clean, and behind-only relative to `origin/main`.
- `scripts/sync_gstack_vendor.py` is the repeatable bulk snapshot sync entry for `codex/skills/gstack`; it clones upstream, validates `VERSION` / `package.json` / `setup`, reports `needs_update` / `diff_files`, replaces the vendor tree, deletes stale files, and strips upstream `.git` metadata.
- `browse` includes supporting code under `codex/skills/browse/*`; first use requires `./setup` in that directory after sync so Bun can build the local binary and install Playwright Chromium.
- The lifecycle-to-skill routing guide is `docs/LIFECYCLE_SKILL_ROUTING.md`; it maps current project workflows and runtime stages to the relevant generic, repo-specific, gstack, validation, review, QA, ship, and documentation skills.

Bulk refresh command:

```bash
python3 scripts/prepare_gstack_dhf_daily_refresh.py --json
python3 scripts/sync_gstack_vendor.py --repo-root "$(pwd)" --source https://github.com/garrytan/gstack.git --dry-run --json
python3 scripts/sync_gstack_vendor.py --repo-root "$(pwd)" --source https://github.com/garrytan/gstack.git
python3 test_runner.py
```

## Codex Thread Discipline and Fluent Triage

Thread discipline and old-session triage are guaranteed in three layers:

1. **Agent policy (best effort, immediate).** `codex/AGENTS.md` owns the
   global contract: each task freezes a `THREAD_DISCIPLINE_V1` anchor envelope
   (one task, one evidence-backed `repo_anchor`, one `mode_anchor`) and carries
   a `THREAD_DISCIPLINE_SUMMARY_V1` marker across summaries. A confirmed first
   compaction refreshes a concise checkpoint; a confirmed second compaction, or
   an unknown/conflicting compaction ordinal, stops normal work and returns a
   terminal chat handoff. Chat handoff is the default: a repo-native handoff
   file requires the original task to have explicitly authorized the exact
   documentation path, and archive or apply authorization does not imply
   file-write authorization.
2. **Deterministic weekly audit (report-only).** The scanner
   `codex/skills/codex-fluent/scripts/report_active_sessions.py` reads only
   `CODEX_HOME/sessions/**/*.jsonl` and `CODEX_HOME/session_index.jsonl`,
   counts compactions from decoded top-level JSONL objects with
   `type == "compacted"`, and ranks eligible non-subagent sessions by
   transcript size. Invocation:

   ```bash
   python3 ~/.codex/skills/codex-fluent/scripts/report_active_sessions.py \
     --codex-home ~/.codex --older-than-days 30 --limit 30 --format markdown
   ```

   Defaults: 30-day window (`older_than_days >= 0`), limit 30 (inclusive
   range 20–50). The primary size ranking is immutable; a separate
   `returned_handoff_queue` (scope `returned-window-only`) references
   `primary_rank` for returned candidates with two or more compactions.
   Repository identity is evidence-backed and nullable (`repo_root` is `null`
   with provenance `unknown` under the current persisted schema); the scanner
   never infers a repository from `cwd`. It never writes file content or
   explicit metadata and never archives, deletes, moves, prunes, rotates,
   normalizes, or applies.
3. **Future Desktop lifecycle hard trigger.** An immediate hard guarantee at
   compaction time requires a future Codex Desktop lifecycle API exposing the
   thread ID and compaction ordinal. The weekly scanner is a deterministic
   audit, not a lifecycle hook, and is not represented as an equivalent
   trigger.

Source and runtime ownership: `codex/AGENTS.md` and
`codex/skills/codex-fluent` are the repo sources; `~/.codex/AGENTS.md` and
`~/.codex/skills/codex-fluent` are runtime copies synchronized only through a
separately authorized activation with persistent backups. The unique
`weekly-codex-maintenance-report` automation remains the only scheduled
maintenance report; when separately authorized, its prompt gains a managed
appendix that runs the scanner in report-only mode with
`--older-than-days 30 --limit 30`, displays the primary size ranking and the
bounded `returned_handoff_queue`, and never calls apply behavior or archives
or deletes anything.

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
./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome
python3 scripts/check_skill_compatibility.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --plugin-root "$HOME/.codex/plugins/cache" --plugin-root "$HOME/.cache/codex-runtimes/codex-primary-runtime/plugins"
python3 scripts/check_codex_skill_loader.py --repo-root "$(pwd)" --codex-home "$HOME/.codex"
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

New evidence appends include `evidence_kind`. Decision evidence covers state,
handoff, approvals, guardrails, sandbox failures, and durable recovery. Routine
gate receipts cover tests, browser smoke, startup probes, ordinary tool calls,
and non-decision subagent reports. Existing local logs are not migrated; old
events without `evidence_kind` report as `unknown`.

Harness runtime report and checkpoint helpers:

```bash
python3 scripts/harness_report.py --phase validation
python3 scripts/harness_report.py --json --limit 20
python3 scripts/harness_report.py --evidence-kind decision --json
python3 scripts/harness_report.py --evidence-kind routine --json
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

Recovery output includes evidence-kind counts and compact latest decision
evidence so routine receipts do not bury handoff, approval, or guardrail
signals. State logs should promote decision evidence summaries rather than copy
every routine gate receipt.

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

6. `command not found: codex` or an existing `codex` shim reports embedded binary `ENOENT`
- Run `codex/runtime/resolve_codex_cli.sh`; it prints only a candidate that passes `--version`.
- For a damaged npm install, the official repair is `npm install -g @openai/codex`, then rerun the resolver and environment verification.
- Scheduled runners should execute the resolver's absolute result instead of relying on launchd's minimal `PATH`.
