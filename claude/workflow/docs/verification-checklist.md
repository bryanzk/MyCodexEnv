# Verification Checklist by Project Type

## Node.js / TypeScript
1. `npm run lint`
2. `npm run build`
3. `npm run test`
4. Security spot-check: `rg -n "(eval\(|innerHTML\s*=|exec\()" src`

## Python
1. `python -m pytest`
2. `python -m mypy .` (if enabled)
3. `python -m ruff check .` (if enabled)
4. Security spot-check: `rg -n "(subprocess\.|eval\(|exec\()" .`

## Go
1. `go test ./...`
2. `go vet ./...`
3. `go build ./...`
4. Security spot-check: `rg -n "(os/exec|unsafe\.Pointer)" .`

## Completion Evidence Format

```yaml
command: <the exact command>
exit_code: <0 or non-zero>
key_output: <critical PASS/FAIL line>
timestamp: <ISO8601>
```
