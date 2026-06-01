# Patch Plan: EFC-Based Improvements to the Delivery Harness

- Date: 2026-06-01
- Author: Claude (Cowork), for Codex review
- Status: PROPOSED — not yet applied. This is a reviewable plan, not a diff.
- Scope class: documentation / skill-text only (no runtime code in this patch)
- Lane: `local_dev` — no external systems, secrets, deploys, or customer data
- task_demand: `medium` — multi-file, cross-repo behavior-contract change, but
  well-bounded, no logic/runtime code. Self-applies the B1 rule: this patch is
  not `low`, so it runs the full `test_runner.py` gate plus byte-identity diffs,
  not just `git diff --check`. (L: moderate; H_tool: low; S_state: medium — two
  skill copies + two repos must stay consistent; N_obs: low.)

## Motivation

Source: arXiv:2605.29682, *Scaling Laws for Agent Harnesses via Effective
Feedback Compute* (Zhang, Wang, Xu, Zhu, Che; 2026-05-28).
Source verification: arXiv abstract page
<https://arxiv.org/abs/2605.29682>, retrieved 2026-06-01.

The paper introduces **Effective Feedback Compute (EFC)**: a feedback event
earns credit only when it is simultaneously **informative (I)**, **valid (V)**,
**non-redundant (R)**, and **retained / memory-updating (M)** — scored as a
product, then normalized by **task demand `D_task`**. Empirically, raw compute
(tokens, tool calls) explains little of the failure-rate variance (R²=0.33/0.42),
while EFC/`D_task` reaches R²≈0.99; and in a matched-budget intervention, holding
raw cost and tool calls fixed and improving only feedback quality raised success
from 0.27 to 0.90.

Audit of the current harness against this lens:

- **Already aligned (do NOT change):** the Evidence And Report Gate (requires
  `command`/`exit_code`/`key_output`/`timestamp`, forbids reusing stale
  verification) and the Debug Feedback Gate (forbids patching from inspection
  alone, requires a runnable feedback loop) already enforce V and I. The
  append-only state log and checkpoint helpers already enforce M. Vertical-slice
  decomposition and disjoint write sets already give structural R.
- **Systematic gap this patch addresses:** the harness verifies that valid
  feedback was *produced* (presence) but never measures how efficiently the spent
  budget *converted* into durable, task-sufficient feedback (conversion). It also
  has no graded notion of `D_task`: gate tables are keyed by coarse work-type
  category, so they cannot distinguish "hard task, reasonable effort" from "easy
  task, wasteful effort."

This patch closes the gap at the **planning / requirements / output-contract**
layer only. The deeper code-level work (stall detection in `harness_recover.py` /
`harness_report.py`, per-worker demand gates in `harness_agent_team.py`) is
explicitly deferred to a separate slice (see Out of Scope).

## Design principle preserved

The Delivery Harness Framework's own Lifecycle Ownership rule: the **generic**
skill must not encode repo paths, fixtures, or project-only commands. Therefore:

- The abstract `task_demand` concept and the conversion self-check live in the
  **generic** `delivery-harness-framework`.
- The concrete, ShipQ-specific gate scaling (which `pytest` scope per demand
  level) lives in the **repo** `shipq-lifecycle-harness`.

## Files changed (4 primary source edits across 2 repos + sync + conditional eval/test updates)

Primary source edits:

1. MyCodexEnv generic DHF skill text.
2. MyCodexEnv ShipQ adapter skill text.
3. ShipQ Phase 1 slice contract template.
4. MyCodexEnv harness requirements template.

Generated/synchronized surfaces:

- `~/.codex/skills/delivery-harness-framework/SKILL.md`
- `~/.codex/skills/shipq-lifecycle-harness/SKILL.md`

Conditional same-slice updates:

- `MyCodexEnv/codex/skills/delivery-harness-framework/evals/evals.json`
- Any validator/test expectations that pin the old Output Contract or template
  shape.

### A. `MyCodexEnv/codex/skills/delivery-harness-framework/SKILL.md` (generic router)

A1. **Engineering Planning Gate** (~lines 239–248, the slice-contract capture
list): add a graded `task_demand` field to the items each slice contract must
capture. Definition uses the paper's four `D_task` components:

- `task_demand`: `low | medium | high`, justified by
  - `L` — estimated minimum reasoning/action steps
  - `H_tool` — tool-selection ambiguity
  - `S_state` — cross-module state-tracking demand
  - `N_obs` — observation / external noise

