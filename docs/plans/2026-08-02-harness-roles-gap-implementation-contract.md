# Harness Roles Gap Implementation Contract

Companion contract for `docs/plans/2026-08-02-harness-roles-gap-plan.md`.
Validate this file with
`python3 scripts/harness_requirements.py validate docs/plans/2026-08-02-harness-roles-gap-implementation-contract.md`
before treating it as source of truth.

Batch order: Batch-1 (R2, R5, R1-tier1) → Batch-2 (R6) → Batch-3 (R3, R4,
R1-tier2, executed only after infra plan W2/W4 land). One role = one commit.
Every `## Scope`, `## Constraints`, and `## Acceptance Criteria` entry is
grouped per role; a `Global` group applies to all.

## Goal
Deliver the six missing harness roles identified from authoritative-source gap
analysis — behavior evaluator (R1), tamper-resistant task ledger (R2), session
bearing ritual (R3), context meter (R4), memory reflection (R5), and guardrail
risk tiers (R6) — as executable infrastructure with per-role degradation paths
when infra-plan dependencies are not yet landed, zero policy text changes, and
zero regressions against the recorded baseline.

## Audience
- Codex operator
- Future agent resuming this repo

## Scope

### R1 behavior evaluator
- New: `scripts/harness_eval.py`, `docs/evals/` scenario fixtures.
- Tests: new `test_harness_eval_tier1` (recovery eval, handoff lint);
  `test_harness_eval_tier2` added only in Batch-3.
- Weekly audit: one line added to
  `codex/skills/codex-fluent/references/maintenance-checklist.md` for tier-3.

### R2 task ledger
- New: `scripts/harness_ledger.py` (subcommands `init`, `pass`, `verify`).
- Tests: new `test_harness_ledger_contract`.

### R3 session bearing (Batch-3)
- New: `codex/hooks/session_bearing.py`; register in `codex/hooks.json`
  SessionStart chain (source only; deployment follows infra plan W6a gate).
- Tests: new `test_session_bearing_hook`.

### R4 context meter (Batch-3)
- Consumes the merged Phase-0 probe result from infra plan W2 (one probe
  records both session id and usage fields).
- New if usage present: `codex/hooks/context_meter.py` or merged into
  `compaction_probe.py`; store at `~/.codex/harness/meter.json`.
- Tests: new `test_context_meter_persistence`.

### R5 memory reflection
- Modified: `scripts/codex_subconscious.py` (new `reflect` subcommand only).
- Tests: new `test_subconscious_reflect`.

### R6 guardrail risk tiers
- Modified: `codex/runtime/tool-policy.json` (add `risk_tier` per category),
  `codex/hooks/harness_guard.py` (emit tier in decision evidence only).
- Tests: extend `test_harness_guard_policy_decisions`.

### Global
- State: `docs/harness-state.md` checkpoint append after every role commit.
- Docs: `docs/HARNESS_RUNTIME.md` and `docs/AGENT_HARNESS_STATUS.md` rows for
  new surfaces; `docs/surfaces.json` + `docs/repo-index.md` per
  `scripts/check_surfaces.py`.

## Non-Goals
- No edits to `codex/AGENTS.md` or `README.md` policy text (gate plan owns them).
- No edits to `tests/fixtures/codex_fluent_report.golden.md`.
- No change to any guard block/allow behavior in R6 (annotation only).
- No fabricated capacity data in R4: absent usage fields read as unknown.
- No automatic deletion of decision-kind records in R5.
- No `~/.codex` sync or hook deployment outside the infra plan W6a gate.

## Constraints

### R1
- Every eval is fixture input + end-state assertion + PASS/FAIL with the four
  verification fields; no free-form quality judgment.
- tier-1 must run with zero dependency on infra plan workstreams; tier-2 evals
  are added only after infra W1+W2 land; tier-3 is weekly audit only, never a
  merge gate.

### R2
- `init` derives ledger entries from a validated requirements artifact and
  records a sha256 over all descriptions+steps; `init` is idempotent.
