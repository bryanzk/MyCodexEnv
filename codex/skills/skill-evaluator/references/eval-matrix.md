# Skill Evaluation Matrix

## Purpose

Use this matrix to evaluate a skill as a behavior change, not as prose quality. A good skill proves four things:

1. It should exist.
2. It loads when it should.
3. It does not load when it should not.
4. It improves task completion after loading.

## 1. Existence Check

Reject or narrow the skill if any of these are true:

- A one-line prompt or normal documentation would solve the problem.
- The content changes faster than the team can maintain it.
- The body mainly lists obvious commands or repeats global instructions.
- Success cannot be evaluated with observable outputs or behaviors.

Accept the skill when:

- The model needs durable domain knowledge, judgment, taste, boundaries, or non-obvious gotchas.
- Consistency matters across runs.
- The agent is wrong without special context.

## 2. Routing Evals

Design routing evals before body edits. These evals answer: should the skill load?

### Positive Routing

Use prompts that clearly express the target intent in real user language.

- Source prompts from production queries, support logs, or known failures.
- Prefer 3-10 hero prompts over dozens of weak prompts.
- Include synonyms users actually say, not just your internal wording.

### Negative Routing

Use adjacent but distinct prompts where another skill or no skill should win.

Examples:

- Similar domain, different tool
- Same noun, different verb
- Same workflow family, different boundary

### Forbidden Loads

Add prompts where loading this skill would be actively harmful.

Examples:

- Generic requests that should stay on base behavior
- Requests owned by a neighbor skill
- Requests where the skill's assumptions are false

## 3. Progressive Loading Evals

If the skill has `references/`, `scripts/`, `assets/`, or subskills, test whether the agent reads the right accessory only when needed.

For each accessory file, define:

- Trigger: the condition that should cause the read
- Evidence: what output or trace proves the file was read
- Non-trigger: a nearby case where reading the file would be unnecessary

Examples:

- Read `references/api-errors.md` only after a non-200 response
- Read `assets/report-template.md` only when the task requires the report format
- Run a deterministic script only when reconstructing the logic would be wasteful

## 4. End-to-End Quality Evals

After routing is correct, test whether the loaded skill improves the actual task.

Minimum set:

- A representative happy-path task
- A known failure case that motivated the skill
- A boundary case where the agent must avoid over-applying the skill

Judge against concrete assertions, not vague style preferences.

Good assertions:

- "The response states that the skill is unnecessary and recommends a prompt tweak."
- "The output identifies at least one forbidden-load prompt for the description."
- "The plan includes routing, progressive-loading, and end-to-end evals."

Weak assertions:

- "The output is good."
- "The explanation is clear."

## 5. Cross-Model and Regression Checks

If the runtime supports multiple orchestration models, rerun routing and domain evals across them. Skills often regress differently across model families.

At minimum, check:

- One high-capability model
- One cheaper or smaller model
- The model family used most often in production

If `description` changes, rerun routing evals first. Description edits are high-risk because they can break neighboring skills without touching their files.

## 6. Evidence to Capture

For every claim that a skill is good, capture:

- Prompt
- Whether the skill loaded
- Whether accessory files were read
- Output with skill
- Output without skill
- Judge result or manual rubric result
- The smallest edit that would improve the next run

## 7. Default Deliverable Format

When evaluating a skill, return results in this shape:

1. `Existence verdict`
2. `Routing findings`
3. `Progressive-loading findings`
4. `End-to-end findings`
5. `Next edits`

Keep findings specific. Prefer "description misses the user's verb 'babysit'" over "routing could improve."
