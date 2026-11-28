# Harness State

This file is append-only evidence for the generic MyCodexEnv harness runtime.
Stable rules belong in `AGENTS.md`, `README.md`, `docs/repo-index.md`, or
`docs/HARNESS_RUNTIME.md`; session facts and phase transitions are appended here.

State Log rules (same as ShipQ, SHI-637):

- `scripts/harness_checkpoint.py` caps each entry: summary 120 characters,
  verification command 240, key output 320, next safe task 240, at most 12
  changed surfaces. Detail beyond the caps goes in the delivery report.
- When the State Log has more than 30 entries, run
  `python3 scripts/archive_harness_state.py --dry-run --verify-only`, then
  `python3 scripts/archive_harness_state.py --apply --keep-latest 10`. It moves
  the oldest entries verbatim into `docs/harness-state-archive/YYYY-MM.md` and
  refreshes the `Archived State Log Entries` table. Do not move entries by hand.
- Readers check the Current Snapshot, the archive table, and the latest entries.

## Current Snapshot
- phase: ship
- source_of_truth:
  - `AGENTS.md`
  - `docs/repo-index.md`
  - `README.md`
  - `docs/HARNESS_RUNTIME.md`
  - `codex/skills/delivery-harness-framework/SKILL.md`
- blocked_sources: none
- unsafe_inputs: none
- next_safe_task: Merge after CI and review; then a two-worktree trial for the SHI-637 no-conflict acceptance
- required_commands:
  - `python3 test_runner.py`
  - `git diff --check`
  - `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"`
- latest_checkpoint: 2026-11-28T11:19:06-05:00 SHI-637: spec says worktrees skip the State Log; the integration PR appends one entry
- latest_verification: 2026-11-28T11:19:06-05:00 command=dhf_content_drift.py; check_surfaces.py --check-public-nav; harness_refresh_identity.py status; exit_code=0; key_output=no drift; surfaces ok; identity A-D fresh
- compaction_ordinal: 0
- transition_key: p1-2-complete
- gate_decision: continue-to-boundary
- constraints: []
- ownership: {}
- next_action: {"command":"Merge after CI and review; then a two-worktree trial for the SHI-637 no-conflict acceptance"}

## Archived State Log Entries

Older entries were moved verbatim by `scripts/archive_harness_state.py`.

| Month | Archive | Entries | sha256 |
| --- | --- | --- | --- |
| 2026-05 | [harness-state-archive/2026-05.md](harness-state-archive/2026-05.md) | 18 | `c119af48eb9eaae1540dd67d52451b80b852fa27257ec3983a8158d2b469b3b9` |
| 2026-06 | [harness-state-archive/2026-06.md](harness-state-archive/2026-06.md) | 63 | `c8e7fa6137fae425cc3399591c01513034f7a1db845582d2999e66500283be1b` |
| 2026-07 | [harness-state-archive/2026-07.md](harness-state-archive/2026-07.md) | 12 | `8a5839f4a14d7ebee1f6bee7c038889fbe8881430f76e66167735110886da909` |
| 2026-08 | [harness-state-archive/2026-08.md](harness-state-archive/2026-08.md) | 69 | `ebf7a10b843af82f26da3daf858da040d1e898a2cb2005b19fc596db14c78681` |
| 2026-09 | [harness-state-archive/2026-09.md](harness-state-archive/2026-09.md) | 5 | `b69b6f22e38eda4de4df62a705b1f9e390195d04a3b62d4aaf05f456cf0f7f4e` |
| 2026-11 | [harness-state-archive/2026-11.md](harness-state-archive/2026-11.md) | 12 | `52eb7a727108dab80d50bdb7978e41357041033a5503ee1b6f95a96f6e37d08d` |

## State Log

