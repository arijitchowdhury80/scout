# Scout E2E Capability Matrix — LIVE PROD Results

Run date: 2026-07-27 (UTC timestamps in evidence files)
Target: `https://scout.chowmes.com` (hosted_beta_pass plan, tenant `tenant_ba3608342ea9475f96d15ae737bf9c13`)
Harness: `harness/scout_e2e.py` + three ad-hoc driver scripts (`scout_e2e_driver.py` → crashed on a
transient 429, `scout_e2e_driver2.py` → resumed, hit a real plan-cap 403 on verticals, killed,
`scout_e2e_driver3.py` → completed the matrix with corrected request bodies). All three drivers
lived in the scratchpad, not this repo. Every row below is backed by a raw JSON (or JSON+PNG)
evidence file under `<site>/` in this directory.

## Verdict counts

**Overall: 44 rows — 11 pass, 18 fail, 15 na.**

| Site | Pass | Fail | N/A | Notes |
|---|---|---|---|---|
| algolia.com | 7 | 0 | 3 | Only site where the crawler could render pages at all |
| adobe.com | 1 | 5 | 3 | Only `map` passed (1 URL discovered) |
| salesforce.com | 1 | 5 | 3 | Only `map` passed (25 URLs discovered) |
| lacoste.com | 1 | 4 | 3 | Only `map` passed (1 URL — sitemap discovery also degraded) |
| eyebuydirect.com | 1 | 4 | 3 | Only `map` passed (25 URLs discovered) |

Per-capability:

| Capability | Pass | Fail | N/A |
|---|---|---|---|
| scrape | 1 (algolia) | 4 | — |
| crawl | 1 (algolia) | 4 | — |
| map | 5 (all sites, after fixing max_pages) | 0 | — |
| screenshot | 1 (algolia) | 4 | — |
| company | 1 (algolia) | 2 (adobe, salesforce) | — |
| careers | 1 (algolia) | 2 (adobe, salesforce) | — |
| products | 0 | 2 (lacoste, eyebuydirect) | — |
| prism | 1 (algolia) | 0 | — |
| extract/harvest/app | — | — | 15 (3 × 5 sites, per matrix scope) |

## Credits consumed

- **182 standard credits** used (5000 → 4818 remaining). Never dropped near the 500-credit floor —
  lowest point during the run was ~4818, comfortably above the stop threshold.
- **0 browser credits** used (100/100 remaining) — no capability in this matrix drew on the browser-credit pool.
- Final live check: `GET /v1/hosted/me` → `standard_credits_remaining: 4818`, `browser_credits_remaining: 100`.
  Saved at `harness/final_credit_check.json`.
- Runs stayed sequential throughout (single httpx client, blocking calls, `max_concurrent_runs=1` on
  the key was never exceeded).

## Two real, deterministic defects found in the test setup itself (not Scout bugs — request-shape mismatches against the matrix spec)

1. **`POST /v1/hosted/map` with `max_pages: 100` → `403 {"detail":"Plan allows at most 25 URLs per map."}`.**
   The matrix spec (`00-test-matrix.md` row 31) calls for `max_pages: 100`; the account's plan hard-caps
   at 25 (matches `limits.max_pages_per_run: 25` from `/v1/hosted/me`). Fixed by re-running with
   `max_pages: 25` — all 5 sites then passed the map capability.
2. **`POST /v1/hosted/run/company` / `run/careers` with `max_records: 50`, and `POST /v1/hosted/products`
   with `max_products: 100` → `403 {"detail":"Plan allows at most 25 records per hosted run."}` /
   `{"detail":"Plan allows at most 25 products per request."}`.**
   Same root cause: the matrix spec's request bodies exceed the plan's flat 25-record-per-call cap.
   Re-ran company/careers/prism with `max_records: 25` (all three subsequently reached their pass bar
   for algolia.com). For products this created a **hard conflict with the task's own >=100-record
   target** — see below.

Both are pre-flight validation rejections; neither one debited credits (confirmed via the flat credit
balance across the 403 rows in the raw evidence).

