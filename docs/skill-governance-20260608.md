# Skill Governance 2026-06-08

## Purpose
- Capture the first read-only skill governance baseline for MyCodexEnv.
- Keep the audit repeatable before any skill deletion, runtime cleanup, or source-of-truth change.
- Separate evidence categories: unused candidates, routing-review candidates, alias candidates, and duplicated source candidates.

## Scope
- repo root: `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv`
- repo skill source: `codex/skills/*`
- runtime skill mirror: `~/.codex/skills/*`
- local imported skill source: `.agents/skills/*`
- session evidence: local Codex sessions, archived sessions, rollout summaries, `session_index.jsonl`, and memory registry.

## Safety Boundary
- This audit is report-only.
- Do not delete, move, archive, rename, or sync skills from this report alone.
- Do not run broad runtime mirroring with `--delete` as part of governance.
- Treat `codex/skills/*` as the durable source of truth for managed skills.
- Treat `~/.codex/skills/*` as runtime state.
- Treat `.agents/skills/*` as imported-source state until a separate source policy is chosen.

## Audit Command

```bash
python3 scripts/audit_skills.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --max-candidates 35
```

Optional JSON form:

```bash
python3 scripts/audit_skills.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --json
```

Report-only deprecation simulation for one or more skills:

```bash
python3 scripts/audit_skills.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --simulate-deprecation bolder --simulate-deprecation gstack-review
```

Report-only deprecation simulation from a newline-delimited target file:

```bash
python3 scripts/audit_skills.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --simulate-deprecation-file /tmp/skill-targets.txt --json
```

Simulation output is intentionally conservative: every target reports `safe_to_remove=false` until a human reviews blockers such as repo references, alias relationships, `.agents` duplication, runtime-only status, and references from another skill or router.

## Usage Signal Definition
- `strong_signal`: explicit `superpowers-codex use-skill NAME` or `Loading ... skill: NAME` traces.
- `explicit_mentions`: user-facing `[$NAME]` mentions.
- Default governance candidates use `strong_signal`, not mentions, because mentions may be requests, examples, or generated docs.
- Use `--include-mentions` only when deciding whether a skill is actively requested by users even if it was not loaded by the runtime.

## 2026-06-08 Baseline
- history files scanned: 1366
- unique skills: 233
- repo skills: 181
- global runtime skills: 225
- `.agents/skills` skills: 37
- repo skills missing from global runtime: 0
- global runtime skills not in repo source: 44
- repo-managed skills with no default strong usage signal: 98
- first-pass decommission candidates with no default strong usage signal and at most two repo references: 25

## First-Pass Decommission Candidates
These are the safest candidates for a freeze/deprecation review because they have no default strong usage signal and at most two repo references.

- `bolder`
- `chronicle-behavior-analysis`
- `code-simplifier`
- `colorize`
- `data-analytics`
- `find-skills`
- `frontend-skill`
- `graphviz`
- `gstack-autoplan`
- `gstack-benchmark`
- `gstack-careful`
- `gstack-design-html`
- `gstack-design-shotgun`
- `gstack-devex-review`
- `gstack-guard`
- `gstack-health`
- `gstack-open-gstack-browser`
- `gstack-pair-agent`
- `gstack-setup-browser-cookies`
- `gstack-setup-deploy`
- `gstack-unfreeze`
- `ljg-roundtable`
- `teach-impeccable`
- `transreader-chrome-store-release`
- `tufte-viz`

Recommended handling: mark as `freeze-review` first, then run a removal simulation that checks docs, tests, routing descriptions, and runtime sync impact.

## 2026-06-08 First-Pass Simulation Result
- command: `python3 scripts/audit_skills.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --json` with one report-only `--simulate-deprecation NAME` argument per first-pass candidate above
- exit_code: `0`
- timestamp: `2026-06-08T17:00:58-04:00`
- key_output: `targets=25`; every target reported `safe_to_remove=false`
- blocker counts: `manual_review_required=25`, `repo_references_present=18`, `alias_relationship_present=13`, `agents_duplicate_present=2`

Initial grouping:

- manual-review only: `chronicle-behavior-analysis`, `code-simplifier`, `colorize`, `find-skills`, `ljg-roundtable`, `teach-impeccable`, `transreader-chrome-store-release`
- repo-reference only: `bolder`, `frontend-skill`, `tufte-viz`
- `.agents` duplicate plus repo references: `data-analytics`, `graphviz`
- gstack alias plus repo references: `gstack-autoplan`, `gstack-benchmark`, `gstack-careful`, `gstack-design-html`, `gstack-design-shotgun`, `gstack-devex-review`, `gstack-guard`, `gstack-health`, `gstack-open-gstack-browser`, `gstack-pair-agent`, `gstack-setup-browser-cookies`, `gstack-setup-deploy`, `gstack-unfreeze`

