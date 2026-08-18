# DHF Models & Patterns and SAFE Extraction Implementation Plan

> **For agentic workers:** Execute this plan task by task in one worktree. Use test-first changes for public contracts. Do not use subagents for this bounded static-site slice.

**Goal:** Organize SAFE, PROTECT, TRUST, CAP/BRIDGE, BEST/CARE, RECOVER, and case evidence under one Models & Patterns hub while extracting all Data/AI-specific comparison content from the canonical SAFE → TRUST page into one auxiliary child page.

**Architecture:** Reuse `docs/dhf-best-care-recover.html` as the hub. Keep `docs/dhf-data-business-value-explainer.html` as the canonical generic SAFE → TRUST page and create one Chinese auxiliary comparison page. Preserve the six-item global top navigation; discovery happens through Engineering Resources and hub-spoke links.

**Tech Stack:** Static HTML/CSS, Python `test_runner.py`, `docs/surfaces.json`, `scripts/check_surfaces.py`, Playwright CLI.

## Global Constraints

- Work only in `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv` on the current clean `main` worktree.
- Preserve every `data-dhf-status="2026-08-11"` attribute byte-for-byte.
- Keep global top navigation unchanged.
- Reuse `dhf-best-care-recover.html`; do not create a second hub.
- Preserve the public URL `dhf-data-business-value-explainer.html`.
- The full Data/AI versus DHF comparison has exactly one owner: `dhf-safe-data-ai-comparison.html`.
- The SAFE main page may mention Data/AI only in one marked auxiliary-link card; it must not retain comparison lanes or Data/AI-specific examples.
- Keep the module Chinese-first. English PROTECT may link to the hub only with an explicit `Models & Patterns（中文）` label.
- Add no dependency, framework, build pipeline, dropdown, shared navigation component, or directory router.
- Do not modify `docs/dhf-site-status.css` unless browser evidence proves a shared-style defect.
- No commit, push, deployment, Cloudflare/DNS change, or runtime synchronization in this task.

## Supported Scenario

- A reader starts from Engineering Resources, opens Models & Patterns, chooses a model by question, and can distinguish core models, conditional subflows, maturity paths, and evidence pages.
- A reader opens SAFE → TRUST for the generic control/value model and follows one auxiliary link for the Data/AI comparison.

## Non-goals

- Full English translation of the Chinese model library.
- Rewriting case-study bodies.
- Changing DHF lifecycle, runtime behavior, public status, or production claims.
- Adding SAFE, TRUST, PROTECT, BRIDGE, or RECOVER as separate top-menu items.

## Complexity Budget

- One new HTML page.
- Eleven existing files modified plus two new files, including this plan and the auxiliary page.
- No new CSS or JavaScript file.
- No duplicated full comparison content.

## Information Architecture

```text
Engineering Resources
└── Models & Patterns
    ├── Control & Value
    │   ├── SAFE → TRUST
    │   └── Auxiliary: Data/AI Architecture vs DHF
    ├── Runtime Architecture
    │   └── PROTECT
    ├── Evolution
    │   └── CAP / BRIDGE
    ├── Operating Memory
    │   └── BEST / CARE
    ├── Incident Response
    │   └── RECOVER
    └── Cases & Evidence
```

## Exact Write Set

### Create

- `docs/dhf-safe-data-ai-comparison.html`
- `docs/plans/2026-08-18-dhf-models-patterns-and-safe-extraction-plan.md`

### Modify

- `docs/index.html`
- `docs/index-en.html`
- `docs/index-zh.html`
- `docs/dhf-best-care-recover.html`
- `docs/dhf-data-business-value-explainer.html`
- `docs/dhf-protect-seven-components-en.html`
- `docs/dhf-protect-seven-components-cn.html`
- `docs/LIFECYCLE_SKILL_ROUTING.md`
- `docs/repo-index.md`
- `docs/surfaces.json`
- `test_runner.py`

### Default No-write Set

- `docs/dhf-site-status.css`
- Existing case, evolution, recovery, and memory-map page bodies
- `README.md`, `docs/CNAME`
- Runtime, hooks, skills, `codex/`, `claude/`

