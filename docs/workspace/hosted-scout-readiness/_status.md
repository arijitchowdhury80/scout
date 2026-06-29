# Hosted Scout Readiness Status

Date: 2026-06-28
Status: In progress

## 2026-06-29 VPS Hosted API Checkpoint

- Caddy now exposes Scout under
  `https://judge.contentengagement.info/scout/*`, proxying to the localhost-only
  Scout container.
- The Scout container was redeployed from the current repo source so the
  `/v1/hosted/*` Bearer-key routes are present.
- VPS env is set to `SCOUT_PUBLIC_HOSTED_ONLY=true` and
  `HOSTED_ACCOUNT_DB_PATH=/data/hosted_accounts.sqlite`.
- Docker compose was corrected to preserve `.env` secrets instead of
  overriding them with defaults, and to bind Scout only on
  `127.0.0.1:8421`.
- Verification passed:
  - public `/health` -> `200`;
  - hosted `/v1/hosted/me` without Bearer -> `401`;
  - hosted `/v1/hosted/scrape` without Bearer -> `401`;
  - `/api/config` -> `403`;
  - raw `/scrape` with local `X-API-Key` -> `403`;
  - hosted provisioned Bearer key -> `/v1/hosted/me` `200`;
  - hosted provisioned Bearer key -> `/v1/hosted/scrape` `200`, one standard
    credit charged.

## Checklist

- [x] Existing auth/settings/run persistence inspected.
- [x] Production architecture written.
- [x] Security and scale audit written.
- [x] Failing hosted policy tests written.
- [x] Minimal hosted policy module implemented.
- [x] Focused verification passed.
- [x] API-key lifecycle tests written.
- [x] API-key lifecycle module implemented.
- [x] API-key focused verification passed.
- [x] URL safety/SSRF tests written.
- [x] URL safety/SSRF module implemented.
- [x] URL safety focused verification passed.
- [x] Hosted account service tests written.
- [x] Hosted account service implemented.
- [x] Hosted account service verification passed.
- [x] Hosted admission service tests written.
- [x] Hosted admission service implemented.
- [x] Hosted admission service verification passed.
- [x] SQLite hosted account persistence tests written.
- [x] SQLite hosted account store implemented.
- [x] SQLite hosted account persistence verification passed.
- [x] Hosted HTTP scrape boundary tests written.
- [x] Hosted HTTP scrape boundary implemented.
- [x] Hosted HTTP scrape boundary verification passed.
- [x] Hosted beta provisioning CLI tests written.
- [x] Hosted beta provisioning CLI implemented.
- [x] Hosted beta provisioning CLI verification passed.
- [x] Hosted payment provisioning tests written.
- [x] Hosted payment provisioning service implemented.
- [x] Hosted payment provisioning verification passed.
- [x] Hosted Stripe webhook tests written.
- [x] Hosted Stripe webhook route implemented.
- [x] Hosted Stripe webhook verification passed.
- [x] Hosted key delivery contract tests written.
- [x] Hosted key delivery gate implemented.
- [x] Hosted key delivery verification passed.
- [x] Hosted SMTP key delivery tests written.
- [x] Hosted SMTP key delivery implemented.
- [x] Hosted SMTP key delivery verification passed.
- [x] Hosted Stripe Checkout Session tests written.
- [x] Hosted Stripe Checkout Session route implemented.
- [x] Hosted Stripe Checkout Session verification passed.
- [x] Hosted Stripe readiness endpoint implemented.
- [x] `.env.example` updated with hosted Stripe/SMTP settings.
- [x] Hosted per-key rate-limit tests written.
- [x] Hosted per-key rate limiter implemented.
- [x] Hosted per-key rate-limit focused verification passed.
- [x] Hosted crawl endpoint tests written.
- [x] Hosted crawl endpoint implemented.
- [x] Hosted crawl endpoint focused verification passed.
- [x] Hosted products endpoint tests written.
- [x] Hosted products endpoint implemented.
- [x] Hosted products endpoint focused verification passed.
- [x] Hosted high-level run endpoint tests written.
- [x] Hosted high-level run endpoint implemented.
- [x] Hosted high-level run endpoint focused verification passed.
- [x] Hosted run retrieval endpoint tests written.
- [x] Hosted run retrieval endpoints implemented.
- [x] Hosted run retrieval focused verification passed.