- `pass` is the only legal status transition and requires the four
  verification fields; missing fields exit non-zero.
- `verify` recomputes the content hash; any add/remove/edit of entry bodies
  (as opposed to the passes bit) fails non-zero.

### R3
- Budget under 200ms typical; any failure exits silently.
- If infra W4 `--boundary` is unavailable, degrade to existing recover output;
  never block session start.

### R4
- Probe-first: build nothing until the merged W2 Phase-0 probe records whether
  usage fields exist. If absent, R4 degrades to the compaction-ordinal
  pressure signal and the conclusion is recorded as decision evidence.

### R5
- `reflect` merges duplicates and prunes only routine/derived records past
  retention; decision-kind records are never pruned; report counts
  merged/pruned/kept.

### R6
- Hard gate: any commit touching `harness_guard.py` must include fresh
  isolated-probe evidence (recorded before merge) proving block behavior is
  unchanged; the fail-open history makes this non-negotiable.

### Global
- Use Python standard library only unless the repo already provides a dependency.
- Do not commit local evidence logs, credentials, auth files, or transcripts.
- Preserve append-only state and unrelated user changes.
- Landing precondition: inherit the infra contract's landing precondition —
  the uncommitted user-owned policy changeset on `main` must be resolved
  (committed by the user, or explicit-path staging mode confirmed) before this
  contract's baseline applies.
- Baseline protocol: reuse the infra-plan baseline checkpoint if fresh
  (same HEAD); otherwise re-record before Batch-1. Per-role acceptance is zero
  new failures versus baseline.
- No role commit includes changes to `codex/AGENTS.md`, `README.md`, or
  `tests/fixtures/codex_fluent_report.golden.md`; pre-existing user-owned
  working-tree changes to those files are left untouched, never reverted or
  absorbed into role commits.
- One role = one commit; revert of any single commit must not break another
  role (shared code only via the W2 counting function, locked by scanner tests).

## Task Demand (D_task)
- estimated_level: high
- L (reasoning/action steps): Roughly 35-50 steps across 6 commits in 3 batches: two new scripts, two new hooks, two script extensions, one policy-file annotation, fixtures directory, and 6 new or extended test functions.
- H_tool (tool-selection ambiguity): Low. Python stdlib, existing test harness and helper conventions; probe-first rules resolve the only unknowns.
- S_state (cross-module state tracking): High. Three interdependent plans (gate, infra, roles) with an explicit dependency matrix, per-role degradation paths, and no-touch boundaries around policy files, golden fixtures, and guard behavior.
- N_obs (observation/external noise): Medium. Unknown hook payload usage fields until the merged probe, real-session corpora needed for tier-3 audit, and a possibly-stale baseline requiring HEAD comparison.

## Source Of Truth
- `AGENTS.md`
- `docs/repo-index.md`
- `docs/harness-state.md`
- `docs/HARNESS_RUNTIME.md`
- `docs/AGENT_HARNESS_STATUS.md`
- `docs/plans/2026-08-02-harness-roles-gap-plan.md`
- `docs/plans/2026-08-02-harness-infra-compaction-implementation-plan.md`

## Acceptance Criteria

### Baseline
- [ ] Baseline checkpoint verified fresh (same HEAD as infra-plan baseline) or re-recorded in `docs/harness-state.md` before Batch-1.

### R1
- [ ] `harness_eval.py` runs tier-1 evals (recovery eval, handoff lint) from `docs/evals/` fixtures, emitting PASS/FAIL plus command, exit_code, key_output, timestamp per eval.
- [ ] New test `test_harness_eval_tier1` passes; tier-1 evals require no infra-plan surface.
- [ ] Maintenance checklist contains the tier-3 weekly audit line.

### R2
- [ ] `harness_ledger.py init --from <validated requirements>` produces `ledger.json` with all entries `passes:false` and a content hash; re-running init is a no-op.
- [ ] `pass` without complete verification fields exits non-zero; with fields it flips exactly one passes bit.
- [ ] `verify` catches body tampering (add/remove/edit) via hash mismatch, exit non-zero.
- [ ] New test `test_harness_ledger_contract` passes covering all three behaviors.

