# EFC Improvement 6 Task Demand Enforcement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Promote `## Task Demand (D_task)` from an advisory requirements-template prompt into a validated requirements artifact contract.

**Architecture:** Keep `scripts/harness_requirements.py` as the single requirements validation entrypoint. Extend its existing Markdown section parser with a small field-level validator for `Task Demand (D_task)`: require `estimated_level` to be `low`, `medium`, or `high`, and require non-empty `L`, `H_tool`, `S_state`, and `N_obs` component fields, while leaving deeper semantic grading and scoring out of scope.

**Tech Stack:** Python standard library, current Markdown section parsing in `scripts/harness_requirements.py`, repo-local `test_runner.py`, and existing Harness Runtime docs/state surfaces.

## Definition Of Done

- `scripts/harness_requirements.py validate PATH` fails when a requirements artifact omits `## Task Demand (D_task)`.
- `scripts/harness_requirements.py validate PATH` fails when `## Task Demand (D_task)` exists but has no meaningful content.
- `estimated_level` must be present and exactly one of `low`, `medium`, or `high`.
- `L`, `H_tool`, `S_state`, and `N_obs` must each be present and have non-empty text after `:`.
- Ordering remains loose: fields may appear in any order inside `Task Demand (D_task)`.
- Component values remain free text: no numeric scoring, no minimum word count, no inference.
- `docs/templates/harness-requirements.md` continues to validate successfully after its placeholder line is converted to a valid example.
- Existing negative checks for missing headings, empty acceptance criteria, and missing verification commands continue to fail for the intended reasons.
- Docs describe the new enforcement boundary without claiming full semantic scoring or automatic propagation of task demand.
- Fresh verification evidence is captured with `command`, `exit_code`, `key_output`, and `timestamp`.
- No implementation begins until this plan is reviewed and accepted.

## Source Context

- `docs/handoffs/2026-06-01-efc-harness-patch-plan.md` names Improvement 6 as a deferred follow-up: add `"Task Demand (D_task)"` to `REQUIRED_HEADINGS` and cover it with an eval/test.
- `docs/templates/harness-requirements.md` already includes `## Task Demand (D_task)` with advisory field labels.
- `scripts/harness_requirements.py` currently validates required headings, non-empty Goal, at least one Acceptance Criteria item, and at least one Verification Gate item.
- `test_runner.py::test_harness_requirements_validator()` is the focused test surface.
- `docs/HARNESS_RUNTIME.md` describes requirements artifacts as source of truth only after validation, so this is the correct enforcement point.

## Scope

Modify only:

- `scripts/harness_requirements.py`
- `test_runner.py`
- `docs/templates/harness-requirements.md`
- `docs/HARNESS_RUNTIME.md`
- `docs/harness-state.md`

Optional only if the implementation changes user-facing command descriptions:

- `README.md`
- `docs/repo-index.md`
- `docs/LIFECYCLE_SKILL_ROUTING.md`

## Backward Compatibility Impact

This is an intentional validation tightening. Older requirements artifacts that omit `Task Demand (D_task)`, keep the template placeholder `estimated_level: low | medium | high`, or leave task-demand fields blank will fail validation after this slice.

Mitigation:

- Error messages must identify the exact missing or invalid field.
- Runtime docs must say this is a required requirements-artifact section.
- Do not migrate or rewrite old artifacts automatically.
- Do not reject free-text estimates beyond the required field presence and `estimated_level` enum.

## Out Of Scope

- Do not assign numeric task-demand scores.
- Do not infer `task_demand` from source code or tool traces.
- Do not require minimum word counts for `L`, `H_tool`, `S_state`, or `N_obs`.
- Do not enforce heading or field order inside `Task Demand (D_task)`.
- Do not add a new schema language or Markdown parser dependency.
- Do not rewrite existing requirements artifacts outside this repo.
- Do not change `scripts/harness_agent_team.py`, evidence schemas, conversion-health scoring, hooks, or model routing.
- Do not mutate runtime homes under `$HOME/.codex` unless a later implementation changes a synced runtime surface and verifies the sync path.

## Task Demand

- estimated_level: medium
- L: about 10-14 concrete reasoning/action steps from preflight through RED tests, validator helper, template/docs updates, checkpoint, and verification.
- H_tool: low; existing helper, test runner, and docs surfaces are known.
- S_state: medium; must preserve post-Improvement-5 clean-main state and avoid overstating semantic enforcement.
- N_obs: low; local deterministic tests and docs checks are sufficient.