### 2026-11-27T17:04:57-05:00
- phase: ship
- event: checkpoint
- summary: SHI-637: the full sync no longer drops owner and host settings from config.toml and no longer writes into the host-owned skills/.system. A rehearsal against a copy of the reference runtime showed the config merge kept only an allowlist of tables, so six runtime-only tables would have been removed, and the skills copy would have overwritten the host's bundled system skills with the repository snapshot. The merge now keeps every table and top-level key the template does not define, refuses a result that is not valid TOML, and prints what it kept. Hook registration still comes only from the template.
- git:
  - branch: codex/shi-637-sync-preserve-20261127
  - latest_commit: d38d268
  - dirty_status: dirty
  - dirty_count: 2
- changed_surfaces:
  - `scripts/sync_codex_home.sh`
  - `test_runner.py`
- verification:
  - command: `python3 test_runner.py (cloud clone, no Codex CLI)`
  - exit_code: 0
  - key_output: 165 pass; the 5 failures and 4 skips are the same set as on main in this environment; test_sync_preserves_runtime_plugin_state fails on main with the new assertions and passes with the change
- blockers:
  - none
- next_safe_task: Owner reruns the full-sync rehearsal against a copy of the runtime on this branch's merge; no full sync against the real runtime before that
- checkpoint_data: {"constraints":["The full sync has still never run against the real runtime"],"next_action":{"command":"Owner reruns the full-sync rehearsal against a copy of the runtime on this branch's merge; no full sync against the real runtime before that"},"ownership":{},"phase":"ship","schema":"dhf_checkpoint_v1","verification_evidence":{"command":"python3 test_runner.py (cloud clone, no Codex CLI)","exit_code":0,"freshness":"fresh","key_output":"165 pass; the 5 failures and 4 skips are the same set as on main in this environment; test_sync_preserves_runtime_plugin_state fails on main with the new assertions and passes with the change","timestamp":"2026-11-27T17:04:57-05:00"}}

### 2026-11-27T17:49:47-05:00
- phase: ship
- event: checkpoint
- summary: SHI-637: final shape of the config.toml merge in the full sync. Review found that matching lines could not read every valid spelling. The merge now scans statements, compares tables by parsed key path, and checks its text result against a merge worked out on parsed data. If they differ, the parsed result is written and the sync says comments were not kept. Only an existing config.toml that is not valid TOML stops the sync. This replaces the earlier entry's statement that the merge refuses on an invalid result.
- git:
  - branch: codex/shi-637-sync-preserve-20261127
  - latest_commit: f33ebb5
  - dirty_status: clean
  - dirty_count: 0
- changed_surfaces:
  - `scripts/sync_codex_home.sh`
  - `test_runner.py`
- verification:
  - command: `python3 test_runner.py (cloud clone, no Codex CLI); CI gate on f33ebb5`
  - exit_code: 0
  - key_output: 165 pass, same 5 failures and 4 skips as main in this environment; CI gate success; Codex review reports no findings on f33ebb5; 18 hand-run spellings of an existing config.toml merge to the expected settings, 16 by text and 2 by the parsed fallback
- blockers:
  - none
- next_safe_task: Owner runs the full suite on the host and reruns the full-sync rehearsal against a copy of the runtime; no full sync against the real runtime before that
- checkpoint_data: {"constraints":["The full sync has still never run against the real runtime","Not run on a host with the Codex CLI"],"next_action":{"command":"Owner runs the full suite on the host and reruns the full-sync rehearsal against a copy of the runtime; no full sync against the real runtime before that"},"ownership":{},"phase":"ship","schema":"dhf_checkpoint_v1","verification_evidence":{"command":"python3 test_runner.py (cloud clone, no Codex CLI); CI gate on f33ebb5","exit_code":0,"freshness":"fresh","key_output":"165 pass, same 5 failures and 4 skips as main in this environment; CI gate success; Codex review reports no findings on f33ebb5; 18 hand-run spellings of an existing config.toml merge to the expected settings, 16 by text and 2 by the parsed fallback","timestamp":"2026-11-27T17:49:47-05:00"}}