Add one sentence: the minimum gate and the chosen next-safe-task should scale
with `task_demand` (low demand must not be forced through a full regression; high
demand requires more than the default gate).

A2. **Evidence And Report Gate** (~lines 371–394): add a short
"Effective-feedback check" paragraph. Before claiming completion, the spent loops
must be classifiable as informative, valid, non-redundant, and retained; any
segment that consumed budget without producing retained, task-relevant feedback
(e.g. re-running an already-green gate, repeating information already in the
trajectory) must be flagged as low-conversion in the handoff.

Use this stable shape (key/value checklist, not rendered markdown):

```text
effective_feedback_check:
- informative:
- valid:
- non_redundant:
- retained:
- low_conversion_segments:
```

Keep this as a structured prose/checklist requirement in this slice, not a new
mandatory script or schema field. `evidence.schema.json` changes stay deferred.

A3. **Output Contract** (~lines 443–467): add one numbered item (becomes item
12) requiring the router to state: the selected `task_demand`, the
demand-matched gate actually used, and the result of the effective-feedback
check.

### B. `MyCodexEnv/codex/skills/shipq-lifecycle-harness/SKILL.md` (repo router)

B1. **Verification Routing** table (~lines 76–83): add a demand-scaled column so
the abstract concept from A1 gets ShipQ-specific teeth. Proposed scaling:

- `low` (docs/config only): `git diff --check` plus path/link/command
  consistency checks. Add a focused test only when the doc/config change affects
  commands, scripts, behavior, contracts, or public output.
- `medium` (single-module code/runtime/import/API): `git diff --check` +
  `PATH=.venv/bin:$PATH pytest -q <focused test file>` or the focused existing
  harness command for the touched behavior.
- `high` (core or cross-module: `quote_engine.py`, `pricing_branch.py`,
  workbook→runtime, internal/public demo boundary, extension/API auth or
  security boundary, public/private data boundary, cross-module importer/facade
  changes): focused gate **+** full
  `PATH=.venv/bin:$PATH pytest -q` **+** at least one new probe targeting the
  slice's active subgoal (not just existing regressions).

Existing ShipQ Hard Gates and the current per-work-type rows remain; the demand
column refines them, it does not replace them.

### C. `ShipQ/docs/templates/phase1-slice-contract.md` (ShipQ repo)

C1. **Slice Summary**: add the `task_demand` fields (same shape as A1).

C2. **Completion Questions**: add the four EFC completion questions —
informative? valid? non-redundant? retained? — with the rule that any "no" marks
the segment as low-conversion in the handoff.

Use the same stable shape as A2:

```text
## Effective Feedback Check
- informative:
- valid:
- non_redundant:
- retained:
- low_conversion_segments:
```

### D. `MyCodexEnv/docs/templates/harness-requirements.md` (requirements artifact)

D1. Add a `## Task Demand (D_task)` section so difficulty is prompted at the
**requirements** stage and intended to be carried downstream into planning,
slices, and verification. In this slice it is an advisory prompt, not an
enforced gate, because `harness_requirements.py` still accepts templates without
this heading:

```
## Task Demand (D_task)
- estimated_level: low | medium | high
- L (reasoning/action steps):
- H_tool (tool-selection ambiguity):
- S_state (cross-module state tracking):
- N_obs (observation/external noise):
```

Note: at requirements time `L` and `S_state` are often rough estimates; the
field is allowed to be refined (not rewritten silently) once code is read at
slice time. This gives downstream plans a stable field to reuse when present; it
does not by itself guarantee first-to-last consistency until Improvement 6
enforces the heading.

**Enforcement limitation (read before relying on D).** `harness_requirements.py`
validates against `REQUIRED_HEADINGS` as an *open* set — it errors only on
*missing* required headings, never on extra ones (verified 2026-06-01). So adding
`## Task Demand (D_task)` is safe and the template still validates, but the
section is **advisory**: an artifact that omits it still passes `validate`. This
slice keeps D advisory (doc-only, no runtime change). Making D actually enforced
("every requirements artifact must carry a populated Task Demand") requires adding
`"Task Demand (D_task)"` to `REQUIRED_HEADINGS` in `harness_requirements.py` —
a one-line code change deferred to the Out-of-Scope list, not done here. Do not
claim "difficulty is captured consistently" until that follow-up lands; until
then D is a prompt, not a gate.

