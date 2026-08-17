# DHF Website Information Architecture Modification Plan

> **For agentic workers:** Execute this plan task by task. Preserve existing dirty-file ownership, use test-first changes for public contracts, and stop before commit, push, deployment, DNS, or runtime synchronization unless separately authorized.

**Goal:** Reorganize the DHF public site around finite context, just-in-time information, governed action, feedback, recovery, and clear source/runtime/publication boundaries.

**Architecture:** Keep the existing flat static-HTML GitHub Pages site and visual system. Simplify the global navigation and homepage, make Context Engineering the conceptual bridge between Beginner and Lifecycle, move operational detail to its existing specialist pages, and keep current-state proof in the canonical status pages.

**Tech Stack:** Static HTML/CSS, Python `test_runner.py`, `scripts/check_surfaces.py`, GitHub Pages.

## Global Constraints

- Work only in `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv` after confirming checkout identity and dirty ownership.
- Existing modified and untracked DHF files are user-owned; merge into them without reset, stash, overwrite, or cross-worktree copying.
- Do not add a frontend framework, build pipeline, directory router, dropdown system, or new dependency.
- Preserve the existing visual language and shared `docs/dhf-site-status.css` unless browser verification proves one minimal CSS fix is required.
- Keep English and Chinese information structures semantically aligned, with one documented exception: Skill Routing exists only in English (see Secondary engineering resources).
- Treat `docs/index.html` as the canonical English root, `docs/index-en.html` as the compatibility copy, and `docs/index-zh.html` as the Chinese root.
- Keep repository source, local runtime, public documentation, production enforcement, adoption, and roadmap status separate.
- Do not change the public status date or runtime claims without fresh status evidence.
- The Claude artifact is an information-architecture lens, not proof of current DHF or Claude product behavior.
- This plan does not authorize commit, push, deployment, Cloudflare/DNS changes, or runtime synchronization.

---

## 1. Target Information Architecture

### Primary navigation

All current public pages use this compact navigation:

```text
Home
Beginner
Context
Lifecycle
Governance
Status
中文 / English
```

Chinese labels:

```text
首页
新手指南
上下文工程
生命周期
治理判定
架构状态
English
```

Move these pages out of primary navigation and into the Engineering Resources section:

- Skill Routing
- Workflow Skills
- PROTECT
- PM & FDE
- Engineering Notes
- Written Spec

Do not create group landing pages or dropdown navigation.

### Recommended learning path

```text
Beginner
→ Context Engineering
→ Lifecycle
→ Governance
→ Skill Routing
→ Architecture Status
```

The pages answer, in order:

1. Why DHF exists.
2. What information an agent receives and how it is governed.
3. When the information enters the delivery lifecycle.
4. What actions the information permits.
5. Which skill or helper owns the work.
6. What is currently implemented, active, or published.

---

## 2. Homepage Target Structure

Reduce the current homepage from a capability catalog to five major sections.

### Section 1: Hero

Keep the headline:

> From ambiguous requests to verifiable delivery.

Chinese:

> 从模糊请求到可验证交付。

Use this concise positioning:

> DHF gives agents the right, fresh, authorized context at the right delivery stage, then closes the work with checkable evidence.

Chinese:

> DHF 让智能体在正确阶段获得正确、最新且获准使用的上下文，并用可核对证据完成交付。

Keep exactly three primary calls to action:

- Read the Beginner Guide
- Understand Context Engineering
- Check Current Status

Do not explain ADRs, hooks, phase capability matrices, transition stores, or runtime manifests in the hero.

### Section 2: Core context supply chain

Show one model, with one sentence per step:

```text
Trusted Sources
→ Session Bearing
→ Just-in-time Shaping
→ Permission Decision
→ Execution Feedback
→ Checkpoint / Recovery
```

This six-step homepage chain is the **simplified public view** of the canonical seven-step chain owned by the Context Engineering page (Section 4, Chapter 3). The mapping between the two is fixed:

| Homepage step | Canonical Context Engineering steps |
|---|---|
| Trusted Sources | Trusted Sources |
| Session Bearing | Session Bearing |
| Just-in-time Shaping | Prompt Shaping + Context Pressure |
| Permission Decision | PreTool Guard |
| Execution Feedback | PostTool Evidence |
| Checkpoint / Recovery | Checkpoint |

Rules:

- The supply chain appears on the site in exactly these two forms; no page may introduce a third variant or rename a step.
- The homepage section links to the Context Engineering page as the single authoritative explanation, consistent with the migration-map rule "keep one authoritative explanation and link to it."

### Section 3: Learn the framework

Use four ordered cards:

1. Beginner
2. Context Engineering
3. Lifecycle
4. Governance

Skill Routing becomes an operational resource, not an introductory step.

### Section 4: Choose by goal

Offer only three paths:

- I am learning DHF for the first time.
- I am integrating DHF into an engineering workflow.
- I am checking implementation status and evidence.

Each path contains no more than three links.

### Section 5: Status boundary and engineering resources

Show only these independent status categories:

- Repository source
- Local runtime
- Public documentation
- Production enforcement

Adoption and roadmap remain separate status boundaries (per Global Constraints) but are intentionally absent from the homepage categories:

- **Adoption** evidence is owned by Architecture Status.
- **Roadmap** items are owned by Context Engineering Chapter 6 as `data-capability-state="planned"` entries.

Architecture Status stays the only current-state proof surface for both.

Move dates, file counts, test counts, parity receipts, and version details to Architecture Status.

List the secondary engineering resources once at the bottom of the page.

---

## 3. Homepage Content Migration Map

| Current homepage content | Authoritative destination |
|---|---|
| Current Routing Contract | Lifecycle |
| Local/demo/production lanes | Governance and PM & FDE |
| Architecture checkpoint | Governance |
| Committee loops | Workflow Skills |
| Compaction governance | Context Engineering and Engineering Notes |
| Rollback prevention | Engineering Notes and Architecture Status |
| Guards that actually block | Governance and PROTECT |
| Scoped governance | Governance |
| Runtime promotion metrics | Architecture Status |
| Capability model | Governance |
| Human in the loop | Governance and PM & FDE |
| Deterministic retries | Engineering Notes |
| Memory lifecycle | Context Engineering |
| Evidence trail | Context Engineering and Architecture Status |
| Agent failure modes | Beginner; retain three representative examples |
| Page and asset catalog | Engineering Resources at the bottom of Home |

Do not copy full paragraphs between pages. Keep one authoritative explanation and link to it.

---

## 4. Context Engineering Page Specification

Continue editing the existing files; do not recreate or overwrite them:

- `docs/dhf-context-engineering-en.html`
- `docs/dhf-context-engineering-cn.html`

### Chapter 1: The finite box

Explain that:

- Context capacity is finite.
- Upfront content consumes task workspace.
- Irrelevant information reduces retrieval and decision quality.
- The governing principle is: do not pay context cost for information the current task does not need.

### Chapter 2: Three required inputs

- **Access:** what the agent can reach.
- **Institutional Knowledge:** what the organization knows that the model does not naturally know.
- **Tooling:** how the right information enters at the right time.

### Chapter 3: The governed supply chain

```text
Trusted Sources
→ Session Bearing
→ Prompt Shaping
→ Context Pressure
→ PreTool Guard
→ PostTool Evidence
→ Checkpoint
```

This seven-step chain is the **canonical model**. The homepage shows only the simplified six-step view defined in Section 2, under the fixed mapping declared there. Any change to step names must update both forms, the mapping table, and the IA contract test together.

### Chapter 4: Primitive selection matrix

| Primitive | Use when | Context cost | DHF role |
|---|---|---:|---|
| Hook | An event should decide whether information is relevant | Pay only when relevant | Guard, Evidence, Bearing |
| Skill | The current task needs complete specialist guidance | Description stays resident; body loads on demand | Specialist workflow |
| Sub-agent | Work needs an independent reasoning window | Parent receives a compact result | Isolated research or review |
| MCP/Tool | Work needs an external capability | Names and schemas consume context | Permission-governed execution |

Recommended order:

```text
Existing CLI or script → Skill
Event-driven feedback → Hook
Independent reasoning → Sub-agent
Cross-client external capability → MCP
```

### Chapter 5: Memory is not governed context

- **Memory:** model-curated historical clues.
- **Context:** task-relevant information selected by source, timing, freshness, and permission.
- **Checkpoint:** durable, recoverable task state.
- **Evidence:** the recorded outcome of actual execution.

Chat and memory can provide search clues but cannot independently authorize action.

### Chapter 6: Current capabilities and roadmap

Use explicit markup:

```html
data-capability-state="current"
data-capability-state="planned"
```

