# UI/UX Constraints For Status Decision Workflow

Read source: `~/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI-Docs/Obsidian/ArijitOS-Brain/Standards/UIUXDesignSOP/index.md`

## Applicable Constraints

- Every content element must have an emphasis tier.
- Status/indicator content should remain visually grounded and not overwhelm the page.
- Evidence/proof content can use proof pills, source tags, or compact command blocks.
- Navigation/wayfinding should stay supporting; no new nav is needed for this slice.
- Accessibility target remains WCAG 2.2 AA.
- Responsive behavior must hold at 375px, 768px, 1024px, and 1280px.

## Component Choice

- Use existing `section step-section` for the workflow.
- Use existing `pre code` command block for terminal commands.
- Use existing `note-grid` articles for explanations.
- Avoid introducing new controls; this is guidance, not an interactive app flow.

## Responsive Notes

The existing static site CSS already handles page sections and note grids. The new copy is short and command lines are wrapped by existing `<pre>` behavior.

## Conflict Check

No conflict with the existing design system. This is a content addition to a status page, not a new app shell or visual system.
