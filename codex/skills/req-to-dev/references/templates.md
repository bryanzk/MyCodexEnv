# Templates (Req-to-Dev)

Use these snippets as starting points. Keep them short and adjust to the repo.

## 1. Recommended Doc Layout

- `SECURITY.md` / `SECURITY.zh-CN.md`
- `docs/safety-net/{en,zh}/...`
- `docs/contracts/{cli,errors,audit}.md`
- `docs/plan/W1-W6.md` (task-level)
- `docs/plan/TASK_INDEX.md`
- `AGENTS.md`
- `docs/adr/*.md`
- `tests/fixtures/README.md`

## 2. Minimal SECURITY.md

```md
# Security Policy

## Safety Net (Authoritative)

- `docs/safety-net/en/README.md`

## Non-Negotiable Invariants

- Never auto-sign or auto-send transactions.
- High-risk actions are explicitly gated.
- No secrets in code/docs/logs/audit/fixtures.
```

## 3. Minimal Error Envelope (JSON)

```json
{
  "ok": false,
  "error_type": "permission_denied",
  "message": "...",
  "details": {"mode": "simulate"}
}
```

## 4. W1 Task Entry (Task-Level)

```md
- [ ] Implement `arb send` confirmation gate.
  - Depends on: error contract
  - Owner: `agent-cli` (support: `agent-core`)
  - Code: `src/cli/arb_send.rs`
  - Tests (TDD): `tests/integration/send_requires_confirm.rs::send_missing_confirm_rejected`
  - BDD: `send without --confirm is rejected`
  - Acceptance: `cargo test -p ...` (or full runner)
```

## 5. AGENTS.md Skeleton

```md
# Subagents (Parallel Development)

## Roster

- `agent-lead`: integrator
- `agent-core`: mode/error/domain/risk
- `agent-cli`: headless CLI
- `agent-ws`: fixtures + ws replay
- `agent-bdd`: gherkin + steps
- `agent-audit`: audit jsonl
- `agent-ai`: ai mock + suggestion validation

## Rules

- Change behavior => update tests + contracts.
- BDD must be offline.
```
