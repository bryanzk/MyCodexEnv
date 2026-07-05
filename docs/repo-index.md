# MyCodexEnv Repo Index

## Purpose
- Reproduce a Codex + Claude dual-agent environment from a Git clone.
- Keep generic Codex runtime rules, skills, hooks, workflow files, and verification scripts under source control.
- Provide a small source-of-truth index for Codex sessions before reading larger docs.

## Read First
- `AGENTS.md`: repo-local navigation and verification expectations.
- `README.md`: environment reproduction, sync, skills, and common commands.
- `docs/harness-state.md`: append-only harness runtime state and latest safe task.
- `docs/HARNESS_RUNTIME.md`: design contract for workflow, infra, state, policy, evidence, hooks, checkpoints, and agent teams.
- `docs/LIFECYCLE_SKILL_ROUTING.md`: Chinese lifecycle-to-skill routing map for current project workflows.
- `docs/MODEL_ROUTER_EVAL_MATRIX.md`: prompt/subtask model router eval matrix and routing assertions.
- `docs/index.html`: Chinese public Delivery Harness Framework docs landing page for GitHub Pages.
- `docs/index-en.html`: English public Delivery Harness Framework docs landing page for GitHub Pages.
- `docs/delivery-harness-framework-manual-cn.md`: Chinese PM-facing Delivery Harness Framework manual draft.
- `docs/dhf-workflow-skills-cn.html`: Chinese DHF workflow skill inventory with GitHub source links.
- `docs/dhf-workflow-skills-en.html`: English DHF workflow skill inventory with GitHub source links.
- `docs/delivery-harness-beginner-guide-cn.html`: Chinese beginner guide for agentic engineering readers.
- `docs/delivery-harness-beginner-guide-en.html`: English beginner guide for agentic engineering readers.
- `docs/project-lifecycle-harness-flow-cn.html`: Chinese vertical lifecycle flow visual guide.
- `docs/project-lifecycle-harness-flow-en.html`: English vertical lifecycle flow visual guide.
- `docs/project-lifecycle-harness-flow-skills.html`: Chinese skill/helper routing visual guide.
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`: current styled Chinese Delivery Harness Framework skill/helper routing guide.
- `docs/project-lifecycle-harness-flow-skills-en-status-style.html`: current styled English Delivery Harness Framework skill/helper routing guide.
- `docs/project-lifecycle-harness-flow-skills-en.html`: archived English Delivery Harness Framework skill/helper routing guide.
- `codex/AGENTS.md`: global Codex rules source copied into `~/.codex/AGENTS.md`.

## Runtime Surfaces
- `docs/surfaces.json`: canonical machine-readable runtime surface inventory; edit this first when adding, renaming, or retiring runtime surfaces.
- `scripts/check_surfaces.py`: validates `docs/surfaces.json` against files on disk, this Runtime Surfaces mirror, and opt-in public landing nav links.
- `docs/repo-index.md`: low-token repo navigation and checked runtime surface mirror.
- `docs/harness-state.md`: append-only harness state, checkpoint, and next-safe-task log.
- `docs/HARNESS_RUNTIME.md`: runtime workflow, evidence, permission, checkpoint, and agent-team contract.
- `docs/AGENT_HARNESS_STATUS.md`: Agent Harness workflow and runtime governance status map.
- `codex/skills/delivery-harness-framework/`: lifecycle router skill.
- `codex/skills/committee-review-loop/`: explicit expert-committee review and revision loop skill.
- `codex/runtime/tool-policy.json`: stage-aware tool and permission policy, including unknown-phase read-only fallback, handoff repo-write ask-gate, and configured agent-dispatch tool patterns.
- `codex/runtime/dhf-packet.schema.json`: portable DHF packet schema for incubation, consumer handoff, and future extraction boundaries.
- `codex/runtime/evidence.schema.json`: compatibility local evidence JSONL event contract, including `agent_team_validated` receipts.
- `codex/runtime/evidence/decision-evidence.schema.json`: focused schema for state, handoff, approval, guardrail, sandbox, agent-team validation, and durable recovery evidence.
- `codex/runtime/evidence/routine-gate-receipt.schema.json`: focused schema for test receipts, browser smoke, startup probes, ordinary tool calls, and routine subagent reports.
- `codex/hooks/`: Codex lifecycle hooks copied to `~/.codex/hooks/`.
- `codex/hooks/harness_guard.py`: PreToolUse permission and guardrail hook.
- `codex/hooks/harness_observer.py`: PostToolUse evidence observer hook.
- `codex/hooks/model_router.py`: prompt/subtask complexity router for cheapest quality-safe model recommendations.
- `codex/hooks/shipq_dhf_preprompt.py`: repo-owned ShipQ DHF preprompt hook surface.
- `scripts/harness_evidence.py`: evidence validation, kind inference, and append helper.
- `scripts/harness_feedback.py`: conversion-health helper for local evidence reports and recovery.
- `scripts/harness_report.py`: local evidence summary CLI with evidence-kind counts and filters.
- `scripts/harness_agent_team.py`: agent team, write-set, worker task demand, demand-matched green gate, optional durable brief validator, and `--emit-evidence` validation receipt helper.
- `scripts/harness_checkpoint.py`: append-only state checkpoint helper.
- `docs/templates/harness-requirements.md`: task requirements artifact template.
- `docs/templates/harness-agent-brief.md`: worker durable brief template with optional Task Demand and Green Gate companion fields.
- `scripts/harness_requirements.py`: requirements artifact validator.
- `scripts/harness_recover.py`: fresh-session recovery smoke check with evidence-kind counts and compact latest decision evidence.
- `scripts/harness_env_probe.py`: observable Codex runtime config and split evidence schema probe.
- `scripts/check_dhf_consumer_compatibility.py`: read-only DHF consumer compatibility and helper drift checker.
- `docs/dhf-consumer-compatibility.json`: machine-readable DHF consumer compatibility matrix for MyCodexEnv, ShipQ, and future consumers.
- `docs/plans/2026-06-15-dhf-incubation-plan.md`: controlled incubation boundary, compatibility, and extraction trigger plan.
- `scripts/headroom_filter.py`: optional stdin filter for compressing large command outputs with Headroom before sending them into agent context.
- `scripts/audit_skills.py`: report-only skill governance audit for repo/global/.agents skill sources and local usage traces.
- `docs/skill-governance-20260608.md`: skill governance baseline and cleanup policy notes.
- `scripts/prepare_gstack_dhf_daily_refresh.py`: preflight the daily refresh automation, retry DNS probes for about two minutes, require a standalone clone, check out the dedicated `automation/gstack-dhf-daily-refresh` branch rebased on `origin/main`, and return dry-run evidence before repo mutation.
- `scripts/merge_gstack_refresh_if_safe.py`: unattended merge gate for gstack daily refresh; only `--verified` ahead-only automation branches can fast-forward `main`.
- `scripts/sync_local_main_if_safe.py`: optional post-merge local sync gate; only clean local worktrees already on `main` and behind-only relative to `origin/main` are fast-forwarded.
- `scripts/sync_gstack_vendor.py`: bulk-sync `codex/skills/gstack` from an upstream `garrytan/gstack` git snapshot.
- `locks/superpowers.lock` + `scripts/sync_codex_home.sh`: pin `~/.codex/superpowers`, register local marketplace `superpowers-dev`, and install `superpowers@superpowers-dev` for new-session `superpowers:*` skills.
- `codex/skills/delivery-harness-framework/evals/evals.json`: routing and boundary evals for the generic lifecycle skill, including gstack brain-aware planning and question-tuning boundaries.
- `scripts/verify_codex_env.sh`: runtime sync and environment verification.
- `docs/LIFECYCLE_SKILL_ROUTING.md`: stage, workflow, skill, and helper usage guide.
- `docs/index.html`: Chinese public docs landing page.
- `docs/index-en.html`: English public docs landing page.
- `docs/delivery-harness-framework-manual-cn.md`: Chinese PM-facing Delivery Harness Framework manual draft.
- `docs/dhf-workflow-skills-cn.html`: Chinese workflow skill inventory with GitHub links.
- `docs/dhf-workflow-skills-en.html`: English workflow skill inventory with GitHub links.
- `docs/delivery-harness-beginner-guide-cn.html`: beginner-oriented Delivery Harness Framework explanation.
- `docs/delivery-harness-beginner-guide-en.html`: English beginner-oriented Delivery Harness Framework explanation.
- `docs/project-lifecycle-harness-flow-cn.html`: visual vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-en.html`: English visual vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-skills.html`: visual skill/helper routing map.
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`: current status-style skill/helper routing map.
- `docs/project-lifecycle-harness-flow-skills-en-status-style.html`: current English status-style skill/helper routing map.
- `docs/project-lifecycle-harness-flow-skills-en.html`: archived English skill/helper routing map.

