# ADR: Product Blocked-Page Fallbacks

Date: 2026-05-13

## Status

Accepted

## Context

Retailer product detail pages can block crawler traffic even when category/listing pages are crawlable. Estee Lauder currently allows Scout to discover product-catalog links from category pages, but its product detail pages return Akamai block pages in live runs. The previous behavior skipped those pages and produced zero Algolia records.

## Decision

Scout will use a fallback ladder for product crawls:

1. Extract product records from PDP JSON-LD when PDP pages are crawlable.
2. Extract partial product records from category/listing-page HTML when PDP pages are blocked or incomplete.
3. Track blocked PDP URLs as first-class response/artifact data.
4. Keep proxy and persisted browser sessions as future advanced retries, not as the core workaround.

Listing fallback records will include a completeness score so downstream Algolia indexing and PDP/search demos can distinguish complete PDP-derived records from partial PLP-derived records.

## Consequences

This keeps Scout generic and useful on hard sites without immediately entering an anti-bot arms race. It also means some records may be intentionally partial; docs and artifacts must make that explicit.

