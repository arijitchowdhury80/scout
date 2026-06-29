# Website Route And Render Verification

Date: 2026-06-29
Status: Launch website route/render smoke passed locally

## Scope

This verification covers the public launch website served by Scout's HTTP
service. It does not certify the legacy `/app` UI as a product surface. The
current release checklist explicitly keeps the legacy app UI out of launch
scope until it is rebuilt and certified.

## Commands

```bash
python3 -m pytest tests/unit/website/test_launch_website.py -q
```

Result:

```text
10 passed, 2 warnings in 1.45s
```

Warnings were Crawl4AI/Pydantic deprecation warnings from the installed
Crawl4AI dependency, not website test failures.

Server smoke:

```bash
SCOUT_API_KEY=dev-key \
SCOUT_WORKDIR=/tmp/scout-website-runs \
DB_PATH=/tmp/scout-website.db \
python3 -m scout.cli serve --host 127.0.0.1 --port 18423
```

## Route Results

| Route | Expected signal | Result |
|---|---|---|
| `/` | `Scout - Evidence-grade web acquisition for AI workflows` | Pass |
| `/?checkout=success` | Stripe checkout return status for successful hosted beta payment | Pass |
| `/?checkout=cancelled` | Stripe checkout return status for cancelled hosted beta checkout | Pass |
| `/quickstart` | `Scout Quickstart - Local-first web acquisition` | Pass |
| `/pricing` | `Scout Pricing - Free local, metered hosted beta` | Pass |
| `/beta` | `Scout Private Beta - Local install or hosted pass` | Pass |
| `/beta?checkout=success` | Stripe checkout return status for successful hosted beta payment | Pass |
| `/beta?checkout=cancelled` | Stripe checkout return status for cancelled hosted beta checkout | Pass |
| `/legal` | `Scout Legal And Third-Party Notices` | Pass |
| `/terms` | `Scout Beta Terms Placeholder` | Pass |
| `/privacy` | `Scout Beta Privacy Placeholder` | Pass |
| `/third-party-notices` | `Third-Party Notices` markdown content | Pass |
| `/styles.css` | public stylesheet content | Pass |
| `/health` | JSON status response | Pass |

Observed `/health` response:

```json
{"status":"ok","crawl4ai_version":"0.7.7","scout_version":"0.1.0"}
```

## Render Evidence

Screenshots were captured with Playwright Chromium at `1440x1100` from the
local Scout server:

- `docs/product/screenshots/website-2026-06-29/home.png`
- `docs/product/screenshots/website-2026-06-29/quickstart.png`
- `docs/product/screenshots/website-2026-06-29/pricing.png`
- `docs/product/screenshots/website-2026-06-29/beta.png`

## What This Proves

- The static launch website files exist and are covered by unit tests.
- The Scout HTTP service serves the public website routes without API auth.
- The hosted beta checkout return URLs surface success/cancel states instead
  of dropping testers back onto the site without context.
- The website now exposes the code-aligned hosted beta pass limits: 2,000
  standard credits, 100 browser credits, 7-day artifact retention, 100 pages
  per run, and 1 concurrent hosted run where relevant.
- The launch readiness checker verifies those hosted beta limit markers against
  the current `hosted_beta_pass` policy so website copy cannot silently drift
  back to vague "finite credits" language.
- The launch website can be rendered by a real browser.
- Public website copy continues to expose local-first install, finite hosted
  beta, legal/third-party notices, pricing direction, and beta boundaries.

## What This Does Not Prove

- It does not prove the old `/app` interface is usable.
- It does not close public launch blockers for license, dependency audit,
  Stripe real test-mode smoke, public registry publishing, or final legal terms.
- It does not certify live product extraction or intelligence module quality.