Current:

- source ordering
- Session Bearing
- Prompt Shaping
- PreTool Guard
- PostTool Evidence
- Checkpoint / Recovery

Planned:

- tighter immediate feedback loops
- context budgets
- access catalogs
- fleet and attention views

Planned content must not use current-state wording.

---

## 5. Exact Write Set

### Core entrances

- Modify: `docs/index.html`
- Modify: `docs/index-en.html`
- Modify: `docs/index-zh.html`

Responsibilities:

- five-section homepage
- compact primary navigation
- three goal-based paths
- engineering-resource demotion
- semantic equivalence between `index.html` and `index-en.html`

### Concept and learning path

- Modify: `docs/dhf-context-engineering-en.html`
- Modify: `docs/dhf-context-engineering-cn.html`
- Modify: `docs/delivery-harness-beginner-guide-en.html`
- Modify: `docs/delivery-harness-beginner-guide-cn.html`
- Modify: `docs/project-lifecycle-harness-flow-en.html`
- Modify: `docs/project-lifecycle-harness-flow-cn.html`
- Modify: `docs/dhf-governance-decision-flow-en.html`
- Modify: `docs/dhf-governance-decision-flow-cn.html`

Required relationship:

```text
Beginner ↔ Context ↔ Lifecycle ↔ Governance
```

### Governance and status boundary

- Modify: `docs/dhf-protect-seven-components-en.html`
- Modify: `docs/dhf-protect-seven-components-cn.html`
- Modify: `docs/dhf-architecture-status-en.html`
- Modify: `docs/dhf-architecture-status-cn.html`

Responsibilities:

- Governance owns permissions, lanes, guards, and human approval.
- PROTECT owns protected runtime components.
- Architecture Status owns current dates, parity evidence, test counts, publication status, and adoption evidence.
- Concept pages link to Status rather than copying status proof.

### Secondary engineering resources

Update primary navigation only; do not rewrite body content unless required by the migration map:

- `docs/project-lifecycle-harness-flow-skills-en-status-style.html`
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`
- `docs/dhf-workflow-skills-en.html`
- `docs/dhf-workflow-skills-cn.html`
- `docs/dhf-for-product-and-field-en.html`
- `docs/dhf-for-product-and-field-cn.html`
- `docs/dhf-engineering-notes-en.html`
- `docs/dhf-engineering-notes-cn.html`
- `docs/lifecycle-skill-routing-en.html`

**Skill Routing bilingual exception (verified 2026-08-17):** `docs/lifecycle-skill-routing-en.html` has no Chinese twin; only the English page exists. Handle it as a documented exception rather than silent asymmetry:

- Wherever Chinese pages link to Skill Routing (Engineering Resources, and the operational next step after 治理判定), label the link 「技能路由（英文）」so Chinese readers know the destination is English-only.
- Do not create a Chinese Skill Routing page under this plan; that is separately scoped follow-up work.
- The IA contract test must not require a Chinese Skill Routing surface.

### Index and contracts

- Modify: `docs/repo-index.md`
- Modify: `docs/surfaces.json`
- Modify: `test_runner.py`

### Default no-write set

- Do not modify: `docs/dhf-site-status.css`
- Do not modify: `docs/CNAME`
- Do not modify: `README.md`
- Do not modify archived page bodies
- Do not modify runtime, hooks, skills, or any `codex/` file

Allow one minimal `docs/dhf-site-status.css` change only if browser verification proves the compact navigation still fails.

---

## 6. Implementation Tasks

### Task 0: Ownership and baseline gate

**Files:** Read-only inspection of the repository and current dirty diff.

- [ ] Confirm checkout identity:

```bash
git rev-parse --show-toplevel
```

Expected: `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv`.

- [ ] Read current ownership state:

```bash
git status --short
git diff --name-status
git diff -- docs test_runner.py
python3 scripts/harness_recover.py --repo-root "$(pwd)" --boundary --json
```

- [ ] Confirm that existing Context pages and public-site diffs are continued in place.

Stop if ownership is unresolved. Do not reset, stash, overwrite, or copy from another worktree.

### Task 1: Add a failing information-architecture contract

**Files:**

- Modify: `test_runner.py`

- [ ] Add `test_public_dhf_information_architecture()` with assertions for:

```python
def test_public_dhf_information_architecture():
    # Canonical home pages expose the same compact primary navigation.
    # Home pages contain no more than six H2 sections.
    # Exactly three primary CTAs exist.
    # Context precedes Lifecycle in the learning path.
    # Engineering resources are absent from primary navigation.
    # Context pages expose finite-box, primitive, memory, and roadmap boundaries.
    # The supply chain appears only in its two declared forms:
    # the canonical seven-step Context chain and the simplified homepage view.
    pass
