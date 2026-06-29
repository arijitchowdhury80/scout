# Examples Page Design Thinking

## Mental Model

The user is carrying a cookbook mental model: "show me concrete recipes I can run today." They expect examples to be practical, copyable, and honest about limits. What would confuse them is a demo page that implies the legacy app UI or hard-site bypass is production-certified.

## Information Architecture

| Content | Tier | Treatment |
|---|---|---|
| "Scout Examples" headline | Hero | Large page headline, one per page |
| Four beta-safe workflows | Primary | Card grid with commands and expected artifacts |
| Artifact contract | Primary | Named files with plain descriptions |
| Export path | Secondary | Short proof row for downstream handoff |
| Boundaries | Primary | Explicit caution block to prevent oversell |
| Footer and nav | Supporting | Existing launch-site navigation |

No tier inflation: technical details stay inside compact code blocks and artifact lists.

## Interaction Flow

Most common actions:

1. Choose an example that matches the task.
2. Copy or adapt the command/API shape manually.
3. Inspect the artifact files named on the page.

Happy path:

1. Visitor opens `/examples`.
2. Visitor selects a workflow card.
3. Visitor runs Scout locally or through hosted beta.
4. Visitor checks `records.json`, `source_pages.json`, `blocked_pages.json`, and `extraction_report.md`.

States:

- Empty state: not applicable, static documentation page.
- Loading state: normal static page load.
- Error state: handled by browser/server if route fails; route is covered by tests.

## Cognitive Load Budget

Visible chunks:

1. Hero.
2. Workflow grid.
3. Artifact contract.
4. Export path.
5. Boundary note.

The page stays at five chunks and avoids nested interactive controls.

## Emotional Journey

The page should move a beta tester from "what do I actually do with this?" to "I can run one small workflow and inspect the evidence." The emotional weight belongs to concrete examples and the artifact contract, not broad marketing claims.

## Design Pre-Mortem

- Risk: examples read like launch promises. Mitigation: include explicit beta boundary copy.
- Risk: the page becomes a CLI manual. Mitigation: group commands by user outcome.
- Risk: stale app UI claims creep back in. Mitigation: include "No certified legacy /app UI claim."
- Risk: mobile code blocks overflow badly. Mitigation: use existing scrollable `pre` treatment.
- Risk: inconsistent site style. Mitigation: reuse Supadesign IndustrialGray classes and existing launch-site components.

## Aesthetic Choice

Use the existing Supadesign IndustrialGray launch-site aesthetic. This is not a new brand surface; it is a consistency extension of the current private-beta website.