## Scope

Define and start the production-readiness foundation for hosted Scout:

- tenant model,
- API key lifecycle,
- Stripe/payment integration boundary,
- quota/credit policy,
- hosted usage limits,
- security risks,
- local-first vs hosted product decision.

This stream now includes SQLite account persistence, a Stripe-compatible payment
provisioning domain layer, a public Stripe Checkout Session creation route, and
a signed Stripe webhook route for `checkout.session.completed`. It also includes
a configurable process-local per-key hosted rate limiter for `/v1/hosted/*` and
hosted crawl admission at `/v1/hosted/crawl`, hosted product extraction at
`/v1/hosted/products`, hosted high-level runs at `/v1/hosted/run/{use_case}`,
and owner-key retrieval for hosted run summaries, records, and artifact paths.
Hosted run persistence now stores non-secret `tenant_id` and `key_id` ownership
metadata so retrieval authorization does not depend on output directory parsing.
It still does not implement user login, secure Customer Portal, distributed
throttling, production Postgres, a public dashboard, async hosted workers, or a
live SMTP/Stripe sandbox smoke.

Hosted beta configuration is now documented in `.env.example`. Local users only
need `SCOUT_API_KEY`, `SCOUT_WORKDIR`, and optional `LLM_API_KEY`; paid hosted
beta additionally needs Stripe Checkout, Stripe webhook, and SMTP key-delivery
settings. Hosted rate limits default to 60 requests per key per 60-second
window and should move to Redis/API-gateway enforcement before multi-instance
production hosting.

## Verification

- RED: `python3 -m pytest tests/unit/core/platform/test_hosted_policy.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.hosted'`.
- GREEN: `python3 -m pytest tests/unit/core/platform/test_hosted_policy.py -q`
  - Result: 6 passed.
- API-key RED: `python3 -m pytest tests/unit/core/platform/test_api_keys.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.api_keys'`.
- API-key GREEN: `python3 -m pytest tests/unit/core/platform/test_api_keys.py -q`
  - Result: 7 passed.
- URL safety RED: `python3 -m pytest tests/unit/core/platform/test_url_safety.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.url_safety'`.
- URL safety GREEN: `python3 -m pytest tests/unit/core/platform/test_url_safety.py -q`
  - Result: 9 passed.
- Hosted account service RED: `python3 -m pytest tests/unit/core/platform/test_account_service.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.account_service'`.
- Hosted account service GREEN: `python3 -m pytest tests/unit/core/platform/test_account_service.py -q`
  - Result: 6 passed.
- Hosted account checkpoint: `python3 -m pytest tests/unit/core/platform -q`
  - Result: 59 passed.
- Hosted admission RED: `python3 -m pytest tests/unit/core/platform/test_hosted_admission.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.hosted_admission'`.
- Hosted admission GREEN: `python3 -m pytest tests/unit/core/platform/test_hosted_admission.py -q`
  - Result: 6 passed.
- Hosted admission checkpoint: `python3 -m pytest tests/unit/ -q`
  - Result: 440 passed.
- SQLite hosted account persistence RED:
  `python3 -m pytest tests/unit/core/platform/test_account_sqlite_store.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.account_sqlite_store'`.
- SQLite hosted account persistence GREEN:
  `python3 -m pytest tests/unit/core/platform/test_account_sqlite_store.py -q`
  - Result: 3 passed.
- SQLite hosted account persistence checkpoint: `python3 -m pytest tests/unit/ -q`
  - Result: 443 passed.
