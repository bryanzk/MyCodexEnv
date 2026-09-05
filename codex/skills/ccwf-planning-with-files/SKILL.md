---
name: ccwf-planning-with-files
version: "1.0.0"
description: Maintain durable task plans and findings for work that needs cross-session recovery or an explicit file-based plan.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - WebFetch
  - WebSearch
---

# Planning with Files

Keep enough durable context for another session to resume the task without repeating discovery.

Use the repository's existing plan or state file first. If file-based planning is authorized and no suitable artifact exists, create one task-scoped plan containing the goal, completion criteria, decisions, relevant evidence, and next action. Separate findings or progress files only when their volume or consumers justify it.

Update the record when a decision, result, blocker, or handoff changes what the next session needs. Re-read it when resuming or resolving uncertainty, rather than after a fixed number of tool calls.

Preserve the task's write boundary. For read-only work or when a handoff file lacks required authorization, report the context in chat. Ordinary bounded edits do not need persistent planning files.

Continue authorized implementation and verification until the completion criteria are met. Escalate when progress depends on a missing decision, permission, credential, or external dependency; a fixed retry count alone is not a reason to stop.
