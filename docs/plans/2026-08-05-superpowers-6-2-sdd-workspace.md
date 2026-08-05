# Superpowers 6.2.0 SDD Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import the already reviewed, user-owned four-file Superpowers 6.2.0 source delta from the protected main checkout into an isolated branch, verify it against repository and live-runtime acceptance checks, and preserve a complete SDD review workspace without changing main or the runtime.

**Architecture:** Treat the dirty main checkout as a read-only patch source and the Codex-native linked worktree as the only implementation workspace. Commit this plan first, initialize a plan-scoped SDD scratch directory, export a binary/full-index patch plus manifest from main, and let one fresh implementer apply, test, and commit the exact four-file delta. A task-scoped reviewer and a whole-branch reviewer independently gate the result; every fix is delegated through the bounded SDD review loop.

**Tech Stack:** Git linked worktrees and commits, Bash, Python 3 repository test runner, Superpowers 6.2.0 SDD workspace scripts, SHA-256 manifests, Codex local plugin/runtime verification.

## Global Constraints

- The canonical repository anchor is `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv`; the main checkout remains on branch `main` and is read-only throughout this plan.
- All implementation commands run from the existing Codex-native linked worktree `/Users/kezheng/.codex/worktrees/0b59/MyCodexEnv` on branch `codex/mce-20260805-superpowers-6-2-sdd-workspace`; never create a nested worktree.
- The branch base is the implementation-start main HEAD `dbbf59675cd2649f5222f865714d76283ea47c4a`.
- The protected main checkout must retain exactly four unstaged paths and no staged or untracked paths: `locks/superpowers.lock`, `scripts/sync_codex_home.sh`, `scripts/verify_codex_env.sh`, and `test_runner.py`.
- The protected main file SHA-256 values are `1e9b876547e81769395b1cc452573a1419e2a1cca23ce70363977e80554f3f9b`, `9227d0c975dcbcd1abb538514ab7738a14c0d26abd992060a2b6cf3086cf8c68`, `738de71edfc37973d70092d3c8b5e33753707c9a7e9f37fc9fdd2e9836c51dca`, and `a83cb3f12ff8fab5463828d0d38156694ae52decadf01b3b15d327df861c1424` in the path order above.
- The exact source write set is the same four paths. No other tracked source or documentation file may enter the source commit.
- The target Superpowers commit is `3dcbd5c4b48e02263fbf4a3c01e3fe4f81d584d9`; the target plugin version is `6.2.0`.
- The `test_runner.py` installed-plugin stub version `6.1.1` is an intentional negative probe proving that an older installed version triggers upgrade; it must remain `6.1.1`.
- The plan-only commit subject is `docs: add Superpowers 6.2.0 SDD workspace plan`; the source commit subject is `chore: upgrade Superpowers to 6.2.0`.
- The plan path is `docs/plans/2026-08-05-superpowers-6-2-sdd-workspace.md`; its basename and SDD slug are `2026-08-05-superpowers-6-2-sdd-workspace`.
- The SDD scratch directory is `/Users/kezheng/.codex/worktrees/0b59/MyCodexEnv/.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/`; it is distinct from the Git worktree and remains ignored, local, and preserved after final review.
- The ledger first line is exactly `# SDD ledger — plan: /Users/kezheng/.codex/worktrees/0b59/MyCodexEnv/docs/plans/2026-08-05-superpowers-6-2-sdd-workspace.md`.
- Do not read, write, move, or delete a sibling plan's SDD workspace. If a same-basename plan or identity-mismatched workspace is found, stop without overwriting it. Leave a legacy `.superpowers/sdd/progress.md` untouched and do not treat it as this plan's ledger.
- Do not use `stash`, `reset`, `restore`, broad sync, `rsync --delete`, `git clean -fdx`, `rm`, `trash`, or worktree removal. Do not modify `/Users/kezheng/.codex`, `/Users/kezheng/.claude`, runtime config, hooks drift, managed-skill drift, or any `.DS_Store`.
- Do not push, merge, deploy, sync runtime state, or clean up the isolated worktree or SDD workspace.
- Fresh source acceptance is `python3 test_runner.py` with `ran=111 passed=111 skipped=0 failed=0` and `[PASS] all tests`.
- All Superpowers-specific rows from `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home /Users/kezheng/.codex --claude-home /Users/kezheng/.claude` must pass. The overall command may remain nonzero only for the known unrelated rows `codex_hooks_runtime_matches_source` and `codex_skill_compatibility`; record them without fixing them.
- Every completion claim must contain a fresh `command`, `exit_code`, `key_output`, and timezone-bearing `timestamp`.
- Controller edits are limited to this plan, the SDD initializer-owned `.superpowers/sdd/.gitignore`, plan-scoped ignored SDD artifacts, persisted reviewer verdicts, and ledger bookkeeping. The controller must not implement or repair Task 1 findings; implementers own source changes and reviewers own verdicts.