```

- [ ] Assert primary navigation contains Home, Beginner, Context, Lifecycle, Governance, and Status.
- [ ] Assert Engineering Notes, Workflow Skills, and Written Spec are not in primary navigation.
- [ ] Assert each canonical homepage contains no more than six `<h2` elements.
- [ ] Assert each homepage contains exactly three primary CTAs.
- [ ] Assert the learning order is Beginner → Context → Lifecycle → Governance.
- [ ] Assert both Context pages contain finite box, Access, Institutional Knowledge, Tooling, Hook, Skill, Sub-agent, MCP, memory boundary, current, and planned concepts.
- [ ] Assert each homepage supply-chain section uses exactly the six simplified step labels from Section 2 and links to the Context Engineering page.
- [ ] Assert both Context pages contain the seven canonical step labels from Chapter 3.
- [ ] Assert no canonical page renders a supply-chain variant other than these two forms (guard the fixed homepage↔canonical mapping).

- [ ] Run the RED gate:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c \
'import test_runner; test_runner.test_public_dhf_information_architecture()'
```

Expected: FAIL because the current homepage and navigation still violate the target IA.

### Task 2: Finish the bilingual Context Engineering pages

**Files:**

- Modify: `docs/dhf-context-engineering-en.html`
- Modify: `docs/dhf-context-engineering-cn.html`

- [ ] Insert the finite-box section before the source taxonomy.
- [ ] Add Access, Institutional Knowledge, and Tooling as the three inputs.
- [ ] Add the primitive selection matrix.
- [ ] Add the Memory/Context/Checkpoint/Evidence distinction.
- [ ] Keep current and planned capabilities visibly separate.
- [ ] Add canonical Architecture Status links.
- [ ] Preserve reciprocal language links.

Run the focused contract. Context assertions should pass; homepage assertions may remain RED.

### Task 3: Simplify the three homepages

**Files:**

- Modify: `docs/index.html`
- Modify: `docs/index-en.html`
- Modify: `docs/index-zh.html`

- [ ] Replace the current primary nav with the compact nav.
- [ ] Replace the hero lead with the concise positioning.
- [ ] Keep exactly three primary CTAs.
- [ ] Replace the capability catalog with the single context supply chain.
- [ ] Replace the current learning sequence with Beginner → Context → Lifecycle → Governance.
- [ ] Add the three goal-based paths.
- [ ] Move implementation detail according to the migration map.
- [ ] Keep one bottom Engineering Resources section.
- [ ] Keep `index.html` and `index-en.html` semantically identical.

Run the focused IA test and expect GREEN.

### Task 4: Align the learning-path pages

**Files:**

- Modify the eight Beginner, Context, Lifecycle, and Governance pages listed above.

- [ ] Beginner next page is Context.
- [ ] Context previous/next pages are Beginner and Lifecycle.
- [ ] Lifecycle previous/next pages are Context and Governance.
- [ ] Governance previous page is Lifecycle; Skill Routing is the operational next step.
- [ ] On the Chinese Governance page, the Skill Routing next step links to `docs/lifecycle-skill-routing-en.html` with the 「技能路由（英文）」label (bilingual exception above).
- [ ] Each page has one dominant next action; secondary resources stay at the end.

### Task 5: Normalize navigation across current pages

**Files:** All current English and Chinese pages in the exact write set.

- [ ] Update English pages mechanically.
- [ ] Update Chinese pages mechanically.
- [ ] Preserve the correct `aria-current="page"` on each page.
- [ ] Preserve each language twin.
- [ ] Leave archived pages out of the canonical navigation refactor; give them only a clear link back to the current page.

### Task 6: Update the surface inventory and repository map

**Files:**

- Modify: `docs/surfaces.json`
- Modify: `docs/repo-index.md`

- [ ] Context EN `public_nav` points only to `docs/index.html`.
- [ ] Context CN `public_nav` points only to `docs/index-zh.html`.
- [ ] Document the new learning order.
- [ ] Document Context Engineering as the conceptual bridge.
- [ ] Document Architecture Status as the only current-state proof surface.