## Related Documentation
- `README.md`: top-level quick start and Harness Runtime overview.
- `docs/HARNESS_RUNTIME.md`: lifecycle, evidence, checkpoint, permission, and subagent contracts.
- `docs/MODEL_ROUTER_EVAL_MATRIX.md`: model routing existence, positive/negative, progressive-switching, and end-to-end evals.
- `docs/HEADROOM_WORKFLOW.md`: optional Headroom command-output compression workflow and ShipQ examples.
- `docs/skill-governance-20260608.md`: first read-only skill governance baseline and cleanup policy notes.
- `docs/AGENT_HARNESS_STATUS.md`: Agent Harness workflow/infra status map.
- `docs/CODEX_ENV_REPRODUCTION.md`: Codex + Claude environment reproduction guide.
- `docs/LIFECYCLE_SKILL_ROUTING.md`: lifecycle stage, workflow, skill, and helper routing.
- `docs/index.html`: GitHub Pages Chinese public entry for Delivery Harness Framework guides.
- `docs/index-en.html`: GitHub Pages English public entry for Delivery Harness Framework guides.
- `docs/delivery-harness-framework-manual-cn.md`: Chinese PM-facing Delivery Harness Framework manual draft organized around why / what / how.
- `docs/dhf-workflow-skills-cn.html`: GitHub Pages Chinese DHF workflow skill inventory.
- `docs/dhf-workflow-skills-en.html`: GitHub Pages English DHF workflow skill inventory.
- `docs/delivery-harness-beginner-guide-cn.html`: beginner guide explaining what Delivery Harness Framework does.
- `docs/delivery-harness-beginner-guide-en.html`: English beginner guide explaining what Delivery Harness Framework does.
- `docs/project-lifecycle-harness-flow-cn.html`: Chinese vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-en.html`: English vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-skills.html`: Chinese lifecycle skill/helper routing visual guide.
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`: current styled Chinese Delivery Harness Framework visual guide.
- `docs/project-lifecycle-harness-flow-skills-en-status-style.html`: current styled English Delivery Harness Framework visual guide.
- `docs/project-lifecycle-harness-flow-skills-en.html`: archived English Delivery Harness Framework visual guide.

## Verification
- Primary: `python3 test_runner.py`.
- CI gate: `.github/workflows/ci.yml` runs `python3 test_runner.py`, `git diff --check`, and `python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav` on `push` to `main`, `pull_request`, and manual dispatch.
- Runtime sync: `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"`.
- Automation-safe runtime sync: `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome`.
- Formatting: `git diff --check`.
- Gstack vendor refresh: `python3 scripts/prepare_gstack_dhf_daily_refresh.py --json`, then in the returned standalone clone and automation branch run `python3 scripts/sync_gstack_vendor.py --repo-root "$(pwd)" --dry-run --json`; only rerun without `--dry-run` when `needs_update=true`. Scheduled automation pushes `automation/gstack-dhf-daily-refresh` first, then may run `python3 scripts/merge_gstack_refresh_if_safe.py --apply --verified --json` to fast-forward `main` only when the branch is ahead-only and verification has passed. If `main` is updated, it may then run `python3 scripts/sync_local_main_if_safe.py --repo-root /Users/kezheng/Codes/CursorDeveloper/MyCodexEnv --apply --json` to fast-forward the local checkout only when it is clean, on `main`, and behind-only.
- Repo-local docs/config changes must keep README, docs, tests, and sync behavior consistent.

