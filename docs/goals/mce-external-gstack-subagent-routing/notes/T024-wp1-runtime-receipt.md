# T024: WP1 Runtime Receipt

Result: `complete`

## Authorized transaction

- Owner approval: `批准执行 T021 replacement WP1 runtime packet`
- Manifest SHA-256: `dd06e3f258328da1b8ef67dab12d390e449efa732ec4e3110c29215d26dd661d`
- Operation: `/Users/kezheng/.codex/runtime-backups/mce-20260902t021100z-external-gstack`
- Apply receipt: exit 0, `status=complete`, timestamp `2026-09-02T03:01:17Z`
- Temporary manifest removed after the durable journal captured it.

## Runtime parity

- External root: clean `main`, HEAD `702a1a9b698080aca72503f5feed9ed8cd552348`, VERSION `1.78.0.0`.
- Status: expected 54, visible 54, missing/drifted empty, sidecar `ok`.
- Checker: errors 0, warnings 35.
- Warning tuple digest: `ee133997bfd7ec99782ab74de28387d09e7a46dd6fa71e7ce866b0ef38e1a74b`.
- Persistent runtime digest: `a848c792388d785d8f050474e7cab010bc1cda6033229ba1f9ae5b3e7c42c0c3`.
- Persistent non-target digest unchanged: `ccaf37014b2c49846e7f04db68486b0f73e6f9f05583f8fe05e73d910760b9d1`.
- External worktree digest unchanged: `b112500a6ce86ca3cf3c85accc56cfa643c46570c4c557c182490ad6ce942943`.

## Recovery evidence

- Journal SHA-256: `bdfed152afc0636ef6b247d78a972dfa4217892bf5a76375b547ea51ae2bba94`.
- Journal state: `complete`; 34/34 targets `verified`.
- Backup: 34 flat directories plus old sidecar retained.
- Staging: absent after verified completion.
- Focused tests cover normal rollback, apply crash recovery, recover crash continuation, corrupt/missing backup zero-mutation blocking, and idempotence.

## Runtime activity

- Fresh app task readback: only this task active.
- Collaboration tree: only root running.
- Process scan: no competing sync/setup/promotion/external-gstack mutation process.
- Loader: 315 records, 275 unique names, loader errors 0, disabled count 85, external-gstack disabled count 21. The pre-existing missing root-path representation remains one; the existing disabled baseline did not worsen.

## Final gates

- `python3 test_runner.py`: exit 0; 149 passed, 0 skipped, 0 failed; timestamp `2026-09-02T03:02:19Z`.
- `git diff --check`: exit 0.
- Identity: A/B/C/D fresh.

This receipt freezes the WP1 baseline for the WP2 delta. It does not authorize WP2 source or runtime writes beyond the already-approved plan and its separate gates.
