---
name: pua-debugging
description: "Use only when the user explicitly invokes PUA debugging for a bounded problem-solving push."
---

# PUA Debugging

Apply the requested corporate-PUA tone while continuing a bounded debugging
task. The rhetoric may add pressure; it must not expand the user's scope,
authorization, systems, or write targets.

## Method

1. Read the complete original failure signal and the directly relevant source.
2. List the assumptions behind the current approach and verify the cheapest
   uncertain one.
3. Build the smallest useful reproduction or diagnostic check.
4. If an attempt fails, use the new evidence to revise the hypothesis; do not
   repeat a cosmetic variant of the same attempt.
5. Stop when the requested outcome is verified, or report the narrowed blocker,
   evidence, and one concrete next step.

Search official documentation or adjacent callers only when the observed
failure makes them relevant. Ask the user when the remaining dependency is a
credential, business decision, permission, or other fact unavailable through
authorized inspection.

Do not use failure counts as an automatic trigger. Do not require exhaustive
search, a different technology stack, unrelated bug hunts, or unrequested
follow-up work. Keep verification proportional to the changed behavior and the
repository's existing gates.
