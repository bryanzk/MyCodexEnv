# Agent Harness Status

This status map follows the Agent Harness diagram: Workflow is cognitive
orchestration, Infra is runtime governance.

## Related Documentation
- `README.md`: top-level quick start and Harness Runtime overview.
- `docs/repo-index.md`: low-token repo navigation and runtime surface index.
- `docs/HARNESS_RUNTIME.md`: lifecycle, evidence, checkpoint, permission, and subagent contracts.
- `docs/LIFECYCLE_SKILL_ROUTING.md`: lifecycle stage, workflow, skill, and helper routing.
- `docs/index.html`: public Delivery Harness Framework docs entry for GitHub Pages.
- `docs/delivery-harness-beginner-guide-cn.html`: beginner-oriented Chinese Delivery Harness Framework guide.
- `docs/CODEX_ENV_REPRODUCTION.md`: Codex + Claude environment reproduction guide.
- `docs/project-lifecycle-harness-flow-cn.html`: Chinese vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-skills.html`: Chinese lifecycle skill/helper routing visual guide.
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`: current styled Chinese Delivery Harness Framework skill/helper routing visual guide.

| Diagram Module | Current Status | Implemented Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| Research | done | `docs/repo-index.md`, startup probes in `project-lifecycle-harness`, `AGENTS.md` read-first rules | automatic source freshness scoring | add optional research evidence events per source |
| Requirements | done | lifecycle stage table, `docs/templates/harness-requirements.md`, `scripts/harness_requirements.py` | template must be filled per task before becoming source of truth | validate requirements artifacts before planning or development |
| Planning | done | planning stage policy, lifecycle router, `docs/HARNESS_RUNTIME.md` | no graphical plan report | keep plan output text-first; add visual report only when requested |
| Development | done | scoped write policy for `development`, repo change rules, `scripts/harness_agent_team.py` write-set validator | validator is explicit, not yet wired into automatic subagent dispatch | run validator before multi-worker dispatch and later integrate with orchestration |
| Validation | done | `verify_codex_env.sh`, `test_runner.py`, evidence schema, verification gate | no automatic final-answer gate in the model runtime | keep AGENTS gate and evidence helper; add completion hook if Codex exposes one |
| Sandbox | done | Codex sandbox/approval model, tool policy guard categories, `scripts/harness_env_probe.py` | global sandbox can be observed and reported, not forced by repo | keep probe output in verification and document runtime limits |
| Memory | done | `docs/harness-state.md`, `codex_subconscious.py`, repo index, `scripts/harness_recover.py` | recovery is an explicit smoke output, not automatic model memory | run recovery smoke at session start or before handoff-sensitive work |
| Skills | done | `codex/skills/*`, sync tests, generic lifecycle skill boundary test | skill quality varies by imported upstream content | add targeted validation for critical local skills |
| Session State | done | `docs/harness-state.md`, local evidence JSONL schema, `scripts/harness_checkpoint.py` | runtime state updates still require explicit helper invocation | use checkpoint helper at phase transitions and handoff |
| Permissions | done | `codex/runtime/tool-policy.json`, `harness_guard.py` | stage inference depends on payload/env/state | add explicit phase marker support in future Codex hook payloads |
| Hooks | done | `SessionStart`, `PreToolUse`, `PostToolUse`, hook sync tests | completion hook not available in current config | keep final verification gate in AGENTS and skill |
| Observability | done | `evidence.schema.json`, `harness_evidence.py`, `harness_observer.py`, `scripts/harness_report.py` | no browser dashboard | generate optional visual report from `harness_report.py --json` |
| Tool Router | done | phase-based policy and guard classifier | not all Codex tools expose identical payload shape | keep payload parser permissive and test common forms |
| Checkpoints | done | `docs/HARNESS_RUNTIME.md` checkpoint contract, `docs/harness-state.md`, `scripts/harness_checkpoint.py` | helper records state but deliberately does not commit | create commits only on explicit user request; otherwise append state checkpoints |
| Guardrails | done | guard hook blocks or asks on destructive, secret, remote, dynamic-exec, and phase write violations | high-risk patterns need ongoing tuning | extend policy with observed false positives/negatives |