- Hosted HTTP boundary RED:
  `python3 -m pytest tests/unit/api/test_hosted_scrape.py tests/unit/api/test_auth.py -q`
  - Result: failed because `get_hosted_account_service` did not exist.
- Hosted HTTP boundary GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_scrape.py tests/unit/api/test_auth.py -q`
  - Result: 9 passed.
- Hosted HTTP boundary checkpoint: `python3 -m pytest tests/unit/ -q`
  - Result: 447 passed.
- Hosted beta provisioning CLI RED:
  `python3 -m pytest tests/unit/cli/test_run_commands.py -q -k "hosted_provision"`
  - Result: failed with Typer exit code 2 because `hosted-provision` did not exist.
- Hosted beta provisioning CLI GREEN:
  `python3 -m pytest tests/unit/cli/test_run_commands.py -q -k "hosted_provision"`
  - Result: 2 passed.
- Hosted beta provisioning CLI checkpoint: `python3 -m pytest tests/unit/ -q`
  - Result: 449 passed.
- Hosted payment provisioning RED:
  `python3 -m pytest tests/unit/core/platform/test_payment_provisioning.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.payment_provisioning'`.
- Hosted payment provisioning GREEN:
  `python3 -m pytest tests/unit/core/platform/test_payment_provisioning.py -q`
  - Result: 6 passed.
- Hosted payment provisioning checkpoint:
  `python3 -m pytest tests/unit/core/platform -q`
  - Result: 74 passed.
- Hosted Stripe webhook RED:
  `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py -q`
  - Result: failed because `get_hosted_payment_provisioning_service` did not exist.
- Hosted Stripe webhook GREEN:
  `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  - Result: 12 passed.
- Hosted Stripe webhook API checkpoint:
  `python3 -m pytest tests/unit/api -q`
  - Result: 116 passed.
- Hosted Stripe webhook full unit checkpoint:
  `python3 -m pytest tests/unit/ -q`
  - Result: 461 passed.
- Hosted Stripe webhook static/lint checkpoint:
  `python3 -m pyright scout/` and `ruff check scout/ tests/ && ruff format --check scout/ tests/`
  - Result: pyright 0 errors; Ruff passed.
- Hosted key delivery gate RED:
  `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.key_delivery'`.
- Hosted key delivery gate GREEN:
  `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  - Result: 13 passed.
- Hosted key delivery gate full checkpoint:
  `python3 -m pytest tests/unit/api -q` and `python3 -m pytest tests/unit/ -q`
  - Result: API unit 117 passed; full unit 462 passed.
- Hosted key delivery static/lint checkpoint:
  `python3 -m pyright scout/` and `ruff check scout/ tests/ && ruff format --check scout/ tests/`
  - Result: pyright 0 errors; Ruff passed.
- Hosted SMTP key delivery RED:
  `python3 -m pytest tests/unit/core/platform/test_key_delivery.py -q`
  - Result: failed because `SmtpHostedApiKeyDeliveryConfig` did not exist.
- Hosted SMTP key delivery GREEN:
  `python3 -m pytest tests/unit/core/platform/test_key_delivery.py tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  - Result: 17 passed.
- Hosted SMTP key delivery full checkpoint:
  `python3 -m pytest tests/unit/api -q` and `python3 -m pytest tests/unit/ -q`
  - Result: API unit 117 passed; full unit 466 passed.
- Hosted SMTP key delivery static/lint checkpoint:
  `python3 -m pyright scout/` and `ruff check scout/ tests/ && ruff format --check scout/ tests/`
  - Result: pyright 0 errors; Ruff passed.
- Hosted Stripe Checkout RED:
  `python3 -m pytest tests/unit/core/platform/test_stripe_checkout.py tests/unit/api/test_billing_stripe_checkout.py -q`
  - Result: failed with missing `scout.core.platform.stripe_checkout` and missing `get_stripe_checkout_service`.
