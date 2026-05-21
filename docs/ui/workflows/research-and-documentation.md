# Research And Documentation Workflow

## User Intent

Capture generic pages, docs sites, PDFs, and research prompts into structured
records with citations and reusable source evidence.

## Required Inputs

- URL, domain, sitemap URL, docs URL, or research prompt.
- Optional max pages, depth, and include/exclude patterns.
- Execution mode, default `auto`.
- Working directory.

## Run States

- **Setup**: target and scope controls.
- **Live Execution**: discovery, crawl, parse, extraction, and artifact writing.
- **Results Review**: records are grouped by page, section, document, or answer.

## Result Tabs

- Overview: scope, page count, summary, and gaps.
- Browser: captured page or document evidence.
- Records: research/docs records.
- Sources: pages, PDFs, sitemaps, markdown.
- Blocked: inaccessible pages.
- Artifacts: records, source pages, reports.
- Logs: parser and provider events.

## Right Drawer

Selected record shows claim, section, source URL, snippet, selector/hash where
available, and confidence.

## Empty, Error, And Blocked States

Research runs must produce either cited records or explicit source/blocked
evidence. Docs runs must show crawled sections or why the docs source failed.

## Expected Artifacts

Standard artifact contract with `research_record.v1` and docs records.

## Controls

Run controls, scope filters, section filters, source links, citation context,
download, and artifact links.
