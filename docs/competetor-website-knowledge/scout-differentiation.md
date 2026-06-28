# Scout Differentiation

Date: 2026-06-28
Status: Launch positioning draft

## The Hard Truth

"Local-owned data" is useful, but it is not enough by itself.

Firecrawl, ScrapingBee, ScraperAPI, Apify, Exa, Tavily, Zyte, Browserbase, and
Diffbot all give users private copies of public data after a run. Scout cannot
win by saying "your result is private" as the only wedge.

Scout needs to win on **what happens after acquisition**.

## Scout's Stronger Wedge

Scout should be positioned as:

> An evidence-grade acquisition workbench that turns web pages into typed,
> citable, downstream-ready records.

That means Scout is not "another crawler." It is a workflow layer around
acquisition:

1. **Acquisition ladder**
   Scout chooses or records how evidence was acquired: direct fetch, Crawl4AI,
   hosted fetch, browser render, user-browser capture, saved HTML/PDF, or API
   adapter.

2. **Evidence ledger**
   Every run preserves source pages, blocked pages, screenshots, markdown/DOM
   evidence, hashes, provider mode, status, and timestamps.

3. **Typed records**
   Scout outputs records that downstream tools can use directly: product,
   company, executive, investor asset, career site, job posting, news signal,
   docs page, location, social profile, and research record.

4. **Citation-grade provenance**
   Records point back to source evidence. Missing citations become validation
   warnings instead of invisible risk.

5. **Local-first artifact contract**
   Users can run locally and keep `manifest.json`, `records.json`,
   `records.jsonl`, `source_pages.json`, `blocked_pages.json`,
   `validation.json`, and `extraction_report.md` in their chosen workspace.

6. **Honest blocked/fallback behavior**
   Scout should not pretend a run worked. A blocked site should produce
   inspectable blocked evidence, attempted providers, reasons, and fallback
   recommendations.

7. **Workflow exports**
   Product data should export to JSONL, CSV, SQLite, Google Sheets, and Algolia
   preparation. Company/PRISM data should export as citable intelligence
   bundles, not just markdown blobs.

## Where Firecrawl Is Stronger

Scout should respect these facts:

- Firecrawl has a very clean developer website and API-first docs.
- It has strong primitive names: scrape, crawl, map, search, interact.
- It has hosted infrastructure, pricing, trust logos, open-source adoption, and
  a simple onboarding path.
- It is likely easier for a developer who only wants hosted markdown from a URL.

## Where Scout Can Be Different

Scout can be better for users who need:

- a local acquisition system they can run inside their own workflow;
- typed records rather than generic markdown;
- artifact folders they can audit later;
- citations per extracted claim;
- blocked-page evidence instead of silent failure;
- vertical workflows such as product catalog, PRISM/company intelligence,
  investor, careers/jobs, docs, news/blogs, website quality;
- downstream export preparation for search, intelligence, spreadsheets, and
  local databases.

## Positioning Do / Do Not

Do say:

- "Turn messy pages into citable records."
- "Run locally, use hosted when convenient."
- "Evidence-first acquisition for AI workflows."
- "Records, sources, blocked pages, and validation in every run."
- "Browser-aware, but honest about blocks."

Do not say:

- "Better than Firecrawl."
- "Unblock any website."
- "Unlimited hosted scraping."
- "Perfect intelligence extraction."
- "Private because SaaS crawlers are not private."

## Website Implication

The Scout website should not center a generic "scrape any website" promise.

The first-page story should show:

```text
URL or target
  -> acquisition ladder
  -> source evidence
  -> typed records
  -> citations and validation
  -> exports / downstream systems
```

The launch page needs a visible "proof strip" showing files/artifacts and record
schemas. This is the clearest way to show how Scout is different from a hosted
markdown crawler.

## Product Implication

Before broad public launch, Scout must prove:

- product records are useful without Algolia-specific assumptions; local export
  adapters now cover JSON, JSONL, CSV, SQLite, and Google Sheets import bundles;
- intelligence modules produce meaningful records, not only non-empty responses;
- live/hard-site failures are inspectable;
- CLI and hosted API contracts match docs;
- direct Google Sheets API push, if added, has an explicit credential and
  security model.
