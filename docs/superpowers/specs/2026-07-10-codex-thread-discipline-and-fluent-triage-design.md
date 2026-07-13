# Codex Thread Discipline and Fluent Triage Design

**Status:** The historical dual-review loop ended **incomplete** at `max_rounds=15`; it remains historical and is not extended. The subsequent Phase 1 docs-only loop also ended **incomplete** at `max_rounds=5` because of PH1-F1. Under a new explicit authorization, `MCE-20260711-phase2-f1` repaired that finding within the two-document planning scope: closure confirmation reached `10.0/10`, and the final fresh blind reached `10.0/10` with `candidate_pass=true`, `threshold_status=met`, and no new findings. This is a docs-only planning-contract pass; it does not claim implementation, runtime/automation, archive/delete, commit, or push success.

## Current Implementation Continuation (2026-07-11; Incomplete)

The plan contract was restored in the working tree through Task 4. The current
source/runtime execution is separate from the historical committee rounds and
does not alter their scores or round limits.

- Task 2 scanner/tests now follow the plan contract, including the root golden
  fixture, persisted subagent count, canonical UTC ordering, and strict
  fixture no-write checks.
- Task 3 routes `codex-fluent` through the report-only scanner and restores the
  terminal-chat handoff default. Task 4 registers the scanner surface and its
  human-readable mirror (`60/60`).
- The vendored gstack source and runtime were synchronized to upstream
  `1.60.1.0` with preserved backups. No `--delete`, commit, push, archive, or
  task deletion was performed.
- Fresh Task 7 passed isolated fixture, live scan/snapshot, concurrent-write
  report, semantics, timing, focused tests, compatibility, surfaces, and full
  suite. It stopped at `verify_codex_env.sh` because the unrelated,
  user-owned `codex/hooks/shipq_dhf_preprompt.py` source differs from its
  runtime copy. The remaining Task 7 gates and final acceptance are therefore
  incomplete.

## Phase 1 Repair Closure Review (Final Blind Pending)

- **Committee result:** `committee_rating=10.0/10`; `candidate_pass=true`;
  `threshold_status=fail` only because the final fresh blind review remains.
- **Closed findings:** NMF-BLIND-001, NMF-BLIND-002, and NMF-BLIND-003 are
  closed at the planning-contract level. This is docs-only evidence and does
  not claim scanner, runtime, or automation implementation success.
- **Required next step:** execute the final fresh blind review using a
  sanitized packet that excludes this section, all historical scores/verdicts,
  ledger updates, and revision briefs. If it finds a material issue, report
  `incomplete` at `max_rounds=5`; otherwise close Phase 1 as passed.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Phase 1 repair closure review | Python Markdown/fence/Python-Bash syntax/Phase 1 blind-repair contract checker plus `git diff --check` | 0 | `phase1_blind_repair_static=pass`; `spec_lines=329`; `plan_lines=2437`; `task7_literal_gates=19`; no new material finding | `2026-07-11T00:24:33Z` |

## Phase 1 Final Blind (Incomplete; `max_rounds=5` Exhausted)

- **Committee result:** `committee_rating=unavailable` (the transport did not
  provide a calibrated numeric scale); `verdict=incomplete (continue after
  repair)`; `candidate_pass=false`; `threshold_status=not_met`.
- **PH1-F1 (major):** the Task 5 `destination.exists()` check can skip a
  broken child symlink before `lstat`, so future runtime containment is not
  fully fail-closed. This is a planning finding only; no runtime or automation
  command was executed.
- **Stop rule:** Phase 1 consumed all five authorized rounds. Do not add a
  sixth round or implement the fix without a new explicit authorization and a
  new loop envelope.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Phase 1 final fresh blind | Sanitized read-only spec/plan slices supplied to fresh committee; no files modified or runtime/automation payloads run | 0 | `committee_rating=unavailable`; `verdict=incomplete`; `candidate_pass=false`; `threshold_status=not_met`; `PH1-F1=major` | `2026-07-11T00:24:12Z` |

## Phase 2 F1 Round 1 (Repair Required)

- **Committee result:** `committee_rating=6.0/10`; `candidate_pass=false`;
  `threshold_status=fail`. The open PH1-F1 major was confirmed; no new
  finding or rubric challenge was added.
- **Required repair:** make the Task 5 source-manifest walk detect dangling
  child symlinks with an unconditional `lstat()`/explicit missing-path branch,
  and add a literal fault-test contract that proves the guard fails closed.