---

## Definition of Done

- The branch contains exactly two local commits after the base: the plan-only commit and the exact four-file source commit, with the required subjects. Any delegated task or final-review fix must amend the source commit in place and must not create a third commit.
- The plan-only commit contains only this plan path; the source commit contains only the four source allowlist paths.
- The source delta pins commit `3dcbd5c4b48e02263fbf4a3c01e3fe4f81d584d9` and plugin version `6.2.0` while preserving the intentional `6.1.1` installed-plugin negative stub.
- The plan-scoped SDD workspace contains the ledger, protected patch and manifest, Task 1 brief/report, per-task review package, whole-branch review package, and review verdict records.
- Task 1 has both a spec-compliance verdict and a task-quality verdict. Critical, Important, or confirmed spec-gap findings are fixed and scoped-re-reviewed within at most five rounds, or the task stops as blocked if a load-bearing finding remains.
- The final whole-branch review has no unadjudicated load-bearing finding after at most one complete fix wave and one scoped re-review.
- Fresh final evidence proves the source suite is green, all Superpowers runtime checks pass, only the two allowed unrelated verify rows may fail, and the main branch/status/hashes are unchanged from the preflight snapshot.
- The isolated worktree and plan-scoped SDD workspace remain present; no push or merge is performed.

## Scope and File Map

**Tracked plan file created before SDD execution**

- `docs/plans/2026-08-05-superpowers-6-2-sdd-workspace.md`: executable implementation and review contract; committed alone.

**Tracked source files imported by Task 1**

- `locks/superpowers.lock`: pin the Superpowers checkout to the target commit.
- `scripts/sync_codex_home.sh`: require the 6.2.0 plugin manifest and installed plugin version during synchronization decisions.
- `scripts/verify_codex_env.sh`: require the 6.2.0 plugin manifest and installed plugin version during runtime verification.
- `test_runner.py`: align fixtures and expectations with the target commit/version while preserving the 6.1.1 negative installed-plugin stub.

**Ignored plan-scoped SDD artifacts**

- `.superpowers/sdd/.gitignore`: initializer-owned self-ignore file containing `*`; permitted only as the documented side effect of live `sdd-workspace`.
- `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/progress.md`: recovery ledger and review/fix-loop state.
- `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/protected-main-delta.patch`: binary/full-index export of the exact main delta.
- `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/protected-main-delta-manifest.txt`: base, paths, file hashes, and patch hash.
- `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/task-1-brief.md`: generated implementer requirements.
- `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/task-1-report.md`: implementer report and any appended fix reports.
- `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/review-*.diff`: immutable per-range task, fix, and final review packages.
- `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/task-1-review.md`: controller-persisted verbatim initial task-review verdict.
- `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/task-1-fix-round-N-review.md`: controller-persisted verbatim scoped re-review verdict for fix round N.
- `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/final-review.md`: controller-persisted verbatim whole-branch verdict.
- `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/final-fix-review.md`: controller-persisted verbatim final fix-wave scoped re-review verdict when a final fix wave is required.

**Out of scope**

- Runtime synchronization or edits under `/Users/kezheng/.codex` or `/Users/kezheng/.claude`.
- Repairing `codex_hooks_runtime_matches_source`, `codex_skill_compatibility`, or any unrelated finding.
- Refactoring synchronization or verification flows beyond the protected four-file delta.
- Push, merge, deployment, worktree removal, scratch deletion, or user-owned file cleanup.

## Controller Setup Before Task 1

- [ ] **Step 1: Re-prove worktree isolation and the protected main snapshot**

