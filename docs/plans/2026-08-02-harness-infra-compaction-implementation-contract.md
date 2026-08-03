# Harness Infra Compaction Implementation Contract

Companion contract for
`docs/plans/2026-08-02-harness-infra-compaction-implementation-plan.md`.
Validate this file with
`python3 scripts/harness_requirements.py validate docs/plans/2026-08-02-harness-infra-compaction-implementation-contract.md`
before treating it as source of truth.

Workstream order: W6b → W1 → W2 → W3 → W4 → W5. One workstream = one commit,
with the single exception that W2 lands as two commits (W2a then W2b, defined
in the W2 constraints). W6a is user-gated and executes as its own commit
whenever approved.
Every `## Scope`, `## Constraints`, and `## Acceptance Criteria` entry below is
grouped per workstream; a `Global` group applies to all workstreams.

## Goal
Deliver the six workstreams (W6b, W1, W2, W3, W4, W5, plus user-gated W6a) from
the implementation plan as executable harness infrastructure: transition
idempotency store, host-observed compaction probe, checkpoint/evidence
compaction fields, boundary verdict, and S_state exposure — with zero policy
text changes and zero regressions against the recorded baseline.

## Audience
- Codex operator
- Future agent resuming this repo

## Scope

### W6b guard fail-open closure
- Touches: local evidence (decision event), `docs/HARNESS_RUNTIME.md` guardrail
  statement only if the probe contradicts it.

### W1 transition idempotency store
- New: `scripts/harness_transition.py`.
- Storage: `~/.codex/harness/transitions.jsonl` (runtime-local, never committed).
- Tests: new `test_harness_transition_record_and_query` in `test_runner.py`.

### W2 host-observed compaction probe
- New: `codex/hooks/compaction_probe.py`.
- Modified: `codex/skills/codex-fluent/scripts/report_active_sessions.py`
  (extract shared compaction counting function only; output contract unchanged),
  `codex/hooks.json` (register probe in UserPromptSubmit chain, source only).
- Tests: new `test_compaction_probe_session_resolution` in `test_runner.py`.

### W3 checkpoint and evidence compaction fields
- Modified: `scripts/harness_checkpoint.py`,
  `codex/runtime/evidence.schema.json`,
  `codex/runtime/evidence/decision-evidence.schema.json`.
- Tests: extend `test_harness_checkpoint_helper` and
  `test_harness_evidence_append_and_observer_failure_mode`.

### W4 boundary verdict
- Modified: `scripts/harness_recover.py` (`--boundary`,
  `--max-verification-age`).
- Tests: extend `test_harness_recovery_smoke`.

### W5 S_state exposure
- Modified: `scripts/harness_recover.py` (payload `task_demand` field only).
- Tests: extend `test_harness_recovery_smoke`.

### W6a runtime parity and deployment (user-gated)
- Touches: `~/.codex` via approved sync; deploys `compaction_probe.py` to
  `~/.codex/hooks`; fixes the 4 runtime-parity failures reported by
  `./scripts/verify_codex_env.sh`.

### Global
- State: `docs/harness-state.md` checkpoint append after every workstream commit.
- Docs: `docs/HARNESS_RUNTIME.md` and `docs/AGENT_HARNESS_STATUS.md` rows for
  new surfaces; `docs/surfaces.json` + `docs/repo-index.md` if
  `scripts/check_surfaces.py` requires it.

## Non-Goals
- No edits to `codex/AGENTS.md` or `README.md` policy text. Thread Discipline
  policy changes belong exclusively to
  `docs/plans/2026-08-02-thread-discipline-compaction-gate-plan.md`.
- No edits to `tests/fixtures/codex_fluent_report.golden.md`.
- No changes to scanner output semantics (`handoff_required` stays
  `compaction_count >= 2`).
- No `~/.codex` runtime sync or deployment outside W6a.
- No policy consumption of S_state (W5 is pipe only; gate plan owns policy).

## Constraints

### W6b
- Rerun the 2026-07-28 isolated guard probe methodology; conclusions go to
  decision evidence in the same commit. Do not "fix" the guard beyond what the
  probe proves; scope is closing the fail-open to-do with evidence.
- Note: the guard `block()` upgrade already exists in the uncommitted
  working-tree changeset (see landing precondition). W6b's job is therefore
  verify-and-evidence, not implement: rerun the probe against the landed
  guard, record the evidence, and correct docs only if the probe contradicts
  them.

### W1
- Record semantics: O_APPEND single-line JSON append, re-read after append,
  first record per key wins (CAS). Recording a key that already has a different
  task_id exits non-zero and prints the prior record.
- Query: first record per key, or explicit not-found; missing file is
  not-found, not an error. Malformed lines are skipped and counted.

