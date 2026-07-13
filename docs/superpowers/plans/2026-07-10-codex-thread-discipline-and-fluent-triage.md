# Codex Thread Discipline and Fluent Triage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce one-repo/one-mode Codex tasks, make the second-compaction chat handoff conservative and auditable, and upgrade codex-fluent plus the existing weekly report to rank the largest 20–50 old active tasks without mutating Codex state.

**Architecture:** Use three explicit layers: agent-policy best-effort immediate handoff, a deterministic weekly persisted-session audit, and a documented future Desktop lifecycle API hard trigger. Put the behavioral contract in the repo-managed global AGENTS source, implement ranking as a pure read-only codex-fluent CLI, and update only the existing weekly automation. Tests use isolated `CODEX_HOME` fixtures; runtime activation uses one-file AGENTS backup/copy plus a targeted skill overlay without deletion.

**Tech Stack:** Python 3 standard library, JSONL, Markdown, shell verification, existing `test_runner.py` registry, `docs/surfaces.json`, Codex automation API.

**Dual-review traceability:** The user expanded `max_rounds` from 5 to 10 on
2026-07-10. Round 6 scored 6/10 with `candidate_pass=false`. This revision
repairs BCF-001, BCF-003, BCF-006, BCF-007, BCF-008, and the UTC/tie-break
minor finding. The fresh round-7 Codex blind review found BFC-001 (major)
against fail-closed execution. Round 8 re-reviewed its bounded repair and kept
BFC-001 open as a major with `candidate_pass=false`; the final dual-review
outcome was **incomplete** under the previous limit. Round 8 Claude review was
not permitted because the round-7 candidate gate was not met. A post-closeout
planning-only remediation now specifies the missing unified application-tool /
Task 7 gate protocol. The user has authorized two additional rounds: Round 9
is a fresh Codex blind review; only a Round-9 candidate pass permits the fresh
Claude blind review in Round 10. Round 9 reached candidate pass; Round 10
returned no required structured fields after the protocol's malformed-response
retry and budget-ladder recovery, so the final outcome is **incomplete** with
no round beyond 10 authorized. The user later authorized continuation up to 15;
a fresh schema-constrained Round 11 again produced the same malformed-response
failure after its allowed retry. A user-authorized, read-only diagnosis then
showed that the same CLI can return a schema-valid result for the complete two-
document evidence at `$2.00`; fresh Round 12 nevertheless returned neither a
result object nor a post-command receipt. The user then changed review transport
by manually supplying a sanitized Claude Round-13 re-review. Its `9.3/10`
`continue` response raised three bounded documentation minors. After a
docs-only repair, fresh Codex Round 14 reached candidate pass at `9.7/10`.
Round 15 returned a fresh manual Claude blind-final `9.6/10` with
`verdict=continue`, three new minor findings, and a rubric challenge. The
independent scores remain separate. `max_rounds=15` is exhausted, so the final
outcome is `incomplete`; do not begin a Round 16 without new explicit
authorization in that historical loop. The user subsequently authorized a
separate docs-only Phase 1 loop with the envelope below. After Phase 1 ended
incomplete on PH1-F1, the user authorized a separate Phase 2 F1 repair loop.

## Current Implementation Continuation (2026-07-11; Incomplete)

This execution continuation is separate from the historical review rounds and
does not change their scores, `max_rounds`, or blind-final records.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Task 2 plan-contract RED | focused scanner tests against the pre-restore implementation | 1 | missing `excluded_subagent_count` | `2026-07-11T14:57:19Z` |
| Task 2 plan-contract GREEN | focused scanner tests | 0 | active report, boundaries, selection, timestamp/source, golden all passed | `2026-07-11T14:58:18Z` |
| Task 3 contract RED | `test_codex_fluent_report_only_contract()` | 1 | missing `scripts/report_active_sessions.py` in current SKILL contract | `2026-07-11T14:58:46Z` |
| Task 3 contract GREEN | skill/checklist contract, py_compile, scoped diff check | 0 | report-only contract passed | `2026-07-11T14:59:26Z` |
| Task 4 surface RED | `python3 scripts/check_surfaces.py --repo-root "$(pwd)" --json` after manifest entry | 1 | `in_manifest_not_index` for scanner | `2026-07-11T14:59:38Z` |
| Task 4 surface GREEN | surface checker plus scoped diff check | 0 | `manifest_count=60`, `repo_index_count=60`, `ok=true` | `2026-07-11T15:00:09Z` |
| gstack latest dry-run | `python3 scripts/sync_gstack_vendor.py ... --dry-run --json` | 0 | upstream `version=1.60.1.0`, `diff_files=9`, `needs_update=true` | `2026-07-11T15:03:14Z` |
| gstack source sync | `python3 scripts/sync_gstack_vendor.py ... --keep-backup --json` | 0 | source synced to `1.60.1.0`; backup preserved outside `codex/skills` | `2026-07-11T15:03:25Z` |
| runtime compatibility | `python3 scripts/check_skill_compatibility.py ...` | 0 | `errors=0`, `managed_missing=0`, `managed_drifted=0` | `2026-07-11T15:05:35Z` |
| Task 7 fresh acceptance | labelled Task 7 gates through `task7-full-suite` | 0 | isolated/live/focused/compatibility/surfaces/full suite passed; `73/73` | `2026-07-11T15:10:04Z` |
| Task 7 environment gate | `./scripts/verify_codex_env.sh ...` | 1 | `FAIL:codex_hook_shipq_dhf_preprompt_runtime_matches_source` | `2026-07-11T15:10:09Z` |

The Task 7 shell stopped fail-closed at `verify_codex_env.sh`; no later
`task7-diff-check` claim was made. The failure is an unrelated user-owned
source/runtime hook mismatch and was not overwritten. The current execution
therefore remains `incomplete`; runtime hook synchronization or an explicit
scope exception requires a separate decision.

## Phase 1 Docs-Only Review Envelope

- **Loop ID:** `MCE-20260710-phase1-r2-rc`.
- **Editable files:** exactly the paired design and plan files named in the
  request; no other source, runtime, automation, handoff, or script file is in
  scope.
- **Mode:** `mode_anchor=plan`; all repair, review, and static verification stay
  in planning mode.
- **Target and limit:** `committee_target=10/10`, `max_rounds=5`; this new loop
  does not extend, renumber, or overwrite historical Rounds 6–15.
- **Forbidden:** runtime/automation calls, task archive/delete,
  branch/worktree/reflog recovery, commit, and push.
- **Completion gate:** close R2-NMF-001–003, RC-001, and PH1-GOV-001; pass
  fresh static checks; and obtain a separate blind final with no new material
  finding. Otherwise report `incomplete` at five rounds.

## Phase 2 F1 Docs-Only Review Envelope

- **Loop ID:** `MCE-20260711-phase2-f1`.
- **Editable files:** exactly this plan and its paired design file at
  `docs/superpowers/specs/2026-07-10-codex-thread-discipline-and-fluent-triage-design.md`;
  no other source, runtime, automation, handoff, or script file is in scope.
- **Mode:** `mode_anchor=plan`; all repair, review, and static verification stay
  in planning mode.
- **Target and limit:** `committee_target=10/10`, `max_rounds=5`; this is a new
  loop and does not extend, renumber, or merge Phase 1 or historical Rounds
  6–15.
- **Starting finding:** PH1-F1, the broken-child-symlink hole in the Task 5
  source-manifest guard.
- **Forbidden:** runtime/automation calls, task archive/delete,
  branch/worktree/reflog recovery, commit, and push.
- **Completion gate:** close PH1-F1 with fresh static evidence and a blind
  final with no new material finding; otherwise report `incomplete` at this
  loop's five-round limit.

## Global Constraints

- One task freezes one evidence-backed `repo_anchor` and one `mode_anchor`.
- Before any tool call for each user request, resolve `request_repo` and
  `request_mode` from the direct request and already-available workspace
  evidence, then compare them with both anchors. A mismatch or unresolved
  anchor forbids the new direction's tools/edits, sets
  `next_action=terminal_chat_handoff`, and ends with a correctly named new-task
  recommendation. Anchor resolution may not probe or partially start the new
  direction.
- `mode_anchor` is exactly one of `plan`, `review`, `implementation`, `report-only`, or `handoff`.
- Research and verification are activities inside the anchored mode.
- Confirmed second compaction and unknown/conflicting compaction ordinal both cause terminal chat handoff.
- Chat handoff is the default. A repo-native file is allowed only when the
  original task explicitly authorized its exact documentation path. Archive
  authorization and apply authorization each do not imply file-write
  authorization; without the exact-path authorization, keep the task active.
- Default scanner window is 30 days; `older_than_days` must be `>= 0`.
- Default result limit is 30; accepted limits are 20–50 inclusive.
- Decode every JSONL line with `json.loads`; count only decoded top-level objects whose `type` equals `compacted`.
- Exclude subagent sessions by default.
- Keep `primary_rank` as size rank; build a separate
  `returned_handoff_queue` covering only returned top-N candidates and label it
  `queue_scope=returned-window-only`.
- Never automatically delete, archive, move, prune, rotate, normalize, or apply.
- Reuse the unique `weekly-codex-maintenance-report` automation; do not create another maintenance automation.
- Repo sources are `codex/AGENTS.md` and `codex/skills/codex-fluent`; runtime copies are not source files.
- Before any runtime or automation mutation, require read-only confirmation that
  the current session exposes `automation_update`, then read its formal schema
  and view the existing automation. Missing capability or schema drift stops
  activation; completed source edits may remain.
- Preserve unrelated dirty files. Forward activation and unattended automation
  never use `--delete`. A runtime failure stops subsequent work and reports
  `partial_runtime_state`; rollback requires separate explicit authorization.
- This plan grants no runtime or automation authority. A later execution task
  must receive explicit authorization for the two named runtime targets before
  creating a backup or writing either target, and separate authorization before
  updating the automation.

---

## File Map

- Modify: `codex/AGENTS.md`
  - Owns the anchor envelope, summary marker, conservative compaction policy, and default chat handoff.
- Create: `codex/skills/codex-fluent/scripts/report_active_sessions.py`
  - Pure read-only session discovery, parsing, primary ranking, and handoff-queue rendering.
- Create: `tests/fixtures/codex_fluent_report.golden.md`
  - Freezes the small human-facing Markdown rendering contract.
- Modify: `codex/skills/codex-fluent/SKILL.md`
  - Routes report-only diagnosis through the scanner and documents limits.
- Modify: `codex/skills/codex-fluent/references/maintenance-checklist.md`
  - Adds bounded handoff-queue review before any separately authorized apply action.
- Modify: `docs/CODEX_ENV_REPRODUCTION.md`
  - Documents the three layers, source/runtime ownership, invocation, and automation behavior.
- Modify: `docs/repo-index.md`
  - Registers the scanner in the human-readable runtime surface index.
- Modify: `docs/surfaces.json`
  - Registers the new scanner as a checked runtime-visible surface.
- Modify: `test_runner.py`
  - Adds global-policy, parser, boundary, no-write, and skill-contract tests.
- Runtime update: `~/.codex/AGENTS.md`
  - Back up this single file, then copy only the verified repo source.
- Runtime update: `~/.codex/skills/codex-fluent/`
  - Overlay only this skill with `rsync -a` and no `--delete`.
- Automation update: unique ID `weekly-codex-maintenance-report`
  - Update through the actual exposed automation tool/schema; requested writable
    change is only `prompt`, with any observed server-managed `updated_at`
    change disclosed separately.

## Round-6 Finding Traceability

| Finding | Planned closure | Verification gate |
|---|---|---|
| BCF-001 | Task 1 adds an ordered `ANCHOR_MISMATCH_SEQUENCE_V1`: resolve from direct/available evidence, compare, prohibit new-direction work on mismatch/unknown, then hand off | Focused policy test asserts the complete ordered sequence and no-probe rule |
| BCF-002 | Task 3 uses source-only tests/static checks; managed compatibility moves after Task 5 overlay and checksum parity | Pre-overlay command list contains no managed parity gate; Task 5 runs it after parity |
| BCF-003 | Task 3 removes mandatory file-handoff language and freezes chat/default/exact-path/keep-active rules; archive and apply permission are independently non-transitive | Positive requirements plus forbidden-phrase test over SKILL and checklist |
| BCF-004 | Task 2 freezes top-N, UTC cutoff, persisted source shapes, nullable repo root, and Markdown output | 55+ eligible fixture, limits 20/30/50, 19/51 failures, time/source/golden tests |
| BCF-005 | Task 2 defines `returned_handoff_queue` as returned-window-only | Outside-window high-compaction fixture is absent from queue |
| BCF-006 | Task 5 requires future explicit runtime authority, persistent backup, target/child symlink guards, a source-manifest-bounded dry-run audit, explicit rsync status, source-file parity, and fail-closed partial-state handling | Path/scope checks, checksum parity, runtime-only inventory, no automatic rollback |
| BCF-007 | Task 5 captures the actual automation tool schema and read-only view before writes; Task 6 accepts only a schema-complete mapping and computes a recursive diff | Same-schema forward/rollback validation, persisted schema/view evidence, and actual changed-path assertion |
| BCF-008 | Tasks 2 and 7 compare a complete fixture-tree file map plus SHA-256/size/mtime/mode, force no bytecode output, and separate overlay parity from runtime-only inventory | Isolated no-write gate and managed-file checksum gate; atime explicitly excluded |
| UTC/tie-break minor | Task 2 rejects naive time, serializes canonical UTC `Z`, and tests equal-size offset ordering plus equal-instant `thread_id` ordering | Timestamp contract asserts exact canonical strings and deterministic candidate IDs |
| BFC-001 | Tasks 5–7 use a receipt-writing `run_gate`, injected failure probe, fatal application-tool gate, and `set -euo pipefail` final verification shell | Nonzero injected gate returns 73, writes `partial-runtime-state`, prevents an after marker; no later write or assertion command can mask a failed gate |

## Frozen Review Rubric (v2)

Version 1 remains the historical rubric for the exhausted dual-review loop.
Version 2 begins the separately authorized docs-only repair loop for R2-NMF and
RC findings. A reviewer may add a material `rubric_challenge`, but may not
silently replace or narrow a criterion.

| Domain | Required review question | Evidence expectation | Counterexample that fails the domain |
|---|---|---|---|
| Anchor and handoff safety | Does every mismatch/unknown terminate before the new direction begins, while preserving chat-default and task-active semantics? | Ordered policy text and its focused contract test | Probe the requested repo to decide a mismatch, or treat archive/apply permission as file-write permission |
| Scanner correctness | Are eligibility, JSONL parsing, ranking, queue scope, source identity, and UTC ordering deterministic from persisted evidence? | Isolated fixtures, exact 20/30/50 assertions, boundary tests, and golden Markdown | String-match compaction counting, a queue built from all eligible rows, a guessed repo root, or raw-offset timestamp sorting |
| Report-only integrity | Can scanner diagnosis and handoff triage run without changing Codex state or silently widening scope? | Complete fixture-tree fingerprint before/after, explicit atime limit, and report-only skill text | Writing a session/index file, creating a handoff file without exact authorization, or archiving/deleting automatically |
| Runtime overlay containment | If separately authorized later, does activation modify only named targets with a recoverable and fail-closed evidence trail? | Explicit authority gate, target/child symlink guards, source manifest, rsync statuses, and managed-file parity | Broad mirror, `--delete` in forward flow, unchecked symlink, or a failed gate followed by automation work |
| Automation schema integrity | If separately authorized later, are updates derived from the current formal tool schema/view and proven to change only the managed prompt? | Fresh schema/view evidence, complete forward/rollback payloads, and tool-view/raw recursive diffs | Hard-coded historical tool shape, partial prompt-only update, silently dropped required field, or automatic rollback |
| Plan usability and evidence | Can a later implementer execute each task in order without confusing a source-stage check with a runtime-stage gate? | Exact paths, commands, expected outcomes, and per-claim evidence receipt | Placeholder instruction, pre-overlay runtime-parity check, or a completion claim without command/exit/key output/timestamp |
| Copy-paste fidelity | For Task 5–7 fatal execution payloads only, is every normative command block directly executable as displayed, with its required label and target visible at the invocation site? | Literal `run_gate` invocations for every Task 7 command body; syntax validation of every affected fence; Task 1–4 TDD commands, examples, and fixture content are out of scope | A prose-only wrapper rule that leaves a copy-pasteable raw Task 5–7 payload, or a label/target inferred from a separate table |

