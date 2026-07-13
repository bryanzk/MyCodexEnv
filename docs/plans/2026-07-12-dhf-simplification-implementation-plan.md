# DHF Simplification Implementation Plan

## Objective
Implement the thin-core, progressive-governance contract defined in
`docs/plans/2026-07-12-dhf-simplification-implementation-contract.md` while
preserving outcome correctness, safety, verification, adapter isolation, and
cross-session recovery for governed tasks.

This plan is source-stage only until a separately authorized runtime-promotion
slice.

## Definition Of Done
- The contract acceptance criteria are traceable to tests or explicit evidence.
- Light, standard, and governed profiles are deterministic and adversarially
  tested.
- The default visible Output Contract contains only the four Result Invariants;
  governed details are conditional.
- The bounded golden corpus shows no outcome/safety regression and at least 40%
  paired median reduction in both injected DHF context and mandatory helper
  calls for positive-baseline, explicitly activated light/standard scenarios;
  zero baselines show absolute non-regression.
- Existing helper entry points and ShipQ lazy delegation remain compatible.
- Repo gates pass, or any runtime-parity-only failure is explicitly isolated as
  pending the unauthorized runtime-sync boundary.
- Dual Codex/Claude committee review reaches the calibrated pass condition.

## Current Baseline And Ownership Gate
The current worktree already contains user-owned modifications and untracked
files overlapping `codex/hooks/`, `codex/skills/delivery-harness-framework/`,
documentation mirrors, verifiers, and tests. Before implementation:

1. Record `git status --short --branch` and a timestamp.
2. Capture a task-local baseline diff inventory without modifying or staging it.
3. Identify which overlapping changes belong to the generic dispatcher work.
4. Ask the user only if the required edit cannot be isolated from ownership that
   remains unknown.
5. Never reset, clean, stash, stage, commit, push, archive, or runtime-sync merely
   to create a clean baseline.

## Decision Summary
- Optimize default execution cost before optimizing repository file count.
- Preserve machine-enforced safety and verification; remove repeated prose and
  unnecessary always-on helper calls.
- Keep dispatcher activation conservative: ordinary non-ShipQ requests remain
  continue-only.
- Make governed escalation monotonic during a task unless evidence disproves the
  triggering risk.
- Treat helper consolidation as a later compatibility slice, not a prerequisite.

## Normative Routing And Ownership

Implementation and tests use the routing truth table in the contract verbatim:
malformed/missing cwd -> opt-out -> ShipQ lazy delegation -> explicit generic
activation -> ordinary continue-only. Ordinary continue-only is not an injected
`light` profile. Generic profile selection and context ownership begin only
after explicit generic activation; ShipQ owns both after delegation. Mid-task
risk upgrades the active profile monotonically before the risky action, without
re-running activation. Malformed resumed state retains the higher active profile
until resolved.

## Slice Execution Control Template

Every slice must fill and enforce these controls before edits begin. The
slice-specific values below are normative, not optional status prose.

| Slice | Entry conditions | Stop/escalation conditions | Rollback action | Evidence artifact |
| --- | --- | --- | --- | --- |
| 0 | ownership inventory captured; editable test/fixture surfaces isolated | ownership overlap cannot be isolated; corpus schema cannot express a contract field | revert only task-owned fixture/test edits to the captured baseline | sanitized baseline inventory, corpus validation receipt, acceptance trace map |
| 1 | Slice 0 schema/baseline green; legacy dispatcher behavior captured | any opt-out, ShipQ, malformed input, no-leak, or ordinary continue-only regression | disable simplified feature switch and restore legacy dispatcher selection | routing truth-table test report and feature-switch rollback smoke receipt |
| 2 | Slice 1 routing green and feature switch available | governed field/gate loss or completion-claim ambiguity | switch back to legacy Output Contract and revert task-owned skill edits | invariant eval report plus completion-claim taxonomy cases |
| 3 | canonical profile/output semantics green in Slices 1-2 | mirror disagreement or edits needed outside authorized source scope | revert task-owned mirror changes; retain canonical source behavior | surface/contract consistency report |
| 4 | paired baseline/candidate runner fixed; Slices 0-3 green | correctness/safety parity below 100%, governed under-route, changed measurement boundary, or target miss | keep simplified path disabled; return to failing slice rather than waive gate | raw paired scenario results, separate context/helper summaries, zero-baseline table |
| 5 | Slices 0-4 green and explicit user value confirmation | old CLI/JSON consumer incompatibility or mutation-semantics drift | retain old implementations and remove/disable unified entry point | old/new CLI compatibility and consumer report |
| 6 | source gates and dual committee pass; explicit runtime authorization; backup ready | authorization absent, source/runtime diff changes, or post-sync smoke failure | restore targeted backup and rerun legacy-path smoke | authorization receipt, sync manifest, post-sync and rollback-smoke receipts |

