# UI/UX Constraints

## Source Status

The external SOP path referenced by `frontend-builder` was not available at:

`~/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI-Docs/Obsidian/ArijitOS-Brain/Standards/UIUXDesignSOP/index.md`

The operative constraints for this draft come from the live Scout site and the locked design system embedded in `website/styles.css`.

## Applicable Scout Constraints

- Preserve `--bg` mint surface, `--fg` text, `--acc` emerald, `--accd` forest CTA, and dark `--scr` screen.
- Use amber only for evidence/citation moments, not general decoration.
- Keep JSON, records, and proof inside dark `.screen` surfaces.
- Use `.neu-card`, `.neu-well`, `.input-well`, `.screen-frame`, `.tab`, and existing typography utilities.
- Do not introduce a separate landing-page aesthetic, gradient hero, decorative orbs, or generic AI illustration.

## Emphasis Rules

- One hero thesis per section.
- Outcome bridge is primary, but must not visually overpower the live console.
- Video frame is a product walkthrough, not a marketing billboard.
- Tester guidance is actionable and compact.

## Responsive Requirements

- Check 375px mobile, 768px tablet, 1024px laptop, and 1280px desktop.
- Multi-column explanation sections collapse to one column on mobile.
- Buttons and links retain at least 44px touch targets.
- Long URLs and endpoint labels must not create horizontal overflow.

## Accessibility Requirements

- Video placeholder must have an accessible label and a clear text alternative.
- Interactive-looking controls that are not functional video controls should not be buttons.
- Focus states remain visible via existing `.btn` and link styles.
- Text contrast must remain on existing Scout AA-tested color pairings.

