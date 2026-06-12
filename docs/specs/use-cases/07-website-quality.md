# Acquisition Contract: website-quality

**Consumer:** audit-research context. Measurement of the site itself — heuristics are deterministic, so this passes the boundary; *opinions* about UX stay out.

## Input contract
`url`: website URL.

## Acquisition plan
Homepage + up to N key templates (one category/listing page, one detail page where discoverable). Browser rung used to measure rendered state.

## Record types & fields
**`site_quality.v1`** (one per target) — all F, all measured:
- meta: title present/length, meta-description present/length, h1 count, canonical present, og tags present
- structure: nav link count, footer link count, broken-link sample (HEAD top 20 internal links → status codes)
- weight: page bytes, request count, DOM node count (browser-measured)
- search: has-search-input detected (selector heuristics), search endpoint observed (form action / network hint)
- mobile: viewport meta present
- citations[] (each metric cites the page + measurement method), confidence

Out of scope: scoring, "UX gaps", competitor comparison, recommendations — consumer judgment.

## Confidence rules
0.9 browser-measured; 0.7 static-fetch-only run (no DOM metrics; flagged).

## Golden e2e flow
Run `website-quality` on `https://www.britishairways.com/` → complete; 1 `site_quality.v1` with ≥10 non-null metrics incl. has_search detection and a broken-link sample with real status codes.
