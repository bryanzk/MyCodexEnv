# DHF Simplification Implementation Contract

## Goal
Reduce the default cost and visible ceremony of the Delivery Harness Framework
without weakening result correctness, safety boundaries, fresh verification, or
cross-session recoverability when those controls are required.

The target operating model is a thin invariant core with progressive governance:

- every task preserves a stable result contract;
- low-risk tasks avoid unnecessary lifecycle narration and helper calls;
- standard tasks add scoped execution and focused verification;
- governed tasks retain the full recovery, safety, evidence, and handoff gates.

## Audience
- Maintainers of the generic DHF skill and runtime hooks.
- Maintainers of repo-specific lifecycle adapters such as ShipQ.
- Codex operators who need predictable output with lower token and tool-call cost.
- Future agents resuming implementation from durable repo state.

## Scope
- `codex/skills/delivery-harness-framework/SKILL.md`
- `codex/hooks/dhf_preprompt.py`
- DHF routing and contract coverage in `test_runner.py` and focused tests under `tests/`
- `codex/skills/delivery-harness-framework/evals/evals.json`
- Contract mirrors in `README.md`, `docs/HARNESS_RUNTIME.md`,
  `docs/LIFECYCLE_SKILL_ROUTING.md`, `docs/repo-index.md`, and `docs/surfaces.json`
- A bounded golden-scenario evaluation corpus covering light, standard, and
  governed tasks.
- Compatibility-preserving entry-point consolidation for recovery, runtime
  probing, and evidence reporting, only after routing/output simplification is
  proven.

## Non-Goals
- Removing dirty-worktree protection, secret/privacy guards, destructive or
  remote approval gates, or fresh verification requirements.
- Deleting existing helper CLIs in the first implementation slice.
- Changing ShipQ business logic or globally registering its project adapter.
- Modifying live `~/.codex` or `~/.claude` runtime state without separate user
  authorization after repo-source verification.
- Rewriting append-only harness history.
- Optimizing for identical prose between the old and simplified DHF.
- Using average committee ratings as a pass condition.

## Constraints
- Probe worktree state at implementation time and preserve every unrelated or
  non-task-owned change found by that probe; this contract does not assume the
  future worktree is clean or dirty.
- Start with source-stage changes only; runtime sync is a separate, explicit gate.
- Keep existing helper commands working until compatibility wrappers and consumer
  checks prove migration safety.
- Preserve the generic dispatcher order: malformed or missing-cwd input,
  explicit opt-out, ShipQ lazy delegation, explicit generic activation, then
  ordinary continue-only behavior.
- Use Python standard library only unless the repo already provides a dependency.
- Do not commit local evidence logs, credentials, auth files, transcripts, or
  raw provider output.
- Use behavior and acceptance evidence, not prose equality, to establish parity.

## Task Demand (D_task)
- estimated_level: high
- L (reasoning/action steps): The change crosses skill text, hook routing, tests,
  evals, documentation mirrors, compatibility boundaries, and a later optional
  helper consolidation slice.
- H_tool (tool-selection ambiguity): Static tests, subprocess hook tests, eval
  corpus execution, runtime parity checks, and committee reviews serve different
  purposes and must not be substituted for one another.
- S_state (cross-module state tracking): Any implementation-time uncommitted
  dispatcher or DHF changes must be classified and preserved while source,
  runtime, adapter, documentation, and evidence contracts remain distinguishable.
- N_obs (observation/external noise): The normative measurement is deterministic
  local execution and excludes model output. Any future model-inclusive study is
  a separate protocol that must pin the model and pre-register its repeat count
  before collecting data; it cannot be mixed into this gate.

## Source Of Truth
- `AGENTS.md`
- `codex/AGENTS.md`
- `docs/repo-index.md`
- `CONTEXT.md`
- `docs/harness-state.md`
- `docs/HARNESS_RUNTIME.md`
- `codex/skills/delivery-harness-framework/SKILL.md`
- `codex/hooks/dhf_preprompt.py`
- `codex/runtime/tool-policy.json`
- `codex/runtime/evidence.schema.json`
- `test_runner.py`

## Result Invariants
Every completed task must preserve these four outcome invariants:

