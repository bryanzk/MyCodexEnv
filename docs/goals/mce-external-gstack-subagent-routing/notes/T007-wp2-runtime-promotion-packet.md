# T007: Exact WP2 Runtime Promotion Packet

Decision: `ready_for_runtime_approval`

This packet authorizes no write by itself.

## Anchor

- Repo: `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv`
- Branch/HEAD: `main` / `286f461966e73db41fc6dfa5d39709e1887d1941`
- Runtime root: `/Users/kezheng/.codex`
- Operation: `mce-20260902t033000z-subagent-routing`
- Backup root: `/Users/kezheng/.codex/runtime-backups/mce-20260902t033000z-subagent-routing`
- Existing targets only; `create_allowed=false` for all rows.

## Exact rows

1. Source `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/codex/AGENTS.md`
   - Source: SHA `7d872b30e95639c82449139250a355e76884c05bd5ddc336a3d6fe1b2c3087ae`, regular `0644`, 8186 bytes.
   - Target `/Users/kezheng/.codex/AGENTS.md`: SHA `9faa099dc92702865331bf402cc293c81f7963ae1e62a8b37b8b82d9f14d4b6e`, regular `0644`, 7905 bytes.
   - Staging `/Users/kezheng/.codex/.AGENTS.md.mce-new-mce-20260902t033000z-subagent-routing`.
   - Backup `/Users/kezheng/.codex/runtime-backups/mce-20260902t033000z-subagent-routing/AGENTS.md`.
2. Source `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/codex/skills/shipq-lifecycle-harness/SKILL.md`
   - Source: SHA `f6ff10851e4e803006a22d45741d0737c35cb2e88201808ce8b0046413b19e1d`, regular `0644`, 7730 bytes.
   - Target `/Users/kezheng/.codex/skills/shipq-lifecycle-harness/SKILL.md`: SHA `3efd33a73a1b3ff036d11ff4544984bc57f9b8fad1ba69deaa6a59d1a4d5e66e`, regular `0644`, 6494 bytes.
   - Staging `/Users/kezheng/.codex/skills/shipq-lifecycle-harness/.SKILL.md.mce-new-mce-20260902t033000z-subagent-routing`.
   - Backup `/Users/kezheng/.codex/runtime-backups/mce-20260902t033000z-subagent-routing/shipq-lifecycle-harness/SKILL.md`.
3. Source `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/codex/skills/delivery-harness-framework/SKILL.md`
   - Source: SHA `714381dfbd5915b2828482e0c29a62f0e425af5a3e7fd67ebf9ffcd67a299591`, regular `0644`, 38948 bytes.
   - Target `/Users/kezheng/.codex/skills/delivery-harness-framework/SKILL.md`: SHA `d6b7e44058134655d91b0c16bd4f7aa20de86dcccdd4ceb2a647cb2d43cadf8d`, regular `0644`, 37712 bytes.
   - Staging `/Users/kezheng/.codex/skills/delivery-harness-framework/.SKILL.md.mce-new-mce-20260902t033000z-subagent-routing`.
   - Backup `/Users/kezheng/.codex/runtime-backups/mce-20260902t033000z-subagent-routing/delivery-harness-framework/SKILL.md`.

## Preserved baseline

- Six regular non-target files under the two skill runtime directories: manifest SHA `5eb8d465323727c74d0ea2a2dd89f0a5de2df5a268c4f2085ebc9101593fcdfa`.
- External gstack: 54/54, warnings baseline 35.
- Identity A/B/C/D fresh.
- Pre-promotion full runner accepted failure set: exactly the two fixed-base DHF intermediate failures; `150 total, 148 pass`.
- Pre-promotion verifier accepted failure set: exactly `codex_agents_runtime_matches_source` and `codex_skill_compatibility`; every other check passed.

## Transaction

After fresh quiescence and rechecking every anchor/hash/state:

1. Create only the exact backup root and copy each target individually with `cp -p`; require backup regular/readable, `cmp`, mode, size and SHA equality.
2. Copy each source with metadata to its exact same-directory staging path; verify type/mode/size/SHA.
3. Promote only the three staging files with `os.replace` and immediately verify source-target parity.
4. Retain backups. Do not run broad sync, rsync, setup, commit, push, deploy, or write siblings.

Any failure enters rollback: construct same-directory rollback staging from the corresponding verified backup, `os.replace` only the three targets, verify restored SHA/mode/size, and recheck the non-target manifest. Preserve the original failure separately.

## Mandatory post-promotion order

1. Three-row `cmp` / SHA / mode / size parity.
2. Strict live checker: errors 0, only the frozen 35 warnings, external gstack 54/54.
3. `python3 test_runner.py`: require `150/150`; either prior intermediate failure remaining triggers rollback.
4. Temporary verification root with the 17 authorized working-tree files: `verify_codex_env.sh` without skips; require all checks pass.
5. Recompute six-file non-target manifest and require SHA `5eb8d465323727c74d0ea2a2dd89f0a5de2df5a268c4f2085ebc9101593fcdfa`.
6. Fresh loader: no new errors, disabled, or missing paths relative to the WP1 baseline.
7. Repo `git status --short`, `git diff --check`, and Identity A-D fresh.

Disk parity and loader readback do not prove cross-task routing behavior; that remains T009.
