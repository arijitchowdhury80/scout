# Scout Feature List

Date: 2026-06-27
Status: Product documentation baseline

## Product Definition

Scout is a self-hosted web acquisition and intelligence engine. It turns public
web pages, browser sessions, and captured HTML into clean markdown, screenshots,
links, typed records, source evidence, artifacts, and downstream-ready data.

Scout is not positioned as "one more crawler." Its strongest value is
evidence-grade acquisition: the workflow, browser handoff, evidence model,
artifacts, typed records, citations, validation, and export paths stay under the
user's control.

## Core Acquisition

- Single-page scrape to clean markdown.
- Optional raw HTML capture.
- Link extraction.
- Metadata extraction: title, description, language, word count, token estimate.
- JavaScript rendering with Crawl4AI.
- Stealth options: user agent, proxy config, navigator override, human-like
  delay, headed/headless mode.
- Screenshot capture.
- URL mapping.
- Multi-page crawling.

## Captured HTML And Browser Workflows

- Structure already-held HTML without refetching.
- Attach to a Chrome/CDP browser session.
- Harvest a live, already-open page.
- Capture native/user browser page state.
- Preserve blocked-page evidence instead of silent failure.
- Embedded browser streaming path for app-based interaction.

## Product Catalog Workflows

- Product/category URL discovery.
- Listing-card extraction.
- JSON-LD product extraction.
- downstream-ready product records.
- Local product exports:
  - JSON,
  - JSONL,
  - CSV,
  - SQLite,
  - Google Sheets import bundle.
- Algolia preparation/push remains one supported destination, not the only
  product data path.
- Product artifact folder:
  - discovered URLs,
  - raw products,
  - records JSON,
  - records NDJSON,
  - Algolia settings,
  - blocked pages,
  - extraction report.
- Product cleanup improvements:
  - multi-currency price detection,
  - category/product URL classification,
  - fallback from empty discovered groups,
  - listing records preserved against equal-score detail overwrites.

## Intelligence Workflows

Scout includes V1 vertical runners for:

- company intelligence,
- careers and hiring,
- investor relations,
- news and blogs,
- research pages,
- documentation sites,
- social profile discovery,
- locations/store locator signals,
- PRISM-style bundle runs.

These runners are useful but should be described as V1 heuristic workflows. They
scrape likely pages and extract structured signals; they are not yet guaranteed
deep research agents.

## Evidence And Artifacts

- Run manifests.
- Records JSON and JSONL.
- Source pages.
- Blocked pages.
- Validation findings.
- Extraction reports.
- Screenshot/DOM/text/link artifacts where browser evidence is captured.
- Citations/source evidence on generated records where available.

## Service Operations

- Hosted HTTP API and Claude/Codex skill usage for beta testers.
- Local CLI, local HTTP API, Python package, and Docker-from-source for
  internal/operator verification.
- Run manifests, records, sources, blocked pages, artifacts, and reports.
- SQLite run persistence.
- Protected browser-capture backend routes for future user-browser workflows.
- Configurable `SCOUT_WORKDIR` for local and hosted artifact storage.
- Docker deployment files for VPS/internal operations.
- API key authentication.

## Product Export And Algolia Integration

- Product export to JSON, JSONL, CSV, SQLite, and Google Sheets import files.
- Algolia record readiness preview.
- Required-field validation.
- Sample objectID preview.
- Push records to Algolia.
- Product records shaped for search/demo indexing.

## Interfaces

- Hosted FastAPI HTTP service.
- Claude/Codex skill backend.
- Operator Python package.
- Operator CLI.
- Internal Docker service.
- Future MCP server target.

## Beta Status

Stronger today:

- scrape, crawl, map, screenshot,
- captured HTML structuring,
- product extraction on friendly ecommerce sites,
- local product exports,
- Algolia preview/push,
- artifact generation,
- local API/UI operation.

Still beta/experimental:

- hard-site extraction,
- user-browser capture reliability,
- vertical intelligence depth,
- public packaging/publishing,
- MCP server,
- commercial legal/compliance posture.
