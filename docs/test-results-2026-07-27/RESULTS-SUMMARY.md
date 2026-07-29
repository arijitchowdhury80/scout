# Scout e2e capability matrix — LIVE PROD rerun, 2026-07-27

**Target:** https://scout.chowmes.com (authed hosted API, live prod)
**Harness:** `docs/test-results-2026-07-27/scout_e2e_20260727.py` (copy of the 07-26 harness with two
test-methodology fixes — see "Harness changes" below — no Scout application code was touched)
**Purpose:** re-verify the FX-1/FX-4/browser-fallback fixes described as "deployed" and measure
distance to 100% on the same 44-row matrix used on 2026-07-26.

## Headline result

**Pass/fail/na is byte-for-byte identical to the 2026-07-26 baseline: 11 pass / 18 fail / 15 na.**
Same 11 rows pass, same 18 rows fail, same numbers in the notes (`word_count=904`,
`total_pages=30`, `total_records=4/1/11`, `total_products=0`, `empty screenshot_base64`) row for
row. None of the fixes changed a single verdict on live prod against these five sites.

| Metric | 2026-07-26 baseline | 2026-07-27 rerun |
|---|---|---|
| Pass | 11 | 11 |
| Fail | 18 | 18 |
| N/A  | 15 | 15 |
| Total | 44 | 44 |

Full row-by-row diff: `docs/test-results-2026-07-27/verdicts.csv` vs
`docs/test-results-2026-07-26/verdicts.csv`.

## The three things this run was specifically asked to check

### 1. adobe.com / salesforce.com — do they render now?

**No.** Both still fail `scrape`, `crawl`, and `screenshot` with the identical error captured on
07-26:

```
Error: Failed on navigating ACS-GOTO:
Page.goto: net::ERR_HTTP2_PROTOCOL_ERROR at https://adobe.com/
```

(same for salesforce.com). `status_code: null`, `word_count: 0`, `screenshot_base64: ""`.
Evidence: `adobe.com/scrape.json`, `adobe.com/crawl.json`, `adobe.com/screenshot.json`,
`salesforce.com/scrape.json`, `salesforce.com/crawl.json`, `salesforce.com/screenshot.json`.

`map` passes for both (returns 1 URL for adobe, 100 for salesforce) because map doesn't need
crawl4ai to render the page body — it's a weaker signal, not evidence the render path works.

This directly cascades into `company` and `careers` for both sites returning
`total_records: 0` (`"warnings": ["company produced no records."]`) — the vertical runners
depend on the same crawl4ai render path.

**Verdict: the HTTP2 rendering failure is not fixed. It is 100% reproducible, not transient,
against these two specific domains on live prod as of 2026-07-27.**

### 2. lacoste.com / eyebuydirect.com — do products return real records now?

**No — 0 real records from either site**, but for two *different* reasons, both captured in the
saved evidence with real detail (not previously documented):

- **lacoste.com**: `blocked_pages: [{"reason": "no_product_records", "fallback_attempted": false}]`
  — the primary extractor found nothing and the browser fallback was **never triggered** for this
  site. `docs/test-results-2026-07-27/lacoste.com/products.json`.

- **eyebuydirect.com**: fallback *was* attempted, but it crashed before it could try to render
  anything:
  ```
  BrowserType.launch: Target page, context or browser has been closed
  Looks like you launched a headed browser without having a XServer running.
  Set either 'headless: true' or use 'xvfb-run <your-playwright-app>' before running Playwright.
  ...
  ERROR:ui/ozone/platform/x11/ozone_platform_x11.cc:257] Missing X server or $DISPLAY
  ```
  This is a **new, previously-undocumented root cause**: the products browser-fallback path in
  the deployed container launches Chromium in headed mode with no X server / Xvfb present, so it
  always dies on launch — regardless of whether Akamai would have blocked it. We never got far
  enough to observe an Akamai block. `docs/test-results-2026-07-27/eyebuydirect.com/products.json`.

**Verdict: the browser-fallback fix did not produce real product records for either site.
lacoste never reaches fallback; eyebuydirect's fallback is broken at the container level
(missing Xvfb/DISPLAY), not blocked by Akamai.**

### 3. algolia.com company vertical — are executives extracted now (was 0)?

**Still 0.** The company run reports `success: true, total_records: 4` and *passes* the harness's
generic "≥1 record" check, but the 4 records are 1 low-quality `company` record (`name: "unknown"`,
garbage `description` scraped from nav/filter chrome) plus 3 `company_social` records
(LinkedIn/Twitter/Facebook URLs). **Zero `executive`-typed records.** Pulled the actual records
via `GET /v1/hosted/runs/run_6dc994a29078/records` (saved to
`algolia.com/company-records.json`) since the job response only returns a manifest, not the
records themselves — worth noting for anyone reading job JSON expecting inline records.