### W2
- Phase-0 is a hard gate: record one real UserPromptSubmit payload to local
  evidence and confirm whether a session/thread id is present before writing
  the probe implementation. The same probe evidence must also record whether
  usage/token fields are present, for consumption by the roles-gap plan R4
  context meter (one merged probe, two consumers). If no id, implement heuristic-only resolution
  (cwd match + mtime window + unique candidate; otherwise inject nothing) and
  record that decision as decision evidence. Never guess.
- Probe budget: under 100ms typical; on timeout or any exception, exit
  silently without blocking the prompt (observer precedent).
- Incremental scanning is mandatory: the probe caches the last-read offset per
  session file in `~/.codex/harness/probe_state.json` and reads only appended
  bytes each turn; a full rescan is permitted only when the state is missing,
  corrupt, or the file shrank (rotation/truncation), and must rebuild the
  state. A per-turn full scan of session JSONL is a defect, not a fallback.
- W2 lands as two commits: W2a (shared counting-function extraction, scanner
  refactor, Phase-0 probe evidence including session-id and usage-field
  presence) then W2b (probe implementation with incremental scanning and
  probe_state, both new tests, hooks.json registration). W2a must merge before
  W2b.
- The extracted counting function is the single source for `"compacted"` event
  counting; scanner behavior is locked by its existing test and fixture.

### W3
- Schema changes are additive optional fields only (`compaction_ordinal`,
  `transition_key`, `gate_decision`); old events without the fields read as
  absent, never migrated, never errors.
- New checkpoint arguments are optional; existing invocations must work
  unchanged.

### W4
- `safe` requires all of: `dirty_status == clean`; latest verification
  `exit_code == 0`; verification timestamp not older than
  `--max-verification-age` (default 24h) and not older than the latest commit.
  Anything undeterminable returns `unknown` (fail-closed; callers treat as
  unsafe).

### W5
- Read `estimated_level` and `S_state` from the latest artifact that passes
  `harness_requirements.py validate`; absent or invalid reads as `unknown`.
  No policy logic.

### W6a
- Requires explicit user approval before any `~/.codex` write. Stop and ask
  when reaching this workstream.

### Global
- Use Python standard library only unless the repo already provides a dependency.
- Do not commit local evidence logs, credentials, auth files, or transcripts.
- Preserve append-only state and unrelated user changes.
- Landing precondition (before anything else): as of 2026-08-02 the entire
  second-compaction policy layer (AGENTS.md Thread Discipline sequences,
  README bullet, `test_global_agents_second_compaction_successor_contract`,
  guard `block()` upgrade, runtime doc updates) exists only as uncommitted
  user-owned working-tree changes on `main` (HEAD befa97f). This changeset is
  the policy foundation this contract builds on. Stop and ask the user to
  commit it (as their own commit, not a workstream commit) before recording
  the baseline. If the user declines, all workstream commits must stage
  explicit paths only, and any contract test asserting policy text runs
  against the working tree.
- Baseline protocol: after the landing precondition is resolved, run
  `python3 test_runner.py`, record pass/fail counts and failing test names as
  a baseline checkpoint in `docs/harness-state.md`. Per-workstream acceptance
  is zero new failures versus that baseline. Full-suite green plus
  `./scripts/verify_codex_env.sh` green is required only at W6a completion.

## Task Demand (D_task)
- estimated_level: high
- L (reasoning/action steps): Roughly 30-45 concrete steps across 6-7 commits: baseline recording, probe rerun, two new scripts, one new hook, two script extensions, two schema extensions, shared-function extraction, and 6+ test additions or extensions.
- H_tool (tool-selection ambiguity): Low. Python stdlib, existing test_runner.py harness, git, and existing helper conventions; no new tool categories.
- S_state (cross-module state tracking): High. Coordinated changes across scripts, hooks, hooks.json, schemas, scanner, surfaces inventory, tests, and append-only state log, with a strict no-touch boundary around policy files and golden fixtures.
- N_obs (observation/external noise): Medium. Host session JSONL observation, unknown UserPromptSubmit payload shape until the Phase-0 probe, and a currently-red verification baseline that must be isolated from new-failure detection.

## Source Of Truth
- `AGENTS.md`
- `docs/repo-index.md`
- `docs/harness-state.md`
- `docs/HARNESS_RUNTIME.md`
- `docs/AGENT_HARNESS_STATUS.md`
- `docs/plans/2026-08-02-harness-infra-compaction-implementation-plan.md`

## Acceptance Criteria

### Baseline (before W6b)
- [ ] Baseline checkpoint exists in `docs/harness-state.md` recording full-suite pass/fail counts and failing test names before any W6b change.

### W6b
- [ ] Isolated guard probe rerun evidence recorded as decision evidence.
- [ ] `docs/HARNESS_RUNTIME.md` guardrail statement confirmed accurate, or corrected in the same commit with the probe evidence cited.