### 2026-11-27T20:03:01-05:00
- phase: ship
- event: checkpoint
- summary: SHI-637: full sync keeps the owner's runtime choices. Template model gpt-6.2-sol and reasoning effort low (owner 2026-11-27 19:59). Machine-local remote hosts move to ~/.codex/remote-hosts.local.md, which sync never reads or writes; AGENTS.md, remote-access.md and remote-hosts.md point to it
- git:
  - branch: codex/shi-637-runtime-keep-20261127
  - latest_commit: 1b1283b
  - dirty_status: dirty
  - dirty_count: 5
- changed_surfaces:
  - `codex/config.template.toml`
  - `codex/AGENTS.md`
  - `codex/remote-access.md`
  - `codex/remote-hosts.md`
  - `test_runner.py`
- verification:
  - command: `PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py (cloud clone, Python 3.13, no Codex CLI)`
  - exit_code: 1
  - key_output: ran=174 passed=165 skipped=4 failed=5; the same five failures and four skips as main in this environment; test_sync_renders_template_and_copies_skills passes with the new remote-hosts.local.md assertions; third rehearsal at 1b1283b: owner host 174/174, sync_exit=0, no config entry lost, skills.config merged by path
- blockers:
  - none
- next_safe_task: After CI and a clean Codex review: owner approves the codex/ digest, regenerates identity fixtures, moves his machine-local host entry from ~/.codex/remote-hosts.md into ~/.codex/remote-hosts.local.md, then decides on the full sync
- checkpoint_data: {"constraints":["codex/ changed: identity layer A is stale until the owner runs harness_refresh_identity.py refresh --approve","The owner's machine-local host entry stays only in the live ~/.codex/remote-hosts.md until he moves it; a full sync before that removes it (a backup is written)","codex exec with gpt-6.2-sol was rejected on this account earlier on 2026-11-27 (model_not_in_accessible_catalog); not re-tested","MyCodexEnv is public: host metadata for the owner's machines stays out of the repository"],"next_action":{"command":"After CI and a clean Codex review: owner approves the codex/ digest, regenerates identity fixtures, moves his machine-local host entry from ~/.codex/remote-hosts.md into ~/.codex/remote-hosts.local.md, then decides on the full sync"},"ownership":{},"phase":"ship","schema":"dhf_checkpoint_v1","verification_evidence":{"command":"PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py (cloud clone, Python 3.13, no Codex CLI)","exit_code":1,"freshness":"fresh","key_output":"ran=174 passed=165 skipped=4 failed=5; the same five failures and four skips as main in this environment; test_sync_renders_template_and_copies_skills passes with the new remote-hosts.local.md assertions; third rehearsal at 1b1283b: owner host 174/174, sync_exit=0, no config entry lost, skills.config merged by path","timestamp":"2026-11-27T20:03:01-05:00"}}

### 2026-11-27T20:41:48-05:00
- phase: ship
- event: checkpoint
- summary: SHI-637: retire Sepia and the Codex side of claude-code-workflow (owner 2026-11-27 20:35). Removed codex/skills/sepia*, codex/skills/ccwf-*, codex/workflow/ and locks/sepia.lock; sync no longer deploys ~/.codex/workflow; verify drops the Codex workflow and ccwf checks; import never brings them back; writing routing names no writing skill except an explicit humanizer
- git:
  - branch: codex/shi-637-retire-sepia-ccwf-20261127
  - latest_commit: bb5b039
  - dirty_status: dirty
  - dirty_count: 58
- changed_surfaces:
  - `codex/skills`
  - `codex/workflow`
  - `scripts/sync_codex_home.sh`
  - `scripts/verify_codex_env.sh`
  - `docs/LIFECYCLE_SKILL_ROUTING.md`
  - `docs/evals/writing-skill-routing-v1.json`
  - `test_runner.py`
- verification:
  - command: `PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py (cloud clone, Python 3.13, no Codex CLI); dhf_content_drift.py; check_surfaces.py --check-public-nav`
  - exit_code: 1
  - key_output: ran=174 passed=165 skipped=4 failed=5, the same five failures and four skips as main in this environment; drift 0 open findings; surfaces pass
