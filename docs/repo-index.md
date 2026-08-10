# MyCodexEnv Repo Index

> **DHF_PUBLIC_STATUS_V1 · 2026-08-03:** Canonical current architecture and
> source/runtime/publication status:
> [English](./dhf-architecture-status-en.html) ·
> [中文](./dhf-architecture-status-cn.html). Source availability is not proof
> of runtime activation.

## Purpose
- Reproduce a Codex + Claude dual-agent environment from a Git clone.
- Keep generic Codex runtime rules, skills, hooks, workflow files, and verification scripts under source control.
- Provide a small source-of-truth index for Codex sessions before reading larger docs.

## DHF Source-Stage Contract Mirror

Canonical profile and Result Invariant semantics live in
`codex/skills/delivery-harness-framework/SKILL.md`; routing and rollout-switch
behavior live in `codex/hooks/dhf_preprompt.py`.

- Governance profiles are `light`, `standard`, and `governed`.
- Generic injection requires explicit generic activation; an ordinary
  non-project prompt stays continue-only. opt-out is evaluated before every
  route, and a ShipQ cwd uses ShipQ adapter lazy delegation.
- Every completion preserves exactly `result`, `scope_and_constraints`,
  `verification_receipt`, and `remaining_risk_or_next_action`; profile-specific
  ceremony is conditional rather than repeated by default.
- The source simplified route uses the exact enabled value
  `DHF_PREPROMPT_SIMPLIFIED_PROFILES=1`; the repo-source default is `simplified`
  after the second final-fix gate. Values `0`, `false`, `off`,
  and `legacy` explicitly roll back. Runtime state is evidence-dependent: the
  live boundary accepts either a source-stage unsynced state or an exact
  promoted state and rejects drift. `source_stage_unsynced` proves source
  acceptance without runtime activation; `runtime_promoted` is required before
  claiming managed runtime activation.
- The source-stage acceptance lane uses
  `scripts/validate_dhf_simplification_corpus.py`,
  `scripts/dhf_simplification_evidence.py`, and
  `scripts/run_dhf_simplification_pair.py`; these validate independent producer
  bindings, frozen identities, parity/efficiency, and the read-only runtime
  boundary without synchronizing runtime.

