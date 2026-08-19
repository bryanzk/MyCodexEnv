# DHF Evolution IA Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the duplicate Chinese SAFE → TRUST page menu and give the English ShipQ development-history page the same seven-part information architecture as the clearer Chinese page.

**Architecture:** Keep the shared `dhf-nav` and page-local TOC components as the canonical navigation surfaces. Treat the Chinese development-history page as the structural source of truth while retaining the English page's visual language, six existing phase cards, and legacy fragments.

**Tech Stack:** Static HTML, vanilla CSS, Python standard-library contract tests, existing public-surface checker, real Chromium acceptance.

## Global Constraints

- Work only in `/private/tmp/MyCodexEnv-dhf-evolution-ia` on `codex/dhf-evolution-ia`.
- Do not introduce frameworks, dependencies, JavaScript routing, new public pages, runtime sync, deployment, or DNS changes.
- Preserve all current `data-dhf-status="2026-08-11"` values and same-language links.
- Preserve the English legacy fragments `overview`, `recover-position`, `route-lifecycle`, `bind-truth`, `completion`, `risk`, and `protect`.
- Use focused tests during iteration and run the repository gate once after the final material change.

---

### Task 1: Remove the duplicate SAFE → TRUST page menu

**Files:**
- Modify: `test_runner.py`
- Modify: `docs/dhf-data-business-value-explainer.html`

**Interfaces:**
- Consumes: the shared `dhf-nav`, `dhf-toc`, `dhf-has-toc`, and `dhf-col` page shell.
- Produces: one global navigation and exactly one page-local navigation for the Chinese SAFE → TRUST page.

- [ ] **Step 1: Write the failing navigation regression test**

Add and register this focused test:

```python
def test_dhf_value_page_has_single_local_navigation():
    text = (ROOT / "docs" / "dhf-data-business-value-explainer.html").read_text(encoding="utf-8")
    require(text.count('class="dhf-nav"') == 1, "Chinese SAFE → TRUST page global navigation count")
    require(text.count('class="dhf-toc"') == 1, "Chinese SAFE → TRUST page local navigation count")
    require('class="side-nav"' not in text, "Chinese SAFE → TRUST page retains legacy side navigation")
    require("querySelectorAll('.nav-link')" not in text,
            "Chinese SAFE → TRUST page retains legacy navigation observer")
    print("[PASS] Chinese SAFE → TRUST page has one local navigation")
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run:

```bash
python3 -c 'import test_runner; test_runner.test_dhf_value_page_has_single_local_navigation()'
```

Expected: failure because `side-nav` and its observer still exist.

- [ ] **Step 3: Remove the legacy navigation path**

In the Chinese SAFE → TRUST page:

- delete the complete navigation element whose class is `side-nav` and whose accessible label is `页面章节`;
- change the legacy `.shell` layout from a two-column grid to one content column;
- remove the final script that selects `.nav-link` and constructs an `IntersectionObserver`;
- leave the shared `dhf-toc` and all section IDs unchanged.

The resulting body hierarchy must retain `dhf-nav` first, followed by `dhf-has-toc`. The `dhf-has-toc` element must have exactly two element children in order: `nav.dhf-toc`, then `div.dhf-col`. Inside the content column, `.shell` must contain the existing `main[data-dhf-model-role="control-value"]` as its only navigation-level child.

- [ ] **Step 4: Run focused regression and surface checks**

Run:

```bash
python3 -c 'import test_runner; test_runner.test_dhf_value_page_has_single_local_navigation()'
python3 scripts/check_surfaces.py --check-public-nav
git diff --check
```

Expected: all pass.

- [ ] **Step 5: Commit the menu repair**

```bash
git add test_runner.py docs/dhf-data-business-value-explainer.html
git commit -m "fix: remove duplicate SAFE TRUST page menu"
```

---

### Task 2: Align the English ShipQ evolution information architecture

**Files:**
- Modify: `test_runner.py`
- Modify: `docs/dhf-shipq-development-history-en.html`

**Interfaces:**
- Consumes: the Chinese page's canonical section IDs and the English page's existing phase-card fragments.
- Produces: matching seven-section bilingual IA with preserved English deep links.

- [ ] **Step 1: Write the failing bilingual IA contract**

Add and register this focused test:

```python
def test_dhf_evolution_bilingual_information_architecture():
    expected_sections = ["thesis", "timeline", "business", "safe-trust", "matrix", "current", "evidence"]
    for name in ["dhf-shipq-development-history-en.html", "dhf-shipq-development-history.html"]:
        text = (ROOT / "docs" / name).read_text(encoding="utf-8")
        require_in_order(text, [f'id="{section}"' for section in expected_sections],
                         f"{name} canonical evolution section order")
    english = (ROOT / "docs" / "dhf-shipq-development-history-en.html").read_text(encoding="utf-8")
    for fragment in ["overview", "recover-position", "route-lifecycle", "bind-truth", "completion", "risk", "protect"]:
        require(english.count(f'id="{fragment}"') == 1,
                f"English evolution page must preserve legacy fragment: {fragment}")
    print("[PASS] bilingual DHF evolution information architecture")
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run:

