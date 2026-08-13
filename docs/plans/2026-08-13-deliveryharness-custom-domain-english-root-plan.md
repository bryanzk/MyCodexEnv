# DeliveryHarness custom-domain English-root rollout

## Scope

Bind `deliveryharness.com` to the repository's GitHub Pages deployment and make
the published root path the English DHF landing page. Keep the old English
filename as a compatibility entry and preserve a stable Chinese entry.

## Target structure

| URL | Source |
| --- | --- |
| `https://deliveryharness.com/` | `docs/index.html` (English) |
| `https://deliveryharness.com/index-en.html` | English compatibility copy |
| `https://deliveryharness.com/index-zh.html` | Chinese landing page |
| `https://deliveryharness.com/dhf-engineering-notes-en.html#derive-heading` | English engineering notes |

## Execution phases

1. Capture the repository, Pages, DNS, redirect, and public URL baseline.
2. Promote the English landing page to `docs/index.html`, preserve the Chinese
   page as `docs/index-zh.html`, keep `docs/index-en.html` byte-identical, and
   add `docs/CNAME`.
3. Update landing-page navigation, surface inventory, repo index, and tests to
   recognize the English root and Chinese compatibility path.
4. Run HTML/link checks, public-surface checks, the repository test runner, and
   a local HTTP smoke test.
5. Publish the repository change, then set the GitHub Pages custom domain and
   remove any Cloudflare redirect that targets `bryanzk.github.io`.
6. Keep Cloudflare DNS pointed directly at GitHub Pages during certificate
   issuance; only consider proxying later with `Full (strict)` after a clean
   readback.

## Acceptance

- Root path serves English content without a cross-domain `Location` header.
- `index-en.html` matches the English root; `index-zh.html` serves Chinese.
- Deep links and `#derive-heading` remain on `deliveryharness.com`.
- HTTP may upgrade to same-host HTTPS, but must not redirect to
  `bryanzk.github.io`.
- GitHub Pages, DNS, and redirect readbacks are captured separately from local
  source and test evidence.

## Rollback

Restore the previous index mapping and remove `docs/CNAME`; then restore the
GitHub Pages custom-domain setting and DNS/redirect records in reverse order.
