# Handoff: Harness Runtime Current State

Date: 2026-05-11
Timestamp: 2026-05-11T20:09:03-04:00
Repo: `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv`
Branch: `main`
Latest commit at handoff: `12b4ba6 Add harness requirements recovery and env probe`
Working tree at handoff creation: clean before this document was added

## Purpose

This handoff lets a new Codex session resume MyCodexEnv Harness Runtime work
without relying on chat history. The immediate context is the generic
`delivery-harness-framework` skill and its alignment with the current runtime:
repo index, state log, requirements artifacts, recovery smoke, env probe,
evidence reporting, checkpointing, and agent team validation.

## Current Phase

- phase: `handoff`
- blocked_sources: none
- unsafe_inputs: none
- evidence_status: present
- next_safe_task: update `delivery-harness-framework` so it routes through the
  latest Harness Runtime helpers and gstack decision points, then sync it into
  `~/.codex/skills`

## Read First

Read these in order:

1. `AGENTS.md`
2. `docs/repo-index.md`
3. `docs/harness-state.md`
4. `docs/HARNESS_RUNTIME.md`
5. `docs/AGENT_HARNESS_STATUS.md`
6. `codex/skills/delivery-harness-framework/SKILL.md`
7. `/Users/kezheng/.codex/skills/delivery-harness-framework/SKILL.md`

Then run the recovery probes:

```bash
python3 scripts/harness_recover.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --json
python3 scripts/harness_env_probe.py --codex-home "$HOME/.codex" --json
git status --short --branch
```

## Current Harness Runtime State

The runtime implementation is functionally complete against the Agent Harness
diagram. `docs/AGENT_HARNESS_STATUS.md` currently marks all 15 diagram modules
as `done`:

- Workflow: Research, Requirements, Planning, Development, Validation.
- Infra: Sandbox, Memory, Skills, Session State, Permissions, Hooks,
  Observability, Tool Router, Checkpoints, Guardrails.

Key runtime surfaces now present:

- `docs/repo-index.md`
- `docs/harness-state.md`
- `docs/HARNESS_RUNTIME.md`
- `docs/templates/harness-requirements.md`
- `codex/runtime/tool-policy.json`
- `codex/runtime/evidence.schema.json`
- `codex/hooks.json`
- `codex/hooks/*`
- `scripts/harness_evidence.py`
- `scripts/harness_report.py`
- `scripts/harness_agent_team.py`
- `scripts/harness_checkpoint.py`
- `scripts/harness_requirements.py`
- `scripts/harness_recover.py`
- `scripts/harness_env_probe.py`

## Important Gap

The repo runtime has advanced further than the current generic
`delivery-harness-framework` skill text.

The current skill still describes the right lifecycle protocol, but it does not
yet fully route through the latest helper CLIs:

- `scripts/harness_requirements.py`
- `scripts/harness_recover.py`
- `scripts/harness_env_probe.py`
- `scripts/harness_report.py`
- `scripts/harness_agent_team.py`
- `scripts/harness_checkpoint.py`

It also does not yet encode the recent generic-vs-gstack lifecycle routing
recommendation. The next session should update the skill as a concise router,
not a large executor: keep top-level instructions compact, use progressive
disclosure, name trigger conditions, and point to scripts/docs for detailed
behavior.

## Suggested Next Task

Update `codex/skills/delivery-harness-framework/SKILL.md` so it matches the
current Harness Runtime:

1. Add latest runtime helper surfaces and when to use each helper.
2. Replace manual-only startup probes with `harness_recover.py` and
   `harness_env_probe.py`, while keeping manual fallbacks.
3. Tighten `requirements` gate around validated requirements artifacts.
4. Add explicit `harness_agent_team.py validate PLAN.json` before multi-worker
   dispatch.
5. Add `harness_checkpoint.py append` as the preferred handoff/checkpoint path.
6. Add gstack routing guidance for product review, engineering review, browser
   QA, security review, ship, deploy, canary, and release documentation.
7. Update tests so the skill cannot drift away from the runtime helpers again.
8. Sync repo skills into runtime `~/.codex/skills` and verify.

## Verification Commands For Next Session

Use these after editing the skill:

```bash
python3 test_runner.py
git diff --check
./scripts/sync_codex_home.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --skip-superpowers-sync
./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"
cmp codex/skills/delivery-harness-framework/SKILL.md "$HOME/.codex/skills/delivery-harness-framework/SKILL.md"
```

Required final evidence fields:

- command
- exit_code
- key_output
- timestamp

## Known Non-Blockers

- `~/.codex/skills` skill count can differ from repo-managed `codex/skills`;
  that is not itself a runtime failure unless a specific sync test expects exact
  parity.
- Current local `codex --version` reports `codex-cli 0.130.0`; the verifier now
  accepts the current CLI line and checks that repo-managed skills are present
  instead of requiring exact parity with local extra skills.
- The repo can observe Codex config and runtime files, but it cannot force the
  Desktop thread sandbox globally. `harness_env_probe.py` should report
  `observable=false` when sandbox fields are absent instead of guessing.
- Local evidence under `~/.codex/harness/evidence/*` must stay out of the repo.

## Validation Observed During This Handoff

- `git diff --check`: passed.
- `python3 test_runner.py`: previously failed because the embedded
  `verify_codex_env.sh` step rejected `codex-cli 0.130.0`; this version policy
  has since been updated.
- `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"`:
  now accepts `codex-cli 0.130.0` and local extra skills when repo-managed
  skills are present.

## Copy-Paste Prompt For New Session

```text
请在 MyCodexEnv 中继续更新通用 skill：delivery-harness-framework。

工作目录：
/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv

先读取：
1. AGENTS.md
2. docs/repo-index.md
3. docs/harness-state.md
4. docs/HARNESS_RUNTIME.md
5. docs/AGENT_HARNESS_STATUS.md
6. docs/handoffs/2026-05-11-harness-runtime-current-state.md
7. codex/skills/delivery-harness-framework/SKILL.md

目标：
- 让 delivery-harness-framework 符合当前完整 Harness Runtime。
- 将 requirements/recovery/env probe/report/agent team/checkpoint helpers 纳入路由。
- 将 generic skill 与 gstack skill 的生命周期分工写进 skill。
- 保持 skill generic，不写入业务 repo 专属路径。
- 更新测试防止 skill 再次与 runtime helper 漂移。
- 同步到 ~/.codex/skills 并运行 fresh verification。

验证必须包含：
- python3 test_runner.py
- git diff --check
- ./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"
- cmp codex/skills/delivery-harness-framework/SKILL.md "$HOME/.codex/skills/delivery-harness-framework/SKILL.md"
```