- blockers:
  - none
- next_safe_task: After CI and a clean Codex review: owner approves the codex/ digest; then the gstack retirement PR, then the public pages
- checkpoint_data: {"constraints":["Runtime copies under ~/.codex/skills and ~/.codex/workflow stay until the owner disables them; sync never deletes","The Claude side of claude-code-workflow (claude/workflow, the CLAUDE.md integration block, vendor/claude-code-workflow) is unchanged","The public lifecycle-skill-routing page still lists Sepia until the public-pages PR"],"next_action":{"command":"After CI and a clean Codex review: owner approves the codex/ digest; then the gstack retirement PR, then the public pages"},"ownership":{},"phase":"ship","schema":"dhf_checkpoint_v1","verification_evidence":{"command":"PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py (cloud clone, Python 3.13, no Codex CLI); dhf_content_drift.py; check_surfaces.py --check-public-nav","exit_code":1,"freshness":"fresh","key_output":"ran=174 passed=165 skipped=4 failed=5, the same five failures and four skips as main in this environment; drift 0 open findings; surfaces pass","timestamp":"2026-11-27T20:41:48-05:00"}}

### 2026-11-27T20:51:56-05:00
- phase: ship
- event: checkpoint
- summary: SHI-637: retire gstack (owner 2026-11-27 20:35). Removed codex/skills/gstack, 35 gstack-* wrappers, the nine short-name imports, external_gstack_runtime.py, the vendor sync, daily refresh prepare and merge scripts, and the daily refresh denylist. Sync no longer classifies external gstack (exit 79 gone). check_skill_compatibility skips retired runtime copies. DHF routes product, planning, design, QA, security, review, PR, docs, handoff and retro stages to existing non-gstack skills (owner choice). Public pages, routing doc, README and C-layer registries updated
- git:
  - branch: codex/shi-637-retire-gstack-20261127
  - latest_commit: 6265c03
  - dirty_status: dirty
  - dirty_count: 1327
- changed_surfaces:
  - `codex/skills`
  - `scripts/sync_codex_home.sh`
  - `scripts/check_skill_compatibility.py`
  - `codex/skills/delivery-harness-framework`
  - `docs/LIFECYCLE_SKILL_ROUTING.md`
  - `docs/surfaces.json`
  - `docs/repo-index.md`
  - `docs/HARNESS_RUNTIME.md`
  - `test_runner.py`
- verification:
  - command: `PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py (cloud clone, Python 3.13, no Codex CLI); dhf_content_drift.py --json; check_surfaces.py --check-public-nav --json`
  - exit_code: 1
  - key_output: ran=160 passed=151 skipped=4 failed=5 (14 gstack tests removed); the same five environment failures and four skips as main; drift ok count 0; surfaces ok
- blockers:
  - none
- next_safe_task: After CI and a clean Codex review: owner approves the codex/ digest, then disables the retired runtime copies through skills.config, stops the gstack-dhf-daily-refresh automation, and decides on the full sync
- checkpoint_data: {"constraints":["Runtime copies of retired skills and ~/.gstack stay on disk; sync never deletes them","The gstack-dhf-daily-refresh Codex automation in the owner's runtime calls scripts this change deletes; the owner must stop it","The automation_execution_clone source role remains in the Phase-0 source guard; removing it is a separate change","Historical records under tasks/, docs/plans, docs/goals, docs/decisions and docs/skill-governance-20260608.md keep their gstack references (owner choice)"],"next_action":{"command":"After CI and a clean Codex review: owner approves the codex/ digest, then disables the retired runtime copies through skills.config, stops the gstack-dhf-daily-refresh automation, and decides on the full sync"},"ownership":{},"phase":"ship","schema":"dhf_checkpoint_v1","verification_evidence":{"command":"PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py (cloud clone, Python 3.13, no Codex CLI); dhf_content_drift.py --json; check_surfaces.py --check-public-nav --json","exit_code":1,"freshness":"fresh","key_output":"ran=160 passed=151 skipped=4 failed=5 (14 gstack tests removed); the same five environment failures and four skips as main; drift ok count 0; surfaces ok","timestamp":"2026-11-27T20:51:56-05:00"}}

