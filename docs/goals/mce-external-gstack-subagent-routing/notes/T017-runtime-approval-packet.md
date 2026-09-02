# T017: Exact WP1 Runtime Approval Packet

Decision: `ready_for_runtime_approval`

This packet authorizes no write by itself. Any pre-apply drift requires a new packet.

## Identity and paths

- operation_id: `mce-20260902t012000z`
- repo_root: `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv`
- codex_home: `/Users/kezheng/.codex`
- external_root: `/Users/kezheng/.gstack/repos/gstack` (read-only)
- operation_root: `/Users/kezheng/.codex/runtime-backups/mce-20260902t012000z-external-gstack`
- staging_root: `/Users/kezheng/.codex/runtime-backups/mce-20260902t012000z-external-gstack/staging`
- backup_root: `/Users/kezheng/.codex/runtime-backups/mce-20260902t012000z-external-gstack/backup`
- journal: `/Users/kezheng/.codex/runtime-backups/mce-20260902t012000z-external-gstack/operation.json`
- external branch/HEAD/VERSION: `main` / `702a1a9b698080aca72503f5feed9ed8cd552348` / `1.78.0.0`

## Exact topology

- Inventory: 54 names; digest `c6e65579802ee0b926c4f7f01d2ca40c42d908de71aff6d319cfd803cc387259`.
- Flat targets: 53 names; digest `7b449f6d72fe16ff1d03a6cab9e700e544ad90f1b48a356927e6fb868a12ec5a`.
- Replace 34 real directories; digest `2fc96722f77c7163bc619a793587e4d4affd12009386412e532e03ed4623cc12`:
  `gstack-autoplan`, `gstack-benchmark`, `gstack-browse`, `gstack-canary`, `gstack-careful`, `gstack-cso`, `gstack-design-consultation`, `gstack-design-html`, `gstack-design-review`, `gstack-design-shotgun`, `gstack-devex-review`, `gstack-document-release`, `gstack-freeze`, `gstack-guard`, `gstack-health`, `gstack-investigate`, `gstack-land-and-deploy`, `gstack-learn`, `gstack-office-hours`, `gstack-open-gstack-browser`, `gstack-pair-agent`, `gstack-plan-ceo-review`, `gstack-plan-design-review`, `gstack-plan-devex-review`, `gstack-plan-eng-review`, `gstack-qa`, `gstack-qa-only`, `gstack-retro`, `gstack-review`, `gstack-setup-browser-cookies`, `gstack-setup-deploy`, `gstack-ship`, `gstack-unfreeze`, `gstack-upgrade`.
- Preserve 19 existing correct links; digest `419a8b3a13ae76b680f693a072703562f5b677ac347792ea4df717f09d1b8869`:
  `gstack-benchmark-models`, `gstack-claude`, `gstack-context-restore`, `gstack-context-save`, `gstack-diagram`, `gstack-document-generate`, `gstack-ios-clean`, `gstack-ios-design-review`, `gstack-ios-fix`, `gstack-ios-qa`, `gstack-ios-sync`, `gstack-landing-report`, `gstack-make-pdf`, `gstack-plan-tune`, `gstack-scrape`, `gstack-setup-gbrain`, `gstack-skillify`, `gstack-spec`, `gstack-sync-gbrain`.
- Sidecar: replace the real `~/.codex/skills/gstack` directory with the exact 13 source-target links and six parent directories defined by `SIDECAR_PAIRS` / `SIDECAR_DIRS`; no fourteenth link or mirror is allowed.
- `gstack-checkpoint` and every non-target skill are excluded from the mutation set.

## Frozen approval context

- approval_context SHA-256: `bb75ab20bb9e0a46bd91f07bc459ff1b14a00d0e72f80eb499c1acbe3be57763`
- authority SHA-256: `25de8ebdfe41df7994b317f216cedb7015c0db81bd4a66f2612dd1eb15e14c90`
- external worktree SHA-256: `b112500a6ce86ca3cf3c85accc56cfa643c46570c4c557c182490ad6ce942943`
- runtime skills SHA-256: `2ddeb63bf0fa70bde7c6472ee9dc807dfb17a77af7c8aa2486267cb028bfaca7`
- non-target SHA-256: `df8f06ba5a24a25b19c156160b03a8cd13aa96e02f6b88ed6ae182d08158b521`
- 34 real-directory prestates SHA-256: `d7e099762d6630f1f7555761a492d55de2f93125e4720e8fab032bdd678efdfd`
- sidecar prestate SHA-256: `c834937a1360720473363fb6fdc9b590ed614021cdd4f275c1db3d1a0b94644c`
- 35 warning tuples SHA-256: `ee133997bfd7ec99782ab74de28387d09e7a46dd6fa71e7ce866b0ef38e1a74b`

The executable manifest must contain these exact values plus a fresh owner-approved quiescence receipt for the same operation ID. The authority rechecks all values under the shared `.phase0-sync.lock` immediately before cutover.

## Current read-only activity baseline

- Collaboration: only root is running; all three committee agents are complete.
- Process scan: no `sync_codex_home`, `external_gstack_runtime`, gstack setup, promotion, or `codex exec` process found.
- Operation root: absent.
- Loader readback: `loader_errors=0`, but the existing runtime baseline has one unresolved external-root path and many pre-existing disabled skills. This is not modified in source and must not worsen; external authority parity is independently required to become 54/54.

## Only allowed mutation and recovery

Apply only through:

```text
python3 scripts/external_gstack_runtime.py apply --manifest <approved-json>
```

On any nonzero apply or failed post-check, recover only through:

```text
python3 scripts/external_gstack_runtime.py recover --operation-root /Users/kezheng/.codex/runtime-backups/mce-20260902t012000z-external-gstack --rollback
```

No setup, sync, network, external-root write, manual continue, commit, push, or non-target write is authorized.

## Post-apply gates

1. `status`: 54/54, missing/drifted empty, sidecar `ok`.
2. Compatibility: no errors; warning tuples stay at the frozen 35-tuple digest.
3. Non-target digest unchanged.
4. Journal state `complete`; backup retained.
5. Fresh loader readback: no loader errors and no worsening from the recorded baseline.
6. `python3 test_runner.py`: 149/149.