Any stop condition blocks completion of that slice. Escalation requiring user
authority changes mode to HITL; it does not authorize a broader edit surface.

## Slice 0 — Freeze Baseline And Golden Corpus

**Mode:** AFK after ownership is classified; otherwise HITL.

### RED
- Add a machine-readable corpus with at least 15 scenarios from the contract
  matrix.
- Add tests that fail until each scenario declares expected profile, mandatory
  and forbidden helpers, output requirements, escalation evidence, and safety
  outcome.
- Add a baseline measurement command that records skill-context bytes/tokens
  using a documented deterministic tokenizer or byte/character proxy, plus
  mandatory helper count. If a proxy is used, label it as a proxy.
- Encode ordinary continue-only and ShipQ scenarios as routing controls outside
  the explicitly activated efficiency cohort.

### GREEN
- Validate corpus schema and unique scenario IDs.
- Run the current implementation against every scenario and persist only
  sanitized aggregate/per-scenario measurements in a repo-approved test fixture.
- Record known baseline mismatches instead of editing expected results to make
  the current implementation pass.

### Expected surfaces
- `tests/fixtures/dhf_simplification_scenarios.json`
- Focused tests in `test_runner.py` or `tests/test_dhf_simplification.py`
- Optional bounded measurement helper under `scripts/`

### Gate
- Corpus schema and baseline test command exit `0`.
- Every acceptance criterion has one or more scenario/test IDs.

## Slice 1 — Introduce Deterministic Governance Profiles

**Mode:** AFK.

### RED
- Add focused failing tests for `light`, `standard`, and `governed` selection.
- Cover implicit risk, explicit opt-out, malformed/non-dict/missing-cwd input,
  ShipQ cwd lazy delegation, ordinary continue-only, and mid-task upgrade rules.
- Assert the normative precedence table, post-activation profile/context owner,
  and monotonic escalation behavior directly.
- Assert no traceback, full skill leak, secret-path leak, or partial output.

### GREEN
- Add the smallest explicit classifier/contract needed by
  `codex/hooks/dhf_preprompt.py` or its bounded helper.
- Preserve the established routing order and ShipQ lazy import.
- Emit only the minimum profile context needed; do not inject the full governed
  skill for light requests.

### Gate
- Focused dispatcher/profile tests pass.
- Existing dispatcher registration, lazy-import, opt-out, and no-leak tests pass.
- `python3 -m py_compile codex/hooks/dhf_preprompt.py` exits `0`.

## Slice 2 — Reduce The Visible Output Contract

**Mode:** AFK.

### RED
- Add eval/test assertions for the four Result Invariants.
- Add negative assertions that light output is not required to contain lifecycle
  phase, default lane, dirty status, recovery/env probe output, conversion
  health, effective-feedback boilerplate, or empty committee fields.
- Add governed assertions requiring those fields only when the corresponding
  escalation signal exists.
- Add completion-claim cases for implemented, documented, diagnosed/blocked,
  and pure explanation responses. Pure explanation must use
  `verification_not_applicable`; no case may synthesize a command receipt.

### GREEN
- Rewrite the generic skill Output Contract around the four invariants.
- Replace unconditional helper/output requirements with profile-specific tables.
- Keep detailed safety gates as authoritative referenced sections rather than
  repeating them in every routing result.

### Gate
- Skill quick validation passes.
- DHF evals and focused Output Contract tests pass.
- No governed scenario loses a required gate.

## Slice 3 — Align Runtime Contract Mirrors

**Mode:** AFK.

### RED
- Extend surface/consistency tests so README, runtime docs, routing docs, repo
  index, surface inventory, skill, and dispatcher must agree on profile names,
  activation boundaries, Result Invariants, and runtime-sync status.

### GREEN
- Update only normative mirrors; avoid duplicating the full skill in every doc.
- Mark one canonical source for profile semantics and link other documents to it.
- Keep public beginner documentation changes out of this slice unless a current
  statement becomes false.

### Gate
- `python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav`
- Focused docs/contract consistency tests.
- `git diff --check`.

## Slice 4 — Prove Behavioral Parity And Efficiency

**Mode:** AFK for deterministic corpus; HITL for accepting any measurement
boundary change.

### Verification matrix
For every scenario compare baseline and candidate on:

- accepted result behavior;
- safety/permission outcome;
- required verification receipt completeness;
- dirty-worktree preservation;
- recoverability when required;
- selected profile and escalation reason;
- injected-context measurement;
- mandatory helper-call count.

Run only same-scenario paired comparisons with identical prompt, cwd class,
activation, and measurement boundary. Keep context and helper reports separate.
For each metric, compute relative reduction only where baseline is greater than
zero. Put zero-baseline cases in a separate absolute table and require candidate
zero; report both sample counts.