### R3
- [ ] `session_bearing.py` injects phase, next_safe_task, boundary_verdict, dirty_status at SessionStart; uses `--boundary` when available, degrades to plain recover output otherwise.
- [ ] Silent-failure path proven: hook error leaves session start unaffected.
- [ ] New test `test_session_bearing_hook` passes covering injection shape, degraded path, and silent failure.

### R4
- [ ] Merged Phase-0 probe evidence records presence/absence of usage fields before any meter code exists.
- [ ] If present: meter persists latest usage to `~/.codex/harness/meter.json` and injects remaining-capacity estimate; if absent: decision evidence records the degradation to ordinal-only signal.
- [ ] New test `test_context_meter_persistence` passes covering both paths.

### R5
- [ ] `codex_subconscious.py reflect` merges duplicates, prunes only routine/derived past retention, and reports merged/pruned/kept counts.
- [ ] Decision-kind records survive reflect unchanged, proven by test.
- [ ] New test `test_subconscious_reflect` passes.

### R6
- [ ] Every category in `tool-policy.json` carries `risk_tier`; guard decision evidence includes the tier.
- [ ] Isolated-probe evidence recorded before merge proves block/allow behavior identical pre/post change.
- [ ] Extended `test_harness_guard_policy_decisions` passes asserting tier presence.

### Global (every role commit)
- [ ] Zero new test failures versus the recorded baseline.
- [ ] `git diff` shows no changes to `codex/AGENTS.md`, `README.md`, or `tests/fixtures/codex_fluent_report.golden.md`.
- [ ] `scripts/check_surfaces.py` passes if surfaces changed.
- [ ] Checkpoint appended to `docs/harness-state.md` with verification fields.

## open_questions_resolved
- question: Do R3/R4/R1-tier2 block on the infra plan, or can this plan start independently?
  answer: Explicit dependency matrix in the plan — Batch-1 (R2, R5, R1-tier1) and Batch-2 (R6) have zero infra dependencies and start immediately; Batch-3 items each carry a defined degradation path and execute after infra W2/W4 land.
- question: Should the R4 usage-field probe duplicate the infra W2 Phase-0 probe?
  answer: No — one merged probe records both session id and usage fields; both consumers read the same probe evidence.
- question: How is the R2 ledger protected from agent tampering without a signing scheme?
  answer: Three-piece design per Anthropic's findings — JSON form factor, sha256 over entry bodies checked by `verify` in the verification gate, and a contract test; signing was rejected as complexity without a matching threat model.
- question: Why does R6 need a probe gate for an annotation-only change?
  answer: `harness_guard.py` has a confirmed fail-open history (2026-07-28 probe); any edit to it, however small, must re-prove block behavior with isolated-probe evidence before merge.

## Verification Gate
- `python3 scripts/harness_requirements.py validate docs/plans/2026-08-02-harness-roles-gap-implementation-contract.md`
- `python3 test_runner.py`
- `git diff --check`
- `python3 scripts/check_surfaces.py`
- `python3 scripts/harness_ledger.py verify` (once R2 lands, for any task using a ledger)

## Risks
- Three-plan coordination: gate plan owns policy text, infra plan owns W1-W6,
  this plan owns roles; a change crossing boundaries must be split, not merged.
- Tier-3 evals depend on real-session corpora and may stay sparse; they are
  audit-only so sparseness degrades coverage, not correctness.
- R6 touches the highest-risk file in the repo; the probe gate mitigates but
  does not eliminate host-behavior drift.
- Red or stale baseline can mask new failures; HEAD-comparison rule mitigates.

## Handoff Notes
- Record phase, verification evidence, blockers, and next safe task in
  `docs/harness-state.md` after every role commit via
  `scripts/harness_checkpoint.py`.
- If a Batch-3 dependency has not landed, checkpoint the blocker and proceed
  with remaining independent roles; never improvise a dependency substitute.
