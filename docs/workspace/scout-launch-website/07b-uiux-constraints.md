# Scout Launch Website - UI/UX Constraints

Date: 2026-06-28

## Source Constraints Loaded

Read:

- `~/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI-Docs/Obsidian/ArijitOS-Brain/Standards/UIUXDesignSOP/index.md`
- Supadesign IndustrialGray `README.md`
- Supadesign IndustrialGray `warm-industrial.css`

## Emphasis Rules

- Every section has at most one hero element.
- Primary content is limited to two or three focus points per section.
- Supporting details use labels, readouts, or footer/FAQ treatment.
- Code/readout proof is primary but must not visually outrank the homepage
  headline.

## Component Constraints

- Use buttons for direct commands: install, docs, hosted beta.
- Use technical readout strips for CLI/API proof.
- Use cards only for repeated items like record types, pricing bands, and FAQ.
- Use a table/comparison layout for local vs hosted because the user is deciding
  between two operating models.
- Avoid nested cards.
- Avoid fake app screenshots as core proof.

## Supadesign Constraints

- Keep warm background `#EBEBE8`.
- Use the 12-column grid and sharp rectangular structure.
- Keep subtle noise overlay.
- Use amber/ochre accent and mono readouts.
- Do not use rounded corners except buttons, pills, badges, and status pulses.
- Keep footer as the main dark surface.

## Responsive Breakpoints

- 375px: one-column flow; nav wraps or collapses into fewer links; code blocks
  scroll horizontally; CTAs remain tappable.
- 768px: two-column sections can stack if needed.
- 1024px: structural grid visible; artifact/comparison sections fit cleanly.
- 1280px+: full 12-column composition.

## Accessibility

- Links and buttons have descriptive accessible text.
- Focus states must be visible.
- Touch targets should be at least 44px high.
- Contrast must meet WCAG 2.2 AA for body text.
- Color is not the only differentiator; labels and text accompany status.
- Reduced motion should disable marquee/reveal animation if added.

## Conflicts

The Supadesign kit uses some strong editorial typography and negative letter
spacing. Project-level frontend guidance says letter spacing must be 0. For this
Scout implementation, custom site CSS should keep letter spacing non-negative
and avoid viewport-width font scaling for compact UI text. Display type can use
large responsive sizes through `clamp`, but body and button text must stay
stable and readable.

