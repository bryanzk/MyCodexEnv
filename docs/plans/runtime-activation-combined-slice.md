# Harness Requirements — Runtime Activation Combined Slice

> One ordered slice that closes the three remaining runtime gaps as a single
> causal chain: (1) make `verify_codex_env.sh` content-check the enforcement
> scripts, not just their existence; (2) make the canonical gate reproducibly
> green by turning `codex`-CLI-dependent failures into explicit skips without
> early `set -e` exits; (3) run the runtime sync so the six landed enforcement
> slices go live, and record honest state — with the post-sync `verify` now
> actually proving live == repo.

## Goal

After this slice: a stale or partially-synced `~/.codex` enforcement script is
caught by `verify_codex_env.sh` (not silently passed); `python3 test_runner.py`
produces a deterministic green (or explicit skip) on any machine including those
without the `codex` CLI; and the live runtime in `~/.codex` provably matches the
repo, with `docs/harness-state.md` recording the real verification truth.

## Why one slice, in this order

The three steps are a dependency chain, not independent tasks:

1. **Stage 1 (verify hardening)** must come first. Until `verify` content-checks
   the hook scripts, Stage 3's "the live guard matches the repo" claim is
   unprovable — you would be trusting `rsync`, not verifying it.
2. **Stage 2 (reproducible green)** comes next so the Stage 3 verification run,
   and any future CI, yields a clean pass/skip instead of an environment-driven
   red that hides real signal.
3. **Stage 3 (sync + state truth)** comes last and is the only stage that mutates
   `~/.codex`. It consumes the stronger gate built in Stages 1–2 to self-verify.

Stages 1 and 2 are `local_dev` and can land now. Stage 3 is gated (see Execution
Lane) and may be deferred without blocking Stages 1–2.

## Audience

- Operator who needs the built guardrails to actually run, and to trust that the
  running guard is current.
- CI or any second machine that must reproduce the green gate.

## Scope

- Stage 1: `scripts/verify_codex_env.sh` — add `cmp -s` runtime-match checks for
  each hook script (`harness_guard.py`, `harness_observer.py`, `model_router.py`,
  `session_start_require_naming.py`, `shipq_dhf_preprompt.py`) and the two split
  evidence schemas (`decision-evidence.schema.json`,
  `routine-gate-receipt.schema.json`). The exact new check names are
  `codex_hook_session_start_runtime_matches_source`,
  `codex_hook_harness_guard_runtime_matches_source`,
  `codex_hook_harness_observer_runtime_matches_source`,
  `codex_hook_model_router_runtime_matches_source`,
  `codex_hook_shipq_dhf_preprompt_runtime_matches_source`,
  `codex_runtime_decision_evidence_schema_matches_source`, and
  `codex_runtime_routine_gate_receipt_schema_matches_source`. `test_runner.py` —
  a test asserting verify fails with the named hook mismatch when a synced script
  is mutated.
- Stage 2: `test_runner.py` (`run_all`/`TestRunResult` and the
  `test_verify_after_full_sync` path) — detect a missing `codex` CLI and emit an
  explicit `[SKIP]` with a recorded reason and a `skipped` count, instead of a
  hard failure. Also harden `scripts/verify_codex_env.sh` so `codex_version` and
  `codex login status` are guarded by the `cmd_codex` result and cannot abort the
  script before the PASS/FAIL/SKIP summary is printed.
- Stage 3: run `scripts/sync_codex_home.sh` then `scripts/verify_codex_env.sh`;
  append an honest `docs/harness-state.md` checkpoint via
  `scripts/harness_checkpoint.py`. No code change beyond the state append. The
  sync is the repo-managed runtime activation path, not a narrow hook copy: it may
  update rendered config, managed skills, workflow files, global AGENTS/remote
  docs, hook config, hook scripts, runtime files, and zsh helpers.
- Docs: `docs/AGENT_HARNESS_STATUS.md` Guardrails/Observability rows note that
  verify now content-checks enforcement scripts and the gate is skip-safe.

## Non-Goals

