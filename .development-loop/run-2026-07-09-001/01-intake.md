# 01 - Intake: Comparative Intelligence

Date: 2026-07-09
Requestor: Arijit
Run: run-2026-07-09-001

## Trigger

Private beta feedback suggested Scout should make business use cases obvious and
support competitive pricing/product research. Arijit identified this as a real
product extension requiring a dedicated development spike.

## Problem

Scout currently proves it can extract website data, but non-technical users want
business outcomes. Competitive pricing and market comparison are clearer value
propositions than "crawler" or "scraper."

## Proposed Feature

Comparative Intelligence: a workflow that collects price/product/service data
across multiple websites and returns a normalized, cited comparison matrix.

## Personas

- Founder launching a product.
- Retail/ecommerce analyst.
- Hotel or local business operator.
- Agency/consultant producing market scans.
- Developer integrating Scout into a research workflow.

## Initial Use Cases

- Same-product price comparison across retailers.
- New-product launch pricing research.
- Local hotel nightly rate benchmarking.
- Competitor pricing-page monitoring.

## Scope Recommendation

Start with product price comparison using user-supplied sources. This reuses the
existing product extraction contract and proves the cross-source comparison
engine before adding hotel-specific complexity.

## Human Gates

- Confirm whether this enters active roadmap now or stays as future backlog.
- Pick first vertical.
- Approve source policy and hosted pricing/credit treatment.