- Hosted Stripe Checkout GREEN:
  `python3 -m pytest tests/unit/core/platform/test_stripe_checkout.py tests/unit/api/test_billing_stripe_checkout.py -q`
  - Result: 4 passed.
- Hosted Stripe Checkout billing checkpoint:
  `python3 -m pytest tests/unit/api/test_billing_stripe_checkout.py tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  - Result: 15 passed.

# Hosted Per-Key Rate-Limit Checkpoint

Date: 2026-06-28

Built:

- `scout.core.platform.hosted_rate_limit`
- `HostedRateLimitConfig`
- `HostedRateLimitDecision`
- `HostedRateLimiter`
- `get_hosted_rate_limiter`
- FastAPI startup binding for `app.state.hosted_rate_limiter`
- `/v1/hosted/me` and `/v1/hosted/scrape` rate-limit enforcement

Behavior:

- each hosted API key has a configurable request window,
- over-limit requests return `429` with `Retry-After`,
- over-limit `/v1/hosted/scrape` calls do not call the crawler,
- over-limit `/v1/hosted/scrape` calls do not spend credits,
- unsafe URLs are still rejected before rate-limit admission or credit debit,
- the limiter is process-local and intended as a private-beta guardrail only.

Verification:

- RED:
  `python3 -m pytest tests/unit/core/platform/test_hosted_rate_limit.py tests/unit/api/test_hosted_scrape.py -q`
  failed because `scout.core.platform.hosted_rate_limit` and
  `get_hosted_rate_limiter` did not exist.
- GREEN:
  `python3 -m pytest tests/unit/core/platform/test_hosted_rate_limit.py tests/unit/api/test_hosted_scrape.py -q`
  passed: 9 tests.
- Focused checkpoint:
  `python3 -m pytest tests/unit/core/platform/test_hosted_rate_limit.py tests/unit/api/test_hosted_scrape.py tests/unit/api/test_env_example.py -q`
  passed: 10 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 125 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 482 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 202 files already
  formatted.

Still pending:

- distributed/shared hosted throttling for multi-instance production,
- global abuse/WAF policy,
- hosted products/run endpoints,
- hosted usage dashboard.

# Hosted Crawl Endpoint Checkpoint

Date: 2026-06-28

Built:

- `POST /v1/hosted/crawl`
- `HostedCrawlResponse`
- hosted crawl plan-page limit enforcement
- hosted crawl standard-credit preflight
- hosted crawl returned-page debit

Behavior:

- hosted crawl requires a Bearer `scout_live_...` key with `runs:create`,
- unsafe URLs are rejected before crawler execution,
- requested `max_pages` must be at least 1 and no greater than the hosted plan
  `max_pages_per_run`,
- the account must have enough standard credits for requested `max_pages` before
  the crawl starts,
- returned crawls charge one standard credit per returned page, capped by the
  requested `max_pages`,
- hosted crawl shares the per-key rate limiter and returns `429` without a
  second debit or crawler call when the key is over limit.

Verification:

- RED:
  `python3 -m pytest tests/unit/api/test_hosted_crawl.py -q` failed because
  `/v1/hosted/crawl` returned 404.
- GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_crawl.py -q` passed: 5 tests.
- Focused checkpoint:
  `python3 -m pytest tests/unit/api/test_hosted_crawl.py tests/unit/api/test_hosted_scrape.py -q`
  passed: 11 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 130 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 487 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 203 files already
  formatted.

Still pending:

- async hosted crawl jobs,
- persisted crawl artifact storage for hosted users,
- high-level hosted `run` endpoints,
- distributed/shared throttling for multi-instance production.

# Hosted Products Endpoint Checkpoint

Date: 2026-06-28

Built:

- `POST /v1/hosted/products`
- `HostedProductsResponse`
- hosted product target URL safety check
- hosted product plan limit enforcement
- hosted product standard-credit preflight
- hosted product returned-record debit

