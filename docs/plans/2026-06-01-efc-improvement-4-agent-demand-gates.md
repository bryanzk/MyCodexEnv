# EFC Improvement 4 Agent Demand Gates Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

## Execution Order And Dependencies

These three EFC code plans (3, 4, 5) are **not parallel-safe** — all three modify
`test_runner.py`, `docs/HARNESS_RUNTIME.md`, and `docs/repo-index.md` (and 3/5
also share `harness_report.py` / `harness_recover.py`). Land them in series, one
branch each, in this order:

1. **Improvement 4** (this plan) — most isolated: only `harness_agent_team.py`
   plus shared tests/docs. Land first.
2. **Improvement 3**.
3. **Improvement 5** (depends on 3).

This plan is otherwise dependency-free: it does not touch the report, recovery,
evidence schema, DHF skill text, or runtime sync. Its only collision with 3 and 5
is the shared `test_runner.py` / `docs/HARNESS_RUNTIME.md` / `docs/repo-index.md`,
which is why it serializes rather than runs in parallel. The worker `task_demand`
contract here intentionally mirrors the slice-contract / requirements
`task_demand` shape from the doc-only patch (`level` + `L`/`H_tool`/`S_state`/
`N_obs`); keep them consistent if either changes.

**Goal:** Extend `harness_agent_team.py validate` so each worker declares `task_demand` and a demand-matched green gate before parallel work can be dispatched.

**Architecture:** Keep the validator JSON-only and generic. Preserve existing role/write-set safety, but add a worker demand contract that is explicit enough for reviewers and future agents to audit. Use structured fields instead of parsing prose from `scope`, `verification_command`, or `rationale`.

**Tech Stack:** Python standard library, JSON plan files, `scripts/harness_agent_team.py`, `docs/templates/harness-agent-brief.md`, `docs/HARNESS_RUNTIME.md`, `test_runner.py`.

## Definition Of Done

- Worker agents require a `task_demand` object.
- Worker agents require a `green_gate` object that matches demand level.
- Read-only roles may omit `task_demand` and `green_gate`, but cannot provide misleading write scopes.
- Validator error messages identify the agent id and the missing or invalid demand field.
- Valid summary output includes worker demand level and green gate.
- Existing write-set overlap, read-only write-set, brief validation, and outside-repo checks still pass.
- `python3 test_runner.py` and `git diff --check` pass.

## Current Facts

- `scripts/harness_agent_team.py` currently validates `agents[]`, roles, scopes, write sets, `verification_command`, optional `brief`, and worker write-set overlap.
- Current valid roles: `planner`, `reviewer`, `security`, `qa`, `worker`.
- Existing tests live in `test_runner.py::test_harness_agent_team_validator`.
- Existing worker plan shape only requires `verification_command`; it does not describe task difficulty or why the selected gate is sufficient.

## Scope

**Modify:**
- `scripts/harness_agent_team.py`
- `test_runner.py`
- `docs/HARNESS_RUNTIME.md`
- `docs/templates/harness-agent-brief.md`
- `docs/repo-index.md` if the validator contract summary needs updating.

**Do not modify:**
- `codex/runtime/evidence.schema.json`
- `scripts/harness_report.py`
- `scripts/harness_recover.py`
- Runtime skill mirrors unless a later review explicitly requires DHF skill text changes.

## Preflight

Run before editing:

```bash
git status --short --branch
sed -n '1,220p' AGENTS.md
sed -n '1,220p' docs/repo-index.md
python3 scripts/harness_recover.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --json
```

Classify dirty files:

- `user_owned`: pre-existing unrelated changes; do not edit, stage, or revert.
- `task_owned`: files listed in this plan after this slice intentionally changes them.
- `blocker`: a target file already contains unrelated dirty changes; stop and resolve ownership before editing.

## Out Of Scope

- No evidence schema changes.
- No report/recovery conversion-health logic.
- No model routing changes.
- No runtime-home sync unless the implementation also changes a global skill.
- No repo-specific demand rules; keep the validator generic.

## JSON Contract

Each `worker` agent must include:

```json
{
  "task_demand": {
    "level": "low | medium | high",
    "L": "reasoning/action steps justification",
    "H_tool": "tool-selection ambiguity justification",
    "S_state": "cross-module state-tracking justification",
    "N_obs": "observation/external noise justification"
  },
  "green_gate": {
    "gate_scope": "worker | integrator",
    "command": "python3 test_runner.py",
    "rationale": "why this command is sufficient for the demand level",
    "focused_gate_command": "python3 test_runner.py",
    "integrator_gate_command": "python3 test_runner.py",
    "full_gate_command": "python3 test_runner.py",
    "new_probe": "name of new probe for high demand"
  }
}
```

