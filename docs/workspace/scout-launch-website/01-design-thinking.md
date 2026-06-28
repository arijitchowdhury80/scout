# Scout Launch Website - Design Thinking

Date: 2026-06-28
Updated: 2026-06-28 website positioning refresh

## 1. Mental Model

The user arrives with the mental model of a developer infrastructure website:
they expect a sharp product promise, proof that the API/CLI exists, quickstart
commands, docs, pricing direction, and honest production-readiness boundaries.

What would confuse them:

- treating Scout as a dashboard app,
- showing a large fake UI surface,
- leading with generic "AI crawler" copy,
- hiding local install behind hosted signup,
- making hard-site extraction sound magical.

The page should feel like an infrastructure field manual: precise, inspectable,
technical, and commercially honest. The refreshed page must also answer the
skeptical question: "why not just use Firecrawl or another crawler?" The answer
cannot be "because local data is private." The answer is evidence-grade records:
source pages, blocked pages, citations, validation, and exportable typed
outputs.

## 2. Information Architecture

| Content | Tier | Visual Treatment |
|---|---|---|
| Core headline | Hero | Oversized editorial display type |
| Local install CTA | Primary | Dark filled button |
| Hosted beta CTA | Primary | Ghost/pill button |
| Docs CTA | Secondary | Text/ghost button |
| Product proof command | Primary | Mono readout/terminal strip |
| Evidence ledger / record pipeline | Hero | Above-the-fold operational schematic |
| Acquisition ladder | Primary | Horizontal process grid |
| Artifact contract | Primary | File-tree schematic |
| Record outputs | Secondary | Compact cards/tags |
| Local vs hosted comparison | Primary | Two-column comparison |
| Pricing recommendation | Secondary | Pricing bands |
| Competitor-aware differentiation | Primary | Direct "crawler vs Scout" comparison |
| Crawl4AI/legal note | Supporting | Footer/FAQ |
| Source/provenance claim | Supporting | Small readout labels |

No section gets more than one hero. Technical proof is primary, but not larger
than the core headline.

## 3. Interaction Flow

Three common actions:

1. Install Scout locally.
2. Read docs or source.
3. Join hosted beta.

Happy path:

1. User reads the positioning.
2. User sees a CLI/API proof snippet.
3. User understands local-first vs hosted optional.
4. User clicks install/docs or hosted beta.

Empty/loading/error states:

- Static site has no loading state beyond normal browser load.
- Beta/payment CTAs can point to placeholder anchors until product flow exists.
- Pricing explains limits instead of pretending checkout is ready.

## 4. Cognitive Load Budget

First viewport chunks:

1. Header/nav.
2. Hero headline and copy.
3. CTA row.
4. Evidence ledger schematic.

Below the fold, each section has one job. Dense details live in structured
grids, artifact tree, and FAQ rows. The site avoids showing app navigation or
screenshots as the main proof because the app UI is not the launch product.

## 5. Emotional Journey

- Arrival: "This is serious infrastructure, not a toy crawler."
- Proof: "I can see what it does and how I would run it."
- Differentiation: "This is not merely Firecrawl with different branding."
- Trust: "They are honest about blocked pages, local control, and hosted cost."
- Action: "I can try this locally without waiting for a SaaS account."

The emotional weight is carried by the headline, evidence ledger, artifact
contract, and local-vs-hosted comparison.

## 6. Design Pre-Mortem

### Tigers

- **Generic AI crawler look.** Mitigation: use Supadesign IndustrialGray,
  structural grid, mono readouts, artifact schematics.
- **Overclaiming.** Mitigation: explicit "honest limits" section.
- **App UI confusion.** Mitigation: no app screenshot hero; site says CLI/API
  utility and local service.
- **Mobile breakage.** Mitigation: single-column mobile sections and horizontally
  safe code blocks.
- **Pricing confusion.** Mitigation: local free, hosted metered, $22 beta pass
  as limited credits only.

### Elephants

- The hosted product is not production-ready yet. The page must frame hosted as
  beta/waitlist, not live SaaS.
- The current package name may not be final. Use install copy that can be
  updated before public publishing.
- Users may compare Scout to Firecrawl immediately. The page should answer the
  comparison without attacking competitors.

## Refresh Design Plan

### Token Direction

- Color: keep Supadesign warm canvas `#EBEBE8`, ink `#18181B`, ochre
  `#BC8A2E`, border `#D4D4D8`, muted `#71717A`, and use blue only for focus.
- Type: keep Supadesign Inter/Playfair/mono roles.
- Layout: hero becomes a two-part grid with a large thesis on the left and a
  structured evidence ledger on the right.
- Signature: "ledger spine" boxes that show target -> acquisition -> evidence
  -> typed record -> export. This is memorable because it represents Scout's
  actual product contract.

### Revised Above-The-Fold Wireframe

```text
HEADER
HERO LEFT
  Evidence-grade acquisition for AI workflows
  Turn messy web pages into citable, downstream-ready records.
  [Install locally] [Join hosted beta]

HERO RIGHT
  TARGET URL
  -> acquisition ladder
  -> source_pages / blocked_pages
  -> product.v1 / company.v1 / ...
  -> JSONL / CSV / SQLite / Algolia
```

## Aesthetic Selection

Chosen aesthetic: Supadesign IndustrialGray, with the provided warm industrial
design system.

Why:

- It matches Scout's evidence/workbench identity.
- It avoids generic SaaS gradients.
- It makes technical artifacts feel like the product, which is correct.
- It gives Scout a distinctive launch look without relying on fake dashboard
  screenshots.
