# DHF Independent Core Requirements

Date: 2026-08-01  
Originating evaluation: `docs/plans/2026-06-15-dhf-independent-project-evaluation.md`  
Consumer role: `MyCodexEnv` remains the pinned reference consumer and integration test bed.

## Goal

Define the bounded, testable contract for extracting the generic Delivery Harness Framework core into one independent public repository without creating a second source of truth. The future `delivery-harness-framework` repository owns generic core releases; `MyCodexEnv` owns installation, local runtime wiring, a version pin, and consumer integration tests.

## Audience

- Maintainers preparing the independent DHF repository.
- MyCodexEnv maintainers reviewing a DHF release pin-bump.
- Consumer-repo owners implementing project-specific adapters.

## Scope

- Specify exact initial copy, adaptation, and exclusion sets.
- Specify the source-checkout installer and consumer-side doctor contracts.
- Specify the portable packet validator and MyCodexEnv snapshot comparator.
- Specify the bootstrap pin manifest and its transition to release pins.
- Define CI, pin-bump, privacy, and rollback gates before any public repository is created.

### Exact copy set

The first independent checkout copies these contents byte-for-byte, with only the destination path changing. Their initial SHA-256 values become the release manifest values.

| MyCodexEnv source | Independent DHF destination |
| --- | --- |
| `codex/runtime/dhf-packet.schema.json` | `schemas/dhf-packet.schema.json` |
| `codex/runtime/evidence.schema.json` | `schemas/evidence.schema.json` |
| `codex/runtime/evidence/decision-evidence.schema.json` | `schemas/evidence/decision-evidence.schema.json` |
| `codex/runtime/evidence/routine-gate-receipt.schema.json` | `schemas/evidence/routine-gate-receipt.schema.json` |
| `codex/skills/delivery-harness-framework/evals/evals.json` | `skills/delivery-harness-framework/evals/evals.json` |
| `scripts/harness_evidence.py` | `scripts/harness_evidence.py` |
| `scripts/harness_requirements.py` | `scripts/harness_requirements.py` |
| `scripts/validate_dhf_packet.py` | `scripts/validate_dhf_packet.py` |
| `docs/templates/harness-requirements.md` | `templates/harness-requirements.md` |
| `docs/templates/harness-agent-brief.md` | `templates/harness-agent-brief.md` |

### Adapt set

These are inputs, not byte-for-byte shared source. Adaptations must remove MyCodexEnv paths and expose configurable repo-local interfaces. Adapted files are owned only by the independent core after extraction and are not entered as exact-hash rows in the MyCodexEnv pin.

| MyCodexEnv input | Independent DHF destination and required adaptation |
| --- | --- |
| `docs/HARNESS_RUNTIME.md` | `docs/runtime-contract.md`; remove home-sync and machine claims. |
| `docs/LIFECYCLE_SKILL_ROUTING.md` | `docs/lifecycle-skill-routing.md`; make specialist skills extension points. |
| `docs/repo-index.md` | `templates/repo-index.md`; retain the compact-navigation pattern only. |
| `docs/surfaces.json` and `scripts/check_surfaces.py` | Core-owned manifest/checker covering only independent-repo surfaces. |
| `codex/skills/delivery-harness-framework/SKILL.md` | `skills/delivery-harness-framework/SKILL.md`; remove MyCodexEnv helper paths. |
| `codex/runtime/tool-policy.json` | `runtime/tool-policy.json`; keep generic phase policy and configurable tool names. |
| `codex/hooks/harness_guard.py`, `harness_observer.py`, `model_router.py` | `hooks/`; make runtime host and evidence destinations injectable. |
| `scripts/harness_recover.py`, `harness_env_probe.py`, `harness_feedback.py`, `harness_report.py`, `harness_agent_team.py`, `harness_checkpoint.py` | `scripts/`; remove Codex-home requirements and accept repo-local configuration. |
| `test_runner.py` | New core-only `test_runner.py`; move generic behavior tests, never copy MyCodexEnv sync tests. |

### Exclude set

The independent core must not copy or publish:

- `docs/harness-state.md`, `docs/handoffs/`, `tasks/`, active task prompts, transcripts, or local evidence logs;
- credentials, authentication files, tokens, customer data, private service names, or machine-specific paths;
- `scripts/sync_codex_home.sh`, `scripts/verify_codex_env.sh`, `bootstrap.sh`, or Codex/Claude home reproduction logic;
- `codex/AGENTS.md`, `codex/remote-access.md`, `codex/remote-hosts.md`, personal policy, or host inventory;
- `codex/skills/gstack/`, vendor-refresh automation, or unrelated skills;
- ShipQ paths, fixtures, quote/workbook/demo rules, live-provider gates, or any other repo-specific adapter.