## Read First
- `AGENTS.md`: repo-local navigation and verification expectations.
- `README.md`: environment reproduction, sync, skills, and common commands.
- `CONTEXT.md`: repo terminology contract for DHF language and forbidden aliases.
- `docs/harness-state.md`: append-only harness runtime state and latest safe task.
- `docs/HARNESS_RUNTIME.md`: design contract for workflow, infra, state, policy, evidence, hooks, checkpoints, and agent teams.
- `docs/LIFECYCLE_SKILL_ROUTING.md`: Chinese lifecycle-to-skill routing map for current project workflows.
- `docs/lifecycle-skill-routing-en.html`: English rendered lifecycle and skill routing specification.
- `docs/MODEL_ROUTER_EVAL_MATRIX.md`: prompt/subtask model router eval matrix and routing assertions.
- `docs/index.html`: Chinese public Delivery Harness Framework docs landing page for GitHub Pages.
- `docs/index-en.html`: English public Delivery Harness Framework docs landing page for GitHub Pages.
- `docs/dhf-architecture-status-cn.html`: canonical Chinese DHF architecture and source/runtime/publication status.
- `docs/dhf-architecture-status-en.html`: canonical English DHF architecture and source/runtime/publication status.
- `docs/delivery-harness-framework-manual-cn.md`: Chinese PM-facing Delivery Harness Framework manual draft.
- `docs/DHF_SIMPLIFICATION_PRODUCT_GUIDE.md`: Chinese product guide for simplified DHF behavior, activation, daily usage, verification, and rollback.
- `docs/dhf-workflow-skills-cn.html`: Chinese DHF workflow skill inventory with GitHub source links.
- `docs/dhf-workflow-skills-en.html`: English DHF workflow skill inventory with GitHub source links.
- `docs/dhf-for-product-and-field-en.html`: English diagram-first DHF overview for product managers and field engineers.
- `docs/dhf-for-product-and-field-cn.html`: Chinese diagram-first DHF overview for product managers and field engineers.
- `docs/dhf-engineering-notes-en.html`: English engineering notes on compaction governance and deployment safety.
- `docs/dhf-engineering-notes-cn.html`: Chinese engineering notes on compaction governance and deployment safety.
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
- `CONTEXT.md`: repo terminology contract for DHF language and forbidden aliases.
- `docs/harness-state.md`: append-only harness state, checkpoint, and next-safe-task log.
- `docs/HARNESS_RUNTIME.md`: runtime workflow, evidence, permission, checkpoint, and agent-team contract.
- `docs/AGENT_HARNESS_STATUS.md`: Agent Harness workflow and runtime governance status map.
- `docs/dhf-site-status.css`: shared status banner and canonical architecture-page styling.
- `docs/dhf-architecture-status-cn.html`: canonical Chinese DHF architecture and source/runtime/publication status.
- `docs/dhf-architecture-status-en.html`: canonical English DHF architecture and source/runtime/publication status.
- `codex/skills/delivery-harness-framework/`: lifecycle router skill.
- `codex/skills/committee-review-loop/`: explicit expert-committee review and revision loop skill.
- `codex/skills/codex-fluent/scripts/report_active_sessions.py`: read-only active Codex session ranking and handoff audit.
- `codex/runtime/tool-policy.json`: stage-aware tool and permission policy with low/medium/high annotations for every guard category, unknown-phase read-only fallback, configured agent-dispatch patterns, and Plan Governor Shadow status.
- `codex/runtime/harness-scope.json`: canonical governed roots, protected/persistence screening patterns, and the 32-file/1-MiB/4-MiB integrity-watch limits; these new controls do not modify `tool-policy.json`.
- `codex/runtime/harness-guard-targets.json`: exact seven-target source/runtime mapping consumed by harness promotion and verification.
- `codex/runtime/resolve_codex_cli.sh`: resolve a Codex CLI only after its `--version` smoke passes, preferring the npm global CLI before ChatGPT/Codex app bundle fallbacks for launchd and stale-shim recovery.
- `codex/runtime/dhf-packet.schema.json`: portable DHF packet schema for incubation, consumer handoff, and future extraction boundaries.
- `codex/runtime/evidence.schema.json`: compatibility local evidence JSONL event contract, including `agent_team_validated` receipts and optional compaction transition decision fields.
- `codex/runtime/evidence/decision-evidence.schema.json`: focused schema for state, handoff, approval, guardrail, sandbox, agent-team validation, durable recovery evidence, and optional compaction transition fields.
- `codex/runtime/evidence/routine-gate-receipt.schema.json`: focused schema for test receipts, browser smoke, startup probes, ordinary tool calls, and routine subagent reports.
- `codex/runtime/evidence/plan-scope-envelope.schema.json`: plan governor frozen scope envelope schema.
- `codex/runtime/evidence/plan-finding-decision.schema.json`: plan governor structured finding decision schema.
- `codex/runtime/evidence/plan-governor-receipt.schema.json`: plan governor bounded round receipt schema.
- `codex/hooks/`: Codex lifecycle hooks copied to `~/.codex/hooks/`.
- `codex/hooks.json`: source lifecycle-hook registration chain deployed only by approved sync.
- `codex/hooks/harness_guard.py`: PreToolUse guard with legacy block wire shape, governed/out-of-scope decisions, per-tool structured targets, protected/persistence screening, and integrity-watch freeze. Env/payload phase is accepted only in governed Git workspaces; precedence then continues through transcript, TTL self-declaration, snapshot, and `unknown`.
- `codex/hooks/task_state.py`: same-Git-root or same canonical non-Git workspace phase resolution, including transcript and TTL state reads.
- `codex/bin/codex-task`: audited TTL-bound `declare`/`revoke`; declarations do not downgrade high-risk categories or unlock protected roots.
- `codex/hooks/compaction_counter.py`: shared decoded top-level `compacted` event counter for scanner and prompt probe.
- `codex/hooks/compaction_probe.py`: incremental UserPromptSubmit host-observed compaction ordinal probe.
- `codex/hooks/context_meter.py`: W2a-capability-gated context pressure helper with ordinal-only no-persistence degradation.
- `codex/hooks/session_bearing.py`: bounded silent-failure SessionStart recovery and boundary-context injector.
- `codex/hooks/harness_observer.py`: PostToolUse evidence observer hook.
- `codex/hooks/model_router.py`: prompt/subtask complexity router for cheapest quality-safe model recommendations.
- `codex/hooks/dhf_preprompt.py`: generic `UserPromptSubmit` DHF dispatcher; malformed or missing-cwd payloads continue, opt-out wins first, non-ShipQ prompts need explicit generic activation, and ShipQ cwd delegates lazily to the adapter.
- `codex/hooks/shipq_dhf_preprompt.py`: ShipQ-only DHF preprompt adapter, never registered globally and loaded only by the generic dispatcher for ShipQ cwd.
- `scripts/harness_evidence.py`: evidence validation, kind inference, append helper, and decision-only compaction transition field validation.
- `scripts/plan_governor.py`: local plan scope, finding, receipt, and shadow evidence CLI.
- `scripts/harness_feedback.py`: conversion-health helper for local evidence reports and recovery.
- `scripts/harness_report.py`: local evidence summary CLI with evidence-kind counts and filters.
- `scripts/harness_agent_team.py`: agent team, write-set, worker task demand, demand-matched green gate, optional durable brief validator, and `--emit-evidence` validation receipt helper.
- `scripts/harness_checkpoint.py`: append-only state checkpoint helper with optional compaction transition decision fields.
- `scripts/harness_transition.py`: append-only first-record-wins transition idempotency store.
- `scripts/harness_ledger.py`: tamper-evident acceptance ledger init/pass/verify helper.
- `scripts/harness_eval.py`: fixture-driven tiered recovery, handoff, transition, and probe behavior evaluator.
- `docs/templates/harness-requirements.md`: task requirements artifact template.
- `docs/evals`: versioned Harness behavior-evaluation scenarios and handoff fixtures.
- `docs/templates/harness-agent-brief.md`: worker durable brief template with optional Task Demand and Green Gate companion fields.
- `scripts/harness_requirements.py`: requirements artifact validator.
- `scripts/harness_recover.py`: fresh-session recovery smoke check with evidence-kind counts, compact latest decision evidence, freshness-aware boundary verdicts, and pipe-only validated task demand.
- `scripts/codex_subconscious.py`: local memory build/brief/publish helper with fail-closed routine/derived reflection.
- `scripts/harness_env_probe.py`: observable Codex runtime config and split evidence schema probe.
- `scripts/harness_status.py`: unified read-only `status` entry point; `--runtime` and `--evidence` preserve the existing env-probe and report JSON contracts while old helper paths remain callable.
- `scripts/check_dhf_consumer_compatibility.py`: read-only DHF consumer compatibility and helper drift checker.
- `scripts/compare_dhf_core_snapshot.py`: read-only comparator for an independent DHF checkout, the MyCodexEnv consumer copy, and its immutable pin hashes.
- `scripts/validate_dhf_packet.py`: standard-library DHF packet validator with field-path errors and fail-close schema handling.
- `scripts/validate_dhf_simplification_corpus.py`: bounded DHF corpus, independent producer catalog, and derived acceptance-gate validator.
- `scripts/dhf_simplification_evidence.py`: read-only Base/promotion identity and managed-runtime boundary evidence producer; it never syncs runtime.
- `scripts/run_dhf_simplification_pair.py`: deterministic frozen-identity DHF parity and efficiency runner.
- `docs/dhf-consumer-compatibility.json`: machine-readable DHF consumer compatibility matrix for MyCodexEnv, ShipQ, and future consumers.
- `docs/dhf-core-pin.json`: MyCodexEnv DHF bootstrap snapshot; after the first upstream release it pins the immutable tag and Git revision.
- `docs/plans/2026-06-15-dhf-incubation-plan.md`: controlled incubation boundary, compatibility, and extraction trigger plan.
- `docs/plans/2026-06-15-dhf-independent-core-requirements.md`: reviewed copy/adapt/exclude, installer, doctor, packet, pin-bump, CI, privacy, and rollback contract for independent extraction.
- `scripts/headroom_filter.py`: optional stdin filter for compressing large command outputs with Headroom before sending them into agent context.
- `scripts/audit_skills.py`: report-only skill governance audit for repo/global/.agents skill sources and local usage traces.
- `scripts/check_skill_compatibility.py`: offline compatibility gate for all local skill manifests, helper syntax, and relative links, plus complete repo/runtime parity for persistent managed skills; ephemeral `.system` projections are loader-gated separately.
- `scripts/check_codex_skill_loader.py`: network-denied `app-server skills/list` gate that verifies every expected repo/runtime skill path is loaded and enabled with no loader errors.
- `docs/skill-governance-20260608.md`: skill governance baseline and cleanup policy notes.
- `scripts/prepare_gstack_dhf_daily_refresh.py`: preflight the daily refresh automation, retry DNS probes for about two minutes, require a standalone clone, check out the dedicated `automation/gstack-dhf-daily-refresh` branch rebased on `origin/main`, and return dry-run evidence before repo mutation.
- `scripts/merge_gstack_refresh_if_safe.py`: unattended merge gate for gstack daily refresh; only `--verified` ahead-only automation branches can fast-forward `main`.
- `scripts/sync_local_main_if_safe.py`: optional post-merge local sync gate; only clean local worktrees already on `main` and behind-only relative to `origin/main` are fast-forwarded.
- `scripts/sync_gstack_vendor.py`: bulk-sync `codex/skills/gstack` from an upstream `garrytan/gstack` git snapshot.
- `locks/superpowers.lock` + `scripts/sync_codex_home.sh`: pin `~/.codex/superpowers`, register local marketplace `superpowers-dev`, and install `superpowers@superpowers-dev` for new-session `superpowers:*` skills.
- `codex/skills/delivery-harness-framework/evals/evals.json`: routing and boundary evals for the generic lifecycle skill, including gstack brain-aware planning and question-tuning boundaries.
- `scripts/verify_codex_env.sh`: runtime sync and environment verification.
- `docs/LIFECYCLE_SKILL_ROUTING.md`: stage, workflow, skill, and helper usage guide.
- `docs/lifecycle-skill-routing-en.html`: English browser-ready rendering of the routing specification.
- `docs/index.html`: Chinese public docs landing page.
- `docs/index-en.html`: English public docs landing page.
- `docs/delivery-harness-framework-manual-cn.md`: Chinese PM-facing Delivery Harness Framework manual draft.
- `docs/dhf-workflow-skills-cn.html`: Chinese workflow skill inventory with GitHub links.
- `docs/dhf-workflow-skills-en.html`: English workflow skill inventory with GitHub links.
- `docs/dhf-for-product-and-field-en.html`: English diagram-first DHF overview for PM and FDE readers.
- `docs/dhf-for-product-and-field-cn.html`: Chinese diagram-first DHF overview for PM and FDE readers.
- `docs/dhf-engineering-notes-en.html`: English deep-dive on governed compaction and forward-only deployment.
- `docs/dhf-engineering-notes-cn.html`: Chinese deep-dive on governed compaction and forward-only deployment.
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
- `docs/DHF_SIMPLIFICATION_PRODUCT_GUIDE.md`: business-facing guide to the simplified DHF profiles, activation, daily usage, verification, and rollback.
- `codex/skills/grilling/`: vendored grilling skill, context format, ADR format, and upstream MIT license.
- `docs/HARNESS_RUNTIME.md`: lifecycle, evidence, checkpoint, permission, and subagent contracts.
- `docs/MODEL_ROUTER_EVAL_MATRIX.md`: model routing existence, positive/negative, progressive-switching, and end-to-end evals.
- `docs/HEADROOM_WORKFLOW.md`: optional Headroom command-output compression workflow and ShipQ examples.
- `docs/skill-governance-20260608.md`: first read-only skill governance baseline and cleanup policy notes.
- `docs/AGENT_HARNESS_STATUS.md`: Agent Harness workflow/infra status map.
- `docs/CODEX_ENV_REPRODUCTION.md`: Codex + Claude environment reproduction guide.
- `docs/LIFECYCLE_SKILL_ROUTING.md`: lifecycle stage, workflow, skill, and helper routing.
- `docs/lifecycle-skill-routing-en.html`: GitHub Pages rendering of the lifecycle and skill routing specification.
- `docs/index.html`: GitHub Pages Chinese public entry for Delivery Harness Framework guides.
- `docs/index-en.html`: GitHub Pages English public entry for Delivery Harness Framework guides.
- `docs/delivery-harness-framework-manual-cn.md`: Chinese PM-facing Delivery Harness Framework manual draft organized around why / what / how.
- `docs/dhf-workflow-skills-cn.html`: GitHub Pages Chinese DHF workflow skill inventory.
- `docs/dhf-workflow-skills-en.html`: GitHub Pages English DHF workflow skill inventory.
- `docs/dhf-for-product-and-field-en.html`: GitHub Pages English diagram-first DHF overview for product and field teams.
- `docs/dhf-for-product-and-field-cn.html`: GitHub Pages Chinese diagram-first DHF overview for product and field teams.
- `docs/dhf-engineering-notes-en.html`: GitHub Pages English engineering deep-dive for agentic systems readers.
- `docs/dhf-engineering-notes-cn.html`: GitHub Pages Chinese engineering deep-dive for agentic systems readers.
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
- Skill compatibility: `python3 scripts/check_skill_compatibility.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --plugin-root "$HOME/.codex/plugins/cache" --plugin-root "$HOME/.cache/codex-runtimes/codex-primary-runtime/plugins"`.
- Skill loader: `python3 scripts/check_codex_skill_loader.py --repo-root "$(pwd)" --codex-home "$HOME/.codex"`.
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
- Behavior Evaluator: `scripts/harness_eval.py` with versioned scenarios under `docs/evals`.