- Auto-running the sync without approval (Stage 3 stays human-gated).
- Changing guard/observer/router behavior (those landed; this slice only verifies
  and activates them).
- Building a full CI pipeline (Stage 2 only makes the suite CI-ready, it does not
  add CI config).
- Reviving the freeze-review skill-governance workstream (separate, optional).

## Constraints

- Bash + Python standard library only; reuse existing `check` helper in
  `verify_codex_env.sh` and `run_all` in `test_runner.py`.
- Stage 3 writes to the operator's real `~/.codex`; it is idempotent repo-managed
  sync followed immediately by the strengthened `verify`. Never commit
  `~/.codex` contents or local evidence.
- Preserve append-only `docs/harness-state.md`.
- A skip must be explicit and counted; a skipped check must never be reported as a
  pass (silent skip is the same failure class as silent failure).

## Task Demand (D_task)

- estimated_level: medium
- L (reasoning/action steps): about 9 — add seven verify checks, one mutation
  test, the skip path plus skipped-count in the runner, the env-detection for the
  verify test, run sync, run strengthened verify, append checkpoint, update one
  docs row.
- H_tool (tool-selection ambiguity): low — known scripts (`verify_codex_env.sh`,
  `sync_codex_home.sh`, `test_runner.py`, `harness_checkpoint.py`); the only
  judgement is where to gate Stage 3.
- S_state (cross-module state tracking): medium — verify, the runner, the sync,
  and the state log must agree on what "live == repo" and "green" mean; Stage 3
  couples repo state to `~/.codex`.
- N_obs (observation/external noise): medium — Stage 2 reasons about environments
  with and without the `codex` CLI; Stage 3 observes real sync/verify output.

## Execution Lane

- Stage 1, Stage 2: `local_dev`. No external systems; tests use temp homes.
- Stage 3: `operator_live_demo`. Mutates the operator's own `~/.codex` via
  idempotent repo-managed sync; local, no production or customer authority.
  Forbidden: any mutation outside `~/.codex`, secret reads, remote ops. **Gate to
  run Stage 3: explicit operator approval for this runtime activation.** Stages
  1–2 may land and ship without it.

## Source Of Truth

- `scripts/verify_codex_env.sh` (existing `check` helper; existence checks at
  lines ~110-113; content `cmp` checks at lines ~133-139).
- `scripts/sync_codex_home.sh` (repo-managed sync of config template, managed
  skills, workflow, AGENTS/remote docs, hook config, hook scripts, runtime files,
  and zsh helpers; `--skip-superpowers-sync` only skips the superpowers vendor
  sync).
- `test_runner.py` (`run`, `run_with_input`, `run_all`, `TestRunResult`,
  `test_verify_after_full_sync`).
- `codex/hooks/*.py`, `codex/runtime/evidence/*.schema.json`.
- `docs/harness-state.md`, `scripts/harness_checkpoint.py`.

## Stage 1 — First failing test (verify must catch script drift)

```python
def test_verify_detects_enforcement_script_drift():
    # fails today: verify only existence-checks the hook scripts, so a mutated
    # ~/.codex/hooks/harness_guard.py still passes verify.
    if run(["bash", "-lc", "command -v codex"])[0] != 0:
        raise SkipTest("verify drift test requires codex CLI until verify is skip-safe")
    with tempfile.TemporaryDirectory() as tmp:
        codex_home = Path(tmp) / ".codex"
        claude_home = Path(tmp) / ".claude"
        # full sync into the temp home so it starts matching the repo
        run([str(SYNC), "--repo-root", str(ROOT), "--codex-home", str(codex_home), "--skip-superpowers-sync"])
        run([str(SYNC_CLAUDE), "--repo-root", str(ROOT), "--claude-home", str(claude_home)])
        ok, _, _ = run([str(VERIFY), "--repo-root", str(ROOT), "--codex-home", str(codex_home),
                        "--claude-home", str(claude_home), "--skip-check", "app_google_chrome"])
        require(ok == 0, "freshly synced runtime should verify clean")
        # mutate the live guard; verify must now FAIL on content mismatch
        (codex_home / "hooks" / "harness_guard.py").write_text("# drifted\n", encoding="utf-8")
        bad, out, err = run([str(VERIFY), "--repo-root", str(ROOT), "--codex-home", str(codex_home),
                             "--claude-home", str(claude_home), "--skip-check", "app_google_chrome"])
        require(bad != 0, "verify must fail when a live enforcement script no longer matches the repo")
        require("FAIL:codex_hook_harness_guard_runtime_matches_source" in f"{out}\n{err}",
                "verify must fail on the named hook content mismatch, not an unrelated check")
    print("[PASS] verify detects enforcement script drift")
```

