# Agent Harness Status

This status map follows the Agent Harness diagram: Workflow is cognitive
orchestration, Infra is runtime governance.

## Related Documentation
- `README.md`: top-level quick start and Harness Runtime overview.
- `docs/repo-index.md`: low-token repo navigation and runtime surface index.
- `docs/HARNESS_RUNTIME.md`: lifecycle, evidence, checkpoint, permission, and subagent contracts.
- `docs/LIFECYCLE_SKILL_ROUTING.md`: lifecycle stage, workflow, skill, and helper routing.
- `docs/index.html`: Chinese public Delivery Harness Framework docs entry for GitHub Pages.
- `docs/index-en.html`: English public Delivery Harness Framework docs entry for GitHub Pages.
- `docs/delivery-harness-beginner-guide-cn.html`: beginner-oriented Chinese Delivery Harness Framework guide.
- `docs/delivery-harness-beginner-guide-en.html`: beginner-oriented English Delivery Harness Framework guide.
- `docs/CODEX_ENV_REPRODUCTION.md`: Codex + Claude environment reproduction guide.
- `docs/project-lifecycle-harness-flow-cn.html`: Chinese vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-en.html`: English vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-skills.html`: Chinese lifecycle skill/helper routing visual guide.
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`: current styled Chinese Delivery Harness Framework skill/helper routing visual guide.
- `docs/project-lifecycle-harness-flow-skills-en-status-style.html`: current styled English Delivery Harness Framework skill/helper routing visual guide.

| Diagram Module | Current Status | Implemented Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| Research | done | `docs/repo-index.md`, startup probes in `delivery-harness-framework`, `AGENTS.md` read-first rules | automatic source freshness scoring | add optional research evidence events per source |
| Requirements | done | lifecycle stage table, `docs/templates/harness-requirements.md`, `scripts/harness_requirements.py` | template must be filled per task before becoming source of truth | validate requirements artifacts before planning or development |
| Planning | done | planning stage policy, lifecycle router, `docs/HARNESS_RUNTIME.md` | no graphical plan report | keep plan output text-first; add visual report only when requested |
| Plan Governor | source-stage Shadow | `scripts/plan_governor.py`, three plan schemas, planner/committee contracts, `guardrail_decision` evidence | Phase 0 found the command marker observable and deny enforceable, but current Codex treats `permissionDecision=ask` as unsupported and fail-open; no Governor hook enforcement, Ask/Enforce rollout, or runtime activation | keep Production no-go; repeat Phase 0 only after the Codex host supports an enforceable PreToolUse Ask response |
| Development | done | scoped write policy for `development`, repo change rules, `scripts/harness_agent_team.py` write-set validator, `--emit-evidence` decision receipt, configured dispatch ask-gate | only configured dispatch tool names/patterns are intercepted; runtime-owned shapes may still need explicit support | validate with `--emit-evidence` before multi-worker dispatch and extend configured shapes as the runtime exposes them |
| Validation | done | `verify_codex_env.sh`, `test_runner.py`, evidence schema, verification gate, skip-counted runner summary, hook/schema runtime content checks | no automatic final-answer gate in the model runtime; runtime activation still requires explicit sync approval | keep AGENTS gate and evidence helper; add completion hook if Codex exposes one |
| Behavior Evaluator | tier-1 done | `scripts/harness_eval.py`, `docs/evals/` recovery and handoff fixtures, exact verification receipts | tier-2 waits for transition/probe infra; tier-3 remains audit-only | run tier-1 as a merge gate and tier-3 only in the weekly audit |
| Sandbox | done | Codex sandbox/approval model, tool policy guard categories, `scripts/harness_env_probe.py` | global sandbox can be observed and reported, not forced by repo | keep probe output in verification and document runtime limits |
| Memory | done | `docs/harness-state.md`, `codex_subconscious.py` build/brief/reflect, repo index, `scripts/harness_recover.py --boundary` freshness-aware verdict and validated `task_demand` payload | recovery and reflection remain explicit helper invocations; unknown boundary is fail-closed; task demand is pipe-only | run recovery at session start and weekly reflect only on routine/derived records |
| Skills | done | `codex/skills/*`, sync tests, generic lifecycle skill boundary test | skill quality varies by imported upstream content | add targeted validation for critical local skills |
| Session State | done | `docs/harness-state.md`, local evidence JSONL schema, `scripts/harness_checkpoint.py` | runtime state updates still require explicit helper invocation | use checkpoint helper at phase transitions and handoff |
| Transition Store | done | `scripts/harness_transition.py` O_APPEND record/query, post-append reread, first-record-wins CAS | lifecycle callers must invoke the helper; runtime store is local and undeployed | query before successor creation and treat conflicts as an existing successor |
| Task Ledger | done | `scripts/harness_ledger.py` init/pass/verify contract, content hash, complete verification receipts | ledger integrity still requires an explicit verify gate | run `harness_ledger.py verify` before accepting tracked criteria |
| Permissions | done | `codex/runtime/tool-policy.json`, `harness_guard.py`, per-category risk tiers in decision reasons, state snapshot phase fallback, unknown-phase read-only fallback | phase inference is still category-level, not path-scoped; tier annotations cannot add top-level block fields | keep the exact legacy block key shape and add explicit phase markers only when the host exposes them |
| Hooks | source-stage done | `SessionStart` naming plus 180ms silent-failure session bearing, `UserPromptSubmit` including compaction probe, `PreToolUse`, `PostToolUse`, hook tests | completion hook not available; session bearing and compaction probe are not deployed before W6a approval | keep final verification gate and defer real runtime activation to W6a |
| Compaction Probe | W2b source done | Phase-0 evidence, shared counter, exact-id/strict-heuristic resolution, incremental offset state, large-fixture non-full-read proof | source is registered but live `~/.codex` remains undeployed; usage fields were absent | consume ordinal only, then deploy at W6a solely after approval |
| Context Meter | ordinal-only source done | W2a usage-absent decision evidence, `context_meter.py`, ordinal pressure injection, unknown token/capacity output, no-persistence false path | host payload exposed no usage fields; source remains undeployed before W6a | retain ordinal-only signal; enable persistence only after a new probe proves observed usage fields |
| Observability | done | `evidence.schema.json`, `harness_evidence.py`, `harness_observer.py`, `scripts/harness_report.py`, optional decision-only compaction transition fields, verify PASS/FAIL/SKIP evidence for missing `codex` without early shell exit | no browser dashboard | generate optional visual report from `harness_report.py --json` |
| Docs Drift | done | `docs/surfaces.json`, `scripts/check_surfaces.py --check-public-nav`, `test_check_surfaces_validates_public_nav()` | public HTML nav generation is still manual | optionally generate HTML nav blocks from the manifest |
| Tool Router | done | phase-based policy, guard classifier, payload/env/state phase resolution order, and configured `agent_dispatch` category | not all Codex tools expose identical payload shape | keep payload parser permissive and test common forms |
| Model Router | done | `codex/hooks/model_router.py`, prompt/subtask complexity tests | hook can recommend and emit JSON; actual model switching depends on runtime or wrapper support | keep deterministic, non-blocking, and quality-floor first |
| Checkpoints | done | `docs/HARNESS_RUNTIME.md` checkpoint contract, `docs/harness-state.md`, `scripts/harness_checkpoint.py`, optional `compaction_ordinal` / `transition_key` / `gate_decision` fields | helper records state but deliberately does not commit | create commits only on explicit user request; otherwise append state checkpoints |
| Guardrails | done | guard hook blocks destructive, secret, remote, dynamic-exec, phase write violations, and unreceipted configured agent dispatch; every category has a risk tier and the 18-round probe preserved behavior | command-form secret classification still has the recorded gap; live `~/.codex` enforcement waits for approved sync | repair the classifier only with a separate probe-backed change |
