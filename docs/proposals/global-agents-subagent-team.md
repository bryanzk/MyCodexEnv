# Global AGENTS draft: adaptive subagent team

Status: review draft only. This file does not install agents or change the active global `AGENTS.md`.

## Adaptive Subagent Team

- Treat `~/.codex/agents/*.toml` as the available persistent team roster.
- For each request, the primary agent decides whether delegation materially improves speed, context isolation, specialist accuracy, or independent verification.
- Handle small, serial, or tightly coupled work directly. For suitable work, dispatch the smallest sufficient team, normally one to three subagents.
- Give each subagent one bounded job, the minimum required context, an explicit read/write boundary, and a checkable output.
- Use read-only roles for exploration, planning, diagnosis, research, security review, QA review, and code review unless the user separately authorizes implementation.
- Give concurrent implementation agents disjoint write sets. The primary agent owns integration, conflict resolution, final verification, and the user-facing answer.
- Delegation preserves the request's authorization boundary. It does not authorize external writes, deployment, publication, financial actions, email mutation, credential access, destructive operations, or new Codex tasks.
- Do not delegate when the primary agent needs the result immediately before any useful work can continue, when agents would contend over the same files, or when coordination costs exceed the task.
- Treat subagent reports as evidence to verify, not completion proof. Re-read changed files and run fresh relevant gates before claiming completion.

## Role Routing

Choose by task evidence rather than project name:

| Signal | Preferred role |
| --- | --- |
| Unknown code path, repository map, impact surface | `explorer` |
| Architecture, interfaces, data flow, implementation boundaries | `architect` |
| Small implementation with settled requirements | `worker` |
| Correctness, regression, tests, pre-landing review | `reviewer` |
| Python, APIs, parsers, SQLite, data pipelines, PDFs | `python_data` |
| React, Vue, TypeScript, static sites, Cloudflare Workers or Pages | `web_cloudflare` |
| Chrome extensions, Playwright, browser behavior, accessibility | `browser_qa` |
| SwiftUI, macOS, RIME, local system integration | `apple_platform` |
| Elixir, OTP, Phoenix, concurrency, agent orchestration | `elixir_orchestrator` |
| LLMs, RAG, evaluation, translation, technical experiments | `ai_researcher` |
| Credentials, PII, authorization, privacy, financial or production boundaries | `security_privacy` |
| Product judgment, bilingual content, SEO, growth, job materials | `product_content` |
| Runtime promotion, deployment, release, rollback, operational evidence | `operations_release` |

When several roles match, prefer the role closest to the requested proof. Add `security_privacy` or `reviewer` only when an independent risk or verification pass is useful; do not make every task a committee.

## Dispatch Completion Gate

Before dispatch, the primary agent must be able to state:

1. why delegation is useful;
2. each member's bounded deliverable;
3. each member's allowed write set, or `read-only`;
4. which result can run independently;
5. how the primary agent will verify the result.

If any item is unclear, keep the work in the primary agent until the boundary is understood.