## Pre-steps (mandatory before editing)

### 1. Two-repo dirty-state and read-first preflight

Run in MyCodexEnv:

```bash
git status --short --branch
sed -n '1,220p' AGENTS.md
sed -n '1,220p' README.md
sed -n '1,220p' docs/repo-index.md
```

Run in ShipQ:

```bash
git status --short --branch
sed -n '1,220p' AGENTS.md
sed -n '1,120p' docs/designs/harness-state.md
tail -n 220 docs/designs/harness-state.md
sed -n '1,220p' docs/templates/phase1-slice-contract.md
```

Classify dirty files in both repos before editing:

- user-owned: pre-existing unrelated changes; do not modify, stage, or revert.
- task-owned: files listed in this plan after they are intentionally changed.
- blocker: any target file already dirty with unrelated content; stop or create a
  fresh branch/worktree before continuing.

Do not commit, push, deploy, read secrets, or run live-provider workflows in this
slice.

### 2. Eval and validator preflight

Read `MyCodexEnv/codex/skills/delivery-harness-framework/evals/evals.json`
(~17 KB). If any eval pins the exact Output Contract item count or its text, edit
A3 will add item 12 and could regress those evals. Any such pinned rows must be
updated in the same patch. If a validator/test pins the old requirements template
shape, update that expectation in the same patch or mark the slice blocked.

Local preflight result from 2026-06-01 review: a scan found no obvious exact
Output Contract item-count pin in `evals.json`, but this must be rechecked fresh
when the patch is implemented.

## Dual-copy sync (mandatory, chosen path)

The skills exist in two copies (recorded in
`MyCodexEnv/docs/harness-state.md`, entry 2026-05-11):

- canonical, git-tracked: `MyCodexEnv/codex/skills/.../SKILL.md`
- live, loaded by Codex: `~/.codex/skills/.../SKILL.md`

Both edits (A, B) must land in both copies, byte-identical.

Chosen path: edit only the MyCodexEnv canonical copies, then run the existing
sync script:

```bash
./scripts/sync_codex_home.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --skip-superpowers-sync
```

Then prove byte identity:

```bash
diff -u codex/skills/delivery-harness-framework/SKILL.md "$HOME/.codex/skills/delivery-harness-framework/SKILL.md"
diff -u codex/skills/shipq-lifecycle-harness/SKILL.md "$HOME/.codex/skills/shipq-lifecycle-harness/SKILL.md"
```

Files C and D exist in a single repo location each and need no live skill mirror.

## Verification

Run fresh. Do not reuse prior output.

### MyCodexEnv

```bash
# NOTE: validate only proves the template parses and keeps its required
# headings. Because Task Demand is advisory (see Enforcement limitation under D),
# this does NOT prove Task Demand is present or populated.
python3 scripts/harness_requirements.py validate docs/templates/harness-requirements.md
python3 test_runner.py
git diff --check
diff -u codex/skills/delivery-harness-framework/SKILL.md "$HOME/.codex/skills/delivery-harness-framework/SKILL.md"
diff -u codex/skills/shipq-lifecycle-harness/SKILL.md "$HOME/.codex/skills/shipq-lifecycle-harness/SKILL.md"
rg -n "task_demand|effective_feedback_check|low_conversion_segments|Output Contract" codex/skills/delivery-harness-framework/SKILL.md codex/skills/shipq-lifecycle-harness/SKILL.md docs/templates/harness-requirements.md
```

Also re-read or scan `evals.json` after edits and update any stale pinned
assertion before claiming completion:

```bash
node - <<'NODE'
const fs = require('fs');
const path = 'codex/skills/delivery-harness-framework/evals/evals.json';
const data = JSON.parse(fs.readFileSync(path, 'utf8'));
const hits = [];
function walk(value, pointer = []) {
  if (typeof value === 'string') {
    if (/Output Contract|After routing, state|item 12|numbered item|exact text/i.test(value)) {
      hits.push(`${pointer.join('.')}: ${value}`);
    }
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => walk(item, pointer.concat(index)));
    return;
  }
  if (value && typeof value === 'object') {
    Object.entries(value).forEach(([key, item]) => walk(item, pointer.concat(key)));
  }
}
walk(data);
console.log(hits.length ? hits.join('\n') : 'no_stale_pins_detected');
NODE
```

