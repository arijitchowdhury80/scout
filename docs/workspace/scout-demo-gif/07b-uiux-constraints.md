# Scout Demo GIF UI/UX Constraints

Source read: UI/UX Design System index.

## Emphasis Tiers

- Primary: demo media and headline.
- Secondary: flow explanation.
- Supporting: boundary note and captions.

## Component Constraints

- Use real `<img>` media with descriptive `alt`.
- Do not add fake interactive controls.
- Keep the media beta-safe: no secrets, no real API keys, no promise of bypass.
- Use existing launch-site layout and CSS variables where possible.

## Responsive Requirements

- 375px: media scales to width; text cards stack.
- 768px: media and description remain readable.
- 1024px+: demo can sit in a two-column section.
- 1280px+: preserve existing max-width rhythm.

## Accessibility Requirements

- GIF must have alt text that conveys the workflow.
- The same workflow must be explained in adjacent text for users who cannot consume animation.
- Do not rely on motion alone.
- Avoid flashing or high-frequency animation.

## Conflicts

No conflicts with the current launch-site design system.

