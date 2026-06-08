# Harness Requirements — Agent-Team Dispatch Gate Slice

> Vertical slice plan for Top-3 Task #2: turn `harness_agent_team.py` from an
> advisory validator that an agent may forget to run into a **recorded,
> blocking pre-dispatch gate**, so multi-worker dispatch cannot happen silently
> with overlapping write sets or a worker that claims `docs/harness-state.md`.

## Goal

Two enforced effects:

1. A successful `harness_agent_team.py validate` leaves a durable **decision
   evidence** receipt (plan hash + agent count), so "the plan was validated" is
   an auditable fact, not a claim in chat.
2. The `PreToolUse` guard (`harness_guard.py`) classifies subagent-dispatch tool
   calls as a new `agent_dispatch` category and returns `ask` unless a matching
   fresh validation receipt exists — making silent multi-agent dispatch
   impossible through the one channel the repo actually controls.

## Problem (current behavior, verified)

- `harness_agent_team.py validate` already enforces disjoint worker write sets,
  protected `docs/harness-state.md`, role/demand/green-gate rules — but only if
  someone runs it. Nothing records that it ran; nothing blocks dispatch if it
  did not. `AGENT_HARNESS_STATUS.md` admits the validator is "not yet wired into
  automatic subagent dispatch."
- `harness_guard.py` has **zero** subagent/dispatch awareness (`grep` for
  `agent|dispatch|spawn` returns nothing). Multi-worker dispatch falls through as
  a plain `read`/tool call and is allowed.
- `tool-policy.json` has no dispatch category. So the highest-risk path for
  irreversible state corruption (parallel workers stepping on each other's write
  sets) has no runtime gate at all.

## Desired behavior

1. `harness_agent_team.py validate --emit-evidence` appends one `decision`
   evidence event on success only. The event uses schema-safe top-level fields
   and stores the receipt contract in `metadata`:
   `{event_type:"agent_team_validated", evidence_kind:"decision",
   metadata:{plan_sha256, agent_count, worker_count, repo_root}}`. On validation
   failure it prints errors and writes nothing. On evidence append failure it
   exits non-zero, because "valid plan but no receipt" is not a successful
   pre-dispatch gate.
2. `tool-policy.json` gains `agent_dispatch_tool_names` and
   `agent_dispatch_command_patterns`. `harness_guard.py` classifies a matching
   tool call as category `agent_dispatch`.
3. The guard returns `ask` for `agent_dispatch` in every phase, with a message:
   "validate the worker plan with harness_agent_team.py and re-dispatch." It
   downgrades to allow only when the dispatch payload includes `plan_sha256` and
   a fresh `agent_team_validated` receipt exists in the local evidence dir with:
   matching `metadata.plan_sha256`, matching normalized `metadata.repo_root`,
   optional matching `metadata.worker_count` if the payload supplies it, and a
   timestamp no older than 10 minutes. Missing hash, stale receipt, cross-repo
   receipt, malformed JSONL, or missing evidence dir all stay `ask`.
4. Stay non-blocking on infra errors (missing evidence dir, unreadable policy):
   the guard never crashes; worst case it asks rather than silently allows.

## Audience

- Codex operator dispatching parallel workers.
- The integrating main agent who must own the final `harness-state.md` append.

## Scope

- `scripts/harness_agent_team.py` — add `--emit-evidence` to the `validate`
  subcommand; compute `plan_sha256`; reuse `scripts/harness_evidence.py` append
  path and the `decision` schema.
- `codex/runtime/tool-policy.json` — add `agent_dispatch_tool_names` and
  `agent_dispatch_command_patterns` arrays.
- `codex/hooks/harness_guard.py` — add `agent_dispatch` classification + receipt
  lookup; return `ask`/allow accordingly.
- `scripts/harness_evidence.py` — add `agent_team_validated` to `EVENT_TYPES`
  and `DECISION_EVENT_TYPES` so `evidence_kind=decision` validates.
- `codex/runtime/evidence.schema.json` — add `agent_team_validated` to the
  compatibility event enum.
