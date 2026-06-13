# Acquisition Contract: tech-stack (NEW)

**Consumer:** `algolia-intel-techstack` (its DOM-detectable half). The skill keeps BuiltWith (paid API) enrichment, historical/removed-tech, and market-share — all out of Scout per the scope boundary.

The #1 displacement signal: is the prospect already on Algolia, on a competitor we can displace (Elasticsearch, Coveo, Bloomreach, Constructor, Searchspring, Klevu, Lucidworks, endeca/ATG), or greenfield? Detected from the open web only — no paid API.

## Input contract
`url`/`query`: company domain or any page URL. Accepts `targets[]`. Best signal from homepage + a search/category page.

## Acquisition plan
1. Fetch homepage + one search/listing page (browser rung to capture runtime-injected scripts and network calls).
2. **Fingerprint from:** script `src` patterns, global JS objects (e.g. `window.__algolia`, `window.coveoHeadless`), network requests (e.g. `*.algolia.net`, `*-dsn.algolia.net`, `*.coveo.com`, `*.bloomreach.com`), `<meta name="generator">`, link/CSS signatures, cookie names, response headers (Server, X-Powered-By, CDN/WAF headers), well-known paths.
3. Match against a maintained deterministic **fingerprint table** (vendor → signals). Categories: search vendor, ecommerce platform, CDN/WAF, analytics, tag manager, personalization/CDP.
4. Each detection records the exact evidence (the matching script URL / network call / header value).

## Record types & fields (F = extraction, T = deterministic classification)
**`tech_stack.v1`** (one per target)
- detections[] — each: category (T), vendor (T: from fingerprint table), evidence (F: the literal script URL / network host / header / JS global that matched), match_type (T: script|network|header|cookie|meta|path|jsglobal), confidence
- search_vendor (T: convenience top-level — the detected search category winner, or "none detected"/"first-party")
- is_algolia (T: bool — already a customer signal), competitor_search (T: vendor name if a displaceable search vendor detected)
- source_urls[], citations[] (each detection cites the page + the matched artifact)

Out of scope (consumer keeps): BuiltWith enrichment, removed/historical tech, spend estimates, vendor market share, "should they switch" judgment.

## Confidence rules
0.95 network-call or JS-global match (runtime proof the vendor is live), 0.85 script-src match, 0.7 header/meta/cookie, 0.5 path-only guess (flagged). "none detected" is a valid honest result, not low confidence.

## Golden e2e flow
Run `tech-stack` on a known Algolia-powered site → `tech_stack.v1` with is_algolia=true and a network-call or jsglobal evidence string containing "algolia". Run on a known Coveo/Elasticsearch site → competitor_search set with matching evidence. Run on a site with first-party search → search_vendor "first-party"/"none detected", no fabricated vendor.
