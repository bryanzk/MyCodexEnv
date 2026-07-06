# MyCodexEnv Context

Terminology contract for the MyCodexEnv Delivery Harness Framework runtime. This file is only a glossary: file locations belong in `docs/repo-index.md`, decisions belong in ADRs, and live state belongs in `docs/harness-state.md`.

## Language

**DHF**:
Delivery Harness Framework; the lifecycle framework that makes agent work recoverable, verifiable, and auditable.
_Avoid_: generic workflow, harness product

**phase**:
A normalized lifecycle stage such as `research`, `requirements`, `planning`, `development`, `validation`, `review`, `ship`, or `handoff`.
_Avoid_: mode, status, step

**lane**:
The execution risk path for a task, such as `local_dev`, `operator_live_demo`, or `customer_or_production`.
_Avoid_: environment, branch, phase

**evidence**:
A verification or decision record, usually a local JSONL event or a four-field record with `command`, `exit_code`, `key_output`, and `timestamp`.
_Avoid_: log dump, proof blob

**checkpoint**:
A repo-visible, recoverable state entry in `docs/harness-state.md` with phase, changed surfaces, verification, blockers, and next safe task.
_Avoid_: commit, backup, diary

**next safe task**:
The next concrete task a future session can execute without rereading chat history or guessing intent.
_Avoid_: TODO, idea, backlog item

**surface**:
A repo file or directory that defines, mirrors, or verifies a DHF runtime contract and is tracked in `docs/surfaces.json`.
_Avoid_: random doc, link, artifact

**write set**:
The exact files or directories a worker agent is allowed to modify for a scoped task.
_Avoid_: broad scope, ownership

**integrator**:
The primary agent that reviews worker output, resolves conflicts, updates global state, and owns final verification.
_Avoid_: coordinator, reviewer

**promotion**:
Moving a local or private finding into a durable repo surface such as a checkpoint, ADR, requirements artifact, or repo-index update.
_Avoid_: sync, copy, publish