**Required evidence for this document-only review:** Markdown structure and
static contract checks; `git diff --check`; and independent read-only reviews.
No runtime activation, automation call, task archive, task deletion, or task
creation is evidence for this review because all are out of scope.

**Known unknowns:** the future Codex Desktop lifecycle API and the live
automation tool schema/view may differ when a separately authorized execution
task begins. The plan directs that task to stop rather than guess.

## Acceptance Ledger

| Finding ID | Severity | Claim | Closure condition | Current status |
|---|---|---|---|---|
| BCF-001 | blocker | Anchor mismatch could be handled after starting the requested direction | Ordered no-probe sequence and focused test cover mismatch and unknown | revised; independent closure pending |
| BCF-003 | blocker | File handoff authorization could be inferred from archive/apply permission | Chat default, exact-path requirement, separate archive/apply non-transitivity, and keep-active test are explicit | revised; independent closure pending |
| BCF-006 | blocker | Runtime overlay scope and rollback could widen or mask a partial state | Explicit future authority, manifest-bounded rsync, symlink checks, statuses, parity, and deletion-free forward/rollback overlay are explicit | revised; independent closure pending |
| BCF-007 | blocker | Automation fields could be hard-coded rather than derived from current schema/view | Formal schema/view evidence, normalized snapshot checks, and authoritative tool-view diff are explicit | revised; independent closure pending |
| BCF-008 | blocker | No-write proof could omit fixture files or metadata | Complete fixture-tree map, SHA-256/size/mtime/mode comparison, and atime limitation are explicit | revised; independent closure pending |
| UTC-TIE-001 | minor | Offset timestamps could be compared as strings or naive timestamps treated as local time | Parser, canonical serializer, and equal-size offset/same-instant tests are explicit | revised; independent closure pending |
| BFC-001 | major | A failed fatal command could be masked by a later command and allow later writes or claims | Unified `record_gate_result`/`run_gate`, shell and tool-result fault injections, post-forward schema/view gating, and individually labelled Task 7 gates | accepted by fresh Codex Round 14; manual Claude blind final pending |
| NMF-001 | minor | Duplicated gate helpers and raw Task 7 groups could make the canonical failure protocol ambiguous | Exactly one Task 5 `run_gate.sh` definition; Task 7 blocks are labelled gate payloads, never raw executable groups | closed by Round-14 Codex re-review |
| NMF-002 | minor | A single rsync itemize width could reject a valid host before activation | Record host `rsync --version`; accept only 9- or 11-character status tokens and fail closed otherwise | closed by Round-14 Codex re-review |
| NMF-003 | minor | `--now` was described as hidden although the plan did not require help suppression | Describe it as documented test-only seam and prohibit ordinary user/automation dependence | closed by Round-14 Codex re-review |
| R2-NMF-001 | minor | Task 7's displayed payloads still look directly executable even though prose requires labelled gates | Rewrite Steps 2–5 as literal per-label `run_gate` invocations, including the two timed `bash -c` forms | closed by Phase 1 closure review |
| R2-NMF-002 | minor | Task 1's `sequence.index()` can raise a traceback before the standard contract diagnostic | Guard every ordered term with `require(term in sequence, ...)` before position lookup | closed by Phase 1 closure review |
| R2-NMF-003 | minor | The golden Markdown note calls fixture `/work/...` labels non-absolute | Reword the invariant to exclude only timestamps and tempdir-dependent paths | closed by Phase 1 closure review |
| RC-001 | minor | Frozen rubric did not define which command blocks are normative | Scope copy-paste fidelity to Task 5–7 fatal payloads and explicitly exclude Task 1–4 TDD commands, examples, and fixture content | closed by Phase 1 closure review |
| PH1-GOV-001 | major | The new docs-only loop could be mistaken for an extension of historical Round 6–15 | Explicit Phase 1 loop envelope with exact files, `target=10/10`, `max_rounds=5`, mode, forbidden actions, and separate completion gate | closed by Phase 1 envelope |
| NMF-BLIND-001 | minor | Formal-tool receipt label `automation-post-forward-view` did not match the normative schema/view gate labels | Use exact `automation-schema-post-forward` and `automation-view-post-forward` labels at each receipt call | closed by Phase 1 repair closure review |
| NMF-BLIND-002 | minor | Task 7 fault injection was described only as an equivalent probe without a literal fatal payload or assertions | Add a copy-pasteable `run_gate` probe with exit code 75, target, marker, receipt, partial-state, and later-gate assertions | closed by Phase 1 repair closure review |
| NMF-BLIND-003 | minor | Absent source fields were not explicitly classified or tested | Treat absent `thread_source` and `source` as eligible `source_kind="unknown"` and add an absence fixture | closed by Phase 1 repair closure review |
| PH1-F1 | major | Task 5's child-symlink guard checks `destination.exists()` before `lstat()`, so a broken child symlink can evade the fail-closed guard | Replace existence check with a broken-link-safe `lexists`/`lstat` walk and add a broken-child-symlink fault test before any future runtime write | closed by Phase 2 closure confirmation |

## Dual-Review Closeout

- **Round 7 — Codex blind final:** `6.5/10`; `candidate_pass=false`; added
  BFC-001 because the original multi-command gates could mask a failure.
- **Round 8 — Codex closure review:** `7/10`; `candidate_pass=false`; BFC-001
  remains open because the shell gate runner does not yet cover successful
  automation's post-forward schema/view failure and every Task 7 fatal gate with
  the same receipt/`partial-runtime-state` protocol.
- **Claude:** not run and therefore has no committee score. The explicit round-8
  Claude condition required a round-7 candidate pass, which did not occur.
- **Verdict:** `incomplete`. `max_rounds=8` is exhausted; do not add a ninth
  review round automatically.

### Authorized Continuation

The user has now explicitly expanded `max_rounds` to 10. Round 9 is a fresh
Codex blind review of the BFC-001 remediation using the frozen rubric. If and
only if Round 9 reaches candidate pass, Round 10 is a fresh Claude blind review.
The independent scores remain separate and are never averaged. If Round 10 does
not converge, report `incomplete` and do not add an eleventh round.

### Round 9–10 Result

- **Round 9 — Codex blind final:** `9.7/10`; candidate pass; no open material
  finding in the planning contract.
- **Round 10 — Claude blind final:** no committee score. The initial response
  omitted every required structured field. One permitted structured retry first
  hit `Exceeded USD budget (1)`; the budget-ladder retry at `$2.00` again omitted
  the required fields. This is a malformed-response stop condition, not a pass.
- **Verdict:** `incomplete`. `max_rounds=10` is exhausted; do not run Round 11
  automatically.

### Round 11 Stop Result

- **Authorization:** the user allowed continuation up to `max_rounds=15`.
- **Round 11 — Claude blind final:** no committee score. A fresh JSON-schema
  request at `$1.00` returned `error_max_budget_usd`; its bounded-excerpt retry
  at `$2.00` returned no result object; the one permitted structured retry with
  tools disabled also returned no result object.
- **Verdict:** `incomplete`. The malformed provider response repeated after
  shrinking the evidence source and disabling tools, which is a loop stop
  condition. Do not start Round 12 without a materially different evidence
  source or user direction.

### Round 12 Diagnostic and Stop Result

- **Authorization and boundary:** the user explicitly authorized a read-only
  Claude CLI diagnosis and continuation within `max_rounds=15`. It did not edit
  runtime, automation, global Claude configuration, repository sources, or
  Codex task state.
- **Diagnostic conclusion:** JSON mode, JSON Schema, tools disabled, the
  nested committee-result schema, and the complete two-document evidence all
  have successful control evidence. A `$1.00` full-evidence request can exceed
  the budget, but the identical factual extraction at `$2.00` returns a valid
  result. Therefore the missing Round-12 result cannot honestly be attributed
  to a local CLI configuration, schema support, disabled tools, or evidence
  size alone.
- **Round 12 — Claude blind final:** no committee score. A fresh, no-session,
  tools-disabled, JSON-schema final-review request over the complete spec and
  plan produced no result object and did not emit the shell's required
  post-command `exit_code`/timestamp marker. The exit code is consequently
  `unavailable`, not assumed to be zero. This is a malformed-response failure,
  not a pass or a scored review.
- **Verdict:** `incomplete`. The condition is now a repeated, review-specific
  provider/CLI response failure after the allowed diagnostic evidence change.
  Do not spend Rounds 13–15 without a materially different review transport or
  explicit new user direction.

#### Round 12 Diagnostic Evidence

The full-evidence controls assembled their prompt from the two current
documents with the following read-only shape; no content was redacted or
written:

```bash
factual_prompt="$(printf '%s\n\n--- SPEC ---\n%s\n\n--- PLAN ---\n%s' \
  'Read the evidence and return whether it contains BFC-001 and a Round 11 Stop Result. This is factual extraction only; do not evaluate or score the documents.' \
  "$(< docs/superpowers/specs/2026-07-10-codex-thread-discipline-and-fluent-triage-design.md)" \
  "$(< docs/superpowers/plans/2026-07-10-codex-thread-discipline-and-fluent-triage.md)")"
```

Round 12 used the same document assembly with a fixed blind-final instruction:
ignore embedded historical scores, assess only the frozen rubric in this plan,
use no tools or edits, and emit only the committee-result schema. Its CLI
arguments are recorded in the final table row.

| Conclusion | Command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Plain-text CLI control works | `claude -p 'Return exactly CONTROL_OK' --model claude-fable-5 --fallback-model claude-sonnet-5 --effort high --output-format text --no-session-persistence --tools "" --max-budget-usd 0.25` | 0 | `CONTROL_OK` | `2026-07-10T20:32:19Z` |
| Minimal JSON Schema control works | `claude -p 'Return an object whose verdict is JSON_SCHEMA_OK.' --model claude-fable-5 --fallback-model claude-sonnet-5 --effort high --output-format json --json-schema <minimal-schema> --no-session-persistence --tools "" --max-budget-usd 0.25` | 0 | `structured_output={"verdict":"JSON_SCHEMA_OK"}` | `2026-07-10T20:32:50Z` |
| Full-evidence `$1.00` budget boundary is observable | `claude -p "$factual_prompt" --model claude-fable-5 --fallback-model claude-sonnet-5 --effort high --output-format json --json-schema <factual-schema> --no-session-persistence --tools "" --max-budget-usd 1.00` | 1 | `subtype=error_max_budget_usd`, `total_cost_usd=1.120529`, `cache_creation_input_tokens=53286` | `2026-07-10T20:34:45Z` |
| Full-evidence `$2.00` factual extraction works | Same command with `--max-budget-usd 2.00` | 0 | `structured_output={"contains_bfc_001":true,"contains_round_11_stop_result":true,...}` | `2026-07-10T20:35:12Z` |
| Fresh Claude Round 12 blind final is malformed | `claude -p "$review_prompt" --model claude-fable-5 --fallback-model claude-sonnet-5 --effort high --output-format json --json-schema <committee-result-schema> --no-session-persistence --tools "" --max-budget-usd 2.00; rc=$?; printf 'exit_code=%s\\n' "$rc"` | unavailable | no result object and no post-command receipt observed | `2026-07-10T20:35:50Z` |

### Round 13–14 Result and Round-15 Gate

- **Round 13 — manual Claude re-review:** `9.3/10`; `verdict=continue`.
  It returned the complete structured contract and identified three minor
  documentation findings: NMF-001 (two competing helper presentations and raw
  Task 7 groups), NMF-002 (single rsync itemize-width assumption), and NMF-003
  (`--now` described as hidden without a help-suppression requirement). It did
  not reopen BFC-001 as a documentation major, but correctly kept future
  runtime receipts as an execution-time acceptance dependency.
- **Docs-only response:** this revision makes Task 5 Step 1 the only
  `run_gate.sh` definition; declares Task 7 snippets labelled `run_gate`
  payloads rather than raw groups; records the host rsync version and accepts
  only 9/11-character itemize tokens; and calls `--now` a documented test-only
  seam. It does not implement or run any runtime/automation step.
- **Round 14 — Codex closure re-review:** `9.7/10`; `candidate_pass=true`.
  NMF-001, NMF-002, and NMF-003 are closed in the planning contract; no new
  material finding was added. This does not average or replace Claude's `9.3`.
- **Round 15 gate:** use a fresh, manually supplied Claude blind-final review
  over a sanitized packet that excludes all dual-review history, scores, and
  this section. It is the final authorized round. If it is not a candidate
  pass, report `incomplete` and do not add a Round 16.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Round 13 Claude re-review packet | sanitized `sed` packet over the two current documents; manual Claude response | 0 | complete YAML response; `committee_rating=9.3`; `verdict=continue`; NMF-001..003 | `2026-07-10T21:55:57Z` |
| Round 14 Codex closure re-review | `python3 - <<'PY'` static contract assertions over the two current documents | 0 | `closure_contract_static=pass canonical_gate_helper=1 task7_labels=19 itemize_widths=9,11 now_test_only=true delete_denied=true` | `2026-07-10T22:10:29Z` |

### Round 15 Final Stop Result

- **Round 15 — manual Claude blind final:** `9.6/10`; `verdict=continue`.
  It found no blocker or major, but opened R2-NMF-001 (Task 7 code blocks are
  still copy-pasteable raw groups), R2-NMF-002 (missing `require()` guard
  before ordered `sequence.index()`), and R2-NMF-003 (the golden Markdown
  wording calls deterministic `/work/...` labels non-absolute). It also added
  RC-001: plan usability should explicitly cover copy-paste fidelity of an
  illustrative versus normative code block.
- **Verdict:** `incomplete`. Round 15 is the final user-authorized round, so
  these findings remain open. Do not fix them, start a Round 16, run runtime or
  automation, delete/archive any task, commit, or push without new explicit
  authorization.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Round 15 manual Claude blind-final packet | sanitized `sed`/`awk` packet over the two documents; manual Claude response | 0 | complete response; `committee_rating=9.6`; `verdict=continue`; R2-NMF-001..003 and RC-001 | `2026-07-10T23:19:31Z` |

## Phase 1 Closure Review (Blind Final Pending)

- **Committee result:** `committee_rating=10.0/10`; `candidate_pass=true`;
  `threshold_status=fail` only because the fresh blind final has not yet run.
  The closure review found no open blocker, major, minor, or rubric challenge
  within the Phase 1 planning contract.