## Execution Lane

- lane: `local_dev`
- allowed external systems: none required.
- forbidden actions: no deployment, no remote service mutation, no secret reads, no customer data, no live provider calls.
- escalation gate: any request to publish, merge, push, or sync runtime homes must move to `ship` with fresh verification and explicit approval.

## Failure Modes To Handle

- Missing source artifact: validator prints the read failure, exits non-zero, and does not write any output file.
- Missing Task Demand section: validator exits non-zero with `missing heading: ## Task Demand (D_task)`.
- Empty Task Demand section: validator exits non-zero with `task demand must be non-empty`.
- Missing field, including `estimated_level`: validator exits non-zero with `task demand field is required: FIELD`.
- Blank field, including `estimated_level`: validator exits non-zero with `task demand field must be non-empty: FIELD`.
- Placeholder or invalid non-empty `estimated_level`: validator exits non-zero with `task demand estimated_level must be one of: low, medium, high`.
- Malformed Markdown structure: preserve current behavior; only lines beginning with `## ` define sections.
- Partial implementation risk: tests must fail before implementation and pass after implementation.
- Scope creep: semantic scoring and downstream propagation must remain deferred unless the user explicitly expands the slice.

## Task 1: Preflight And Branch

**Files:**

- Read: `AGENTS.md`
- Read: `docs/repo-index.md`
- Read: `docs/harness-state.md`
- Read: `docs/handoffs/2026-06-01-efc-harness-patch-plan.md`

**Step 1: Confirm clean continuation state**

Run:

```bash
git status --short --branch
python3 scripts/harness_recover.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --json
python3 scripts/harness_env_probe.py --codex-home "$HOME/.codex" --json
```

Expected:

- `git status` shows clean `main`.
- `harness_recover` reports `dirty_status=clean`.
- `harness_env_probe` reports runtime surfaces present.

**Step 2: Create an implementation branch**

Run:

```bash
git switch -c codex/mce-20260601-efc-impr6-task-demand-enforcement
```

Expected:

- Current branch is `codex/mce-20260601-efc-impr6-task-demand-enforcement`.

## Task 2: Add RED Tests

**Files:**

- Modify: `test_runner.py`
- Test target: `test_harness_requirements_validator()`

**Step 1: Preserve valid-template success case**

Keep the existing assertion:

```python
code, out, err = run([sys.executable, str(HARNESS_REQUIREMENTS), "validate", str(HARNESS_REQUIREMENTS_TEMPLATE)])
require(code == 0, f"requirements template should validate: {err or out}")
```

This test should still pass after the template is updated in Task 4.

**Step 2: Add missing Task Demand heading negative case**

Create a temp artifact from `docs/templates/harness-requirements.md` with the whole `## Task Demand (D_task)` section removed.

Expected assertion:

```python
code, out, err = run([sys.executable, str(HARNESS_REQUIREMENTS), "validate", str(invalid_missing_task_demand)])
require(code != 0 and "missing heading: ## Task Demand (D_task)" in err, "missing task demand heading should fail")
```

**Step 3: Add empty Task Demand section negative case**

Create a temp artifact where `## Task Demand (D_task)` remains, but all task-demand field lines before `## Source Of Truth` are removed.

Expected assertion:

```python
code, out, err = run([sys.executable, str(HARNESS_REQUIREMENTS), "validate", str(invalid_empty_task_demand)])
require(code != 0 and "task demand must be non-empty" in err, "empty task demand should fail")
```

**Step 4: Add placeholder estimated_level negative case**

Create a temp artifact where Task Demand contains:

```markdown
- estimated_level: low | medium | high
- L (reasoning/action steps): enough steps to justify medium
- H_tool (tool-selection ambiguity): low
- S_state (cross-module state tracking): medium
- N_obs (observation/external noise): low
```

Expected assertion:

```python
code, out, err = run([sys.executable, str(HARNESS_REQUIREMENTS), "validate", str(invalid_placeholder_level)])
require(code != 0 and "task demand estimated_level must be one of: low, medium, high" in err, "placeholder task demand level should fail")
```

**Step 5: Add missing estimated_level negative case**

