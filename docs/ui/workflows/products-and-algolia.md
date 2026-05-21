# Products And Algolia Prep Workflow

## User Intent

Collect product records from a category or product URL, preserve source evidence,
and prepare Algolia-ready JSON/JSONL without persisting Algolia credentials.

## Required Inputs

- Product/category URL or domain.
- Execution mode, default `auto`.
- Working directory.
- Crawl settings: max depth, robots.txt behavior, delay.
- Optional product/category limits.
- Optional Algolia App ID, API key, and index name for readiness preview only.

## Run States

- **Setup**: checklist confirms use case, URL, workdir, crawl settings, and mode.
- **Live Execution**: timeline shows queued, discovery, rendering/browser,
  extraction, enrichment, artifacts, and complete/blocked/failed.
- **Results Review**: metrics show pages processed, product records, unique SKUs,
  blocked pages, and warnings.

## Result Tabs

- Overview: run summary, listing records found, detail pages blocked, readiness.
- Browser: captured screenshot/DOM/markdown when available.
- Records: product table, filters, columns, download, selected record drawer.
- Sources: source registry with listing/detail/browser/blocked badges.
- Blocked: blocked URLs, reasons, attempted providers, fallback result.
- Artifacts: manifest, records JSON/JSONL, sources, blocked pages, report.
- Logs: timestamped execution events.

## Right Drawer

Selecting a product opens name, brand, price, SKU, image URL, product URL,
completeness, missing fields, citations, source snippets, and blocked detail
evidence if enrichment failed.

## Empty, Error, And Blocked States

- Zero records plus zero blocked evidence is a failure.
- Listing records with blocked detail pages is a partial success.
- Estée Lauder can pass with listing records or complete blocked/fallback
  evidence.
- API keys must never appear outside the password input/session payload.

## Expected Artifacts

`manifest.json`, `records.json`, `records.jsonl`, `source_pages.json`,
`blocked_pages.json`, `validation.json`, `extraction_report.md`, and optional
Algolia preview output.

## Controls

Start Execution, Cancel Run, Clear Run, Browse folder, Crawl Settings chips,
Developer Details, tabs, record select, filters, columns, download, Algolia
preview, copy object IDs, artifact links, and citation context.
