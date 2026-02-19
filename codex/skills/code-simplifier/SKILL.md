---
name: code-simplifier
description: Simplify recently modified code for clarity and maintainability while preserving behavior, following CLAUDE.md project standards.
metadata:
  short-description: Simplify code without changing behavior
---

# Code Simplifier

Use this skill when the user wants code simplified or cleaned up without changing behavior.

## Scope

- Only edit code the user selected or explicitly referenced.
- If no selection is given, focus on files recently modified in this session.

## Standards

Follow `CLAUDE.md` for project-specific rules. Key expectations:

- Use ES modules with proper import sorting and extensions.
- Prefer `function` keyword over arrow functions.
- Add explicit return types for top-level functions.
- React components use explicit Props types.
- Avoid try/catch when possible; follow existing error handling patterns.
- Avoid nested ternaries; use switch or if/else chains.

## Simplification Guidelines

- Preserve behavior exactly; change structure only for clarity.
- Reduce unnecessary nesting and remove redundant abstractions.
- Use clear, explicit names; avoid overly compact code.
- Remove comments that restate obvious code.

## Output

- Provide updated code only.
- Add up to 3 concise bullets describing significant changes.
