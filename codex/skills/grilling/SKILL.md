---
name: grilling
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
source: Adapted from mattpocock/skills (MIT), commit 694fa30
---

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

## DHF Adaptation

Use this skill when `delivery-harness-framework` classifies a task as `requirements` or `planning` and the goal, scope, acceptance criteria, domain vocabulary, or architecture decision tree is still ambiguous.

Stop grilling only when the remaining facts can produce a requirements artifact that passes `scripts/harness_requirements.py validate PATH` and every acceptance criterion traces to a confirmed user answer or repo source.

When a term is settled during grilling, update `CONTEXT.md` immediately using the local context format. Record resolved questions and answers in the requirements artifact's `open_questions_resolved` field.