Behavior:

- hosted products requires a Bearer `scout_live_...` key with `runs:create`,
- requests must provide `site` or `start_url`,
- unsafe target URLs are rejected before product extraction,
- requested `max_products` must be at least 1 and no greater than the hosted
  plan `max_pages_per_run`,
- the account must have enough standard credits for requested `max_products`
  before product extraction starts,
- returned product runs charge one standard credit per returned product record,
  capped by requested `max_products`,
- hosted products shares the per-key rate limiter and returns `429` without a
  second debit or product crawler call when the key is over limit.

Verification:

- RED:
  `python3 -m pytest tests/unit/api/test_hosted_products.py -q` failed because
  `/v1/hosted/products` returned 404.
- GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_products.py -q` passed: 5 tests.
- Focused checkpoint:
  `python3 -m pytest tests/unit/api/test_hosted_products.py tests/unit/api/test_hosted_crawl.py tests/unit/api/test_hosted_scrape.py -q`
  passed: 16 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 135 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 492 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 204 files already
  formatted.

Still pending:

- async hosted product jobs,
- persisted product artifacts for hosted users,
- dashboard access to hosted run artifacts,
- distributed/shared throttling for multi-instance production.

# Hosted High-Level Run Endpoint Checkpoint

Date: 2026-06-28

Built:

- `POST /v1/hosted/run/{use_case}`
- `HostedRunResponse`
- hosted run record-limit enforcement
- hosted run standard-credit preflight
- hosted run returned-record debit
- tenant-labeled server-derived output directories

Behavior:

- hosted high-level runs require a Bearer `scout_live_...` key with
  `runs:create`,
- request `url` is checked through hosted URL safety when supplied,
- caller-provided `output_dir` is ignored for hosted safety,
- Scout derives output under server `SCOUT_WORKDIR` with a tenant-labeled run
  folder,
- requested `max_records` must be at least 1 and no greater than the hosted plan
  `max_pages_per_run`,
- the account must have enough standard credits for requested `max_records`
  before the run starts,
- returned runs charge one standard credit per returned record, capped by
  requested `max_records`,
- hosted run shares the per-key rate limiter and returns `429` without a second
  debit when the key is over limit.

Verification:

- RED:
  `python3 -m pytest tests/unit/api/test_hosted_run.py -q` failed because
  `/v1/hosted/run/company` returned 404.
- GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_run.py -q` passed: 5 tests.
- Focused checkpoint:
  `python3 -m pytest tests/unit/api/test_hosted_run.py tests/unit/api/test_hosted_products.py tests/unit/api/test_hosted_crawl.py tests/unit/api/test_hosted_scrape.py -q`
  passed: 21 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 140 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 497 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 205 files already
  formatted.

Still pending:

- async hosted run jobs,
- hosted run artifact dashboard UI,
- distributed/shared throttling for multi-instance production.

# Hosted Run Retrieval Checkpoint

Date: 2026-06-28

Built:

- `GET /v1/hosted/runs/{run_id}`
- `GET /v1/hosted/runs/{run_id}/records`
- `GET /v1/hosted/runs/{run_id}/artifacts`
- hosted owner-key retrieval guard

Behavior:

- hosted retrieval requires a Bearer `scout_live_...` key with `runs:create`,
- owner keys can retrieve run summary metadata,
- owner keys can retrieve `records.json` content,
- owner keys can retrieve artifact path metadata,
- another hosted tenant receives `404` for a run it does not own,
- raw hosted API keys are not returned in retrieval responses,
- private-beta ownership is enforced through tenant-labeled run output
  directories until run persistence has explicit tenant columns.

Verification:

- RED:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py -q` failed
  because `/v1/hosted/runs/{run_id}` returned 404.
- GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py -q` passed:
  3 tests.
