# Agent Harness Status

This status map follows the Agent Harness diagram: Workflow is cognitive
orchestration, Infra is runtime governance.

| Diagram Module | Current Status | Implemented Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| Research | done | `docs/repo-index.md`, startup probes in `project-lifecycle-harness`, `AGENTS.md` read-first rules | automatic source freshness scoring | add optional research evidence events per source |
| Requirements | partial | lifecycle stage table and `docs/harness-state.md` snapshot | no dedicated requirements artifact template | add lightweight requirements section to state/handoff templates |
| Planning | done | planning stage policy, lifecycle router, `docs/HARNESS_RUNTIME.md` | no graphical plan report | keep plan output text-first; add visual report only when requested |
| Development | partial | scoped write policy for `development`, repo change rules | no automatic write-set enforcement outside hooks | add worktree/write-set validator for multi-agent tasks |
| Validation | done | `verify_codex_env.sh`, `test_runner.py`, evidence schema, verification gate | no automatic final-answer gate in the model runtime | keep AGENTS gate and evidence helper; add completion hook if Codex exposes one |
| Sandbox | partial | Codex sandbox/approval model, tool policy guard categories | repo cannot control global sandbox mode | document expected sandbox and verify config where possible |
| Memory | partial | `docs/harness-state.md`, `codex_subconscious.py`, repo index | subconscious remains heuristic and local-only | keep memory as hint; add state recovery smoke checks |
| Skills | done | `codex/skills/*`, sync tests, generic lifecycle skill boundary test | skill quality varies by imported upstream content | add targeted validation for critical local skills |
| Session State | done | `docs/harness-state.md`, local evidence JSONL schema | runtime evidence is local and not automatically summarized | add summary command over JSONL evidence |
| Permissions | done | `codex/runtime/tool-policy.json`, `harness_guard.py` | stage inference depends on payload/env/state | add explicit phase marker support in future Codex hook payloads |
| Hooks | done | `SessionStart`, `PreToolUse`, `PostToolUse`, hook sync tests | completion hook not available in current config | keep final verification gate in AGENTS and skill |
| Observability | done | `evidence.schema.json`, `harness_evidence.py`, `harness_observer.py` | no dashboard | add CLI report over evidence files |
| Tool Router | done | phase-based policy and guard classifier | not all Codex tools expose identical payload shape | keep payload parser permissive and test common forms |
| Checkpoints | partial | `docs/HARNESS_RUNTIME.md` checkpoint contract, state log | no automated git checkpoint command | add optional checkpoint helper after evidence report exists |
| Guardrails | done | guard hook blocks or asks on destructive, secret, remote, dynamic-exec, and phase write violations | high-risk patterns need ongoing tuning | extend policy with observed false positives/negatives |