1. `result`: a usable artifact, answer, or explicit blocker matching the request.
2. `scope_and_constraints`: material boundaries and forbidden actions are obeyed;
   default boundaries need not be narrated when no risk signal exists.
3. `verification_receipt`: completion claims include fresh `command`,
   `exit_code`, `key_output`, and `timestamp` evidence proportionate to risk.
4. `remaining_risk_or_next_action`: unresolved risk, user decision, or next safe
   action is stated when one exists; empty ritual fields are not required.

## Governance Profiles

### Light
Use when the task is self-contained, low-risk, single-session, and has clear
acceptance behavior. Execute directly, run the narrowest useful verification,
and return the four invariant fields only as needed. Do not require recovery,
environment probes, evidence reports, lifecycle narration, or checkpoints.

### Standard
Use when scoped repo changes, debugging, or multi-step local work is required
without live systems or cross-session state. Require an explicit Definition of
Done, dirty-worktree ownership check, runnable feedback loop, focused green
gate, and fresh verification receipt.

### Governed
Use when any escalation signal is present:

- resume, takeover, handoff, or durable source conflict;
- unknown or overlapping worktree ownership;
- credentials, customer/private data, or external captures;
- destructive, remote, deployment, production, or release actions;
- multiple agents, overlapping write sets, or architecture alignment conflicts.

Governed tasks retain the relevant recovery, lane, environment, permission,
evidence, checkpoint, deployment-readiness, and agent-team gates.

When uncertain between two profiles, select the higher profile and record the
specific escalation signal. A profile may be upgraded during execution; it may
only be downgraded after the triggering risk is disproven with evidence.

## Normative Routing Contract

The dispatcher and the activated DHF profile selector are separate normative
stages. `ordinary continue-only` is an uninjected outcome, not a `light`
profile and not part of the activated measurement cohort. Only an explicitly
activated generic DHF request reaches generic profile selection. ShipQ owns its
profile/context after lazy delegation; the generic classifier must not
pre-classify or inject generic context into that path.

The machine-readable activation grammar is `DHF_ACTIVATION_V1` below. An
implementation may compile these strings to case-insensitive regular
expressions, but may not add an unlisted activation token without a contract and
corpus revision. `prompt_text` is the newline join, in source/key order, of
non-empty strings found at the root and then object-valued `tool_input`, `input`,
`arguments`, and `params`, using keys `prompt`, `user_prompt`, `message`, `task`,
and `input_text`. `cwd_text` is the first non-empty string from the same sources
using keys `cwd`, `workdir`, and `repo_root`.

```json
{
  "schema": "DHF_ACTIVATION_V1",
  "match": "regex_search_ignore_case_any",
  "opt_out_patterns": [
    "\\bno\\s+dhf\\b", "\\bskip\\s+dhf\\b", "\\bwithout\\s+dhf\\b",
    "\\bno\\s+delivery[-\\s]+harness\\b", "\\bskip\\s+delivery[-\\s]+harness\\b",
    "\\b(?:do\\s+not|don't)\\s+use\\s+(?:dhf|delivery[-\\s]+harness)\\b",
    "\\bdisable\\s+(?:dhf|delivery[-\\s]+harness)\\b",
    "不用\\s*(dhf|delivery[-\\s]*harness)", "不要\\s*(dhf|delivery[-\\s]*harness)",
    "跳过\\s*(dhf|delivery[-\\s]*harness)", "不调用\\s*(dhf|delivery[-\\s]*harness)"
  ],
  "activation_patterns": [
    "\\buse\\s+dhf\\b", "\\buse\\s+(?:the\\s+)?delivery[-\\s]+harness(?:\\s+framework)?\\b",
    "\\bcomplex\\b", "\\bresume\\b", "\\btake\\s*over\\b", "\\btakeover\\b",
    "\\bhandoff\\b", "\\bstate[-\\s]+conflict\\b", "接手", "恢复", "交接", "状态冲突",
    "(?:使用|启用|调用)\\s*(?:dhf|交付(?:治理)?框架|交付(?:治理)?流程)"
  ]
}
```

