# DHF Evidence Memory Keywords Implementation Plan

> **For agentic workers:** Implement sequentially with TDD. This plan authorizes worktree changes, verification, code review, and a commit on the current feature branch. It does not authorize push, merge, deployment, DNS, or runtime sync.

## Goal

Strengthen CAP, SAFE, TRUST, BRIDGE, and RECOVER across the bilingual Evidence family while placing BEST and CARE only where their system and action perspectives help readers remember the framework.

## Architecture

The two Evidence hubs own the complete memory spine: `CAP → BRIDGE × SAFE → TRUST`, with RECOVER shown as a conditional failure branch. Each child page owns one compact Memory Cue containing no more than three core terms, except the dedicated BEST / CARE / RECOVER memory page. English and Chinese twins use identical term and lens sets.

## Fixed Page Mapping

| Page family | Core terms | Lens |
|---|---|---|
| Evidence hubs | CAP, BRIDGE, SAFE, TRUST, RECOVER | BEST, CARE |
| BEST / CARE / RECOVER | CAP, BRIDGE, SAFE, TRUST, RECOVER | BEST, CARE |
| SAFE → TRUST value | SAFE, TRUST | CARE |
| Data/AI comparison | SAFE, TRUST | none |
| PROTECT | SAFE, TRUST | BEST |
| Evolution | CAP, BRIDGE, TRUST | BEST |
| SAFE case map | SAFE, TRUST | CARE |
| Three-lens casebook | CAP, TRUST | CARE |
| Three-lens × SAFE | SAFE, TRUST | CARE |
| Controlled recovery | SAFE, RECOVER, TRUST | CARE |
| Incident memory map | SAFE, RECOVER | CARE |

## Global Constraints

- Preserve all existing URLs and `data-dhf-status="2026-08-11"` attributes.
- Do not turn SAFE, TRUST, or RECOVER into lifecycle stages.
- RECOVER appears only on the hubs, memory page, and recovery pages.
- Ordinary child cues contain at most three core terms.
- BEST appears only on system, architecture, and evolution pages.
- CARE appears only on practice, case, and recovery pages.
- English and Chinese twin mappings must be identical.
- Use shared native CSS; add no JavaScript, framework, dependency, or build step.
- Do not change the global navigation or Evidence versus Status boundary.

## Exact Write Set

### Create

- `docs/dhf-evidence-memory.css`
- `docs/plans/2026-08-18-dhf-evidence-memory-keywords-plan.md`

### Modify

- `test_runner.py`
- `docs/surfaces.json`
- `docs/repo-index.md`
- `docs/LIFECYCLE_SKILL_ROUTING.md`
- `docs/dhf-value-evidence-en.html`
- `docs/dhf-value-evidence-cn.html`
- the ten existing bilingual Evidence child pairs registered by `test_dhf_value_evidence_information_architecture()`

## Task 0: Ownership and Baseline

- Confirm worktree, branch, clean ownership, and current main SHA.
- Confirm no existing `data-dhf-memory-spine` or `data-dhf-memory-cue` markers.
- Run the existing Evidence and public IA tests.

## Task 1: RED Contract

- Add and register `test_dhf_evidence_memory_keyword_contract()` in `test_runner.py`.
- Assert the exact page mapping above, one spine per hub, one cue per child, bilingual parity, stylesheet use, the three-term limit, and BEST / CARE / RECOVER boundaries.
- Run the single test and confirm failure on the missing English hub spine.

## Task 2: Shared Styles and Hub Spine

- Create `docs/dhf-evidence-memory.css` with responsive spine, cue, term, lens, conditional RECOVER, dark-compatible variables, and reduced-motion behavior.
- Link it from all 22 Evidence pages.
- Add the five-term spine and BEST / CARE lenses to both hubs.

## Task 3: Value, Control, and Evolution Cues

- Add exact Memory Cues to SAFE → TRUST, Data/AI comparison, PROTECT, Evolution, and SAFE Case Mapping twins.
- Keep each cue within the fixed mapping.

## Task 4: Case, Recovery, and Memory Cues

- Add exact Memory Cues to the casebooks, controlled recovery, incident map, and dedicated memory-page twins.
- State that RECOVER restores facts and state, not permission.

## Task 5: Registration

- Register the shared CSS in `docs/surfaces.json` and `docs/repo-index.md`.
- Document the memory contract in `docs/LIFECYCLE_SKILL_ROUTING.md`.

## Task 6: Verification and Review

Run after the final material change:

1. focused memory, Evidence IA, public IA, architecture status, and registry tests;
2. `python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav`;
3. `git diff --check`;
4. real browser desktop, 375px, light, dark, and reduced-motion acceptance for all 22 pages;
5. one final `PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py`;
6. code review against the branch base;
7. commit the reviewed write set to the current feature branch.

## Acceptance Criteria

- Both hubs show the same five-term spine and BEST / CARE relationship.
- All 20 child pages have exactly one compact, responsibility-specific cue.
- Bilingual mappings are identical and ordinary cues never exceed three core terms.
- No whole-page mobile overflow; dark-mode text and cues remain readable.
- Focused, surfaces, diff, browser, full-suite, and code-review gates pass.
