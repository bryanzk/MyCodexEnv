# T010: Surfaces Manifest Blocker

Task: `T010`
Kind: `worker`
Status: `blocked`

## Summary

WP1 source implementation, focused tests, documentation contracts, sync regressions and Identity refresh are complete enough to reach the full repository gate. The gate ran 149 tests: 147 passed and two failed for the same reason.

## Exact Failure

```text
ERROR[in_index_not_manifest] scripts/external_gstack_runtime.py
```

Failing tests:

- `test_surfaces_manifest_no_orphans`
- `test_check_surfaces_validates_public_nav`

The new public script is correctly listed in `docs/repo-index.md`, but the canonical `docs/surfaces.json` inventory is not in the current cumulative allowlist.

## Judge Decision

T012 determined the minimum correct repair is one manifest entry:

```json
{
  "path": "scripts/external_gstack_runtime.py",
  "role": "single external gstack status, apply, recover, journal, and rollback authority",
  "audience": ["codex", "human"]
}
```

Removing the repo-index entry would evade the repository's source-of-truth contract. T013 remains blocked until the owner explicitly authorizes `docs/surfaces.json` as the seventeenth cumulative path.

## Evidence

- command: `python3 test_runner.py`
- exit_code: `1`
- key_output: `ran=149 passed=147 skipped=0 failed=2`
- timestamp: `2026-09-02T00:27:04Z`
