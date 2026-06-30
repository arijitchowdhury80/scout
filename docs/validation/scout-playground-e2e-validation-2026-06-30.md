# Scout Playground E2E Validation - 2026-06-30

## Scope

Validate the public Scout Playground end to end across every listed capability:

- `scrape`
- `crawl`
- `map`
- `screenshot`
- `extract`
- `products`
- `company`
- `prism`
- `investor`
- `careers`
- `jobs`
- `news`
- `research`
- `docs`
- `social`
- `locations`
- `website-quality`

## What Was Added

- `tests/e2e/test_playground_full_e2e.py`
  - Opens the real static `/quickstart.html` page in Chromium.
  - Selects every workflow option from the playground dropdown.
  - Verifies workflow-specific helper copy.
  - Verifies scheme-less URLs normalize into `https://...`.
  - Verifies generated cURL payloads.
  - Clicks every playground output tab: Preview, JSON, Markdown, cURL.
  - Clicks and inspects JSON and Markdown downloads for every workflow.
  - Verifies every UI run sends the expected workflow, URL, query, and limit.

- `tests/live/test_playground_live_workflows.py`
  - Starts a local Scout HTTP server.
  - Calls the real `/v1/playground/run` endpoint for every workflow.
  - Uses safe public example URLs.
  - Verifies HTTP 200, `success=true`, nonzero records, and downloadable JSON/Markdown.

## Example Targets Used

| Workflow | Example |
|---|---|
| scrape | `https://example.com` |
| crawl | `https://example.com` |
| map | `https://example.com` |
| screenshot | `https://example.com` |
| extract | `https://example.com` |
| products | `https://books.toscrape.com/` |
| company | `https://www.algolia.com` |
| prism | `https://www.algolia.com` |
| investor | `https://www.adobe.com/investor-relations.html` |
| careers | `https://www.adobe.com/careers.html` |
| jobs | `https://jobs.ashbyhq.com/kong` |
| news | `https://www.algolia.com/blog` |
| research | `https://openai.com/news` |
| docs | `https://www.algolia.com/doc/` |
| social | `https://www.algolia.com` |
| locations | `https://example.com` |
| website-quality | `https://example.com` |

## Failures Found

| Failure | Root Cause | Fix |
|---|---|---|
| Browser rejected `www.algolia.com` as missing URL | Playground URL field used `type="url"`, so native browser validation blocked submit before JS ran | Changed field to `type="text"` with `inputmode="url"` and normalized missing schemes in JS |
| Direct playground API rejected `example.com`/`www.algolia.com` with 403 | Server-side URL safety ran before adding a default scheme | Added backend URL normalization before safety validation |
| `crawl` summary had `blocked_count=null` in live output | Crawl playground response omitted `blocked_count` | Added `blocked_count: 0` to crawl response summary |
| `social` returned zero records in first live probe | The test used `example.com`, which has no social profile links | Live certification now uses `https://www.algolia.com`, which returns social records |

## Verification Commands

```bash
python3 -m pytest tests/e2e/test_playground_full_e2e.py -v
SCOUT_LIVE_TESTS=1 python3 -m pytest tests/live/test_playground_live_workflows.py -v
python3 -m pytest tests/unit/api/test_playground.py tests/unit/website/test_launch_website.py tests/e2e/test_playground_full_e2e.py -q
python3 -m pyright scout/
ruff check scout/ tests/
ruff format --check scout/ tests/
```

## Latest Results

| Command | Result |
|---|---|
| `python3 -m pytest tests/e2e/test_playground_full_e2e.py -v` | Passed, all 17 UI workflows |
| `SCOUT_LIVE_TESTS=1 python3 -m pytest tests/live/test_playground_live_workflows.py -v` | Passed, all 17 real backend workflows in 155.67s after fixes |
| `python3 -m pytest tests/unit/api/test_playground.py tests/unit/website/test_launch_website.py tests/e2e/test_playground_full_e2e.py -q` | Passed, 29 tests |
| `python3 -m pyright scout/` | Passed, 0 errors |
| `ruff check scout/ tests/` | Passed |
| `ruff format --check scout/ tests/` | Passed, 226 files formatted |

## Status

The Scout Playground is now validated at two levels:

1. Deterministic browser UI E2E across every visible workflow and playground control.
2. Live local backend certification across every playground workflow using public example targets.

This does not replace broader hard-site/live matrix certification for Estée Lauder, Nike, Adobe, Home Depot, and other launch targets. It specifically certifies the public Playground surface and its all-workflow examples.
