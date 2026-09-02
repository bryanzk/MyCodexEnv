# T001: Final Plan Validation

Task: `T001`
Kind: `judge`
Status: `current`

## Decision

The final two-package plan is executable. Activate `T002` for WP1 source work. GoalBuddy control files are a separately authorized PM surface and must be excluded from WP1/WP2 implementation allowlist counts.

## Current Baseline

- MyCodexEnv branch: `main...origin/main`; no pre-existing product/runtime diff was observed before GoalBuddy files were created.
- Global AGENTS: 87 lines / 7905 bytes.
- Identity status: A/B/C/D fresh.
- External gstack: `/Users/kezheng/.gstack/repos/gstack`, clean `main...origin/main`, HEAD `702a1a9b698080aca72503f5feed9ed8cd552348`, VERSION `1.78.0.0`.
- External inventory: 54 generated skill names; runtime flat topology is 19 correct symlinks plus 34 official generated real directories; root `gstack` is a separate sidecar.
- Shared mutation lock already exists as `${CODEX_HOME}/.phase0-sync.lock` using non-blocking `fcntl.flock`; WP1 must reuse it.

## WP1 Worker Contract

Allowed implementation files are exactly the ten paths on `T002.allowed_files`. GoalBuddy files remain PM-owned and are not Worker implementation files.

Required test-first seams in `test_runner.py`:

1. `test_external_gstack_runtime_status_contract`
2. `test_external_gstack_runtime_transaction_contract`
3. `test_sync_external_gstack_authority_contract`
4. `test_external_gstack_documentation_contract`

Required source behavior:

- One `external_gstack_runtime.py` authority owns `status`, `apply`, `recover`, inventory, lock, journal, fsync, cutover and rollback.
- Checker imports its pure functions; sync consumes its status/exact excludes and never applies or recovers.
- `flat_generated = external_skill_names - {"gstack"}` and must contain 53 names at the current external version.
- Repo-owned nonexternal `gstack-*` names remain managed by MyCodexEnv.
- All existing sync/checker/loader fixtures isolate HOME and choose active or legacy mode explicitly.
- Six specified source-of-truth documents receive only the minimum conflicting-line corrections.

Required WP1 source gates:

```text
Focused RED/GREEN contract functions
Python and shell syntax checks
Targeted docs/link assertions
git diff --check
WP1 implementation diff = exactly 10 allowed files
GoalBuddy control diff reported separately
python3 scripts/harness_refresh_identity.py status => A/B/C/D fresh
python3 test_runner.py once after the final material WP1 source change
```

## WP1 Runtime Approval Boundary

Source completion does not authorize runtime apply. `T003` must produce a fresh manifest containing canonical roots, external identity, 54-name inventory, 53 flat mappings, sidecar pairs, prestates, warning tuple baseline, quiescence receipt, lock/journal/staging/backup paths, rollback and loader gates. `T004` must stop until that packet is explicitly approved.

## WP2 Contract

WP2 remains blocked until `T005` proves WP1 complete and freezes its baseline. The WP2 Worker may touch only the seven paths on `T006.allowed_files`; its runtime promotion remains a separate three-target PM transaction after `T007` approval.

## Known Blocker

The requested local visual board is blocked because unpinned `npx goalbuddy` would dynamically download and execute a third-party package. The file board is valid and execution can continue. Starting the visual board requires separate explicit approval for pinned `goalbuddy@0.3.6` execution.

## Board Receipt Snippet

```yaml
receipt:
  result: done
  note: notes/T001-plan-validation.md
  decision: "Activate T002; runtime remains independently approval-gated."
  next_allowed_task: T002
```