## Real product FAILURES (genuine Scout defects, not harness artifacts)

Independently re-confirmed each of these via a second, isolated retry outside the main harness run —
none of it is a one-off flake.

- **`adobe.com` — scrape / crawl / screenshot / company / careers all fail.**
  Root cause: `net::ERR_HTTP2_PROTOCOL_ERROR` when crawl4ai's Playwright browser navigates to
  `https://adobe.com/`. Confirmed twice (initial run + isolated retry, job `job_79f33819b1a746b4`).
  Evidence: `adobe.com/scrape.json`, `adobe.com/crawl.json`, `adobe.com/screenshot.json`,
  `adobe.com/company.json`, `adobe.com/careers.json`.
- **`salesforce.com` — scrape / crawl / screenshot / company / careers all fail.**
  Same `net::ERR_HTTP2_PROTOCOL_ERROR` signature as adobe.com.
  Evidence: `salesforce.com/scrape.json`, `salesforce.com/crawl.json`, `salesforce.com/screenshot.json`,
  `salesforce.com/company.json`, `salesforce.com/careers.json`.
- **`lacoste.com` — scrape / crawl / screenshot / products all fail.**
  Same `net::ERR_HTTP2_PROTOCOL_ERROR` signature. `map` also degraded (only discovered the homepage
  URL itself, `total=1`, instead of a real sitemap) — technically "passes" the matrix's `total>=1` bar
  but is not a healthy result.
  Evidence: `lacoste.com/scrape.json`, `lacoste.com/crawl.json`, `lacoste.com/screenshot.json`,
  `lacoste.com/products.json`.
- **`eyebuydirect.com` — scrape / crawl / screenshot / products all fail.**
  Root cause is different from the other three sites and more specific:
  **"Blocked by anti-bot protection: Akamai block"** — confirmed via a targeted diagnostic scrape of a
  real category page (`https://www.eyebuydirect.com/eyeglasses/cheap`), which returned the explicit
  Akamai-block error message (`eyebuydirect.com/scrape_category_diagnostic.json`). `map` still passed
  (25 real category URLs discovered — sitemap/robots fetch apparently bypasses the block that blocks
  full-page rendering), but scrape/crawl/screenshot/products against actual page URLs all fail the
  same way.
- **`algolia.com/company` — passes the harness's simplified bar but misses the matrix's fuller spec.**
  `total_records=4` (1 company profile + 3 social records: LinkedIn/Twitter/Facebook), which satisfies
  the harness's `total_records >= 1` check. But the matrix's stated pass criteria also require
  ">=1 exec/leadership record" — **zero exec/leadership records were returned.** Flagging this as a
  partial miss, not a clean pass, even though verdicts.csv shows `pass`.
  Evidence: `algolia.com/company.json`, `algolia.com/company_records.json`.

### Products vertical — genuine capability failure, not a request-shape issue

