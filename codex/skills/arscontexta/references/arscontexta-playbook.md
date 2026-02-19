# Ars Contexta Playbook (Codex Edition)

## 1. Derivation Inputs

Collect these fields before scaffolding:

| Field | Required | Example |
|---|---|---|
| domain | yes | research notes, trading journal, personal reflection |
| operator | yes | human, agent, hybrid |
| scale | yes | low, medium, high |
| notes folder | yes | notes, ideas, claims, reflections |
| inbox folder | yes | inbox, journal, encounters |
| pain points | no | cannot find old notes, too much maintenance |

If user does not specify, use:
- operator: `hybrid`
- scale: `medium`
- notes folder: `notes`
- inbox folder: `inbox`

## 2. Architecture Defaults (8 Dimensions)

| Dimension | Default | Override signal |
|---|---|---|
| granularity | atomic | narrative-heavy writing prefers moderate/compound |
| organization | flat | very high scale with strict taxonomy prefers hierarchy |
| linking | explicit + implicit | low-complexity personal logging can use explicit only |
| processing | heavy | low-friction capture needs light |
| navigation | 3-tier MOC | tiny vault can use 2-tier |
| maintenance | condition-based | strict governance may require scheduled |
| schema density | moderate | compliance-heavy domains may need dense |
| automation | full where safe | fragile repo may use partial/manual |

## 3. Three-Space Invariant

Always preserve:
- `self/`: stable identity, principles, constraints.
- `<notes_dir>/`: knowledge graph and MOCs.
- `ops/`: queue, health, sessions, tensions, observations.

Folder names can change, role boundaries cannot.

## 4. Minimal Note Contract

Each durable note should include:

1. One clear claim or observation.
2. Source or provenance.
3. At least one outbound link when related context exists.
4. A short description line for scanability.

Template:

```markdown
---
title: "<title>"
type: note
description: "<one-line summary>"
source: "<url|book|conversation|self>"
---

# <title>

## Claim
<main claim>

## Evidence
<supporting facts>

## Links
- [[related-note-a]]
- [[related-note-b]]
```

## 5. 6R Execution Checklist

For each processing batch:

| Phase | Done when |
|---|---|
| record | raw items captured in inbox |
| reduce | new or updated notes contain claims and provenance |
| reflect | links/MOC updated for new notes |
| reweave | impacted historical notes updated |
| verify | schema/link/health checks reported |
| rethink | one assumption reviewed and decision recorded |

## 6. Verification Checklist

Run before completion:

1. Queue state is coherent (no impossible phase transitions).
2. Every new note has `description`.
3. New notes have at least one inbound or outbound relation unless isolated by design.
4. MOC index references new topical clusters.
5. `ops/tensions/` captures unresolved conflicts.
6. `ops/sessions/` stores this cycle summary.

## 7. Failure Patterns

| Pattern | Symptom | Correction |
|---|---|---|
| capture-only drift | inbox grows, notes do not | enforce reduce quota per cycle |
| over-atomic fragmentation | many tiny notes without synthesis | add reflect/reweave before new capture |
| stale structure | old MOCs stop routing traffic | run periodic MOC rebuild |
| fake verification | checks are declared but not run | require explicit evidence in session log |
