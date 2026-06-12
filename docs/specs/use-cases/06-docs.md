# Acquisition Contract: docs

**Consumer:** general research / PRISM context; no dedicated skill yet.

## Input contract
`url`: documentation root or sitemap URL, or company domain (probes `/docs`, `/documentation`, `/developers`, `docs.{domain}`, `developers.{domain}`).

## Acquisition plan
1. Resolve doc root; prefer its sitemap; else nav-tree parse.
2. Extract section taxonomy (top-level nav groups) and page inventory.
3. Fetch top-level section landing pages (cap-bounded); deeper crawl only when `max_depth` raised.

## Record types & fields
**`doc_page.v1`** — title (F), url (F), section_path[] (F: nav ancestry), first_paragraph (F: verbatim), last_updated (F: if exposed), citations[], confidence.
Run metadata: section taxonomy tree, total pages discovered vs fetched.

## Confidence rules
0.9 fetched page; 0.6 discovered-but-not-fetched inventory entries (flagged `fetched: false`).

## Golden e2e flow
Run `docs` on `https://www.algolia.com/doc/` → complete; section taxonomy non-empty; ≥10 `doc_page.v1` with section_path; fetched pages have verbatim first_paragraph present in source.