```bash
python3 -c 'import test_runner; test_runner.test_dhf_evolution_bilingual_information_architecture()'
```

Expected: failure because the English page lacks `thesis`, `timeline`, `business`, `safe-trust`, `matrix`, `current`, and `evidence` parity.

- [ ] **Step 3: Rebuild the English page around the seven canonical sections**

Keep the existing English top navigation, language switch, palette, and memory cue. Replace the current single timeline-only narrative with these exact top-level landmarks:

| Element | Canonical ID | Visible heading |
|---|---|---|
| `header.hero` | `thesis` | From business blockage to governed enforcement |
| timeline section heading container | `timeline` | Six stages of evolution: BRIDGE |
| business section heading container | `business` | Why DHF follows ShipQ business boundaries |
| control section heading container | `safe-trust` | SAFE controls the transition; TRUST tests the value |
| value section heading container | `matrix` | Pain removed, control added, evidence required |
| maturity section heading container | `current` | Current maturity and the next proof boundary |
| evidence section heading container | `evidence` | Evidence and claim boundary |

Use these content decisions:

- Thesis: DHF grew from delivery risk rather than from a generic process template.
- Timeline: present CAP as Continuity, Accuracy, Permission; retain the six current English phase cards as the BRIDGE path and retain their six legacy IDs.
- Business pressures: cover Gmail intake continuity, workbook-to-quote accuracy, and owner-controlled external effects.
- SAFE × TRUST: explain SAFE as the state-transition control and TRUST as the value lens; neither is a lifecycle phase.
- Value matrix: map the six BRIDGE stages to the pain removed, control added, and observable evidence required.
- Current maturity: separate current recoverable/verified/auditable capability from unproven full Level 2 automation and customer outcomes.
- Evidence boundary: retain historical/source evidence without upgrading it to current runtime, production enforcement, adoption, or commercial proof.

Update the English page-local TOC to exactly:

```html
<a href="#thesis">Thesis</a>
<a href="#timeline">Six-stage evolution</a>
<a href="#business">ShipQ business pressures</a>
<a href="#safe-trust">SAFE × TRUST</a>
<a href="#matrix">Value matrix</a>
<a href="#current">Current maturity</a>
<a href="#evidence">Evidence boundary</a>
```

- [ ] **Step 4: Run focused IA and memory contracts**

Run:

```bash
python3 - <<'PY'
import test_runner
test_runner.test_dhf_evolution_bilingual_information_architecture()
test_runner.test_dhf_evidence_memory_keyword_contract()
test_runner.test_dhf_value_evidence_information_architecture()
PY
python3 scripts/check_surfaces.py --check-public-nav
git diff --check
```

Expected: all pass.

- [ ] **Step 5: Run real-browser acceptance**

For the repaired SAFE → TRUST page and both development-history pages, verify at 375px, 768px, and 1440px:

- exactly one global navigation and one visible page-local navigation;
- no document-level horizontal overflow;
- all seven canonical evolution fragments resolve;
- Chinese ↔ English links are bidirectional;
- dark mode and reduced motion remain usable.

- [ ] **Step 6: Run the final repository gate once**

```bash
python3 test_runner.py
```

Expected: all registered tests pass.

- [ ] **Step 7: Commit the English IA alignment**

```bash
git add test_runner.py docs/dhf-shipq-development-history-en.html
git commit -m "docs: align English DHF evolution IA"
```

## Self-Review Result

- Spec coverage: both requested changes and their browser/test boundaries are represented.
- Deferred-marker scan: no incomplete implementation markers.
- Interface consistency: canonical IDs and legacy fragments are spelled consistently across tasks and tests.
