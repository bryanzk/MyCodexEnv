# T002: WP1 Identity C Blocker

Task: `T002`
Kind: `worker`
Status: `blocked`

## Summary

The first WP1 source slice is materially implemented and its focused contracts pass, but the fresh Identity gate reports `C stale`. The original task cannot satisfy both its ten-file write set and its A-D-fresh completion gate.

## Evidence

- Focused status/checker/lock/apply-recover/docs/sync contracts passed.
- `python3 scripts/harness_refresh_identity.py status` returned A/B/D fresh and C stale.
- The three Identity files already belong to the approved cumulative goal scope, so sharing them across WP1 and WP2 does not add a new unique path.

## Decision

T003 replaced this blocked task with T010, whose write set is the original ten WP1 files plus the same three shared Identity files. WP1 runtime work remains separately approval-gated.

## Board Receipt Snippet

```yaml
receipt:
  result: blocked
  summary: "Fresh Identity C is stale; replaced by T010 without widening the cumulative scope."
  replaced_by: T010
```
