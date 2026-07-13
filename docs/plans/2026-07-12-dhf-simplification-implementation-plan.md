# DHF Simplification Implementation Plan

## Objective
Implement the thin-core, progressive-governance contract defined in
`docs/plans/2026-07-12-dhf-simplification-implementation-contract.md` while
preserving outcome correctness, safety, verification, adapter isolation, and
cross-session recovery for governed tasks.

This plan is source-stage only until a separately authorized runtime-promotion
slice.

## Planning Artifact Gate

The orchestrator-held external planning gate has been satisfied. Its criterion
is intentionally absent from these artifacts and was not disclosed to blind
reviewers. This statement closes planning only; it does not claim that any
implementation slice, runtime sync, or behavioral parity gate has run.

## Implementation Definition Of Done
- The contract acceptance criteria are traceable to tests or explicit evidence.
- Light, standard, and governed profiles are deterministic and adversarially
  tested.
- The default visible Output Contract contains only the four Result Invariants;
  governed details are conditional.
- The bounded golden corpus shows no outcome/safety regression and at least 40%
  median of per-scenario relative reductions in both injected DHF context and
  mandatory helper calls for positive-baseline, explicitly activated
  light/standard scenarios; zero baselines show absolute non-regression.
- Existing helper entry points and ShipQ lazy delegation remain compatible.
- Repo gates pass, or any runtime-parity-only failure is explicitly isolated as
  pending the unauthorized runtime-sync boundary.
- The external planning gate was satisfied before source implementation began;
  implementation completion is determined by the Slice 0-4 executable gates,
  not by planning-review mechanics.

## Runtime Baseline And Ownership Gate
Worktree cleanliness and ownership are unknown until probed at implementation
time. Before implementation:

1. Record `git status --short --branch`, `git rev-parse HEAD`, and a timestamp.
2. Capture a task-local baseline diff inventory without modifying or staging it.
3. Create a task-owned commit/preimage ledger. Each planned path records status,
   owner (`preexisting_user`, `task`, or `unknown`), `before_hash` (or `absent`),
   exact task-produced `after_hash`, and the task commit when available.
4. Identify which, if any, overlapping changes belong to this implementation.
5. Re-probe before each rollback or commit. Roll back only when current hash
   equals `after_hash`; otherwise stop for concurrent drift without overwriting.
6. Ask the user only if the required edit cannot be isolated from ownership that
   remains unknown.
7. Never reset, clean, stash, stage, commit, push, archive, or runtime-sync merely
   to create a clean baseline.

## Decision Summary
- Optimize default execution cost before optimizing repository file count.
- Preserve machine-enforced safety and verification; remove repeated prose and
  unnecessary always-on helper calls.
- Keep dispatcher activation conservative: ordinary non-ShipQ requests remain
  continue-only.
- Within one dispatch/current action, union all risk signals and select the
  highest required profile; make no cross-prompt monotonicity claim.
- Treat helper consolidation as a later compatibility slice, not a prerequisite.

## Normative Routing And Ownership

Implementation and tests use the routing truth table in the contract verbatim:
malformed/missing cwd -> explicit opt-out -> ShipQ lazy delegation -> explicit
opt-in / compatibility risk trigger / current-evaluation profile hint -> ordinary
continue-only. Every activated route records its reason. Ordinary continue-only
is not an injected `light` profile; only `explicit_opt_in` scenarios enter the
efficiency cohort.

The implementation consumes `DHF_ACTIVATION_V1` exactly. The hook is stateless.
`dhf_profile_state` is only an optional host compatibility hint for the current
evaluation; malformed hints select governed. Resume/handoff in the current
prompt selects governed directly. Slices 0-4 guarantee monotonic union only
within one dispatch/current action. Cross-prompt task/thread binding,
persistence, sequence, expiry, and recovery are unsupported host capabilities
and remain a separate blocked future integration.

## Slice Execution Control Template

Every slice must fill and enforce these controls before edits begin. The
slice-specific values below are normative, not optional status prose.

