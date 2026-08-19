# DHF Evidence Spine Links

## Goal

Make every keyword module in the bilingual Evidence Hub memory spine directly navigable to its most relevant same-language Evidence page.

## Link contract

| Module | English target | Chinese target |
|---|---|---|
| `CAP` | `./dhf-shipq-development-history-en.html` | `./dhf-shipq-development-history.html` |
| `BRIDGE` | `./dhf-shipq-development-history-en.html` | `./dhf-shipq-development-history.html` |
| `SAFE` | `./dhf-case-safe-mapping-en.html` | `./dhf-case-safe-mapping.html` |
| `TRUST` | `./dhf-data-business-value-explainer-en.html` | `./dhf-data-business-value-explainer.html` |
| `RECOVER` | `./shipq-dhf-safe-controlled-recovery-en.html` | `./shipq-dhf-safe-controlled-recovery.html` |
| `BEST` | `./dhf-best-care-recover-en.html` | `./dhf-best-care-recover.html` |
| `CARE` | `./dhf-best-care-recover-en.html` | `./dhf-best-care-recover.html` |

## Interaction design

- Convert each keyword card and each BEST/CARE lens bar into one semantic link so the complete visible module is clickable.
- Preserve all existing classes, `data-dhf-memory-*` attributes, text, order, connectors, and bilingual structure.
- Keep default text colors and remove default link underlines; use the existing border/accent tokens for hover and `:focus-visible` feedback.
- Do not add buttons, new pages, dropdown navigation, dependencies, or unrelated copy changes.

## Verification

- Extend the existing Evidence memory keyword contract to assert the exact seven destination URLs for both languages.
- Assert that no keyword crosses language boundaries.
- Run the focused memory-keyword test, public navigation surface check, `git diff --check`, and a real-browser keyboard/click check on both hubs.
