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

## Do Not Delete Directly
These categories need routing or source policy decisions before cleanup:

- `gstack-*` alias wrappers: keep until a canonical gstack naming policy is selected.
- `arscontexta-*` child skills: most child skills have no direct strong signal, but the parent/router skills are active enough that this should be reviewed as a bundle.
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

## Next Safe Slice
Implement a deprecation simulation mode in `scripts/audit_skills.py`:

- input: a skill name or file containing skill names
- checks: repo references, alias relationship, `.agents` duplication, runtime-only status, and whether the skill is mentioned by another skill description or router
- output: `safe_to_remove=false` by default with blockers and required manual review
- verification: temporary fixture test in `test_runner.py`, then `python3 test_runner.py` and `git diff --check`
