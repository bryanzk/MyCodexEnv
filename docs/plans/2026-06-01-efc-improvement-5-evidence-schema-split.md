# EFC Improvement 5 Evidence Schema Split Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

## Execution Order And Dependencies

These three EFC code plans (3, 4, 5) are **not parallel-safe**. Land them in
series, one branch each, in this order:

1. **Improvement 4** (isolated).
2. **Improvement 3** (conversion health).
3. **Improvement 5** (this plan) — **land last.**

This plan has a **hard precondition**: Improvement 3 must already be merged.
Plan 5 and Plan 3 both modify `scripts/harness_report.py`, `scripts/harness_recover.py`,
and `test_runner.py`; running them concurrently violates the Agent Team Gate
(disjoint write sets). Plan 5 also assumes 3's `conversion_health` already exists
and must not change its scoring rules (see Out Of Scope). If 3 is not yet landed,
stop and land 3 first. After 3 merges, rebase this plan on the updated
report/recover/test files before starting.

**Schema accuracy correction (read before Task 2).** The Current Facts below call
`evidence.schema.json` a single flat schema; in the actual file it is richer than
that and the implementer must preserve its structure:

- `schema_version` is `{"type": "integer", "const": 1}` — keep the const.
- It contains a top-level `allOf` conditional block (this is what enforces
  `verification_result` → required `command` / `exit_code` / `key_output`). Do
  **not** flatten or drop the `allOf`; add `evidence_kind` alongside it.
- The compat schema's `properties.event_type.enum` currently lists all ten event
  types. `scripts/harness_env_probe.py` derives
  `evidence_verification_event_present` from this enum
  (`"verification_result" in schema_event_types`). **Keep the full ten-type union
  in the compat schema.** Only the two split schemas narrow the enum per kind. If
  the compat enum is trimmed, the env-probe assertion silently goes false and
  `test_harness_env_probe()` regresses.

**Goal:** Split harness evidence into decision evidence and routine gate receipts so state recovery can stay high-signal while routine verification receipts remain available for audit.

**Architecture:** Add an explicit `evidence_kind` while preserving existing evidence logs. Keep `codex/runtime/evidence.schema.json` as the compatibility entrypoint, and add two focused schemas under `codex/runtime/evidence/`. Update helper validation, reports, env probe, runtime sync tests, and docs together.

**Tech Stack:** JSON Schema files, Python standard library validation in `scripts/harness_evidence.py`, report filters in `scripts/harness_report.py`, runtime probe in `scripts/harness_env_probe.py`, sync verification in `test_runner.py`.

## Definition Of Done

- New events appended by `scripts/harness_evidence.py` include `evidence_kind`.
- Existing old logs without `evidence_kind` still read and report successfully.
- `codex/runtime/evidence.schema.json` remains present for compatibility.
- New schemas exist:
  - `codex/runtime/evidence/decision-evidence.schema.json`
  - `codex/runtime/evidence/routine-gate-receipt.schema.json`
- `scripts/harness_report.py` supports `--evidence-kind decision|routine|unknown`.
- Report JSON includes `evidence_kind_counts`.
- `scripts/harness_recover.py` includes `evidence_kind_counts` and a compact
  `latest_decision_evidence` summary so routine receipts do not dominate
  recovery.
- `scripts/harness_env_probe.py` reports the compatibility schema plus both split schemas.
- `test_runner.py` covers helper append, legacy unknown read, report filter,
  recovery kind summary, schema parse, full sync copy, and `--sync-agents-only`
  nested runtime copy.
- `python3 test_runner.py`, `git diff --check`, and runtime sync verification pass.

## Current Facts

- Current `codex/runtime/evidence.schema.json` is a single schema with `schema_version = 1`, `event_type`, `phase`, and optional command/output fields.
- `scripts/harness_evidence.py` does manual validation; it does not use a JSON Schema library.
- `scripts/harness_report.py` reads any object-shaped JSONL event and tolerates malformed lines.
- `scripts/harness_env_probe.py` only checks `~/.codex/runtime/evidence.schema.json`.
- `test_runner.py` asserts the runtime copied `evidence.schema.json` exactly.
- Runtime evidence logs are local and not committed, so migration must be backward compatible.

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

