# T021: Replacement WP1 Runtime Approval Packet

Decision: `ready_for_reapproval`

T017 was invalidated before manifest creation or runtime writes because a fresh loader readback materialized the loader-owned `.system` projection. T020 now excludes only the exact top-level `.system` name from persistent runtime/non-target digests. Independent Judge confirmed all other non-target paths remain protected.

## Exact operation

- operation_id: `mce-20260902t021100z`
- repo_root: `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv`
- codex_home: `/Users/kezheng/.codex`
- external_root: `/Users/kezheng/.gstack/repos/gstack` (read-only)
- operation_root: `/Users/kezheng/.codex/runtime-backups/mce-20260902t021100z-external-gstack`
- staging_root: `/Users/kezheng/.codex/runtime-backups/mce-20260902t021100z-external-gstack/staging`
- backup_root: `/Users/kezheng/.codex/runtime-backups/mce-20260902t021100z-external-gstack/backup`
- journal: `/Users/kezheng/.codex/runtime-backups/mce-20260902t021100z-external-gstack/operation.json`
- external branch/HEAD/VERSION: `main` / `702a1a9b698080aca72503f5feed9ed8cd552348` / `1.78.0.0`

## Exact unchanged runtime write set

- 54-name inventory, digest `c6e65579802ee0b926c4f7f01d2ca40c42d908de71aff6d319cfd803cc387259`.
- 53 flat targets, digest `7b449f6d72fe16ff1d03a6cab9e700e544ad90f1b48a356927e6fb868a12ec5a`.
- Replace the same 34 real directories listed in T017, digest `2fc96722f77c7163bc619a793587e4d4affd12009386412e532e03ed4623cc12`.
- Preserve the same 19 existing links listed in T017, digest `419a8b3a13ae76b680f693a072703562f5b677ac347792ea4df717f09d1b8869`.
- Replace the `gstack` real sidecar with exactly 13 links and six parent directories from `SIDECAR_PAIRS` / `SIDECAR_DIRS`.
- Preserve `gstack-checkpoint`, every other non-target, external root, and repo source.

## Frozen replacement context

- approval_context SHA-256: `ca7488859b6350c227fc5e672fa67bd962211763c87760b15896932845a067ad`
- authority SHA-256: `f7e69b42bfa58694790986a345dfd361512f2b7bbf2386d2671fe1452b6c7a63`
- external worktree SHA-256: `b112500a6ce86ca3cf3c85accc56cfa643c46570c4c557c182490ad6ce942943`
- persistent runtime skills SHA-256: `daa451342ea0a56b64e4e8505d39a14ea711756e73d37bdd38c0de971b298983`
- persistent non-target SHA-256: `ccaf37014b2c49846e7f04db68486b0f73e6f9f05583f8fe05e73d910760b9d1`
- 34 real-directory prestates SHA-256: `d7e099762d6630f1f7555761a492d55de2f93125e4720e8fab032bdd678efdfd`
- sidecar prestate SHA-256: `c834937a1360720473363fb6fdc9b590ed614021cdd4f275c1db3d1a0b94644c`
- 35 warning tuples SHA-256: `ee133997bfd7ec99782ab74de28387d09e7a46dd6fa71e7ce866b0ef38e1a74b`

The context was identical before and after a fresh loader readback while `.system` existed. Any change to these fields, 34/19 partition, or operation path invalidates this packet.

## Execution and recovery

Apply only through `python3 scripts/external_gstack_runtime.py apply --manifest <approved-json>`.

On any failure, recover only through:

```text
python3 scripts/external_gstack_runtime.py recover --operation-root /Users/kezheng/.codex/runtime-backups/mce-20260902t021100z-external-gstack --rollback
```

No setup, sync, network, external-root write, manual continue, commit, push, or non-target write is authorized. Post-apply gates remain the T017 gates: 54/54 status, zero compatibility errors, frozen warning tuples, unchanged persistent non-target digest, complete journal with retained backup, loader readback without worsening, and 149/149 tests.
