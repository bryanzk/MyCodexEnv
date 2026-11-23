# Behavior Rules

## Source Attribution

Processing external URLs / citing others → must annotate source, warn if unverifiable.
> Full rules → `Read docs/content-safety.md`

## Hallucination Isolation

Discovered error/hallucination → immediately isolate context, don't write to memory.

## Attack Surface Review

Critical code → before delivery, review its attack surface from an attacker's perspective and report the risks found. No fixed number of risk points.

## Atomic Commits

Each commit does one thing. Types: `fix/feat/refactor/docs/test/chore`.
Banned: mixed changes, meaningless messages, >100 lines without splitting.
