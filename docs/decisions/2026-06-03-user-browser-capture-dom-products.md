# 2026-06-03 — User Browser Capture V1 and Browser DOM Product Extraction

## Status

Accepted.

## Context

Scout can capture rendered evidence with its own Playwright browser session, but hard retail sites such as Estée Lauder can still behave differently in Scout's isolated browser than in Arijit's normal browser session. The app already exposed a User Browser mode, but it only recorded that the bridge was not connected.

Product extraction also stopped at browser evidence capture. The captured DOM, links, text, and screenshot were useful for review, but not yet converted into Algolia-ready product records.

## Decision

User Browser Capture V1 is an explicit ingestion contract:

- `POST /app/runs/{run_id}/user-browser-capture` accepts DOM, text, screenshot data URL, title, URL, and links from a future Chrome CDP or extension bridge.
- The endpoint writes browser evidence artifacts under the app run directory.
- Scout cancels the placeholder user-browser task when capture arrives so the setup-warning path cannot overwrite an ingested capture.
- User Browser and Scout Browser captures both use the same DOM-to-listing-card parser and emit `user_browser_dom` or `scout_browser_dom` source extractors.

The listing parser now handles product details distributed across an enclosing tile, including `data-product-name`, `data-brand`, ARIA labels, sibling price text, and image-only product links. URL discovery now treats Estée Lauder singular `/product/.../product-catalog/...` and Nike `/t/...` paths as product details while still rejecting Estée Lauder plural `/products/.../product-catalog/...` category pages.

## Consequences

This does not yet control the user's browser directly. A Chrome CDP bridge or extension still needs to collect and post the active-tab evidence. The backend and parser are now ready for that bridge, and Scout Browser runs can immediately produce product records from captured DOM when the rendered page is accessible.

Verification on 2026-06-03:

- `python3 -m pytest tests/unit/ -v` — 200 passed
- `python3 -m pyright scout/` — 0 errors
- `ruff check scout/ tests/unit/core/products/test_discovery.py tests/unit/core/products/test_listing.py tests/unit/api/test_app_runs.py` — all checks passed
- `ruff format --check scout/ tests/unit/core/products/test_discovery.py tests/unit/core/products/test_listing.py tests/unit/api/test_app_runs.py` — 64 files already formatted
