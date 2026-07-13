# Harness Runtime

> **DHF_PUBLIC_STATUS_V1 · 2026-08-03:** This file is the source contract, not
> proof of the currently installed runtime. Current source/runtime/publication
> status: [English](./dhf-architecture-status-en.html) ·
> [中文](./dhf-architecture-status-cn.html). The approved W6a sync passed
> historically, but a fresh comparison now detects runtime drift.

## Purpose
MyCodexEnv treats the model as only one part of the agent system. The harness
runtime provides the surrounding workflow and infrastructure: state, tool
routing, permissions, evidence, verification, checkpoints, and recoverable
handoffs.

## DHF Source-Stage Contract Mirror

Canonical profile and Result Invariant semantics live in
`codex/skills/delivery-harness-framework/SKILL.md`; routing and rollout-switch
behavior live in `codex/hooks/dhf_preprompt.py`.

- Governance profiles are `light`, `standard`, and `governed`.
- Generic injection requires explicit generic activation; an ordinary
  non-project prompt stays continue-only. opt-out is evaluated before every
  route, and a ShipQ cwd uses ShipQ adapter lazy delegation.
- Every completion preserves exactly `result`, `scope_and_constraints`,
  `verification_receipt`, and `remaining_risk_or_next_action`; profile-specific
  ceremony is conditional rather than repeated by default.
- The source candidate is enabled only by
  `DHF_PREPROMPT_SIMPLIFIED_PROFILES=1`; default remains `legacy`. Runtime
  promotion is pending separate authorization, and runtime home remains
  unsynced.

## Workflow Contract
The lifecycle router uses these stages:

| Stage | Write Access | Network | Subagents | Minimum Gate |
| --- | --- | --- | --- | --- |
| `research` | no | only if explicitly allowed | optional read-only | source files read and cited |
| `requirements` | no | no by default | no | success criteria captured |
| `planning` | no | no by default | optional read-only | implementation plan and validation gate |
| `development` | yes, scoped | no by default | optional scoped workers | focused tests for touched behavior |
| `validation` | no repo edits by default | browser/test-only if needed | optional review/qa | fresh verification evidence |
| `review` | no by default | no by default | optional read-only reviewers | findings or no-issue statement |
| `ship` | yes, only requested release actions | yes if release requires it | optional | ship/deploy gates |
| `handoff` | no | no | no | state log and next safe task |

Memory is a hint. Before acting, Codex must verify against repo files, git state,
tests, or runtime evidence.

### Tool policy classification boundaries

The `secret` category has two independent classifiers. Anchored
`secret_path_patterns` inspect only candidate path fields, while
`secret_command_patterns` inspect only `tool_input.command` or `cmd` for
credential-shaped literals. Both classifiers are case-insensitive and every
match remains a hard block in every phase.

The classifier does not inspect file contents. It reads command text and the
path-like fields `path`, `file`, `file_path`, `filename`, `cwd`, and `workdir`;
content carried by a tool payload never participates. Consequently, this gate
cannot stop a credential from being written to an ordinarily named file.

There is no approval or `ask` channel. The host's unsupported `ask` result is
fail-open, so `secret`, `destructive`, and `dynamic_exec` are hard blocks in
every phase. `minimum_gate` is a human-readable acceptance description, not an
executable policy field. `plan_governor` is a status record whose current
`mode: shadow` and `production_status: no_go` values are not executable policy.

`allow_subagents` is executable policy. `requirements` and `handoff` set it to
`false`, so configured agent dispatch is blocked in those phases before any
fresh validation receipt can short-circuit the receipt gate. If the key is
missing or is not the boolean `false`, receipt-based behavior is preserved.

## Phase 0-pre Source Guard

`scripts/sync_codex_home.sh` performs one source-attestation preflight after
argument validation and before any managed runtime write. It checks the required
source file set, source role/path agreement, source cleanliness, membership in an
approved-digest manifest, runtime-to-source direction, and producer
attestation when automation is involved. Failures exit `78`, emit one JSON object
with `status=blocked` and `authorized_clone_root=null`, and use one of these stable
reason codes:

- `source_required_file_missing`
- `source_role_path_mismatch`
- `source_dirty`
- `approved_manifest_dirty`
- `source_digest_unapproved`
- `runtime_newer_than_source`
- `attestation_producer_dirty_or_unapproved`

The source roles are `git_head` (committed source of truth), `caller_worktree`
(manual source), `automation_controller` (producer only), and
`automation_execution_clone` (automation sync source). `runtime_disk` is only a
disk target observation; it is not loaded-state evidence. The automation producer
set is exactly the launcher `run-network-enabled.sh`, `automation.toml`, and the
controller copy of the actually executed `prepare_gstack_dhf_daily_refresh.py`.
The prepare-to-sync edge is prompt-mediated, not a protected function call.

Approved source digests are read only from the tracked, clean repository file
`runtime-approvals/approved-source-digests.txt`; the caller cannot select a
different authority with `PHASE0_APPROVED_DIGESTS_FILE`. Valid entries use
`sha256:<64 lowercase hex characters>  <reviewed description>`, while blank and
comment lines are ignored. A missing or empty manifest approves nothing. Every
blocked preflight receipt includes `approved_source` (`repo_manifest` or
`absent`), the absolute `approved_manifest_path`, and the manifest's own
`approved_manifest_digest` (or `null` when absent).

