# Routing Trigger/Ban Keywords

## Trigger Keywords

### High-capability route (critical/security)
- `critical logic`
- `secret` / `credential` / `key management`
- `auth` / `authorization`
- `fund flow` / `settlement`
- `core metric` / `risk`

### Main workhorse route (regular delivery)
- `feature` / `refactor` / `api`
- `ui` / `frontend`
- `config`
- `normal bugfix`

### Economy/local route (low risk / repetitive)
- `format`
- `translation`
- `summarize logs`
- `batch classify`

## Ban Keywords (must stop and confirm)
- `delete project`
- `production deploy now`
- `skip tests`
- `ignore verification`
- `temporary hack, no root cause`

## Drift Prevention Rules
- Trigger keyword hit is necessary but not sufficient; always combine with impact scope.
- Ban keyword hit always wins over efficiency routing.
