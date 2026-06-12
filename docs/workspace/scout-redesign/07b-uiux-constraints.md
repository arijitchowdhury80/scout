# Scout Redesign — Aesthetic Choice + UI/UX Constraints (Steps 7 & 7.5)

## Aesthetic: `theme-dashboard`

Why: Scout is a monitoring/operations console — live runs, streaming events, an embedded browser, evidence tables. The dark cloud-console aesthetic (IBM Plex Sans/Mono, glass panels, #0C5CAB primary, surface #09090b) matches the "mission console" mental model and is the designed-for case of this theme. Rejected: `theme-enterprise` (warm cream reads as forms/back-office, wrong for live monitoring), `report-designer` (output documents, not consoles — reserved for Scout's extraction *reports* if ever rendered), `theme-clean` (too little structure for a 3-pane console).

Brand: generic/custom (Scout's own identity) — NOT `brand: algolia`. Scout is a self-hosted tool that *feeds* Algolia workflows; dressing it in Algolia brand would misrepresent it. Algolia blue appears only inside the push-to-Algolia flow as a destination accent.

## Constraints applied to this design (from UIUXDesignSOP)

**Emphasis tiers** (tier map in 01-design-thinking.md §2): max 1 Hero per screen honored — launcher: card grid; live: browser pane or timeline, never both as hero; results: records table. Counters use Metric Tile (Secondary), never KPI-hero — they are activity gauges, not scores.

**Decision matrix mappings used:** Tabular data → Data Table (records, history, sources); Status → Severity/status badges paired with text (run states queued/running/complete/failed/blocked); Evidence → Source Tag + Proof Pill (citation chips in the drawer); Signal/News → Signal Card (news results preset); Quote → Quote Card (filings results preset); Navigation → Tab Rail (results tabs) + sidebar; Pipeline → Flow Diagram (escalation ladder indicator in live view).

**Required component states:** every interactive element ships empty/loading/error states — mockups must SHOW: empty launcher (no history), live loading skeleton, blocked-run results, failed run, empty Algolia credentials.

**Responsive:** desktop-first console; 1280px+ primary, 1024px supported, ≤768px panes stack vertically and browser pane degrades to latest-screenshot, 375px read-only review mode. Tables reflow (priority columns + drawer for the rest).

**Accessibility (WCAG 2.2 AA):** status never color-only (badge text always), focus ring in primary color, keyboard path launcher→setup→start→results, 44px targets, AA contrast checked for amber/red on #09090b, canvas browser pane: all actions duplicated as real buttons; `prefers-reduced-motion` honored (no pulse animations).

**Anti-generic-AI:** IBM Plex loaded explicitly; glass panels with real backdrop-blur; distinctive elements: (1) embedded browser pane with console chrome + honesty chip, (2) evidence-trace drawer with verbatim snippet highlighting, (3) use-case launcher cards with record-type glyphs and live "what you'll get" field lists from the contracts.

**Conflicts raised:** none blocking. One deviation noted: theme-dashboard suggests sidebar-first nav; Scout keeps its left rail (icon+label) which satisfies the same rule — rail labels must not clip (existing e2e test enforces).
