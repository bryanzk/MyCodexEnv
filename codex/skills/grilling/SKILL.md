---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
source: Adapted from mattpocock/skills v1.3.1 (MIT), commit 24fe0ef7737efae15c87225755e9f6f5965e4888
---


## Local document compatibility

Resolve the project's domain documents before following the filename references below or in bundled templates. Prefer an existing `GLOSSARY-MAP.md` (follow its links to the relevant context), then an existing root `GLOSSARY.md`. If neither exists, follow an existing `CONTEXT-MAP.md`, otherwise use the existing root `CONTEXT.md`. References below to `GLOSSARY.md` and `GLOSSARY-MAP.md` mean those selected project documents. Write terminology updates to the selected file; do not rename, overwrite, duplicate, or automatically merge existing documents. When neither convention exists, create `GLOSSARY.md` lazily as upstream describes. If both conventions exist, prefer GLOSSARY and leave CONTEXT intact. Creating new project files still requires the task's existing write authorization.

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Word each question so "yes" accepts your recommended answer.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.

## DHF Adaptation

Use this skill when `delivery-harness-framework` classifies a task as `requirements` or `planning` and the goal, scope, acceptance criteria, domain vocabulary, or architecture decision tree is still ambiguous.

Stop grilling only when the remaining facts can produce a requirements artifact that passes `scripts/harness_requirements.py validate PATH` and every acceptance criterion traces to a confirmed user answer or repo source.

When a term is settled during grilling, update the selected domain document immediately: use [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md) for GLOSSARY, or [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) for a retained CONTEXT document. Record resolved questions and answers in the requirements artifact's `open_questions_resolved` field.
