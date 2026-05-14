# Harness Agent Brief

Use this template when a worker agent needs a durable task contract. The brief
should describe behavior and interfaces that survive normal refactors.

## Category
bug / enhancement

## Summary
One-line description of the work.

## Current Behavior
Describe what happens now. For a new feature, describe the current baseline the
feature extends.

## Desired Behavior
Describe the observable behavior after the worker finishes, including important
error states.

## Key Interfaces
- Name the types, commands, config shapes, public functions, or user-visible
  flows the worker must preserve or change.

## Acceptance Criteria
- [ ] Specific, testable criterion.

## Out Of Scope
- Adjacent behavior the worker must not change.

## Writing Rules
- Do not use line numbers as the task contract.
- Avoid file-path-only instructions; paths may help orientation, but behavior,
  interfaces, and acceptance criteria define done.
- Keep implementation details out unless they are stable public contracts.
