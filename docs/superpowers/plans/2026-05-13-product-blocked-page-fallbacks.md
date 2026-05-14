# Product Blocked-Page Fallbacks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `scout products` produce useful Algolia-ready product records when product detail pages are blocked, especially for hard retailer sites like Estee Lauder.

**Architecture:** Keep the generic crawler path as the default: discover categories, scrape category pages, discover product URLs, scrape PDPs, and extract JSON-LD. Add a fallback path that extracts product-card records from category/listing-page HTML before PDP crawling, tracks blocked PDPs explicitly, and writes blocked evidence into artifacts and reports. This avoids turning Scout into a site-specific anti-bot tool while still making blocked runs useful.

**Tech Stack:** Python 3.13, Pydantic v2 contracts, Crawl4AI-backed Scout scrape mode, pytest, pyright, ruff.

---

## Files

- Create: `scout/core/products/listing.py` for PLP/listing-page product extraction.
- Modify: `scout/core/types.py` to add blocked-page and completeness metadata contracts.
- Modify: `scout/core/products/algolia.py` to support listing-card records and completeness scoring.
- Modify: `scout/core/modes/products.py` to carry category-page raw HTML, use listing fallback, and return blocked pages.
- Modify: `scout/core/artifacts.py` to write `blocked_pages.json` and richer reports.
- Modify: `tests/unit/core/products/` and `tests/unit/core/modes/test_products.py` for RED/GREEN coverage.
- Modify: `tests/integration/test_product_sites_live.py` so Estee is expected to produce records from fallback or blocked evidence.
- Modify: `docs/product-to-algolia.md` with hard-site behavior and examples.

## Task 1: Contracts

- [ ] Add `BlockedPage` and `ProductListingCard` Pydantic models.
- [ ] Add `completeness_score` to `AlgoliaProductRecord`.
- [ ] Add `blocked_pages` and `total_blocked_pages` to `ProductCrawlResponse`.
- [ ] Add `blocked_pages_json` to `ProductArtifactFiles`.
- [ ] Write contract tests first and verify they fail before implementation.

## Task 2: Listing Extraction

- [ ] Add tests for generic product-card extraction from category HTML.
- [ ] Extract anchors, image URLs, names, prices, and brand hints from repeated product-card-like blocks.
- [ ] Support embedded JSON product lists from common script payloads when present.
- [ ] Keep extractor generic; do not add Estee-only hardcoding.

## Task 3: Product Mode Fallback

- [ ] Capture raw category HTML during discovery.
- [ ] Build listing fallback records before PDP scrape results are finalized.
- [ ] Prefer PDP JSON-LD records over listing fallback records for the same URL.
- [ ] When a PDP is blocked, retry once through the browser fallback channel.
- [ ] If browser fallback succeeds, emit `*_browser_fallback` provenance.
- [ ] If browser fallback is still blocked, retain the listing fallback record and add a `BlockedPage` entry.
- [ ] If no fallback exists, skip the blocked PDP but report it.

## Task 4: Artifacts And Docs

- [ ] Write `blocked_pages.json` for every persisted product run.
- [ ] Include extractor counts, completeness range, and blocked-page count in `report.md`.
- [ ] Document blocked-site workflow and commands.

## Task 5: Verification

- [ ] Run targeted RED/GREEN tests during each implementation slice.
- [ ] Run `python3 -m pytest tests/unit/core/products tests/unit/core/modes/test_products.py tests/unit/core/test_contracts.py -v`.
- [ ] Run `python3 -m pytest tests/unit/ -v`.
- [ ] Run `python3 -m pyright scout/`.
- [ ] Run `ruff check scout tests && ruff format --check scout tests`.
- [ ] Run live Estee command with network access and inspect generated artifacts.
