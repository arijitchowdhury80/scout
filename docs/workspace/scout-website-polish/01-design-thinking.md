# Scout Website Polish Design Thinking

Date: 2026-06-29

## Mental Model

The site is a launch/product narrative, not an app shell. The user's current
reaction is positive: the page feels strong, but slightly too dense. The right
move is subtraction and navigation polish, not redesign.

## Information Architecture

| Element | Tier | Treatment |
|---|---|---|
| Hero headline and primary CTA | Hero | Keep dominant |
| Logo/brand wordmark | Primary | More distinctive, less blocky |
| Section nav | Primary | Section-aware on homepage, compact |
| Ledger/demo/operating model | Primary | Keep, reduce spacing slightly |
| Repeated grids | Secondary | Reduce padding/min-height about 10% |
| Legal/status/pricing links | Supporting | Stay available, less visually loud |

## Interaction Flow

1. User lands on hero and understands Scout.
2. User scrolls through sections; nav highlights the current section.
3. Clicking a homepage nav link lands the section below sticky header.
4. Utility page links still navigate normally.

## Cognitive Load Budget

The homepage currently shows many sections with strong borders and large cards.
Reduction strategy:

- compact header/nav spacing;
- reduce hero and section padding by about 10%;
- reduce card min-height/padding;
- make homepage nav reflect fewer, clearer section anchors.

## Emotional Journey

The page should feel credible, sharp, and usable. The logo should add product
identity without making the page feel like a different brand. Scroll-aware nav
should make the long page feel intentional rather than sprawling.

## Pre-Mortem

- Risk: logo becomes decorative noise. Mitigation: use a simple SVG mark with
  one geometry idea and a restrained wordmark.
- Risk: density reduction makes the page feel less premium. Mitigation: reduce
  spacing only 8-12%, keep strong grid structure.
- Risk: scrollspy conflicts with non-homepage links. Mitigation: only track
  links with `data-section-link` and matching homepage section IDs.
- Risk: sticky header hides anchored sections. Mitigation: set `scroll-margin-top`
  on section anchors.