The manifest lives outside `codex/`, so changing an approval or its comments
does not change the source digest and the file is not copied into the runtime.
This prevents accidental or unreviewed synchronization of an unexpected source
version; it does not stop a repository writer from changing source and approval
together. The manifest is an auditable code-review control, not mechanical
authorization isolation. Defending against an intentional repository writer
would require a separately designed signed commit or tag scheme.

Full-sync directory promotion uses an exact source-file allowlist and never
deletes non-target files. Each file is copied to a same-directory temporary file,
`fsync`ed, metadata-preserved, installed with `os.replace`, and followed by parent
directory `fsync`. A backup manifest and append-only journal support rollback of
partial copy, disk-digest mismatch, and self-test failure. This guarantees
per-file atomic replacement and a crash-recoverable transaction, not atomic
visibility of the whole file set to a host loader. A nonblocking `fcntl.flock`
serializes writers; contention exits `75` with `reason_code=lock_contended` before
managed targets change.

`--sync-agents-only` writes only `AGENTS.md`, `remote-access.md`, and
`remote-hosts.md` (plus backups of those files). It does not write hooks,
runtime policy, zsh helpers, `hooks.json`, `config.toml`, or a sync manifest, and
there is no legacy bypass flag.

The receipt boundaries remain distinct:

- producer manifest: `schema_version`, `verified_at`, `result`, `reason_code`,
  and `producers[]` entries containing `role`, `path`, `sha256`, `git_clean`, and
  `dirty_paths`;
- promotion receipt: transaction timestamps and id, producer/source/allowlist/
  backup digests, disk and loaded digests before/after, non-allowlist invariant,
  policy/self-test outcomes, final outcome, and reason code;
- controlled-unpause receipt: unpause timestamp, referenced producer/promotion
  receipt digests, checkout/controller/execution-clone/disk/loaded digests,
  prepare-to-sync ordering, policy/self-test outcomes, final outcome, and reason
  code.

`harness_observer.py` refreshes `${CODEX_HOME}/harness/loaded-receipt.json` on
every invocation. The atomic, mode-`0600` receipt records the executing
`__file__` path and its runtime-computed SHA-256 digest, session and event
identity, and a timezone-aware timestamp. Receipt write failures do not block
the originating tool event; the next sync fails closed instead.

Before runtime mutation, sync requires a valid receipt, rejects a receipt older
than the prior manifest with `loaded_readback_stale`, and rejects a digest that
does not match the current runtime observer with `loaded_readback_mismatch`.
Missing, malformed, timezone-naive, or otherwise unavailable evidence uses
`loaded_readback_unavailable`; timestamps are parsed and compared as instants,
not strings. Disk digest must never be reported as loaded digest.

Sync manifests are written as schema 3 with `loaded_readback` (`verified` or
`bootstrap_operator_attested`) and `loaded_receipt_digest`; schema 2 remains
readable for transition compatibility. A target with neither manifest nor
receipt can cross the gate once with `--bootstrap-loaded-readback` plus a valid
four-field `--operator-checkpoint`. Bootstrap is rejected when a receipt exists
or a schema 3 manifest already records `loaded_readback`, so it cannot be used
again after the first crossing.

This source contract does not establish runtime sync, runtime load, rollout
observation, automation unpause, pilot start, or owner GO. Receipt evidence is
drift and operator-error control, not isolation from an actor who can write the
runtime directory.

Requirements artifacts use `docs/templates/harness-requirements.md`. Validate
them with `scripts/harness_requirements.py validate PATH` before treating them
as source of truth.

For execution tracking, `scripts/harness_ledger.py init --from PATH` derives a
JSON ledger from a validated requirements artifact. The ledger starts every
criterion at `passes:false`, hashes the ordered descriptions and steps, and is
idempotent when the source is unchanged. Only `harness_ledger.py pass` records a
successful transition, and it requires `command`, `exit_code`, `key_output`,
and `timestamp`. Run `harness_ledger.py verify` to reject added, removed, or
edited criterion bodies.

Automatic successor creation uses `scripts/harness_transition.py`. Its runtime
store is `~/.codex/harness/transitions.jsonl`: `record` performs one single-line
`O_APPEND` write and then re-reads the store, while `query` returns the first
valid record for a key. The first record wins under concurrent writers; a later
different task id exits non-zero and prints that prior record. Missing files are
explicit not-found results, and malformed lines are skipped and counted.

Behavior evaluation uses `scripts/harness_eval.py` with versioned scenarios in
`docs/evals/`. Tier 1 runs without compaction infrastructure: the recovery eval
builds an isolated fixture repo and asserts recovered phase, next-safe task, and
latest verification; the handoff lint requires the frozen thread anchors, a
non-empty artifact list, complete verification evidence, and exactly one
next-safe task. Each eval emits PASS/FAIL with command, exit code, key output,
and timestamp.