Field rules:

- `task_demand.level` must be one of `low`, `medium`, `high`.
- `L`, `H_tool`, `S_state`, and `N_obs` must be non-empty strings.
- `green_gate.gate_scope` must be `worker` or `integrator`.
- `green_gate.command` and `green_gate.rationale` must be non-empty strings for every worker.
- `green_gate.focused_gate_command` is required for `medium` and `high`.
- `high` demand requires `green_gate.full_gate_command` and `green_gate.new_probe`.
- `low` may omit `focused_gate_command`, `full_gate_command`, and `new_probe`.
- `medium` may omit `full_gate_command` and `new_probe`.
- `verification_command` remains required for backward compatibility with the existing top-level contract.
- If `green_gate.gate_scope == "worker"`, `verification_command` must equal `green_gate.command`.
- If `green_gate.gate_scope == "integrator"`, `green_gate.integrator_gate_command`
  is required and must equal `verification_command`; `green_gate.command` is the
  worker-local command and may be narrower.

Do not infer demand from file paths or command names. The validator should enforce structure and consistency, not project-specific testing policy.

Demand-level minimums:

- `low`: requires `green_gate.command`; intended for docs/config/localized helper
  checks. The validator only requires structure.
- `medium`: requires `green_gate.command` and `green_gate.focused_gate_command`.
  They may be the same command.
- `high`: requires `green_gate.command`, `green_gate.focused_gate_command`,
  `green_gate.full_gate_command`, and `green_gate.new_probe`.

Read-only role behavior:

- `planner`, `reviewer`, `security`, and `qa` must not provide `task_demand` or
  `green_gate`.
- If a read-only role supplies either field, reject with
  `ERROR[read_only_demand_gate]`.

## Task 1: Write RED Tests For Demand And Gate Validation

**Files:**
- Modify: `test_runner.py`

**Step 1: Update the valid worker fixture**

In `test_harness_agent_team_validator()`, add `task_demand` and `green_gate` to each worker in `valid_plan`.

Example:

```python
"task_demand": {
    "level": "medium",
    "L": "Adds one report behavior with tests.",
    "H_tool": "Known Python CLI and test runner.",
    "S_state": "Touches one runtime helper and its test.",
    "N_obs": "Local deterministic evidence fixtures.",
},
"green_gate": {
    "gate_scope": "worker",
    "command": "python3 test_runner.py",
    "focused_gate_command": "python3 test_runner.py",
    "rationale": "Full local runner covers harness report behavior and existing contracts.",
},
```

**Step 2: Add missing demand failure**

Add a worker fixture with no `task_demand`.

Expected:

```text
ERROR[task_demand_missing] agent=worker
```

**Step 3: Add invalid level failure**

Add a worker with `task_demand.level = "extreme"`.

Expected:

```text
ERROR[task_demand_level] agent=worker
```

**Step 4: Add high demand missing full gate failure**

Add a worker with high demand but no `full_gate_command` or `new_probe`.

Expected:

```text
ERROR[green_gate_high_full_gate] agent=worker
ERROR[green_gate_high_new_probe] agent=worker
```

**Step 5: Add medium missing focused gate failure**

Add a worker with medium demand but no `focused_gate_command`.

Expected:

```text
ERROR[green_gate_medium_focused_gate] agent=worker
```

**Step 6: Add mismatched worker gate failure**

Add a worker where `green_gate.gate_scope == "worker"` and
`verification_command != green_gate.command`.

Expected:

```text
ERROR[green_gate_command_mismatch] agent=worker
```

**Step 7: Add integrator gate success**

Add a worker where:

- `green_gate.gate_scope == "integrator"`
- `green_gate.command == "python3 -m pytest focused"`
- `green_gate.integrator_gate_command == "python3 test_runner.py"`
- `verification_command == "python3 test_runner.py"`

Expected:

- Validator exits 0.

**Step 8: Add read-only supplied demand/gate failures**

Add a `reviewer` with empty `write_set` but supplied `task_demand`.

Expected:

```text
ERROR[read_only_demand_gate] agent=reviewer
```

Add a second `reviewer` with empty `write_set` but supplied `green_gate`.

Expected:

```text
ERROR[read_only_demand_gate] agent=reviewer
```

**Step 9: Run RED**

Run:

```bash
python3 test_runner.py
```

Expected:

- Fails because the validator ignores `task_demand` and `green_gate`.

## Task 2: Implement Validator Contract

**Files:**
- Modify: `scripts/harness_agent_team.py`

**Step 1: Add constants**

