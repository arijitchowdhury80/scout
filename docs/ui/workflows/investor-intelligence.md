# Investor Intelligence Workflow

## User Intent

Collect investor relations evidence: reports, presentations, filings, events,
earnings materials, and parent/public-company evidence when direct investor
pages are unavailable.

## Required Inputs

- Investor relations URL, company domain, or parent-company investor URL.
- Optional ticker or parent-company hint.
- Execution mode, default `auto`.
- Working directory.

## Run States

- **Setup**: expected outputs show reports, presentations, filings, events.
- **Live Execution**: discovery differentiates site pages, PDFs, and filing links.
- **Results Review**: assets are grouped by type and recency.

## Result Tabs

- Overview: investor coverage summary.
- Browser: captured investor page evidence.
- Records: investor assets and events.
- Sources: pages, PDFs, filing pages, parent-company evidence.
- Blocked: inaccessible assets.
- Artifacts: source registry, reports, records.
- Logs: provider and parser attempts.

## Right Drawer

Asset drawer shows title, type, date, URL, source citation, confidence, and
download/source status.

## Empty, Error, And Blocked States

If a company has no direct investor page, parent/public evidence is acceptable
only when the UI labels it clearly. No investor records and no explanation is a
failure.

## Expected Artifacts

Standard artifact contract with `investor_asset.v1` records.

## Controls

Run controls, asset-type filters, source links, artifact links, selected asset
drawer, and citation context.