| Precedence | Input condition | Dispatcher outcome | Profile/context owner |
| --- | --- | --- | --- |
| 1 | payload is non-dict, malformed, or `cwd` is missing/invalid | safe continue-only; no traceback, partial output, or DHF context | none |
| 2 | explicit opt-out is present | continue-only, even if ShipQ or generic activation also matches | none |
| 3 | valid ShipQ cwd matches the lazy adapter boundary | lazy delegate without importing generic activated context | ShipQ adapter |
| 4 | explicit generic DHF activation matches | enter activated cohort, then select `light`, `standard`, or `governed` from task/risk signals | generic DHF profile selector |
| 5 | ordinary non-ShipQ request | continue-only with zero injected DHF context | none |

### Active Profile State Contract

The task/thread lifecycle state owner, not the stateless hook or model, is the
authoritative owner of `active_profile`. The owner transports state to the hook
in top-level `dhf_profile_state`; the hook returns only derived context and must
not claim to persist state. The state shape is:

```json
{
  "schema_version": 1,
  "task_id": "non-empty stable task id",
  "thread_id": "non-empty stable thread id",
  "active_profile": "light|standard|governed",
  "sequence": 0,
  "updated_at": "RFC3339 UTC",
  "expires_at": "RFC3339 UTC or null",
  "escalation_signals": []
}
```

The owner binds state to both current `task_id` and `thread_id`. A binding
mismatch, unknown schema/profile, non-integer or decreasing sequence, or expired
state is `malformed_profile_state`: fail closed to `governed` and require recover
before risky work. A new risk signal causes monotonic
`light -> standard -> governed` escalation before the risky action and an atomic
sequence increment; duplicate delivery at the same sequence is idempotent, and a
lower sequence is rejected. Normal prompt processing must not downgrade. Task
terminal state expires the record. Time expiry never silently downgrades; recover
reconstructs the last valid checkpoint for the same task/thread, marks prior
verification freshness accurately, and writes a higher sequence before routing
continues. Tests must cover binding mismatch, expiry, duplicate delivery,
out-of-order delivery, upgrade, forbidden downgrade, and checkpoint recovery.

### Feature Switch Contract

`DHF_PREPROMPT_SIMPLIFIED_PROFILES` accepts exactly string `"0"` (legacy route)
or `"1"` (simplified profiles). Slice 0 has no candidate activation; Slice 1
introduces the switch with absent-value default `"0"`; Slices 2-3 keep that
default; Slice 4 may change the repo-source default to `"1"` only after every
parity, recoverability, traceability, and efficiency gate passes. Any other value
is invalid and must emit a bounded diagnostic and fail closed to the legacy
route. Runtime remains unchanged until Slice 6. Rollback explicitly sets `"0"`
and proves legacy dispatcher and helper callability; merely editing prose or
unsetting a post-promotion default is not a rollback.

## Completion Claim Taxonomy

Completion language must match one of these claim classes:

| Claim class | Required evidence |
| --- | --- |
| `implemented_or_fixed` | fresh `command`, `exit_code`, `key_output`, and `timestamp`, proportionate to the claimed behavior |
| `documented_or_configured` | fresh structural/contract validation receipt with the same four fields |
| `diagnosed_or_blocked` | concrete inspected evidence and the exact blocker; commands use the four-field receipt when run |
| `verification_not_applicable` | allowed only for a pure explanation/advice response with no artifact, state, runtime, or behavior completion claim; state why verification is not applicable |

Never invent a command or receipt to satisfy the schema. A pure explanation
must use `verification_not_applicable` rather than implying that code or runtime
behavior was verified. Any generated or edited artifact is not a pure
explanation and requires fresh validation.

## Efficiency Measurement Contract

Efficiency is evaluated only with same-scenario paired observations from the
explicitly activated generic cohort. Ordinary continue-only and ShipQ delegated
scenarios remain routing/safety controls, but are excluded from the reduction
denominator because they are not injected `light` cases.

For each scenario, record baseline and candidate measurements under the same
prompt, cwd class, activation state, measurement boundary, runner version, and
byte proxy. The normative runner is deterministic local bounded execution: it
does not call a model and makes no model-quality or model-token claim. Report
injected context and mandatory helper calls separately. For each scenario and
metric with baseline `b_i > 0`, compute `r_i = (b_i - c_i) / b_i`; the estimator
is `median(r_i)` across scenarios, not a ratio of aggregate or median counts. A
zero baseline is excluded from relative-reduction aggregation and reported in a
separate absolute non-regression table; its candidate must remain zero. Sample
counts for positive-baseline and zero-baseline groups are mandatory. The 40%
target applies independently to the two per-scenario-relative-reduction medians.
Any future model-inclusive measurement requires a separate, pre-registered
repeat protocol and cannot satisfy this acceptance criterion.