- **Ledger:** `PH1-GOV-001`, `R2-NMF-001`, `R2-NMF-002`, `R2-NMF-003`, and
  `RC-001` are closed at the docs-contract level. This does not claim scanner,
  runtime, or automation implementation success.
- **Required next step:** run one fresh blind final using a packet that excludes
  this section, all historical scores/verdicts, ledger updates, and revision
  briefs. If it finds a material issue, continue within the new Phase 1
  `max_rounds=5`; otherwise close the loop as passed.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Phase 1 closure review | Python Markdown/fence/Python-Bash syntax/Phase 1 envelope/Task 7 literal-gate checker plus `git diff --check` | 0 | `phase1_envelope_and_r2_rc_static=pass`; `spec_lines=328`; `plan_lines=2343`; `task7_literal_gates=19`; no new material finding | `2026-07-10T23:59:12Z` |

## Phase 1 Fresh Blind Final (Repair Required)

- **Committee result:** `committee_rating=8.0/10`; `verdict=continue`;
  `candidate_pass=false`; `threshold_status=fail`. The review was blind to
  this history, prior scores, the ledger, and the revision brief.
- **Findings:** NMF-BLIND-001, NMF-BLIND-002, and NMF-BLIND-003 are minor and
  are bounded to the planning contract. No blocker, major finding, or rubric
  challenge was raised.
- **Required repair:** normalize the two post-forward formal gate labels,
  replace the Task 7 fault-injection placeholder with a literal fatal payload
  and assertions, and define/test absent-source classification as
  `source_kind="unknown"`.
- **Next gate:** run one Phase 1 closure review after these docs-only repairs;
  only a candidate pass permits the final fresh blind review. Do not execute
  runtime/automation, archive/delete tasks, commit, push, or exceed
  `max_rounds=5`.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Phase 1 fresh blind final | Sanitized read-only spec/plan slices supplied to fresh committee; no files modified or runtime/automation commands run | 0 | `committee_rating=8.0`; `verdict=continue`; `candidate_pass=false`; `NMF-BLIND-001..003` | `2026-07-11T00:11:01Z` |

## Phase 1 Repair Closure Review (Final Blind Pending)

- **Committee result:** `committee_rating=10.0/10`; `candidate_pass=true`;
  `threshold_status=fail` only because the final fresh blind review remains.
  No new material finding or rubric challenge was raised.
- **Ledger:** NMF-BLIND-001, NMF-BLIND-002, and NMF-BLIND-003 are closed at
  the planning-contract level. This does not claim scanner, runtime, or
  automation implementation success.
- **Required next step:** run the final fresh blind review with a sanitized
  packet that excludes this section, all historical scores/verdicts, ledger
  updates, and revision briefs. If it finds a material issue, report
  `incomplete` at `max_rounds=5`; otherwise close Phase 1 as passed.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Phase 1 repair closure review | Python Markdown/fence/Python-Bash syntax/Phase 1 blind-repair contract checker plus `git diff --check` | 0 | `phase1_blind_repair_static=pass`; `spec_lines=329`; `plan_lines=2437`; `task7_literal_gates=19`; no new material finding | `2026-07-11T00:24:33Z` |

## Phase 1 Final Blind (Incomplete; `max_rounds=5` Exhausted)

- **Committee result:** `committee_rating=unavailable` (the transport did not
  provide a calibrated numeric scale); `verdict=incomplete (continue after
  repair)`; `candidate_pass=false`; `threshold_status=not_met`.
- **New major:** PH1-F1 remains open. The blind review found that Task 5's
  `destination.exists()` check can skip a broken child symlink before `lstat`,
  so the future runtime containment contract is not fully fail-closed. This is
  a planning finding only; no runtime or automation command was executed.
- **Stop rule:** Phase 1 has consumed all five authorized rounds. Do not add a
  sixth round, implement the fix, run runtime/automation, archive/delete tasks,
  commit, or push without a new explicit authorization and a new loop
  envelope.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Phase 1 final fresh blind | Sanitized read-only spec/plan slices supplied to fresh committee; no files modified or runtime/automation payloads run | 0 | `committee_rating=unavailable`; `verdict=incomplete`; `candidate_pass=false`; `threshold_status=not_met`; `PH1-F1=major` | `2026-07-11T00:24:12Z` |

## Phase 2 F1 Round 1 (Repair Required)

- **Committee result:** `committee_rating=6.0/10`; `candidate_pass=false`;
  `threshold_status=fail`. The open PH1-F1 major is confirmed; no new finding
  or rubric challenge was added.
- **Frozen rubric:** reuse the v2 domains without narrowing them. The repair
  must make the source-manifest walk broken-link-safe and add a literal
  dangling-child-symlink fault-test contract before any future runtime write.
- **Bounded revision:** edit only these two docs, then run fresh Markdown,
  fenced Python/Bash syntax, and `git diff --check` evidence. Do not run
  runtime/automation or mutate Codex state.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Phase 2 F1 committee round 1 | `rg` source-manifest/rubric inspection plus `git diff --check -- <design> <plan>` | 0 | `committee_rating=6.0`; `candidate_pass=false`; PH1-F1 major confirmed; no new finding | `2026-07-11T00:45:00Z` |

## Phase 2 F1 Repair Closure Review (Bookkeeping Repair Recorded)

- **Committee result:** `committee_rating=7.0/10`; `candidate_pass=false`;
  `threshold_status=fail` due only to the still-open PH1-F1 ledger/status at
  review time. The technical repair itself passed static inspection; no new
  finding or rubric challenge was added.
- **Bookkeeping repair:** PH1-F1 remains explicitly open until a fresh closure
  confirmation observes the repaired ledger/status and the same static guard
  evidence. This preserves the rating cap rather than claiming premature
  closure.
- **Next gate:** the bookkeeping update was followed by a separate closure
  confirmation and final fresh blind review within this loop's `max_rounds=5`.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Phase 2 F1 repair closure review | Read-only Python source-manifest/fixture/ledger checker plus `git diff --check -- <design> <plan>` | 0 | `committee_rating=7.0`; `candidate_pass=false`; technical repair pass; ledger/status closure pending | `2026-07-11T00:49:03Z` |

## Phase 2 F1 Closure Confirmation (Final Blind Passed)

- **Committee result:** `committee_rating=10.0/10`; `candidate_pass=true`;
  `threshold_status=fail` only while the final blind was pending. The ledger
  now has no open material finding; PH1-F1 is closed by this confirmation.
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
- **Stop rule:** Phase 2 is complete at the authorized five-round ceiling
  envelope; do not start runtime/automation or another review loop without a
  new explicit authorization.

| Conclusion | command | exit_code | key_output | timestamp |
|---|---|---:|---|---|
| Phase 2 F1 final fresh blind | Sanitized fresh blind review over the specified slices plus `git diff --check -- <design> <plan>` | 0 | `committee_rating=10.0`; `verdict=pass`; `candidate_pass=true`; `threshold_status=met`; `new_material_findings=[]` | `2026-07-11T00:54:01Z` |

## BFC-001 Follow-Up Remediation (Planning Only; Not Yet Re-Reviewed)

This section implements the round-8 revision brief without changing its
historical verdict or consuming another review round. It is the canonical
execution protocol for Tasks 5–7: Task 5 Step 1 contains its one and only
`run_gate.sh` definition, and every Task 7 command body below is executed only
through the labelled `run_gate` mapping in this section. It does not authorize
runtime synchronization, an automation tool call, task archival, task deletion,
or a new committee round.

All fatal gates—shell commands and formal application-tool results alike—must
use one protocol. A nonzero result always appends the same receipt shape, writes
`partial-runtime-state.json`, and exits before the next gate, mutation, timing
display, or task can start. A successful result updates the durable
`LAST_SUCCESS_OPERATION` value. Task 5 Step 1 writes and sources the sole
canonical helper after its backup directory and receipt paths exist; no other
section defines or overwrites `run_gate.sh`.

For a formal application tool, persist the exact structured result first. Use
the real tool result's status—never a synthesized success—and then invoke
`record_gate_result` before examining a later result or starting another task:

```bash
schema_result="$runtime_backup/gates/automation-schema-post-forward.json"
# Write the exact, non-secret formal schema response to "$schema_result".
# schema_status is 0 only when that exact call succeeded and returned the
# required schema shape.
record_gate_result \
  "automation-schema-post-forward" \
  "weekly-codex-maintenance-report" \
  "automation_update schema weekly-codex-maintenance-report" \
  "$schema_status" \
  "$schema_result"

view_result="$runtime_backup/gates/automation-view-post-forward.json"
# Write the exact, non-secret read-only view response to "$view_result".
# view_status is 0 only when that exact call succeeded and returned the
# required view shape.
record_gate_result \
  "automation-view-post-forward" \
  "weekly-codex-maintenance-report" \
  "automation_update view weekly-codex-maintenance-report" \
  "$view_status" \
  "$view_result"
```

The future execution task must use this mapping; each row is a separate fatal
gate and a failure stops at the stated boundary.

| Gate label | Exact source | Failure boundary |
|---|---|---|
| `automation-schema-before-runtime` / `automation-view-before-runtime` | Task 5 Step 0 formal schema and read-only view | Before any runtime backup or write |
| `automation-schema-before-forward` / `automation-view-before-forward` | Task 6 Step 1 repeated formal schema and view | Before payload construction or forward update |
| `automation-forward-update` | Task 6 forward `automation_update` response | Before post-forward preflight, diff, or Task 7 |
| `automation-schema-post-forward` / `automation-view-post-forward` | Task 6 Step 3 repeated formal schema and view | Before `automation-after-state-diff` |
| `automation-after-state-diff` | Task 6 recursive diff assertion | Before rollback proof or Task 7 |
| `broken-child-symlink-guard` | Task 5 Step 1 disposable dangling-child-symlink fixture | Before any runtime backup or write |
| `task7-isolated-fixture`, `task7-live-scan-before`, `task7-selected-snapshot`, `task7-live-scan-after`, `task7-concurrent-write-report`, `task7-semantics`, `task7-timing-display` | Task 7 Steps 1–4 commands in their listed order | Before the next Task 7 command or final claim |
| `task7-global-policy`, `task7-active-report`, `task7-boundaries`, `task7-selection`, `task7-timestamp-source`, `task7-markdown`, `task7-report-only`, `task7-skill-compatibility`, `task7-surfaces`, `task7-full-suite`, `task7-env-verify`, `task7-diff-check` | Task 7 Step 5 commands in their listed order | Before the next verification command, commit, or handoff |

The Task 7 code bodies below are command payloads, not raw executable command
groups. Execute each one only as an individual
`run_gate <label> <affected-target> <command...>` call using the labels above;
do not run a payload's former top-level `set -euo pipefail` wrapper directly.
For the two `/usr/bin/time` scanner invocations, run the existing braced command
through `run_gate` via `bash -c` so the report JSON and matching timing file
remain in `live_dir`; only call `task7-timing-display` after
`task7-semantics` succeeds. The final `git diff --check` remains
`task7-diff-check`, not a substitute for an earlier gate's receipt.

Before any authorized forward update, prove both non-shell failure paths with
separate fault injections. They exercise `record_gate_result`, not the real
automation or runtime targets:

```bash
tool_probe="$runtime_backup/tool-gate-failure-probe"
mkdir -p "$tool_probe"
printf '%s\n' 'simulated formal tool failure' > "$tool_probe/result.json"
set +e
bash -c 'source "$1"; record_gate_result "injected-post-forward-view" "probe-only" "automation_update view" 74 "$2/result.json"; touch "$2/after-failure"' \
  bash "$runtime_backup/run_gate.sh" "$tool_probe"
tool_probe_status=$?
set -e
test "$tool_probe_status" -eq 74
test ! -e "$tool_probe/after-failure"
python3 - "$GATE_RECEIPTS" "$PARTIAL_STATE" <<'PY'
import json
from pathlib import Path
import sys

receipts = [json.loads(line) for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()]
assert receipts[-1]["gate"] == "injected-post-forward-view"
assert receipts[-1]["exit_code"] == 74
partial = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
assert partial["failed_gate"] == "injected-post-forward-view"
assert partial["exit_code"] == 74
print("tool_gate_fault_injection=pass after_failure=false")
PY
```

Run this exact Task 7 failure probe before any authorized Task 7 command. It
uses the canonical helper, the real fatal label, an affected target, an injected
exit code of 75, and explicit post-gate assertions:

```bash
task7_failure_probe="$runtime_backup/task7-gate-failure-probe"
mkdir -p "$task7_failure_probe"
set +e
bash -c 'source "$1"; run_gate "task7-semantics" "report-only-task7-semantics" sh -c "exit 75"; touch "$2/after-failure"' \
  bash "$runtime_backup/run_gate.sh" "$task7_failure_probe"
task7_failure_status=$?
set -e
test "$task7_failure_status" -eq 75
test ! -e "$task7_failure_probe/after-failure"
python3 - "$GATE_RECEIPTS" "$PARTIAL_STATE" <<'PY'
import json
from pathlib import Path
import sys

receipts = [
    json.loads(line)
    for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
]
assert receipts[-1]["gate"] == "task7-semantics"
assert receipts[-1]["affected_target"] == "report-only-task7-semantics"
assert receipts[-1]["exit_code"] == 75
partial = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
assert partial["failed_gate"] == "task7-semantics"
assert partial["affected_target"] == "report-only-task7-semantics"
assert partial["exit_code"] == 75
assert not any(
    receipt["gate"] in {"task7-timing-display", "task7-diff-check"}
    for receipt in receipts[-2:]
)
print("task7_gate_fault_injection=pass after_failure=false later_gates=false")
PY
```

The probe's nonzero result, receipt, `partial-runtime-state`, absent
`after-failure` marker, and absent later-gate receipts are all required
evidence. A future reviewer may only close BFC-001 after inspecting those fresh
receipts and the actual bounded execution output.

### Task 1: Add the Global Thread-Discipline Contract

**Files:**
- Modify: `test_runner.py`
- Modify: `codex/AGENTS.md`

**Interfaces:**
- Consumes: repo-managed global AGENTS text loaded into each Codex task.
- Produces: `THREAD_DISCIPLINE_V1` anchor envelope and `THREAD_DISCIPLINE_SUMMARY_V1` marker.

- [ ] **Step 1: Write the failing policy-contract test**

Add this function before `TESTS` in `test_runner.py`:

```python
def test_global_agents_thread_discipline_contract():
    text = (ROOT / "codex" / "AGENTS.md").read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    required = [
        "## Thread Discipline",
        "THREAD_DISCIPLINE_V1",
        "THREAD_DISCIPLINE_SUMMARY_V1",
        "repo_anchor",
        "repo_anchor_provenance",
        "mode_anchor",
        "compaction_ordinal",
        "checkpoint",
        "terminal chat handoff",
        "unknown",
        "future Codex Desktop lifecycle API",
        "ANCHOR_MISMATCH_SEQUENCE_V1",
        "resolve request_repo and request_mode from direct request and already-available workspace evidence",
        "unknown mismatch",
        "next_action=terminal_chat_handoff",
        "forbid new-direction tool calls and edits",
        "must not probe or partially start the new direction",
        "<project>-<YYYYMMDD>-<summary>",
    ]
    for term in required:
        require(term in text, f"global AGENTS missing thread discipline term: {term}")
    require(
        "Research and verification do not change mode_anchor" in text,
        "supporting work must remain inside the anchored mode",
    )
    for term in [
        "explicitly authorized the exact documentation path",
        "Archive authorization does not imply file-write authorization",
        "Apply authorization does not imply file-write authorization",
        "keep the task active",
    ]:
        require(term in normalized, f"global AGENTS missing handoff authorization term: {term}")
    require(
        "Do not automatically create, archive, or delete a task" in text,
        "global AGENTS must preserve the no-mutation boundary",
    )
    sequence_start = text.index("ANCHOR_MISMATCH_SEQUENCE_V1")
    sequence = text[sequence_start:]
    ordered_terms = [
        "1. resolve request_repo and request_mode from direct request and already-available workspace evidence",
        "2. compare both values with the frozen anchors",
        "3. on mismatch or unknown mismatch, forbid new-direction tool calls and edits",
        "4. set next_action=terminal_chat_handoff and return the bounded terminal chat handoff",
        "5. recommend <project>-<YYYYMMDD>-<summary>",
    ]
    positions = []
    for term in ordered_terms:
        require(term in sequence, f"missing ordered term: {term}")
        positions.append(sequence.index(term))
    require(positions == sorted(positions), "anchor mismatch handling must preserve its fail-closed order")
    print("[PASS] global AGENTS thread discipline contract")
```

Register `test_global_agents_thread_discipline_contract` immediately before
`test_runner_registry_complete` in `TESTS`.

- [ ] **Step 2: Run the test and verify RED**

```bash
python3 -c 'import test_runner; test_runner.test_global_agents_thread_discipline_contract()'
```

Expected: exit code 1 with a missing thread-discipline term.

- [ ] **Step 3: Add the minimal policy**

Add this section to `codex/AGENTS.md` before `Workflow Hooks`:

```markdown
## Thread Discipline
- At task start, freeze a THREAD_DISCIPLINE_V1 envelope containing task_name,
  repo_anchor, repo_anchor_provenance, mode_anchor, and compaction_ordinal.
- repo_anchor is a canonical absolute root proven by git top-level or a
  registered project; otherwise use explicit projectless scope. Never infer it
  from a cwd basename.
- mode_anchor is exactly one of plan, review, implementation, report-only, or
  handoff. Research and verification do not change mode_anchor.
- ANCHOR_MISMATCH_SEQUENCE_V1
  1. resolve request_repo and request_mode from direct request and already-available workspace evidence
  2. compare both values with the frozen anchors
  3. on mismatch or unknown mismatch, forbid new-direction tool calls and edits
  4. set next_action=terminal_chat_handoff and return the bounded terminal chat handoff
  5. recommend <project>-<YYYYMMDD>-<summary>
- The resolver must not probe or partially start the new direction. If available
  evidence cannot safely resolve either anchor, treat it as an unknown mismatch.
- Carry THREAD_DISCIPLINE_SUMMARY_V1 with repo_anchor, mode_anchor,
  compaction_ordinal, and next_action across summaries.
- After a confirmed first compaction, refresh a concise checkpoint.
- At a confirmed second compaction, stop normal work and return a terminal chat
  handoff. If the ordinal is missing, conflicting, or untrusted, conservatively
  return the same terminal chat handoff.
- Chat handoff is the default. Write a repo-native handoff only when the
  original task explicitly authorized the exact documentation path. Archive
  authorization does not imply file-write authorization. Apply authorization
  does not imply file-write authorization. Without that exact-path
  authorization, keep the task active and do not archive it.
- The weekly scanner is a deterministic audit, not an immediate trigger. A hard
  trigger requires a future Codex Desktop lifecycle API.
- Do not automatically create, archive, or delete a task.
```

- [ ] **Step 4: Run the focused test and verify GREEN**

```bash
python3 -c 'import test_runner; test_runner.test_global_agents_thread_discipline_contract()'
```

Expected: exit code 0 and `[PASS] global AGENTS thread discipline contract`.

- [ ] **Step 5: Commit the policy slice**

```bash
git add codex/AGENTS.md test_runner.py
git commit -m "feat: enforce Codex thread discipline"
```

### Task 2: Build the Read-Only Active-Session Scanner

**Files:**
- Create: `codex/skills/codex-fluent/scripts/report_active_sessions.py`
- Create: `tests/fixtures/codex_fluent_report.golden.md`
- Modify: `test_runner.py`

**Interfaces:**
- Produces: `scan_sessions(codex_home, older_than_days, limit, now) -> ScanReport`.
- CLI: `report_active_sessions.py --codex-home PATH --older-than-days N --limit N --format markdown|json`.
- Test-only, documented deterministic seam: `--now ISO_TIMESTAMP`; tests may
  freeze time, but ordinary user and automation invocations must not depend on
  it. It may appear in CLI help and is not a policy or automation input.
- Primary candidate fields: `primary_rank`, `thread_id`, `title`, `cwd_label`, nullable `repo_root`, `repo_root_provenance`, `session_path`, canonical-UTC `started_at`, `age_days`, `size_bytes`, `compaction_count`, `handoff_required`, and `source_kind`.
- Produces: separate `returned_handoff_queue` entries containing `primary_rank`
  references plus `queue_scope="returned-window-only"`.

- [ ] **Step 1: Add failing fixture helpers and the core behavior test**

Add `datetime as dt`, `hashlib`, `json`, and `os` imports when absent. Add a fixture
that writes compact JSON, spaced JSON, an embedded compaction string, malformed
session/index lines, a recent session, a subagent session, and equal-size old
sessions. Snapshot every session and `session_index.jsonl` before invocation:

```python
def _file_fingerprint(path):
    stat = path.stat()
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "mode": stat.st_mode,
    }


def _fixture_tree_fingerprint(root):
    files = sorted(path for path in root.rglob("*") if path.is_file())
    return {
        str(path.relative_to(root)): _file_fingerprint(path)
        for path in files
    }


def test_codex_fluent_active_session_report():
    script = ROOT / "codex" / "skills" / "codex-fluent" / "scripts" / "report_active_sessions.py"
    require(script.exists(), "codex-fluent active-session scanner missing")
    with tempfile.TemporaryDirectory() as tmp:
        codex_home = Path(tmp) / ".codex"
        sessions = codex_home / "sessions" / "2026" / "05" / "01"
        sessions.mkdir(parents=True)
        index = codex_home / "session_index.jsonl"
        now = dt.datetime(2026, 7, 10, tzinfo=dt.timezone.utc)

        old = "2026-05-01T00:00:00Z"
        recent = "2026-07-09T00:00:00Z"
        rows = [
            {"timestamp": old, "type": "session_meta", "payload": {
                "id": "thread-large", "timestamp": old, "cwd": "/work/display-only"}},
            {"timestamp": old, "type": "compacted", "payload": {}},
        ]
        large = sessions / "rollout-thread-large.jsonl"
        large.write_text(
            json.dumps(rows[0], separators=(",", ":")) + "\n"
            + json.dumps(rows[1], indent=None) + "\n"
            + json.dumps({"type": "event_msg", "payload": {
                "message": "embedded only: \\\"type\\\":\\\"compacted\\\""}}) + "\n"
            + json.dumps({"type": "event_msg", "payload": {"type": "compacted"}}) + "\n"
            + json.dumps({"type": "compacted", "payload": {"pad": "x" * 4000}}) + "\n",
            encoding="utf-8",
        )
        tie_a = sessions / "rollout-thread-a.jsonl"
        tie_b = sessions / "rollout-thread-b.jsonl"
        for path, thread_id in ((tie_a, "thread-a"), (tie_b, "thread-b")):
            path.write_text(json.dumps({"timestamp": old, "type": "session_meta", "payload": {
                "id": thread_id, "timestamp": old, "cwd": "/work/not-a-repo"}}) + "\n", encoding="utf-8")
        tie_b.write_bytes(tie_b.read_bytes().ljust(tie_a.stat().st_size, b" "))
        (sessions / "rollout-recent.jsonl").write_text(json.dumps({
            "timestamp": recent, "type": "session_meta", "payload": {
                "id": "thread-recent", "timestamp": recent, "cwd": "/work/recent"}}) + "\n", encoding="utf-8")
        (sessions / "rollout-agent.jsonl").write_text(json.dumps({
            "timestamp": old, "type": "session_meta", "payload": {
                "id": "thread-agent", "timestamp": old, "cwd": "/work/agent",
                "thread_source": "subagent"}}) + "\n", encoding="utf-8")
        (sessions / "rollout-malformed.jsonl").write_text("{malformed\n", encoding="utf-8")
        index.write_text(
            json.dumps({"id": "thread-large", "thread_name": "Large task"}) + "\n"
            + "{malformed index\n",
            encoding="utf-8",
        )
        before = _fixture_tree_fingerprint(codex_home)

        proc = subprocess.run([
            sys.executable, str(script), "--codex-home", str(codex_home),
            "--older-than-days", "30", "--limit", "20", "--format", "json",
            "--now", now.isoformat(),
        ], capture_output=True, text=True, check=False,
           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        require(proc.returncode == 0, f"scanner failed: {proc.stderr}")
        report = json.loads(proc.stdout)
        candidates = report["candidates"]
        require(all(item["thread_id"] not in {"thread-agent", "thread-recent"} for item in candidates),
                "scanner must exclude subagents and recent sessions")
        large_row = next(item for item in candidates if item["thread_id"] == "thread-large")
        require(large_row["compaction_count"] == 2, "only decoded top-level compactions count")
        spaced_naive_count = large.read_text(encoding="utf-8").count('"type": "compacted"')
        require(spaced_naive_count == 3,
                "fixture must make spaced substring counting overcount the nested payload")
        require(large_row["compaction_count"] != spaced_naive_count,
                "scanner must reject naive spaced substring counting")
        require(large_row["handoff_required"] is True, "second compaction requires handoff")
        require(large_row["repo_root"] is None
                and large_row["repo_root_provenance"] == "unknown",
                "real persisted schema must not invent a canonical repo root")
        unknown = next(item for item in candidates if item["thread_id"] == "thread-a")
        require(unknown["repo_root"] is None and unknown["repo_root_provenance"] == "unknown",
                "scanner must not infer a repo from cwd")
        tie_ids = [item["thread_id"] for item in candidates if item["thread_id"] in {"thread-a", "thread-b"}]
        require(tie_ids == ["thread-a", "thread-b"], "size ties need deterministic thread-id ordering")
        require([item["primary_rank"] for item in candidates] == list(range(1, len(candidates) + 1)),
                "primary size ranks must be contiguous")
        require(all(entry["primary_rank"] == next(
            item["primary_rank"] for item in candidates if item["thread_id"] == entry["thread_id"])
            for entry in report["returned_handoff_queue"]),
                "returned handoff queue must preserve primary ranks")
        require(report["queue_scope"] == "returned-window-only",
                "queue scope must disclose the bounded returned window")
        require(report["skipped_session_lines"] >= 1 and report["skipped_index_lines"] >= 1,
                "malformed session and index lines must be reported")
        after = _fixture_tree_fingerprint(codex_home)
        require(set(before) == set(after), "fixture scan must preserve the complete file path set")
        require(before == after,
                "fixture scan must preserve sha256/size/mtime/mode for every original file")
        # atime is intentionally not asserted: a read-only scanner cannot
        # control OS or mount read-access metadata behavior.
    print("[PASS] codex-fluent active session report")
```

Register the test before `test_runner_registry_complete`.

- [ ] **Step 2: Add failing argument-boundary tests**

```python
def test_codex_fluent_active_session_boundaries():
    script = ROOT / "codex" / "skills" / "codex-fluent" / "scripts" / "report_active_sessions.py"
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / ".codex"
        (home / "sessions").mkdir(parents=True)
        for value, expected in ((19, 2), (20, 0), (50, 0), (51, 2)):
            proc = subprocess.run([sys.executable, str(script), "--codex-home", str(home),
                                   "--limit", str(value), "--format", "json"],
                                  capture_output=True, text=True, check=False)
            require(proc.returncode == expected, f"unexpected limit result for {value}")
        valid_zero_age = subprocess.run([sys.executable, str(script), "--codex-home", str(home),
                                         "--older-than-days", "0", "--format", "json"],
                                        capture_output=True, text=True, check=False)
        require(valid_zero_age.returncode == 0, "older-than-days must accept zero")
        invalid_age = subprocess.run([sys.executable, str(script), "--codex-home", str(home),
                                      "--older-than-days", "-1"],
                                     capture_output=True, text=True, check=False)
        require(invalid_age.returncode == 2, "older-than-days must reject negative values")
        require("older-than-days must be at least 0" in invalid_age.stderr,
                "negative-age error must be explicit")
    print("[PASS] codex-fluent active session boundaries")
```

- [ ] **Step 2A: Add selection, timestamp, source-shape, queue-scope, and Markdown golden tests**

Use one fixture generator that creates 60 persisted-schema sessions with
deterministic byte sizes. At least 55 must be eligible. Do not add synthetic
`git_toplevel` or `project_root` fields. Add these imports and the complete
fixture implementation before the tests. Every session is padded to an exact
byte count with a valid `event_msg`, so size ordering does not depend on JSON
whitespace or filesystem allocation:

