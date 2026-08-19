<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="MyCodexEnv: build verified Codex and Claude environments from one Git repository">
</p>

# MyCodexEnv

**English** · [简体中文](README.zh-CN.md)

Reproduce a complete Codex and Claude workflow on a new Apple Silicon Mac with a Git clone and one bootstrap command.

This is not a loose dotfiles backup. It is a reviewable, synchronized, and verifiable control plane for agentic engineering. Repository files are the source of truth for rules, skills, hooks, runtime policy, workflows, and verification scripts. Machine-specific account and runtime state remain local.

[Quick start](#quick-start) · [How it works](#how-it-works) · [Managed contents](#managed-contents) · [Common workflows](#common-workflows) · [Documentation](#documentation) · [Verification](#verification)

## Quick start

```bash
git clone https://github.com/bryanzk/MyCodexEnv.git
cd MyCodexEnv
./bootstrap.sh
```

The bootstrap process installs or configures the declared local dependencies, synchronizes managed content into the Codex and Claude home directories, and preserves machine-specific account, session, memory, and runtime data. Sign in separately on each new machine after bootstrap.

### Requirements

- macOS on Apple Silicon
- Git
- Access to Homebrew and the required package sources
- Local Codex and Claude accounts

Available options:

```text
./bootstrap.sh \
  [--codex-home <path>] \
  [--claude-home <path>] \
  [--non-interactive]
```

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
- The source simplified route uses the exact enabled value
  `DHF_PREPROMPT_SIMPLIFIED_PROFILES=1`; the repo-source default is `simplified`
  after the second final-fix gate. Values `0`, `false`, `off`,
  and `legacy` explicitly roll back. Runtime state is evidence-dependent: the
  live boundary accepts either a source-stage unsynced state or an exact
  promoted state and rejects drift. `source_stage_unsynced` proves source
  acceptance without runtime activation; `runtime_promoted` is required before
  claiming managed runtime activation.

## Why this repository exists

Agent environments tend to spread across home directories, plugin state, prompt files, skills, hooks, and personal scripts. When moving to a new machine or debugging an environment, three questions become difficult to answer:

1. Which files are the actual source of truth?
2. Does the active runtime really match the repository?
3. Did a change break a loader, hook, policy, or another workflow?

MyCodexEnv turns those questions into a repeatable loop:

- **Reviewable source** — managed Codex and Claude configuration lives in Git.
- **Bounded synchronization** — machine-specific account and runtime state does not move with the repository.
- **Verifiable results** — tests, skill-loader checks, compatibility checks, and environment verification provide fresh evidence.

## How it works

<p align="center">
  <img src="./assets/readme/runtime-flow.svg" width="100%" alt="MyCodexEnv takes repository source through bootstrap and targeted synchronization into local Codex and Claude runtimes, then verifies the result">
</p>

1. **Source** — `codex/`, `claude/`, `docs/`, `scripts/`, and lock files define the expected state.
2. **Build and sync** — `bootstrap.sh` and targeted synchronization scripts install dependencies, copy managed files, and preserve local state.
3. **Runtime** — the local Codex and Claude homes receive runnable rules, skills, hooks, and workflows.
4. **Evidence** — `test_runner.py`, loader gates, compatibility checks, and environment verification confirm the result instead of assuming that a successful script invocation proves parity.

## Managed contents

| Surface | Repository source of truth | Local target or purpose |
| --- | --- | --- |
| Codex rules | `codex/AGENTS.md` | Local Codex rules |
| Codex config | `codex/config.template.toml` | Codex runtime configuration template |
| Hooks | `codex/hooks.json`, `codex/hooks/` | Session, prompt, policy, and evidence hooks |
| Runtime policy | `codex/runtime/` | Tool policy, schemas, and CLI resolver |
| Skills | `codex/skills/` | Local Codex skills |
| Codex workflow | `codex/workflow/` | Local Codex workflow |
| Shell integration | `codex/zsh/` | Session-title and shell helpers |
| Claude workflow | `claude/workflow/` | Local Claude workflow |
| Claude integration | `claude/CLAUDE_INTEGRATION_BLOCK.md` | Local Claude instructions block |
| Version pins | `locks/` | Reproducible third-party component versions |

### Skills

`codex/skills/*` is the repository source of truth for persistently managed skills. After synchronization, the loader gate confirms that every expected path is loaded, enabled, and free of loader errors.

The repository maintains:

- project-owned workflow skills for planning, verification, delivery harnesses, skill evaluation, and session continuity;
- the vendored `garrytan/gstack` skill collection and its shared support files;
- controlled copies of third-party skills, licenses, and runtime synchronization metadata.

After the first gstack synchronization, run the `setup` entry point inside the synchronized gstack skill directory to build its local support components.

### Harness Runtime

Harness Runtime extends agent work from “prompt plus tools” into a recoverable, observable, and verifiable delivery system:

- lifecycle and skill routing;
- phase-aware tool permissions and destructive, sensitive-data, and remote guardrails;
- prompt and subtask model recommendations;
- decision and routine evidence schemas;
- checkpoint, recovery, requirements, and agent-team validation;
- a global generic dispatcher with lazily loaded repository adapters;
- a local Runtime Plan Governor v1 CLI, three schemas, and managed-skill contracts. Phase 0 is currently `payload_capable=false`, so it supports source-stage shadow evidence only; production enforcement is not active.

Key entry points:

- [`docs/HARNESS_RUNTIME.md`](docs/HARNESS_RUNTIME.md) — workflow and infrastructure contract
- [`docs/LIFECYCLE_SKILL_ROUTING.md`](docs/LIFECYCLE_SKILL_ROUTING.md) — lifecycle-to-skill routing
- [`docs/MODEL_ROUTER_EVAL_MATRIX.md`](docs/MODEL_ROUTER_EVAL_MATRIX.md) — model-routing evaluation
- [`docs/harness-state.md`](docs/harness-state.md) — append-only state and next safe task
- [`docs/AGENT_HARNESS_STATUS.md`](docs/AGENT_HARNESS_STATUS.md) — current capability map
- [`scripts/harness_status.py`](scripts/harness_status.py) — unified read-only entry point for recovery, runtime probes, and evidence reports

### Current controls

- **Thread discipline** — every task freezes repository, mode, and compaction anchors. A confirmed anchor mismatch or second compaction can create at most one bounded successor when the project, tools, counters, and idempotency state are all safely known. A transition chain is limited to three automatic moves and never automatically archives or deletes tasks.
- **Codex Fluent** — a report-only scanner ranks active tasks by size and audits handoff readiness. Maintenance operations still require separate authorization, backups, and a recoverable handoff.
- **gbrain-aware planning** — when configured, gstack planning skills can use cached product, goal, developer-persona, brand, competitor, and user-profile context. The generic Harness remains responsible only for repository state, execution lane, and verification boundaries.
- **iOS QA bridge** — vendored gstack includes real-device and SwiftUI QA, synchronization, repair, and cleanup workflows. They remain specialist skills and do not broaden the permissions of ordinary prompts.

## Project map

```text
MyCodexEnv/
├── bootstrap.sh          # New-machine entry point
├── codex/                # Codex rules, config, hooks, runtime, skills, workflow
├── claude/               # Claude workflow and integration block
├── scripts/              # Synchronization, verification, recovery, reporting, maintenance
├── docs/                 # Architecture, guides, status, public documentation, visualizations
├── locks/                # Third-party version locks
├── tasks/                # Runtime and maintenance evidence
└── test_runner.py        # Canonical repository test suite
```

For a compact, machine-friendly index, see [`docs/repo-index.md`](docs/repo-index.md).

## Common workflows

### Synchronize the Codex runtime

```bash
./scripts/sync_codex_home.sh \
  --repo-root "$(pwd)" \
  --codex-home "<codex-home>"
```

This entry point synchronizes repository-managed Codex surfaces. For high-risk directories or a single skill, prefer an explicit targeted synchronization followed by source/runtime parity verification to avoid unrelated runtime drift.

### Verify the complete environment

```bash
python3 test_runner.py

./scripts/verify_codex_env.sh \
  --repo-root "$(pwd)" \
  --codex-home "<codex-home>" \
  --claude-home "<claude-home>"
```

If the full suite reports an explicit host-capability skip for the Codex loader
or full-sync gate, do not rerun the full suite outside the sandbox. Run only the
required host integrations with `python3 test_runner.py --host-only`; that
command fails if either test skips.

### Check skills

```bash
python3 scripts/check_skill_compatibility.py \
  --repo-root "$(pwd)"

python3 scripts/check_codex_skill_loader.py \
  --repo-root "$(pwd)" \
  --codex-home "<codex-home>"
```

The compatibility check validates manifests, helper syntax, relative links, and complete parity for persistently managed skills. The loader gate invokes the Codex app server without network access and checks loaded/enabled state and loader errors.

### Refresh vendored gstack

```bash
python3 scripts/prepare_gstack_dhf_daily_refresh.py --json
python3 scripts/sync_gstack_vendor.py \
  --repo-root "$(pwd)" \
  --source https://github.com/garrytan/gstack.git \
  --dry-run \
  --json
```

Run the actual synchronization only when the dry run returns `needs_update=true`. After synchronization, rerun the repository tests, runtime synchronization, gstack setup, and environment verification.

### Manage multi-repository AGENTS files

```bash
python3 scripts/manage_agents.py scan
python3 scripts/manage_agents.py backup --backup-id "$(date +%Y%m%d%H%M%S)"
python3 scripts/manage_agents.py generate --backup-id "<backup_id>"
python3 scripts/manage_agents.py verify
```

### Optional utilities

| Goal | Entry point |
| --- | --- |
| Record command, prompt, or conversation text | `python3 scripts/capture_text.py "text to record"` |
| Build the local Codex subconscious index | `python3 scripts/codex_subconscious.py build --emit-briefs` |
| Recover the repository's next safe task | `python3 scripts/harness_recover.py` |
| Summarize local evidence | `python3 scripts/harness_report.py` |
| Compress large command output | `some-command \| python3 scripts/headroom_filter.py --mode auto --stats` |

Runtime output from these tools remains local by default and is not committed to Git.

## Documentation

| Document | Purpose |
| --- | --- |
| [`docs/CODEX_ENV_REPRODUCTION.md`](docs/CODEX_ENV_REPRODUCTION.md) | Detailed Codex and Claude environment reproduction |
| [`docs/repo-index.md`](docs/repo-index.md) | Source-of-truth and runtime-surface index |
| [`docs/HARNESS_RUNTIME.md`](docs/HARNESS_RUNTIME.md) | Harness Runtime design contract |
| [`docs/LIFECYCLE_SKILL_ROUTING.md`](docs/LIFECYCLE_SKILL_ROUTING.md) | Lifecycle, workflow, and skill routing |
| [`docs/DHF_SIMPLIFICATION_PRODUCT_GUIDE.md`](docs/DHF_SIMPLIFICATION_PRODUCT_GUIDE.md) | Business changes, activation, daily use, and rollback for simplified DHF |
| [`docs/project-lifecycle-harness-flow-cn.html`](docs/project-lifecycle-harness-flow-cn.html) | Chinese vertical lifecycle flow |
| [`docs/project-lifecycle-harness-flow-skills.html`](docs/project-lifecycle-harness-flow-skills.html) | Chinese skill/helper routing visualization |
| [`docs/HEADROOM_WORKFLOW.md`](docs/HEADROOM_WORKFLOW.md) | Headroom output-compression workflow |
| [`docs/CODEX_SUBCONSCIOUS.md`](docs/CODEX_SUBCONSCIOUS.md) | Local subconscious companion |
| [`docs/index-en.html`](docs/index-en.html) / [`docs/index.html`](docs/index.html) | English and Chinese GitHub Pages entry points |
| [`docs/delivery-harness-beginner-guide-en.html`](docs/delivery-harness-beginner-guide-en.html) / [`docs/delivery-harness-beginner-guide-cn.html`](docs/delivery-harness-beginner-guide-cn.html) | English and Chinese beginner guides |

## Verification

The portable CI green gate matches the local verification entry point:

```bash
python3 test_runner.py
git diff --check
python3 scripts/check_surfaces.py \
  --repo-root "$(pwd)" \
  --check-public-nav
```

Every completion claim should include the current run's:

```text
command
exit_code
key_output
timestamp
```

## Security boundaries

- Keep local account data, session state, and machine-specific memory out of Git.
- Review external URLs, third-party skills, MCP integrations, and dynamic execution entry points before use.
- `scripts/`, `codex/hooks/`, `codex/runtime/`, and `codex/skills/` are high-impact surfaces and require fresh verification after changes.
- Follow `codex/remote-access.md` before any SSH, remote-service, or tunnel operation.
- Every new machine must complete its own account setup.

## FAQ

<details>
<summary>Codex Desktop cannot create a directory under Documents or Desktop</summary>

Move the task root to an unprotected location such as `~/Codes/...`, or grant Codex access under macOS **Privacy & Security → Files and Folders / Full Disk Access**.

</details>

<details>
<summary>Can I still use a legacy Superpowers checkout?</summary>

The current entry point uses the Codex plugin installation path. If an older environment still contains the legacy Superpowers checkout, treat it only as a conditional fallback, not as the new source of truth.

</details>
