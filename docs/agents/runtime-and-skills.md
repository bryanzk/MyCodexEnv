# Runtime and skill changes

## Runtime boundary

- Before changing Codex runtime, skills, or global configuration, check `git status` and identify the exact repository source and runtime target.
- Treat repository source, tests, runtime synchronization, and live runtime parity as separate states.
- Prefer targeted synchronization. Do not use a broad mirror or `--delete` for a narrow change.

## Skills

- `codex/skills/*` is the repository source for persistently managed skills; synchronize runtime copies only through an existing script or an explicit targeted copy.
- After adding or installing a skill, validate its `SKILL.md` frontmatter and run the repository gate.
- Use `skill-evaluator` and `committee-review-loop` when a complex skill requires formal evaluation.

## Delivery Harness Framework

- Preserve helper read/write boundaries when changing DHF helpers or runtime evidence.
- After related code and tests pass, update the affected sections in `docs/HARNESS_RUNTIME.md`, `docs/repo-index.md`, and `docs/CODEX_ENV_REPRODUCTION.md`.
