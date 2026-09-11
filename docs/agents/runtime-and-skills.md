# Runtime and skill changes

## Runtime boundary

- Before changing Codex runtime, skills, or global configuration, check `git status` and identify the exact repository source and runtime target.
- Treat repository source, tests, runtime synchronization, and live runtime parity as separate states.
- Prefer targeted synchronization. Do not use a broad mirror or `--delete` for a narrow change.

## Skills

- `codex/skills/*` is the repository source for persistently managed skills except active external gstack. A valid `~/.gstack/repos/gstack` is managed by `scripts/external_gstack_runtime.py status|apply|recover`; ordinary sync preserves its exact targets and never performs cutover. The repo vendor remains the legacy/bootstrap fallback, and active mode does not run `setup`.
- After adding or installing a skill, validate its `SKILL.md` frontmatter and run the repository gate.
- When revising a skill, keep its description short and specific to the actual workflow. Put substantial conditional guidance behind relevant reference links; a short single-workflow skill needs no extra files. Preserve safety invariants and support the Sol/Terra/Luna consumers as well as Astra.
- The config template disables the legacy Superpowers `using-superpowers` and `brainstorming` entries while preserving the plugin's other skills. Use existing planning skills when needed; `pua-debugging` is explicit-only through its native invocation policy.
- Use `skill-evaluator` for formal evaluation or observed routing failures. Use `committee-review-loop` only when the user explicitly requests a committee or iterative scoring; use proportional independent review for changes to real authorization, privacy, data-integrity, or recovery/rollback boundaries.

## Delivery Harness Framework

- Preserve helper read/write boundaries when changing DHF helpers or runtime evidence.
- After related code and tests pass, update the affected sections in `docs/HARNESS_RUNTIME.md`, `docs/repo-index.md`, and `docs/CODEX_ENV_REPRODUCTION.md`.