- `codex/runtime/evidence/decision-evidence.schema.json` — allow the
  `agent_team_validated` event_type.
- `test_runner.py` — new test `test_agent_dispatch_gate()`.
- `docs/HARNESS_RUNTIME.md` + `docs/AGENT_HARNESS_STATUS.md` — update the
  Subagent / Guardrails rows from "advisory" to "recorded + ask-gated", and
  document the honest limit below.
- `docs/repo-index.md` — update the helper/schema surface descriptions if needed
  so the receipt event remains discoverable.

## Non-Goals

- Claiming full automatic enforcement of every subagent path. The guard can only
  intercept dispatch tools whose **names or command patterns are configured**;
  Codex's actual subagent-dispatch tool shape is runtime-owned and not
  repo-controlled. This slice makes the gate real for configured shapes and
  fail-safe (ask) for unknown ones — it does not pretend to force a runtime that
  exposes no dispatch hook.
- Auto-running validation for the operator. Receipt-or-ask, not auto-fix.
- Changing the validation rules themselves (write-set/demand/gate logic already
  correct).

## Constraints

- Python standard library only; reuse existing `harness_evidence.py` append and
  schema rather than adding a JSON-schema dependency.
- Evidence stays local under `~/.codex/harness/evidence`; never commit it.
- Guard must keep exiting 0 with valid JSON on any infra error.
- Preserve the validator's current exit codes and stdout/stderr contract when
  `--emit-evidence` is absent. With `--emit-evidence`, append success becomes
  part of success; append failure returns non-zero and prints a clear error.

## Task Demand (D_task)

- estimated_level: high
- L (reasoning/action steps): ~10 — evidence emit + hashing, policy keys, guard
  category + receipt lookup, helper/schema enum sync, test, docs sync, focused +
  full gates.
- H_tool (tool-selection ambiguity): medium — must reuse the existing evidence
  append path and decision schema correctly rather than inventing a second
  writer; freshness/receipt-matching design has options.
- S_state (cross-module state tracking): high — couples validator output →
  evidence file → guard read; three surfaces must agree on event shape and the
  `plan_sha256` contract, and the guard now reads evidence it previously ignored.
- N_obs (observation/external noise): medium — guard reads a local evidence
  directory whose contents vary; lookup must tolerate legacy/unknown events and
  malformed JSONL lines (the report helper already models this).

## Execution Lane

- `local_dev`. Receipts are local JSONL; no network, no remote, no deploy. The
  test builds a temp `CODEX_HOME` evidence dir.

## Source Of Truth

- `AGENTS.md`, `docs/repo-index.md`, `docs/harness-state.md`
- `docs/HARNESS_RUNTIME.md` (Subagent Contract, Evidence Contract)
- `scripts/harness_agent_team.py`, `scripts/harness_evidence.py`
- `codex/hooks/harness_guard.py`, `codex/runtime/tool-policy.json`
- `codex/runtime/evidence.schema.json`
- `codex/runtime/evidence/decision-evidence.schema.json`

## First Failing Test (write first — must fail on current code)