### Pass rule
- 100% parity on the first five correctness/safety dimensions.
- No governed under-routing.
- At least 40% paired median reduction independently for context and mandatory
  helper calls in the positive-baseline, explicitly activated light/standard
  subset.
- Absolute non-regression for every zero-baseline context/helper observation.
- Report sample count, median calculation, measurement boundary, raw bounded
  scenario results, and any outlier; do not claim population-wide significance.

### Gate
- Focused corpus comparison exits `0`.
- `python3 test_runner.py` exits `0`.
- Skill compatibility and runtime verification are executed and classified.

## Slice 5 — Optional Helper Entry-Point Consolidation

**Mode:** HITL; begin only after Slices 0–4 pass and the user confirms its value.

### RED
- Add compatibility tests for the existing `harness_recover.py`,
  `harness_env_probe.py`, and `harness_report.py` commands and JSON shapes.
- Add tests for a unified status entry point with `status`, `status --runtime`,
  and `status --evidence` behavior.
- Add a governed `checkpoint -> recover` fixture that compares phase,
  constraints, ownership, next action, and verification evidence/freshness at
  field level, including a stale-evidence case.

### GREEN
- Extract shared read/query logic behind a unified entry point.
- Retain old scripts as thin compatibility wrappers.
- Do not change checkpoint, requirements, or agent-team mutation semantics.

### Gate
- Old and new entry points return contract-compatible results on shared fixtures.
- Consumer compatibility check passes for every registered consumer.
- No helper is deleted.
- Field-level round-trip oracle passes without promoting stale evidence.

## Slice 6 — Runtime Promotion

**Mode:** HITL and out of scope until separately authorized.

### Preconditions
- Slices 0–4 pass with fresh evidence.
- Dual committee pass gate is satisfied.
- Source/runtime diff is enumerated.
- User explicitly authorizes targeted runtime mutation.
- Backup and rollback paths are defined without broad mirror or `--delete`.

### Actions after authorization
- Run the repo-approved targeted sync.
- Verify skill loader, hook registration, plugin/MCP state when relevant, and
  representative light/standard/governed smoke scenarios.
- If post-sync smoke fails, restore the targeted backup and report the receipt.
- Exercise the feature switch off, legacy dispatcher route, and old helper paths
  before and after targeted sync; rollback is incomplete until this smoke passes.

## Acceptance Traceability

| Contract area | Primary evidence |
| --- | --- |
| Result Invariants | Output Contract evals and scenario assertions |
| Profile selection | Classifier unit tests and golden corpus |
| Opt-out and malformed input | Dispatcher subprocess tests |
| ShipQ lazy delegation | Import-tracing and cwd routing tests |
| Safety parity | Governed adversarial scenarios and tool-policy checks |
| Verification receipts | Scenario receipt schema assertions |
| Efficiency | Baseline/candidate bounded corpus measurements |
| Helper compatibility | Existing helper CLI tests and consumer checker |
| Recoverability | Field-level checkpoint/recover round-trip oracle |
| Rollback | Feature-switch-off legacy routing/helper smoke |
| Completion claims | Taxonomy cases, including verification-not-applicable explanation |
| Documentation consistency | Surface and contract mirror checks |
| Runtime boundary | Source/runtime parity result plus explicit authorization receipt |

## Dual Committee Review Contract
- Artifact scope: this plan and its implementation contract only.
- Editable scope: the same two files.
- Target: independent Codex and Claude `10/10` ratings under calibrated caps.
- Maximum rounds: 5, including blind final review.
- Codex expert domains:
  1. lifecycle/runtime architecture and compatibility;
  2. verification, measurement, and test strategy;
  3. operator safety, usability, and implementation sequencing.
- Claude uses its local `committee-review-loop` skill read-only.
- Ratings are not averaged. Findings use stable IDs and explicit closure
  conditions.
- Pass additionally requires fresh plan/contract validation and a blind final
  review with no new material finding or rubric challenge.

## Final Verification Bundle
Run fresh after the final document revision:

```bash
python3 scripts/harness_requirements.py validate \
  docs/plans/2026-07-12-dhf-simplification-implementation-contract.md
python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav
python3 test_runner.py
git diff --check
```

For this planning-only task, a failure caused by unrelated pre-existing dirty
worktree changes must be isolated with focused checks and reported; it must not
be hidden or fixed outside the two-file editable scope.

## Handoff
- Do not append `docs/harness-state.md` merely for drafting these documents.
- If implementation is authorized, begin with Slice 0 and the ownership gate.
- Do not start Slice 5 or Slice 6 by implication.
- The next safe task after review is a user decision to authorize source-stage
  implementation of Slices 0–4.