## Task 0: Ownership and Baseline

- [x] Confirm `git rev-parse --show-toplevel` is the MyCodexEnv repository.
- [x] Confirm `main...origin/main` is clean and synchronized.
- [x] Confirm no linked dirty worktree is in scope.
- [ ] Capture the initial exact write set and existing surface entries.

Completion criterion: ownership is unambiguous and no file outside the exact write set is modified.

## Task 1: Add the Failing Models Contract

**File:** `test_runner.py`

- [ ] Add `test_dhf_models_and_patterns_information_architecture()`.
- [ ] Register it in `TESTS`.
- [ ] Assert the hub has exactly one `data-dhf-models-hub` marker.
- [ ] Assert the SAFE page has `data-dhf-model-role="control-value"`.
- [ ] Assert the auxiliary page has `data-dhf-model-role="auxiliary-comparison"`.
- [ ] Assert the full comparison appears once through `data-dhf-comparison="data-ai-vs-dhf"`.
- [ ] Assert the SAFE page has one `data-dhf-auxiliary-link="data-ai-comparison"` and no comparison marker.
- [ ] Assert Data/AI-specific implementation terms are absent from the SAFE page except inside the marked auxiliary link.
- [ ] Assert the hub links SAFE, PROTECT CN/EN, CAP/BRIDGE, RECOVER, TRUST, and Cases & Evidence.
- [ ] Replace the old full-mesh visual-page rule with hub-spoke rules: hub links every child; each child links to the hub; sibling links remain optional.
- [ ] Assert the three home pages expose Models & Patterns only in Engineering Resources, not primary navigation.
- [ ] Assert `index.html` and `index-en.html` remain byte-identical after existing URL normalization.
- [ ] Assert all affected current pages preserve `data-dhf-status="2026-08-11"`.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c \
'import test_runner; test_runner.test_dhf_models_and_patterns_information_architecture()'
```

Expected RED: missing hub/model markers and missing auxiliary page.

## Task 2: Upgrade the Existing Hub

**File:** `docs/dhf-best-care-recover.html`

- [ ] Retitle the page to `DHF Models & Patterns` while preserving BEST/CARE/RECOVER content.
- [ ] Add `data-dhf-models-hub` to the main hub container.
- [ ] Organize cards by Control & Value, Runtime Architecture, Evolution, Operating Memory, Incident Response, and Cases & Evidence.
- [ ] Explain that SAFE/TRUST are cross-stage lenses, PROTECT is runtime implementation, CAP/BRIDGE is evolution, RECOVER is conditional, and BEST/CARE is memory/communication.
- [ ] Link the auxiliary Data/AI comparison under SAFE, marked as auxiliary rather than a peer model.
- [ ] Preserve all existing public URLs to child pages.

Completion criterion: the hub answers what each model is for without presenting the acronyms as competing workflows.

## Task 3: Make SAFE → TRUST Generic

**File:** `docs/dhf-data-business-value-explainer.html`

- [ ] Change title/H1 to `SAFE Controls Create TRUST` with a Chinese explanatory subtitle.
- [ ] Add `data-dhf-model-role="control-value"` to the page content root.
- [ ] Retain SAFE, TRUST, generic value-domain mappings, and generic SAFE 2.0 boundaries.
- [ ] Remove the two-system hero equation and every Data/AI-specific lane, schema, quality, model-decision, drift, privacy, and risk-map example.
- [ ] Remove Data/AI-specific implementation recommendations from the generic gap table while preserving Generic DHF boundaries.
- [ ] Add one marked auxiliary card linking to `dhf-safe-data-ai-comparison.html`.
- [ ] Link back to Models & Patterns.

Completion criterion: the page is understandable without Data/AI knowledge and contains no full comparison content.

## Task 4: Create the Auxiliary Data/AI Comparison

**File:** `docs/dhf-safe-data-ai-comparison.html`

- [ ] Reuse the existing visual language from the SAFE page; do not add shared CSS.
- [ ] Add `data-dhf-model-role="auxiliary-comparison"` and `data-dhf-comparison="data-ai-vs-dhf"`.
- [ ] Move, rather than copy, the Data/AI versus DHF hero and five TRUST-domain lane comparisons.
- [ ] Include schema, data quality, model decision, drift, privacy/risk map, execution lane, receipts, checkpoint, rollback, and handoff examples.
- [ ] Explain Generic DHF, Repo Adapter, Runtime Platform, and Learning Workflow ownership.
- [ ] Add a visible evidence boundary: auxiliary analysis is not production or adoption proof.
- [ ] Link back to SAFE → TRUST and Models & Patterns.

Completion criterion: all detailed Data/AI comparison content has one owner and the page works independently as an auxiliary case.

## Task 5: Add Discovery Without Expanding Top Navigation

**Files:** `docs/index.html`, `docs/index-en.html`, `docs/index-zh.html`, PROTECT EN/CN.

- [ ] Add Models & Patterns as the first Engineering Resources item on all three home pages.
- [ ] Label English-home links `Models & Patterns（中文）` with `lang="zh-CN"` and `hreflang="zh-CN"`.
- [ ] Keep the six primary top-menu entries unchanged.
- [ ] Add `Models & Patterns（中文）` to English PROTECT and `Models & Patterns` to Chinese PROTECT as secondary links.
- [ ] Preserve PROTECT’s status and language-twin links.

Completion criterion: the module is discoverable from Home and PROTECT without becoming a primary lifecycle route.

## Task 6: Register the Hub and Auxiliary Surface

**Files:** routing doc, repo index, surfaces manifest, tests.

- [ ] Update the role of `dhf-best-care-recover.html` to Models & Patterns hub.
- [ ] Update the role of `dhf-data-business-value-explainer.html` to generic SAFE → TRUST page.
- [ ] Register `dhf-safe-data-ai-comparison.html` as an auxiliary human page.
- [ ] Set hub `public_nav` to `docs/index-zh.html` and comparison `public_nav` to `docs/dhf-best-care-recover.html`.
- [ ] Document the Chinese-first language boundary.
- [ ] Update `docs/LIFECYCLE_SKILL_ROUTING.md` to distinguish the generic SAFE page and auxiliary comparison.

Completion criterion: `check_surfaces.py --check-public-nav` reports no drift.

## Task 7: Verification

Run after the final material change, in order:

```bash
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
PYTHONDONTWRITEBYTECODE=1 python3 -c \
'import test_runner; test_runner.test_dhf_models_and_patterns_information_architecture(); test_runner.test_public_dhf_information_architecture(); test_runner.test_public_dhf_architecture_status_alignment()'
```

```bash
python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav
```

```bash
git diff --check
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py
```

Browser acceptance with a real browser:

- Chinese home, English home, Models Hub, SAFE → TRUST, Data/AI auxiliary, PROTECT EN/CN.
- Desktop and real 375px viewport.
- No whole-page overflow; comparison tables own local overflow.
- Hub-spoke links, language disclosure, one H1, reasonable H2/H3 hierarchy.
- Dark mode preserves distinction and readable contrast.
- Reduced motion leaves all content visible.

Every claimed gate records `command`, `exit_code`, `key_output`, and UTC `timestamp`.

## Stop Conditions

- Required write outside the exact write set.
- Data/AI comparison remains duplicated on the SAFE page.
- A model is added to primary top navigation.
- Status date or runtime claim changes.
- Hub-spoke links or language disclosure fail.
- Any focused, surface, full, or browser gate fails.

## Acceptance Criteria

- One Models & Patterns hub organizes the complete model family.
- SAFE → TRUST is generic and contains only one auxiliary Data/AI link.
- Data/AI comparison exists only on the auxiliary page.
- PROTECT is discoverable through the module without entering top navigation.
- Existing case pages remain unchanged and discoverable through the hub.
- No duplicate source of truth, new dependency, build pipeline, or runtime mutation.
- All gates pass with fresh receipts.