```python
def test_agent_dispatch_gate():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        codex_home = tmp_path / ".codex"
        (codex_home / "runtime").mkdir(parents=True)
        (codex_home / "runtime" / "tool-policy.json").write_text(
            (ROOT / "codex" / "runtime" / "tool-policy.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["CODEX_HOME"] = str(codex_home)

        # 1) a dispatch-shaped tool call with no validation receipt -> ask
        dispatch_payload = json.dumps({
            "tool_name": "spawn_agent",
            "tool_input": {"plan_sha256": "deadbeef", "worker_count": 1, "cwd": str(tmp_path)},
        })
        code, out, err = run_with_input([sys.executable, str(HARNESS_GUARD)], dispatch_payload, env=env)
        require(code == 0, f"guard dispatch run failed: {err or out}")
        require(
            json.loads(out).get("permissionDecision") == "ask",
            "multi-agent dispatch without a validation receipt must require approval",
        )

        # 2) validate --emit-evidence writes exactly one decision receipt
        plan = tmp_path / "plan.json"
        plan.write_text(json.dumps({"agents": [{
            "id": "w1", "role": "worker", "scope": "edit module a",
            "write_set": ["src/a.py"], "verification_command": "pytest -k a",
            "task_demand": {"level": "low", "L": "2", "H_tool": "low", "S_state": "low", "N_obs": "low"},
            "green_gate": {"gate_scope": "worker", "command": "pytest -k a", "rationale": "touched a"},
        }]}), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(HARNESS_AGENT_TEAM), "validate", str(plan),
             "--repo-root", str(tmp_path), "--emit-evidence"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        code, out, err = proc.returncode, proc.stdout.strip(), proc.stderr.strip()
        require(code == 0, f"validate --emit-evidence failed: {err or out}")
        evdir = codex_home / "harness" / "evidence"
        receipts = list(evdir.glob("*.jsonl")) if evdir.exists() else []
        joined = "\n".join(p.read_text(encoding="utf-8") for p in receipts)
        require("agent_team_validated" in joined, "validate --emit-evidence must append a decision receipt")
        events = [json.loads(line) for line in joined.splitlines() if line.strip()]
        receipt = next((event for event in events if event.get("event_type") == "agent_team_validated"), None)
        require(receipt is not None, "agent_team_validated receipt should be parseable JSON")
        metadata = receipt.get("metadata") or {}
        plan_hash = metadata.get("plan_sha256")
        require(plan_hash, "receipt metadata must include plan_sha256")
        require(metadata.get("worker_count") == 1, "receipt metadata must include worker_count")
        require(Path(metadata.get("repo_root", "")).resolve() == tmp_path.resolve(), "receipt repo_root must match")
        require(receipt.get("command") == "harness_agent_team.py validate", "receipt command should identify validator")
        require(receipt.get("exit_code") == 0, "receipt exit_code should be 0")
        require(receipt.get("key_output") == "agent team valid", "receipt key_output should summarize validation")

        receipt_file = tmp_path / "receipt.json"
        receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
        code, out, err = run([sys.executable, str(HARNESS_EVIDENCE), "validate", str(receipt_file)])
        require(code == 0, f"agent_team_validated receipt must validate through harness_evidence.py: {err or out}")

        # 3) matching fresh receipt -> allow
        allowed_payload = json.dumps({
            "tool_name": "spawn_agent",
            "tool_input": {"plan_sha256": plan_hash, "worker_count": 1, "cwd": str(tmp_path)},
        })
        code, out, err = run_with_input([sys.executable, str(HARNESS_GUARD)], allowed_payload, env=env)
        require(code == 0, f"guard matching receipt run failed: {err or out}")
        require(json.loads(out) == {}, "matching fresh agent_team_validated receipt should allow dispatch")

        mismatch_payload = json.dumps({
            "tool_name": "spawn_agent",
            "tool_input": {"plan_sha256": plan_hash, "worker_count": 2, "cwd": str(tmp_path)},
        })
        code, out, err = run_with_input([sys.executable, str(HARNESS_GUARD)], mismatch_payload, env=env)
        require(code == 0, f"guard worker-count mismatch run failed: {err or out}")
        require(json.loads(out).get("permissionDecision") == "ask", "worker-count mismatch must ask")

        cross_repo = dict(receipt)
        cross_repo["metadata"] = dict(metadata)
        cross_repo["metadata"]["plan_sha256"] = "crossrepohash"
        cross_repo["metadata"]["repo_root"] = str(tmp_path / "other-repo")
        (evdir / "cross-repo.jsonl").write_text(json.dumps(cross_repo) + "\n", encoding="utf-8")
        cross_repo_payload = json.dumps({
            "tool_name": "spawn_agent",
            "tool_input": {"plan_sha256": "crossrepohash", "worker_count": 1, "cwd": str(tmp_path)},
        })
        code, out, err = run_with_input([sys.executable, str(HARNESS_GUARD)], cross_repo_payload, env=env)
        require(code == 0, f"guard cross-repo receipt run failed: {err or out}")
        require(json.loads(out).get("permissionDecision") == "ask", "cross-repo receipt must ask")

        # 4) no hash, stale receipt, cross-repo receipt, or malformed JSONL -> ask
        missing_hash_payload = json.dumps({"tool_name": "spawn_agent", "tool_input": {"cwd": str(tmp_path)}})
        code, out, err = run_with_input([sys.executable, str(HARNESS_GUARD)], missing_hash_payload, env=env)
        require(code == 0, f"guard missing-hash run failed: {err or out}")
        require(json.loads(out).get("permissionDecision") == "ask", "dispatch without plan_sha256 must ask")

        stale = dict(receipt)
        stale["timestamp"] = "2000-01-01T00:00:00-00:00"
        stale["metadata"] = dict(metadata)
        stale["metadata"]["plan_sha256"] = "stalehash"
        (evdir / "stale.jsonl").write_text(json.dumps(stale) + "\n", encoding="utf-8")
        stale_payload = json.dumps({
            "tool_name": "spawn_agent",
            "tool_input": {"plan_sha256": "stalehash", "worker_count": 1, "cwd": str(tmp_path)},
        })
        code, out, err = run_with_input([sys.executable, str(HARNESS_GUARD)], stale_payload, env=env)
        require(code == 0, f"guard stale receipt run failed: {err or out}")
        require(json.loads(out).get("permissionDecision") == "ask", "stale receipt must ask")

    print("[PASS] agent dispatch gate")
```