- **Scope:** docs-only under `MCE-20260711-phase2-f1`; no runtime/automation
  execution or Codex state mutation.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Phase 2 F1 committee round 1 | `rg` source-manifest/rubric inspection plus `git diff --check -- <design> <plan>` | 0 | `committee_rating=6.0`; `candidate_pass=false`; PH1-F1 major confirmed; no new finding | `2026-07-11T00:45:00Z` |

## Phase 2 F1 Repair Closure Review (Bookkeeping Repair Recorded)

- **Committee result:** `committee_rating=7.0/10`; `candidate_pass=false`;
  `threshold_status=fail` only because PH1-F1 was still open in the ledger at
  review time. The technical lstat/fixture repair passed static inspection;
  no new finding or rubric challenge was added.
- **Bookkeeping repair:** keep PH1-F1 explicitly open until a fresh closure
  confirmation observes the repaired status and the same static evidence.
- **Next gate:** the bookkeeping update was followed by a separate closure
  confirmation and final fresh blind within `MCE-20260711-phase2-f1` and
  `max_rounds=5`.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Phase 2 F1 repair closure review | Read-only Python source-manifest/fixture/ledger checker plus `git diff --check -- <design> <plan>` | 0 | `committee_rating=7.0`; `candidate_pass=false`; technical repair pass; ledger/status closure pending | `2026-07-11T00:49:03Z` |

## Phase 2 F1 Closure Confirmation (Final Blind Passed)

- **Committee result:** `committee_rating=10.0/10`; `candidate_pass=true`;
  `threshold_status=fail` only while the final blind was pending. PH1-F1 is
  closed and no material finding remains in the planning ledger.
- **Scope statement:** this is a docs-only planning-contract result. It does
  not claim scanner implementation, runtime overlay, automation, archive,
  deletion, commit, or push success.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Phase 2 F1 closure confirmation | Read-only Python closure checker over both docs plus `git diff --check -- <design> <plan>` | 0 | `committee_rating=10.0`; `candidate_pass=true`; no open material finding; PH1-F1 closed | `2026-07-11T00:51:34Z` |

## Phase 2 F1 Final Blind (Passed)

- **Committee result:** `committee_rating=10.0/10`; `verdict=pass`;
  `candidate_pass=true`; `threshold_status=met`.
- **Blind findings:** none; `rubric_challenges=[]`.
- **Stop rule:** Phase 2 is complete; do not start runtime/automation or
  another review loop without a new explicit authorization.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Phase 2 F1 final fresh blind | Sanitized fresh blind review over the specified slices plus `git diff --check -- <design> <plan>` | 0 | `committee_rating=10.0`; `verdict=pass`; `candidate_pass=true`; `threshold_status=met`; `new_material_findings=[]` | `2026-07-11T00:54:01Z` |
**Repository:** MyCodexEnv
**Delivery boundary:** Design and implementation plan only; implementation is a later task.

## Phase 1 Docs-Only Review Envelope

- **Loop ID:** `MCE-20260710-phase1-r2-rc`.
- **Editable scope:** exactly this design file and the paired implementation
  plan at `docs/superpowers/plans/2026-07-10-codex-thread-discipline-and-fluent-triage.md`.
- **Mode:** `mode_anchor=plan`; review and static verification remain inside
  this mode.
- **Target and limit:** committee target `10/10`, `max_rounds=5`; this is a new
  loop and does not extend or renumber historical Rounds 6–15.
- **Forbidden:** no runtime or automation call, task archive/delete,
  branch/worktree/reflog recovery, commit, or push.
- **Completion:** close the Phase 1 ledger, pass fresh static evidence, and
  obtain a blind final with no new material finding; otherwise report
  `incomplete` at the new limit.

## Phase 2 F1 Docs-Only Review Envelope

- **Loop ID:** `MCE-20260711-phase2-f1`.
- **Editable scope:** exactly this design file and the paired implementation
  plan at `docs/superpowers/plans/2026-07-10-codex-thread-discipline-and-fluent-triage.md`.
- **Mode:** `mode_anchor=plan`; all repair, review, and static verification stay
  in planning mode.
- **Target and limit:** `committee_target=10/10`, `max_rounds=5`; this is a new
  loop and does not extend, renumber, or merge Phase 1 or historical Rounds
  6–15.
- **Starting finding:** PH1-F1, the broken-child-symlink hole in the Task 5
  source-manifest guard.
- **Forbidden:** runtime/automation calls, task archive/delete,
  branch/worktree/reflog recovery, commit, and push.
- **Completion:** close PH1-F1 with fresh static evidence and a blind final
  with no new material finding; otherwise report `incomplete` at this loop's
  limit.

## Problem

Long-running Codex tasks currently accumulate two related forms of drag:

1. A task may drift across repositories or switch between planning, review,
   report-only, and implementation behavior.