## Non-Goals

- Do not create a GitHub repository, release, tag, commit, push, or runtime sync in this prerequisite slice.
- Do not make MyCodexEnv and the independent repository co-own generic core source.
- Do not migrate ShipQ or modify any consumer repository.
- Do not implement a package-registry distribution path, Windows support, hosted service, or production SLA in Phase 1.
- Do not claim a bootstrap snapshot is a published release.

## Constraints

- Python 3.10+ standard library only for the Phase 1 validator, comparator, installer, and doctor.
- All paths in manifests must be normalized relative POSIX paths; absolute paths, `..`, duplicate mappings, and symlink escapes fail closed.
- Validation and comparison are read-only. They must not rewrite packets, source checkouts, consumers, or manifests.
- Invalid input must return non-zero, name the invalid field/path, and avoid printing field values that may contain sensitive material.
- `MyCodexEnv` retains install/sync/runtime wiring and consumes one immutable DHF tag plus Git revision after the first release.
- A bootstrap pin may carry `release: null` and `source_revision: null`; it is a pre-release content baseline, not evidence that an upstream repository exists.
- Release pins must use `dhf-core-vYYYY.MM.DD.N`, include a 40-character lowercase Git revision, and update only through a reviewed pin-bump.

## Task Demand (D_task)

- estimated_level: high
- L (reasoning/action steps): Coordinate extraction boundaries, portable contracts, validators, content hashes, CI, and rollback across two repositories.
- H_tool (tool-selection ambiguity): Prefer deterministic standard-library CLIs; repository creation and remote tooling remain explicitly out of scope.
- S_state (cross-module state tracking): Preserve one upstream source of truth while tracking an immutable release pin and MyCodexEnv consumer parity.
- N_obs (observation/external noise): A future remote tag and checkout require fresh evidence; current local bootstrap artifacts cannot prove publication or runtime activation.

## Source Of Truth

- `docs/plans/2026-06-15-dhf-independent-project-evaluation.md`
- `docs/plans/2026-06-15-dhf-incubation-plan.md`
- `codex/runtime/dhf-packet.schema.json`
- `docs/dhf-consumer-compatibility.json`
- `docs/dhf-core-pin.json`
- Future independent repository release tag and release manifest, once they exist.

Ownership is intentionally asymmetric:

1. Independent DHF owns generic core source, schemas, portable helpers, release tags, and migration notes.
2. MyCodexEnv owns bootstrap/install/sync wiring, the pin manifest, consumer integration tests, and local runtime verification.
3. Project repositories own their adapters, durable state paths, business gates, and data handling rules.

## Acceptance Criteria

- [ ] The exact copy, adapt, and exclude sets above survive security and engineering review before repository creation.
- [ ] `scripts/validate_dhf_packet.py` accepts the checked schema example and rejects missing, extra, mistyped, invalid-enum, and malformed fields with non-zero exit and field paths.
- [ ] `scripts/compare_dhf_core_snapshot.py` reports `match` with exit 0, hash `drift` with exit 1, and malformed manifests, unsafe paths, missing roots/files, or I/O failure with fail-close exit 2.
- [ ] `docs/dhf-core-pin.json` is a non-empty bootstrap snapshot whose hashes match the exact-copy files currently held by MyCodexEnv; it contains no invented release or upstream revision.
- [ ] The first upstream release converts the bootstrap pin to `kind: release`, an immutable DHF tag, and its exact Git revision in the same reviewed pin-bump PR.
- [ ] MyCodexEnv remains a pinned reference consumer; it does not become a mirror that can overwrite upstream generic core.
- [ ] Repo-specific adapters and all private/local evidence remain outside the public core.
- [ ] Dedicated tests cover packet valid/invalid input and comparator match/drift/fail-close behavior.

### Source-checkout installer contract

The future `scripts/dhf_install.py` accepts `--source`, `--target`, `--profile minimal`, and `--no-overwrite`. It must:

1. Resolve both roots, reject target paths outside the consumer, and read the source release manifest.
2. Verify every selected source file against the immutable release digest before writing.
3. Stage managed files in a temporary directory on the same filesystem, then atomically place them under `.dhf/`.
4. Create `.dhf/manifest.json` with release, revision, profile, file paths, and hashes.
5. Create `docs/repo-index.md` and `docs/harness-state.md` only when absent; never claim unmanaged existing files.
6. Refuse unknown overwrites, leave existing files unchanged, and emit `.dhf/install-report.md` describing conflicts and the verification command.
7. Never copy credentials, evidence logs, handoffs, customer fixtures, remote configuration, or MyCodexEnv sync logic.

The installer is idempotent for the same verified source and profile. Upgrade behavior is a separate explicit command or later phase; install must not silently advance a pin.

### Consumer-side doctor contract

The future `.dhf/scripts/dhf_doctor.py --repo-root PATH [--json]` is read-only and must verify:

- `.dhf/manifest.json` structure, release/tag/revision syntax, and managed-file hashes;
- required schema/helper presence and packet-schema compatibility;
- repo-local state and navigation files exist without requiring Codex or Claude authentication;
- modified, missing, unexpected, or unsafe managed paths are individually reported;
- output includes `dhf_consumer_ok`, `managed_files_ok`, release, revision, counts, and a bounded remediation command.

Doctor returns 0 only when all selected-profile files match. It must never repair or upgrade files automatically.

### Packet validator contract

`scripts/validate_dhf_packet.py PACKET [--schema PATH] [--json]` uses the portable packet schema, returns `dhf packet valid`/`status=valid` on success, and returns exit 1 for invalid packet content. Schema loading, unsupported schema keywords, or schema I/O failures return exit 2. Output identifies JSON paths but never echoes rejected values.

### Snapshot and pin-bump contract

`scripts/compare_dhf_core_snapshot.py --source UPSTREAM --consumer MYCODEXENV --manifest docs/dhf-core-pin.json [--json]` hashes both sides against the pin. It is not a sync tool. Missing files are fail-close errors rather than ordinary drift because parity cannot be established.

For each upstream release:

1. Fetch or check out the exact reviewed tag outside this prerequisite task.
2. Confirm the tag resolves to the manifest revision and verify release digests.
3. Run the comparator before changing MyCodexEnv; expected old-pin result is match or explicit reviewed drift.
4. Update consumer exact-copy files and `docs/dhf-core-pin.json` in one pin-bump PR.
5. Run comparator, dedicated prerequisite tests, MyCodexEnv tests, surfaces check, environment verification when runtime wiring changed, and `git diff --check`.
6. Merge only when the new pin is immutable and all consumer gates pass. No automatic runtime sync follows from merge.

## Verification Gate

- `python3 scripts/harness_requirements.py validate docs/plans/2026-06-15-dhf-independent-core-requirements.md`
- `python3 -m unittest tests/test_dhf_independent_core_prerequisites.py`
- `python3 scripts/validate_dhf_packet.py <valid-packet-path> --json`
- `python3 scripts/compare_dhf_core_snapshot.py --source <independent-checkout> --consumer "$(pwd)" --manifest docs/dhf-core-pin.json --json`
- `python3 test_runner.py`
- `python3 scripts/check_surfaces.py --repo-root "$(pwd)"`
- `git diff --check`

The placeholder paths above are future release gates. The prerequisite slice proves the same behaviors with isolated fixtures and does not fabricate an upstream checkout.

## Risks

- A bootstrap hash may be mistaken for a published release. Control: null release/revision plus explicit `bootstrap_snapshot` kind.
- Adapted files may accidentally be treated as byte-identical shared source. Control: only exact-copy rows enter the pin.
- A comparator could become an implicit sync tool. Control: no write operation or copy option exists.
- Schema evolution may exceed the standard-library validator subset. Control: unsupported schema keywords fail closed until validator support and tests land together.
- Public extraction may expose local/private material. Control: explicit exclusion audit and reject any release containing state, evidence, handoff, auth, customer, or machine-specific surfaces.
- Two repositories may drift into dual ownership. Control: upstream release first, then a MyCodexEnv pin-bump PR; never edit generic core independently in both repositories.

## Handoff Notes

Current prerequisite state is source-only in MyCodexEnv. No independent repository, release, tag, or runtime activation is claimed. The next safe task after these artifacts validate is an independent security/engineering review of the exact copy/adapt/exclude sets. Only after that review may a separately authorized task create the public repository and publish its first immutable release. Rollback before publication is removal/revision of these prerequisite artifacts; rollback after a bad pin-bump is a new reviewed pin-bump to the last known-good immutable tag, never retagging or rewriting release history.
