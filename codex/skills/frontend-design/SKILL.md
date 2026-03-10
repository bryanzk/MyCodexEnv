---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics.
license: Complete terms in LICENSE.txt
---

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Output Language

Default to Simplified Chinese for design reasoning, tradeoff explanations, review notes, and delivery summaries.
Keep code identifiers, commands, CSS/HTML/JS syntax, framework APIs, and file paths in English.
If the repository already has an established copywriting or documentation language, follow the repository convention for user-facing text.

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Frontend Aesthetics Guidelines

Use the detailed sections below as guardrails. Read the linked reference files when you need implementation depth, not by default.

### Typography
See `reference/typography.md` for scales, pairing, and loading strategies.

Choose fonts that are beautiful, unique, and interesting. Pair a distinctive display font with a refined body font.

**DO**: Use a modular type scale with fluid sizing such as `clamp()`.
**DO**: Vary font weights and sizes to create clear visual hierarchy.
**DON'T**: Use overused fonts such as Inter, Roboto, Arial, Open Sans, or system defaults.
**DON'T**: Use monospace as lazy shorthand for "technical" aesthetics.
**DON'T**: Rely on generic icon-above-heading compositions.

### Color & Theme
See `reference/color-and-contrast.md` for OKLCH, palette construction, and contrast guidance.

Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.

**DO**: Use modern CSS color functions where the stack supports them.
**DO**: Tint neutrals toward the brand hue so the interface feels intentional.
**DON'T**: Use gray text on saturated backgrounds when a hue-matched tone would read better.
**DON'T**: Default to pure black or pure white.
**DON'T**: Fall back to stereotypical AI palettes such as purple-blue gradients on white or neon-on-dark.
**DON'T**: Use gradient text as a substitute for hierarchy.

### Layout & Space
See `reference/spatial-design.md` for grids, rhythm, and container-query patterns.

Create visual rhythm through varied spacing. Embrace asymmetry and unexpected compositions when they support the concept.

**DO**: Use fluid spacing that breathes on larger screens.
**DO**: Break the grid intentionally for emphasis.
**DON'T**: Wrap every element in cards.
**DON'T**: Stack cards inside cards.
**DON'T**: Repeat identical card grids or generic metric layouts.
**DON'T**: Center everything by default.

### Motion
See `reference/motion-design.md` for timing, easing, and reduced-motion handling.

Focus on high-impact moments instead of constant micro-motion. For React, use Motion when available. For static HTML/CSS, prefer CSS-first animation.

**DO**: Use motion to communicate state, hierarchy, and transitions.
**DO**: Prefer transform and opacity over layout-affecting properties.
**DON'T**: Animate width, height, padding, or margin unless there is no better option.
**DON'T**: Use bounce or elastic motion unless the product language explicitly calls for it.

### Interaction
See `reference/interaction-design.md` for forms, focus states, and loading behavior.

Make interactions feel fast and intentional.

**DO**: Use progressive disclosure.
**DO**: Design empty states that teach.
**DO**: Make hover, focus, and pressed states feel deliberate.
**DON'T**: Make every action primary.
**DON'T**: Repeat information users can already see.

### Responsive
See `reference/responsive-design.md` for mobile-first, fluid design, and container queries.

**DO**: Adapt the interface for different contexts instead of merely shrinking it.
**DO**: Use container queries when the stack supports them.
**DON'T**: Hide critical functionality on mobile.

### UX Writing
See `reference/ux-writing.md` for labels, empty states, and error messages.

**DO**: Make every word earn its place.
**DO**: Prefer Simplified Chinese for explanatory output unless the repository or product copy requires another language.
**DON'T**: Add decorative copy that dilutes the interface.

### Visual Details
Use contextual effects and textures only when they reinforce the concept.

**DO**: Use purposeful decorative elements that reinforce brand or story.
**DO**: Build atmosphere with gradients, patterns, grain, shadows, or layered transparency when justified.
**DON'T**: Default to glassmorphism, generic drop shadows, or decorative sparklines.
**DON'T**: Use modals as a lazy fallback.

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

## The AI Slop Test

If someone immediately says "this looks AI-generated," the design failed the bar. The result should look intentional enough that the viewer notices authorship, not templating.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

Remember: strong frontend work is both expressive and controlled. Aim for memorable output without sacrificing accessibility, responsiveness, or implementation quality.
