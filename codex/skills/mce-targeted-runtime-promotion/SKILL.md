---
name: mce-targeted-runtime-promotion
description: Use when the user has explicitly approved an exact MyCodexEnv repo-source to local Codex-runtime target allowlist for forward promotion. Do not use for runtime-to-repo imports, branch governance, general capability repair, broad bootstrap/sync, or requests without exact source and target paths.
---

# MCE Targeted Runtime Promotion

Promote only user-approved files from the MyCodexEnv source lane into the local
Codex runtime. This is a high-risk write workflow: exact authorization is the
gate, and source implementation, disk parity, loaded activity, and rollout
observation remain separate states.

## Required Approval Packet

Do not write until the user has approved all of these values together:

- canonical repo root, branch, and current `HEAD`;
- canonical runtime root;
- one source file and one runtime target per row, with no directories, globs, or
  inferred siblings;
- the approved SHA-256 of every source file;
- whether an absent target may be created;
- focused post-promotion gates and any accepted pre-existing gate failures.

Reject `rsync`, `--delete`, directory mirroring, `sync_codex_home.sh`, and any
helper whose effective write set is larger than the approved rows.

## 1. Read-Only Preflight

From the approved repo root, capture fresh receipts for:

```bash
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
```

Record all dirty and untracked paths as user-owned unless the user explicitly
says otherwise. Stop if the root, branch, or `HEAD` differs from the approval;
ownership is ambiguous; an approved source changed digest; a source is not a
regular repo file; or a resolved target escapes the approved runtime root. Do
not follow or replace a symlink target without separate exact authorization.

For every row, record:

| source | target | source SHA-256 | target state and SHA-256 | create allowed |
| --- | --- | --- | --- | --- |

Run the focused source gates and `python3 test_runner.py` before mutation. Also
capture a verifier baseline when applicable. A baseline failure may proceed
only when it is already accepted in the approval packet or is exactly the
allowlisted source/runtime drift that this promotion will repair.

Before any runtime write, create a normalized relative-path/SHA-256 manifest of
every regular file in the managed runtime scope except the exact target paths.
Use a temporary, stdlib-only one-shot or an existing read-only repo command;
exclude by exact resolved path, not pattern. This is the non-target baseline.

## 2. Back Up Every Existing Target

Create a task-specific backup directory outside the managed runtime tree. Before
copying any promoted file:

- copy each existing target individually with metadata preserved;
- record an absent marker for each approved new target;
- require the backup to be a readable regular file;
- run `cmp` between each existing target and its backup;
- record both SHA-256 values and require them to match.

If any backup, read, `cmp`, or hash check fails, stop with zero promotion writes.
Keep the backup path in the receipt so rollback does not depend on shell history.

## 3. Copy Only the Allowlist

Recheck repo `HEAD`, source hashes, target hashes/states, and the non-target
baseline immediately before writing. Stop on concurrent change.

Copy one approved source to its paired target with a direct, metadata-preserving
file command such as `cp -p`. Do not create or touch sibling files. After each
copy, immediately require both:

```bash
cmp SOURCE TARGET
shasum -a 256 SOURCE TARGET
```

Stop at the first mismatch and enter rollback. Never widen the allowlist to make
a gate pass.

## 4. Verify After Promotion

Run, in order:

1. file-by-file `cmp` and SHA-256 checks for every approved row;
2. the approved focused runtime or loader gates;
3. `python3 test_runner.py`;
4. `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"` when the promoted surface is covered by the environment contract;
5. a fresh non-target manifest made with the same command and exclusions, then
   `cmp` it with the baseline;
6. `git status --short` and `git diff --check` to prove unrelated repo state was
   preserved.

The verifier appends `TEST_VERIFICATION.md`. If that file is outside the approved
repo write set, run the verifier through a temporary verification root whose
read-only source paths map to the checkout and whose report lands in the
temporary root. Runtime checks must still point at the approved real runtime.

Post-promotion results must remove the allowlisted drift and add no new failure
relative to the recorded baseline. A target mismatch, focused failure, new full
gate failure, new verifier failure, or changed non-target manifest triggers
rollback.

## 5. Rollback

Rollback touches only allowlisted targets:

- restore every pre-existing target from its verified backup;
- remove only a target that this run created and whose absent marker was
  recorded;
- `cmp` and hash every restored target against its backup, or prove the approved
  new target is absent again;
- regenerate and compare the non-target manifest;
- report the original failure and rollback verification separately.

If rollback verification fails, stop all further writes and report the exact
target and recovery artifact. Never delete the backup automatically.

## Stop Conditions

Stop before mutation for missing exact approval, anchor or digest drift,
ambiguous dirty-file ownership, path escape/symlink ambiguity, unexpected
baseline failures, unreadable backups, or inability to prove the non-target
baseline. After mutation, stop and roll back for concurrent changes, copy/parity
failure, gate regression, or non-target drift.

## Reporting Contract

Report these lanes independently; never infer a later lane from an earlier one:

- `source_implementation`: repo source exists and source gates passed;
- `runtime_parity`: approved source and runtime files are byte/hash equal;
- `runtime_activity`: a fresh host-level probe proved the runtime loaded or
  executed the promoted content;
- `rollout_observation`: separately timed deployment/host observation exists.

Use `not_proven` when activity or rollout evidence was not collected. For every
claim, rollback action, and failed gate, include:

| command | exit_code | key_output | timestamp |
| --- | ---: | --- | --- |

Also list the exact promoted targets, backup paths, unchanged non-target
manifest result, final repo status, and whether commit, push, deployment, or
runtime restart occurred.