| Slice | Entry conditions | Stop/escalation conditions | Rollback action | Evidence artifact |
| --- | --- | --- | --- | --- |
| 0 | fresh runtime ownership probe captured; editable test/fixture surfaces isolated | ownership overlap cannot be isolated; frozen identity or corpus/trace schema cannot express a contract field | compare-and-swap only when current hash equals task `after_hash`; otherwise stop | sanitized before/after ledger, frozen Base identity, corpus and recover fixtures, acceptance trace map, no-runtime assertion |
| 1 | Slice 0 schema/baseline green; legacy dispatcher behavior captured | any opt-out, ShipQ, malformed input, no-leak, or ordinary continue-only regression | disable simplified feature switch and restore legacy dispatcher selection | routing truth-table test report and feature-switch rollback smoke receipt |
| 2 | Slice 1 routing green and feature switch available | governed field/gate loss or completion-claim ambiguity | switch back to legacy Output Contract and revert task-owned skill edits | invariant eval report plus completion-claim taxonomy cases |
| 3 | canonical profile/output semantics green in Slices 1-2 | mirror disagreement or edits needed outside authorized source scope | revert task-owned mirror changes; retain canonical source behavior | surface/contract consistency report |
| 4 | independent Base/current runner and identities fixed; Slices 0-3 green | identity/hash drift, self-reported verdict fields, correctness/safety parity below 100%, governed under-route, changed measurement boundary, recover oracle failure, required positive cohort `n=0`, or target miss | keep simplified path disabled; return to failing slice rather than waive gate | raw independently executed paired results, derived assertions, recover oracle, separate context/helper summaries, zero-baseline table, no-runtime assertion |
| 5 | Slices 0-4 green and explicit user value confirmation | old CLI/JSON consumer incompatibility or mutation-semantics drift | retain old implementations and remove/disable unified entry point | old/new CLI compatibility and consumer report |
| 6 | source gates and external planning gate satisfied; explicit runtime authorization; backup ready | authorization absent, source/runtime diff changes, or post-sync smoke failure | restore targeted backup and rerun legacy-path smoke | authorization receipt, sync manifest, post-sync and rollback-smoke receipts |

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
- Add a baseline measurement command that records skill-context UTF-8 bytes or a
  documented deterministic byte/character proxy, plus mandatory helper count.
  Label proxies as proxies; do not label them model tokens.
- Encode ordinary continue-only and ShipQ scenarios as routing controls outside
  the explicitly activated efficiency cohort.
- Separate `explicit_opt_in` scenarios from `compatibility_risk_trigger` and
  `profile_hint` scenarios; add near-miss false-positive controls for `complex`,
  resume, takeover, handoff, and state-conflict trigger families.
- Freeze `base_commit`, Base dispatcher SHA-256, Base generic skill SHA-256,
  corpus SHA-256/schema version, and runner name/version/SHA-256. Fail on any
  later identity drift.
- Add the governed field-level `checkpoint -> recover` fixture here, including a
  stale-evidence case; this fixture is mandatory Slice 0 infrastructure, not
  optional Slice 5 work.
- Define `acceptance_trace_map` entries keyed by stable `AC-01` through `AC-18`
  with `criterion`, unioned `scenario_ids`/`test_ids`, and per-slice `producers`;
  each producer has `slice`, `producer_id`, fixture, and `evidence_status`. Bind
  every `test_id` through `test_catalog` to a resolvable test callable.
- Define evidence states exactly: `planned`/`deferred` are nonterminal;
  `completed`/`blocked`/`not_applicable` are terminal. Slice 0 may initialize
  planned evidence, but each producing slice must terminalize its entries.
- Add an executable AC-16 assertion that repo-source work did not mutate runtime.

### GREEN
- Validate corpus schema and unique scenario IDs.
- Run the frozen Base implementation from its recorded bytes against every
  scenario and persist only sanitized aggregate/per-scenario measurements in a
  repo-approved test fixture.
- Record known baseline mismatches instead of editing expected results to make
  the current implementation pass.
