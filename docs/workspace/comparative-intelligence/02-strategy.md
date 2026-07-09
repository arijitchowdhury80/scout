# Comparative Intelligence Strategy

Date: 2026-07-09

## Product Thesis

Scout should evolve from a crawler that returns records into a web intelligence
system that answers comparison questions with cited evidence.

The durable product promise:

> Give Scout a market question and a set of sources or constraints. Scout
> returns a normalized, cited comparison matrix you can trust enough to inspect,
> export, and act on.

## Target Buyers

Primary:

- Small businesses doing competitor pricing checks.
- Product founders validating price positioning before launch.
- Retail, ecommerce, and marketplace operators monitoring comparable products.
- Local operators such as hotels, clinics, gyms, and service businesses
  benchmarking nearby prices.
- Agencies and consultants producing market scans for clients.

Secondary:

- Consumers comparing high-ticket purchases.
- Internal analysts building periodic price reports.

## Wedge

Start with user-supplied sources and explicit market constraints.

This avoids overpromising broad web search, competitor discovery, and universal
retail coverage in V1. Scout can still support discovery later, but the first
version should prove the harder parts:

- extract comparable fields from different sites,
- normalize prices and units,
- match equivalent products or services,
- cite every claim,
- show confidence and freshness.

## V1 Positioning

"Competitive pricing research, with citations."

The first paid workflow should feel like:

1. Enter the product, service, or hotel/date/location question.
2. Provide source URLs or choose from a small source preset.
3. Scout crawls the sources.
4. Scout returns a comparison matrix with price, package, availability, source,
   timestamp, and confidence.
5. Export to CSV/JSON/SQLite and optionally re-run later.

## Non-Goals

- Do not promise a universal consumer shopping engine.
- Do not scrape logged-in, cart-only, membership-only, or paywalled prices in
  V1.
- Do not claim prices are authoritative after the crawl timestamp.
- Do not automatically buy, reserve, or transact.
- Do not silently merge products or hotels with low match confidence.

## Success Metric

A non-technical beta tester can enter a realistic comparison task and receive a
reviewable matrix in under five minutes, with at least 80 percent of extracted
price cells backed by source citations and timestamps.