2. Active session transcripts can remain large after repeated compactions, while
   the existing weekly maintenance report does not deterministically rank the
   first 20–50 handoff candidates.

The live report-only baseline on 2026-07-10 found 3.6 GB of active sessions,
1,143 active session files, 666 non-subagent sessions older than 30 days, and
24 of the largest 30 sessions already at or above two compactions.

## Goals

- Enforce one task, one repository anchor, and one execution-mode anchor.
- Treat verification as part of the anchored mode rather than a separate mode.
- On the first confirmed compaction, preserve a concise checkpoint.
- On the second confirmed compaction, or when the ordinal cannot be trusted,
  stop normal work and return a resumable chat handoff.
- Add a deterministic, report-only codex-fluent scanner that ranks 20–50 old
  active tasks by transcript size and reports real top-level compaction counts.
- Upgrade the existing weekly maintenance automation instead of creating a
  duplicate automation.
- Preserve the hard safety boundary: no automatic delete, archive, move, prune,
  rotate, normalize, or apply operation.

## Non-Goals

- Do not modify Codex Desktop or claim that it exposes a native post-compaction
  event hook.
- Do not automatically create a new Codex task.
- Do not automatically archive or delete any session.
- Do not infer that a handoff exists solely from a similar filename or title.
- Do not guess a canonical repository from the basename of `cwd`.
- Do not mix this work with worktree cleanup, log rotation, credential cleanup,
  or general Codex-state maintenance.

## Mode and Anchor Contract

Each task freezes an anchor envelope at its start:

```text
THREAD_DISCIPLINE_V1
task_name: <stable task name>
repo_anchor: <canonical absolute repo root | projectless>
repo_anchor_provenance: <git-toplevel | registered-project | explicit-projectless>
mode_anchor: <plan | review | implementation | report-only | handoff>
compaction_ordinal: <0 | 1 | 2+ | unknown>
```

`repo_anchor` is populated only from explicit evidence: `git rev-parse
--show-toplevel`, a registered project root, or an explicit projectless scope.
The task must never turn `Path(cwd).name` into a canonical repository claim.

Research needed to complete a plan and verification needed to prove an
implementation are activities inside the current mode. They do not change the
mode anchor. For every user request, the agent follows this ordered,
fail-closed sequence before starting the requested direction:

1. Resolve `request_repo` and `request_mode` from the explicit request and
   already-available workspace evidence.
2. Compare both values with the frozen anchors.
3. On any mismatch or unresolved value, make no new-direction tool call or
   edit, set `next_action=terminal_chat_handoff`, and return the bounded chat
   handoff.
4. Recommend a new task named `<project>-<YYYYMMDD>-<summary>`.

The resolver may not probe, edit, or otherwise partially start the requested
new direction in order to make a mismatch decision. If the available evidence
cannot resolve an anchor safely, it is an `unknown` mismatch and follows the
same terminal-handoff path.

## Three-Layer Compaction Contract

Compaction handling is deliberately split into three guarantees.

### Layer 1: agent-policy best-effort immediate handling

The active agent carries the anchor envelope across summaries. Every summary or
handoff emitted after compaction must include this durable marker:

```text
THREAD_DISCIPLINE_SUMMARY_V1
repo_anchor: <value>
mode_anchor: <value>
compaction_ordinal: <1 | 2+ | unknown>
next_action: <checkpoint | terminal-chat-handoff>
```

- Confirmed ordinal `0`: continue inside both anchors.
- Confirmed ordinal `1`: refresh the concise checkpoint marker.
- Confirmed ordinal `2+`: stop normal work and return a terminal chat handoff.
- Missing, conflicting, or untrusted ordinal: conservatively treat it as
  `unknown`, stop normal work, and return a terminal chat handoff. Do not assume
  it was only the first compaction.

This layer is best effort because the current Codex Desktop does not expose a
native lifecycle callback that can force execution exactly at compaction time.

### Layer 2: deterministic weekly audit

The report-only scanner parses persisted JSONL line by line with `json.loads`
and counts an event only when the decoded top-level object has
`event.get("type") == "compacted"`. Whitespace style and an embedded
`"type":"compacted"` string inside payload text cannot affect the count.

The weekly job deterministically identifies returned tasks with two or more
persisted compactions and places references to them in a separate
`returned_handoff_queue`. This queue has
`queue_scope="returned-window-only"`: it covers only the primary returned top-N
window and makes no claim about eligible tasks outside that bounded window.
This audits missed immediate handoffs but cannot retroactively stop a task.

### Layer 3: future Desktop lifecycle hard trigger