Use existing `run()` / `run_with_input()` helpers where they fit. For the
`--emit-evidence` call, use `subprocess.run(..., env=env)` directly unless the
test helper has been extended to support env.

## Implementation Sketch

`tool-policy.json`:

```jsonc
"agent_dispatch_tool_names": ["spawn_agent", "multi_agent_v1.spawn_agent", "dispatch_agents", "dispatch_agent", "spawn_agents", "task_team"],
"agent_dispatch_command_patterns": ["\\bharness_agent_team\\.py\\b.*\\bdispatch\\b"]
```

`harness_guard.py` `classify()` — add **before** the `repo_write` branch:

```python
names = set(policy.get("agent_dispatch_tool_names", []))
if name in names or match_any(policy.get("agent_dispatch_command_patterns", []), cmd):
    return "agent_dispatch", "multi-agent dispatch"
```

`decision()` — handle the new category:

```python
if category == "agent_dispatch":
    if has_fresh_validation_receipt(payload, policy):   # matches plan_sha256 in evidence
        return {}
    return {"permissionDecision": "ask",
            "message": "[harness] validate the worker plan with "
                       "scripts/harness_agent_team.py validate --emit-evidence before dispatch."}
```

`harness_agent_team.py` — on `cmd_validate` success with `--emit-evidence`,
compute `hashlib.sha256(canonical_plan_bytes).hexdigest()` using canonical JSON
bytes (`sort_keys=True`, compact separators), print `plan_sha256: ...`, and call
the existing evidence append (decision kind) with
`event_type="agent_team_validated"` and metadata containing `plan_sha256`,
`agent_count`, `worker_count`, and normalized `repo_root`.

Pin the receipt top-level verification fields so it validates through the normal
`scripts/harness_evidence.py` append/validate path, not a bespoke JSONL writer:
`command="harness_agent_team.py validate"`, `exit_code=0`,
`key_output="agent team valid"`, `phase="handoff"` or `"unknown"` if no phase is
available, plus the helper-generated `timestamp`.

Schema/helper updates are part of the same green step:

- add `agent_team_validated` to `scripts/harness_evidence.py` `EVENT_TYPES` and
  `DECISION_EVENT_TYPES`;
- add it to `codex/runtime/evidence.schema.json` and
  `codex/runtime/evidence/decision-evidence.schema.json`;
- keep `plan_sha256`, counts, and `repo_root` inside `metadata` rather than as
  top-level fields, because the decision schema has `additionalProperties:false`.

## Acceptance Criteria

- [ ] `test_agent_dispatch_gate()` added, registered, **fails on current `main`**
      (guard returns `{}` for dispatch today), passes after.
