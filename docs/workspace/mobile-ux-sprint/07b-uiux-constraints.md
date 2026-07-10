# Mobile UX Sprint - UI/UX Constraints

Date: 2026-07-09

## SOP Status

The expected SOP file was not present at:

`~/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI-Docs/Obsidian/ArijitOS-Brain/Standards/UIUXDesignSOP/index.md`

Fallback constraints are drawn from the repo design system and the frontend
builder checklist.

## Responsive Requirements

- 360px, 375px, 390px, 412px: dedicated phone journey, not stacked desktop.
- 768px, 800px: tablet keeps the console and video, but touch targets must be
  usable.
- 1024px and wider: desktop layout remains intact.

## Accessibility Requirements

- Interactive targets at least 44px tall.
- No horizontal page scroll.
- Focus states remain visible.
- Buttons and links keep accessible names.
- Video remains reachable and visible.

## Component Constraints

- Desktop console may be hidden on phones because the existing JavaScript already
  disables live running on small screens.
- Mobile replacement must show proof, not marketing decoration.
- Do not introduce a new visual language; preserve premium mint neumorphism and
  the dark evidence surface.