### W1
- [ ] `python3 scripts/harness_transition.py record --key K --task-id T` then `query --key K` round-trips.
- [ ] Duplicate key with different task-id exits non-zero and prints the prior record.
- [ ] New test `test_harness_transition_record_and_query` passes covering round-trip, first-record-wins, mismatch rejection, malformed-line tolerance, and missing-file not-found.

### W2
- [ ] Phase-0 payload evidence exists and predates the probe implementation commit, recording both session-id presence and usage-field presence.
- [ ] Shared compaction counting function is used by both `report_active_sessions.py` and `compaction_probe.py`.
- [ ] `test_codex_fluent_active_session_report` passes without fixture changes.
- [ ] New test `test_compaction_probe_session_resolution` passes covering id-hit, three-condition heuristic, no-injection on ambiguity, and silent failure.
- [ ] New test `test_compaction_probe_incremental_scan` passes covering correct counting under append-only growth, offset-cache reuse, full-rescan fallback on file shrink or corrupt state, and proof via a large fixture that the incremental path does not re-read the whole file.
- [ ] W2a merged before W2b, with Phase-0 probe evidence timestamped in W2a.

### W3
- [ ] `harness_checkpoint.py` accepts `--compaction-ordinal`, `--transition-key`, `--gate-decision {continue-to-boundary,immediate-successor,none}`.
- [ ] Both evidence schemas accept the new optional fields.
- [ ] Extended `test_harness_checkpoint_helper` and `test_harness_evidence_append_and_observer_failure_mode` pass, including old-format interop assertions.

### W4
- [ ] `harness_recover.py --boundary` returns `safe` only under the W4 constraints; otherwise `unsafe` or `unknown` with reasons.
- [ ] Extended `test_harness_recovery_smoke` passes covering safe, dirty-unsafe, stale-unknown, and empty-unknown.

### W5
- [ ] `harness_recover.py` payload includes `task_demand` with `estimated_level` and `S_state`, `unknown` when absent or invalid.
- [ ] Extended `test_harness_recovery_smoke` asserts presence and fallback.

### W6a (user-gated)
- [ ] User approval recorded before any `~/.codex` write.
- [ ] After approved sync: `python3 test_runner.py` fully green and `./scripts/verify_codex_env.sh` passes.
- [ ] `compaction_probe.py` deployed to `~/.codex/hooks` in this step only.

### Global (every workstream commit)
- [ ] Zero new test failures versus the recorded baseline.
- [ ] No workstream commit includes changes to `codex/AGENTS.md`, `README.md`, or `tests/fixtures/codex_fluent_report.golden.md` (verified per commit via `git show --stat`; pre-existing user-owned working-tree changes to these files are left untouched, not reverted).
- [ ] `scripts/check_surfaces.py` passes if surfaces changed.
- [ ] Checkpoint appended to `docs/harness-state.md` via `scripts/harness_checkpoint.py` with verification fields.

## open_questions_resolved
- question: Does the UserPromptSubmit hook payload contain a session or thread id usable for session-file resolution?
  answer: Unknown at contract time; resolved procedurally — W2 Phase-0 probe is a hard gate that records a real payload before implementation, with the heuristic-only fallback design pre-agreed in the implementation plan.
- question: The current verification baseline is red (89/93 with 4 runtime-parity failures per `docs/harness-state.md`); how can acceptance require green?
  answer: Baseline protocol — record the baseline first; per-workstream acceptance is zero new failures versus baseline; full green is required only at W6a completion, whose scope is exactly those parity failures.
- question: Who owns the AGENTS.md and README policy text changes that will consume these helpers?
  answer: `docs/plans/2026-08-02-thread-discipline-compaction-gate-plan.md` exclusively; this contract forbids touching those files.

## Verification Gate
- `python3 scripts/harness_requirements.py validate docs/plans/2026-08-02-harness-infra-compaction-implementation-contract.md`
- `python3 test_runner.py`
- `git diff --check`
- `python3 scripts/check_surfaces.py`
- `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"` (required at W6a; advisory before)

## Risks
- Red baseline can mask genuinely new failures; mitigated by recording failing test names, not just counts.
- Payload shape assumptions in W2 can silently rot if the host changes hook payloads; probe evidence records the observed shape for future comparison.
- Shared counting function couples scanner and probe; the scanner's own test locks the contract.
- Runtime docs and scripts can drift if tests do not cover the contract.

## Handoff Notes
- Record phase, verification evidence, blockers, and next safe task in `docs/harness-state.md` after every workstream commit via `scripts/harness_checkpoint.py`, including the new compaction fields once W3 lands.
- If any workstream is blocked (probe shows no viable session resolution, sync not approved, unexpected baseline drift), stop that workstream, checkpoint the blocker, and continue with the next independent workstream rather than improvising.