- [ ] Dispatch-shaped tool call with no fresh receipt → `ask`.
- [ ] `validate --emit-evidence` writes exactly one `decision` event with
      `event_type=agent_team_validated` and `metadata.plan_sha256`; failed
      validation writes nothing.
- [ ] The receipt validates through `scripts/harness_evidence.py validate` and
      carries top-level `command`, `exit_code`, `key_output`, `timestamp`, and
      `phase` fields compatible with the normal append path.
- [ ] Evidence append failure under `--emit-evidence` exits non-zero and writes
      no fabricated receipt.
- [ ] A dispatch payload carrying `plan_sha256` + matching repo root and optional
      worker count that matches a receipt newer than 10 minutes → allowed (`{}`).
- [ ] Dispatch with missing hash, stale receipt, cross-repo receipt, worker-count
      mismatch, missing evidence dir, or malformed JSONL → `ask`.
- [ ] The focused test includes at least stale-receipt and worker-count-mismatch
      cases so a receipt lookup that ignores timestamp or worker identity fails.
- [ ] Existing `test_harness_guard_policy_decisions()` and agent-team validator
      tests still pass; default (no `--emit-evidence`) behavior unchanged.
- [ ] Guard exits 0 with valid JSON when the evidence dir is missing or contains
      malformed JSONL.
- [ ] Docs updated; the honest limit (only configured dispatch shapes are
      intercepted) is stated in `HARNESS_RUNTIME.md` and the STATUS Remaining-Gap
      column.
- [ ] Docs sync decision is explicit: `docs/repo-index.md` is updated for new
      helper/schema semantics if needed; `docs/CODEX_ENV_REPRODUCTION.md` is
      unchanged unless a sync command or runtime install step changes.
- [ ] RED/GREEN evidence is captured for the focused test with `command`,
      `exit_code`, `key_output`, and `timestamp`.
- [ ] `python3 test_runner.py` → `[PASS] all tests`; `git diff --check` clean.

## Verification Gate

- Focused: `python3 -c "import test_runner as t; t.test_agent_dispatch_gate()"`
- Full: `python3 test_runner.py`
- Formatting: `git diff --check`
- Sync: `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome`

## Exception / Failure Modes

- Missing evidence dir → `has_fresh_validation_receipt` returns False → `ask`
  (fail-safe, not fail-open). No crash.
- Malformed JSONL receipt line → skip line, continue (mirror `harness_report.py`
  tolerance).
- Unknown dispatch tool shape (name/pattern not configured) → not classified as
  `agent_dispatch`; documented limit, not a silent bypass claim.
- Validation failure with `--emit-evidence` → non-zero exit, no receipt written.
- Evidence append failure with `--emit-evidence` → non-zero exit; print a clear
  error and do not fabricate a receipt.
- Receipt older than 10 minutes, missing `metadata.plan_sha256`, or mismatched
  `metadata.repo_root` → skip receipt and keep dispatch at `ask`.

## Risks

- **Receipt-matching design:** if freshness is keyed only on `plan_sha256`, a
  stale-but-matching receipt could re-authorize an old plan. Mitigation: include
  a timestamp window and record it in the docs contract; start strict (short
  window) and loosen only with evidence.
- **Runtime shape unknown:** if Codex never surfaces a dispatch tool call to
  `PreToolUse`, the gate is inert for that path. Mitigation: keep the recorded
  receipt (effect #1) valuable on its own, and state the limit honestly rather
  than over-claiming enforcement.

## Handoff Notes

Append after the slice lands:

- `scripts/harness_checkpoint.py append --phase development --summary "agent-team
  validation now emits decision receipt; guard ask-gates configured dispatch
  shapes" ...` with fresh `test_runner.py` evidence and dirty-state
  classification (agent_owned: validator + guard + policy + schema + test + 2
  docs).
- Next safe task: Task #3 (runtime surfaces single-source manifest).
- effective_feedback_check: focused gate once, full gate once; flag any repeated
  green run as low_conversion.
