# T008: WP2 Runtime Promotion Receipt

Result: `complete`

## Exact promotion

- Owner approval: `批准执行 T007 WP2 three-target runtime promotion packet`.
- Operation: `/Users/kezheng/.codex/runtime-backups/mce-20260902t033000z-subagent-routing`.
- Three existing regular `0644` targets were promoted with same-directory staging and `os.replace`.
- Backups retained with original SHA values:
  - AGENTS `9faa099dc92702865331bf402cc293c81f7963ae1e62a8b37b8b82d9f14d4b6e`
  - ShipQ `3efd33a73a1b3ff036d11ff4544984bc57f9b8fad1ba69deaa6a59d1a4d5e66e`
  - DHF `d6b7e44058134655d91b0c16bd4f7aa20de86dcccdd4ceb2a647cb2d43cadf8d`

The first attempt stopped before cutover because the non-target check counted the three approved staging files. Live targets remained at old SHA; the exact staging files were verified against source and removed, non-target baseline was restored, and backups were retained. The retry excluded only those three exact staging paths and completed the same approved operation.

## Promoted parity

- AGENTS `7d872b30e95639c82449139250a355e76884c05bd5ddc336a3d6fe1b2c3087ae`
- ShipQ `f6ff10851e4e803006a22d45741d0737c35cb2e88201808ce8b0046413b19e1d`
- DHF `714381dfbd5915b2828482e0c29a62f0e425af5a3e7fd67ebf9ffcd67a299591`
- Each source/target pair passes `cmp`, SHA, mode and size parity; all staging paths are absent.

## Ordered post-gates

1. Three-target parity: exit 0, timestamp `2026-09-02T03:53:29Z`.
2. Strict checker: errors 0, warnings 35, managed drift empty, external gstack 54/54; timestamp `2026-09-02T03:53:29Z`.
3. Full runner: `150 passed, 0 skipped, 0 failed`; timestamp `2026-09-02T03:53:37Z`.
4. Temporary no-skip `verify_codex_env.sh`: all checks passed; temp root removed.
5. Six-file non-target manifest unchanged: `5eb8d465323727c74d0ea2a2dd89f0a5de2df5a268c4f2085ebc9101593fcdfa`.
6. Loader: 315 records, 275 unique names, loader errors 0, missing/disabled baseline unchanged at one missing root representation and 85 disabled paths.
7. Identity A/B/C/D fresh; repo `git diff --check` clean; timestamp `2026-09-02T04:00:06Z`.

## Evidence lanes

- `source_implementation`: proven.
- `runtime_parity`: proven for the exact three targets.
- `runtime_activity`: loader and verifier readback proven; global AGENTS behavior in a new task remains separate.
- `behavior_observation`: not yet proven; T009 requires user-created tasks.

No commit, push, deploy, runtime restart, broad sync, setup, or non-target mutation occurred.