## High-Risk Areas
- `scripts/`: may write to runtime homes or verification reports.
- `codex/hooks/`: can block or alter Codex lifecycle behavior.
- `codex/runtime/`: policy/schema changes affect tool routing and evidence validation.
- `codex/skills/`: global skill source copied into runtime `~/.codex/skills`.

## Harness Workflow Map
- Research: read repo index, AGENTS, README, docs, and relevant state before acting.
- Requirements: capture success criteria and scope in a validated requirements artifact, plan, state, or handoff surface.
- Planning: use lifecycle routing and keep planning read-only unless implementation is explicitly requested.
- Development: edit only scoped repo files and preserve unrelated user changes.
- Validation: run fresh gates and record evidence with command, exit code, key output, and timestamp.

## Harness Infra Map
- Sandbox: Codex sandbox and approval rules, repo high-risk path guidance, and env probe output.
- Memory: `docs/harness-state.md`, recovery smoke output, and local subconscious briefs as hints only.
- Skills: `codex/skills/*` copied into `~/.codex/skills/*`.
- Session State: `docs/harness-state.md` plus local evidence JSONL.
- Permissions: `codex/runtime/tool-policy.json` and guard hooks.
- Hooks: `codex/hooks.json` and `codex/hooks/*`.
- Observability: `scripts/harness_evidence.py`, `scripts/harness_feedback.py`, `scripts/harness_report.py`, split evidence schemas, and local evidence files. Decision evidence is promoted into state and handoff summaries; routine gate receipts remain available for audit without burying recovery signals.
- Tool Router: lifecycle stage policy in `tool-policy.json`.
- Model Router: `model_router.py` recommends `gpt-5.4-mini`, `gpt-5.4`, or `gpt-5.5` per prompt/subtask and can be re-run at complex task phase boundaries.
- Checkpoints: `docs/HARNESS_RUNTIME.md` contract, `scripts/harness_checkpoint.py`, and `docs/harness-state.md` log.
- Guardrails: hooks, global AGENTS rules, remote-access policy, and verification gate.