Run the git-dir/common-dir/submodule guard in the isolated worktree. In the main checkout, record Git top-level, branch, HEAD, short status, unstaged paths, staged paths, untracked paths, and SHA-256 for the four allowlist files. Stop unless the worktree is linked and non-submodule, main is on `main`, main HEAD matches the branch base, and main contains exactly the four unstaged allowlist paths with the recorded hashes.

- [ ] **Step 2: Validate the recorded collision preflight and current identity**

Use this persisted implementation-start receipt:

- `command`: `test ! -e docs/plans/2026-08-05-superpowers-6-2-sdd-workspace.md && test -z "$(find docs -type f -name '2026-08-05-superpowers-6-2-sdd-workspace.md' -print)" && test ! -e .superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace && test ! -e .superpowers/sdd/progress.md`
- `exit_code`: `0`
- `key_output`: `PLAN_CANDIDATE=ABSENT; PLAN_BASENAME_MATCHES=none; SCRATCH=ABSENT; FLAT_LEDGER=ABSENT`
- `timestamp`: `2026-08-05T09:34:31-0400`

Before plan commit, require the only current same-basename match to be this canonical plan path and require the scratch path to remain absent. If a plan-scoped workspace later exists, verify its ledger first line names this plan's canonical absolute path before reading or writing any artifact; leave any legacy flat ledger untouched.

- [ ] **Step 3: Review and commit the plan alone**

Run a spec-coverage self-review, scan for placeholder language, check all paths/types/values, obtain one independent read-only plan review, and fix blocking plan findings before continuing. Then run `git diff --check`, stage only the exact plan path, prove the cached path list contains only that path, and commit with `docs: add Superpowers 6.2.0 SDD workspace plan`.

- [ ] **Step 4: Initialize the SDD workspace from the live 6.2.0 runtime skill**

Run:

```bash
/Users/kezheng/.codex/superpowers/skills/subagent-driven-development/scripts/sdd-workspace \
  "$(realpath docs/plans/2026-08-05-superpowers-6-2-sdd-workspace.md)"
```

Require the returned path to equal the isolated worktree plus `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace`. Create `progress.md` with the required plan-identity first line, then append the plan commit SHA, main base SHA, protected main hashes, branch, and worktree path.

- [ ] **Step 5: Export and manifest the protected main delta**

Set `PATCH_FILE=/Users/kezheng/.codex/worktrees/0b59/MyCodexEnv/.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/protected-main-delta.patch` and `MANIFEST_FILE=/Users/kezheng/.codex/worktrees/0b59/MyCodexEnv/.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/protected-main-delta-manifest.txt`. From the main checkout, run `git diff --binary --full-index -- locks/superpowers.lock scripts/sync_codex_home.sh scripts/verify_codex_env.sh test_runner.py` and redirect it to `"$PATCH_FILE"`. Compute `PATCH_SHA=$(shasum -a 256 "$PATCH_FILE" | awk '{print $1}')`, emit the following exact line schema and order from a grouped `printf` block, and redirect that grouped block to `"$MANIFEST_FILE"`:

```text
main_head=dbbf59675cd2649f5222f865714d76283ea47c4a
path=locks/superpowers.lock sha256=1e9b876547e81769395b1cc452573a1419e2a1cca23ce70363977e80554f3f9b
path=scripts/sync_codex_home.sh sha256=9227d0c975dcbcd1abb538514ab7738a14c0d26abd992060a2b6cf3086cf8c68
path=scripts/verify_codex_env.sh sha256=738de71edfc37973d70092d3c8b5e33753707c9a7e9f37fc9fdd2e9836c51dca
path=test_runner.py sha256=a83cb3f12ff8fab5463828d0d38156694ae52decadf01b3b15d327df861c1424
patch_sha256=$PATCH_SHA
```

The final line is produced with `printf 'patch_sha256=%s\n' "$PATCH_SHA"`; `$PATCH_SHA` is the computed digest, not literal manifest text. Recheck main branch, HEAD, status, staged/untracked emptiness, and all four hashes after export.

- [ ] **Step 6: Establish the clean branch baseline**