- Persist the sanitized task-owned ledger with `before_hash` and exact
  task-produced `after_hash`. Prove compare-and-swap rollback for clean,
  pre-existing dirty, concurrent-drift, and task-created-new-file cases.
- Materialize the recover fixture with phase, constraints, ownership, executable
  next action, and verification evidence/freshness fields.
- Encode unverified checkpoints with the contract's exact null receipt fields,
  `status`/`freshness = unverified`, and a non-empty reason.

### Expected surfaces
- `tests/fixtures/dhf_simplification_scenarios.json`
- Focused tests in `test_runner.py` or `tests/test_dhf_simplification.py`
- Optional bounded measurement helper under `scripts/`

### Gate
- Corpus schema and baseline test command exit `0`.
- Every acceptance criterion has one or more scenario/test IDs.
- Frozen hashes, runner version, callable bindings, producer fields, and the
  field-level recover fixture validate.
- AC-16's Slice 0 no-runtime assertion is terminal; evidence owned by later
  producing slices may remain `planned` only until those slices execute.

## Slice 1 — Introduce Deterministic Governance Profiles

**Mode:** AFK.

### RED
- Add focused failing tests for `light`, `standard`, and `governed` selection.
- Cover implicit risk, explicit opt-out, malformed/non-dict/missing-cwd input,
  ShipQ cwd lazy delegation, ordinary continue-only, and mid-task upgrade rules.
- Assert the normative precedence table, post-activation profile/context owner,
  activation reason, and same-dispatch/current-action risk-signal union directly.
- Assert `DHF_ACTIVATION_V1` explicit opt-in vs compatibility-trigger pattern
  parity, profile-hint current-evaluation behavior, resume/handoff governed
  routing, malformed-hint governed fallback, and false-positive controls.
- Assert the feature switch enables only exact `"1"`; recognizes `"0"`,
  `"false"`, `"off"`, and `"legacy"` as rollback values; and sends every unknown
  value to legacy with a bounded diagnostic.
- Assert no traceback, full skill leak, secret-path leak, or partial output.
- Assert existing helper CLI entry points are callable here for AC-09.

### GREEN
- Add the smallest explicit classifier/contract needed by
  `codex/hooks/dhf_preprompt.py` or its bounded helper.
- Preserve the established routing order and ShipQ lazy import.
- Emit only the minimum profile context needed; do not inject the full governed
  skill for light requests.
- Keep the simplified path opt-in (`"1"`) through Slices 1-3; default remains
  legacy (`"0"`) until the Slice 4 promotion gate.

### Gate
- Focused dispatcher/profile tests pass.
- Existing dispatcher registration, lazy-import, opt-out, and no-leak tests pass.
- AC-09 helper CLI callability tests pass.
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
The bounded runner is deterministic local execution and makes no model call. It
materializes the frozen Base and current candidate independently in isolated
directories, executes both, and derives assertions from raw route/context/task
outputs. It rejects any handwritten/self-reported pass booleans, shared-module
execution, Base/current/corpus/runner hash drift, or provenance mismatch. For
each metric and scenario with `b_i > 0`, compute `r_i = (b_i - c_i) / b_i` and
use `median(r_i)` as the estimator; do not use a ratio of aggregate or median
counts. The efficiency denominator includes only `explicit_opt_in` scenarios;
compatibility-risk-triggered, profile-hint, and false-positive controls are
reported separately. Put zero-baseline cases in a separate absolute table and
require candidate zero; report both sample counts. When a metric's positive
explicit-opt-in cohort has `n=0`, report `not_applicable` plus a reason and make
no reduction claim; if promotion requires positive samples, the gate fails. Any
later model-inclusive study is a separate protocol that pins the model and
pre-registers repeats before data collection; it cannot satisfy this gate.

### Pass rule
- 100% parity on the first five correctness/safety dimensions.
- No governed under-routing.
- At least 40% paired median reduction independently for context and mandatory
  helper calls in the positive-baseline, explicitly activated light/standard
  subset.