A future hard guarantee requires a Codex Desktop lifecycle API that supplies
the current thread ID and compaction ordinal and allows a terminal handoff
transition. This design records that dependency; it does not simulate the API
or represent the weekly scanner as an equivalent trigger.

## Handoff Contract

The default artifact is a structured terminal chat handoff. It records the
anchor envelope, current branch and SHA when applicable, user-owned dirty state,
completed work, fresh verification evidence, blockers, constraints, and one
next-safe task.

A repo-native handoff file is allowed only when the original task already
explicitly authorized writing the exact documentation path. The existence of a
repository handoff convention is not write authorization. Archive authorization does not imply file-write authorization. Apply authorization does not imply file-write authorization. Without the exact-path authorization the task returns a terminal chat handoff, remains active, and is not archived. Neither chat nor file handoff authorizes automatic task creation, deletion, or archival.

## Report-Only Scanner

The scanner lives at:

`codex/skills/codex-fluent/scripts/report_active_sessions.py`

It reads only:

- `CODEX_HOME/sessions/**/*.jsonl`
- `CODEX_HOME/session_index.jsonl`

Default behavior:

- `older_than_days`: 30, accepted range `>= 0`
- `limit`: 30, accepted inclusive range 20–50
- exclude subagent sessions
- primary sort: `size_bytes` descending, then `started_at` ascending, then
  `thread_id` ascending for deterministic size ties
- output Markdown for humans or JSON for automation and tests

Eligibility uses UTC instants and the inclusive boundary
`started_at <= now - older_than_days`. The parser rejects timezone-naive,
missing, and invalid timestamps rather than interpreting them in host local
time. Exact-cutoff, one-second-before, one-second-after, and equivalent
timezone-offset timestamps are test cases. Missing or invalid timestamps are
skipped and counted rather than guessed. Eligible timestamps are normalized to
one canonical UTC `Z` representation before output and the deterministic
`started_at` tie-break sort. Equal-size rows whose source offsets represent the
same instant therefore fall through to `thread_id` ascending; raw timestamp
strings are never compared.

Subagent exclusion recognizes only persisted shapes that have been observed:
`payload.thread_source == "subagent"`, or a dictionary `payload.source` that
contains the key `subagent`. An unknown source shape—including an absent
`thread_source` and absent `source` fields—is not guessed to be a subagent: it
remains eligible and is reported with `source_kind="unknown"`.

Each primary candidate contains:

- `primary_rank`
- `thread_id`
- `title`
- `cwd_label`
- `repo_root` (nullable)
- `repo_root_provenance` (`verified-canonical-field` or `unknown`)
- `session_path`
- `started_at`
- `age_days`
- `size_bytes`
- `compaction_count`
- `handoff_required`
- `source_kind`

`cwd_label` is display-only. The current persisted schema usually has no
canonical repository root. `repo_root` is filled only from an explicitly
verified canonical field whose semantics have been established; otherwise it
is `null` with provenance `unknown`. In particular, ordinary fixtures model the
real persisted schema and return `null`; the scanner does not invent
`git_toplevel` or `project_root` as if those fields were currently available.
It does not probe guessed paths or infer repository identity from `cwd`.

The report also contains a separate `returned_handoff_queue`, sorted by
`compaction_count` descending and then `primary_rank` ascending. Each queue item
references the immutable `primary_rank`; it does not overwrite or renumber the
primary size ranking. `queue_scope` is always `returned-window-only`. An
eligible session beyond the requested top-N never appears in this queue, even
when it has a high compaction count.

Malformed session/index lines and invalid/missing timestamps are skipped and
counted by source. The scanner
returns nonzero only when the scan itself cannot complete or arguments are
invalid, not because an individual line is malformed. It opens inputs only for
reading and never writes file content or explicit metadata. Filesystem access
time is outside this guarantee because the OS or mount may update atime on
read. Isolated no-write tests compare the complete fixture-tree path set and
every original file's SHA-256, size, mtime, and mode. A small Markdown golden
test freezes headings, column order, queue scope, and empty-state rendering.

## Weekly Automation

Reuse the unique automation `weekly-codex-maintenance-report` named **Weekly
Codex Maintenance Report**:

- Keep its existing kind, status, schedule, model, reasoning effort, project,
  and execution environment.
- Run codex-fluent in report-only mode with `--older-than-days 30 --limit 30`.
- Display the primary size ranking unchanged.
- Display the bounded `returned_handoff_queue` with `primary_rank` references
  and `queue_scope="returned-window-only"`.
- Include active/archived/worktree sizes and exact blockers.
- Never call apply behavior and never archive or delete.