## Harness Infra Map
- Sandbox: Codex sandbox and approval rules, repo high-risk path guidance, and env probe output.
- Memory: `docs/harness-state.md`, recovery smoke output, local subconscious briefs as hints, and decision-preserving routine/derived reflection.
- Skills: `codex/skills/*` copied into `~/.codex/skills/*`.
- Session State: `docs/harness-state.md` plus local evidence JSONL.
- Permissions: `codex/runtime/tool-policy.json` and guard hooks.
- Hooks: `codex/hooks.json` and `codex/hooks/*`.
- Task-scoped phase: `codex/hooks/task_state.py` reads owner transcript markers and workspace-keyed TTL state without writing; `codex/bin/codex-task` is the only declare/revoke writer. Git workspaces require the same repo root; non-Git workspaces require the same canonical cwd. Host wrapper blocks are skipped only when well formed.
- DHF Prompt Dispatch: global `UserPromptSubmit` registers `dhf_preprompt.py`; `shipq_dhf_preprompt.py` remains a lazy project adapter and ordinary non-ShipQ prompts do not receive `additionalContext`.
- Observability: `scripts/harness_evidence.py`, `scripts/harness_feedback.py`, `scripts/harness_report.py`, split evidence schemas, and local evidence files. Decision evidence is promoted into state and handoff summaries; routine gate receipts remain available for audit without burying recovery signals.
- Tool Router: lifecycle stage policy in `tool-policy.json`.
- Model Router: `model_router.py` recommends `gpt-5.4-mini`, `gpt-5.4`, or `gpt-5.5` per prompt/subtask and can be re-run at complex task phase boundaries.
- Checkpoints: `docs/HARNESS_RUNTIME.md` contract, `scripts/harness_checkpoint.py`, and `docs/harness-state.md` log.
- Guardrails: hooks, global AGENTS rules, remote-access policy, and verification gate.