```python
TASK_DEMAND_LEVELS = {"low", "medium", "high"}
TASK_DEMAND_FIELDS = ["level", "L", "H_tool", "S_state", "N_obs"]
GREEN_GATE_SCOPES = {"worker", "integrator"}
GREEN_GATE_REQUIRED_FIELDS = ["gate_scope", "command", "rationale"]
```

**Step 2: Add `validate_task_demand()`**

Behavior:

- Only called for `role == "worker"`.
- Reject missing or non-object `task_demand`.
- Reject invalid `level`.
- Reject empty `L`, `H_tool`, `S_state`, `N_obs`.
- Return normalized dict for summary output.

**Step 3: Add `validate_green_gate()`**

Behavior:

- Only called for `role == "worker"`.
- Reject missing or non-object `green_gate`.
- Reject empty `command` and `rationale`.
- Reject invalid `gate_scope`.
- For medium and high demand, require non-empty `focused_gate_command`.
- For high demand, require non-empty `full_gate_command` and `new_probe`.
- For `gate_scope == "worker"`, require `verification_command == green_gate.command`.
- For `gate_scope == "integrator"`, require non-empty
  `integrator_gate_command` and require it to equal `verification_command`.
- Return normalized dict for summary output.

**Step 4: Include normalized fields in summary**

Add to each worker summary:

```python
"task_demand": demand,
"green_gate": green_gate,
```

Read-only role summaries can use `None`.

**Step 5: Update CLI summary**

Print worker demand and gate:

```text
- worker-runtime role=worker ... demand=medium gate_scope=worker green_gate=python3 test_runner.py ...
```

Do not print multi-line JSON in the CLI summary.

## Task 3: Run GREEN Tests

Run:

```bash
python3 test_runner.py
```

Expected:

- Existing agent-team tests pass.
- Existing failures still fail for the original reasons.
- New task-demand and green-gate tests pass.

## Task 4: Update Runtime Docs And Templates

**Files:**
- Modify: `docs/HARNESS_RUNTIME.md`
- Modify: `docs/templates/harness-agent-brief.md`
- Modify: `docs/repo-index.md` if needed.

**Step 1: Update Subagent Contract**

In `docs/HARNESS_RUNTIME.md`, add:

- Worker agents require `task_demand`.
- Worker agents require `green_gate`.
- High-demand workers require full gate and a new probe.
- Demand gates do not replace disjoint write-set validation.

**Step 2: Update agent brief template**

Add optional sections:

```markdown
## Task Demand
- level:
- L:
- H_tool:
- S_state:
- N_obs:

## Green Gate
- gate_scope:
- command:
- rationale:
- focused_gate_command:
- integrator_gate_command:
- full_gate_command:
- new_probe:
```

Make clear that the JSON agent team plan is the validator input; the markdown brief is a durable human-readable companion.

## Task 5: Add A Tiny Example Plan For Manual QA

**Files:**
- Do not commit temporary JSON unless it belongs in docs.

Use a temp file:

```bash
tmp_plan="$(mktemp)"
cat > "$tmp_plan" <<'JSON'
{
  "agents": [
    {
      "id": "worker-demand-demo",
      "role": "worker",
      "scope": "demo validation",
      "write_set": ["scripts/harness_agent_team.py"],
      "verification_command": "python3 test_runner.py",
      "task_demand": {
        "level": "high",
        "L": "Multiple validator branches.",
        "H_tool": "Known local Python runner.",
        "S_state": "Validator, docs, and tests must stay aligned.",
        "N_obs": "Local deterministic JSON."
      },
      "green_gate": {
        "gate_scope": "integrator",
        "command": "python3 test_runner.py",
        "rationale": "Full runner is the integrator gate for validator and docs.",
        "focused_gate_command": "python3 test_runner.py",
        "integrator_gate_command": "python3 test_runner.py",
        "full_gate_command": "python3 test_runner.py",
        "new_probe": "high-demand missing full gate regression"
      }
    }
  ]
}
JSON
python3 scripts/harness_agent_team.py validate "$tmp_plan" --repo-root "$(pwd)"
rm -f "$tmp_plan"
```

Expected:

- Exit 0.
- Output includes `demand=high`.

## Final Verification

Run fresh:

```bash
python3 test_runner.py
git diff --check
```

Also run one direct validator smoke as shown above.

Required final evidence fields:

- `command`
- `exit_code`
- `key_output`
- `timestamp`

## Rollback

- Revert edits to `scripts/harness_agent_team.py`, `test_runner.py`, and docs.
- No runtime-home sync is required unless DHF skill text is also changed in a later implementation.