### Task 7: Run the full verification gate

- [ ] Focused public-contract gate:

```bash
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
PYTHONDONTWRITEBYTECODE=1 python3 -c \
'import test_runner; test_runner.test_public_dhf_information_architecture(); test_runner.test_public_dhf_architecture_status_alignment()'
```

- [ ] Public surface gate:

```bash
python3 scripts/check_surfaces.py \
  --repo-root "$(pwd)" \
  --check-public-nav
```

- [ ] Diff hygiene:

```bash
git diff --check
```

- [ ] After the final material change, run the repository gate exactly once:

```bash
python3 test_runner.py
```

Record `command`, `exit_code`, `key_output`, and `timestamp` for every claimed gate.

---

## 7. Browser Acceptance

### Desktop pages

- English home
- Chinese home
- EN/CN Context Engineering
- Beginner
- Lifecycle
- Governance
- Architecture Status

### 375px mobile checks

- Primary navigation scrolls or wraps without whole-page overflow.
- Large headings do not obscure content.
- The primitive matrix remains readable.
- The status bar does not crowd out the main CTA.
- No page has `scrollWidth > clientWidth` unless a deliberate local scroller owns the overflow.

### Interaction and semantics

- Skip links work.
- Keyboard focus reaches all navigation items.
- `aria-current` is correct.
- Language twins resolve correctly.
- Each page has one `H1`, a small number of section `H2`s, and card `H3`s.
- Content remains visible with reduced motion.
- Dark mode distinguishes Current and Planned states.

---

## 8. Publication Boundary

This plan does not authorize publication.

After separate commit/push/deploy authorization:

1. Reconfirm the exact write set and dirty ownership.
2. Rerun the complete gate with fresh receipts.
3. Stage only the approved plan files.
4. Use one bounded documentation commit:

```text
docs: simplify DHF public information architecture
```

5. Push the approved branch.
6. Wait for GitHub Pages completion.
7. Read back:
   - `https://deliveryharness.com/`
   - `https://deliveryharness.com/index-zh.html`
   - `https://deliveryharness.com/dhf-context-engineering-en.html`
   - `https://deliveryharness.com/dhf-context-engineering-cn.html`
   - `https://deliveryharness.com/dhf-architecture-status-en.html`
   - `https://deliveryharness.com/dhf-architecture-status-cn.html`

HTTP 200 proves reachability only; it does not prove runtime parity, production enforcement, or user adoption.

---

## 9. Acceptance Criteria

- Primary navigation has no more than six content entries.
- Home has no more than six `H2` sections.
- Home has exactly three primary CTAs.
- Home no longer acts as a release log or capability catalog.
- Context Engineering is a primary entry.
- Beginner → Context → Lifecycle → Governance is consistent in both languages.
- Current capabilities and planned roadmap are visibly distinct.
- Architecture Status is the sole current-state proof surface, including for adoption evidence.
- The context supply chain exists in exactly two forms — the canonical seven-step chain on Context Engineering and the simplified six-step homepage view — under the fixed mapping in Section 2, enforced by the IA contract test.
- English and Chinese Context pages are structurally equivalent.
- The English-only Skill Routing page is linked from Chinese pages with the explicit 「技能路由（英文）」label.
- No new dependency, framework, build pipeline, or routing system is introduced.
- Focused tests, surface checks, full repository tests, and browser acceptance pass with fresh receipts.
- Existing dirty changes are preserved.
- Commit, push, deployment, and runtime synchronization remain separately authorized actions.

## 10. Known Risks

- The main worktree already contains overlapping uncommitted public-site work; ownership readback is mandatory.
- Navigation is duplicated across static HTML files, so drift must be guarded by tests.
- `index.html` and `index-en.html` can silently diverge without an explicit parity assertion.
- Public status language can become stale; conceptual pages must not copy current-state metrics.
- The prior mobile viewport audit was incomplete; the implementation must perform a fresh real 375px check.
- The Claude artifact is user-generated and unverified; use its abstractions for framing only.
- The supply chain is rendered in two forms (homepage simplified view, Context canonical chain); without the fixed mapping and its test assertions the two will drift into a third variant.
- Skill Routing has no Chinese twin; without the explicit 「技能路由（英文）」label, Chinese readers hit an unannounced language switch at the end of the learning path.
