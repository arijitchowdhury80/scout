# Scout Site IA And Docs Refresh - Design Thinking

Date: 2026-07-01

## Mental Model

The site is a developer product website, not an app dashboard. Visitors expect
one logical product story on the homepage, a working demo/playground area, a
purchase or beta access path, and separate technical documentation. Putting the
playground inside docs makes docs feel like a marketing sandbox instead of
software documentation.

## Information Architecture

Homepage flow:

1. Hero: what Scout is.
2. Features: mapped to use cases and capability areas.
3. Demo: the guided product proof.
4. Playground: interactive trial immediately after the demo.
5. Purchase: pricing and beta access.

Primary nav mapping:

- Demo -> demo plus playground area.
- Features -> use cases.
- Docs -> software documentation page.
- Pricing -> purchase section/page.

Docs page:

- Hero: "Scout Docs" and what this page contains.
- Primary sections: hosted API, local install, API reference, examples, artifact
  contract, readiness.
- Playground appears only as a link/callout, not the primary body.

## Interaction Flow

Common actions:

1. Read what Scout does and who it is for.
2. Watch the demo, then try the playground.
3. Open docs for implementation details.
4. Go to pricing/purchase when ready.

No dead ends: demo links to playground, playground links to docs/purchase, docs
links back to playground and purchase.

## Cognitive Load

The homepage should keep each section to one job. The previous docs page was
overloaded because the playground consumed the first major documentation
section. Moving it to the homepage reduces docs to structured reference content.

## Emotional Journey

The flow should move from understanding to proof to hands-on trial to purchase:
"I get it" -> "I can see it" -> "I can try it" -> "I know the next step."

## Pre-Mortem

- Risk: docs still feels like a landing page. Mitigation: use technical section
  structure, endpoint table, commands, examples, and artifact contract.
- Risk: nav labels do not match destinations. Mitigation: make labels explicit:
  Features, Demo, Docs, Pricing.
- Risk: playground disappears from docs discovery. Mitigation: docs includes
  clear links to `/playground` or `/#playground`.

