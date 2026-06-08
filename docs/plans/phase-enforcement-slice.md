# Harness Requirements — Phase Enforcement Slice

> Vertical slice plan for Top-3 Task #1: make the phase-aware tool-policy
> guardrail actually enforced at runtime, instead of silently degrading to
> `development` (writes-allowed) whenever the hook payload carries no phase.

## Goal

`codex/hooks/harness_guard.py` must resolve the **real** lifecycle phase before
applying `tool-policy.json`, so that read-only phases (`research`,
`requirements`, `planning`, `validation`, `review`) block or `ask` on repo
writes during normal Codex sessions where the hook payload has no `phase` field
and no `CODEX_HARNESS_PHASE` is exported. The same slice also aligns `handoff`
with the documented "docs/state only" contract by making repo writes ask-gated,
because the current policy can only allow/ask/deny by category, not by path.

## Problem (current behavior, verified)

`current_phase()` resolves in this order:

```
payload.phase  →  tool_input.phase  →  $CODEX_HARNESS_PHASE  →  policy.default_phase("development")  →  "development"
```

- Codex `PreToolUse` payloads do not carry `phase`.
- `CODEX_HARNESS_PHASE` is **read** by `harness_guard.py` / `harness_observer.py`
  but **set by nobody** in the repo (only `test_runner.py` sets it for tests).
- Therefore real sessions fall through to `default_phase: "development"`, which
  has `allow_repo_write: true`. The entire read-only matrix in `tool-policy.json`
  is inert at runtime; only category hard-blocks (secret / destructive /
  dynamic_exec / remote) still fire.
- `tool-policy.json` already declares `"unknown_phase_behavior": "read_only"`,
  but `current_phase()` never consults it.
- `docs/harness-state.md` currently snapshots `phase: handoff`, while
  `tool-policy.json` currently sets `handoff.allow_repo_write=true`. If the guard
  starts trusting the snapshot without changing policy, any repo write during a
  handoff snapshot would be silently allowed, contradicting the
  `docs/HARNESS_RUNTIME.md` "handoff = docs/state only" row.

## Desired behavior

1. When payload/`tool_input`/env give no phase, resolve phase from the durable
   state snapshot: the `phase:` field under `## Current Snapshot` in
   `docs/harness-state.md` (located via `git rev-parse --show-toplevel`, which
   the guard already computes for write-scope checks).
2. When no phase can be resolved from payload, env, or state snapshot, apply
   `unknown_phase_behavior` (`read_only`) instead of `default_phase`
   (`development`). Read-only means: `repo_write` → `ask`, `network` → `ask`.
3. Keep the explicit channels authoritative and ordered:
   `payload.phase → tool_input.phase → $CODEX_HARNESS_PHASE → state snapshot → unknown_phase_behavior`.
   `default_phase` is demoted to "only used if the policy author opts in", not the
   silent catch-all.
4. Stay non-blocking and dependency-free (stdlib only); never raise on a missing
   or malformed state file — fall back to `unknown_phase_behavior`.
5. Change the `handoff` phase policy to `allow_repo_write: false` and include
   `repo_write` in `require_approval`. This preserves docs/state handoff writes
   through explicit approval while preventing the snapshot-derived `handoff`
   phase from becoming a broad write bypass.

## Audience

- Codex operator running real (non-test) sessions.
- Future agent resuming this repo and trusting the phase guardrail.

## Scope

- `codex/hooks/harness_guard.py` — `current_phase()` resolution chain + a new
  `phase_from_state_snapshot(git_root)` helper.
- `codex/runtime/tool-policy.json` — align `handoff` with the docs/state-only
  contract by ask-gating repo writes.
- `test_runner.py` — new test `test_harness_guard_phase_resolution()`.
- `docs/HARNESS_RUNTIME.md` + `docs/AGENT_HARNESS_STATUS.md` — update the
  Permissions / Tool Router rows to state that phase is resolved from state
  snapshot and that the unknown fallback is read-only.
- `docs/repo-index.md` — update the Runtime Surfaces note for `tool-policy.json`
  only if the description needs the snapshot/unknown fallback made discoverable.

## Non-Goals

- Forcing Codex to emit a `phase` field (runtime-owned, out of repo control).
- Changing `model_router.py` or `harness_observer.py` phase logic (observer is
  non-enforcing; can adopt the same helper in a later slice).
- Adding any new dependency or daemon. No auto-commit.

## Constraints

- Python standard library only.
- Preserve append-only `docs/harness-state.md`; the guard only **reads** it.
- The hook must keep exiting 0 and emit valid JSON even when state is missing or
  malformed (observability/guard must not crash tool intake).
- Do not commit local evidence, credentials, or auth files.
- Keep `PreToolUse` overhead bounded: compute the repo root once per hook payload
  and pass it into phase resolution and any write-scope checks rather than
  shelling out to `git rev-parse` multiple times.

## Task Demand (D_task)