Tier 2 runs only after W1/W2. Its transition fixture executes the real
first-record-wins helper and asserts that a conflicting task id, the query, and
the JSONL end state all resolve to one successor. Its probe-agreement fixture
runs the real incremental prompt probe and codex-fluent scanner over the same
session JSONL and requires identical host-observed ordinals. Tier 1 remains
callable without either infra script; tier 3 remains weekly audit-only.

Validated requirements artifacts must include `## Task Demand (D_task)`.
The validator requires `estimated_level` to be exactly `low`, `medium`, or
`high`, and requires non-empty `L`, `H_tool`, `S_state`, and `N_obs` fields.
It does not score, infer, or deeply validate the semantic quality of those
values; they remain operator or agent estimates that can be refined in later
planning.

When a repo has domain docs, use `CONTEXT.md`, `CONTEXT-MAP.md`, and relevant
ADRs as planning inputs. They sharpen domain vocabulary, surface ADR conflicts,
and keep plans from inventing inconsistent terms.

For the current project workflow and skill routing map, read
`docs/LIFECYCLE_SKILL_ROUTING.md`.

## Related Documentation
- `docs/dhf-architecture-status-en.html`: canonical English source/runtime/publication status.
- `docs/dhf-architecture-status-cn.html`: canonical Chinese source/runtime/publication status.
- `README.md`: top-level quick start and Harness Runtime overview.
- `docs/repo-index.md`: low-token repo navigation and runtime surface index.
- `docs/surfaces.json`: canonical machine-readable runtime surface inventory.
- `docs/LIFECYCLE_SKILL_ROUTING.md`: lifecycle stage, workflow, skill, and helper routing.
- `docs/MODEL_ROUTER_EVAL_MATRIX.md`: prompt/subtask model router eval matrix.
- `docs/index.html`: Chinese public Delivery Harness Framework docs entry for GitHub Pages.
- `docs/index-en.html`: English public Delivery Harness Framework docs entry for GitHub Pages.
- `docs/delivery-harness-beginner-guide-cn.html`: beginner-oriented Chinese explanation of what Delivery Harness Framework does.
- `docs/delivery-harness-beginner-guide-en.html`: beginner-oriented English explanation of what Delivery Harness Framework does.
- `docs/AGENT_HARNESS_STATUS.md`: Agent Harness workflow/infra status map.
- `docs/CODEX_ENV_REPRODUCTION.md`: Codex + Claude environment reproduction guide.
- `docs/project-lifecycle-harness-flow-cn.html`: Chinese vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-en.html`: English vertical lifecycle flow.
- `docs/project-lifecycle-harness-flow-skills.html`: Chinese lifecycle skill/helper routing visual guide.
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`: current styled Chinese Delivery Harness Framework skill/helper routing visual guide.
- `docs/project-lifecycle-harness-flow-skills-en-status-style.html`: current styled English Delivery Harness Framework skill/helper routing visual guide.

## Infra Contract
- `Sandbox`: Codex sandboxing and approval rules remain the primary technical boundary; `scripts/harness_env_probe.py` reports the observable runtime configuration.
- `Memory`: `docs/harness-state.md` is the repo-visible memory surface; `scripts/harness_recover.py` proves recovery from state, git, and local evidence.
- `Memory Reflection`: `scripts/codex_subconscious.py reflect` merges duplicate routine/derived JSONL records and prunes only expired routine/derived records; decision and unknown records remain unchanged.
- `Skills`: `codex/skills/*` is the source copied into runtime `~/.codex/skills/*`.
- `Runtime Publication`: any commit that touches a `codex/` runtime surface is complete only after an operator-present push to `origin/main`; automation must not perform that push, and an unpushed source commit is not evidence of live runtime activation.
- `Session State`: `docs/harness-state.md` records durable phase and handoff facts.
- `Task Ledger`: `scripts/harness_ledger.py` creates and verifies tamper-evident acceptance ledgers from validated requirements.
- `Transition Store`: `scripts/harness_transition.py` provides append-only first-record-wins CAS semantics for successor task ids.
- `Behavior Evaluator`: `scripts/harness_eval.py tier1` executes fixture-driven recovery and handoff-lint end-state assertions from `docs/evals/`.
- `Permissions`: `codex/runtime/tool-policy.json` declares stage-level tool permissions and low/medium/high risk annotations for every guard category; unknown phases fall back to read-only, and blocked categories have no approval bypass.
- `Hooks`: `codex/hooks/*` implements thin objective guardrails, prompt model routing recommendations, and evidence plumbing.
- `Observability`: local JSONL evidence records lifecycle and verification events.
- `Surface Inventory`: `docs/surfaces.json` is the canonical runtime surface inventory; `scripts/check_surfaces.py` keeps it consistent with files on disk, the `docs/repo-index.md` `## Runtime Surfaces` mirror, and opt-in public landing nav links declared with `public_nav`.
- `Tool Router`: lifecycle stage determines allowed read/write/network/remote behavior. The guard resolves phase in order from the host-owned top-level payload, `CODEX_HARNESS_PHASE`, the transcript marker, one unambiguous repo snapshot, then `unknown`. The marker precedes the snapshot because a task-scoped owner declaration is narrower than repo-scoped state. `tool_input.phase`, `tool_input.cwd`, `tool_input.transcript_path`, and `tool_input.session_id` never participate in authorization. Repository lookup uses only the host-owned top-level `cwd` (or the hook process cwd when absent), while tool-input paths remain classification and logging inputs only.
- `Model Router`: `codex/hooks/model_router.py` classifies each prompt or subtask as `simple`, `medium`, or `complex` and recommends the cheapest quality-safe model tier. It intentionally stays non-blocking; runtimes or wrapper scripts that can switch models may consume the JSON `routing` object, while plain Codex hooks inject the recommendation and response telemetry requirement as additional context.
- `Checkpoints`: use git commits, state log entries, and handoff docs as recovery points.
- `Guardrails`: recognized repo-write phase violations, destructive commands, sensitive paths, credential-shaped command literals, remote operations, and dynamic-execution actions are blocked. The guard emits the Codex-supported legacy block shape; a 2026-07-28 isolated probe proved that the former top-level `permissionDecision` shape and every `ask` variant fail open, so there is no approval channel.