From the isolated worktree before applying the patch, run `python3 test_runner.py` and require `ran=111 passed=111 skipped=0 failed=0`. Record Task 1 `BASE` as the plan-only commit HEAD in the ledger.

- [ ] **Step 7: Generate the bounded brief and dispatch Task 1**

Set `PLAN_FILE=/Users/kezheng/.codex/worktrees/0b59/MyCodexEnv/docs/plans/2026-08-05-superpowers-6-2-sdd-workspace.md` and `TASK_BASE=$(git rev-parse HEAD)`, append `Task 1 BASE: $TASK_BASE` to the ledger, then run `/Users/kezheng/.codex/superpowers/skills/subagent-driven-development/scripts/task-brief "$PLAN_FILE" 1`. Require the printed path to be this plan's `task-1-brief.md` and require the last line of that brief to belong to Task 1. Dispatch one fresh standard-model implementer with the brief path, report path, worktree path, and short report contract. No implementation agents run in parallel.

## Controller Review After Task 1

- [ ] **Step 1: Package the complete Task 1 range and persist the review**

Use the `TASK_BASE` recorded before implementer dispatch; do not overwrite or recompute it after implementation. Run `/Users/kezheng/.codex/superpowers/skills/subagent-driven-development/scripts/review-package "$PLAN_FILE" "$TASK_BASE" "$(git rev-parse HEAD)"`, then dispatch a fresh task reviewer with `task-1-brief.md`, `task-1-report.md`, the printed package path, and the Global Constraints. Require both a spec-compliance verdict and task-quality verdict. The controller writes the reviewer's returned report verbatim to `task-1-review.md` and appends its two verdicts to the ledger.

- [ ] **Step 2: Execute the bounded per-task fix loop**

Critical, Important, or confirmed spec-gap findings enter at most five rounds: rounds 1-3 resume the original implementer; rounds 4-5 use a fresh stronger implementer. Every round records `FIX_BASE=$(git rev-parse HEAD)` before the fix, requires the implementer to stage only the four source paths and run `git commit --amend --no-edit`, packages the resulting tree delta with `review-package "$PLAN_FILE" "$FIX_BASE" "$(git rev-parse HEAD)"`, appends a fix report with covering tests, receives a scoped re-review, writes that returned verdict verbatim to `task-1-fix-round-N-review.md`, and adds the required ledger entry. Because fixes amend the source commit, `FIX_BASE..HEAD` compares the old and amended trees while branch history remains exactly two commits after the base. Minor findings are deferred to final review. After round 5, any load-bearing finding records `Task 1: BLOCKED` and stops; a clean verdict records `Task 1: complete`.

## Final Whole-Branch Review and Delivery

- [ ] **Step 1: Generate the whole-branch package and persist the verdict**

Set `MERGE_BASE=dbbf59675cd2649f5222f865714d76283ea47c4a` and run `/Users/kezheng/.codex/superpowers/skills/subagent-driven-development/scripts/review-package "$PLAN_FILE" "$MERGE_BASE" "$(git rev-parse HEAD)"`, covering the plan-only and source commits. Dispatch the strongest available reviewer with the plan, the printed whole-branch package path, current HEAD, and pointers to every deferred/parked ledger entry. The controller writes the returned whole-branch report verbatim to `final-review.md` and appends its verdict to the ledger.

- [ ] **Step 2: Resolve final findings within one amend-only wave**

If the final review has findings, record `FIX_BASE=$(git rev-parse HEAD)` and dispatch one fresh implementer with the complete findings list. The implementer must stage only the four source paths, run covering tests, append its report, and use `git commit --amend --no-edit`; it must not create a third commit or amend the plan-only commit. Generate one `FIX_BASE..HEAD` package and run one scoped re-review. The controller writes the returned verdict verbatim to `final-fix-review.md` and adjudicates every residual finding in the ledger. Stop if any residual is load-bearing; otherwise record the ruling and final approved verdict. The controller never performs the fix.

- [ ] **Step 3: Produce fresh final receipts**

Re-run `git diff --check`, the focused Python check, `python3 test_runner.py`, and the runtime verification command. Record a fresh `command`, `exit_code`, `key_output`, and timezone-bearing `timestamp` for each completion claim. Verify branch history/subjects, per-commit path sets, clean tracked/index state, and the preserved SDD artifacts.