- estimated_level: medium
- L (reasoning/action steps): ~7 — add snapshot parser, reorder resolution,
  wire `unknown_phase_behavior`, ask-gate `handoff` repo writes, write test,
  update docs, run gates.
- H_tool (tool-selection ambiguity): low — hook, policy, and test files are
  obvious; no new dependency or runtime daemon.
- S_state (cross-module state tracking): medium — guard now depends on the
  `harness-state.md` snapshot **format**; the parser must tolerate format drift
  and the docs contract must record the new coupling.
- N_obs (observation/external noise): low — deterministic, fully covered by a
  temp-dir unit test; no network or external systems.

## Execution Lane

- `local_dev`. No live external calls, no secret reads, no remote mutation, no
  deploy. Fixtures are temp dirs created by the test.

## Source Of Truth

- `AGENTS.md`
- `docs/repo-index.md`
- `docs/harness-state.md` (snapshot format being consumed)
- `docs/HARNESS_RUNTIME.md` (Permissions / Tool Router contract)
- `codex/runtime/tool-policy.json` (`default_phase`, `unknown_phase_behavior`,
  per-phase `allow_repo_write`, `handoff.require_approval`)
- `codex/hooks/harness_guard.py` (`current_phase`, `decision`, `git_root`)

## First Failing Test (write this first — it must fail on current code)

Add to `test_runner.py`, register it in the runner list, and run it before any
guard edit. It fails today because, with no phase signal, the guard returns `{}`
(development, write allowed) instead of `ask`.

```python
def test_harness_guard_phase_resolution():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        git_probe = subprocess.run(["git", "--version"], capture_output=True, text=True, check=False)
        if git_probe.returncode != 0:
            print("[SKIP] harness guard phase resolution requires git for snapshot repo setup")
            return
        # runtime policy
        runtime_dir = tmp_path / ".codex" / "runtime"
        runtime_dir.mkdir(parents=True)
        (runtime_dir / "tool-policy.json").write_text(
            (ROOT / "codex" / "runtime" / "tool-policy.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        # a git repo whose state snapshot says we are in a read-only phase
        repo = tmp_path / "repo"
        (repo / "docs").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "docs" / "harness-state.md").write_text(
            "# Harness State\n\n## Current Snapshot\n- phase: planning\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["CODEX_HOME"] = str(tmp_path / ".codex")
        env.pop("CODEX_HARNESS_PHASE", None)  # no env phase

        write_payload = json.dumps({
            "tool_name": "apply_patch",
            "tool_input": {"file_path": str(repo / "docs" / "x.md"), "cwd": str(repo)},
        })
        code, out, err = run_with_input([sys.executable, str(HARNESS_GUARD)], write_payload, env=env)
        require(code == 0, f"guard phase-resolution run failed: {err or out}")
        require(
            json.loads(out).get("permissionDecision") == "ask",
            "write during snapshot phase=planning must require approval, not silently pass as development",
        )

        # no snapshot phase anywhere -> unknown_phase_behavior=read_only, not development
        (repo / "docs" / "harness-state.md").write_text("# Harness State\n", encoding="utf-8")
        code, out, err = run_with_input([sys.executable, str(HARNESS_GUARD)], write_payload, env=env)
        require(code == 0, f"guard unknown-phase run failed: {err or out}")
        require(
            json.loads(out).get("permissionDecision") == "ask",
            "write with no resolvable phase must fall back to read_only, not development",
        )

        # snapshot handoff is docs/state-only, so the guard must not broad-allow writes
        (repo / "docs" / "harness-state.md").write_text(
            "# Harness State\n\n## Current Snapshot\n- phase: handoff\n",
            encoding="utf-8",
        )
        code, out, err = run_with_input([sys.executable, str(HARNESS_GUARD)], write_payload, env=env)
        require(code == 0, f"guard handoff-phase run failed: {err or out}")
        require(
            json.loads(out).get("permissionDecision") == "ask",
            "write during snapshot phase=handoff must require approval because handoff is docs/state-only",
        )

    print("[PASS] harness guard phase resolution")
```

## Implementation Sketch (after the test is red)

In `codex/hooks/harness_guard.py`:

```python
import re

def phase_from_state_snapshot(root: Path | None) -> str | None:
    if root is None:
        return None
    state = root / "docs" / "harness-state.md"
    try:
        text = state.read_text(encoding="utf-8")
    except OSError:
        return None
    in_snapshot = False
    for line in text.splitlines():
        if line.strip().lower().startswith("## current snapshot"):
            in_snapshot = True
            continue
        if in_snapshot:
            if line.startswith("## "):
                break
            m = re.match(r"\s*-\s*phase:\s*([A-Za-z_]+)\s*$", line)
            if m:
                return m.group(1)
    return None

def current_phase(payload, policy, root: Path | None) -> str:
    snapshot_phase = phase_from_state_snapshot(root)
    value = (
        payload.get("phase")
        or tool_input(payload).get("phase")
        or os.environ.get("CODEX_HARNESS_PHASE")
        or snapshot_phase
        or "unknown"          # was: policy.get("default_phase") or "development"
    )
    phase = str(value)
    if phase in policy.get("phases", {}):
        return phase
    # honor unknown_phase_behavior instead of defaulting to a writable phase
    return "unknown"
```