## Frozen Baseline Identity And Independent Execution

Slice 0 records one immutable Base identity: `base_commit`, SHA-256 of the Base
dispatcher and Base generic skill bytes, corpus SHA-256, schema version, and
runner name/version/SHA-256. The fixture also records the current candidate
source hashes at capture time. Slice 4 executes Base and current independently
from those exact bytes in isolated directories; it must not emulate Base by
toggling the current implementation or accept a shared imported module.

Raw route/context/task output is the oracle input. The runner derives pass/fail
from executable assertions and rejects handwritten/self-reported booleans such
as `baseline_pass` or `candidate_accepted`. Any Base identity mismatch, current
source-hash drift, corpus drift, runner drift, or shared execution provenance
fails the comparison before metrics are accepted.

## Recoverability Oracle

Every governed checkpoint/recovery fixture must exercise a field-level
`checkpoint -> recover` round trip. Recovery passes only when the following
semantic fields are preserved (normalization of formatting is allowed):

- lifecycle `phase`;
- active `constraints` and forbidden actions;
- worktree/agent `ownership` boundaries;
- executable `next_action`;
- verification evidence plus its freshness state, including whether evidence
  became stale across recovery.

Missing, widened, or silently defaulted fields fail the oracle. Tests must also
prove that stale verification is not promoted to fresh after recovery.

## Acceptance Criteria
- [ ] **AC-01** The generic DHF Output Contract is reduced from an always-visible routing
      checklist to the four Result Invariants, with conditional governed fields.
- [ ] **AC-02** A deterministic classifier or equivalent explicit routing contract maps
      representative prompts to `light`, `standard`, or `governed`.
- [ ] **AC-03** Ordinary non-ShipQ prompts remain continue-only and receive no DHF context.
- [ ] **AC-04** Explicit opt-out continues to win before all project and generic activation.
- [ ] **AC-05** ShipQ continues to load only through lazy adapter delegation under its cwd.
- [ ] **AC-06** Malformed, non-dict, and missing-cwd payloads continue safely without
      leaking traceback, skill text, secrets, or unrelated local context.
- [ ] **AC-07** Light tasks do not require `harness_recover.py`, `harness_env_probe.py`,
      `harness_report.py`, lifecycle narration, or a checkpoint.
- [ ] **AC-08** Governed scenarios still select every safety/recovery gate required by
      their escalation signal.
- [ ] **AC-09** Existing helper CLI entry points remain callable after the initial slices.
- [ ] **AC-10** Golden scenarios establish 100% parity for outcome correctness, safety
      blocking, fresh verification completeness, worktree preservation, and
      recoverability where required.
- [ ] **AC-11** No scenario improves efficiency by weakening a required verification or
      permission gate.
- [ ] **AC-12** On same-scenario paired, explicitly activated light/standard observations
      with baseline greater than zero, the median of per-scenario relative
      reductions is at least 40% independently for injected DHF context and
      mandatory helper invocations; context and helpers are reported separately.
- [ ] **AC-13** Zero-baseline observations are reported separately and show absolute
      non-regression (`candidate == 0`), not an undefined relative improvement.
- [ ] **AC-14** Results include raw per-scenario measurements and sample counts; no claim
      of statistical generality is made beyond the bounded corpus.
- [ ] **AC-15** Repo source, documentation mirrors, surface inventory, tests, and evals
      agree on the same three-profile contract.
- [ ] **AC-16** Runtime sync remains blocked until source verification passes and the user
      separately authorizes runtime mutation.
- [ ] **AC-17** Governed checkpoint fixtures pass the field-level recoverability oracle.
- [ ] **AC-18** A feature-switch rollback smoke proves the simplified route can be
      disabled and legacy paths/helper entry points still execute.

## Golden Scenario Matrix
The first corpus must contain at least 15 scenarios, including:

- 4 light: explanation, bounded docs edit, one-file safe change, trivial format.
- 5 standard: local feature, failing test investigation, scoped refactor,
  non-sensitive CLI change, local UI behavior.
