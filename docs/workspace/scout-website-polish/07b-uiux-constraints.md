# Scout Website Polish UI/UX Constraints

Date: 2026-06-29

## Applicable Constraints

- One hero-scale message per section.
- Navigation and labels are supporting content and must not compete with the
  hero.
- Section nav must be keyboard accessible and expose current state with more
  than color alone (`aria-current` plus visual underline/state).
- Header links must remain at least 44px tall on touch devices.
- Homepage anchors need `scroll-margin-top` so sticky header does not cover the
  section title.
- Responsive checks must cover 375px, 768px, 1024px, and 1280px.
- Avoid changing the warm industrial aesthetic unless a later brand direction
  supersedes it.

## Implementation Constraints

- Keep the frontend static: no framework added.
- Use a real SVG asset for logo and favicon.
- Use IntersectionObserver for scrollspy; no scroll polling loop.
- External page nav links must remain normal links.
