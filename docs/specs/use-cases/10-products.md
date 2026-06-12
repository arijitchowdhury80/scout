# Acquisition Contract: products (LIVE — spec codifies current behavior + Phase C quality fixes)

**Consumer:** SE demo indexing (Algolia push in Phase C0.4); already implemented end-to-end.

## Input contract
`url`: product/category URL or store domain. Options: max_depth, delay, respect_robots.

## Acquisition plan (as built)
URL discovery → category/product grouping (`scout/core/products/discovery.py`) → detail fetch with JSON-LD extraction → listing-card extraction for categories → browser ladder on block → user-browser capture ingestion. Unchanged.

## Record type
**`AlgoliaProductRecord`** (existing contract in `scout/core/types.py`): objectID, name, brand, description, images[], price, currency, sku, categories[], hierarchicalCategories, url, source{extractor, provider}, completeness_score.

## Phase C quality fixes (from 2026-06-12 audit evidence)
1. **Interstitial junk filter**: drop records whose name matches checkout/interstitial patterns ("Hang Tight", "Routing to checkout", cart/login titles) — deterministic blocklist, logged in report (no silent drops).
2. **Variant dedupe**: collapse records sharing sku+name where URLs differ only by variant query params; keep variant URLs in a variants[] field.
3. **Brand backfill**: when JSON-LD brand absent, use og:site_name/company name as brand with its own citation (extraction, not guess — flagged `brand_source: "site"`).

## Golden e2e flow (must keep passing)
Run `products` on Patagonia category URL → complete; ≥8 records with name+price+sku; 0 records matching the junk blocklist; no two records with identical sku+name; blocked hard-site run (Estée Lauder) still produces honest BlockedPage evidence.
