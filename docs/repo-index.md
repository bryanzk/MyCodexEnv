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
- `docs/index.html`: public Delivery Harness Framework docs landing page for GitHub Pages.
- `docs/delivery-harness-beginner-guide-cn.html`: Chinese beginner guide for agentic engineering readers.
- `docs/project-lifecycle-harness-flow-cn.html`: Chinese vertical lifecycle flow visual guide.
- `docs/project-lifecycle-harness-flow-skills.html`: Chinese skill/helper routing visual guide.
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`: current styled Chinese Delivery Harness Framework skill/helper routing guide.
- `codex/AGENTS.md`: global Codex rules source copied into `~/.codex/AGENTS.md`.

## Runtime Surfaces
- `codex/skills/project-lifecycle-harness/`: lifecycle router skill.
- `codex/runtime/tool-policy.json`: stage-aware tool and permission policy.
- `codex/runtime/evidence.schema.json`: local evidence JSONL event contract.
- `codex/hooks/`: Codex lifecycle hooks copied to `~/.codex/hooks/`.
- `scripts/harness_evidence.py`: evidence validation and append helper.
- `scripts/harness_report.py`: local evidence summary CLI.
- `scripts/harness_agent_team.py`: agent team and write-set validator.
- `scripts/harness_checkpoint.py`: append-only state checkpoint helper.
- `docs/templates/harness-requirements.md`: task requirements artifact template.
- `scripts/harness_requirements.py`: requirements artifact validator.
- `scripts/harness_recover.py`: fresh-session recovery smoke check.
- `scripts/harness_env_probe.py`: observable Codex runtime config probe.
- `scripts/verify_codex_env.sh`: runtime sync and environment verification.
- `docs/LIFECYCLE_SKILL_ROUTING.md`: stage, workflow, skill, and helper usage guide.
- `docs/index.html`: public docs landing page.
- `docs/delivery-harness-beginner-guide-cn.html`: beginner-oriented Delivery Harness Framework explanation.
- `docs/project-lifecycle-harness-flow-cn.html`: visual vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-skills.html`: visual skill/helper routing map.
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`: current status-style skill/helper routing map.

## Related Documentation
- `README.md`: top-level quick start and Harness Runtime overview.
- `docs/HARNESS_RUNTIME.md`: lifecycle, evidence, checkpoint, permission, and subagent contracts.
- `docs/AGENT_HARNESS_STATUS.md`: Agent Harness workflow/infra status map.
- `docs/CODEX_ENV_REPRODUCTION.md`: Codex + Claude environment reproduction guide.
- `docs/LIFECYCLE_SKILL_ROUTING.md`: lifecycle stage, workflow, skill, and helper routing.
- `docs/index.html`: GitHub Pages public entry for Delivery Harness Framework guides.
- `docs/delivery-harness-beginner-guide-cn.html`: beginner guide explaining what Delivery Harness Framework does.
- `docs/project-lifecycle-harness-flow-cn.html`: Chinese vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-skills.html`: Chinese lifecycle skill/helper routing visual guide.
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`: current styled Chinese Delivery Harness Framework visual guide.

## Verification
- Primary: `python3 test_runner.py`.
- Runtime sync: `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"`.
- Formatting: `git diff --check`.
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
- Observability: `scripts/harness_evidence.py`, `scripts/harness_report.py`, and local evidence files.
- Tool Router: lifecycle stage policy in `tool-policy.json`.
- Checkpoints: `docs/HARNESS_RUNTIME.md` contract, `scripts/harness_checkpoint.py`, and `docs/harness-state.md` log.
- Guardrails: hooks, global AGENTS rules, remote-access policy, and verification gate.
