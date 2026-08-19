# DHF Evolution IA and SAFE → TRUST Menu Repair

## Goals

1. Remove the duplicate page-navigation rail from the Chinese SAFE → TRUST business-value page.
2. Align the English ShipQ development-history page with the clearer seven-part information architecture of its Chinese counterpart.

## Menu repair

- Keep the shared global navigation and shared page-local TOC as the only navigation surfaces on the Chinese SAFE → TRUST page.
- Remove the legacy `side-nav` markup and its IntersectionObserver script.
- Collapse the legacy inner shell to one content column so the shared TOC owns the desktop rail and the article is not pushed right.
- Preserve all existing section IDs and public fragments.

## English evolution IA

The English page will expose the same seven top-level destinations as the Chinese page, in the same order:

1. Thesis
2. Six-stage evolution
3. ShipQ business pressures
4. SAFE × TRUST
5. Value matrix
6. Current maturity
7. Evidence boundary

- Reuse the current six English stage cards inside the Six-stage evolution section.
- Add English equivalents of the Chinese CAP framing, ShipQ business-boundary narrative, SAFE/TRUST relationship, value matrix, maturity boundary, and evidence boundary.
- Preserve the existing English visual language instead of copying the Chinese page CSS or producing a line-by-line translation.
- Preserve all existing English fragment IDs on their stage cards while adding the seven canonical bilingual section IDs.
- Keep claims bounded to the evidence already present in the Chinese source; do not introduce new deployment, production, adoption, or commercial claims.

## Verification

- Add a regression assertion that the Chinese SAFE → TRUST page has exactly one page-local TOC and no legacy `side-nav`.
- Assert that both development-history pages expose the same seven canonical section IDs in the same order.
- Assert that the six existing English legacy fragments remain present.
- Run focused IA tests, public navigation surface validation, diff hygiene, and real-browser checks at 375px, 768px, and desktop widths for both languages.
