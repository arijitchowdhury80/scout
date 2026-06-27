# Scout Website Design Thinking

Date: 2026-06-27

## Mental Model

The website should feel like a product launch page for a developer/operator
tool, not a crawler API brochure. The user's mental model is:

"I have websites I need to turn into usable records. Show me what Scout can do,
why it is different, and how I can try it safely."

## Information Architecture

Hero:

- one-sentence product promise,
- private beta CTA,
- screenshot/product surface.

Primary:

- what Scout does,
- why Scout is different,
- quickstart.

Secondary:

- feature grid,
- use cases,
- comparison,
- launch status,
- legal/compliance note.

Supporting:

- attribution,
- repo/docs links,
- beta limitations.

## Interaction Flow

Primary actions:

1. Read value proposition.
2. View feature/use-case list.
3. Install or request beta access.

Happy path:

1. User lands on page.
2. User understands Scout is acquisition-to-record infrastructure.
3. User sees a concrete workflow.
4. User clicks install/beta CTA.
5. User follows quickstart.

States:

- Empty state is not relevant for static landing page.
- Loading state should be minimal because page is static.
- Error state is handled by local install troubleshooting docs.

## Cognitive Load Budget

First viewport should contain at most:

1. product promise,
2. proof screenshot,
3. primary CTA,
4. short differentiator line.

The feature list should be lower on the page and grouped into scannable bands.

## Emotional Journey

- First view: "This is serious and useful."
- Feature section: "This is more than a crawler."
- Comparison: "I understand when to use Scout vs Firecrawl."
- Quickstart: "I can try this today."
- Status: "The beta limitations are honest."

## Design Pre-Mortem

Risk: Generic AI SaaS page.

Mitigation: Use real Scout app screenshots, concrete terminal/API snippets, and
artifact examples.

Risk: Overclaiming against Firecrawl.

Mitigation: Position Scout as owned acquisition workbench, not hosted crawler
replacement.

Risk: Too much information.

Mitigation: Keep hero crisp; move detail into sections and docs.

Risk: Legal concern from unblock language.

Mitigation: Avoid "bypass"; use "browser-assisted capture" and "blocked
evidence."