Create a temp artifact where Task Demand contains all component fields but omits `estimated_level`.

Expected assertion:

```python
code, out, err = run([sys.executable, str(HARNESS_REQUIREMENTS), "validate", str(invalid_missing_estimated_level)])
require(code != 0 and "task demand field is required: estimated_level" in err, "missing task demand estimated_level should fail")
```

**Step 6: Add blank estimated_level negative case**

Create a temp artifact where Task Demand contains:

```markdown
- estimated_level:
- L (reasoning/action steps): enough steps to justify medium
- H_tool (tool-selection ambiguity): low
- S_state (cross-module state tracking): medium
- N_obs (observation/external noise): low
```

Expected assertion:

```python
code, out, err = run([sys.executable, str(HARNESS_REQUIREMENTS), "validate", str(invalid_blank_estimated_level)])
require(code != 0 and "task demand field must be non-empty: estimated_level" in err, "blank task demand estimated_level should fail")
```

**Step 7: Add missing component field negative cases**

Loop over `L`, `H_tool`, `S_state`, and `N_obs`. For each field, create a temp artifact with a valid Task Demand section except that one field is omitted.

Expected assertion:

```python
require(code != 0 and f"task demand field is required: {field}" in err, f"missing task demand field should fail: {field}")
```

**Step 8: Add blank component field negative case**

Create a temp artifact where one component field is present but blank, for example:

```markdown
- L (reasoning/action steps):
```

Expected assertion:

```python
require(code != 0 and "task demand field must be non-empty: L" in err, "blank task demand field should fail")
```

**Step 9: Add explicit populated success case**

Create a temp artifact with:

```markdown
## Task Demand (D_task)
- estimated_level: medium
- L (reasoning/action steps): 10-14 focused implementation and verification steps.
- H_tool (tool-selection ambiguity): low because existing helper and tests are known.
- S_state (cross-module state tracking): medium because docs, validator, tests, and state must stay aligned.
- N_obs (observation/external noise): low because checks are local and deterministic.
```

Expected assertion:

```python
code, out, err = run([sys.executable, str(HARNESS_REQUIREMENTS), "validate", str(valid_populated_task_demand)])
require(code == 0 and "valid" in out, f"populated task demand should validate: {err or out}")
```

**Step 10: Run focused RED gate**

Run:

```bash
python3 -c 'import test_runner; test_runner.test_harness_requirements_validator()'
```

Expected:

- Fails before validator changes because missing, placeholder, and incomplete Task Demand cases are still accepted.

## Task 3: Implement Minimal Validator Change

**Files:**

- Modify: `scripts/harness_requirements.py`

**Step 1: Require the heading**

Add `"Task Demand (D_task)"` to `REQUIRED_HEADINGS`, preferably after `"Constraints"` and before `"Source Of Truth"` to match the template order.

**Step 2: Add a small Task Demand parser**

Use `meaningful_lines(sections["Task Demand (D_task)"])`.

Normalize lines by stripping one leading Markdown bullet:

```python
line = line.removeprefix("- ").strip()
```

Parse only `label: value` pairs. Ignore unknown labels for forward compatibility.

Map full template labels to stable internal field names:

- `estimated_level` -> `estimated_level`
- `L (reasoning/action steps)` -> `L`
- `H_tool (tool-selection ambiguity)` -> `H_tool`
- `S_state (cross-module state tracking)` -> `S_state`
- `N_obs (observation/external noise)` -> `N_obs`

**Step 3: Validate required field shape**

If the section has no meaningful lines, append:

```python
"task demand must be non-empty"
```

For each missing field, including `estimated_level`, append:

```python
f"task demand field is required: {field}"
```

For each present but blank field, including `estimated_level`, append:

```python
f"task demand field must be non-empty: {field}"
```

If non-empty `estimated_level` is not `low`, `medium`, or `high`, append:

```python
"task demand estimated_level must be one of: low, medium, high"
```

Keep the existing error aggregation style.

**Step 4: Run focused GREEN gate**

Run:

```bash
python3 -c 'import test_runner; test_runner.test_harness_requirements_validator()'
```

Expected:

- Prints `[PASS] harness requirements validator`.

## Task 4: Update Template And Docs

**Files:**

