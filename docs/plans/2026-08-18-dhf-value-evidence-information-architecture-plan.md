# DHF Value & Evidence Information Architecture Implementation Plan

> Execute sequentially in the isolated `codex/dhf-value-evidence` worktree. Use test-first public contracts. Do not publish, push, deploy, or sync runtime.

## Goal

Replace the Chinese-only Models & Patterns hub with a bilingual Evidence information architecture organized around customer value, evidence maturity, evolution, controls, cases, recovery, and current boundaries.

## Supported Scenario

A reader can open `Evidence` from the global navigation, understand what customer value DHF claims, see what level of evidence supports each claim, follow same-language evidence pages, and distinguish durable evidence from current status.

## Information Architecture

Global navigation:

```text
Home | Beginner | Context | Lifecycle | Governance | Evidence | Status
首页 | 新手指南 | 上下文工程 | 生命周期 | 治理判定 | 证据 | 架构状态
```

Evidence hub sections:

1. Customer Value
2. Evidence Ladder
3. Evolution Evidence
4. Control Evidence
5. Case Evidence
6. Recovery Evidence
7. Current Boundaries

The fixed evidence ladder is:

```text
Design intent
→ Source implemented
→ Verification passed
→ Runtime active
→ Publicly published
→ Production enforced
→ Customer outcome validated
```

## Global Constraints

- Preserve all existing public URLs; do not delete or rename current Chinese pages.
- Create English twins for every page in the Evidence family.
- English hubs and ordinary related links point only to English pages. Chinese hubs and ordinary related links point only to Chinese pages. The language switch is the only cross-language path.
- Keep the four-step learning path unchanged; Evidence is not lifecycle step five.
- Distinguish Evidence (durable value/proof library) from Status (dated current-state snapshot).
- SAFE, TRUST, PROTECT, CAP/BRIDGE, BEST/CARE, and RECOVER are supporting concepts, not global navigation items.
- Preserve every `data-dhf-status="2026-08-11"` attribute byte-for-byte.
- Preserve normalized byte parity between `docs/index.html` and `docs/index-en.html`.
- Do not introduce a framework, build pipeline, dropdown navigation, dependency, shared JavaScript navigation, or runtime change.
- Do not change `docs/dhf-site-status.css` unless real 375px browser measurements prove the seven-item navigation fails; if it fails, make one measured minimal change.
- Do not claim production enforcement, customer adoption, or commercial outcomes without corresponding evidence.
- No commit, push, deployment, Cloudflare/DNS mutation, or runtime synchronization in this plan.

## Exact Write Set

### Create

- `docs/plans/2026-08-18-dhf-value-evidence-information-architecture-plan.md`
- `docs/dhf-value-evidence-en.html`
- `docs/dhf-value-evidence-cn.html`
- `docs/dhf-best-care-recover-en.html`
- `docs/dhf-data-business-value-explainer-en.html`
- `docs/dhf-safe-data-ai-comparison-en.html`
- `docs/dhf-shipq-development-history-en.html`
- `docs/dhf-case-safe-mapping-en.html`
- `docs/dhf-examples-three-lenses-en.html`
- `docs/dhf-examples-three-lenses-safe-en.html`
- `docs/shipq-dhf-safe-controlled-recovery-en.html`
- `docs/shipq-dhf-incident-recovery-memory-map-en.html`

### Modify Evidence family

- `docs/dhf-best-care-recover.html`
- `docs/dhf-data-business-value-explainer.html`
- `docs/dhf-safe-data-ai-comparison.html`
- `docs/dhf-shipq-development-history.html`
- `docs/dhf-case-safe-mapping.html`
- `docs/dhf-examples-three-lenses.html`
- `docs/dhf-examples-three-lenses-safe.html`
- `docs/shipq-dhf-safe-controlled-recovery.html`
- `docs/shipq-dhf-incident-recovery-memory-map.html`
- `docs/dhf-protect-seven-components-en.html`
- `docs/dhf-protect-seven-components-cn.html`

### Modify global navigation

All current HTML files returned by:

```bash
rg -l 'class="dhf-nav"' docs/*.html
```

The baseline set contains 26 files. Only add the Evidence item, set `aria-current` on the Evidence hubs, and update same-language Evidence discovery links.

### Modify contracts and registries

- `test_runner.py`
- `docs/surfaces.json`
- `docs/repo-index.md`
- `docs/LIFECYCLE_SKILL_ROUTING.md`
- `docs/dhf-site-status.css` only under the measured overflow exception above