**Verdict: FX-4 (JSON-LD/team-cards executive extraction) is not surfacing executives on live
prod for algolia.com. The harness's pass/fail check for "company" only verifies `total_records
>= 1`, which is why this reads as a pass in verdicts.csv despite having no executives — that's a
matrix-validator gap, not a claim that this row is actually healthy.**

## Every other real failure with its surfaced error (FX-1c)

All failures below have `status_code` and `error_message` genuinely present in the saved JSON —
none were the generic "job errored" placeholder from before FX-1c.

| Site | Capability | HTTP codes | Surfaced error |
|---|---|---|---|
| adobe.com | scrape | 202,200,200 | `net::ERR_HTTP2_PROTOCOL_ERROR` on `Page.goto` |
| adobe.com | crawl | 202,200,200 | same, `total_pages=1` |
| adobe.com | screenshot | 202,200,200 | same, empty `screenshot_base64` |
| salesforce.com | scrape | 202,200,200 | same `ERR_HTTP2_PROTOCOL_ERROR` |
| salesforce.com | crawl | 202,200,200 | same, `total_pages=1` |
| salesforce.com | screenshot | 202,200,200 | same, empty `screenshot_base64` |
| lacoste.com | scrape | 202,200,200 | same `ERR_HTTP2_PROTOCOL_ERROR` |
| lacoste.com | crawl | 202,200,200 | same, `total_pages=1` |
| lacoste.com | screenshot | 202,200,200 | same, empty `screenshot_base64` |
| eyebuydirect.com | scrape | 202,200,200 | same `ERR_HTTP2_PROTOCOL_ERROR` |
| eyebuydirect.com | crawl | 202,200,200 | same, `total_pages=1` |
| eyebuydirect.com | screenshot | 202,200,200 | same, empty `screenshot_base64` |
| adobe.com | company | 202,200×5 | `"company produced no records."` (0 records; cascades from HTTP2 fail) |
| adobe.com | careers | 202,200×3 | same, 0 records |
| salesforce.com | company | 202,200×3 | same, 0 records |
| salesforce.com | careers | 202,200×2 | same, 0 records |
| lacoste.com | products | 202,200,200 | `reason: "no_product_records"`, fallback never attempted |
| eyebuydirect.com | products | 202,200×3 | fallback attempted, crashed: `Missing X server or $DISPLAY` (Playwright headed-browser launch, no Xvfb in container) |

Note: `eyebuydirect.com` and `adobe.com`/`salesforce.com` scrape/crawl/screenshot all show the
*same* `ERR_HTTP2_PROTOCOL_ERROR` signature as adobe/salesforce — this is not adobe/salesforce-
specific, it reproduces on lacoste.com and eyebuydirect.com too. Whatever is causing it isn't
site-specific; the memory note calling this "resource-OOM under load, not a config bug" is worth
re-examining given it now blocks 4 of 5 test sites identically and consistently (not
intermittently) across two independent runs a day apart.

## What passed (11/44, unchanged from baseline)

- algolia.com: scrape, crawl (30 pages), map (100 URLs), screenshot, company (4 records, no
  executives — see caveat above), careers (1 record), prism (11 records)
- adobe.com: map (1 URL — the only URL crawl4ai could reach before HTTP2 failure)
- salesforce.com: map (100 URLs)
- lacoste.com: map (1 URL)
- eyebuydirect.com: map (100 URLs)

## Algolia push

**Not performed.** Both `lacoste.com` and `eyebuydirect.com` products runs returned
`total_records: 0` — there were no real product records to push to `scout_lacoste` /
`scout_eyebuydirect`. Pushing nothing and calling it "verified searchable" would be a false-green
claim; skipped per instructions to report honestly rather than force a pass.

## Credits consumed

- Standard credits: **609 used this session** across both harness runs (balance 4814 → 4572 after
  attempt 1 → 4205 after the clean rerun). The account's lifetime `standard_credits_used` counter
  reads 795 (186 pre-existing + 609 this session) — don't mistake that lifetime figure for this
  session's spend. Well above the 500-credit floor — no need to stop.
- Browser credits: **0 used** (100/100 remaining) — the browser-fallback path never got past
  launch for eyebuydirect, and was never triggered for lacoste, so no browser-credit-metered work
  actually ran.

## Harness changes (test methodology only — no Scout app code touched)

The first attempt (`run.attempt1.log`) hit a real operational issue: the hosted API rate-limits
at 60 req/60s (`scout/api/config.py: hosted_rate_limit_max_requests=60`), and the original
harness's 3s poll interval + no 429 backoff meant one 429 during a long-running job's polling
cascaded into every subsequent request in the run 429-ing too (20 of 44 rows failed as `429 Too
Many Requests`, masking the real signal). Fixed for the rerun used in this report:

1. `POLL_INTERVAL_SECONDS` 3 → 8s.
2. Added `_retry_on_429` with `Retry-After`-aware backoff (up to 6 attempts) wrapping every POST
   and GET.
3. `crawl` `max_pages` 10 → 25 per this task's ask (actual observed: `total_pages=30` for
   algolia.com — sitemap discovery exceeded the request pages hint).
4. `TERMINATE_AFTER_SECONDS` 180 → 600 to give slower verticals/products room to finish before
   timing out under the longer poll interval.
5. Output redirected to `docs/test-results-2026-07-27/`.

The failed first attempt's raw log is preserved at `run.attempt1.log` for reference; its
verdicts.csv was overwritten by the clean rerun's — do not treat attempt 1's 429-cascade failures
as real capability failures, they're a rate-limit artifact of the harness, not the API under
test. The clean rerun's log is `run.log`.
