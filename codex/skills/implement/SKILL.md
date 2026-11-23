---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---


## Codex skill invocation

When this harness has no Skill tool, load each named skill with the available skill-reading tool, or read its installed `SKILL.md` and relevant references, before following it. Naming a skill alone does not load it. User-invoked skills still require the user's invocation; this note grants no new permissions, external actions, session creation, or agent delegation. Keep the harness's existing disabled states and authorization boundaries.

Implement the work described by the user in the spec or tickets.

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask.

Call the Skill tool with "tdd" where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, call the Skill tool with "code-review" to review the work.

Commit your work to the current branch.