## Do Not Delete Directly
These categories need routing or source policy decisions before cleanup:

- `gstack-*` alias wrappers: keep until a canonical gstack naming policy is selected.
- `.agents/skills` duplicates: 29 skills have identical copies under `.agents/skills`, repo, and global runtime. This is source duplication, not proof the skills are obsolete.
- `codex-retrospective`: current strong signal is low, but it is intentionally repo-managed and connected to previous skill maintenance work.

## Alias Governance
`scripts/audit_skills.py` reports gstack alias pairs such as:

- `gstack-review` -> `review`
- `gstack-ship` -> `ship`
- `gstack-browse` -> `browse`
- `gstack-plan-eng-review` -> `plan-eng-review`

Recommended handling: choose one canonical user-facing name per pair, then keep a compatibility alias only if user prompts, docs, or generated gstack artifacts still depend on it.

## Duplicate Source Governance
`scripts/audit_skills.py` reports `.agents/skills` duplicates. If hashes are identical, cleanup should start with a source policy decision:

- keep `.agents/skills` as an imported-source lock layer, or
- remove `.agents/skills` from runtime discovery and rely on `skills-lock.json` plus `codex/skills`, or
- keep only selected external skill families in `.agents/skills`.

Do not delete `.agents/skills` duplicates until the chosen policy is reflected in README, `docs/repo-index.md`, tests, and sync behavior.

## Freeze-Review Policy

`freeze-review` is a reversible governance status for a skill or skill family.
It is not deletion, archival, renaming, runtime hiding, or runtime sync.

Use `freeze-review` before any skill removal, archive, rename, or broad runtime
sync when the action could change user-facing skill availability, routing,
source ownership, or compatibility aliases.

### Entry Criteria

A skill or bundle may enter `freeze-review` only after all of these are true:

- A fresh `scripts/audit_skills.py` report identifies the candidate, source
  locations, usage signals, repo references, alias relationships, and duplicate
  source relationships.
- A report-only deprecation simulation exists for the exact candidate list:
  `python3 scripts/audit_skills.py --repo-root "$(pwd)" --codex-home "$HOME/.codex" --simulate-deprecation NAME`.
- The simulation output has been reviewed with `safe_to_remove=false` treated as
  the default state, not as an error to bypass.
- Runtime-only, `.agents` duplicate, gstack alias, router-reference, or repo
  reference blockers are each assigned to an explicit follow-up decision.

### Allowed Actions During Freeze-Review

- Mark candidates in governance notes, issue/spec text, or a future decision
  table as `freeze-review`.
- Add or update report-only evidence, simulation commands, human review notes,
  and rollback notes.
- Update tests or docs that make the policy enforceable.

### Forbidden Actions During Freeze-Review

- Do not delete, move, archive, or rename `codex/skills/*`,
  `~/.codex/skills/*`, or `.agents/skills/*`.
- Do not make a broad runtime sync, mirror, or `--delete` operation part of the
  same slice.
- Do not remove user-facing skill names, aliases, routing references, or prompt
  examples.
- Do not claim a skill is removed, unavailable, deprecated, or safe to remove
  while the report-only simulation still reports blockers.

### Exit Criteria

Every frozen candidate or bundle must leave `freeze-review` through one explicit
decision:

- `keep`: retain the skill unchanged and record the reason.
- `defer`: keep the status open with the unresolved blocker named.
- `policy-needed`: resolve alias behavior, `.agents` source ownership, or
  runtime-only source ownership before deciding.
- `ready-for-deprecation-plan`: create a separate implementation plan with
  exact file changes, runtime sync boundary, rollback path, and verification
  commands.

Before any actual removal/archive/rename or broad runtime sync, the separate
implementation plan must include:

- exact candidate list and source paths
- explicit source-of-truth owner for repo, runtime, and `.agents` copies
- references to update in docs, routing, tests, prompts, and templates
- rollback path for repo and runtime state
- fresh verification with `command`, `exit_code`, `key_output`, and `timestamp`
- a checkpoint in `docs/harness-state.md`

## Next Safe Slice
Run a report-only freeze-review batch for the seven manual-review-only
candidates, then record the decision table without mutating skill source or
runtime state:

- start with the seven manual-review-only candidates if a reversible pilot is needed:
  `chronicle-behavior-analysis`, `code-simplifier`, `colorize`, `find-skills`,
  `ljg-roundtable`, `teach-impeccable`, `transreader-chrome-store-release`
- keep gstack aliases as a bundle until canonical alias behavior is decided
- keep `.agents` duplicates untouched until imported-source policy is decided
- verification: policy doc update, `python3 test_runner.py`, and `git diff --check`
