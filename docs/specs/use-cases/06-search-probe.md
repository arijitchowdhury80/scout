# Acquisition Contract: search-probe (NEW)

**Consumer:** `algolia-audit-browser`. Today the skill does this by hand with stealth Playwright; Scout systematizes the *capture*. The skill keeps everything judgmental: which queries to run (that's `algolia-intel-queries`), and rating relevance/quality/zero-results severity.

Depends on the embedded live browser (Phase C0.6) — runs queries on the prospect's OWN on-site search.

## Input contract
`url`: the prospect site (or its search URL/endpoint if known). `queries[]`: the query mix to run — **supplied by the consumer** (Scout does not invent the query set; generating a smart mix is judgment owned by `algolia-intel-queries`). Option: `default_probe` (a small deterministic fallback set — one broad term, one known-misspelling, one specific SKU/long-tail — used only if no queries supplied, clearly labeled as generic).

## Acquisition plan
1. Open the site in the browser rung; locate the search input (reuse site-signals has_search detection).
2. For each query: type it, submit, wait for results to settle, capture.
3. Capture per query: result count (where shown/derivable), zero-results boolean, top-N result titles, response timing, full screenshot, and the results-page URL/network response shape if exposed.
4. No interpretation — just faithful capture of what the site returned.

## Record types & fields (F = extraction)
**`search_probe.v1`** (one per query)
- query (F: echoed input), results_page_url (F), result_count (F: extracted/derived or null), zero_results (F: bool)
- top_results[] (F: titles/links as returned), response_ms (F: measured), screenshot_path (F: artifact)
- captured_at (F), source (F: the search surface), citations[], confidence

Out of scope (consumer keeps): relevance rating, "good/bad" verdicts, typo-tolerance/synonym/NLP judgments, severity scoring, the query strategy itself.

## Confidence rules
0.9 captured with result_count + screenshot from a detected search surface; 0.6 search input detected but result_count not derivable (screenshot still captured, flagged). Search input not found → no records + a documented "no on-site search detected" note (a finding in itself, handed to site-signals/audit).

## Golden e2e flow
Run `search-probe` on a retail site with queries ["red running shoes","reb running shoes","<known SKU>"] → 3 `search_probe.v1`, each with a screenshot artifact and zero_results boolean; the misspelling probe records whatever the site returned (recovered vs zero) without rating it; a no-search site yields the documented no-search note, not a crash.