`lacoste.com` and `eyebuydirect.com` both returned **`total_records: 0`** from `/v1/hosted/products`,
with `blocked_pages: [{"reason": "no_product_records", "fallback_attempted": true, "fallback_used": false}]`.
Tried three different inputs to rule out a bad start URL:
1. Homepage start URL, `max_products: 25` (corrected from the spec's 100) — 0 records, both sites.
2. A real category start URL for eyebuydirect.com (`/eyeglasses/cheap`, taken from its own successful
   `map` output) — still 0 records.
3. A direct diagnostic `scrape` of that same category URL — returned the explicit Akamai block error,
   confirming the products extractor is failing for the same underlying reason as the rest of the
   crawler on that domain.

**Conclusion: the products vertical could not extract a single real record from either target site on
live prod right now** — this is a genuine gap, not a test-harness bug, and it is far short of the
task's >=100-record target for both sites. No records exist to report a "best-seller-proxy" on either.

### Hard constraint conflict discovered live: products target vs. plan cap

Separately from the 0-record failure above: even if extraction had worked, the account's plan caps
`max_products` at **25 per request** (`{"detail":"Plan allows at most 25 products per request."}`),
while the task's own target was **>=100 records**. There is no documented multi-call aggregation path
in the matrix or the products endpoint that would let a single tenant legitimately reach >=100 records
per site within this plan's per-call ceiling — this is a real spec/plan mismatch worth flagging
upstream, independent of the Akamai/HTTP2 blocking issue.

## Algolia push verification

**Could not fulfill the original ask** ("push the two product sites' product records to
`scout_lacoste` / `scout_eyebuydirect`") **because there are zero real product records for either
site** — see above. Pushing anything to those index names would have required fabricating data, which
is explicitly prohibited by the task. No push was attempted for either target index; they do not exist.

**Ran a substitute, honest verification instead**, using real (non-fabricated) records that Scout did
successfully extract, to confirm the push mechanism itself works end-to-end:

- Took the 4 real company/social records returned by the algolia.com `company` vertical run
  (`run_9bc3f52609bb`) — 1 `company` record + 3 `company_social` records (LinkedIn/Twitter/Facebook).
- Pushed them via Scout's own connector, `POST /v1/hosted/destinations/send` with
  `{"destination": "algolia", "config": {"app_id": ..., "api_key": ..., "index_name": "scout_algolia_connector_verify"}, "records": [...]}`
  (this is the code path in `scout/api/routers/destinations.py` + `scout/core/platform/destinations.py::AlgoliaDestination`,
  which itself calls `algoliasearch`'s `save_objects`).
  Result: `HTTP 200`, `{"success": true, "result": {"records_sent": 4, "errors": []}}`.
  Evidence: `algolia-push-verification/push_result_scout_algolia_connector_verify.json`.
- Verified directly against the Algolia Search API (bypassing Scout, using the raw
  `ALGOLIA_APP_ID`/`ALGOLIA_API_KEY` from the test creds) with
  `POST https://<app_id>-dsn.algolia.net/1/indexes/scout_algolia_connector_verify/query {"query":"algolia"}`.
  Result: `nbHits: 4` — all 4 objects present and searchable, `objectID`s
  `company_unknown`, `social_unknown_linkedin`, `social_unknown_twitter`, `social_unknown_facebook`.
  Evidence: `algolia-push-verification/search_result_scout_algolia_connector_verify.json`.

**Conclusion:** the Algolia destination connector itself is real and functional end-to-end (push →
index → searchable) when given real records. The task's specific ask — push *product* records from
lacoste.com/eyebuydirect.com — is blocked purely by the products-vertical extraction failure above, not
by the connector.

## Evidence index

```
docs/test-results-2026-07-26/
├── verdicts.csv                              # 44-row definitive verdict table
├── algolia.com/{scrape,crawl,map,screenshot,company,careers,prism}.json (+screenshot.png)
│   └── company_records.json                  # real records pushed to Algolia (see above)
├── adobe.com/{scrape,crawl,map,screenshot,company,careers}.json
├── salesforce.com/{scrape,crawl,map,screenshot,company,careers}.json
├── lacoste.com/{scrape,crawl,map,screenshot,products}.json
├── eyebuydirect.com/{scrape,crawl,map,screenshot,products}.json
│   ├── products_category_retry.json          # 2nd products attempt, real category URL
│   └── scrape_category_diagnostic.json        # confirms Akamai block on a real page
├── algolia-push-verification/
│   ├── push_result_scout_algolia_connector_verify.json
│   └── search_result_scout_algolia_connector_verify.json
└── harness/
    ├── final_credit_check.json
    └── prism_run_id.json
```

## Caveats / scope notes carried over from the matrix spec

- `/extract`, `/harvest`, `/app/*` were never called against prod — all 15 rows are `na` by design
  (LLM disabled on hosted, CDP not exposed on hosted, `/app/*` being deleted).
- The careers 24h-recency filter is a known, out-of-scope gap and was not scored as a defect — moot
  here anyway since careers only ran successfully for algolia.com (1 job record).
- "Top-selling" product framing was never at risk of fabrication because the products vertical
  returned zero records for both target sites — there was nothing to apply a best-seller-proxy label to.
