---
name: arscontexta
description: Use when users want to build or evolve a persistent Markdown second-brain using Ars Contexta patterns, including domain derivation, self/notes/ops workspace scaffolding, 6R processing (record/reduce/reflect/reweave/verify/rethink), and ongoing quality maintenance for links, schema, and note health.
---

# Ars Contexta

## Overview

Apply Ars Contexta in Codex environments without Claude plugin commands. Derive a domain-specific knowledge system, scaffold file structure, and run the 6R operating loop with deterministic checks.

## Workflow

1. Scope the domain in one pass
- Capture domain, scale, operator model (human, agent, hybrid), and pain points.
- If key info is missing, assume: moderate scale, hybrid operator, explicit links.

2. Derive the architecture
- Use defaults from `references/arscontexta-playbook.md`.
- Resolve folder vocabulary first: `self/`, notes folder name, inbox folder name, `ops/`.
- Keep the three-space invariant even when names are customized.

3. Scaffold the workspace
- Run:
  ```bash
  ./scripts/bootstrap_arscontexta_vault.sh <root_dir> [notes_dir] [inbox_dir]
  ```
- This creates a minimal operational vault with derivation manifest, MOC, queue, health, and session paths.

4. Execute the 6R loop
- `record`: capture raw material into inbox.
- `reduce`: turn sources into compact notes with clear claims and links.
- `reflect`: add or strengthen cross-note links and MOCs.
- `reweave`: update old notes when new context changes interpretation.
- `verify`: check schema and graph health before claiming done.
- `rethink`: challenge assumptions and adjust architecture.

5. Enforce output contract
- Every completed cycle must produce:
  - changed files list
  - note/link deltas
  - unresolved tensions
  - next action recommendation

## Command Translation

Use this skill to map Ars Contexta slash commands into Codex tasks:

| Original command | Codex action |
|---|---|
| `/setup` | Derive config, run scaffold script, create manifest + initial MOC |
| `/reduce` | Transform one source into notes and link graph updates |
| `/reflect` | Analyze graph gaps and add connection notes |
| `/reweave` | Revisit older notes and patch with new links/context |
| `/verify` | Run checklist from playbook and report failures |
| `/health` | Summarize queue, sparse links, stale notes, schema gaps |
| `/next` | Recommend highest-value next operation |

## References

- Read `references/arscontexta-playbook.md` for defaults, templates, and verification checklist.
- Use `scripts/bootstrap_arscontexta_vault.sh` when project lacks the three-space structure.