Stage 1 implementation: in `verify_codex_env.sh`, alongside the existing
`*_runtime_matches_source` block, add one `cmp -s` check per hook script and per
split evidence schema (repo `codex/...` vs `${CODEX_HOME}/...`).

## Stage 2 — First failing test (gate is reproducibly green/skip)

```python
def test_runner_reports_skips_distinctly():
    from test_runner import run_all
    def good(): pass
    def skipper(): raise SkipTest("codex CLI unavailable")   # new lightweight signal
    res = run_all([good, skipper])
    require(res.passed == 1 and res.skipped == 1 and res.failed == 0,
            "an environment-skipped check must count as skip, not pass or fail")
    print("[PASS] runner reports skips distinctly")
```

Stage 2 implementation: add a tiny `SkipTest` exception and a `skipped` list to
`run_all`/`TestRunResult`; print `[SKIP] <name>: <reason>` and a
`ran=.. passed=.. skipped=.. failed=..` summary. Change
`test_verify_after_full_sync` (and any codex-CLI-dependent check) to
`raise SkipTest("codex CLI not installed")` when `command -v codex` fails, instead
of failing. Exit non-zero only on real failures; skips do not break green.
Existing ad hoc tests that currently print `[SKIP]` and return are not counted by
this change unless they are explicitly converted to `SkipTest`; this slice must at
least migrate the `codex`-CLI-dependent full-sync verify test.

Stage 2 must also fix `verify_codex_env.sh` itself: today it directly evaluates
`codex_version="$(codex --version | awk '{print $2}')"` under `set -e`, so a
machine without `codex` exits before normal reporting. Replace that with guarded
logic:

- if `cmd_codex` is skipped, append `SKIP:codex_version`, set
  `codex_version="unavailable"`, and skip `codex login status`;
- if `cmd_codex` fails and is not skipped, append `FAIL:cmd_codex`,
  `FAIL:codex_version`, set `codex_version="unavailable"`, and still print the
  full summary;
- if `cmd_codex` passes, run `codex --version` and the login-status probe inside
  conditionals that cannot abort the script before results are printed.

## Stage 3 — Activation (gated; run only with approval)

```bash
# 1. ensure Stages 1-2 are green
git status --short --branch
python3 test_runner.py            # expect: ran=.. passed=.. skipped>=0 failed=0

# 2. capture pre-activation truth; this may expose that live runtime is stale
./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome || true

# 3. sync repo -> live runtime (operator approval required)
./scripts/sync_codex_home.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --skip-superpowers-sync

# 4. the now-stronger verify proves live == repo, scripts included
./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome

# 5. record the truth
python3 scripts/harness_checkpoint.py append --phase handoff \
  --summary "runtime activated: verify now content-checks enforcement scripts; ~/.codex synced and matches repo" \
  --changed-surface "scripts/verify_codex_env.sh" \
  --verification-command "./scripts/verify_codex_env.sh ..." \
  --verification-exit-code 0 --verification-key-output "Verification passed." \
  --next-safe-task "<next priority>"
```

## Acceptance Criteria

- [ ] Stage 1: `verify_codex_env.sh` content-checks all five hook scripts and both
      split evidence schemas; `test_verify_detects_enforcement_script_drift`
      passes (verify fails on a mutated live guard with
      `FAIL:codex_hook_harness_guard_runtime_matches_source`).