The 2026-08-02 landed-guard isolation rerun confirmed that the legacy block
shape prevents execution for repo-write, dynamic-execution, remote,
destructive, agent-dispatch, network, and unknown-phase cases. Path and command
classification are now intentionally separate: path patterns do not scan
command text, and command patterns recognize credential-shaped literals rather
than ordinary naming vocabulary.

### Task-scoped transcript marker

An owner may declare the task phase by placing one independent marker line as
the first non-empty line of the task's first real owner instruction:

```text
task-mode: development
```

`任务模式：development` is the equivalent Chinese form. Matching is
case-insensitive and closed to this vocabulary:

- `planning` or `plan`: read-only planning.
- `development` or `implementation`: scoped repository implementation.
- `review`: read-only review.
- `validation`: validation without a general repository-write grant.
- `handoff`: handoff, with category-level repository writes still blocked.
- `report-only`: alias of `review`.
- `ship`: explicitly not declarable; ship combines repository write and network
  authority and therefore requires a separate owner-controlled path.

Only the earliest real owner instruction is considered, so a task cannot change
mode midway. Start a new task to change mode. A marker mentioned later in the
message, in a later message, or inside pasted documentation does not trigger.
For attachment-wrapped prompts beginning with `# Files mentioned by the user:`,
the parser requires `## My request for Codex:` and evaluates its first non-empty
request line. Injected recommended-plugin, AGENTS, environment, and skill blocks
are skipped because they lack the host's following `user_message` event.
`automation` and unknown thread sources are ineligible even if their preset
prompt starts with a valid marker.

`codex/hooks/task_state.py` is a read-only parser: it creates no task-state
file, cache, or audit record. It accepts only top-level `transcript_path` and
`session_id`, resolves the path, and requires it to remain under
`<CODEX_HOME>/sessions/`; symlink escapes fail closed. It reads at most the first
50 transcript lines. Missing, truncated, malformed, identity-mismatched, or
out-of-bounds transcripts yield no marker phase and a fail-closed reason code;
the guard then continues to the repo snapshot and `unknown` sources in the
documented precedence chain.

Session metadata has two distinct identities. `session_meta.payload.id` is the
current thread's globally unique id and equals the UUID suffix in that thread's
rollout filename. `session_meta.payload.session_id` is the session-root thread
id; every descendant retains that same root id regardless of nesting depth.
The top-level PreToolUse `session_id` has the latter session-root meaning. The
current transcript is associated only when that top-level value equals either
its own `meta.id` (the root-transcript case) or its `meta.session_id` (the
descendant-transcript case).

Subagents do not declare their own marker. Every thread in a session tree,
including depth 2 and deeper descendants, resolves directly to and shares the
owner root's declared phase without mapping, decay, or elevation. If the
current transcript's `meta.id` is not the root `session_id`, the parser narrows
the root candidate by the fixed rollout filename suffix
`rollout-*-<session_id>.jsonl` under the `YYYY/MM/DD` session layout. It then
opens the candidate and requires its internal `meta.id` to equal the requested
root id; the filename alone is never trusted. Exactly one root must be found,
that root must have `thread_source=user`, and its cwd Git root must equal the
top-level current payload cwd Git root. Automation roots, missing roots,
ambiguous roots, identity mismatches, and cross-repository reuse all fail
closed to `unknown`/read-only.

Direct-parent ids, depth fields, and agent-controlled
`<codex_delegation><source_thread_id>` text are not read for authorization.
Marker-like text in a subagent body is ignored; only the real owner instruction
in the root transcript can declare the shared session-tree phase. If a restored
long-lived session's root transcript is unavailable, its descendants remain
read-only and the owner must start or redeclare through an eligible root task;
the child cannot self-declare.

This is a defense-in-depth task-scoping mechanism, not a hard security boundary.
Transcript files have mode `600`, but the agent and hook execute under the same
uid, so the agent can technically write those files. The path fence, host-shaped
identity checks, owner-message predicate, and task-scoped declaration
significantly raise the cost of accidental misuse and deliberate abuse compared
with globally polluted environment state or a forgeable cwd; they do not make
the transcript unforgeable. A true hard boundary requires either a trusted
payload-level phase supplied by the host or a hook running under a different
uid. Neither capability is implemented in this slice.