- [ ] **Step 4: Re-prove main invariants and preserve all authorized artifacts**

From the main checkout, re-record top-level, `main` branch, HEAD, exact short status, unstaged paths, staged paths, untracked paths, and all four SHA-256 values. Require equality with the preflight snapshot. Leave the linked worktree, branch, and plan-scoped SDD workspace present. Confirm that push, merge, runtime sync, worktree removal, and scratch deletion were not run.

### Task 1: Import and verify the protected Superpowers 6.2.0 delta

**Files:**

- Modify: `locks/superpowers.lock`
- Modify: `scripts/sync_codex_home.sh`
- Modify: `scripts/verify_codex_env.sh`
- Modify: `test_runner.py`
- Read: `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/protected-main-delta.patch`
- Read: `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/protected-main-delta-manifest.txt`
- Write report: `.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/task-1-report.md`

**Interfaces:**

- Consumes: a clean isolated worktree at the plan-only commit and the protected patch whose SHA-256 matches its manifest.
- Produces: one source commit whose tree changes exactly the four allowlist paths and whose behavior passes the focused, full, and Superpowers runtime checks below.

- [ ] **Step 1: Record the acceptance RED probe before applying the patch**

Record that the clean base still contains the prior Superpowers commit/version expectations by checking the four target files for `d884ae04edebef577e82ff7c4e143debd0bbec99` and `6.1.1`, and that the exact target state is not yet fully satisfied. This is an acceptance-state RED probe, not a fabricated failing test; the clean-base test suite is expected to remain green.

- [ ] **Step 2: Validate and apply the protected patch**

Read the expected patch digest from `protected-main-delta-manifest.txt`, compute `shasum -a 256` of the patch, and require exact equality. Run `git apply --check /Users/kezheng/.codex/worktrees/0b59/MyCodexEnv/.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/protected-main-delta.patch`, then run `git apply /Users/kezheng/.codex/worktrees/0b59/MyCodexEnv/.superpowers/sdd/2026-08-05-superpowers-6-2-sdd-workspace/protected-main-delta.patch` from the isolated worktree. Require `git diff --name-only` to print exactly the four allowlist paths, `git status --short` to show exactly those four paths as modified, and `git ls-files --others --exclude-standard` to print nothing.

- [ ] **Step 3: Verify the exact target values and preserved negative probe**

Confirm `locks/superpowers.lock` names commit `3dcbd5c4b48e02263fbf4a3c01e3fe4f81d584d9`; sync and verify scripts require plugin version `6.2.0`; fixtures use commit/version `3dcbd5c4b48e02263fbf4a3c01e3fe4f81d584d9` and `6.2.0`; and the installed-plugin stub inside `test_sync_registers_and_installs_superpowers_plugin` still reports `6.1.1`.

- [ ] **Step 4: Run focused acceptance checks**

Run:

```bash
python3 -c 'import test_runner as t; t.test_sync_registers_and_installs_superpowers_plugin(); t.test_verify_requires_superpowers_plugin_install_not_only_marketplace()'
```

Require both focused tests to print their PASS messages and exit zero.

- [ ] **Step 5: Run source validation**

Run `git diff --check` and then `python3 test_runner.py`. Require the full suite to exit zero with `ran=111 passed=111 skipped=0 failed=0` and `[PASS] all tests`.

- [ ] **Step 6: Run read-only runtime verification**

Run:

```bash
./scripts/verify_codex_env.sh \
  --repo-root "$(pwd)" \
  --codex-home /Users/kezheng/.codex \
  --claude-home /Users/kezheng/.claude
```

Require every `codex_superpowers_*` row to pass. If the command is nonzero, only `codex_hooks_runtime_matches_source` and `codex_skill_compatibility` may be failing; report those two as known unrelated runtime drift without modifying runtime or source.

- [ ] **Step 7: Commit only the exact source write set**

Stage the four allowlist paths explicitly, prove `git diff --cached --name-only` contains exactly those paths, and commit with `chore: upgrade Superpowers to 6.2.0`. Do not amend the plan-only commit. Write the full implementer report with acceptance RED/GREEN evidence, every command/result, changed paths, self-review, and concerns; return only the short SDD status contract.