- No migration or rewriting of existing local JSONL evidence files.
- No external upload or remote evidence store.
- No new non-standard-library JSON Schema dependency.
- No automatic pruning of routine receipts.
- No changes to the conversion-health scoring rules from Improvement 3. Per the
  Execution Order section, Improvement 3 is a hard precondition (must be merged
  first); this plan may consume `evidence_kind` for reporting but must not alter
  3's scoring.

## Evidence Kind Contract

Add field for newly appended events:

```json
"evidence_kind": "decision | routine"
```

Compatibility readers also use `unknown`, but only for old local JSONL events
that predate this field.

Kind derivation:

- `decision`: `checkpoint`, `handoff`, `guardrail_decision`, `approval_request`, `sandbox_failure`.
- `routine`: `startup_probe`, `tool_call`, `verification_result`, `browser_smoke`.
- `subagent_report`: default `decision` when `metadata.decision == true`; otherwise `routine`.
- Old events with no `evidence_kind`: report/recover as `unknown` on read, but
  do not fail.

New appends:

- If caller supplies `--evidence-kind`, it may only be `decision` or `routine`;
  explicit append of `unknown` is invalid.
- If caller omits it, infer from `event_type`.
- Persist inferred kind in the appended event.
- `unknown` exists only for legacy read normalization of old JSONL lines that
  have no `evidence_kind`.

Do not bump `schema_version` in this slice. The field addition is backward compatible for reader code, and old logs remain valid input to reports.

## Schema File Strategy

Keep:

- `codex/runtime/evidence.schema.json`

Add:

- `codex/runtime/evidence/decision-evidence.schema.json`
- `codex/runtime/evidence/routine-gate-receipt.schema.json`

Compatibility schema responsibilities:

- Document shared envelope fields.
- Include `evidence_kind` enum.
- Keep existing `verification_result` requirement for `command`, `exit_code`, and `key_output`.
- Refer readers to the split schemas in `description` fields, not via remote `$ref` that local tooling cannot resolve.

Split schema responsibilities:

- Decision schema requires `evidence_kind = decision` and allows only decision event types.
- Routine schema requires `evidence_kind = routine` and allows only routine event types.

This avoids introducing a JSON Schema resolver dependency.

## Task 1: Add RED Tests For Evidence Kind

**Files:**
- Modify: `test_runner.py`

**Step 1: Extend helper append test**

In `test_harness_evidence_append_and_observer_failure_mode()`:

- After appending a `verification_result`, assert `event["evidence_kind"] == "routine"`.
- Append a `checkpoint` event and assert `evidence_kind == "decision"`.
- Append with `--evidence-kind decision` and `--event-type verification_result`; expect non-zero with `invalid evidence_kind`.
- Append with `--evidence-kind unknown` and any new event; expect non-zero with
  `invalid evidence_kind`.

**Step 2: Extend report test**

In `test_harness_report_cli_summarizes_evidence()`:

- Assert JSON includes `evidence_kind_counts`.
- Assert routine count includes the verification receipt.
- Run `scripts/harness_report.py --evidence-kind routine --json` and assert only routine events match.
- Run `scripts/harness_report.py --evidence-kind decision --json` and assert only decision events match.
- Manually append one old-style JSONL object without `evidence_kind`, then assert
  `evidence_kind_counts["unknown"] == 1`.
- Run `scripts/harness_report.py --evidence-kind unknown --json` and assert the
  old event is returned.

**Step 3: Extend recovery test**

In `test_harness_recovery_smoke()`:

- Add a routine `verification_result`, a decision `checkpoint`, and one legacy
  event without `evidence_kind`.
- Assert recovery JSON includes:

```python
payload["evidence_kind_counts"]["routine"] >= 1
payload["evidence_kind_counts"]["decision"] >= 1
payload["evidence_kind_counts"]["unknown"] >= 1
payload["latest_decision_evidence"]["event_type"] == "checkpoint"
```

- Assert latest verification behavior remains unchanged.

**Step 4: Extend runtime surface test**

In `test_harness_runtime_surfaces_exist_and_parse()`:

- Add both split schema paths to `required_paths`.
- Parse both as JSON.
- Assert compatibility schema has `evidence_kind`.

**Step 5: Extend env probe test**

In `test_harness_env_probe()`:

- Ensure the temp runtime includes the split schema files.
- Assert probe JSON reports `decision_evidence_schema` and `routine_gate_receipt_schema`.

**Step 6: Extend sync tests**

In both sync surfaces:

- `test_sync_renders_template_and_copies_skills()` or the current full-sync test
  that checks runtime files.
- `test_sync_agents_only_copies_and_backs_up_agents()`.

Assert the nested files are copied:

```python
require((codex_home / "runtime" / "evidence" / "decision-evidence.schema.json").exists(), "decision schema should be copied")
require((codex_home / "runtime" / "evidence" / "routine-gate-receipt.schema.json").exists(), "routine schema should be copied")
```

If either sync mode does not copy nested runtime files, update
`scripts/sync_codex_home.sh` in this slice.

**Step 7: Run RED**

Run:

```bash
python3 test_runner.py
```

Expected:

- Fails because schema files, helper field, report filter, and probe keys do not exist.

## Task 2: Add Schema Files

**Files:**
- Modify: `codex/runtime/evidence.schema.json`
- Create: `codex/runtime/evidence/decision-evidence.schema.json`
- Create: `codex/runtime/evidence/routine-gate-receipt.schema.json`

**Step 1: Update compatibility schema**

Add property:

```json
"evidence_kind": {
  "type": "string",
  "enum": ["decision", "routine", "unknown"],
  "description": "New appenders write decision or routine. Unknown is reserved for legacy read normalization."
}
```

Do not add `evidence_kind` to `required` in the compatibility schema yet, because old local evidence logs are still valid inputs.

**Preserve (see Schema accuracy correction in the header):** keep the existing
top-level `allOf` block, the `schema_version` `const: 1`, and the full ten-value
`event_type` enum. `harness_env_probe.py` reads `verification_result` out of this
enum; trimming it regresses `test_harness_env_probe()`.

**Step 2: Create decision schema**

Decision schema should require:

- `schema_version`
- `timestamp`
- `event_type`
- `cwd`
- `phase`
- `evidence_kind`

And enforce:

- `evidence_kind.const = "decision"`
- `event_type.enum = ["approval_request", "sandbox_failure", "checkpoint", "handoff", "guardrail_decision", "subagent_report"]`

**Step 3: Create routine schema**

Routine schema should require the same envelope and enforce:

- `evidence_kind.const = "routine"`
- `event_type.enum = ["startup_probe", "tool_call", "verification_result", "browser_smoke", "subagent_report"]`
- `verification_result` still requires `command`, `exit_code`, `key_output`.

## Task 3: Update Evidence Helper

**Files:**
- Modify: `scripts/harness_evidence.py`

**Step 1: Add constants**

```python
EVIDENCE_KINDS = {"decision", "routine", "unknown"}
DECISION_EVENT_TYPES = {"approval_request", "sandbox_failure", "checkpoint", "handoff", "guardrail_decision"}
ROUTINE_EVENT_TYPES = {"startup_probe", "tool_call", "verification_result", "browser_smoke"}
APPENDABLE_EVIDENCE_KINDS = {"decision", "routine"}
```

Handle `subagent_report` as metadata-dependent.

**Step 2: Add inference**

```python
def infer_evidence_kind(event: dict[str, Any]) -> str:
    ...
```

**Step 3: Validate explicit kind**

In `validate_event()`:

- If `evidence_kind` is present in an appended event, it must be in
  `APPENDABLE_EVIDENCE_KINDS`; `unknown` is rejected for new writes.
- If `evidence_kind` is missing, assign it before validation in `build_event()`.
- If explicit kind conflicts with inferred kind, fail with a clear message.

**Step 4: Add CLI option**

Add:

```python
append_parser.add_argument("--evidence-kind", choices=sorted(APPENDABLE_EVIDENCE_KINDS))
```

Include it in `build_event()`.

## Task 4: Update Report Reader And Filters

**Files:**
- Modify: `scripts/harness_report.py`

**Step 1: Normalize old events**

When reading events, if `evidence_kind` is missing:

```python
event["evidence_kind"] = "unknown"
```

Do not mutate files on disk.

**Step 2: Add CLI filter**

Add:

```python
parser.add_argument("--evidence-kind", choices=["decision", "routine", "unknown"])
```

Update `event_matches()`.

**Step 3: Add counts**