### 2026-11-27T21:39:38-05:00
- phase: ship
- event: checkpoint
- summary: SHI-637: owner approved digest 5a6baf4e for retiring Sepia, ccwf and gstack. Owner host after approval: 158 of 160 passed; the two failures are the runtime-boundary checks (golden corpus slice 4 and paired gate focused CLI) reporting runtime_state=drifted because the live runtime differs from source in exactly the two files this change edits (delivery-harness-framework SKILL.md and evals.json). Before this change the runtime was exactly promoted. A full sync restores it. Retired skills disabled in the runtime config (45 entries added, 26 already listed); the gstack daily refresh automation is already PAUSED. .gitignore keeps leftover codex/workflow data out of git
- git:
  - branch: codex/shi-637-retire-gstack-20261127
  - latest_commit: 9663de5
  - dirty_status: dirty
  - dirty_count: 1
- changed_surfaces:
  - `runtime-approvals/approved-source-digests.txt`
  - `tests/fixtures`
  - `.gitignore`
- verification:
  - command: `PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py (owner host, after refresh --approve)`
  - exit_code: 1
  - key_output: ran=160 passed=158 skipped=0 failed=2; promotion_difference_paths=['codex/skills/delivery-harness-framework/SKILL.md', 'codex/skills/delivery-harness-framework/evals/evals.json']
- blockers:
  - none
- next_safe_task: Merge PR #61 once CI and review pass; owner decides on the full sync, after which the two runtime-boundary tests should pass on the owner host
- checkpoint_data: {"constraints":["The two runtime-boundary tests stay red on the owner host until the runtime receives the new delivery-harness-framework files","The owner's Mac worktree is left on the feature branch with the approval files modified; it needs git checkout -- . and git checkout main"],"next_action":{"command":"Merge PR #61 once CI and review pass; owner decides on the full sync, after which the two runtime-boundary tests should pass on the owner host"},"ownership":{},"phase":"ship","schema":"dhf_checkpoint_v1","verification_evidence":{"command":"PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py (owner host, after refresh --approve)","exit_code":1,"freshness":"fresh","key_output":"ran=160 passed=158 skipped=0 failed=2; promotion_difference_paths=['codex/skills/delivery-harness-framework/SKILL.md', 'codex/skills/delivery-harness-framework/evals/evals.json']","timestamp":"2026-11-27T21:39:38-05:00"}}

### 2026-11-27T22:15:34-05:00
- phase: ship
- event: checkpoint
- summary: SHI-631: hook on/off belongs to the owner. Full sync moves [hooks.state] entries to follow their hook's command when template positions change and drops entries that point at no registered hook; status --runtime and the conformance doctor flag a disabled Guard; verify lists owner-disabled hooks and still passes; the spec says so. No switch command an agent can run (direction decision: codex-task is not a hard owner boundary)
- git:
  - branch: codex/shi-631-hook-state-by-command-20261127
  - latest_commit: 59a44d4
  - dirty_status: dirty
  - dirty_count: 8
- changed_surfaces:
  - `scripts/sync_codex_home.sh`
  - `scripts/harness_status_runtime.py`
  - `scripts/dhf_conformance.py`
  - `scripts/verify_codex_env.sh`
  - `docs/dhf-spec.md`
  - `test_runner.py`
- verification:
  - command: `PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py (cloud clone, Python 3.13, no Codex CLI)`
  - exit_code: 1
  - key_output: ran=162 passed=153 skipped=4 failed=5, the same environment failures as main; test_sync_moves_hook_state_with_its_hook fails on main's sync script and passes here; test_owner_disabled_hooks_are_reported_not_failed passes; drift 0; surfaces ok
