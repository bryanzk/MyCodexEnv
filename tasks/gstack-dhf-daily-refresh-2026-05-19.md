# Gstack & DHF Daily Refresh Report

Date: 2026-05-19
Automation ID: `gstack-dhf-daily-refresh`

## Summary

- Checked the vendored gstack baseline in this repo: `codex/skills/gstack/VERSION` is `0.18.3.0`.
- Checked upstream GitHub `garrytan/gstack` on 2026-05-19: `VERSION` is `1.40.0.0`.
- Sampled current upstream workflow skill surfaces that Delivery Harness Framework routes into:
  `office-hours`, `plan-ceo-review`, `plan-eng-review`, `plan-design-review`,
  `qa`, `review`, `ship`, `document-release`, `retro`, `learn`, `gstack-upgrade`.
- Updated local DHF routing surfaces so they reflect the latest observed upstream workflow posture.

## Key Upstream Changes Observed

1. Planning and review skills are more opinionated than the vendored 0.18.x set.
   `plan-eng-review` now explicitly checks search/built-in alternatives, completeness vs shortcuts, and distribution/publish paths for new artifacts.

2. UI planning is now mockup-first, not prose-first.
   `plan-design-review` treats visual mockup generation as the default when UI exists and the designer is available.

3. QA and review flows are more fix-first.
   `qa` couples browser testing with iterative bug fixing and regression evidence.
   `review` is oriented around auto-fixing low-risk findings before escalating.

4. Ship and docs workflows widened.
   `ship` now bakes in coverage audit, plan-completion audit, documentation sync, and stricter PR title/version hygiene.
   `document-release` now includes a Diataxis-style coverage map and documentation-debt checks.

5. Retros and learnings are broader.
   `retro` now covers team-aware and global/project-spanning analytics.
   `learn` now supports explicit search/export/prune/stats/add management patterns.

## Local Changes Made

### Delivery Harness Framework

- Updated `codex/skills/delivery-harness-framework/SKILL.md` to reflect that gstack now owns:
  - design review plus mockup generation
  - fix-first diff review
  - distribution-aware release workflows
  - documentation-debt aware release docs
  - retrospective analytics and learnings management

- Tightened stage-routing guidance:
  - `Product boundary` now prefers `gstack-office-hours` when the problem statement is still fluid.
  - `Engineering plan` now explicitly checks distribution/publish paths for new artifacts.
  - `Design plan` now prefers mockup-first review when visual tooling exists.
  - `Review` now notes fix-first review posture.
  - `Documentation/release notes` now treats coverage and diagram drift as first-class debt.

### Lifecycle Documentation

- Updated `docs/LIFECYCLE_SKILL_ROUTING.md` so the public routing map matches the current observed upstream workflow semantics for:
  - `gstack-plan-eng-review`
  - `gstack-plan-design-review`
  - `gstack-qa`
  - `gstack-review`
  - `gstack-ship`
  - `gstack-document-release`
  - `skill-evaluator`

## Skill Evaluator Review

### Existence Verdict

Yes. `delivery-harness-framework` should continue to exist as a separate skill.
Upstream gstack is getting more specialized, not less. DHF still provides the generic cross-repo lifecycle routing, runtime probing, evidence gates, and helper selection that gstack does not own.

### Routing Review

- Improved:
  DHF now explicitly distinguishes:
  - problem discovery vs product review
  - prose-only design critique vs mockup-first design review
  - generic review vs fix-first near-landing review
  - generic docs update vs documentation-debt aware release docs

- Residual risk:
  The vendored gstack source in this repo is still `0.18.3.0`, so generated local skill text outside DHF may still lag current upstream behavior.

### Eval Plan

- Positive route checks:
  - ambiguous product idea -> `gstack-office-hours`
  - complex engineering plan with new artifact -> `gstack-plan-eng-review`
  - UI-heavy plan with visual tooling -> `gstack-plan-design-review`
  - near-landing diff review -> `gstack-review`
  - shipped code with doc drift -> `gstack-document-release`
  - time-windowed retrospective -> `gstack-retro`

- Negative / forbidden-load checks:
  - do not route ordinary repo startup to gstack when DHF/helper probes are the right first step
  - do not route read-only QA reporting to `gstack-qa` when `gstack-qa-only` fits better
  - do not treat `gstack-review` as the generic answer for all review asks when a committee loop is explicitly requested

### Evidence Summary

- Evidence for change:
  Upstream skill descriptions and templates show richer routing semantics than this repo's DHF docs previously documented.
- Expected lift:
  Future DHF routing decisions should now better match current upstream gstack capabilities without overfitting repo-specific commands.

## Constraints / Follow-up

- This run did not perform a full vendored source sync of `codex/skills/gstack/*`.
- Reason:
  The shell environment cannot resolve GitHub hosts directly, and this session does not expose a bulk repo archive import path for safely replacing the full gstack vendor tree.
- Safe next step for a future refresh:
  add a dedicated sync path that can import upstream `garrytan/gstack` source snapshots wholesale, then run `bun run gen:skill-docs --host all` and repo verification.
