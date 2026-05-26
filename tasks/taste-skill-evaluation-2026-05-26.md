# Taste Skill Evaluation - 2026-05-26

## Scope

Installed source: `https://github.com/Leonxlnx/taste-skill`

Installed workspace skills evaluated:

- `.agents/skills/brandkit`
- `.agents/skills/industrial-brutalist-ui`
- `.agents/skills/gpt-taste`
- `.agents/skills/image-to-code`
- `.agents/skills/imagegen-frontend-mobile`
- `.agents/skills/imagegen-frontend-web`
- `.agents/skills/minimalist-ui`
- `.agents/skills/full-output-enforcement`
- `.agents/skills/redesign-existing-projects`
- `.agents/skills/high-end-visual-design`
- `.agents/skills/stitch-design-taste`
- `.agents/skills/design-taste-frontend`
- `.agents/skills/design-taste-frontend-v1`

## Existence verdict

The set is worth keeping, but only if routing boundaries are explicit. The value comes from non-obvious design judgement: anti-default patterns, responsive guardrails, image-generation choreography, style-specific constraints, and productized design-system prompts. A normal prompt tweak would not reliably preserve those behaviors across sessions.

The main weakness before revision was not content quality. It was collision risk:

- `design-taste-frontend`, `high-end-visual-design`, `gpt-taste`, `minimalist-ui`, and `industrial-brutalist-ui` all looked eligible for broad frontend asks.
- `imagegen-frontend-web`, `imagegen-frontend-mobile`, `brandkit`, and `image-to-code` mixed image direction with implementation unless carefully bounded.
- `full-output-enforcement` could over-trigger on ordinary answers and fight the user's desire for concise output.
- `design-taste-frontend-v1` existed only as compatibility material and should not load by default.

## Routing findings

Primary route should be:

- Use `design-taste-frontend` for new landing pages, portfolios, editorial pages, and visually important redesigns when the user asks for code.
- Use `redesign-existing-projects` only when there is an existing local project or screenshot to audit and improve in place.
- Use `image-to-code` only when the workflow explicitly includes generating or matching design images before implementation.
- Use `imagegen-frontend-web` only for website reference images, not code.
- Use `imagegen-frontend-mobile` only for mobile app screen images, not code.
- Use `brandkit` only for brand identity boards, logos, and visual-system images.
- Use `stitch-design-taste` only to create or revise Stitch-oriented `DESIGN.md` files.
- Use `minimalist-ui`, `industrial-brutalist-ui`, `high-end-visual-design`, and `gpt-taste` only when the user names or strongly signals that specific aesthetic.
- Use `full-output-enforcement` only when the user explicitly asks for complete/unabridged output or repeated truncation has been a problem.
- Use `design-taste-frontend-v1` only when exact v1 compatibility is requested.

## Eval plan

This section is the reusable regression plan. The current turn also executed a static/manual routing evidence check, recorded below under "Executed evidence".

### Positive routing

| Skill | Prompt | Expected load |
|---|---|---|
| `design-taste-frontend` | "Build a premium landing page for a boutique AI consultancy." | Loads as default frontend taste skill. |
| `redesign-existing-projects` | "Audit this existing React app and make the UI less generic without changing behavior." | Loads for in-place redesign. |
| `image-to-code` | "Generate section reference images first, then code the homepage to match them." | Loads image-first implementation workflow. |
| `imagegen-frontend-web` | "Create one image mockup per section for a marketing site." | Loads image generation only. |
| `imagegen-frontend-mobile` | "Generate a five-screen iOS onboarding concept." | Loads mobile image generation only. |
| `brandkit` | "Create a brand board with logo system, color, type, and mockups." | Loads brand-kit image skill. |
| `stitch-design-taste` | "Write a DESIGN.md for Google Stitch to generate a premium app UI." | Loads Stitch design-system skill. |
| `full-output-enforcement` | "Return the entire file, no omissions or placeholders." | Loads complete-output guardrail. |

### Negative routing

| Prompt | Should not load |
|---|---|
| "Explain how CSS grid works." | All taste skills; answer directly. |
| "Fix this backend API bug." | Frontend design/image skills. |
| "Make a dense operations dashboard easier to scan." | `design-taste-frontend` unless the task is visual marketing; use local product UI judgement. |
| "Create a database ER diagram." | Taste skills; route to diagram/data skills. |
| "Give a concise summary of this file." | `full-output-enforcement`. |

