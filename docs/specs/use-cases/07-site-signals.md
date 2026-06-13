# Acquisition Contract: site-signals (renamed from website-quality)

**Consumer:** search audit (`algolia-audit-research` / `-browser`). Renamed because "quality" smuggles in a verdict — Scout **measures**, the audit skill **grades**.

## Input contract
`url`: website URL.

## Acquisition plan
Homepage + up to N key templates (one category/listing, one detail where discoverable). Browser rung to measure rendered state.

## Record types & fields (all F — measured facts)
**`site_signals.v1`** (one per target)
- meta: title present/length, meta-description present/length, h1 count, canonical present, og tags present, viewport meta present
- structure: nav link count, footer link count, broken-link sample (HEAD top 20 internal links → status codes)
- weight: page bytes, request count, DOM node count (browser-measured)
- search: has_search_input (selector heuristics), search_endpoint (form action / observed network call) — feeds search-probe
- citations[] (each metric cites the page + measurement method), confidence

Out of scope (consumer judgment): scores, "UX gaps", "weak/strong", recommendations, competitor comparison.

## Confidence rules
0.9 browser-measured; 0.7 static-fetch-only run (no DOM/weight metrics; flagged).

## Golden e2e flow
Run `site-signals` on britishairways.com → 1 `site_signals.v1` with ≥10 non-null measured metrics including has_search_input and a broken-link sample carrying real HTTP status codes. No metric expresses a verdict.