In the final implementation, compute `root = git_root(cwd)` once in `decision()`
or an adjacent helper, then pass it to `current_phase(payload, policy, root)` and
any write-scope helper that needs repo root. Avoid a second `git rev-parse` for
the same hook payload.

The existing `phase_policy is None` branch (already a read-only-ish default)
handles `"unknown"`; make it explicitly map `unknown_phase_behavior ==
"read_only"` to `repo_write/network → ask`. Keep the secret / destructive /
dynamic_exec / remote category blocks unchanged.

In `codex/runtime/tool-policy.json`, change the `handoff` phase to:

```json
"allow_repo_write": false,
"require_approval": ["repo_write", "network", "remote", "secret", "destructive", "dynamic_exec"]
```

Do not add path-scoped writes in this slice. If future work needs automatic
docs/state-only handoff writes, add a separate path-scope policy contract and
tests instead of broadening this phase back to allow-all writes.

## Acceptance Criteria

- [ ] `test_harness_guard_phase_resolution()` is added, registered, and **fails
      on current `main`** before the guard change, **passes** after.
- [ ] With no payload/env phase and a `harness-state.md` snapshot of `planning`,
      an `apply_patch`/write returns `permissionDecision: "ask"`.
- [ ] With no resolvable phase anywhere, a write falls back to read-only
      (`ask`), never silently allowed as `development`.
- [ ] With snapshot `phase=handoff`, repo writes return `ask`; the policy no
      longer broad-allows repo writes in handoff.
- [ ] Existing `test_harness_guard_policy_decisions()` still passes (env-var and
      explicit-payload channels remain authoritative and ordered ahead of the
      snapshot).
- [ ] Guard still exits 0 and emits valid JSON when `harness-state.md` is
      missing, empty, or malformed.
- [ ] `git_root` is computed once per hook payload and reused by phase
      resolution / write-scope checks.
- [ ] The focused test confirms `git` is available before creating a temp repo;
      if `git` is unavailable, it skips the snapshot-specific assertions and the
      documented `git unavailable → unknown` path remains covered separately.
- [ ] `docs/HARNESS_RUNTIME.md` and `docs/AGENT_HARNESS_STATUS.md` describe the
      new resolution order and the read-only unknown fallback.
- [ ] Docs sync decision is explicit: `docs/repo-index.md` is updated if the
      `tool-policy.json` description needs the new snapshot/unknown fallback;
      `docs/CODEX_ENV_REPRODUCTION.md` is unchanged unless a command or sync
      entrypoint changes.
- [ ] RED/GREEN evidence is captured for the focused test with `command`,
      `exit_code`, `key_output`, and `timestamp`.
- [ ] `python3 test_runner.py` → `[PASS] all tests`; `git diff --check` clean.

## Verification Gate

- Focused (green gate, run first): the new test in isolation —
  `python3 -c "import test_runner as t; t.test_harness_guard_phase_resolution()"`
- Full (slice gate): `python3 test_runner.py`
- Formatting: `git diff --check`
- Runtime sync (confirms the edited hook copies into `~/.codex/hooks/`):
  `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome`

## Exception / Failure Modes

- Missing `harness-state.md` → `phase_from_state_snapshot` returns `None`; resolve
  to `unknown` → read-only `ask`. No crash.
- Malformed snapshot / no `phase:` line → `None` → `unknown`. No crash.
- `git rev-parse` unavailable (not a repo) → `git_root` returns `None` →
  snapshot skipped → `unknown`. No crash.
- Phase value not in policy `phases` → `unknown`, not a guessed writable phase.
- Snapshot `phase=handoff` → repo writes require approval because handoff has no
  path-scoped write policy in this slice.
- Guard must never raise on malformed state; observability/guard cannot block
  tool intake.

## Risks

- **Snapshot-format coupling:** the guard now depends on the
  `## Current Snapshot` + `- phase:` shape of `harness-state.md`. Mitigation: the
  parser is tolerant (returns `None` on any deviation and degrades to read-only,
  the safe direction), and the docs contract records the coupling so future
  format edits keep the field.
- **Behavior change for operators** who relied on the implicit
  development-writable default. This is the intended fix; call it out in the
  state-log handoff entry.

## Handoff Notes

Append after the slice lands, not now:

- `scripts/harness_checkpoint.py append --phase development --summary "guard
  resolves phase from state snapshot; unknown falls back read-only" ...`
- Record fresh `python3 test_runner.py` evidence (command, exit_code, key_output,
  timestamp), dirty-state classification (agent_owned: guard + test + 2 docs),
  and next safe task (Task #2: make `harness_agent_team.py` a hard dispatch
  gate).
- effective_feedback_check: run the focused gate once (informative), then the
  full gate once (valid, non-redundant); do not re-run an already-green full
  suite — flag any repeat as low_conversion.