```python
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass(frozen=True)
class _FixtureSession:
    thread_id: str
    path: Path
    started_at: str | None
    size_bytes: int
    compaction_count: int


@dataclass(frozen=True)
class _SessionFixture:
    home: Path
    now: dt.datetime
    eligible_rows: tuple[_FixtureSession, ...]


def _write_session(
    path,
    *,
    thread_id,
    started_at,
    target_size,
    compaction_count=0,
    source_fields=None,
    omit_timestamp=False,
):
    payload = {"id": thread_id, "cwd": f"/work/{thread_id}"}
    event = {"type": "session_meta", "payload": payload}
    if not omit_timestamp:
        event["timestamp"] = started_at
        payload["timestamp"] = started_at
    payload.update(source_fields or {})
    events = [event]
    events.extend(
        {"timestamp": started_at, "type": "compacted", "payload": {}}
        for _ in range(compaction_count)
    )
    prefix = b"".join(
        (json.dumps(row, separators=(",", ":")) + "\n").encode("utf-8")
        for row in events
    )
    empty_pad = (
        json.dumps(
            {"type": "event_msg", "payload": {"message": ""}},
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    pad_length = target_size - len(prefix) - len(empty_pad)
    require(pad_length >= 0, f"target size too small for {thread_id}")
    pad = (
        json.dumps(
            {"type": "event_msg", "payload": {"message": "x" * pad_length}},
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    content = prefix + pad
    require(len(content) == target_size, f"exact fixture size drift for {thread_id}")
    path.write_bytes(content)
    return _FixtureSession(
        thread_id=thread_id,
        path=path,
        started_at=started_at,
        size_bytes=target_size,
        compaction_count=compaction_count,
    )


@contextmanager
def _session_fixture(count=60, eligible=56):
    require(count == 60 and eligible == 56, "fixture contract is exactly 60/56")
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / ".codex"
        sessions = home / "sessions" / "2026" / "05" / "01"
        sessions.mkdir(parents=True)
        now = dt.datetime(2026, 7, 10, tzinfo=dt.timezone.utc)
        old = "2026-05-01T00:00:00Z"
        recent = "2026-07-09T00:00:00Z"
        rows = []
        index_rows = []
        for index in range(count):
            thread_id = f"thread-{index:02d}"
            is_eligible = index < eligible
            is_subagent = index >= 58
            started_at = old if index < 56 or is_subagent else recent
            source_fields = {"thread_source": "subagent"} if is_subagent else {}
            compactions = 2 + (index % 3) if is_eligible else 0
            row = _write_session(
                sessions / f"rollout-{thread_id}.jsonl",
                thread_id=thread_id,
                started_at=started_at,
                target_size=20_000 - (index * 100),
                compaction_count=compactions,
                source_fields=source_fields,
            )
            index_rows.append({"id": thread_id, "thread_name": f"Task {index:02d}"})
            if is_eligible:
                rows.append(row)
        require(len(rows) == eligible, "fixture must expose exactly 56 eligible rows")
        (home / "session_index.jsonl").write_text(
            "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in index_rows),
            encoding="utf-8",
        )
        yield _SessionFixture(home=home, now=now, eligible_rows=tuple(rows))


def _run_report(home, *, limit, now, output_format="json"):
    script = ROOT / "codex" / "skills" / "codex-fluent" / "scripts" / "report_active_sessions.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--codex-home",
            str(home),
            "--older-than-days",
            "30",
            "--limit",
            str(limit),
            "--format",
            output_format,
            "--now",
            now.isoformat(),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    require(proc.returncode == 0, f"scanner failed: {proc.stderr}")
    return json.loads(proc.stdout) if output_format == "json" else proc.stdout


def _expected_size_order(rows):
    return sorted(rows, key=lambda row: (-row.size_bytes, row.started_at or "", row.thread_id))


def _run_timestamp_cases(cases, *, now):
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / ".codex"
        sessions = home / "sessions" / "2026" / "06" / "10"
        sessions.mkdir(parents=True)
        index_rows = []
        for index, (thread_id, (started_at, _)) in enumerate(cases.items()):
            _write_session(
                sessions / f"rollout-{thread_id}.jsonl",
                thread_id=thread_id,
                started_at=started_at,
                target_size=4_000 + index * 100,
                omit_timestamp=started_at is None,
            )
            index_rows.append({"id": thread_id, "thread_name": thread_id})
        (home / "session_index.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in index_rows), encoding="utf-8"
        )
        report = _run_report(home, limit=20, now=now)
        returned_ids = {row["thread_id"] for row in report["candidates"]}
        report["_fixture_eligibility"] = {
            thread_id: thread_id in returned_ids
            for thread_id, (started_at, _) in cases.items()
            if started_at is not None and started_at != "not-a-time"
        }
        return report


def _eligibility_map(report):
    return report["_fixture_eligibility"]


def _run_equal_size_timestamp_tiebreak_cases():
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / ".codex"
        sessions = home / "sessions" / "2026" / "05" / "01"
        sessions.mkdir(parents=True)
        cases = [
            ("same-a", "2026-05-01T02:00:00+02:00"),
            ("same-b", "2026-05-01T00:00:00Z"),
            ("offset-later", "2026-05-01T01:30:00+01:00"),
            ("naive", "2026-05-01T00:00:00"),
        ]
        index_rows = []
        for thread_id, started_at in cases:
            _write_session(
                sessions / f"rollout-{thread_id}.jsonl",
                thread_id=thread_id,
                started_at=started_at,
                target_size=4_096,
            )
            index_rows.append({"id": thread_id, "thread_name": thread_id})
        (home / "session_index.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in index_rows),
            encoding="utf-8",
        )
        return _run_report(
            home,
            limit=20,
            now=dt.datetime(2026, 7, 10, tzinfo=dt.timezone.utc),
        )


def _run_source_cases(source_shapes):
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / ".codex"
        sessions = home / "sessions" / "2026" / "05" / "01"
        sessions.mkdir(parents=True)
        index_rows = []
        ids = ["thread-source", "nested-source", "unknown-source", "absent-source"]
        for index, (thread_id, source_fields) in enumerate(zip(ids, source_shapes, strict=True)):
            _write_session(
                sessions / f"rollout-{thread_id}.jsonl",
                thread_id=thread_id,
                started_at="2026-05-01T00:00:00Z",
                target_size=4_000 + index * 100,
                source_fields=source_fields,
            )
            index_rows.append({"id": thread_id, "thread_name": thread_id})
        (home / "session_index.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in index_rows), encoding="utf-8"
        )
        return _run_report(
            home,
            limit=20,
            now=dt.datetime(2026, 7, 10, tzinfo=dt.timezone.utc),
        )


@contextmanager
def _golden_home():
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / ".codex"
        sessions = home / "sessions" / "2026" / "05" / "01"
        sessions.mkdir(parents=True)
        now = dt.datetime(2026, 7, 10, tzinfo=dt.timezone.utc)
        large = _write_session(
            sessions / "rollout-golden-large.jsonl",
            thread_id="golden-large",
            started_at="2026-05-01T00:00:00Z",
            target_size=4_096,
            compaction_count=2,
        )
        small = _write_session(
            sessions / "rollout-golden-small.jsonl",
            thread_id="golden-small",
            started_at="2026-05-01T00:00:00Z",
            target_size=2_048,
            compaction_count=0,
        )
        (home / "session_index.jsonl").write_text(
            json.dumps({"id": "golden-large", "thread_name": "Golden large"}) + "\n"
            + json.dumps({"id": "golden-small", "thread_name": "Golden small"}) + "\n",
            encoding="utf-8",
        )
        yield _SessionFixture(home=home, now=now, eligible_rows=(large, small))


def test_codex_fluent_selection_contract():
    with _session_fixture(count=60, eligible=56) as fixture:
        all_rows = _run_report(fixture.home, limit=50, now=fixture.now)
        expected = _expected_size_order(fixture.eligible_rows)
        require(all_rows["candidate_count"] == 56, "eligible count must be complete")
        for limit in (20, 30, 50):
            report = _run_report(fixture.home, limit=limit, now=fixture.now)
            require(report["returned_count"] == limit, f"limit={limit} count drift")
            require(
                [(row["thread_id"], row["primary_rank"])
                 for row in report["candidates"]]
                == [(row.thread_id, rank)
                    for rank, row in enumerate(expected[:limit], 1)],
                f"limit={limit} must return exact top-N IDs and ranks",
            )
        outside = expected[50]
        require(outside.compaction_count >= 2,
                "fixture must include a high-compaction eligible item outside top 50")
        require(outside.thread_id not in {
            row["thread_id"] for row in all_rows["returned_handoff_queue"]
        }, "queue must never audit outside the returned top-N window")
        require(all_rows["queue_scope"] == "returned-window-only",
                "bounded queue disclosure missing")


def test_codex_fluent_timestamp_and_source_contract():
    cutoff = dt.datetime(2026, 6, 10, 12, 0, tzinfo=dt.timezone.utc)
    cases = {
        "cutoff-exact": ("2026-06-10T12:00:00Z", True),
        "cutoff-minus-one": ("2026-06-10T11:59:59Z", True),
        "cutoff-plus-one": ("2026-06-10T12:00:01Z", False),
        "offset-equivalent": ("2026-06-10T08:00:00-04:00", True),
        "invalid": ("not-a-time", False),
        "missing": (None, False),
    }
    report = _run_timestamp_cases(cases, now=cutoff + dt.timedelta(days=30))
    require(report["invalid_or_missing_timestamp_count"] == 2,
            "invalid and missing timestamps must be skipped and counted")
    require(_eligibility_map(report) == {
        key: expected for key, (_, expected) in cases.items() if key not in {"invalid", "missing"}
    }, "eligibility must use inclusive UTC cutoff")

    tie_report = _run_equal_size_timestamp_tiebreak_cases()
    tie_rows = tie_report["candidates"]
    require(tie_report["invalid_or_missing_timestamp_count"] == 1,
            "timezone-naive timestamps must be skipped and counted")
    require([row["thread_id"] for row in tie_rows] == [
        "same-a", "same-b", "offset-later",
    ], "equal-size rows must sort by UTC instant, then thread_id for same instants")
    require([row["started_at"] for row in tie_rows] == [
        "2026-05-01T00:00:00.000000Z",
        "2026-05-01T00:00:00.000000Z",
        "2026-05-01T00:30:00.000000Z",
    ], "output must use canonical UTC Z timestamps before applying the tie-break")

    source_report = _run_source_cases([
        {"thread_source": "subagent"},
        {"source": {"subagent": {"parent_thread_id": "p"}}},
        {"source": "unrecognized-shape"},
        {},
    ])
    require(source_report["excluded_subagent_count"] == 2,
            "both observed persisted subagent shapes must be excluded")
    unknown = next(row for row in source_report["candidates"]
                   if row["thread_id"] == "unknown-source")
    require(unknown["source_kind"] == "unknown",
            "unknown shape stays eligible and is disclosed, never guessed")
    absent = next(row for row in source_report["candidates"]
                  if row["thread_id"] == "absent-source")
    require(absent["source_kind"] == "unknown",
            "absent source fields stay eligible and are disclosed as unknown")
    require(unknown["repo_root"] is None
            and unknown["repo_root_provenance"] == "unknown",
            "ordinary persisted schema must return nullable repo identity")


def test_codex_fluent_markdown_golden():
    with _golden_home() as fixture:
        rendered = _run_report(
            fixture.home, limit=20, now=fixture.now, output_format="markdown"
        )
        expected = (
            ROOT / "tests" / "fixtures" / "codex_fluent_report.golden.md"
        ).read_text(encoding="utf-8")
        require(rendered == expected,
                "Markdown headings, columns, queue scope, and rows must remain stable")
```

Register all three tests. The helper implementation is part of the same
`test_runner.py` slice and uses temporary directories only. Create
`tests/fixtures/codex_fluent_report.golden.md` with this exact content,
including its final newline:

```markdown
# Codex Fluent Active Session Report

- candidate_count: 2
- returned_count: 2
- queue_scope: returned-window-only
- skipped_session_lines: 0
- skipped_index_lines: 0
- invalid_or_missing_timestamp_count: 0
- excluded_subagent_count: 0

## Primary Size Ranking

| primary_rank | size_bytes | age_days | compaction_count | handoff_required | thread_id | title | cwd_label | repo_root |
|---:|---:|---:|---:|:---:|---|---|---|---|
| 1 | 4096 | 70 | 2 | true | golden-large | Golden large | /work/golden-large | unknown |
| 2 | 2048 | 70 | 0 | false | golden-small | Golden small | /work/golden-small | unknown |

## Returned Handoff Queue

| primary_rank | compaction_count | thread_id |
|---:|---:|---|
| 1 | 2 | golden-large |
```

The scanner Markdown renderer must emit this contract byte-for-byte. An empty
primary or queue section uses the same heading and header rows with no data
rows; no timestamp or tempdir-dependent path appears in Markdown. The fixture's
deterministic `/work/<thread_id>` `cwd_label` is intentionally allowed.

- [ ] **Step 3: Run all scanner tests and verify RED**

```bash
python3 -c 'import test_runner; test_runner.test_codex_fluent_active_session_report()'
python3 -c 'import test_runner; test_runner.test_codex_fluent_active_session_boundaries()'
python3 -c 'import test_runner; test_runner.test_codex_fluent_selection_contract()'
python3 -c 'import test_runner; test_runner.test_codex_fluent_timestamp_and_source_contract()'
python3 -c 'import test_runner; test_runner.test_codex_fluent_markdown_golden()'
```

Expected: each exits 1 because the scanner/contract is not implemented.

- [ ] **Step 4: Implement exact JSONL parsing and data contracts**

Create `report_active_sessions.py` with these core contracts; discovery and
rendering must use them without prefix/string matching:

```python
@dataclass
class Candidate:
    primary_rank: int
    thread_id: str
    title: str
    cwd_label: str
    repo_root: str | None
    repo_root_provenance: str
    session_path: str
    started_at: str
    age_days: int
    size_bytes: int
    compaction_count: int
    handoff_required: bool
    source_kind: str


def decoded_events(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                yield line_number, None
                continue
            yield line_number, event if isinstance(event, dict) else None


def count_top_level_compactions(path: Path) -> tuple[int, int]:
    count = 0
    malformed = 0
    for _, event in decoded_events(path):
        if event is None:
            malformed += 1
        elif event.get("type") == "compacted":
            count += 1
    return count, malformed


def validate_args(older_than_days: int, limit: int) -> None:
    if older_than_days < 0:
        raise ValueError("older-than-days must be at least 0")
    if not 20 <= limit <= 50:
        raise ValueError("limit must be between 20 and 50")
```

Timestamp and source logic must be explicit and UTC-normalized:

```python
class InvalidTimestamp(ValueError):
    pass


def parse_iso_utc(raw: str) -> datetime:
    if not isinstance(raw, str) or not raw:
        raise InvalidTimestamp("timestamp is missing")
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise InvalidTimestamp(f"invalid timestamp: {raw!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InvalidTimestamp(f"timezone offset required: {raw!r}")
    return parsed.astimezone(timezone.utc)


def canonical_utc_z(moment: datetime) -> str:
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise InvalidTimestamp("timezone-aware datetime required")
    return moment.astimezone(timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")


def eligible(started_at: str, *, now: datetime, older_than_days: int) -> bool:
    started = parse_iso_utc(started_at)  # raises InvalidTimestamp
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    cutoff = now.astimezone(timezone.utc) - timedelta(days=older_than_days)
    return started <= cutoff


def source_kind(payload: dict) -> str:
    if payload.get("thread_source") == "subagent":
        return "subagent"
    source = payload.get("source")
    if isinstance(source, dict) and "subagent" in source:
        return "subagent"
    return "unknown"


def canonical_repo(payload: dict, index_entry: dict) -> tuple[str | None, str]:
    # Start fail-closed for the current persisted schema. Add a source field
    # only after its canonical-root semantics are verified and tested.
    return None, "unknown"
```

For every accepted session, call `parse_iso_utc` once, store
`canonical_utc_z(parsed_started_at)` in `Candidate.started_at`, and use that
canonical value in the primary `(-size_bytes, started_at, thread_id)` key.
`parse_iso_utc` returns an aware UTC instant and rejects naive values. Never
order offset-bearing timestamp strings before normalization.

Sort primary candidates with `(-size_bytes, started_at, thread_id)`, assign
`primary_rank` once, and build the second view without changing it:

```python
returned_handoff_queue = [
    {"primary_rank": item.primary_rank, "thread_id": item.thread_id,
     "compaction_count": item.compaction_count}
    for item in sorted(
        (item for item in candidates if item.handoff_required),
        key=lambda item: (-item.compaction_count, item.primary_rank),
    )
]
report["queue_scope"] = "returned-window-only"
```

Build the queue only from the already sliced `candidates` list. First discover
and sort all eligible rows; then slice `candidates = eligible_rows[:limit]`,
assign ranks 1..N, and construct `returned_handoff_queue`. Never construct the
queue from all eligible rows.

- [ ] **Step 5: Run focused tests and verify GREEN**

```bash
python3 -c 'import test_runner; test_runner.test_codex_fluent_active_session_report()'
python3 -c 'import test_runner; test_runner.test_codex_fluent_active_session_boundaries()'
python3 -c 'import test_runner; test_runner.test_codex_fluent_selection_contract()'
python3 -c 'import test_runner; test_runner.test_codex_fluent_timestamp_and_source_contract()'
python3 -c 'import test_runner; test_runner.test_codex_fluent_markdown_golden()'
```