Snapshot phase resolution checks exactly two repo-relative candidates:
`docs/harness-state.md` and `docs/designs/harness-state.md`. Exactly one may be
present. The candidate must be a regular non-symlink file with exactly one
`## Current Snapshot` section and exactly one explicit `Phase` field inside
that section; the field name is case-insensitive, while its value must directly
match a phase key in `codex/runtime/tool-policy.json`. `Lifecycle stage`, titles,
directory names, and fields outside the current snapshot are never inferred as
phase. Multiple candidates, duplicate in-section fields, missing or invalid
fields, symlinks, and read errors all resolve to `unknown`. Historical `phase`
entries under `## State Log` do not participate in duplicate detection.

The resolved phase is task-scoped through the host cwd, not target-path scoped:
a command that names another repository in its tool input does not make that
repository's snapshot authoritative. Cross-repository target enforcement is a
separate design concern and is not supplied by this parser hardening.

R6 adds risk tiers as evidence-only annotations. Block responses keep the exact
legacy `decision`/`reason` key set and append `risk_tier=<tier>` inside the
reason. A first 2026-08-02 pre-commit probe proved that adding a top-level
`risk_tier` field invalidates the host response and lets a planning write run;
that shape was rejected. The corrected reason-only shape then matched all 18
W6b reference rounds: every hook ran once, G0/G4 retained their known allowed
outcomes, and G1/G2/G3/G5/G6/G7/G8 remained blocked. Risk tiers do not change
block/allow behavior.

## Session Bearing

`codex/hooks/session_bearing.py` is registered in the source `SessionStart`
chain. W6a deployed the approved snapshot on 2026-08-02, but a fresh
2026-08-03 comparison finds the current runtime copy missing; therefore this
section describes source behavior, not current activation. For a cwd inside
this repo the source hook runs
`scripts/harness_recover.py --boundary --json` and injects `phase`,
`next_safe_task`, `boundary_verdict`, and `dirty_status`. The hook shares one
180ms deadline across the boundary call and its compatibility fallback; only an
explicitly unsupported `--boundary` argument triggers plain recovery, which
reports `boundary_verdict=unknown`. Missing repo helpers, malformed results,
timeouts, and other failures exit zero without output so session start remains
unaffected. Restore of runtime parity requires a new, explicit sync action.

## Compaction Observation

`codex/hooks/compaction_counter.py` is the single decoded-event classifier for
top-level `type=compacted` events. The codex-fluent active-session scanner uses
it without changing report output; the prompt-time probe will consume the same
function after W2b lands.

W2 Phase-0 captured one real Codex CLI 0.144.1 `UserPromptSubmit` payload shape
in an isolated Codex home before any probe implementation existed. The logger
retained keys and presence flags only, never prompt or identifier values.

- command: `bash /tmp/run_mce_phase0_user_prompt_probe.sh`
- exit_code: 0
- key_output: `session_or_thread_id_present=true path=session_id; usage_or_token_fields_present=false; cwd_present=true path=cwd`
- timestamp: `2026-08-02T22:16:30-04:00`

Therefore W2b may resolve the observed payload by its top-level `session_id`,
while retaining the strict three-condition heuristic for payloads without it.
Because no usage/token field was observed, R4 must use only the host-observed
compaction ordinal as its pressure signal and must not synthesize capacity.

R4 records that degradation as decision evidence before meter code exists:

- command: `python3 scripts/harness_evidence.py append ... --metadata '{"usage_or_token_fields_present":false,"degradation":"ordinal-only"}'`
- exit_code: 0
- key_output: `evidence_kind=decision; degradation=ordinal-only; token_usage=unknown; remaining_capacity=unknown; validation=valid`
- timestamp: `2026-08-02T22:58:31-04:00`
- isolated evidence file: `/tmp/mce-r4-evidence.aUpBFW/harness/evidence/2026-08-02.jsonl`

W2b implements that source-stage probe in `codex/hooks/compaction_probe.py` and
registers it in the source `UserPromptSubmit` chain. W6a deployed the approved
snapshot on 2026-08-02; the current 2026-08-03 runtime comparison finds this
hook missing, so it must not be described as runtime-active. Resolution
prefers an exact session id. Without an id it injects only when the payload cwd
matches session metadata, the file mtime is inside the configured window, and
exactly one candidate remains; otherwise it returns continue-only and records
routine `probe_inconclusive` evidence.

The per-session cache is `~/.codex/harness/probe_state.json`, keyed by canonical
session-file path. Missing/corrupt state, a missing entry, file replacement, or
file shrink permits one full scan and rebuild. Stable rounds seek to the cached
complete-line offset and read only appended bytes. Partial trailing lines remain
unconsumed until completed. Every successful match injects
`compaction_ordinal=N (host-observed)` plus an explicit ordinal-only pressure
label and `token_usage=unknown; remaining_capacity=unknown`; exceptions and
budget overruns are silent. `codex/hooks/context_meter.py` consumes the frozen
W2a capability conclusion. With the source conclusion set to false it never
persists `~/.codex/harness/meter.json`. Its separately tested usage-capable path
persists only observed integer fields and derives remaining capacity only when
both total tokens and context window are present; missing values remain
`unknown`.