- 6 governed: resumed task, dirty ownership conflict, external capture,
  remote/deploy request, multi-agent plan, architecture source conflict.

Each scenario records expected profile, escalation signal or absence, mandatory
and forbidden helpers, required output fields, permission outcome, result
acceptance checks, injected-context size, helper-call count, and verification
receipt status.

The corpus owns an `acceptance_trace_map` keyed by the stable `AC-01` through
`AC-18` IDs. Every entry must contain `criterion`, `slice`, `scenario_ids`,
`test_ids`, `producer`, and `evidence_status`; `producer` identifies the slice
runner and scenario/output fixture that creates the evidence. `test_ids` resolve
through `test_catalog` entries in the exact callable form
`path.py::ClassName.test_method` or `path.py::test_function`. Validation imports
or otherwise resolves each binding and rejects missing/non-test callables,
unknown scenarios, duplicate IDs, missing producers, and non-terminal evidence
states. Renumbering an AC requires an explicit schema migration.

## Verification Gate
- `python3 -m py_compile codex/hooks/dhf_preprompt.py`
- Focused dispatcher/profile/golden-scenario tests added to `test_runner.py` or
  `tests/`, including success, missing input, malformed input, forbidden input,
  lazy import, opt-out precedence, no-leak output, and no partial write.
- `python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav`
- `python3 test_runner.py`
- `python3 scripts/check_skill_compatibility.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --plugin-root "$HOME/.codex/plugins/cache" --plugin-root "$HOME/.cache/codex-runtimes/codex-primary-runtime/plugins"`
- `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome`
- `git diff --check`

Runtime parity failures caused solely by the intentionally unsynced source-stage
change must be reported as an expected pending gate, never presented as green.

## Risks
- A shorter skill may silently omit a rare governed route unless the golden
  corpus includes adversarial escalation cases.
- Keyword-only classification may under-route implicit risk; structural signals
  and safe upgrade behavior are required.
- Token reduction can be overstated if measurement excludes adapter or system
  context; measurement boundaries must be recorded.
- Helper consolidation can create compatibility churn disproportionate to its
  value; it is gated behind successful output/routing simplification.
- Implementation-time dirty files may overlap planned surfaces, so Slice 0 must
  probe state and may require user direction when ownership cannot be isolated.

## Rollback And Compatibility
- Keep the current dispatcher and helper entry points recoverable during each
  slice.
- Put simplified profile injection behind a deterministic feature switch until
  parity gates pass. The rollback smoke disables it, exercises the legacy
  dispatcher path and old helper CLI names, and asserts their documented output
  shapes remain callable without runtime sync.
- Land profile routing behind deterministic tests before shortening the skill.
- Do not remove helper files in the initial implementation.
- If any governed scenario loses a required gate, revert the slice or disable
  the simplified path; do not compensate with documentation-only warnings.
- Runtime promotion requires source tests, compatibility checks, explicit user
  authorization, a targeted sync, and a post-sync smoke test.

## open_questions_resolved
- question: Is the objective to minimize file count or minimize execution cost?
  answer: Minimize default prompt/tool/ceremony cost first; file-count reduction
    is optional and deferred until compatibility evidence exists.
- question: May safety and verification requirements be removed for speed?
  answer: No. They are invariant; only their unconditional narration or
    unnecessary invocation may be removed.
- question: Should simplified output remain text-identical to current output?
  answer: No. Behavioral acceptance and safety parity are authoritative.
- question: Is live runtime sync part of the initial implementation?
  answer: No. Initial work is repo source-stage only; runtime mutation requires
    separate authorization.
- question: How is blind-review acceptance decided without leaking the target?
  answer: The orchestrator holds the external acceptance criterion and does not
    place it in either reviewed artifact or the blind-review prompt. The artifact
    records only closed material findings and fresh validation evidence.

## Handoff Notes
- Editable scope for this planning task is limited to this contract and
  `docs/plans/2026-07-12-dhf-simplification-implementation-plan.md`.
- During implementation, append a checkpoint only after a meaningful verified
  slice or before runtime/remote/handoff boundaries.
- Preserve all non-task-owned changes found by the fresh worktree probe. Do not
  reset, clean, push, archive, or sync runtime as part of this contract-review
  task; staging/commit coordination follows the task owner.