A static string scan is not proof that behavior is unaffected: an eval can assert
routing behavior that shifts when the Output Contract re-enumerates, without ever
quoting "Output Contract" literally. So also run the eval suite **before and
after** the edits and compare pass counts; a drop is a regression even if the
scan returns `no_stale_pins_detected`.

```bash
# capture BEFORE editing (on the unmodified skill), then AFTER, and diff:
python3 test_runner.py 2>&1 | tee /tmp/efc-evals-before.txt   # baseline
# ...apply edits...
python3 test_runner.py 2>&1 | tee /tmp/efc-evals-after.txt    # post-patch
diff <(grep -Eo '[0-9]+ (passed|failed|errors?)' /tmp/efc-evals-before.txt) \
     <(grep -Eo '[0-9]+ (passed|failed|errors?)' /tmp/efc-evals-after.txt) \
  && echo "eval pass/fail counts unchanged" || echo "REGRESSION: counts changed, investigate"
```

Current local decision: no executable repo runner for
`codex/skills/delivery-harness-framework/evals/evals.json` has been identified.
Unless the implementer first discovers and names a concrete command, behavioral eval execution is unavailable for this slice. Final claims may cover only the
static stale-pin scan plus full `test_runner.py` before/after pass-count parity,
not behavioral DHF eval execution. If a concrete eval runner is discovered, add
the exact command to this plan before editing and run it before/after like
`test_runner.py`.

### ShipQ

```bash
git diff --check
rg -n "task_demand|Effective Feedback Check|low_conversion_segments" docs/templates/phase1-slice-contract.md
rg -n "docs/templates/phase1-slice-contract.md|docs/designs/harness-state.md" AGENTS.md docs/repo-index.md docs/designs/harness-state.md
# B1 names specific high-demand trigger files; confirm they still exist so the
# demand column does not reference dead paths:
for f in src/quote_engine.py src/pricing_branch.py; do test -e "$f" && echo "OK $f" || echo "MISSING $f (update B1 triggers)"; done
```

If the ShipQ template change alters any documented workflow beyond the template
itself, run the narrowest focused docs/contract check named by ShipQ's current
harness state. If the change affects behavior, scripts, API, workbook/runtime,
demo, security, or public/private output, it is no longer low demand and must use
the medium/high gates from B1.

No runtime code executes in this patch.

## Out of scope (deferred to a separate slice)

- Improvement 3: stall / conversion-health signal computed from existing local
  evidence in `harness_recover.py` / `harness_report.py`, surfaced as a flag in
  the Output Contract. Requires reading those scripts first.
- Improvement 4: per-worker `task_demand` + demand-matched green gate in
  `harness_agent_team.py validate`.
- Improvement 5: splitting `evidence.schema.json` into decision-evidence vs.
  routine gate receipts to keep the state log high-R and lower cold-start cost.
- Improvement 6 (enforce D): add `"Task Demand (D_task)"` to `REQUIRED_HEADINGS`
  in `scripts/harness_requirements.py` so every requirements artifact must carry
  a populated Task Demand section, plus an eval/test covering the new required
  heading. One-line code change; deferred to keep this slice doc-only.

These are real code changes and get their own implementation plan.

## Rollback

One commit per repo, documentation-only. Revert via `git revert`. No data
migration, no state-log mutation, no runtime behavior change.

## Review questions for Codex

Resolved by review:

1. Generic/repo split is correct: abstract `task_demand` in DHF; concrete
   ShipQ gate scaling in `shipq-lifecycle-harness`.
2. High-demand ShipQ triggers include `quote_engine.py`, `pricing_branch.py`,
   workbook→runtime, internal/public demo boundary, extension/API auth or
   security boundary, public/private data boundary, and cross-module
   importer/facade changes.
3. Effective-feedback check stays a structured prose/checklist field in this
   slice. `evidence.schema.json` changes remain deferred.
4. Dual-copy sync path is canonical edit plus `sync_codex_home.sh`; no direct
   hand-editing of `~/.codex/skills/*`.
5. Edit D ships **advisory** this slice (doc-only). The validator is open-set, so
   Task Demand is a prompt, not a gate, until Improvement 6 (Out of Scope) adds it
   to `REQUIRED_HEADINGS`. The plan must not claim consistent capture before then.
6. This patch self-classifies as `task_demand: medium` and runs the medium/high
   gate on itself (full `test_runner.py` + byte-identity diffs), not just
   `git diff --check`.