- Modify: `docs/templates/harness-requirements.md`
- Modify: `docs/HARNESS_RUNTIME.md`
- Optionally modify only if wording currently conflicts: `README.md`, `docs/repo-index.md`, `docs/LIFECYCLE_SKILL_ROUTING.md`

**Step 1: Make the template validate**

Replace the placeholder line:

```markdown
- estimated_level: low | medium | high
```

with a valid example such as:

```markdown
- estimated_level: medium
```

Keep the component field labels and add enough guidance text after each `:` so the template itself validates.

**Step 2: Document the enforcement boundary**

Update requirements validation docs to say:

- `Task Demand (D_task)` is required in requirements artifacts.
- The validator enforces `estimated_level` enum and non-empty `L`, `H_tool`, `S_state`, and `N_obs`.
- It does not score, infer, or deeply validate the semantic quality of those values.

**Step 3: Avoid overclaiming**

Do not write that task demand is automatically correct, complete, scored, or propagated through all downstream planning surfaces.

## Task 5: Full Verification

**Files:**

- No edits.

**Step 1: Run focused validator command and capture evidence**

Run:

```bash
python3 scripts/harness_requirements.py validate docs/templates/harness-requirements.md
rc=$?
printf 'exit_code=%s\n' "$rc"
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
exit "$rc"
```

Expected:

- Exit code `0`.
- Output contains `valid`.
- Evidence records:
  - command: `python3 scripts/harness_requirements.py validate docs/templates/harness-requirements.md`
  - exit_code: `0`
  - key_output: `valid`
  - timestamp: current UTC timestamp from the command output.

**Step 2: Run full test suite and capture evidence**

Run:

```bash
python3 test_runner.py
rc=$?
printf 'exit_code=%s\n' "$rc"
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
exit "$rc"
```

Expected:

- Exit code `0`.
- Output contains `[PASS] all tests`.
- Evidence records:
  - command: `python3 test_runner.py`
  - exit_code: `0`
  - key_output: `[PASS] all tests`
  - timestamp: current UTC timestamp from the command output.

**Step 3: Run whitespace check and capture evidence**

Run:

```bash
git diff --check
rc=$?
printf 'exit_code=%s\n' "$rc"
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
exit "$rc"
```

Expected:

- Exit code `0`.
- No output.
- Evidence records:
  - command: `git diff --check`
  - exit_code: `0`
  - key_output: `no whitespace errors`
  - timestamp: current UTC timestamp from the command output.

## Task 6: Checkpoint And Handoff

**Files:**

- Modify: `docs/harness-state.md`

**Step 1: Append checkpoint only after implementation validation**

Run:

```bash
python3 scripts/harness_checkpoint.py append \
  --phase validation \
  --summary "Improvement 6 Task Demand requirements enforcement implemented and verified" \
  --changed-surface "scripts/harness_requirements.py" \
  --changed-surface "test_runner.py" \
  --changed-surface "docs/templates/harness-requirements.md" \
  --changed-surface "docs/HARNESS_RUNTIME.md" \
  --changed-surface "docs/harness-state.md" \
  --verification-command "python3 test_runner.py" \
  --verification-exit-code 0 \
  --verification-key-output "[PASS] all tests" \
  --next-safe-task "Review Improvement 6 diff, then stage/commit/push and open or merge per ship flow."
```

Expected:

- `docs/harness-state.md` current snapshot and state log reflect Improvement 6 validation.

**Step 2: Re-run final checks after checkpoint and capture evidence**

Run:

```bash
git diff --check
rc=$?
printf 'exit_code=%s\n' "$rc"
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
exit "$rc"
```

Then run:

```bash
python3 scripts/harness_recover.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --json
rc=$?
printf 'exit_code=%s\n' "$rc"
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
exit "$rc"
```

Expected:

- `git diff --check` exits `0`.
- `harness_recover` reports `phase=validation`, dirty files owned by this slice, and the new next safe task.
- Evidence records include `command`, `exit_code`, `key_output`, and `timestamp` for both commands.

## Review Notes For Committee

- This revised scope follows the committee recommendation: it enforces a populated D_task shape, not just heading presence.
- It still avoids semantic overreach: no automatic score, no field-order gate, no minimum text length, no downstream propagation claims.
- The main backward-compatibility cost is intentional: older artifacts must be updated before they can validate.
- A future slice may add richer task-demand quality checks only after deciding how placeholders, rough estimates, and later refinements should be represented.