- Focused checkpoint:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py tests/unit/api/test_hosted_run.py -q`
  passed: 8 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 143 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 500 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 206 files already
  formatted.

Still pending:

- hosted artifact dashboard UI,
- object storage and signed artifact URLs for multi-instance hosting.

## Hosted Run Ownership Persistence Checkpoint

Date: 2026-06-28

Built:

- `RunRow.tenant_id`
- `RunRow.key_id`
- SQLite `runs.tenant_id`
- SQLite `runs.key_id`
- SQLite migration helper for missing run columns on `init_db`
- `remember_run(..., tenant_id, key_id)`
- hosted run retrieval guard based on persisted tenant ownership

Behavior:

- hosted runs persist non-secret tenant and key IDs with the run,
- hosted retrieval uses the persisted `tenant_id`, not output-directory path
  parsing,
- local/non-hosted runs keep empty tenant/key IDs,
- existing SQLite databases add missing ownership columns during `init_db`,
- raw hosted API keys are not returned by retrieval endpoints.

TDD:

- RED:
  `python3 -m pytest tests/unit/api/test_db.py tests/unit/api/test_hosted_run_retrieval.py -q`
  failed because the `runs` table, `RunRow`, and hosted summary response lacked
  persisted ownership fields.
- GREEN:
  `python3 -m pytest tests/unit/api/test_db.py tests/unit/api/test_hosted_run_retrieval.py -q`
  passed: 14 tests.

Verification:

- Focused checkpoint:
  `python3 -m pytest tests/unit/api/test_db.py tests/unit/api/test_hosted_run_retrieval.py tests/unit/api/test_hosted_run.py -q`
  passed: 19 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 144 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 501 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 206 files already
  formatted.

Still pending:

- hosted artifact dashboard UI,
- object storage and signed artifact URLs for multi-instance hosting,
- production user/account model beyond hosted API keys.

## Hosted Artifact Download Checkpoint

Date: 2026-06-28

Built:

- `GET /v1/hosted/runs/{run_id}/artifacts/{artifact_name}/download`
- `download_urls` in `GET /v1/hosted/runs/{run_id}/artifacts`
- known-artifact allowlist for hosted downloads
- run-output-directory confinement before serving artifact files

Behavior:

- hosted artifact downloads require the same Bearer key ownership check as run
  summary, records, and artifact metadata,
- another tenant receives `404` for an owned run's artifact download route,
- unknown artifact names return `404`,
- artifact files are only served when the resolved file lives under the
  persisted run output directory,
- the private-beta route is local filesystem backed; production object storage
  and signed URLs remain future work.

TDD:

- RED:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py -q` failed
  because `/artifacts` had no `download_urls` and artifact download routes
  returned the framework `404`.
- GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py -q` passed:
  5 tests.

Still pending:

- hosted artifact dashboard UI,
- object storage and signed artifact URLs for multi-instance hosting,
- async hosted jobs for long-running artifact-producing workflows.

## Hosted Run List Checkpoint

Date: 2026-06-28

Built:

- `GET /v1/hosted/runs`
- tenant-scoped run listing in `scout.api.run_store`
- SQLite `RunDB.list_runs(..., tenant_id=...)`
- dashboard-safe hosted run list items with summary, records, and artifact URLs

Behavior:

- hosted users can list runs created by their own Bearer key tenant,
- runs from other tenants are omitted,
- list responses do not expose server `output_dir` paths,
- list responses do not echo raw hosted API keys,
- persisted SQLite run ownership supports listing after restart.

TDD:

- RED:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py -q` failed
  because `/v1/hosted/runs` returned `404`.
- GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py tests/unit/api/test_db.py -q`
  passed: 18 tests.

Verification:

- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 148 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 508 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 206 files already
  formatted.

Still pending:

- hosted dashboard UI,
- object storage and signed artifact URLs for multi-instance hosting,
- async hosted jobs for long-running workflows.