- [ ] Stage 2: `run_all`/`TestRunResult` support an explicit skip with a reason and
      a `skipped` count; `test_verify_after_full_sync` skips (not fails) when the
      `codex` CLI is absent; the suite is green on a machine without `codex`
      (`failed=0`, `skipped>=1`).
- [ ] `verify_codex_env.sh` never exits early from `codex --version` or
      `codex login status`; missing `codex` becomes reported FAIL/SKIP evidence
      with `codex_version="unavailable"`.
- [ ] A skipped check is never reported as a pass; the summary line shows
      `ran/passed/skipped/failed`.
- [ ] Stage 3 (when approved): `sync_codex_home.sh` runs; the strengthened
      `verify` exits 0 and now genuinely proves the live enforcement scripts match
      the repo; `docs/harness-state.md` records the exact sync command and real
      verification line.
- [ ] `python3 scripts/harness_requirements.py validate docs/plans/runtime-activation-combined-slice.md` passes.
- [ ] `python3 test_runner.py` green; `git diff --check` clean; no `~/.codex`
      content committed.

## Verification Gate

- Stage 1 focused: `python3 -c "import test_runner as t; t.test_verify_detects_enforcement_script_drift()"`
- Stage 2 focused: `python3 -c "import test_runner as t; t.test_runner_reports_skips_distinctly()"`
- Full: `python3 test_runner.py`
- Stage 3 (gated): `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome`
- Formatting: `git diff --check`
- Requirements: `python3 scripts/harness_requirements.py validate docs/plans/runtime-activation-combined-slice.md`

## Exception / Failure Modes

- `codex` CLI absent → Stage 1 drift test and Stage 2 verify check both SKIP with
  a reason once `SkipTest` exists; they never count as pass or fail. The verify
  script itself must still print a full summary and must not terminate at
  `codex --version`.
- `cmp` target missing in `~/.codex` (never synced) → existing existence checks
  already fail; the new content checks add the "exists but stale" case.
- `sync_codex_home.sh` partial failure → strengthened `verify` now catches the
  resulting script mismatch instead of passing; do not record green until verify
  is clean.
- `sync_codex_home.sh` has broader blast radius than hooks/runtime → treat Stage
  3 as runtime activation for all repo-managed Codex home surfaces (config,
  skills, workflow, AGENTS/remote docs, hooks, runtime, zsh). Do not describe it
  as a narrow enforcement-script copy.
- Existing manual `print("[SKIP]"); return` tests → remain ad hoc until converted
  to `SkipTest`; do not count them in `skipped` unless migrated.
- Stage 3 run without approval → not permitted; Stages 1-2 still ship.
- Checkpoint append with no real green → use `--allow-unverified` handoff with an
  explicit blocker; never fabricate a green verification line.

## Risks

- **Stage 3 touches the operator home.** Idempotent rsync, immediately verified;
  reversible by re-sync from repo or by restoring script-created backups for the
  files that the sync script backs up explicitly. Gated behind explicit approval.
- **Skip could hide a real regression** if over-applied. Mitigation: skip only on
  a specific, detected missing external tool (`command -v codex`), never on an
  assertion failure; keep the skip reason in the output.
- **`set -e` can erase evidence** if future direct shell probes are added outside
  `check`. Mitigation: any direct probe added to `verify_codex_env.sh` must be
  wrapped in conditionals and append PASS/FAIL/SKIP into `results`.
- **Verify content-check false positives** from line-ending or trailing-newline
  differences. Mitigation: `cmp -s` matches the existing config checks' behavior;
  the sync uses `rsync -a`, so bytes match.

## Handoff Notes

- Land Stages 1-2 first as one PR (`local_dev`, fully testable now). Run Stage 3
  only after explicit operator approval for this runtime activation, then append
  the activation checkpoint.
- If implementation starts now, do not run `sync_codex_home.sh` as part of the PR
  unless the operator explicitly approves Stage 3 in that same turn.
- effective_feedback_check: one focused run per stage, one full suite, one gated
  verify; do not re-run a green suite to pad evidence.
- When reporting evidence from any environment, state whether the `codex` CLI was
  available so a skip is not misread as a gap.
