---
name: transreader-chrome-store-release
description: Use when preparing, auditing, publishing, or verifying Transreader Chrome Web Store release assets, promo video, screenshots, listing copy, BYOK wording, or browser-control fallbacks.
---

# Transreader Chrome Store Release

## Overview

Use this for Transreader store-listing work, not general extension runtime work. The acceptance target is a publishable Chrome Web Store listing backed by refreshed local artifacts and explicit verification.

## Read First

```bash
cd /Users/kezheng/Codes/CursorDeveloper/Transreader
git status --short --branch
test -f AGENTS.md && sed -n '1,220p' AGENTS.md
find release/chrome-store -maxdepth 3 -type f | sort
```

## Workflow

1. Treat the latest approved logo/art direction as the single source of truth across icons, dist assets, promo tiles, screenshots, and video frames.
2. Audit outward-facing surfaces, especially:
   - `release/chrome-store/promo/`
   - `release/chrome-store/screenshots/`
   - `release/chrome-store/screenshots-v2/`
   - `release/chrome-store/transreader-*.zip`
   - `video/TransreaderPromo.jsx`
   - `video/promoTimeline.js`
3. Regenerate assets through repo scripts instead of hand-editing generated output when scripts exist.
4. For promo video, remember the Chrome Web Store `Global promo video` field expects a YouTube URL, not a local MP4 upload. Prepare or verify `transreader-promo.mp4`, then use YouTube Studio and paste the hosted URL into the listing.
5. If Codex Chrome extension communication fails, do not equate extension installed/enabled with browser-control success. Use Browser/DevTools or visible dashboard checks as fallback and report the control blocker separately.
6. Keep release copy aligned with current behavior. If the current release is BYOK, do not imply bundled translation credits or managed API access.

## Verification

Use the repo's current scripts first. Common gates:

```bash
npm run verify
npm run video:still
npm run video:render
ffprobe -hide_banner release/chrome-store/promo/transreader-promo.mp4
git diff --check
```

For Chrome Web Store readiness, inspect that the listing-visible asset set exists:

```bash
test -f release/chrome-store/screenshots-v2/01-wikipedia-side-panel.png
test -f release/chrome-store/screenshots-v2/02-aligned-bilingual-reader.png
test -f release/chrome-store/screenshots-v2/03-scroll-sync-context.png
test -f release/chrome-store/screenshots-v2/04-progressive-translation.png
test -f release/chrome-store/screenshots-v2/05-bring-your-own-key.png
```

Final answer must include `command`, `exit_code`, `key_output`, and `timestamp`.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Claiming local render success means store readiness | Check Chrome Web Store field semantics and uploaded URL state. |
| Updating icons but leaving promo tiles/video frames stale | Audit every outward-facing release surface. |
| Treating passive Chronicle UI as command proof | Re-run commands in the current shell or label it as visible historical evidence. |
| Debugging runtime behavior when the user asked store assets | Keep scope on listing, package, screenshots, promo video, and copy. |
