# Scout e2e harness

Dependency-light Python (httpx only) harness that runs the launch-readiness
test matrix in `../00-test-matrix.md` against `https://scout.chowmes.com`.

## Requirements

```bash
python3 -m pip install httpx
```

No other dependencies. Never hardcodes a key — reads `SCOUT_BASE_URL` and
`SCOUT_API_KEY` from the environment.

## Dry run (no key needed)

Proves the harness works end to end by hitting only the public, unauthenticated
`/v1/demo/*` endpoints:

```bash
python3 scout_e2e.py --dry-run
```

Writes evidence to `../_dry-run/<capability>.json` and a verdict summary to
`../verdicts.csv`. Note: the demo endpoints are IP-rate-limited to ~5 runs/day
(shared across ALL demo callers on the box, including other testing done the
same day) — a `429` there is an expected quota response, not a harness bug.
Re-run tomorrow, or from a different IP, to see all four demo capabilities
pass.

## Full authed matrix (needs a real hosted API key)

```bash
export SCOUT_BASE_URL=https://scout.chowmes.com   # optional, this is the default
export SCOUT_API_KEY=<your hosted Bearer key>       # never hardcode this
python3 scout_e2e.py
```

This runs all 29 live rows described in `../00-test-matrix.md` (scrape/crawl/
map/screenshot across 5 sites, company+careers across 3 sites, products
across 2 sites, one prism bundle) plus 15 `na` markers for `/extract`,
`/harvest`, and `/app/*` (never called against prod). Each row:

1. POSTs to the relevant `/v1/hosted/*` endpoint.
2. If the response is `202` with a `job_id` (expected — `HOSTED_ASYNC_FIRST=true`
   on prod), polls `GET /v1/hosted/jobs/{job_id}` every 3s for up to 180s until
   the job reaches a terminal status.
3. Saves the raw JSON (job status + `result`) to
   `../<site>/<capability>.json`, plus `../<site>/screenshot.png` for the
   screenshot capability.
4. Appends one row to `../verdicts.csv`: `site,capability,verdict,http_codes,evidence_path,notes`.

Exit code is `0` if every row passed or was `na`, `1` if any row failed, `2`
if `SCOUT_API_KEY` is missing and `--dry-run` was not passed.

## Credits

This will consume real hosted credits from the configured API key — see the
credit-cost column in `../00-test-matrix.md` (roughly 32 credits for
scrape+crawl+map+screenshot per site, up to 50/100 for vertical/product runs).
Do not run against a production key without confirming the account has
enough balance and that spending it is expected.

## Extending the matrix

Add new `harness.run_authed_job(...)` calls in `run_authed_matrix()` in
`scout_e2e.py`, with a small `result_ok` validator function that returns
`(bool, str)` — pass/fail plus a one-line evidence note. Follow the existing
`_ok_*` functions as templates.