- blockers:
  - none
- next_safe_task: Merge after CI and a clean Codex review; the next full sync on the owner host drops the stale user_prompt_submit:0:2 state entry; owner toggles dhf_preprompt.py with /hooks to close the acceptance
- checkpoint_data: {"constraints":["trusted_hash is carried unchanged when an entry moves; whether Codex asks to re-trust a moved hook is not measured","Only [hooks.state.\"...\"] header-form entries are moved; other spellings stay as they are"],"next_action":{"command":"Merge after CI and a clean Codex review; the next full sync on the owner host drops the stale user_prompt_submit:0:2 state entry; owner toggles dhf_preprompt.py with /hooks to close the acceptance"},"ownership":{},"phase":"ship","schema":"dhf_checkpoint_v1","verification_evidence":{"command":"PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py (cloud clone, Python 3.13, no Codex CLI)","exit_code":1,"freshness":"fresh","key_output":"ran=162 passed=153 skipped=4 failed=5, the same environment failures as main; test_sync_moves_hook_state_with_its_hook fails on main's sync script and passes here; test_owner_disabled_hooks_are_reported_not_failed passes; drift 0; surfaces ok","timestamp":"2026-11-27T22:15:34-05:00"}}

### 2026-11-27T22:45:44-05:00
- phase: ship
- event: checkpoint
- summary: SHI-633 (re-appended after merging main, which added the SHI-631 entry): the compaction probe uses host PostCompact events instead of transcript scans. compaction_recorder.py on PostCompact and a second SessionStart group keeps per-session ordinals; compaction_probe.py injects only for complete records and counts misses without evidence. Owner approved digest caca9a75 (owner host 160/160 before and after). The batch sync from the unmerged branch was refused (source transition rejected: forward source is not the fresh remote tip), so the runtime is unchanged until a sync from main after merge
- git:
  - branch: codex/shi-633-postcompact-recorder-20261127
  - latest_commit: 0940f48
  - dirty_status: dirty
  - dirty_count: 10
- changed_surfaces:
  - `codex/hooks/compaction_recorder.py`
  - `codex/hooks/compaction_probe.py`
  - `codex/config.template.toml`
  - `scripts/harness_eval.py`
  - `runtime-approvals/approved-source-digests.txt`
- verification:
  - command: `PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py (owner host, after refresh --approve)`
  - exit_code: 0
  - key_output: ran=160 passed=160 skipped=0 failed=0; sync_exit=1 source transition rejected: unknown (forward source is not the fresh remote tip); ~/.codex/hooks/compaction_recorder.py absent
- blockers:
  - none
- next_safe_task: Merge PR #62 after CI and review; owner runs the full sync from main; then /compact in a new session should show compaction_ordinal=1
- checkpoint_data: {"constraints":["Full sync only accepts the fresh remote tip as its source: run it after merge, from main"],"next_action":{"command":"Merge PR #62 after CI and review; owner runs the full sync from main; then /compact in a new session should show compaction_ordinal=1"},"ownership":{},"phase":"ship","schema":"dhf_checkpoint_v1","verification_evidence":{"command":"PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py (owner host, after refresh --approve)","exit_code":0,"freshness":"fresh","key_output":"ran=160 passed=160 skipped=0 failed=0; sync_exit=1 source transition rejected: unknown (forward source is not the fresh remote tip); ~/.codex/hooks/compaction_recorder.py absent","timestamp":"2026-11-27T22:45:44-05:00"}}

### 2026-11-27T23:06:42-05:00
- phase: ship
- event: checkpoint
- summary: SHI-637: wrote the parallel-work rules into the DHF spec (dhf-spec.md and the CN/EN pages, section 9): non-overlapping write sets, the lead agent integrates and verifies, a shared repository is not shared write rights, no agent changes a workspace while the owner runs commands there, worktree receipts go in the delivery report and the main session appends one State Log entry at merge. Added a gap entry: no tool enforces these rules and each PR still appends its own State Log entry
- git:
  - branch: codex/shi-637-parallel-rules-20261128
  - latest_commit: 1da3dd1
  - dirty_status: dirty
  - dirty_count: 3