Add to summary:

```python
"evidence_kind_counts": dict(Counter(str(event.get("evidence_kind", "unknown")) for event in filtered))
```

Add markdown section:

```markdown
## Evidence Kind Distribution
```

## Task 5: Update Env Probe And Sync Tests

**Files:**
- Modify: `scripts/harness_env_probe.py`
- Modify: `test_runner.py`

**Step 1: Probe split schemas**

In `scripts/harness_env_probe.py`, require:

- `runtime/evidence.schema.json`
- `runtime/evidence/decision-evidence.schema.json`
- `runtime/evidence/routine-gate-receipt.schema.json`

Output keys under `runtime`:

```json
"decision_evidence_schema": "...",
"routine_gate_receipt_schema": "...",
"split_evidence_schemas_present": true
```

**Step 2: Ensure sync copies nested runtime files**

If sync already copies `codex/runtime/*` recursively, only update tests to assert the new files are copied. If it does not, update `scripts/sync_codex_home.sh` in the same slice.

Update both existing sync test surfaces:

- Full sync test that verifies runtime files copied into `~/.codex/runtime`.
- `--sync-agents-only` test, because this mode also copies runtime policy/schema
  surfaces today.

## Task 6: Update Recovery For High-Signal State

**Files:**
- Modify: `scripts/harness_recover.py`
- Modify: `test_runner.py`

**Step 1: Normalize old events**

When reading events, if `evidence_kind` is missing:

```python
event["evidence_kind"] = "unknown"
```

Do not mutate local JSONL files.

**Step 2: Add evidence kind counts**

Add to recovery payload:

```python
"evidence_kind_counts": {
    "decision": decision_count,
    "routine": routine_count,
    "unknown": unknown_count,
}
```

Counts apply only to events matching the repo cwd.

**Step 3: Add latest decision summary**

Add:

```python
"latest_decision_evidence": compact_decision_event(decision_events[0]) if decision_events else {}
```

Compact decision event fields:

- `timestamp`
- `event_type`
- `phase`
- `message`
- `key_output`
- `failure_class`

Do not include full metadata or long command output in recovery. The purpose is
to keep startup/handoff state high-signal.

**Step 4: Preserve latest verification**

Do not change `latest_verification` behavior; it still returns the latest
matching `verification_result`, regardless of evidence kind.

## Task 7: Update Docs

**Files:**
- Modify: `docs/HARNESS_RUNTIME.md`
- Modify: `docs/repo-index.md`
- Modify: `docs/CODEX_ENV_REPRODUCTION.md` if runtime sync docs name only the old schema.

Docs must state:

- Decision evidence is for state, handoff, approvals, guardrails, and durable recovery.
- Routine gate receipts are for tests, browser smoke, startup probes, and ordinary tool calls.
- Local logs are not migrated; old missing-kind events report as `unknown`.
- State log should promote decision evidence summaries rather than copying every routine receipt.
- Recovery output includes evidence-kind counts and latest decision evidence so
  routine receipts do not bury handoff/decision signals.

## Task 8: Runtime Sync

Run:

```bash
./scripts/sync_codex_home.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --skip-superpowers-sync
```

Verify:

```bash
diff -u codex/runtime/evidence.schema.json "$HOME/.codex/runtime/evidence.schema.json"
diff -u codex/runtime/evidence/decision-evidence.schema.json "$HOME/.codex/runtime/evidence/decision-evidence.schema.json"
diff -u codex/runtime/evidence/routine-gate-receipt.schema.json "$HOME/.codex/runtime/evidence/routine-gate-receipt.schema.json"
```

## Final Verification

Run fresh:

```bash
python3 test_runner.py
git diff --check
python3 scripts/harness_env_probe.py --codex-home "$HOME/.codex" --json
python3 scripts/harness_report.py --codex-home "$HOME/.codex" --evidence-kind decision --json
python3 scripts/harness_report.py --codex-home "$HOME/.codex" --evidence-kind routine --json
```

Required final evidence fields:

- `command`
- `exit_code`
- `key_output`
- `timestamp`

## Rollback

- Revert schema files and helper/report/probe/test/docs changes.
- Re-run runtime sync.
- Confirm old compatibility schema is restored at `$HOME/.codex/runtime/evidence.schema.json`.