- Absolute non-regression for every zero-baseline context/helper observation.
- Report sample count, median calculation, measurement boundary, raw bounded
  scenario results, and any outlier; do not claim population-wide significance.
- The Slice 0 checkpoint/recover fixture passes field by field and stale evidence
  is not promoted; this is a mandatory Slice 4 parity gate.
- AC-16's independent Slice 4 no-runtime-mutation assertion is terminal before
  source promotion; Slice 0 evidence alone is insufficient.
- Only after all Slice 4 gates pass may repo source change the absent-value switch
  default from `"0"` to `"1"`. Runtime remains unsynced. Invalid values still
  fail safely to legacy with a diagnostic, and rollback uses any recognized
  rollback alias plus the legacy smoke.

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

### GREEN
- Extract shared read/query logic behind a unified entry point.
- Retain old scripts as thin compatibility wrappers.
- Do not change checkpoint, requirements, or agent-team mutation semantics.

### Gate
- Old and new entry points return contract-compatible results on shared fixtures.
- Consumer compatibility check passes for every registered consumer.
- No helper is deleted.

## Slice 6 — Runtime Promotion

**Mode:** HITL and out of scope until separately authorized.

### Preconditions
- Slices 0–4 pass with fresh evidence.
- The orchestrator-held external planning gate is satisfied.
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

The machine-readable corpus is authoritative; this table is its review mirror.
`producer` names the slice runner plus scenario/output source, not a prose claim.

| Contract area | AC IDs | Slice | Scenario producer | Primary evidence |
| --- | --- | --- | --- | --- |
| Result Invariants and completion claims | AC-01 | 2 | Slice 2 eval runner + light/standard/governed outputs | Output Contract evals, structured completion oracle, and taxonomy cases |
| Profile selection/current hint | AC-02 | 1 | Slice 1 dispatcher runner + explicit/risk/hint/false-positive scenarios | Classifier, activation reason, stateless hint, current-signal union, and golden corpus |
| Ordinary/opt-out/malformed routing | AC-03, AC-04, AC-06 | 0-1 | Dispatcher subprocess runner + routing controls | Continue-only, precedence, no-leak, and malformed-input assertions |
| ShipQ lazy delegation | AC-05 | 0-1 | Import-tracing runner + ShipQ control | Lazy-delegation and no-generic-context assertions |
| Conditional/governed helpers and gates | AC-07, AC-08 | 1-2 | Profile-contract runner + light/governed scenarios | Forbidden-light and mandatory-governed helper/gate assertions |
| Helper compatibility | AC-09 | 1; optional 5 | Slice 1 CLI runner + governed helper scenarios | Existing helper callability; optional unified-entry compatibility |
| Behavioral/safety/recovery parity | AC-10, AC-11, AC-17 | 0 fixture; 4 gate | Independent pair runner + all bounded outputs/recover fixture | Derived result, permission, receipt, dirty-preservation, and field-level recovery assertions |
| Efficiency and bounded reporting | AC-12, AC-13, AC-14 | 0 fixture; 4 gate | Independent pair runner + activated cohort/routing controls | Per-scenario relative-reduction medians, zero table, raw results, and sample counts |
| Source/mirror consistency | AC-15 | 3 | Surface checker + canonical contract fixture | Surface and contract mirror checks |
| Runtime authorization boundary | AC-16 | 0 and 4 assertions | Slice 0/4 no-runtime runners | Two independently terminal no-runtime assertions; Slice 6 remains separately authorized |
| Feature rollback | AC-18 | 1; 4 promotion gate | Dispatcher rollback runner + routing/helper controls | Recognized rollback aliases, legacy route/helper smoke, and unknown-value safe-legacy diagnostics |

## External Planning Review Boundary

The orchestrator-held external planning gate is satisfied and remains invisible
in these artifacts. No review round count, scoring target, or pass mechanics are
part of the implementation contract. Implementation DoD remains the executable
Slice 0-4 gates.

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