- changed_surfaces:
  - `docs/dhf-spec.md`
  - `docs/dhf-spec-cn.html`
  - `docs/dhf-spec-en.html`
- verification:
  - command: `python3 scripts/dhf_content_drift.py --repo-root . ; python3 scripts/check_surfaces.py --repo-root . --check-public-nav --json`
  - exit_code: 0
  - key_output: no drift, 0 open findings; check_surfaces ok true
- blockers:
  - none
- next_safe_task: Merge after CI and a clean Codex review; next SHI-637 item: State Log field caps and archiving following ShipQ
- checkpoint_data: {"constraints":[],"next_action":{"command":"Merge after CI and a clean Codex review; next SHI-637 item: State Log field caps and archiving following ShipQ"},"ownership":{},"phase":"ship","schema":"dhf_checkpoint_v1","verification_evidence":{"command":"python3 scripts/dhf_content_drift.py --repo-root . ; python3 scripts/check_surfaces.py --repo-root . --check-public-nav --json","exit_code":0,"freshness":"fresh","key_output":"no drift, 0 open findings; check_surfaces ok true","timestamp":"2026-11-27T23:06:42-05:00"}}

### 2026-11-27T23:12:00-05:00
- phase: ship
- event: checkpoint
- summary: SHI-637 (re-appended after merging main): removed the automation_execution_clone source role from the sync source guard. Allowed roles are git_head and caller_worktree; any other role is refused with source_role_path_mismatch. The edit to docs/HARNESS_RUNTIME.md makes Layer C stale; the owner refreshes Layer C on this branch before merge
- git:
  - branch: codex/shi-637-drop-automation-source-role-20261128
  - latest_commit: a71ec64
  - dirty_status: dirty
  - dirty_count: 4
- changed_surfaces:
  - `scripts/sync_codex_home.sh`
  - `docs/HARNESS_RUNTIME.md`
  - `test_runner.py`
- verification:
  - command: `python3 -c 'import test_runner as t; t.test_sync_phase0_pre_preflight_matrix()'; CI gate on a71ec64`
  - exit_code: 1
  - key_output: preflight matrix PASS; CI ran=162 passed=156 failed=1: test_harness_refresh_identity_status_current_head (Layer C stale)
- blockers:
  - none
- next_safe_task: Owner runs _to_delete/batch-1128a.sh (Layer C refresh on this branch); then CI and review, merge
- checkpoint_data: {"constraints":[],"next_action":{"command":"Owner runs _to_delete/batch-1128a.sh (Layer C refresh on this branch); then CI and review, merge"},"ownership":{},"phase":"ship","schema":"dhf_checkpoint_v1","verification_evidence":{"command":"python3 -c 'import test_runner as t; t.test_sync_phase0_pre_preflight_matrix()'; CI gate on a71ec64","exit_code":1,"freshness":"fresh","key_output":"preflight matrix PASS; CI ran=162 passed=156 failed=1: test_harness_refresh_identity_status_current_head (Layer C stale)","timestamp":"2026-11-27T23:12:00-05:00"}}

### 2026-11-28T10:16:49-05:00
- phase: ship
- event: checkpoint
- summary: SHI-637: State Log field caps and archive (ShipQ rules); 179 old entries moved verbatim, 10 kept
- git:
  - branch: codex/shi-637-state-log-caps-archive-20261128
  - latest_commit: bd4fa94
  - dirty_status: dirty
  - dirty_count: 5
- changed_surfaces:
  - `scripts/harness_checkpoint.py`
  - `scripts/archive_harness_state.py`
  - `docs/harness-state.md`
  - `docs/harness-state-archive`
  - `test_runner.py`