## Evidence Contract
Evidence events are JSON objects that match `codex/runtime/evidence.schema.json`.
That file remains the compatibility entrypoint. Focused schemas live under
`codex/runtime/evidence/`:
- `decision-evidence.schema.json`
- `routine-gate-receipt.schema.json`

Runtime events are written to local files under `~/.codex/harness/evidence`.
Local logs are not migrated when the schema evolves. Old events that do not
carry `evidence_kind` are read as `unknown`.

The source observer minimizes new tool-call evidence by default. It omits the
raw command and records only `command_present`, `command_length`, and the first
12 hexadecimal characters of its SHA-256 digest. `key_output` remains capped at
500 characters and adds its original length and the same digest prefix. Setting
`CODEX_HARNESS_EVIDENCE_RAW=1` is the only raw-debug opt-in; those events carry
`raw_capture=true` and retain at most a 200-character `command_head`.

Each serialized observer record is capped at 8 KiB and marks source or record
truncation with `truncated=true`. Files keep daily names and rotate at 32 MiB to
`<date>.<seq>.jsonl`. The evidence directory and files are enforced as
owner-only (`0700` and `0600`). Evidence has a minimum 30-day retention window:
rotation never deletes files, and any separately authorized cleanup must not
remove a file still inside that window.

Decision evidence may add the optional `compaction_ordinal`, `transition_key`,
and `gate_decision` fields. They are accepted only for decision evidence;
existing events and append calls remain valid without them.

Evidence kinds:
- `decision`: state, handoff, approvals, guardrails, sandbox failures, agent-team
  validation receipts, and durable recovery decisions.
- `routine`: test receipts, browser smoke, startup probes, ordinary tool calls,
  and non-decision subagent reports.
- `unknown`: legacy read-only normalization for old local JSONL events; new
  appends must use or infer `decision` or `routine`.

Required verification evidence fields:
- `command`
- `exit_code`
- `key_output`
- `timestamp`

Evidence helper behavior:
- malformed event: fail non-zero and do not write.
- missing required verification fields: fail non-zero and do not write.
- partial write risk: validate before append.
- observer hook failure: warn and continue so observability does not block normal work.
- report view: `scripts/harness_report.py` summarizes local JSONL evidence with
  `--cwd`, `--since`, `--phase`, `--event-type`, `--evidence-kind`, `--limit`,
  and `--json`.
- conversion health: `scripts/harness_feedback.py` computes a local advisory
  `conversion_health` signal from already-filtered evidence events; report and
  recover outputs include status, reason, productive event counts, repeated
  command counts, and low-conversion signals.

- stalled conversion health is advisory for planning and recovery, not an
  automatic failure gate.
- empty evidence: report exits 0 with an explicit empty summary.
- malformed JSONL lines: report continues, increments `malformed_count`, and
  lists file and line.
- state logs should promote compact decision evidence summaries instead of
  copying every routine gate receipt into handoff state.

Memory reflection is fail-closed and atomic. A malformed JSONL record, missing
timestamp on a routine/derived record, or invalid timezone prevents every
rewrite. Duplicate detection ignores only record identity and timestamp fields,
keeps the newest routine/derived copy, and never deduplicates or expires a
decision-kind record.

## Runtime Plan Governor Contract

Runtime Plan Governor v1 is a local stdlib CLI at `scripts/plan_governor.py`.
It freezes a bounded scope envelope, evaluates structured findings, records
complexity drift, and emits time-bound receipts. Its three managed schemas are:

- `codex/runtime/evidence/plan-scope-envelope.schema.json`
- `codex/runtime/evidence/plan-finding-decision.schema.json`
- `codex/runtime/evidence/plan-governor-receipt.schema.json`

The CLI exposes only `freeze`, `evaluate-round`, `status`, and
`verify-receipt`. State lives under
`~/.codex/harness/plan-governor/<session-binding>/state.json`, uses owner-only
permissions and atomic replacement, and stores only hashes, enums, counters,
and bounded reason codes. Governor decisions reuse
`event_type=guardrail_decision`; no evidence event type or taxonomy is added.

Phase 0 on 2026-07-26 established `payload_capable=false`. A real Bash dispatch
probe exposed `session_id`, `cwd`, tool name, and the exact command marker, and
an enforceable `deny` was demonstrated after emitting the current Codex wire
shape. However, both the desktop session and an independent
`approval_policy=on-request` CLI session executed a command after the hook
returned `permissionDecision=ask`. The current official Codex implementation
also classifies that decision as unsupported and fails open. Because Ask is a
required response capability, the managed source fixes
`plan_governor.mode=shadow` and
`production_status=no_go`. Phase 2 hook integration, Ask/Enforce behavior, and
runtime activation are not implemented in this branch. Shadow classification
and evidence never alter an existing tool result.

`source_implemented`, `rollout_observed`, and `runtime_active` are independent
milestones. Source tests or temporary-home evidence do not imply either rollout
observation or runtime activation.