Before any runtime activation, run a read-only capability preflight: the current
session must actually expose `automation_update`, its formal tool schema must be
read, and the current automation must be viewed. If the tool is absent or the
shape has drifted, stop before runtime or automation mutation; source edits may
remain. Normalize a writable `before` object from the real schema and existing
automation, excluding documented server-managed fields such as `created_at`,
`updated_at`, and `cwds`. Never silently drop a writable required field.

Forward and rollback payloads are derived and asserted against the same live
schema. After mutation, compute a real recursive before/after diff. Only the
requested `prompt` path and an explicitly documented server-managed
`updated_at` path may differ. Save the exact old prompt and schema-valid rollback
payload as evidence. Any mismatch stops the workflow; rollback is not executed
without separate explicit authorization.

## Source, Runtime, and Surface Ownership

- `codex/AGENTS.md` owns the global task-discipline policy.
- `codex/skills/codex-fluent` owns the scanner and skill instructions.
- `docs/surfaces.json` registers the new runtime-visible scanner surface.
- `docs/repo-index.md` mirrors that registered surface for navigation.
- `~/.codex/AGENTS.md` and `~/.codex/skills/codex-fluent` are runtime copies.
- The existing weekly automation remains the only scheduled maintenance report.

This design and its implementation plan do not grant runtime or automation
authority. A later execution task must receive explicit authorization for the
two named runtime targets before it can create a backup or write either target;
it must separately receive authorization before it can update the automation.

Runtime synchronization is targeted and fail closed:

1. Persist backups under
   `~/Documents/Codex/codex-backups/codex-thread-discipline-<timestamp>` until
   acceptance or explicit cleanup.
2. Before writes, use Python `resolve()` and an unconditional `lstat()` walk
   (with only an explicit missing-path branch) to prove the two runtime targets
   are their expected absolute paths, already exist, are not symlinks, and have
   no unexpected parent or child symlink escape. A dangling child symlink must
   be detected rather than skipped by `Path.exists()`.
3. Record the host `rsync --version`, then run
   `rsync -a --dry-run --itemize-changes` and audit every relative path against
   the codex-fluent destination scope. Accept only the documented 9- or
   11-character itemize status tokens; an unknown format stops before a write.
   Then run real `rsync -a` without a pipeline, redirect output to persistent
   evidence, and explicitly inspect its exit status. Forward synchronization
   never uses `--delete`.
4. Compare checksums only for repo-managed source files. Report runtime-only
   inventory separately and do not delete it; directory-wide exact parity is
   not required for an overlay.
5. Before any backup or write, run a disposable broken-child-symlink fault
   fixture through the same guard and require it to fail closed; record the
   receipt and absence of any after-failure marker.
6. If any dry-run, write, or post-write gate fails, stop all later steps, report
   `partial_runtime_state`, and wait for explicit authorization of an exact
   rollback. Do not automatically restore or proceed to automation mutation.

## Verification Strategy

- TDD RED/GREEN policy and scanner tests in `test_runner.py`.
- Fixture coverage includes compact/spaced top-level JSON, embedded strings,
  at least 55 eligible sessions, exact top-N IDs/ranks for limits 20/30/50,
  rejected limits 19/51, inclusive UTC cutoff and offset equivalence,
  invalid/missing/naive timestamp counts, canonical-UTC output, equal-size
  offset-order and same-instant `thread_id` tie-breaks, both known persisted
  subagent shapes, an
  unknown and absent-source shapes, real-schema nullable repo identity, a high-compaction
  candidate outside the returned window, immutable primary ranks, Markdown
  golden output, and complete fixture-tree no-write equality.
- Source-stage focused tests, `py_compile`, and static checks validate the skill
  before runtime activation. `scripts/check_skill_compatibility.py` runs only
  after the overlay and source-file checksum parity; it must not reject the
  intentional pre-activation source/runtime difference.
- `scripts/check_surfaces.py` validates `docs/surfaces.json` and
  `docs/repo-index.md` consistency.
- `git diff --check`, focused tests, `python3 test_runner.py`, and
  `scripts/verify_codex_env.sh` provide repository gates.
- Isolated fixtures require the same complete path set and exact pre/post
  equality for every original session and index input's content checksum, size,
  mtime, and mode. Atime is not asserted.
- Live smoke snapshots only the selected candidate paths. Concurrent writes are
  allowed and reported as `concurrent_write`; whole-session-tree digest equality
  is not a live acceptance gate.

## Known Limitation

Immediate second-compaction handoff remains a best-effort agent-policy action.
The weekly scanner is a deterministic audit, not a lifecycle hook. A hard event
boundary requires the future Desktop API described above.
