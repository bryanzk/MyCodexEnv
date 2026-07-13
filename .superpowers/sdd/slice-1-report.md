# Slice 1 Report: Deterministic Governance Profiles

## Status

- Result: GREEN; Slice 1 source-stage implementation complete.
- Implementation commit: `1652992c89adb4d6aba2bdb1c4db977b44fe2623` (`feat: add deterministic DHF governance profiles`).
- Runtime boundary: `~/.codex`, `~/.claude`, remote services, the skill Output Contract, and documentation mirrors were not changed.

## Delivered

- Added deterministic `light`, `standard`, and `governed` classification to `codex/hooks/dhf_preprompt.py`.
- Preserved dispatcher precedence: invalid payload/cwd, opt-out, ShipQ lazy delegation, explicit generic activation, ordinary continue-only.
- Added monotonic active-profile retention and governed fail-closed classification for resumed malformed state.
- Added minimum profile-specific injected context; simplified light/standard/governed routes do not read or inject the full skill.
- Added default-on `DHF_PREPROMPT_SIMPLIFIED_PROFILES`; rollback values `0`, `false`, `off`, and `legacy` execute the preserved full-skill `generic_response()` route.
- Split Slice 0 measurement into explicit legacy baseline and simplified candidate paths without changing canonical baseline values.
- Added focused corpus/profile, implicit-risk, precedence, ownership, upgrade, no-leak, and rollback tests.

## TDD Receipts

### RED 1: Profile behavior

- command: `python3 tests/test_dhf_simplification.py`
- exit_code: `1`
- key_output: `FAILED (failures=2, errors=19)`; expected failures named missing `select_governance_profile`, missing `generic-activated:light`, and missing `generic-activated:legacy`.
- timestamp: `2026-07-13T19:35:54Z`

### RED 2: Candidate measurement interface

- command: `python3 -m unittest tests.test_dhf_simplification.DhfSimplificationCorpusTests.test_candidate_measurement_exposes_selected_profiles_without_rewriting_baseline`
- exit_code: `1`
- key_output: `AttributeError: module 'dhf_simplification_validator' has no attribute 'measure_candidate'`.
- timestamp: `2026-07-13T19:37:00Z`

### GREEN: Focused profile/corpus suite

- command: `python3 tests/test_dhf_simplification.py`
- exit_code: `0`
- key_output: `Ran 19 tests in 1.139s` and `OK`.
- timestamp: `2026-07-13T19:41:19Z`

### GREEN: Existing dispatcher compatibility bundle

- command: direct invocation of the nine registered `test_runner` dispatcher/profile functions covering registration, malformed payloads, runtime errors, invalid adapters, ShipQ truth table, opt-out, lazy import/no-write, no-leak output, and golden corpus.
- exit_code: `0`
- key_output: nine `[PASS]` lines ending with `[PASS] DHF simplification golden corpus`.
- timestamp: `2026-07-13T19:37:42Z`

## Final Verification

- command: `python3 -m py_compile codex/hooks/dhf_preprompt.py scripts/validate_dhf_simplification_corpus.py tests/test_dhf_simplification.py`
- exit_code: `0`
- key_output: no output.
- timestamp: `2026-07-13T19:41:19Z`

- command: `git diff --check`
- exit_code: `0`
- key_output: no whitespace errors.
- timestamp: `2026-07-13T19:41:19Z`

- command: `set -o pipefail; python3 -u test_runner.py | tail -12`
- exit_code: `0`
- key_output: `ran=86 passed=86 skipped=0 failed=0` and `[PASS] all tests`.
- timestamp: `2026-07-13T19:42:20Z`

## Files Changed

- `codex/hooks/dhf_preprompt.py`
- `scripts/validate_dhf_simplification_corpus.py`
- `test_runner.py`
- `tests/test_dhf_simplification.py`
- `.superpowers/sdd/slice-1-report.md`

## Self-Review

- Confirmed ordinary continue-only never becomes `light` and receives no profile context.
- Confirmed opt-out precedes ShipQ and generic activation; ShipQ adapter response remains unchanged and owns its context.
- Confirmed feature-switch rollback preserves the existing `generic_response()` entry point and full-skill path.
- Confirmed classifier only uses standard-library deterministic matching, profile rank never downgrades a valid active profile, and governed signals are ordered to keep architecture conflicts distinct from generic state conflicts.
- Confirmed malformed/error subprocess paths emit one valid JSON response, bounded diagnostics, and no traceback, skill marker, secret path, or unrelated local context.
- Confirmed no runtime-home, skill Output Contract, docs mirror, helper CLI, fixture baseline, or remote mutation occurred.

## Concerns / Deferred Work

- The classifier is intentionally bounded to the approved corpus and named risk signals. Future vocabulary expansion should begin with a failing scenario test to avoid silent under-routing.
- Slice 2 owns the skill Output Contract; Slice 3 owns documentation mirrors. They remain intentionally unchanged in this slice.
- Runtime promotion remains separately gated and unauthorized; repo source and runtime home are intentionally out of parity until a later explicit sync decision.