## DHF Packet Contract
`codex/runtime/dhf-packet.schema.json` is the incubation contract for future DHF
extraction. It defines the smallest portable packet a consumer can exchange
without inheriting all of `MyCodexEnv`.

The packet carries phase, execution lane, state path, source-of-truth files,
verification evidence, next safe task, blockers, and consumer adapter metadata.
It explicitly excludes secrets, raw local evidence, customer data, and
machine-specific auth paths. First-stage incubation validates the schema and
examples only; helpers may add `--emit-dhf-packet` later without changing the
current runtime path.

## Recovery Contract
Fresh sessions should be able to recover the next safe task without chat
history. `scripts/harness_recover.py` reads repo index, harness state, git
status/log, and local evidence summary.

Recovery behavior:
- missing repo index or harness state: fail non-zero and print the missing path.
- no matching local evidence: exit 0 with `evidence_status=empty`.
- dirty repo: report `dirty_status=dirty` and `dirty_count`.
- evidence kind summary: JSON and markdown output include counts for
  `decision`, `routine`, and `unknown` evidence matching the repo cwd.
- latest decision evidence: JSON and markdown output include a compact
  `latest_decision_evidence` summary so routine receipts do not bury durable
  handoff and guardrail decisions.
- conversion health: JSON and markdown output include the advisory
  `conversion_health` status and reason for matching local evidence.
- boundary check: `--boundary` adds `boundary_verdict` and `boundary_reason`.
  `safe` requires a clean worktree plus a zero-exit verification whose timestamp
  is no older than the latest commit and no older than
  `--max-verification-age` (24 hours by default). A dirty worktree or failed
  verification is `unsafe`; unavailable, invalid, future, stale, or pre-commit
  timestamps are `unknown` and callers must treat them as unsafe.
- task demand: recovery scans `docs/plans/**/*.md` by modification time and
  exposes `task_demand.estimated_level` and `task_demand.S_state` from the latest
  artifact that passes `harness_requirements.py`; newer invalid artifacts are
  skipped, and no validated artifact yields `unknown` for both fields. Recovery
  only transports these values and applies no policy to them.
- JSON output: use `--json` for automation and visual reports.

## Environment Probe Contract
`scripts/harness_env_probe.py` reports what the repo can observe about the local
Codex runtime: config, hooks, tool policy, compatibility evidence schema, split
evidence schemas, sandbox fields, and approval fields.

Probe behavior:
- missing required runtime files: fail non-zero and name each missing file.
- split evidence schemas must exist at
  `runtime/evidence/decision-evidence.schema.json` and
  `runtime/evidence/routine-gate-receipt.schema.json`.
- sandbox fields absent from config: do not infer; report `observable=false`.
- global Desktop sandbox is outside repo control; the probe reports observable
  config only.

## Model Routing Contract
`codex/hooks/model_router.py` is the pre-task prompt router. It reads hook JSON
from stdin and exits 0 in all normal cases so routing cannot block task intake.

Routing behavior:
- missing or malformed prompt: recommend balanced fallback `gpt-5.4` with low
  confidence;
- very short harmless prompts: recommend `gpt-5.4-mini` with low reasoning;
- simple formatting, translation, README, and documentation subtasks: recommend
  `gpt-5.4-mini` with low reasoning;
- ordinary implementation, tests, scripts, and refactors: recommend `gpt-5.4`
  with medium reasoning;
- architecture, auth, security, migrations, deploys, destructive operations, or
  long cross-module tasks: recommend `gpt-5.5` with high reasoning;
- review phase: recommend `gpt-5.5` with high reasoning;
- validation phase without high-risk signals: recommend `gpt-5.4-mini` with low
  reasoning for evidence collection and summarization;
- when `subtask` is present, classify the subtask instead of anchoring on the
  parent prompt, allowing complex tasks to downshift for cheap subtasks and
  upgrade again for planning, security, review, or release steps.

The hook output includes `routing.switch_points` for complex prompts so an
orchestrator can re-run or apply routing at research, planning, development,
validation, and review boundaries. The hook does not claim to force a model
change in Codex versions that only accept additional prompt context.

Response telemetry behavior:
- output includes `telemetry.models_used`, `telemetry.token_usage`, and
  `telemetry.five_hour_limit`;
- actual model names are read from payload fields such as `model`,
  `current_model`, `selected_model`, or `active_model`, then combined with the
  routed recommendation;
- token usage is read from payload `usage` / `token_usage` fields such as
  `input_tokens`, `output_tokens`, and `total_tokens`;
- five-hour limit data is read from payload `limits` / `quota` / `rate_limit`
  fields or from `CODEX_5H_LIMIT_REMAINING` and `CODEX_5H_LIMIT_RESET_AT`;
- unavailable telemetry must be reported as `unavailable`; the hook and final
  response instructions must not estimate or invent token usage or limits.

## Checkpoint Contract
Create a checkpoint only when a matching `governed` escalation signal requires
one: resume/handoff, ownership conflict, external capture/private data,
destructive or remote/deployment/release action, multi-agent execution,
architecture source conflict, or malformed/retained governed state. A validated
`light` or `standard` slice does not checkpoint by default.