### Forbidden load

| Prompt | Forbidden skill | Reason |
|---|---|---|
| "Generate mobile screen images only. No code." | `image-to-code` | It would implement code against the user's boundary. |
| "Use the exact legacy v1 taste-skill behavior." | `design-taste-frontend` | Must route to `design-taste-frontend-v1`. |
| "Make this government benefits form accessible and plain." | `gpt-taste`, `high-end-visual-design` | Cinematic motion and premium styling would harm the task. |
| "Please keep the answer short." | `full-output-enforcement` | Completeness pressure conflicts with brevity. |

## Progressive-loading findings

Only `stitch-design-taste` has an accessory file, `DESIGN.md`. It should be read or copied only when the user asks for a Stitch design-system artifact or asks to update an existing `DESIGN.md`. It should not load for normal frontend code or image generation.

The installed skills are mostly monolithic `SKILL.md` files. The next improvement would be to move long reference sections from the largest files into `references/` and keep top-level routing short.

## End-to-end findings

Expected lift vs baseline:

- Better avoidance of generic AI landing-page patterns.
- More reliable image-first workflows when images are actually requested.
- Stronger prevention of partial-code placeholders for full-file asks.
- Less accidental over-application after routing descriptions are narrowed.

Baseline risk without revisions:

- Multiple skills load for the same "make it premium" request.
- Image-generation skills start writing code or implementation skills start demanding image generation when the user did not ask for it.
- Compatibility v1 skill competes with the current default.

## Executed evidence

This was a static/manual paired evaluation, not a live runtime auto-router test. The installed skill loader for this workspace was not re-run inside a fresh Codex session, so routing conclusions are based on frontmatter, opening boundaries, targeted text scans, and committee review.

### Static routing checks executed

| Check | Result |
|---|---|
| All 13 frontmatter blocks parse as YAML | Pass |
| Every installed skill has matching `name` metadata | Pass |
| Every installed skill has a non-empty routed `description` | Pass |
| Every installed skill has an opening `## Routing Boundary` section | Pass |
| Image-only skills explicitly say not to implement code | Pass |
| `design-taste-frontend` declares default implementation precedence | Pass |
| `design-taste-frontend-v1` is gated to explicit legacy/v1 use | Pass |
| `full-output-enforcement` is gated to explicit full/unabridged requests | Pass |
| `gpt-taste` no longer claims Python/tool execution without a real tool run | Pass |
| `high-end-visual-design` no longer assumes premium fonts are available | Pass |

### Manual paired routing results

| Prompt | Expected route | Baseline risk | Revised result |
|---|---|---|---|
| "Build a premium landing page for a boutique AI consultancy." | `design-taste-frontend` | Multiple premium/aesthetic skills could compete. | Default route is explicit. |
| "Generate one image mockup per section for a marketing site." | `imagegen-frontend-web` | Could be confused with implementation. | Image-only boundary is explicit. |
| "Generate section reference images first, then code the homepage." | `image-to-code` | Could split between image and code skills. | Full image-to-implementation route is explicit. |
| "Create a five-screen iOS onboarding concept." | `imagegen-frontend-mobile` | Could route to web image skill. | Mobile-only boundary is explicit. |
| "Create a brand board with logo system and mockups." | `brandkit` | Could route to web mockup skill. | Brand identity/image-only boundary is explicit. |
| "Use exact legacy v1 taste-skill behavior." | `design-taste-frontend-v1` | v1 could compete with current default. | Legacy gate is explicit. |
| "Give a concise summary of this file." | No taste skill / no `full-output-enforcement` | Full-output skill could over-trigger. | Forbidden concise boundary is explicit. |

## Next edits applied

- Narrowed all 13 `description` fields to describe when to load, not just what the skill contains.
- Added a `Routing Boundary` section near the top of each skill.
- Marked code/image/Stitch/full-output boundaries explicitly.
- Replaced fake Python-execution wording in `gpt-taste` with deterministic internal selection language, including the hero-layout option heading.
- Added dependency/font availability gating to `high-end-visual-design`.
- Preserved the original design content and avoided broad rewrites.
