# Model Router Eval Matrix

## Purpose
Evaluate `codex/hooks/model_router.py` as a routing behavior, not as prose. The
router should recommend the cheapest model that still preserves quality for the
current prompt, phase, or subtask.

## Existence Verdict
- Keep as hook logic, not a skill: the output must be deterministic JSON that a
  runtime or wrapper can consume.
- Keep non-blocking: malformed or missing prompt payloads must exit 0 and
  return a balanced fallback.
- Keep quality-floor first: security, auth, migrations, deployment, production,
  destructive work, and review should not downshift.

## Routing Evals
| Case | Prompt Shape | Expected |
| --- | --- | --- |
| positive-simple | Translation, formatting, README sync, short harmless acknowledgements. | `gpt-5.4-mini`, low reasoning. |
| positive-medium | Bug fix, tests, refactor, scripts without high-risk terms. | `gpt-5.4`, medium reasoning. |
| positive-complex | Architecture, auth, security, migration, deployment, rollback, cross-module work. | `gpt-5.5`, high reasoning. |
| phase-review | Review current diff, regressions, or risk assessment. | `gpt-5.5`, high reasoning. |
| phase-validation | Run checks and summarize evidence without new judgment-heavy review. | `gpt-5.4-mini`, low reasoning. |

## Negative And Forbidden Upgrade Evals
| Case | Prompt Shape | Expected |
| --- | --- | --- |
| harmless-chat | `谢谢`, `ok`, `continue`. | Economy model; never frontier. |
| missing-prompt | Empty or malformed JSON. | Balanced fallback, low confidence, no block. |
| medium-not-frontier | Ordinary implementation without security/data/deploy signals. | Balanced model; no quality-floor reason. |
| simple-subtask-in-complex-parent | Complex parent prompt with a README/docs subtask. | Economy model and `subtask_downshift`. |

## Progressive Switching Evals
For a complex parent task, reroute at each durable stage boundary:
- `research`: economy when reading narrow docs or gathering file maps.
- `planning`: frontier for architecture and risk decisions.
- `development`: balanced for scoped implementation.
- `validation`: economy for command execution and evidence summaries.
- `review`: frontier for behavioral regression and risk review.

## End-To-End Assertions
- The router output includes `routing.model`, `routing.reasoning_effort`,
  `routing.complexity`, `routing.confidence`, and `routing.reasons`.
- The hook exits 0 for all normal and malformed payloads.
- Simple work should lower expected token cost compared with always using
  `gpt-5.5`.
- High-risk work should avoid false downshift even when the prompt is short.
- Complex tasks should support repeated routing by honoring `subtask` over the
  parent prompt.
