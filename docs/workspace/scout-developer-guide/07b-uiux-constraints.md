# Scout Developer Guide UI/UX Constraints

Source read: UI/UX Design System index.

## Emphasis Tiers

- Hero: one headline introducing the guide.
- Primary: surface chooser, auth/workdir rules, artifact contract, hosted boundaries.
- Secondary: Swagger handoff and supporting notes.
- Supporting: labels, nav, footer links, code comments.

## Component Constraints

- Use existing static launch-site components: `page-hero`, `step-section`, `note-grid`, `check-grid`, and code blocks.
- No fake interactive controls.
- Every link points to an implemented route or existing artifact.
- Keep `/docs` as Swagger; the guide lives at `/guide`.

## Responsive Requirements

- 375px: cards stack; code blocks scroll horizontally.
- 768px: two-column note grids remain readable or stack via existing CSS.
- 1024px: page should match quickstart/examples density.
- 1280px+: preserve current max-width rhythm.

## Accessibility Requirements

- Semantic heading order.
- Descriptive link text.
- No color-only state.
- Focus states inherited from site CSS.
- Touch targets remain at existing nav/button sizes.

## Conflicts

No conflict with current launch-site design. The only content constraint is honesty: hosted examples must remain finite-beta examples, not public SaaS promises.

