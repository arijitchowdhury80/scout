# Scout Website Plan

Date: 2026-06-28
Status: Draft for review before implementation

## Recommended Positioning

Scout should not be presented as a generic crawler app.

Recommended headline:

> Turn messy web pages into citable, downstream-ready records.

Supporting copy:

> Scout is a local-first acquisition system for AI workflows. Scrape pages,
> capture browser evidence, preserve citations, and export structured records
> your agents, search indexes, and intelligence pipelines can trust.

## Primary CTAs

1. `Install locally`
2. `Read the docs`
3. `Join hosted beta`

Avoid leading with `Get API key` until the hosted product has tenancy, payment,
quotas, and security controls.

## Site Map

### `/`

Homepage.

Sections:

1. Hero with install + hosted beta CTAs.
2. Code/readout demo.
3. Acquisition ladder.
4. Evidence/artifact contract.
5. Typed record outputs.
6. Local-first vs hosted optional.
7. Use cases.
8. Pricing preview.
9. FAQ.
10. Footer with docs/GitHub/license/attribution.

### `/docs`

Developer documentation.

Initial docs:

- Quickstart.
- Installation.
- CLI.
- HTTP API.
- Artifact contract.
- Execution modes.
- Product extraction.
- Browser/user-session capture.
- Hosted beta limits.
- Legal/acceptable-use.

### `/pricing`

Pricing and usage.

Initial copy:

- Local free.
- Hosted beta pass.
- Hosted subscriptions later.
- Credit explanation.

### `/examples`

Example workflows:

- URL to markdown.
- Product category to records.
- Product records to JSONL, CSV, SQLite, and Algolia.
- Captured HTML to records.
- Company intelligence run.
- Hard-site blocked evidence.

### `/beta`

Private beta signup or checkout.

## Homepage Wireframe

```text
HEADER
  SCOUT                         Docs  Examples  Pricing  GitHub  Join Beta

HERO
  Turn messy web pages into citable, downstream-ready records.
  Local-first acquisition for AI workflows.
  [Install locally] [Join hosted beta] [Docs]

READOUT STRIP
  scout scrape URL -> source_pages.json -> records.jsonl -> extraction_report.md

ACQUISITION LADDER
  direct fetch | Crawl4AI | scout browser | user browser | saved HTML | API adapters

EVIDENCE CONTRACT
  manifest / records / source pages / blocked pages / screenshots / citations

RECORD OUTPUTS
  products | company | investor | careers | news | research | docs | website quality

LOCAL-FIRST
  Runs on your machine. You pick the workdir. You own artifacts.

HOSTED OPTIONAL
  Hosted API keys for convenience. Metered, limited, transparent.

USE CASES
  AI agents, competitive intelligence, product catalogs, search demos,
  research automation.

PRICING
  Local free. Hosted beta from $22 with credits. Subscriptions planned.

FAQ
  Is it legal? Does it beat blocks? How is Crawl4AI used? What data is stored?

FOOTER
  Docs, GitHub, Attribution, License, Security, Contact
```

## Design Direction: Supadesign IndustrialGray

Use the provided design system:

`/Users/arijitchowdhury/Dropbox/AI-Development/DesignSystems/Supadesign-IndustrialGray.zip`

Key rules:

- warm industrial background `#EBEBE8`,
- structural 12-column grid,
- sharp rectangular sections,
- amber/ochre accent,
- technical mono readouts,
- editorial display type,
- subtle noise overlay,
- dark footer.

Recommended hero feel:

- not a SaaS gradient,
- not a dashboard mockup,
- more like an infrastructure field manual,
- terminal/readout proof above the fold.

## Messaging Pillars

### 1. Owned Acquisition

Run locally, choose acquisition mode, store artifacts where you want.

### 2. Evidence First

Every useful result should point back to source evidence, screenshots, blocked
pages, or extraction reports.

### 3. Browser-Aware

Scout can escalate from crawler to browser/user-session capture when ordinary
fetching is not enough.

### 4. Records, Not Blobs

Output product records, company records, investor assets, news signals, docs
records, and research records.

### 5. Honest Limits

Scout does not promise universal unblock or perfect extraction. It preserves
what happened and makes failures inspectable.

## Website Build Recommendation

Do not build the website inside the current `/app` interface. The app UI is not
the product. Build a separate marketing/docs website surface.

Implementation options:

1. **Static site in this repo** under `website/` using the Supadesign CSS.
2. **Docs-first site** with MkDocs/Docusaurus later.
3. **Separate site repo** after messaging stabilizes.

Recommended next step:

- Build a static `website/` v1 homepage first.
- Use existing `website/README.md`.
- Copy design-system CSS into `website/assets/`.
- Make `/website/index.html` self-contained enough for private beta review.

## Claims To Avoid

- "Unblock any website."
- "Better than Firecrawl."
- "Unlimited hosted scraping."
- "Production-ready multi-tenant SaaS."
- "Perfect intelligence extraction."

## Claims Scout Can Make If Backed By Current Certification

- local CLI/API service,
- scrape/crawl/map/screenshot,
- artifact contract,
- product extraction and Algolia preparation,
- V1 intelligence workflows,
- blocked/fallback evidence,
- user-browser capture path,
- Docker packaging path,
- certification report available for tested scenarios.
