---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
disable-model-invocation: true
---



## Codex skill invocation

When this harness has no Skill tool, load each named skill with the available skill-reading tool, or read its installed `SKILL.md` and relevant references, before following it. Naming a skill alone does not load it. User-invoked skills still require the user's invocation; this note grants no new permissions, external actions, session creation, or agent delegation. Keep the harness's existing disabled states and authorization boundaries.

## Local document compatibility

Resolve the project's domain documents before following the filename references below or in bundled templates. Prefer an existing `GLOSSARY-MAP.md` (follow its links to the relevant context), then an existing root `GLOSSARY.md`. If neither exists, follow an existing `CONTEXT-MAP.md`, otherwise use the existing root `CONTEXT.md`. References below to `GLOSSARY.md` and `GLOSSARY-MAP.md` mean those selected project documents. Write terminology updates to the selected file; do not rename, overwrite, duplicate, or automatically merge existing documents. When neither convention exists, create `GLOSSARY.md` lazily as upstream describes. If both conventions exist, prefer GLOSSARY and leave CONTEXT intact. Creating new project files still requires the task's existing write authorization.

Call the Skill tool twice, for "grilling" and "domain-modeling".