## Task 0: Ownership and Baseline

- Confirm checkout identity, branch, synchronization, status, and exact write set.
- Record the 26 baseline `dhf-nav` files and current public surface entries.
- Run the existing focused Models & Patterns contract as a clean baseline; do not run the full repository gate before the final material change.

Completion: ownership is unambiguous and the baseline focused contract passes.

## Task 1: Add the Failing Evidence Contract

Modify `test_runner.py` first and register `test_dhf_value_evidence_information_architecture()`.

Assert:

- exactly one `data-dhf-evidence-hub="en"` and one `data-dhf-evidence-hub="cn"`;
- bidirectional language twins;
- the seven evidence ladder labels occur once and in order on both hubs;
- both hubs expose all seven required sections;
- every Evidence child has one same-language hub backlink and one language-twin link;
- ordinary English Evidence links do not route to Chinese children and vice versa;
- all 26 baseline global nav files contain Evidence between Governance and Status, with exact language targets;
- the four-step learning path remains four steps;
- `index.html` and `index-en.html` retain normalized byte parity;
- affected status markers remain unchanged;
- the former `data-dhf-models-hub` marker is absent.

Run the focused test and confirm RED because the bilingual Evidence hubs do not exist.

## Task 2: Create the Bilingual Evidence Hubs

Create `dhf-value-evidence-en.html` and `dhf-value-evidence-cn.html` with the seven fixed sections and evidence ladder. Use customer questions and proof levels, not acronym taxonomy. Include exact language switches and current-status links.

Completion: hub-only assertions pass while missing children/navigation assertions remain RED.

## Task 3: Re-scope BEST / CARE / RECOVER

Convert `dhf-best-care-recover.html` from the global hub into the Chinese memory-and-recovery aid. Create `dhf-best-care-recover-en.html`. Each page links its same-language Evidence hub and exact language twin. Preserve useful existing BEST/CARE/RECOVER content.

## Task 4: Complete the English Evidence Family

Create English twins for SAFE → TRUST, Data/AI auxiliary comparison, ShipQ evolution, SAFE case mapping, both casebooks, controlled recovery, and incident recovery. Preserve facts and evidence boundaries; do not invent outcomes. Add same-language hub backlinks and exact twin links to existing Chinese pages.

## Task 5: Wire Global Navigation and Same-language Discovery

- Add Evidence between Governance and Status in all 26 baseline global nav files.
- Use `Evidence` → `dhf-value-evidence-en.html` for English and `证据` → `dhf-value-evidence-cn.html` for Chinese.
- Keep the four-step learning path unchanged.
- Replace English-home `Models & Patterns（中文）` with English Evidence.
- Replace Chinese-home Models & Patterns with Chinese Evidence.
- Link PROTECT EN/CN and all Evidence children to their same-language hub.

## Task 6: Register Surfaces and Documentation

Update `docs/surfaces.json`, `docs/repo-index.md`, and `docs/LIFECYCLE_SKILL_ROUTING.md` for the two hubs, bilingual children, language boundary, and new roles. Remove the former Models-hub role without removing its page.

## Task 7: Final Verification

Run in order after the final material change:

1. focused Evidence IA, public IA, architecture status, and relevant registry tests;
2. `python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav`;
3. `git diff --check`;
4. exactly one final `PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py`;
5. real-browser desktop and 375px checks for both homes, both Evidence hubs, every bilingual child pair, and PROTECT EN/CN.

Browser acceptance:

- no whole-page horizontal overflow;
- one H1 per page and readable hierarchy;
- Evidence has `aria-current` on both hubs;
- language twins are bidirectional;
- English/Chinese related links remain language-local;
- dark mode and reduced motion preserve readable content;
- Evidence and Status are visibly distinct.

Every gate receipt records command, exit code, key output, and UTC timestamp.

## Stop Conditions

- Any required write outside the exact write set.
- Ownership ambiguity or unrelated dirty changes.
- Mixed-language ordinary Evidence links.
- Changed status date, learning-path length, or lifecycle claims.
- Any focused, surface, parity, browser, or final gate failure that cannot be corrected within scope.

## Acceptance Criteria

- Evidence is a consistent seventh global navigation item.
- Both languages have a complete Evidence hub and exact twin page family.
- Customer value, evidence maturity, evolution, controls, cases, recovery, and current boundaries form one coherent narrative.
- Existing public URLs remain valid.
- No claim exceeds its evidence level.