Expected: all commands exit 0 with their PASS markers.

- [ ] **Step 6: Commit the scanner slice**

```bash
git add codex/skills/codex-fluent/scripts/report_active_sessions.py \
  tests/fixtures/codex_fluent_report.golden.md test_runner.py
git commit -m "feat: add report-only Codex session triage"
```

### Task 3: Route codex-fluent Through the Scanner

**Files:**
- Modify: `codex/skills/codex-fluent/SKILL.md`
- Modify: `codex/skills/codex-fluent/references/maintenance-checklist.md`
- Modify: `test_runner.py`

- [ ] **Step 1: Add the failing skill-contract test**

```python
def test_codex_fluent_report_only_contract():
    root = ROOT / "codex" / "skills" / "codex-fluent"
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    checklist = (root / "references" / "maintenance-checklist.md").read_text(encoding="utf-8")
    required = [
        "scripts/report_active_sessions.py", "--older-than-days 30", "--limit 30",
        "20", "50", "primary_rank", "returned_handoff_queue", "compaction_count",
        "handoff_required", "report-only", "Do not archive or delete",
        "queue_scope=returned-window-only", "terminal chat handoff",
    ]
    for term in required:
        require(term in skill, f"codex-fluent missing report contract term: {term}")
    require("Review the 20–50 item returned handoff queue" in checklist,
            "maintenance checklist must review the bounded queue")
    combined = skill + "\n" + checklist
    normalized = " ".join(combined.lower().split())
    forbidden = [
        "always write a handoff document",
        "must write a repo-native handoff",
        "archive authorization implies handoff-file authorization",
    ]
    for phrase in forbidden:
        require(phrase not in combined.lower(),
                f"unconditional file handoff conflicts with chat default: {phrase}")
    require("exact documentation path" in " ".join(combined.split()),
            "file handoff requires exact-path authorization")
    require("archive authorization does not imply file-write authorization" in normalized,
            "archive permission must not imply file-write authorization")
    require("apply authorization does not imply file-write authorization" in normalized,
            "apply permission must not imply file-write authorization")
    require("keep active" in normalized,
            "no file authorization must keep the task active")
    print("[PASS] codex-fluent report-only contract")
```

- [ ] **Step 2: Run the test and verify RED**

```bash
python3 -c 'import test_runner; test_runner.test_codex_fluent_report_only_contract()'
```

Expected: exit code 1 identifying the first missing term.

- [ ] **Step 3: Document deterministic report-only routing**

Add a skill section containing the exact runtime invocation, the inclusive
20–50 bound, `older_than_days >= 0`, immutable primary size rank, separate
returned handoff queue and `queue_scope=returned-window-only`, nullable
evidence-backed repo root, malformed-line counts, and the prohibition on
archive/delete/apply.

Also replace any existing unconditional or mandatory handoff-document wording
in both files with this consistent policy: terminal chat handoff is the
default; a file is allowed only when the original task pre-authorized the exact
documentation path; archive authorization does not imply file-write
authorization; apply authorization does not imply file-write authorization;
without exact-path file authorization, keep the task active and do not archive
it. Update the checklist with:

```markdown
- [ ] Review the 20–50 item returned handoff queue by its primary_rank
  references; queue_scope is returned-window-only. Keep active unless a
  separately authorized workflow confirms a handoff and action.
- [ ] Use terminal chat handoff by default. A repo-native file requires the
  original task to authorize the exact documentation path; archive authorization
  does not imply file-write authorization; apply authorization does not imply
  file-write authorization. Without it, keep active and do not archive.
```

- [ ] **Step 4: Verify GREEN with source-only checks**

```bash
python3 -c 'import test_runner; test_runner.test_codex_fluent_report_only_contract()'
python3 -m py_compile codex/skills/codex-fluent/scripts/report_active_sessions.py
git diff --check -- codex/skills/codex-fluent test_runner.py
```

Expected: all source-stage commands exit 0. Do not run
`scripts/check_skill_compatibility.py` yet: the runtime intentionally remains
unsynchronized until Task 5, so managed parity would be a false failure.

- [ ] **Step 5: Commit the skill-routing slice**

```bash
git add codex/skills/codex-fluent/SKILL.md codex/skills/codex-fluent/references/maintenance-checklist.md test_runner.py
git commit -m "docs: route codex fluent through bounded triage"
```

### Task 4: Register and Document the Runtime Surface

**Files:**
- Modify: `docs/CODEX_ENV_REPRODUCTION.md`
- Modify: `docs/repo-index.md`
- Modify: `docs/surfaces.json`

- [ ] **Step 1: Verify the new surface is initially RED**

Add this object to the intended `docs/surfaces.json` diff first, before adding
the corresponding `docs/repo-index.md` entry:

```json
{
  "path": "codex/skills/codex-fluent/scripts/report_active_sessions.py",
  "role": "read-only active Codex session ranking and handoff audit",
  "audience": ["runtime", "codex", "human"]
}
```

Run:

```bash
python3 scripts/check_surfaces.py --repo-root "$(pwd)" --json
```

Expected: exit code 1 because the human-readable surface mirror is missing.

- [ ] **Step 2: Add exact documentation and surface mirror**

Document the three-layer guarantee, source/runtime ownership, exact invocation,
chat-handoff default, evidence-only repo identity, primary rank plus separate
`returned_handoff_queue` with returned-window-only scope, and report-only safety
boundary. Add the scanner path as a
backticked Runtime Surfaces bullet in `docs/repo-index.md` matching the role in
`docs/surfaces.json`.

- [ ] **Step 3: Verify GREEN with existing checks**

```bash
python3 scripts/check_surfaces.py --repo-root "$(pwd)" --json
git diff --check -- docs/CODEX_ENV_REPRODUCTION.md docs/repo-index.md docs/surfaces.json
```

Expected: both commands exit 0; surface checker reports no missing or drifted
entries.

- [ ] **Step 4: Commit the documentation slice**

```bash
git add docs/CODEX_ENV_REPRODUCTION.md docs/repo-index.md docs/surfaces.json
git commit -m "docs: register Codex task triage surface"
```

### Task 5: Synchronize Only the Allowed Runtime Paths

**Files:**
- Runtime update: `~/.codex/AGENTS.md`
- Runtime update: `~/.codex/skills/codex-fluent/`

- [ ] **Step 0: Obtain future write authority, then run the automation capability/schema preflight before any runtime write**

Do not start this task merely because this plan exists. First obtain explicit
user authorization to write exactly `~/.codex/AGENTS.md` and
`~/.codex/skills/codex-fluent/`; this authorization does not authorize the
automation update. Use the current session's actual tool inventory, not shell
discovery, to locate the exposed `automation_update` tool, read its formal
schema, and perform a read-only view with
`{"id":"weekly-codex-maintenance-report","mode":"view"}`. Preserve the full
formal declaration, the formal required-field set, and the complete view
response as task evidence for Task 6. The current expected writable fields are
`id`, `mode`, `kind`, `name`, `prompt`, `rrule`, `status`,
`executionEnvironment`, `model`, `projectId`, and `reasoningEffort`, but the
live formal schema—not this list or TOML—is authoritative. If the tool is
absent, the ID is not unique, view fails, or the schema has an additional,
renamed, or missing required field without an explicit mapping, stop before
runtime or automation mutation.

- [ ] **Step 1: Verify source gates, declare the allowed targets, and validate paths**

Run Task 5 Steps 1–4 in one non-interactive shell process so the
`runtime_backup` location and gate environment created here remain live for each
later step. Do not continue manually after any nonzero gate result: `run_gate`
records the receipt and exits that shell before another write, verification, or
Task 6 action can begin.

```bash
set -euo pipefail
git status --short
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
runtime_backup="$HOME/Documents/Codex/codex-backups/codex-thread-discipline-$timestamp"
mkdir -p "$runtime_backup"
export GATE_RECEIPTS="$runtime_backup/gate-receipts.jsonl"
export PARTIAL_STATE="$runtime_backup/partial-runtime-state.json"
export GATE_LOG_DIR="$runtime_backup/gates"
mkdir -p "$GATE_LOG_DIR"
# This is the sole canonical gate helper for Tasks 5–7. Do not define a
# second helper in a later task or copy an older helper from this plan.
cat > "$runtime_backup/run_gate.sh" <<'SH'
set -Eeuo pipefail

record_gate_result() {
  label="$1"
  affected_target="$2"
  command="$3"
  status="$4"
  result_file="$5"
  timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  last_success_before="${LAST_SUCCESS_OPERATION:-pre-write}"
  python3 - "$GATE_RECEIPTS" "$label" "$affected_target" "$command" \
    "$status" "$result_file" "$timestamp" <<'PY'
import json
from pathlib import Path
import sys

receipts, label, target, command, status, result_file, timestamp = sys.argv[1:]
key_output = Path(result_file).read_text(encoding="utf-8", errors="replace")[:2000]
with Path(receipts).open("a", encoding="utf-8") as handle:
    handle.write(json.dumps({
        "command": command,
        "exit_code": int(status),
        "key_output": key_output,
        "timestamp": timestamp,
        "gate": label,
        "affected_target": target,
    }, sort_keys=True) + "\n")
PY
  if [ "$status" -ne 0 ]; then
    python3 - "$PARTIAL_STATE" "$label" "$affected_target" \
      "$last_success_before" "$timestamp" "$status" <<'PY'
import json
from pathlib import Path
import sys

path, failed_gate, affected_target, last_success, timestamp, status = sys.argv[1:]
Path(path).write_text(json.dumps({
    "partial_runtime_state": True,
    "failed_gate": failed_gate,
    "affected_target": affected_target,
    "last_success_operation": last_success,
    "timestamp": timestamp,
    "exit_code": int(status),
}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
PY
    exit "$status"
  fi
  LAST_SUCCESS_OPERATION="$label"
}

run_gate() {
  label="$1"
  affected_target="$2"
  shift 2
  log="$GATE_LOG_DIR/$label.log"
  set +e
  "$@" > "$log" 2>&1
  status=$?
  set -e
  record_gate_result "$label" "$affected_target" "$*" "$status" "$log"
  cat "$log"
}
SH
source "$runtime_backup/run_gate.sh"
run_gate "rsync-version-evidence" "host-rsync" rsync --version
run_gate "source-diff" "repo-source" \
  git diff --check -- codex/AGENTS.md codex/skills/codex-fluent
printf '%s\n' \
  "$HOME/.codex/AGENTS.md" \
  "$HOME/.codex/skills/codex-fluent/" \
  > "$runtime_backup/allowed-paths.txt"
run_gate "runtime-target-validation" "~/.codex/AGENTS.md,~/.codex/skills/codex-fluent/" \
  python3 - "$HOME/.codex/AGENTS.md" "$HOME/.codex/skills/codex-fluent" <<'PY'
import os, stat, sys
from pathlib import Path

expected = [
    Path.home() / ".codex" / "AGENTS.md",
    Path.home() / ".codex" / "skills" / "codex-fluent",
]
provided = [Path(raw) for raw in sys.argv[1:]]
assert provided == expected
home = Path.home().resolve()
for target in provided:
    assert target.is_absolute() and target.exists(), target
    assert not stat.S_ISLNK(target.lstat().st_mode), target
    assert target.resolve() == target, (target, target.resolve())
    parent = target.parent
    while parent != home:
        assert parent.exists(), parent
        assert not stat.S_ISLNK(parent.lstat().st_mode), parent
        assert parent.resolve().is_relative_to(home), parent
        parent = parent.parent
print("runtime_targets=2 symlink_escape=false")
PY
run_gate "source-manifest" "repo-source" \
  python3 - "$runtime_backup/source-manifest.json" <<'PY'
from hashlib import sha256
import json
from pathlib import Path
import stat
import sys

source_root = Path.cwd() / "codex" / "skills" / "codex-fluent"
runtime_root = Path.home() / ".codex" / "skills" / "codex-fluent"
assert source_root.is_dir() and not stat.S_ISLNK(source_root.lstat().st_mode)
assert runtime_root.is_dir() and not stat.S_ISLNK(runtime_root.lstat().st_mode)
allowed_paths = {"."}
files = []
for path in sorted(source_root.rglob("*")):
    relative = path.relative_to(source_root)
    relative_text = relative.as_posix()
    assert relative_text and not path.is_symlink(), relative_text
    allowed_paths.add(relative_text)
    destination = runtime_root / relative
    while destination != runtime_root:
        try:
            mode = destination.lstat().st_mode
        except FileNotFoundError:
            destination = destination.parent
            continue
        assert not stat.S_ISLNK(mode), destination
        destination = destination.parent
    if path.is_file():
        files.append({
            "relative_path": relative_text,
            "sha256": sha256(path.read_bytes()).hexdigest(),
        })
assert files, "managed source must not be empty"
Path(sys.argv[1]).write_text(json.dumps({
    "allowed_paths": sorted(allowed_paths),
    "files": files,
}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(f"managed_source_files={len(files)} allowed_source_paths={len(allowed_paths)}")
PY
```

Immediately after the source-manifest gate, run this disposable fault fixture
through the same guard before any backup or write. It must detect a dangling
child symlink via `lstat()` rather than treating `Path.exists()` as absence:

```bash
run_gate "broken-child-symlink-guard" "runtime-target-validation" \
  python3 - <<'PY'
import stat
import tempfile
from pathlib import Path

def assert_no_symlink_escape(destination: Path, root: Path) -> None:
    while destination != root:
        try:
            mode = destination.lstat().st_mode
        except FileNotFoundError:
            destination = destination.parent
            continue
        assert not stat.S_ISLNK(mode), destination
        destination = destination.parent

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp) / "runtime"
    root.mkdir()
    dangling = root / "broken-child"
    dangling.symlink_to("missing-target")
    try:
        assert_no_symlink_escape(dangling, root)
    except AssertionError as exc:
        assert exc.args == (dangling,)
        print("broken_child_symlink_guard=pass")
    else:
        raise AssertionError("dangling child symlink was not rejected")
PY
```

Expected: the gate exits 0 only after the fixture proves that the dangling
child is rejected. A failure records the normal receipt and
`partial-runtime-state`, and no runtime backup or write may begin.

Before backing up or writing either runtime target, fault-inject the gate runner
in a disposable evidence directory. The nested shell must return the injected
status, write both receipts, and never create its `after-failure` marker:

```bash
failure_probe="$runtime_backup/gate-failure-probe"
mkdir -p "$failure_probe"
set +e
bash -c 'source "$1"; run_gate "injected-failure" "probe-only" sh -c "exit 73"; touch "$2/after-failure"' \
  bash "$runtime_backup/run_gate.sh" "$failure_probe"
failure_status=$?
set -e
test "$failure_status" -eq 73
test ! -e "$failure_probe/after-failure"
python3 - "$GATE_RECEIPTS" "$PARTIAL_STATE" <<'PY'
import json
from pathlib import Path
import sys

receipts = [json.loads(line) for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()]
assert receipts[-1]["gate"] == "injected-failure"
assert receipts[-1]["exit_code"] == 73
partial = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
assert partial["partial_runtime_state"] is True
assert partial["failed_gate"] == "injected-failure"
assert partial["exit_code"] == 73
print("gate_fault_injection=pass after_failure=false")
PY
```

