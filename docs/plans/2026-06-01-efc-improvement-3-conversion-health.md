# EFC Improvement 3 Conversion Health Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

## Execution Order And Dependencies

These three EFC code plans (3, 4, 5) are **not parallel-safe**. They share write
sets — all three modify `test_runner.py`, `docs/HARNESS_RUNTIME.md`, and
`docs/repo-index.md`; plans 3 and 5 both modify `scripts/harness_report.py` and
`scripts/harness_recover.py`. Under the harness Agent Team Gate (disjoint write
sets), they cannot be dispatched concurrently. Land them in series, one branch
each, in this order:

1. **Improvement 4** (most isolated — only `harness_agent_team.py` + tests/docs).
2. **Improvement 3** (this plan).
3. **Improvement 5** (depends on 3: it consumes `evidence_kind` and must not alter
   3's conversion-health scoring).

This plan (3) **must land before 5**. After each plan, re-run the full
`test_runner.py` on a clean tree before opening the next branch.

**DHF Output Contract sequencing.** Task 4 below adds a `conversion_health` item
to the generic DHF Output Contract and re-syncs `~/.codex`. The earlier
doc-only patch (improvements 1 & 2,
`docs/handoffs/2026-06-01-efc-harness-patch-plan.md`) **also** adds an Output
Contract item (`task_demand` + effective-feedback check) to the same skill
region. These two edits collide. Whichever lands second must re-run the
`evals.json` pin recheck (Task 4 Step 2) because item numbering shifts, and must
re-run `sync_codex_home.sh`. Confirm which of the two has already landed before
editing the Output Contract.

**Goal:** Add a stall / conversion-health signal computed from existing local evidence, expose it through `harness_report.py` and `harness_recover.py`, and require the generic DHF Output Contract to surface the flag.

**Architecture:** Keep the signal local, deterministic, and derived only from existing JSONL evidence fields. Introduce one shared pure helper so `harness_report.py` and `harness_recover.py` cannot drift. Treat conversion health as an advisory signal for planning and handoff, not as an automatic blocker.

**Tech Stack:** Python standard library, existing local evidence JSONL, `test_runner.py`, `scripts/harness_evidence.py`, `scripts/harness_report.py`, `scripts/harness_recover.py`, `codex/skills/delivery-harness-framework/SKILL.md`, `./scripts/sync_codex_home.sh`.

## Definition Of Done

- `scripts/harness_report.py --json` includes `conversion_health`.
- Markdown report output includes a compact `Conversion Health` section.
- `scripts/harness_recover.py --json` includes the same `conversion_health` object for the current repo.
- Recovery markdown includes the conversion status and reason.
- `codex/skills/delivery-harness-framework/SKILL.md` Output Contract requires stating conversion-health status when evidence exists.
- Runtime skill mirror is byte-identical after sync.
- `python3 test_runner.py`, `git diff --check`, and the DHF mirror diff pass with fresh evidence.

## Current Facts

- `scripts/harness_report.py` already reads all `*.jsonl` evidence files, filters by `cwd`, `since`, `phase`, and `event_type`, and returns counts plus recent verifications/failures.
- `scripts/harness_recover.py` currently has a separate evidence reader that returns `evidence_status`, the latest matching `verification_result`, and malformed count.
- Existing evidence fields are enough for a first signal: `timestamp`, `event_type`, `cwd`, `phase`, `command`, `exit_code`, `key_output`, `failure_class`, and `message`.
- `codex/hooks/harness_observer.py` writes routine `tool_call` evidence and should remain non-blocking.
- `test_runner.py` contains the harness report and recovery tests; there is no separate `tests/` directory.

## Scope

**Create:**
- `scripts/harness_feedback.py`

**Modify:**
- `scripts/harness_report.py`
- `scripts/harness_recover.py`
- `test_runner.py`
- `docs/HARNESS_RUNTIME.md`
- `docs/repo-index.md`
- `codex/skills/delivery-harness-framework/SKILL.md`

**Runtime sync after skill edit:**
- `~/.codex/skills/delivery-harness-framework/SKILL.md`

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

- No schema migration in this slice.
- No new evidence event type.
- No model-token accounting.
- No automatic stop / retry policy.
- No remote evidence ingestion.
- No changes to `harness_observer.py` beyond using existing event shapes.

## Conversion Health Contract

Add a shared pure function:

```python
def compute_conversion_health(events: list[dict[str, Any]]) -> dict[str, Any]:
    ...
```

Return shape:

```json
{
  "status": "healthy | watch | stalled | insufficient_evidence",
  "reason": "short human-readable reason",
  "window_event_count": 0,
  "tool_call_count": 0,
  "productive_event_count": 0,
  "repeated_command_count": 0,
  "latest_productive_timestamp": "",
  "low_conversion_signals": []
}
```

Status rules:

- `insufficient_evidence`: fewer than three matching evidence events.
- `healthy`: at least one productive event in the recent window and no low-conversion signal.
- `watch`: some low-conversion signal exists but there is also recent productive feedback.
- `stalled`: low-conversion signal exists and no productive event appears in the recent window.

Status precedence: `compute_conversion_health()` itself returns
`insufficient_evidence` for fewer than three matching events. Report/recover
callers may post-process that helper result to `watch` only when malformed
evidence exists, because malformed evidence is an external reader health signal
not visible to the pure helper.

Productive events:

- `verification_result` with `command`, `exit_code`, and `key_output`.
- `browser_smoke` with `key_output`.
- `checkpoint` or `handoff` with `message` or `key_output`.
- `subagent_report` with `message` or `key_output`.

Low-conversion signals:

- `many_tool_calls_without_productive_feedback`: five or more `tool_call` events and zero productive events in the recent window.
- `repeated_same_command`: same non-empty `command` appears three or more times without an intervening productive event.
- `malformed_evidence_present`: malformed evidence count is non-zero. This signal is supplied by report/recover callers as an optional flag, not inferred by the helper from events.

Keep the default window simple: use the already filtered event list after existing
CLI filters, sorted newest first. Do not add time-window semantics in this
slice.

### Window Semantics

Use **post-filter, pre-limit** events for conversion health.

- Existing report filters (`--cwd`, `--since`, `--phase`, `--event-type`) define
  the semantic population.
- Display truncation (`--limit`) must not hide earlier evidence from the
  conversion calculation.
- `recent_verifications` and `recent_failures` can stay limit-aware for display,
  but `conversion_health.window_event_count` must count the full filtered set.
- `harness_recover.py` has no user-facing limit option today, so it computes
  health over all matching events for the repo cwd.

This removes ambiguity: `--limit 1` can shrink displayed events, but it must not
turn a healthy evidence history into `insufficient_evidence`.

## Task 1: Add Shared Conversion Helper

**Files:**
- Create: `scripts/harness_feedback.py`
- Modify: `test_runner.py`

**Step 1: Write failing tests**

Add a new `test_harness_feedback_conversion_health()` near the harness tests.

Test cases:

```python
def test_harness_feedback_conversion_health():
    from scripts.harness_feedback import compute_conversion_health

    healthy = [
        {"timestamp": "2026-06-01T00:00:03", "event_type": "verification_result", "command": "python3 test_runner.py", "exit_code": 0, "key_output": "[PASS]"},
        {"timestamp": "2026-06-01T00:00:02", "event_type": "tool_call", "command": "python3 test_runner.py"},
        {"timestamp": "2026-06-01T00:00:01", "event_type": "tool_call", "command": "rg foo"},
    ]
    require(compute_conversion_health(healthy)["status"] == "healthy", "verification should be productive")

    stalled = [
        {"timestamp": f"2026-06-01T00:00:0{i}", "event_type": "tool_call", "command": "pytest -q"}
        for i in range(6)
    ]
    result = compute_conversion_health(stalled)
    require(result["status"] == "stalled", "repeated unproductive tool calls should be stalled")
    require("many_tool_calls_without_productive_feedback" in result["low_conversion_signals"], "stall signal should be named")

    insufficient = [{"timestamp": "2026-06-01T00:00:01", "event_type": "tool_call", "command": "pwd"}]
    require(compute_conversion_health(insufficient)["status"] == "insufficient_evidence", "small windows should be explicit")
```

Add the test call to the bottom test runner sequence.

**Step 2: Run RED**

Run:

```bash
python3 test_runner.py
```

Expected:

- Fails because `scripts.harness_feedback` does not exist.

**Step 3: Implement helper**

Create `scripts/harness_feedback.py` with only standard library imports.

Implementation rules:

- Do not read files in this helper.
- Do not know about repo paths.
- Accept event dictionaries already selected by callers.
- Sort by `timestamp` ascending only for repeated-command sequence checks; keep output count based on the input list.
- Treat missing fields as empty strings.

**Step 4: Run GREEN for helper**

Run:

```bash
python3 test_runner.py
```

Expected:

- New helper test passes.

## Task 2: Add Conversion Health To Report CLI

**Files:**
- Modify: `scripts/harness_report.py`
- Modify: `test_runner.py`

**Step 1: Extend existing report test**

In `test_harness_report_cli_summarizes_evidence()`, assert:

```python
require("conversion_health" in summary, "report JSON should include conversion health")
require(summary["conversion_health"]["status"] in {"healthy", "watch", "stalled", "insufficient_evidence"}, "conversion status should be valid")
```

For the existing markdown report call, assert:

```python
require("Conversion Health" in out, "markdown report should include conversion health section")
```

Add a limit regression:

```python
code, out, err = run([
    sys.executable,
    str(HARNESS_REPORT),
    "--codex-home",
    str(codex_home),
    "--cwd",
    str(ROOT),
    "--limit",
    "1",
    "--json",
])
limited_summary = json.loads(out)
require(
    limited_summary["conversion_health"]["window_event_count"] >= 2,
    "conversion health should use post-filter pre-limit events",
)
```

**Step 2: Run RED**

Run:

```bash
python3 test_runner.py
```

Expected:

- Fails because `conversion_health` is missing.

**Step 3: Integrate helper**

In `scripts/harness_report.py`:

- Import `compute_conversion_health`.
- Split the filtered population from the display list:

```python
matching = [event for event in events if event_matches(event, args)]
matching.sort(key=event_timestamp, reverse=True)
# NOTE: --limit defaults to 50 (never None) in harness_report.py, so slice
# directly. Conversion health is computed on the full `matching` set, never the
# display slice, so --limit can shrink the displayed list without affecting the
# signal.
display_events = matching[: args.limit]
conversion_health = compute_conversion_health(matching)
```

- Use `display_events` for recent lists and counts that are intentionally
  limited.
- Use `matching` for `conversion_health`.
- Include malformed signal by passing a flag or by post-processing:

```python
if malformed:
    conversion_health["low_conversion_signals"].append("malformed_evidence_present")
    if conversion_health["status"] in {"healthy", "insufficient_evidence"}:
        conversion_health["status"] = "watch"
```

Malformed handling rules:

- `malformed_evidence_present` is always included when malformed count is
  non-zero.
- It can raise `healthy` or `insufficient_evidence` to `watch`.
- It must not downgrade `stalled`; a stalled signal is already stronger.
- It must not erase the original low-conversion signals.

- Add `conversion_health` to JSON summary.
- Add markdown section:

```markdown
## Conversion Health
- status: `...`
- reason: ...
- productive_event_count: ...
- low_conversion_signals: ...
```

**Step 4: Run GREEN**

Run:

```bash
python3 test_runner.py
```

Expected:

- Report test passes and existing output remains backwards compatible.

## Task 3: Add Conversion Health To Recovery CLI

**Files:**
- Modify: `scripts/harness_recover.py`
- Modify: `test_runner.py`

**Step 1: Extend recovery smoke test**

In `test_harness_recovery_smoke()`:

- For empty evidence, assert `conversion_health.status == "insufficient_evidence"`.
- For tool-call-only evidence, assert status is `insufficient_evidence`, `watch`, or `stalled` based on the number of events used in the test.
- Add five tool-call events with the same command before a verification event case, then assert a stalled status before the verification is appended.
- After verification evidence is appended, assert status returns `healthy` or `watch`, not `stalled`.
- Add a malformed JSONL line and assert `malformed_evidence_present` appears and
  status is at least `watch` unless it is already `stalled`.

**Step 2: Run RED**

Run:

```bash
python3 test_runner.py
```

Expected:

- Fails because recovery JSON does not include `conversion_health`.

**Step 3: Refactor recovery evidence read**

In `scripts/harness_recover.py`:

- Keep current output keys for compatibility.
- Return all matching events from the internal evidence reader or add a second helper function.
- Compute `conversion_health` from matching events and malformed count.
- Add it to payload:

```python
"conversion_health": conversion_health,
```

In `render_markdown()`, add:

```markdown
- conversion_health: `status` - reason
```

**Step 4: Run GREEN**

Run:

```bash
python3 test_runner.py
```

Expected:

- Recovery smoke passes.

## Task 4: Surface In DHF Output Contract

**Files:**
- Modify: `codex/skills/delivery-harness-framework/SKILL.md`
- Modify: `codex/skills/delivery-harness-framework/evals/evals.json` only if needed.
- Modify: `docs/HARNESS_RUNTIME.md`
- Modify: `docs/repo-index.md`

**Step 1: Update DHF skill**

Add to Evidence And Report Gate:

- Use `harness_report.py --json` or `harness_recover.py --json` when local evidence exists.
- Report `conversion_health.status` and reason in handoff or final routing output.
- Treat `stalled` as a planning/recovery warning, not an automatic failure.

Add to Output Contract:

- `conversion_health` status and whether any stall / low-conversion signals are present.

**Step 2: Check eval pins**

Run:

```bash
rg -n "Output Contract|conversion_health|harness_report|harness_recover" codex/skills/delivery-harness-framework/evals/evals.json
```

If evals assert old contract content, update them in the same slice.

**Step 3: Update docs**

In `docs/HARNESS_RUNTIME.md`, add the conversion-health contract under Evidence or Recovery.

In `docs/repo-index.md`, mention `scripts/harness_feedback.py`.

## Task 5: Sync Runtime Skill Copy

**Files:**
- Runtime mirror only after source edits.

**Step 1: Run sync**

Run:

```bash
./scripts/sync_codex_home.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --skip-superpowers-sync
```

**Step 2: Prove byte identity**

Run:

```bash
diff -u codex/skills/delivery-harness-framework/SKILL.md "$HOME/.codex/skills/delivery-harness-framework/SKILL.md"
```

Expected:

- No output, exit 0.

## Final Verification

Run fresh:

```bash
python3 test_runner.py
git diff --check
python3 scripts/harness_report.py --codex-home "$HOME/.codex" --cwd "$(pwd)" --json
python3 scripts/harness_recover.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --json
diff -u codex/skills/delivery-harness-framework/SKILL.md "$HOME/.codex/skills/delivery-harness-framework/SKILL.md"
```

Required final evidence fields:

- `command`
- `exit_code`
- `key_output`
- `timestamp`

## Rollback

- Revert `scripts/harness_feedback.py`, edits to report/recover/test/docs/DHF skill, and runtime sync.
- Re-run `./scripts/sync_codex_home.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --skip-superpowers-sync`.
- Confirm the DHF skill mirror diff is clean.
