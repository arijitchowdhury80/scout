# Scout Launch Homepage UI/UX Constraints

Reference read: UI/UX Design System index from the user's standards vault.

## Emphasis Tier Rules

- One hero headline only in the homepage hero.
- Operating-model readout is primary because it answers the core launch
  question: local vs hosted vs artifacts.
- Readiness caveats are secondary/supporting; visible, but not styled as the
  main promise.
- Metadata labels stay in mono/readout treatment.

## Component Constraints

- Use Supadesign IndustrialGray tokens and structure.
- Keep warm industrial background and grid/noise surfaces.
- Use sharp rectangular cards; avoid rounded SaaS panels except existing
  button/pill patterns.
- Operating-model readout should be compact, scannable, and factual.
- No app UI screenshots or fake dashboard imagery.

## Responsive Breakpoints

- 375px: single-column hero/readout; buttons become full width.
- 768px: compact stacked layout, no horizontal overflow.
- 1024px: header wraps nav cleanly.
- 1280px+: hero uses two-column copy plus evidence ledger.

## Accessibility

- Text contrast must remain AA against warm canvas.
- Links/buttons keep visible focus states.
- The operating-model readout must use text labels, not color alone.
- Touch targets stay at least 44px where interactive.

## Conflicts Raised

No direct conflict. The homepage already uses the IndustrialGray kit; the needed
change is content hierarchy, not a new design system.