- verification:
  - command: `archive --apply --keep-latest 10; parity check; 4 checkpoint/archive/bearing tests`
  - exit_code: 0
  - key_output: entries=189 moved=179 kept=10; verbatim: True; field limits, archive, checkpoint helper, session bearing PASS
- blockers:
  - none
- next_safe_task: Merge after CI and review; next SHI-637 items: merge-time State Log append, sync dry-run mode
- checkpoint_data: {"constraints":[],"next_action":{"command":"Merge after CI and review; next SHI-637 items: merge-time State Log append, sync dry-run mode"},"ownership":{},"phase":"ship","schema":"dhf_checkpoint_v1","verification_evidence":{"command":"archive --apply --keep-latest 10; parity check; 4 checkpoint/archive/bearing tests","exit_code":0,"freshness":"fresh","key_output":"entries=189 moved=179 kept=10; verbatim: True; field limits, archive, checkpoint helper, session bearing PASS","timestamp":"2026-11-28T10:16:49-05:00"}}

### 2026-11-28T10:32:56-05:00
- phase: ship
- event: checkpoint
- summary: SHI-637: sync --dry-run previews a full sync in a sandbox copy; writes nothing to the Codex home
- git:
  - branch: codex/shi-637-sync-dry-run-20261128
  - latest_commit: e4096b9
  - dirty_status: dirty
  - dirty_count: 4
- changed_surfaces:
  - `scripts/sync_dry_run.py`
  - `scripts/sync_codex_home.sh`
  - `README.md`
  - `test_runner.py`
- verification:
  - command: `python3 -c 'import test_runner as t; t.test_sync_*()' (all sync tests, cloud clone)`
  - exit_code: 0
  - key_output: test_sync_dry_run_matches_real_sync PASS: preview set == real sync change set; home unchanged; all sync tests PASS
- blockers:
  - none
- next_safe_task: Merge after CI and review; owner runs sync --dry-run on Mac Studio (SHI-637 item 5)
- checkpoint_data: {"constraints":[],"next_action":{"command":"Merge after CI and review; owner runs sync --dry-run on Mac Studio (SHI-637 item 5)"},"ownership":{},"phase":"ship","schema":"dhf_checkpoint_v1","verification_evidence":{"command":"python3 -c 'import test_runner as t; t.test_sync_*()' (all sync tests, cloud clone)","exit_code":0,"freshness":"fresh","key_output":"test_sync_dry_run_matches_real_sync PASS: preview set == real sync change set; home unchanged; all sync tests PASS","timestamp":"2026-11-28T10:32:56-05:00"}}

### 2026-11-28T11:19:06-05:00
- phase: ship
- event: checkpoint
- summary: SHI-637: spec says worktrees skip the State Log; the integration PR appends one entry
- git:
  - branch: codex/shi-637-state-log-integration-rule-20261128
  - latest_commit: 5bcf9f3
  - dirty_status: dirty
  - dirty_count: 3
- changed_surfaces:
  - `docs/dhf-spec.md`
  - `docs/dhf-spec-cn.html`
  - `docs/dhf-spec-en.html`
- verification:
  - command: `dhf_content_drift.py; check_surfaces.py --check-public-nav; harness_refresh_identity.py status`
  - exit_code: 0
  - key_output: no drift; surfaces ok; identity A-D fresh
- blockers:
  - none
- next_safe_task: Merge after CI and review; then a two-worktree trial for the SHI-637 no-conflict acceptance
- checkpoint_data: {"constraints":[],"next_action":{"command":"Merge after CI and review; then a two-worktree trial for the SHI-637 no-conflict acceptance"},"ownership":{},"phase":"ship","schema":"dhf_checkpoint_v1","verification_evidence":{"command":"dhf_content_drift.py; check_surfaces.py --check-public-nav; harness_refresh_identity.py status","exit_code":0,"freshness":"fresh","key_output":"no drift; surfaces ok; identity A-D fresh","timestamp":"2026-11-28T11:19:06-05:00"}}