Expected: every non-injected gate exits 0; the manifest has exactly two expected
absolute targets; both targets exist and neither they nor their relevant parents
escape through a symlink. `source-manifest.json` lists every allowed
source-relative path plus the SHA-256 of each managed source file. The persistent
backup directory remains until acceptance or explicit cleanup. The deliberately
failed probe returns 73 rather than 0 and proves that no command after a failed
gate is run.

- [ ] **Step 2: Back up both runtime targets without changing runtime**

```bash
set -euo pipefail
source "$runtime_backup/run_gate.sh"
run_gate "backup-agents" "~/.codex/AGENTS.md" \
  cp -p "$HOME/.codex/AGENTS.md" "$runtime_backup/AGENTS.md.before"
run_gate "backup-codex-fluent" "~/.codex/skills/codex-fluent/" \
  cp -a "$HOME/.codex/skills/codex-fluent" "$runtime_backup/codex-fluent.before"
```

Expected: all commands exit 0 and both authorized targets have restorable
backups. Runtime remains unchanged. Do not invoke a broad sync helper.

- [ ] **Step 3: Audit a dry-run, then overlay codex-fluent without a pipeline or deletion**

```bash
set -euo pipefail
source "$runtime_backup/run_gate.sh"
run_gate "codex-fluent-rsync-dry-run" "~/.codex/skills/codex-fluent/" \
  rsync -a --dry-run --itemize-changes --out-format='%i %n%L' \
    codex/skills/codex-fluent/ \
    "$HOME/.codex/skills/codex-fluent/"
dry_run_log="$GATE_LOG_DIR/codex-fluent-rsync-dry-run.log"
run_gate "codex-fluent-dry-run-manifest-audit" "~/.codex/skills/codex-fluent/" \
  python3 - "$runtime_backup/source-manifest.json" "$dry_run_log" <<'PY'
import json
from pathlib import Path, PurePosixPath
import sys

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
allowed_paths = set(manifest["allowed_paths"])
items = Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
known_itemize_widths = {9, 11}
for item in items:
    if not item.strip():
        continue
    parts = item.split(" ", 1)
    assert len(parts) == 2 and len(parts[0]) in known_itemize_widths, item
    relative = PurePosixPath(parts[1])
    relative_text = relative.as_posix()
    assert not relative.is_absolute() and ".." not in relative.parts, relative
    assert relative_text in allowed_paths, (relative_text, sorted(allowed_paths))
print(f"dry_run_items={len(items)} destination_scope=codex-fluent manifest_bounded=true")
PY
run_gate "agents-copy" "~/.codex/AGENTS.md" \
  cp -p codex/AGENTS.md "$HOME/.codex/AGENTS.md"
run_gate "codex-fluent-rsync-write" "~/.codex/skills/codex-fluent/" \
  rsync -a --itemize-changes --out-format='%i %n%L' \
    codex/skills/codex-fluent/ \
    "$HOME/.codex/skills/codex-fluent/"
```

Expected: the recorded host `rsync --version` is retained as evidence; every
dry-run itemize token is exactly 9 or 11 characters, every dry-run path is
relative, contains no parent traversal, and is an exact allowed source-manifest
path; an unknown token format stops before a write. The real command exits 0.
Each gate writes
`command`, `exit_code`, `key_output`, and `timestamp` to
`gate-receipts.jsonl`; a nonzero status writes `partial-runtime-state.json` and
exits before `agents-copy` or the real rsync can run. Neither command uses
`--delete`, and no pipeline can mask the rsync exit status.

- [ ] **Step 4: Prove source-file parity and inventory runtime-only files separately**

```bash
set -euo pipefail
source "$runtime_backup/run_gate.sh"
run_gate "managed-source-parity" "~/.codex/AGENTS.md,~/.codex/skills/codex-fluent/" \
  python3 - "$runtime_backup" <<'PY'
from hashlib import sha256
import json
from pathlib import Path
import stat
import sys

repo = Path.cwd()
source_root = repo / "codex" / "skills" / "codex-fluent"
runtime_root = Path.home() / ".codex" / "skills" / "codex-fluent"
backup = Path(sys.argv[1])

manifest = json.loads((backup / "source-manifest.json").read_text(encoding="utf-8"))
managed = [Path(item["relative_path"]) for item in manifest["files"]]
assert managed == sorted(
    path.relative_to(source_root)
    for path in source_root.rglob("*")
    if path.is_file()
), "source manifest must enumerate exactly the managed source files"
for relative in managed:
    source = source_root / relative
    runtime = runtime_root / relative
    assert source.is_file() and runtime.is_file(), relative
    assert not stat.S_ISLNK(source.lstat().st_mode), source
    assert not stat.S_ISLNK(runtime.lstat().st_mode), runtime
    assert runtime.resolve().is_relative_to(runtime_root.resolve()), runtime
    assert sha256(source.read_bytes()).digest() == sha256(runtime.read_bytes()).digest(), relative
runtime_files = {path.relative_to(runtime_root) for path in runtime_root.rglob("*") if path.is_file()}
runtime_only = sorted(str(path) for path in runtime_files - set(managed))
(backup / "runtime-only-inventory.txt").write_text("\n".join(runtime_only) + "\n", encoding="utf-8")
agents_source = repo / "codex" / "AGENTS.md"
agents_runtime = Path.home() / ".codex" / "AGENTS.md"
assert sha256(agents_source.read_bytes()).digest() == sha256(agents_runtime.read_bytes()).digest()
print(f"managed_source_files={len(managed)} source_file_parity=true runtime_only={len(runtime_only)}")
PY
run_gate "managed-skill-compatibility" "~/.codex/skills/codex-fluent/" \
  python3 scripts/check_skill_compatibility.py --repo-root "$(pwd)" --codex-home "$HOME/.codex"
```

Expected: source-file checksum parity and the managed compatibility check pass.
Runtime-only files are reported but neither treated as source drift nor deleted.
Retain the backup path and `gate-receipts.jsonl` in the delivery report until
acceptance. A failed parity or compatibility gate writes `partial-runtime-state`
and prevents Task 6 from starting.

- [ ] **Step 5: Fail closed on any activation error and record, but do not execute, rollback**

Record these exact commands in the runtime evidence without running them after
a successful activation:

```bash
cp -p "$runtime_backup/AGENTS.md.before" "$HOME/.codex/AGENTS.md"
rsync -a --itemize-changes \
  "$runtime_backup/codex-fluent.before/" \
  "$HOME/.codex/skills/codex-fluent/"
```

The default action is to record these commands without running them. If any
path validation, backup, dry-run, write, checksum, or compatibility gate fails,
stop before every remaining runtime or automation step and report
`partial_runtime_state` with the last successful operation and affected target.
Obtain separate explicit user authorization before the exact rollback. Do not
automatically restore, do not continue to Task 6, and do not delete runtime-only
files. This non-destructive rollback overlay restores backed-up managed files
but intentionally does not remove later runtime-only or newly added files; any
destructive cleanup is a separate user-scoped decision. Forward and unattended
operations remain deletion-free.

### Task 6: Upgrade the Existing Weekly Automation with Rollback Evidence

**Files:**
- Runtime automation update: unique ID `weekly-codex-maintenance-report`

- [ ] **Step 1: Reassert live schema, fetch the unique automation, and normalize writable state**

The explicit runtime authority from Task 5 never authorizes this step's update:
obtain separate explicit user authorization before any automation mutation.
Immediately before mutation, repeat Task 5 Step 0 and stop if the tool name,
formal schema, required-field set, or read-only view differs from the captured
evidence. Persist the fresh formal declaration and complete read-only view with
the runtime backup evidence. The formal schema and its view response are the
source of truth. Read
`~/.codex/automations/weekly-codex-maintenance-report/automation.toml` with
`tomllib` only as a read-only storage cross-check; do not edit it. The current
storage-to-tool mapping is:

| TOML | tool argument |
|---|---|
| `id` | `id` |
| constant `"update"` | `mode` |
| `kind` | `kind` |
| `name` | `name` |
| `prompt` | `prompt` |
| `rrule` | `rrule` |
| `status` | `status` |
| `execution_environment` | `executionEnvironment` |
| `model` | `model` |
| `target.project_id` | `projectId` |
| `reasoning_effort` | `reasoningEffort` |

`version` is storage-format metadata. `created_at`, `updated_at`, and `cwds` are
server-managed and excluded from update payloads; `target.type` must equal
`project`. Save the original TOML bytes as `raw_before_toml` and parsed object
as `raw_before`. Before Task 6 Step 2, normalize the current tool view into the
same argument names in the right column and assert every non-server-managed
value equals `raw_before`; any mismatch is schema/state drift and stops without
mutation. Save two derived evidence files alongside the complete raw tool
evidence: `automation-schema.json` contains exactly `tool_name` and the sorted
`required_fields` copied from the current formal schema; and
`automation-view-before.json` is the normalized flat writable object using the
right-column names. Do not invent a missing field, silently discard an added
required field, or use the TOML mapping to paper over a tool-view mismatch.

- [ ] **Step 2: Construct schema-complete forward and rollback payloads**

Preserve the existing maintenance prompt in full; add the bounded thread-triage
requirements as a final managed appendix rather than replacing the existing
active-session, archived-session, worktree, log, config, process, or other
report-only duties. The appendix calls the scanner with `--older-than-days 30
--limit 30`, displays the primary size ranking and a separate
`returned_handoff_queue` with `primary_rank` references, reports
`queue_scope=returned-window-only`, malformed counts and evidence-backed
nullable repo roots, and prohibits every mutation named in the global
constraints. Construct both complete payloads with this executable code:

```bash
set -euo pipefail
source "$runtime_backup/run_gate.sh"
run_gate "automation-payload-construction" "weekly-codex-maintenance-report" \
  python3 - "$runtime_backup/automation-schema.json" \
  "$runtime_backup/automation-view-before.json" \
  "$runtime_backup" <<'PY'
import hashlib
import json
import tomllib
from pathlib import Path
import sys

schema_evidence_path = Path(sys.argv[1])
view_evidence_path = Path(sys.argv[2])
runtime_backup = Path(sys.argv[3])
automation_path = (
    Path.home() / ".codex" / "automations"
    / "weekly-codex-maintenance-report" / "automation.toml"
)
raw_before_toml = automation_path.read_bytes()
raw_before = tomllib.loads(raw_before_toml.decode("utf-8"))
(runtime_backup / "automation-raw-before.toml").write_bytes(raw_before_toml)
required_tool_fields = frozenset({
    "id", "mode", "kind", "name", "prompt", "rrule", "status",
    "executionEnvironment", "model", "projectId", "reasoningEffort",
})
schema_evidence = json.loads(schema_evidence_path.read_text(encoding="utf-8"))
view_before = json.loads(view_evidence_path.read_text(encoding="utf-8"))
assert set(schema_evidence) == {"tool_name", "required_fields"}
assert isinstance(schema_evidence["tool_name"], str) and schema_evidence["tool_name"]
assert frozenset(schema_evidence["required_fields"]) == required_tool_fields
assert set(view_before) == required_tool_fields
assert raw_before["id"] == "weekly-codex-maintenance-report"
assert raw_before["target"]["type"] == "project"

rollback_prompt = raw_before["prompt"]
marker_begin = "<!-- THREAD_TRIAGE_AUTOMATION_V1:BEGIN -->"
marker_end = "<!-- THREAD_TRIAGE_AUTOMATION_V1:END -->"
bounded_queue_appendix = (
    "Use codex-fluent report-only mode and run scripts/report_active_sessions.py "
    "with --older-than-days 30 --limit 30. Show the immutable primary size "
    "ranking and separate returned_handoff_queue using primary_rank references; "
    "report queue_scope=returned-window-only, malformed-line counts, and nullable "
    "evidence-backed repo roots. Do not archive, delete, move, prune, rotate, "
    "normalize, apply, create handoff files, or otherwise mutate Codex state."
)

def split_managed_appendix(prompt):
    begin_count = prompt.count(marker_begin)
    end_count = prompt.count(marker_end)
    assert begin_count == end_count
    assert begin_count in (0, 1), "managed appendix marker must be unique"
    if begin_count == 0:
        return prompt.rstrip(), False
    prefix, marked_tail = prompt.split(marker_begin, 1)
    _old_appendix, suffix = marked_tail.split(marker_end, 1)
    assert not suffix.strip(), "managed appendix must remain the final block"
    return prefix.rstrip(), True

def upsert_bounded_queue_appendix(prompt):
    preserved_prompt, _had_managed_appendix = split_managed_appendix(prompt)
    managed_block = (
        f"{marker_begin}\n{bounded_queue_appendix.strip()}\n{marker_end}"
    )
    return (
        f"{preserved_prompt}\n\n{managed_block}"
        if preserved_prompt else managed_block
    )

preserved_prompt, had_managed_appendix = split_managed_appendix(rollback_prompt)
new_prompt = upsert_bounded_queue_appendix(rollback_prompt)
assert new_prompt.startswith(f"{preserved_prompt}\n\n") if preserved_prompt else True
assert marker_begin not in preserved_prompt and marker_end not in preserved_prompt
assert new_prompt.count(marker_begin) == new_prompt.count(marker_end) == 1
assert new_prompt.count(bounded_queue_appendix.strip()) == 1
assert upsert_bounded_queue_appendix(new_prompt) == new_prompt
if not had_managed_appendix:
    assert new_prompt.startswith(f"{rollback_prompt.rstrip()}\n\n")

def tool_payload(config, prompt):
    payload = {
        "id": config["id"],
        "mode": "update",
        "kind": config["kind"],
        "name": config["name"],
        "prompt": prompt,
        "rrule": config["rrule"],
        "status": config["status"],
        "executionEnvironment": config["execution_environment"],
        "model": config["model"],
        "projectId": config["target"]["project_id"],
        "reasoningEffort": config["reasoning_effort"],
    }
    assert frozenset(payload) == required_tool_fields
    assert all(payload[key] not in (None, "") for key in required_tool_fields)
    return payload

forward_payload = tool_payload(raw_before, new_prompt)
rollback_payload = tool_payload(raw_before, rollback_prompt)
assert view_before == rollback_payload, "tool view and TOML mapping drifted"
assert forward_payload.keys() == rollback_payload.keys()
assert {k: v for k, v in forward_payload.items() if k != "prompt"} == {
    k: v for k, v in rollback_payload.items() if k != "prompt"
}
assert forward_payload["prompt"] != rollback_payload["prompt"]
rollback_prompt_sha256 = hashlib.sha256(rollback_prompt.encode()).hexdigest()
rollback_prompt_length = len(rollback_prompt)
(runtime_backup / "automation-forward-payload.json").write_text(
    json.dumps(forward_payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
)
(runtime_backup / "automation-rollback-payload.json").write_text(
    json.dumps(rollback_payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps({
    "forward_payload": forward_payload,
    "rollback_payload": rollback_payload,
    "rollback_prompt_sha256": rollback_prompt_sha256,
    "rollback_prompt_length": rollback_prompt_length,
}, sort_keys=True, indent=2))
PY
```

Before mutation, compare `required_tool_fields` to the required properties in
the freshly displayed formal tool schema and stop on any missing or added field.
Call the actual formal `automation_update` tool identified in the fresh
preflight with the decoded `forward_payload` object; do not send a prompt-only
partial update or assume a historical tool namespace remains valid. Treat that
application-tool invocation as a fatal gate: record `command`, `exit_code`,
`key_output`, and `timestamp` in `gate-receipts.jsonl` immediately from the real
tool result. If the call errors, returns a malformed state, or does not identify
the requested automation, write `partial-runtime-state.json` with the last
successful gate and stop; do not issue the after-view or start Task 7. Only a
successful forward result may enter Step 3.