A checkpoint must record:
- phase;
- files or surfaces changed;
- validation evidence;
- blockers;
- next safe task;
- whether a git commit exists.

Checkpoint helper:
- `scripts/harness_checkpoint.py append` updates `docs/harness-state.md` and
  appends a checkpoint entry.
- it records git branch, latest commit, dirty status, changed surfaces, blockers,
  latest verification, and next safe task.
- when explicitly supplied, `--compaction-ordinal`, `--transition-key`, and
  `--gate-decision` add the transition decision to both the current snapshot and
  appended checkpoint; old invocations continue to omit these fields.
- it does not create git commits or push changes.
- missing verification fields fail non-zero before writing.
- `--allow-unverified` is only valid for `handoff` checkpoints with an explicit
  blocker.

## Subagent Contract
Each delegated agent must receive:
- role: planner, worker, reviewer, security, or qa;
- scope: exact task and owned files or modules;
- write set: empty for read-only roles, disjoint for workers, and no protected
  integrator state surfaces such as `docs/harness-state.md`;
- verification command;
- report schema: changes, evidence, blockers, and risks.

Worker agents may also receive a durable brief using
`docs/templates/harness-agent-brief.md`. A brief records category, summary,
current behavior, desired behavior, key interfaces, acceptance criteria, and out
of scope. Use behavior and interfaces as the task contract; line numbers and
file-path-only instructions are not durable enough.

Worker JSON plans must include `task_demand` and `green_gate` objects:
- `task_demand`: `level` (`low`, `medium`, or `high`), `L`, `H_tool`,
  `S_state`, and `N_obs`.
- `green_gate`: `gate_scope` (`worker` or `integrator`), `command`, and
  `rationale`.
- medium and high demand require `focused_gate_command`.
- high demand also requires `full_gate_command` and `new_probe`.
- when `gate_scope=worker`, `verification_command` must match
  `green_gate.command`.
- when `gate_scope=integrator`, `integrator_gate_command` must match
  `verification_command`.

Read-only roles must not carry `task_demand` or `green_gate`; demand gates are
for scoped workers only. Demand gates do not replace disjoint write-set checks
or the required `verification_command`.

Default permissions:
- planner: read-only;
- worker: scoped writes only;
- reviewer/security/qa: read-only;
- main agent: integration, final judgment, and verified checkpoint updates.

Overlapping worker write sets block dispatch until the task is split again.
Delegated workers must not claim `docs/harness-state.md`, or a parent path such
as `docs/`, in their write set. Worker handoff belongs in a slice-local artifact
or report; the main agent appends the consolidated harness checkpoint after
integration and fresh verification. Single-line tasks executed directly by the
main agent are not worker plans and may still use `scripts/harness_checkpoint.py
append` after the usual verification gate.

Agent team validator:
- `scripts/harness_agent_team.py validate PLAN.json` validates `agents[]`.
- `scripts/harness_agent_team.py validate PLAN.json --emit-evidence` also appends
  one local `agent_team_validated` decision receipt on success, with
  `metadata.plan_sha256`, `agent_count`, `worker_count`, and `repo_root`.
- every agent requires `id`, `role`, `scope`, `write_set`, and
  `verification_command`.
- optional worker `brief` objects are validated when present and are backward
  compatible when omitted.
- worker roles require `task_demand` and `green_gate`; the gate must match the
  declared demand level.
- read-only roles reject `task_demand` and `green_gate`.
- planner, reviewer, security, and qa roles must have an empty `write_set`.
- worker roles must have a non-empty `write_set` and verification command.
- worker write sets are normalized to repo-relative paths and must be disjoint.
- worker write sets must not overlap protected integrator state surfaces,
  currently `docs/harness-state.md`.
- empty paths, `..` traversal, and absolute paths outside the repo fail.
- configured dispatch tool names and command patterns are block-gated by
  `codex/hooks/harness_guard.py` (legacy `{"decision":"block"}` shape).
  `requirements` and `handoff` block dispatch before receipt evaluation; other
  phases require `plan_sha256` and a matching local receipt less than 10 minutes
  old.
- this is an honest configured-shape gate: runtime dispatch paths not exposed to
  `PreToolUse` or not named in `tool-policy.json` cannot be intercepted by this
  repo hook.

## Failure Modes
- missing state file: fail or warn at startup, then read repo AGENTS and README before acting.
- unknown lifecycle stage: default to restrictive read-only behavior.
- missing, malformed, duplicated, unreadable, symlinked, or multiply located `## Current Snapshot` phase: treat the phase as unknown and block repo writes under the read-only fallback.
- sensitive path access or a credential-shaped literal in command text: hard block; file content is outside this classifier's input boundary.
- remote operation: require `~/.codex/remote-access.md` review and approval.
- dynamic download execution: hard block.
- evidence write failure in observer hook: print a warning and allow the original tool result.
- missing, stale, cross-repo, worker-count-mismatched, or malformed agent-team
  validation receipt: block configured multi-agent dispatch until a fresh
  receipt exists (ask is unsupported by the host and fails open).
