# Repository navigation and sources of truth

## Read first

- Start with `README.md` for workflows and `docs/repo-index.md` for the compact repository map.
- Read a nearer `AGENTS.md` when the target directory contains one.

## Map

- `codex/`: Codex rules, configuration, hooks, runtime, skills, and workflow.
- `claude/`: Claude workflow and integration source.
- `scripts/`: synchronization, verification, recovery, reporting, and maintenance entry points.
- `docs/`: architecture, guides, status, plans, and public documentation.
- `tasks/`: task-specific runtime and maintenance evidence.

## Sources of truth

- The repository root `AGENTS.md` is the project-instruction entry point.
- `package.json` and `package-lock.json` describe the npm dependency; this repository defines no npm scripts.
- `codex/AGENTS.md` is only the managed source for global Codex rules and is synchronized to the local Codex runtime; it is not the source for repository-specific instructions.
