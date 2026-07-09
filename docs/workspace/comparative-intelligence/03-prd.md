# Comparative Intelligence PRD

Date: 2026-07-09

## Summary

Add a Scout workflow that collects comparison data across multiple websites and
returns a normalized, cited comparison matrix.

## Problem

Business users understand outcomes, not crawlers. They want to know:

- What do competitors charge?
- How is a product positioned against alternatives?
- What is the going rate in this market, location, or date window?
- Which claims, packages, or features appear repeatedly across competitors?

Today Scout can extract data from websites, but the user still has to decide
which sites to crawl, how to normalize fields, and how to compare results.

## Users

- Founder launching a new product.
- Retail or ecommerce analyst comparing product prices.
- Hotel or local service operator benchmarking nearby rates.
- Consultant preparing a market scan.
- Developer using the Scout API to build a research workflow.

## V1 Use Cases

### 1. Product Price Comparison

Input:

- Product name, model, SKU, UPC, or URL.
- User-supplied retailer URLs or a source preset.

Output:

- Retailer/source.
- Product title.
- Matched model/SKU/UPC if found.
- Price, currency, sale price, list price if available.
- Availability.
- Shipping or membership caveat if visible.
- Source URL, citation snippet, crawl timestamp.
- Match confidence.

### 2. Product Launch Pricing Research

Input:

- New product category, value proposition, optional competitor URLs.

Output:

- Comparable products.
- Price bands.
- Feature/claim matrix.
- Packaging or plan names.
- Source citations and timestamps.
- Gaps or positioning opportunities.

### 3. Local Hotel Rate Benchmark

Input:

- Hotel name or address.
- Zip code or radius.
- Date, length of stay, occupancy.
- User-supplied hotel/OTA URLs or approved source preset.

Output:

- Comparable hotel.
- Distance/location context if provided.
- Nightly rate, fees if visible, currency.
- Room type and occupancy.
- Source URL, timestamp, caveats.
- Match confidence.

## Functional Requirements

- Create a new comparative run type with a typed request and response contract.
- Support explicit source lists in V1.
- Support at least three vertical templates: product, launch-pricing, hotel-rate.
- Normalize prices, currencies, units, package names, and timestamps.
- Attach citations to every extracted comparison cell where possible.
- Emit low-confidence rows instead of silently merging uncertain matches.
- Export comparison matrices to JSON, JSONL, CSV, and SQLite through existing
  export patterns where practical.
- Produce standard Scout artifacts:
  - `manifest.json`
  - `records.json`
  - `records.jsonl`
  - `source_pages.json`
  - `blocked_pages.json`
  - `validation.json`
  - `extraction_report.md`
  - `comparison_matrix.csv`

## Suggested API Shape

`POST /v1/comparisons`

Request fields:

- `comparison_type`: `product_price | launch_pricing | hotel_rate`
- `query`: user-visible comparison question
- `sources`: list of URLs or domains
- `constraints`: typed object per comparison type
- `max_sources`
- `max_pages_per_source`
- `freshness_policy`
- `export_formats`

Response fields:

- `success`
- `run_id`
- `comparison_type`
- `matrix`
- `records`
- `blocked_sources`
- `warnings`
- `artifact_paths`
- `duration_ms`

## Acceptance Criteria

- Product comparison fixture run matches the same TV model across at least four
  retailer fixture pages and returns a matrix with normalized prices.
- Launch-pricing fixture run extracts at least five comparable product records
  and groups them into price bands with cited feature claims.
- Hotel-rate fixture run extracts nightly rates for a requested date and refuses
  to compare rows when date or occupancy cannot be confirmed.
- All prices include currency, timestamp, source URL, and confidence.
- Blocked, sparse, or ambiguous sources are recorded in `blocked_pages.json` or
  `validation.json`; they are not reported as successful price observations.
- API, CLI, and hosted workflow all use the same core service contract.
- Unit, contract, integration-fixture, and at least one live smoke test exist
  before production.

## Open Questions

- Which V1 vertical should ship first: product price comparison, launch pricing,
  or hotel rates?
- Should V1 include source discovery, or only user-supplied URLs?
- Which source categories are allowed under Scout hosted terms?
- Do we need a recurring monitor model immediately, or is one-shot research
  enough for launch?
- Should this be priced as standard credits, browser-heavy credits, or a
  separate research-pack SKU?
