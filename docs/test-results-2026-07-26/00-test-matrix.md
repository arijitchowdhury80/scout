# Scout Launch-Readiness Test Matrix — LIVE PROD (https://scout.chowmes.com)

Date created: 2026-07-26
Owner: Scout e2e harness (`harness/`)
PRD reference: `docs/workspace/scout-core/04-prd.md` (AC-1..AC-12)

## Sites under test

| Site | Type | Notes |
|---|---|---|
| algolia.com | SaaS/marketing | company + careers vertical target |
| adobe.com | Enterprise SaaS | company + careers vertical target, heavier page weight |
| salesforce.com | Enterprise SaaS | company + careers vertical target |
| lacoste.com | Ecommerce | products vertical target |
| eyebuydirect.com | Ecommerce | products vertical target |

## Scope notes (read before running)

- **N/A on hosted, do not test on prod:** `/extract` (LLM disabled on hosted), `/harvest` (CDP, not exposed on hosted), `/app/*` (being deleted). Every row for these is marked `na`.
- **Known gap — careers 24h filter:** the careers vertical runner does not yet filter job postings to "posted in the last 24h." Pass criteria below test that the vertical *returns job records at all* with correct shape; the recency filter is explicitly out of scope and must not be reported as a defect.
- **Known gap — "top-selling" products:** Scout has no signal for actual sales velocity. The products vertical/endpoint is tested for volume + shape only. Any "best seller" framing in reporting must say "best-seller-proxy (e.g. positional/badge heuristic), not verified sales data" — never fabricate a top-seller claim.
- Async: `HOSTED_ASYNC_FIRST=true` means most `POST` calls return `202` + `job_url`; the harness polls `GET /v1/hosted/jobs/{job_id}` until `status == "done"`/`"complete"`/`"error"`, then reads `result`. Vertical/company/products runs may also be read back via `GET /v1/hosted/runs/{run_id}/records` and `/artifacts`.
- Credit costs (standard credits unless noted): scrape/crawl-page/map-page = 1 credit each; screenshot = 3 credits; products/run = 1 credit per record up to `max_products`/`max_records` (preflight-checked, not necessarily fully charged if the run returns fewer records — see `scout/core/platform/hosted.py::HostedAction`).

## Matrix

| Capability | Endpoint | Request body | Expected shape (AC) | Pass criteria | Credit cost | Notes |
|---|---|---|---|---|---|---|
| scrape | `POST /v1/hosted/scrape` | `{"url": "https://<site>"}` | AC-1: `success=true`, non-empty `markdown`, `metadata.title` set, `metadata.word_count > 0`, `duration_ms > 0` (delivered inside `HostedScrapeResponse.scrape` after job completes) | Job reaches `status=done`/`complete`; `result.scrape.success == true`; `word_count > 0` | 1 credit | Run once per site (5 rows) |
| crawl (>=10 pages) | `POST /v1/hosted/crawl` | `{"url": "https://<site>", "max_pages": 10}` | AC-3: `total_pages >= 1` and at least one page has non-empty `markdown`; harness additionally asserts `total_pages >= 10` since the matrix requires >=10 pages | Job completes; `result.crawl.total_pages >= 10`; >=1 page `success=true` with non-empty markdown | 10 credits (1/page) | Run once per site (5 rows) |
| map | `POST /v1/hosted/map` | `{"url": "https://<site>", "max_pages": 100}` | AC-5: `urls` list with >=1 URL, `total >= 1` | Job completes; `result.map.total >= 1`; `urls` non-empty | up to 100 credits (1/page discovered, plan-capped) | Run once per site (5 rows) |
| screenshot (homepage) | `POST /v1/hosted/screenshot` | `{"url": "https://<site>", "full_page": true}` | AC-6: non-empty `screenshot_base64`, correct `width`/`height` | Job completes; `result.screenshot.screenshot_base64` non-empty; `width`/`height` > 0; base64 decodes to a valid PNG (harness writes it to `<site>/screenshot.png` and checks the PNG magic bytes) | 3 credits | Run once per site (5 rows) |
| company vertical | `POST /v1/hosted/run/company` | `{"use_case": "company", "url": "https://<site>", "max_records": 50}` | AC-1/AC-3 analog for structured runs: `success=true`, `manifest` populated, `total_records >= 1`; records include company profile + at least one exec and one social record | Job completes; `run.total_records >= 1`; `GET /v1/hosted/runs/{run_id}/records` contains >=1 record tagged as company profile, >=1 exec/leadership record, >=1 social record | up to 50 credits | algolia.com, adobe.com, salesforce.com only (not ecommerce sites) |
| careers vertical | `POST /v1/hosted/run/careers` | `{"use_case": "careers", "url": "https://<site>", "max_records": 50}` | Structured run returns job posting records with title/location/department fields | Job completes; `run.total_records >= 1`; records include job listings. **KNOWN GAP:** no 24h-recency filter exists yet — do not fail/flag on stale postings, only on missing job records entirely | up to 50 credits | algolia.com, adobe.com, salesforce.com only |
| products (>=100 records) | `POST /v1/hosted/products` | `{"start_url": "https://<site>/<category>", "max_products": 100, "max_categories": 5}` | Products response: `total_products >= 1`; harness additionally asserts `total_products >= 100` | Job completes; `result.products.total_products >= 100`; records have `name`+`url`; note in report: "top-selling" is a **KNOWN GAP** — no sales-velocity signal exists, so any "best seller" framing is a best-seller-proxy (badge/position heuristic) only, never a fabricated sales claim | up to 100 credits | lacoste.com, eyebuydirect.com only (product sites) |
| prism bundle | `POST /v1/hosted/run/prism` | `{"use_case": "prism", "url": "https://<site>", "max_records": 100}` | Aggregate PRISM evidence bundle: `success=true`, `manifest` populated, artifacts include a report/manifest bundling company+careers+investor+news evidence | Job completes; `run.total_records >= 1`; `GET /v1/hosted/runs/{run_id}/artifacts` returns a non-empty artifact set | up to 100 credits | **One site only** — algolia.com (per spec: "one site") |
| /extract | N/A on hosted | — | LLM disabled on hosted | `na` — do not call | 0 | Do not test on prod |
| /harvest | N/A on hosted | — | CDP not exposed on hosted | `na` — do not call | 0 | Do not test on prod |
| /app/* | N/A on hosted | — | Being deleted | `na` — do not call | 0 | Do not test on prod |

## Row count reconciliation

- scrape: 5 (one per site)
- crawl: 5
- map: 5
- screenshot: 5
- company: 3 (algolia, adobe, salesforce)
- careers: 3 (algolia, adobe, salesforce)
- products: 2 (lacoste, eyebuydirect)
- prism: 1 (algolia.com)
- extract/harvest/app: 3 rows, all `na`

Total authed rows to execute once a key is available: **32** (29 live calls + 3 na markers).

## Evidence layout

Each executed row writes:
- `docs/test-results-2026-07-26/<site>/<capability>.json` — raw job/result JSON
- `docs/test-results-2026-07-26/<site>/<capability>.png` (screenshot only)
- `docs/test-results-2026-07-26/verdicts.csv` — one row per (site, capability): `pass|fail|na`, evidence path, HTTP codes seen, notes