- [ ] **Step 3: Update, capture complete after-state, and calculate a real recursive diff**

After the forward tool call succeeds, repeat the formal-schema preflight and
view the same ID again. Save the fresh complete schema/view evidence and a
normalized writable `automation-view-after.json` beside the before evidence.
Do not proceed if the required-field set changed. Then run this self-contained
comparison, which treats the before/after tool views as the authority and uses
TOML only to detect a raw storage-side change outside `prompt` or
server-managed `updated_at`:

```bash
set -euo pipefail
source "$runtime_backup/run_gate.sh"
run_gate "automation-after-state-diff" "weekly-codex-maintenance-report" \
  python3 - "$runtime_backup" <<'PY'
import hashlib
import json
import tomllib
from pathlib import Path
import sys

backup = Path(sys.argv[1])
required_tool_fields = frozenset({
    "id", "mode", "kind", "name", "prompt", "rrule", "status",
    "executionEnvironment", "model", "projectId", "reasoningEffort",
})
view_before = json.loads((backup / "automation-view-before.json").read_text(encoding="utf-8"))
view_after = json.loads((backup / "automation-view-after.json").read_text(encoding="utf-8"))
forward_payload = json.loads((backup / "automation-forward-payload.json").read_text(encoding="utf-8"))
rollback_payload = json.loads((backup / "automation-rollback-payload.json").read_text(encoding="utf-8"))
for payload in (view_before, view_after, forward_payload, rollback_payload):
    assert frozenset(payload) == required_tool_fields

def recursive_diff(before, after, path=()):
    if isinstance(before, dict) and isinstance(after, dict):
        changes = []
        for key in sorted(set(before) | set(after)):
            child = path + (key,)
            if key not in before:
                changes.append({"path": child, "kind": "added", "after": after[key]})
            elif key not in after:
                changes.append({"path": child, "kind": "removed", "before": before[key]})
            else:
                changes.extend(recursive_diff(before[key], after[key], child))
        return changes
    if isinstance(before, list) and isinstance(after, list):
        changes = []
        for index in range(max(len(before), len(after))):
            child = path + (index,)
            if index >= len(before):
                changes.append({"path": child, "kind": "added", "after": after[index]})
            elif index >= len(after):
                changes.append({"path": child, "kind": "removed", "before": before[index]})
            else:
                changes.extend(recursive_diff(before[index], after[index], child))
        return changes
    return [] if before == after else [
        {"path": path, "kind": "changed", "before": before, "after": after}
    ]

automation_path = (
    Path.home() / ".codex" / "automations"
    / "weekly-codex-maintenance-report" / "automation.toml"
)
raw_before_toml = (backup / "automation-raw-before.toml").read_bytes()
raw_before = tomllib.loads(raw_before_toml.decode("utf-8"))
raw_after_toml = automation_path.read_bytes()
raw_after = tomllib.loads(raw_after_toml.decode("utf-8"))

def payload_from_toml(config):
    return {
        "id": config["id"],
        "mode": "update",
        "kind": config["kind"],
        "name": config["name"],
        "prompt": config["prompt"],
        "rrule": config["rrule"],
        "status": config["status"],
        "executionEnvironment": config["execution_environment"],
        "model": config["model"],
        "projectId": config["target"]["project_id"],
        "reasoningEffort": config["reasoning_effort"],
    }

assert view_before == rollback_payload
assert view_after == payload_from_toml(raw_after), "tool view and raw after-state drifted"
tool_changes = recursive_diff(view_before, view_after)
tool_changed_paths = {tuple(change["path"]) for change in tool_changes}
assert tool_changed_paths == {("prompt",)}, tool_changes
assert view_after == forward_payload, "forward tool payload was not applied exactly"
raw_changes = recursive_diff(raw_before, raw_after)
raw_changed_paths = {tuple(change["path"]) for change in raw_changes}
assert raw_changed_paths <= {("prompt",), ("updated_at",)}, raw_changes
assert ("prompt",) in raw_changed_paths, raw_changes
print(json.dumps({
    "tool_changes": tool_changes,
    "raw_changes": raw_changes,
    "rollback_prompt_sha256": hashlib.sha256(
        rollback_payload["prompt"].encode()
    ).hexdigest(),
    "rollback_prompt_length": len(rollback_payload["prompt"]),
}, default=list, indent=2, sort_keys=True))
PY
```

The authoritative tool-view gate permits exactly `prompt`; the raw TOML gate
permits `prompt` plus the separately disclosed server-managed `updated_at`.
Record the computed output and both complete tool view results.

- [ ] **Step 4: Prove rollback is executable without performing it**

Validate that the persisted `rollback_payload` has a non-empty `prompt` and the
exact formal required-field set. The executable rollback is the same fresh
formal `automation_update` tool called with the decoded persisted
`rollback_payload`; record the complete payload, prompt checksum, and prompt
length, but do not send it after a successful update. Forward and rollback
payloads differ only in `prompt`. If the tool disappears or its schema/shape
drifts at any point before the forward mutation, stop without mutation. After a
successful forward mutation, any verification failure produces
`partial_runtime_state` and waits for explicit rollback authorization rather
than automatically rolling back.

### Task 7: Run Isolated No-Write Acceptance, Live Smoke, and Full Verification

**Files:**
- No new repository files.

**Execution precondition:** Run every step below in the separately authorized
Task 5/6 shell that retains `runtime_backup`, `GATE_RECEIPTS`, `PARTIAL_STATE`,
and `GATE_LOG_DIR`. Before executing a displayed command, source the one
canonical helper from `"$runtime_backup/run_gate.sh"`. Every displayed command
is a literal labelled `run_gate` invocation; do not unwrap, regroup, or run its
payload directly.

- [ ] **Step 1: Re-run strict isolated fixture equality**

```bash
: "${runtime_backup:?Task 5 runtime backup is required}"
source "$runtime_backup/run_gate.sh"
run_gate "task7-isolated-fixture" "isolated CODEX_HOME fixture" \
  env PYTHONDONTWRITEBYTECODE=1 \
  python3 -c 'import test_runner; test_runner.test_codex_fluent_active_session_report()'
```

Expected: exit 0. This is the strict no-write gate: every fixture session and
index file has equal checksum, size, mtime, and mode before and after, and the
complete fixture-tree file path set is unchanged. The scanner promises no
content or explicit metadata write; OS/mount atime changes are not asserted.

- [ ] **Step 2: Select live candidate paths and snapshot only those paths**

Run Task 7 Steps 2–5 in one shell. A failed scanner, assertion, compatibility
check, or full verification gate exits from `run_gate` before any later timing
display or final claim; do not rely on a later `cat` or `git diff --check` exit
status.

```bash
: "${runtime_backup:?Task 5 runtime backup is required}"
source "$runtime_backup/run_gate.sh"
live_dir="$(mktemp -d /tmp/codex-fluent-live.XXXXXX)"
export live_dir
run_gate "task7-live-scan-before" "selected live candidate window" \
  bash -c '
    {
      /usr/bin/time -p env PYTHONDONTWRITEBYTECODE=1 \
        python3 "$HOME/.codex/skills/codex-fluent/scripts/report_active_sessions.py" \
          --codex-home "$HOME/.codex" \
          --older-than-days 30 \
          --limit 30 \
          --format json > "$1/report-before.json"
    } 2> "$1/scanner-before-time.txt"
  ' bash "$live_dir"
run_gate "task7-selected-snapshot" "selected live candidate paths" \
  python3 - "$live_dir/report-before.json" "$live_dir/selected-before.json" <<'PY'
import hashlib, json, sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
snapshot = {}
pre_snapshot_missing = []
for row in report["candidates"]:
    path = Path(row["session_path"])
    try:
        content = path.read_bytes()
        stat = path.stat()
    except FileNotFoundError:
        pre_snapshot_missing.append({"path": str(path), "reason": "pre_snapshot_missing"})
        continue
    snapshot[str(path)] = {
        "sha256": hashlib.sha256(content).hexdigest(),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }
evidence = {"files": snapshot, "pre_snapshot_missing": pre_snapshot_missing}
Path(sys.argv[2]).write_text(json.dumps(evidence, sort_keys=True, indent=2), encoding="utf-8")
print(json.dumps({"selected_path_count": len(snapshot),
                  "pre_snapshot_missing": pre_snapshot_missing}, indent=2))
PY
```

Expected: scanner exits 0 and only its returned candidate paths enter the live
snapshot. Preserve `/usr/bin/time -p` `real`, `user`, and `sys` output as the
live elapsed-time baseline; it is evidence only and adds no performance feature.

- [ ] **Step 3: Run the live smoke and report concurrent writes**

```bash
: "${runtime_backup:?Task 5 runtime backup is required}"
: "${live_dir:?Task 7 Step 2 live directory is required}"
source "$runtime_backup/run_gate.sh"
run_gate "task7-live-scan-after" "selected live candidate window" \
  bash -c '
    {
      /usr/bin/time -p env PYTHONDONTWRITEBYTECODE=1 \
        python3 "$HOME/.codex/skills/codex-fluent/scripts/report_active_sessions.py" \
          --codex-home "$HOME/.codex" \
          --older-than-days 30 \
          --limit 30 \
          --format json > "$1/report-after.json"
    } 2> "$1/scanner-after-time.txt"
  ' bash "$live_dir"
run_gate "task7-concurrent-write-report" "selected live candidate paths" \
  python3 - "$live_dir/selected-before.json" <<'PY'
import hashlib, json, sys
from pathlib import Path

before_evidence = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
before = before_evidence["files"]
changed = []
for raw, old in before.items():
    path = Path(raw)
    if not path.exists():
        changed.append({"path": raw, "reason": "concurrent_remove"})
        continue
    stat = path.stat()
    new = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
           "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    if new != old:
        changed.append({"path": raw, "reason": "concurrent_write", "before": old, "after": new})
print(json.dumps({"selected_path_count": len(before),
                  "pre_snapshot_missing": before_evidence["pre_snapshot_missing"],
                  "concurrent_changes": changed}, indent=2))
PY
```

Concurrent writes are allowed and must be reported; they are not attributed to
the scanner and do not fail live acceptance. Do not compare a digest of the
entire active sessions tree because unrelated running tasks may write to it.

- [ ] **Step 4: Validate live report semantics with executable assertions**

```bash
: "${runtime_backup:?Task 5 runtime backup is required}"
: "${live_dir:?Task 7 Step 2 live directory is required}"
source "$runtime_backup/run_gate.sh"
run_gate "task7-semantics" "live scanner report" \
  python3 - "$live_dir/report-after.json" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
candidates = report["candidates"]
returned = report["returned_count"]
candidate_count = report["candidate_count"]

assert returned == len(candidates)
assert returned == min(candidate_count, 30)
assert 0 <= returned <= 30
if candidate_count >= 20:
    assert 20 <= returned <= 30

expected_candidates = sorted(
    candidates,
    key=lambda item: (-item["size_bytes"], item["started_at"], item["thread_id"]),
)
assert candidates == expected_candidates
assert [item["primary_rank"] for item in candidates] == list(range(1, returned + 1))
assert all(
    item["handoff_required"] == (item["compaction_count"] >= 2)
    for item in candidates
)

expected_queue = [
    {
        "primary_rank": item["primary_rank"],
        "thread_id": item["thread_id"],
        "compaction_count": item["compaction_count"],
    }
    for item in sorted(
        (item for item in candidates if item["handoff_required"]),
        key=lambda item: (-item["compaction_count"], item["primary_rank"]),
    )
]
assert report["returned_handoff_queue"] == expected_queue
assert report["queue_scope"] == "returned-window-only"
print(
    f"returned_count={returned} candidate_count={candidate_count} "
    f"returned_handoff_queue_count={len(expected_queue)} semantics=pass"
)
PY
run_gate "task7-timing-display" "live scanner timing evidence" \
  bash -c 'cat "$1/scanner-before-time.txt" "$1/scanner-after-time.txt"' \
  bash "$live_dir"
```

Expected: exit 0 with `semantics=pass`; both timing files contain `real`, `user`,
and `sys` values.

- [ ] **Step 5: Run focused and full existing verification gates**

```bash
: "${runtime_backup:?Task 5 runtime backup is required}"
source "$runtime_backup/run_gate.sh"
run_gate "task7-global-policy" "repo source" \
  python3 -c 'import test_runner; test_runner.test_global_agents_thread_discipline_contract()'
run_gate "task7-active-report" "repo source" \
  python3 -c 'import test_runner; test_runner.test_codex_fluent_active_session_report()'
run_gate "task7-boundaries" "repo source" \
  python3 -c 'import test_runner; test_runner.test_codex_fluent_active_session_boundaries()'
run_gate "task7-selection" "repo source" \
  python3 -c 'import test_runner; test_runner.test_codex_fluent_selection_contract()'
run_gate "task7-timestamp-source" "repo source" \
  python3 -c 'import test_runner; test_runner.test_codex_fluent_timestamp_and_source_contract()'
run_gate "task7-markdown" "repo source" \
  python3 -c 'import test_runner; test_runner.test_codex_fluent_markdown_golden()'
run_gate "task7-report-only" "repo source" \
  python3 -c 'import test_runner; test_runner.test_codex_fluent_report_only_contract()'
run_gate "task7-skill-compatibility" "managed runtime overlay" \
  python3 scripts/check_skill_compatibility.py --repo-root "$(pwd)" --codex-home "$HOME/.codex"
run_gate "task7-surfaces" "repo surfaces" \
  python3 scripts/check_surfaces.py --repo-root "$(pwd)" --json
run_gate "task7-full-suite" "repo source" python3 test_runner.py
run_gate "task7-env-verify" "managed runtime overlay" \
  ./scripts/verify_codex_env.sh \
    --repo-root "$(pwd)" \
    --codex-home "$HOME/.codex" \
    --claude-home "$HOME/.claude"
run_gate "task7-diff-check" "repo source" git diff --check
```

Expected: every command exits 0; focused tests print PASS markers,
`test_runner.py` reports zero failed, surface and skill checks report no drift,
and `verify_codex_env.sh` prints `Verification passed.`

- [ ] **Step 6: Record final operational evidence**

For every completion claim report:

```text
command:
exit_code:
key_output:
timestamp:
```

Also report the final candidate count, number with `compaction_count >= 2`,
isolated fixture equality, selected-path concurrent-write report, immutable
primary ranks, managed source-file/runtime checksum parity, separate
runtime-only inventory, allowed-path manifest and checksums, complete computed
automation recursive diff, `rollback_prompt` checksum/length, unchanged
`rrule`, both scanner elapsed-time records, and the explicit Desktop lifecycle
API limitation.

- [ ] **Step 7: Commit only in-scope final integration adjustments**

Run this step only after a separately authorized implementation task grants
commit authority for the named paths. Do not infer commit authority from source,
runtime, automation, or verification authority.

```bash
git add codex/AGENTS.md codex/skills/codex-fluent \
  tests/fixtures/codex_fluent_report.golden.md \
  docs/CODEX_ENV_REPRODUCTION.md docs/repo-index.md docs/surfaces.json test_runner.py
git commit -m "feat: automate Codex task handoff triage"
```

Do not push unless the user explicitly requests it.
