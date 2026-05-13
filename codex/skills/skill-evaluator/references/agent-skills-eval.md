# agent-skills-eval Usage

## When to Use

Use this runner when you want repeatable `with_skill` vs `without_skill` comparisons with judge-graded assertions and disk artifacts. It is especially useful once the skill already has a plausible `SKILL.md` and you need evidence of lift.

If the runtime cannot call external models or you do not have an API key, fall back to a manual paired test:

1. Run the same prompt with the skill.
2. Run the same prompt without the skill.
3. Grade both outputs against the same assertions.
4. Record whether the skill improved routing, file reads, or task quality.

## Minimal Folder Additions

Add an `evals/evals.json` file inside the skill directory.

Example:

```json
{
  "skill_name": "skill-evaluator",
  "evals": [
    {
      "id": "routing-positive",
      "name": "loads for skill review request",
      "prompt": "Review this agent skill and tell me whether it should exist, how to test it, and whether its description will over-trigger.",
      "expected_output": "The output decides whether the skill should exist and proposes routing and end-to-end evals.",
      "assertions": [
        "The output gives an existence verdict.",
        "The output proposes routing evals.",
        "The output proposes an end-to-end eval."
      ]
    }
  ]
}
```

If the runner supports attached files, add representative artifacts such as the target `SKILL.md`, eval fixtures, or sample outputs.

## CLI Pattern

```bash
npx agent-skills-eval /path/to/skills \
  --target gpt-4o-mini \
  --judge gpt-4o-mini \
  --baseline \
  --strict
```

Useful flags:

- `--baseline`: compare `with_skill` and `without_skill`
- `--strict`: fail fast on schema issues
- `--config agent-skills-eval.yaml`: move settings into a config file

## What the Runner Gives You

- Side-by-side `with_skill` and `without_skill` outputs
- Judge-graded assertions
- Timing and token metadata
- JSON artifacts and an HTML report

Treat this as evidence, not as the whole evaluation story. You still need routing and progressive-loading cases that reflect your actual runtime.

## How to Read Results

Interpret results in this order:

1. Did the skill load when it should?
2. Did it avoid loading when it should not?
3. Did it read the correct accessory files?
4. Did task quality improve against the same assertions?

If the skill only makes outputs longer, but not better against the rubric, count that as no lift.

## Common Failure Patterns

- The judge likes verbose answers, but the skill did not improve correctness.
- The eval only checks content quality and never checks routing.
- The prompt is so explicit that the baseline already passes.
- Assertions are vague and cannot distinguish lift from noise.
- The skill body is large, but the accessory files are never exercised.

## Manual Paired-Test Template

When the CLI is unavailable, capture this manually for each case:

- `prompt`
- `mode`: `with_skill` or `without_skill`
- `did_load`
- `did_read_accessory`
- `rubric_result`
- `notes`

Use the same rubric for both modes. Do not move the goalposts between baseline and skill runs.
