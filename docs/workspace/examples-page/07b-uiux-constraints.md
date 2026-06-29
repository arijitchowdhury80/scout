# Examples Page UI/UX Constraints

Source read: UI/UX Design System index.

## Emphasis Tiers

- Hero: one page headline only.
- Primary: workflow cards, artifact contract, and boundary block.
- Secondary: export path and supporting descriptions.
- Supporting: nav, labels, footer links, file names inside descriptions.

## Component Constraints

- Use existing static launch-site sections, grids, pills, and code blocks.
- Do not add a new app-like control surface.
- Do not include fake buttons, simulated runs, or nonfunctional controls.
- Every link must point to an existing site route or external repo/docs path.

## Responsive Requirements

- 375px: cards stack, code blocks scroll horizontally, nav wraps as existing CSS allows.
- 768px: workflow cards remain readable in one or two columns depending on available width.
- 1024px: page should match existing quickstart/pricing density.
- 1280px+: use existing max-width page shell.

## Accessibility Requirements

- Semantic headings in order.
- Links use descriptive text.
- No color-only status meaning; boundary text is explicit.
- Focus states inherited from existing site CSS.
- Code examples are readable text, not images.

## Conflicts

No conflict with the current launch website design system. The main constraint is honesty: examples must not imply that every intelligence module or legacy `/app` UI workflow has been certified.

