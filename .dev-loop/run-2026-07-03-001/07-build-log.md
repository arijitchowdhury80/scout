# Build Log

Date: 2026-07-03
Feature: Public hosted beta production hardening for 250 testers

## Implemented This Slice

- Added email-delivered self-service hosted beta key signup.
  - `POST /v1/hosted/beta-key` now records `name` and `email`.
  - Raw API keys are emailed and no longer returned in the browser/API response.
  - Signup requires a configured delivery service and rolls back the tenant if delivery fails.
- Added hosted tenant `name` persistence.
  - Stored in SQLite `hosted_tenants.name`.
  - Exposed through CLI provisioning and self-service signup responses.
- Added credit usage ledger.
  - Successful hosted debits are persisted in `hosted_credit_ledger`.
  - `GET /v1/hosted/usage` returns recent per-tenant usage for the authenticated bearer key.
  - Failed capacity/rate/credit checks do not write usage ledger rows.
- Added process-local admission controls for hosted/playground expensive work.
  - Hosted scrape rejects at capacity before credit debit or crawl.
  - Playground capacity tests use the same shared dependency shape.
- Added Mac-side hosted admin helper.
  - `scripts/scout-hosted-admin generate-secret`
  - `scripts/scout-hosted-admin provision-key`
  - `scripts/scout-hosted-admin list-accounts`
- Updated VPS provisioning helper.
  - Accepts `--name`.
  - Carries name into `scout hosted-provision`.
- Updated hosted operations documentation.
  - Clarifies no login system exists yet.
  - Documents self-service email signup, admin key provisioning, usage ledger, and current pricing/billing gaps.
- Added hosted credit packaging and unit-economics model.
  - `scout.core.platform.pricing` defines the beta trial, standard credit packages, browser-credit package, credit meanings, and margin calculator.
  - First pay-as-you-go candidate: `$10 for 1,000 standard credits`.
  - Beta trial candidate: `30 days`, `100 standard credits`, `$0 charge`, payment method required later.
  - Default economics for the $10 package: `$2.59` loaded cost, `$7.41` gross profit, `74.1%` gross margin, `17 packs/month` break-even against a `$120` fixed monthly cost assumption.
- Updated public pricing surface and product docs.
  - `website/pricing.html` now explains the beta trial, $10 package, credit meanings, and margin math.
  - Product docs no longer claim the stale 2,000 standard / 100 browser beta pass; active beta pass is aligned to 100 standard / 0 browser credits.
- Added package-aware Stripe Checkout and webhook provisioning.
  - `beta_trial` creates a Stripe Checkout `mode=setup` session, collects a payment method, charges `$0`, and provisions 100 standard credits after signed webhook completion.
  - `standard_1000` creates a Stripe Checkout `mode=payment` session using `STRIPE_STANDARD_1000_PRICE_ID` and provisions 1,000 standard credits after signed webhook completion.
  - Payment records now persist `package_id` for auditability and older SQLite payment DBs receive a safe `package_id` column migration.
  - `website/beta.html` posts `package_id: beta_trial` explicitly.
- Added bounded async hosted job queue for saturated expensive endpoints.
  - `/v1/hosted/scrape`, `/crawl`, `/products`, and `/run/{use_case}` now return `202 Accepted` with `job_id`/`job_url` when synchronous worker capacity is full and queue space is available.
  - `/v1/hosted/jobs/{job_id}` returns tenant-scoped queued/running/complete/failed state and completed result payloads.
  - Credits are charged only when queued work executes, not when it is accepted.
  - Queue controls are `HOSTED_JOB_QUEUE_MAX_SIZE`, `HOSTED_JOB_QUEUE_WORKERS`, and `CAPACITY_RETRY_AFTER_SECONDS`.

## Verified

```bash
python3 -m pytest tests/unit/ -q
```

Result: 678 passed, 8 warnings.

```bash
python3 -m pytest tests/unit/core/platform/test_pricing.py tests/unit/test_hosted_pricing_docs.py tests/unit/website/test_launch_website.py tests/unit/core/platform/test_hosted_policy.py tests/unit/test_launch_governance_docs.py::test_hosted_api_quickstart_verification_records_new_key_smoke tests/unit/test_launch_governance_docs.py::test_hosted_operating_contract_documents_private_beta_boundary -q
```

Result: 42 passed, 2 warnings.

```bash
python3 -m pytest tests/unit/core/platform/test_stripe_checkout.py tests/unit/api/test_billing_stripe_checkout.py tests/unit/core/platform/test_payment_provisioning.py tests/unit/api/test_billing_stripe_webhook.py tests/unit/core/platform/test_pricing.py tests/unit/test_hosted_pricing_docs.py tests/unit/website/test_launch_website.py tests/unit/test_launch_governance_docs.py::test_stripe_test_mode_readiness_keeps_live_gate_open_until_real_smoke -q
```

Result: 56 passed, 2 warnings.

```bash
python3 -m pytest tests/unit/ -q
```

Result: 696 passed, 8 warnings.

```bash
python3 -m pytest tests/unit/api/test_hosted_jobs.py tests/unit/api/test_hosted_scrape.py tests/unit/api/test_hosted_crawl.py tests/unit/api/test_hosted_products.py tests/unit/api/test_hosted_run.py tests/unit/api/test_hosted_run_retrieval.py -q
```

Result: 41 passed, 2 warnings.

```bash
python3 -m pyright scout/
ruff check scout/ tests/ scripts/*.py
ruff format --check scout/ tests/ scripts/*.py
bash -n scripts/scout-hosted-admin scripts/scout-vps-list-hosted-accounts scripts/scout-vps-provision-hosted-key scripts/scout-vps-list-hosted-purchases scripts/scout-hosted-load-test
```

Result: pyright 0 errors; Ruff passed; format passed; shell syntax passed.

## Production Load Finding

- A 250-user full hosted workload on the current VPS overloaded the service before this admission-control slice.
- VPS evidence: 2 vCPU, 7.8 GiB RAM, no swap; full 250 concurrent heavy jobs pushed load over 100 and made `/health` time out.
- The admission controls added here are an overload guardrail so production returns explicit retryable 429 responses instead of spawning unbounded expensive work.
- This does not prove the current VPS can serve 250 simultaneous heavy users without queueing/retries. That still requires either larger capacity, horizontal workers, a real job queue, or a reduced beta concurrency promise.

## Production Verification On VPS

Commit deployed: `15948b5`.

Runtime guardrails:

```bash
HOSTED_MAX_ACTIVE_REQUESTS=2
PLAYGROUND_MAX_ACTIVE_REQUESTS=1
CAPACITY_RETRY_AFTER_SECONDS=10
HOSTED_LLM_MODE=disabled
```

Hosted-only 250-user probe:

- Command target: `http://127.0.0.1:8421`
- Users/concurrency: 250/250
- Requests: 4,000 across `/v1/hosted/me`, hosted scrape/crawl/products, hosted intelligence runs, and hosted run listing.
- Result file: `/opt/prism/scout-load-tests/results/hosted-250-cooldown-1783046288.json`
- Duration: 27.72s
- Throughput: 144.32 req/s
- P95 latency: 2,789ms
- Error rate: 87.45%, mostly intentional 429 overload responses
- Post-test `/health`: 200
- Post-test container: CPU 0.78%, memory 136MiB, PIDs 35

Hosted plus playground 250-user probe:

- Command target: `http://127.0.0.1:8421`
- Users/concurrency: 250/250
- Requests: 8,000 across hosted endpoints plus all public playground workflows.
- Result file: `/opt/prism/scout-load-tests/results/hosted-playground-250-cooldown-1783046334.json`
- Duration: 55.83s
- Throughput: 143.29 req/s
- P95 latency: 5,900ms
- Error rate: 93.74%, mostly intentional 429 overload responses
- Post-test `/health`: 200
- Post-test container: CPU 0.18%, memory 147.9MiB, PIDs 38

Interpretation: production now survives a 250-concurrent-user stampede by rejecting excess expensive work quickly. It is not verified to successfully execute all workflows for 250 simultaneous users on the current 2-vCPU VPS.

## Production Verification After Hosted Queue Deploy

Commit deployed: `145586e`.

Runtime guardrails:

```bash
SCOUT_PUBLIC_HOSTED_ONLY=true
HOSTED_LLM_MODE=disabled
LLM_API_KEY=
HOSTED_RATE_LIMIT_MAX_REQUESTS=40
HOSTED_RATE_LIMIT_WINDOW_SECONDS=60
HOSTED_MAX_ACTIVE_REQUESTS=2
HOSTED_JOB_QUEUE_MAX_SIZE=250
HOSTED_JOB_QUEUE_WORKERS=2
PLAYGROUND_MAX_ACTIVE_REQUESTS=1
CAPACITY_RETRY_AFTER_SECONDS=10
```

Queue smoke:

- Command target: `https://scout.chowmes.com/v1/hosted/scrape`
- Requests/concurrency: 10/10 using one temporary hosted key.
- Result: 2 synchronous `200` responses and 8 queued `202 Accepted` responses.
- Queued responses returned `credits_charged: 0`, `job_id`, and `job_url`.

Hosted-only 250-user / 250-key production probe:

- Command target: `https://scout.chowmes.com`
- Users/concurrency: 250/250
- Requests: 4,000 across `/v1/hosted/me`, hosted scrape/crawl/products, hosted intelligence runs, and hosted run listing.
- Result file: `/tmp/scout-load-results/hosted-250-1783048267.json`
- Duration: 237.51s
- Throughput: 16.84 req/s
- P95 latency: 41,388ms
- Error rate: 81.20%
- Result: failed the `p95 <= 15000ms` and `error_rate <= 2%` gates.
- Sample failures included `429 Too Many Requests` and local client `TimeoutError(60, 'Operation timed out')`.
- Post-test `/health`: 200
- During drain container: CPU 196.21%, memory 951.4MiB, PIDs 594.

Cleanup:

- Revoked 251 temporary load-test keys, including the smoke key.
- Restarted the Scout container to flush the in-process queue.
- Post-cleanup container: healthy, CPU 0.18%, memory 105.2MiB, PIDs 7.
- Revoked smoke key returned `403 {"detail":"API key is not active."}`.

Interpretation: the queue slice is working, but the current single 2-vCPU VPS still cannot honestly support 250 users simultaneously hitting every heavy endpoint. The current production posture protects the box and limits cost; it does not yet meet the 250-user all-endpoint success bar.

## Still Pending

- No email/password login, user dashboard, or password reset.
- No public paid self-serve Stripe purchase flow enabled in production.
- No invoice dashboard, revenue dashboard, COGS dashboard, or packaged per-customer analytics.
- Real Stripe test-mode smoke is still required with live Stripe test credentials, Checkout completion, Stripe CLI/webhook delivery, emailed key delivery, and `/v1/hosted/me` verification.
- Stripe payment records persist checkout/package/idempotency, usage ledger persists debits, and `scripts/scout-hosted-admin list-purchases` now gives an operator purchase ledger view.
- Unit-economics assumptions still need live cost validation from hosting, browser workers, LLM usage, support, firewall/security, and payment operations.
- The beta signup path currently emails one hosted key; account management beyond that is still admin/manual.
- The hosted queue is in-process and single-node. It improves the current VPS beta behavior, but a larger public launch still needs a durable queue, shared rate limiter, worker autoscaling, and external artifact storage.

## Purchase Ledger Admin Slice

Implemented:

- `SQLiteHostedPaymentStore.list_checkouts(limit=...)` returns recent checkout/package records without secret material.
- `scripts/scout-vps-list-hosted-purchases` lists Stripe checkout/package records from `/data/hosted_accounts.sqlite`.
- `scripts/scout-hosted-admin list-purchases` wraps the VPS purchase ledger command.
- README and hosted admin docs now show `generate-api-key`, `list-accounts`, and `list-purchases`.
- Removed the obsolete beta invite-password framing from admin helper/docs; hosted signup is name plus email plus one-time key delivery.
- `/v1/hosted/purchases` now returns checkout/package purchase records for the authenticated Bearer key's tenant only.

Verification:

```bash
python3 -m pytest tests/unit/core/platform/test_payment_provisioning.py::test_sqlite_payment_store_lists_checkout_purchase_records tests/unit/scripts/test_vps_admin_scripts.py -q
```

Result: 6 passed, 2 warnings.

```bash
python3 -m pytest tests/unit/api/test_hosted_purchases.py tests/unit/scripts/test_vps_admin_scripts.py tests/unit/test_hosted_pricing_docs.py -q
```

Result: 10 passed, 2 warnings.

```bash
rg -n "BETA_INVITE|HOSTED_BETA_INVITE_PASSWORD|beta invite password|invite-password|invite password|password gate" scripts scout docs website README.md .env.example
```

Result: no matches.

## Public Package Discovery Slice

Implemented:

- `/v1/billing/packages` returns public hosted package definitions, credit-cost meanings, and unit-economics outputs with no Stripe secrets.
- `website/pricing.html` now exposes `data-packages-endpoint="/v1/billing/packages"` and stable containers for package cards, credit meanings, and unit economics.
- `website/assets/pricing.js` hydrates the pricing page from Scout's package model while preserving static fallback copy.
- Auth/static allowlists now expose `/v1/billing/packages` and `/assets/pricing.js` publicly.

Verification:

```bash
python3 -m pytest tests/unit/api/test_billing_stripe_checkout.py::test_billing_packages_returns_credit_meanings_and_unit_economics_without_secrets tests/unit/website/test_launch_website.py::test_pricing_page_explains_credit_packages_and_unit_economics tests/unit/website/test_launch_website.py::test_api_serves_launch_website_static_assets_without_auth -q
```

Result: 3 passed, 2 warnings.

```bash
python3 -m pytest tests/unit/core/platform/test_key_delivery.py tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_hosted_purchases.py tests/unit/api/test_billing_stripe_checkout.py tests/unit/website/test_launch_website.py tests/unit/test_hosted_pricing_docs.py -q
```

Result: 47 passed, 2 warnings.

```bash
python3 -m pytest tests/unit/ -q
```

Result: 704 passed, 8 warnings.

```bash
python3 -m pyright scout/
ruff check scout/ tests/ scripts/*.py
ruff format --check scout/ tests/ scripts/*.py
```

Result: pyright 0 errors; Ruff passed; format check passed.

## Hosted Account Monitoring Summary Slice

Implemented:

- `/v1/hosted/me` now returns compact monitoring summaries in addition to
  tenant, key, plan, balance, and limits.
- `usage_summary` includes usage event count, standard credits used, browser
  credits used, and the deeper `/v1/hosted/usage` URL.
- `purchase_summary` includes purchase count, total amount paid, currency, last
  package id, and the deeper `/v1/hosted/purchases` URL.
- `links` gives callers stable docs/pricing/usage/purchase locations without
  exposing raw API keys.
- Hosted operations docs now describe `/v1/hosted/me` as the account snapshot
  endpoint for self-service and monitoring.

Verification:

```bash
python3 -m pytest tests/unit/api/test_hosted_purchases.py::test_hosted_me_returns_usage_and_purchase_monitoring_summary -q
```

Result: 1 passed, 2 warnings.

## Final Production Smoke And Load On Current Branch Tip

Runtime commit deployed for this smoke: `e0c956f`.

Production public smoke:

- `GET https://scout.chowmes.com/health` returned `200`.
- `GET https://scout.chowmes.com/pricing` returned `200`.
- `GET https://scout.chowmes.com/quickstart` returned `200`.
- `GET https://scout.chowmes.com/assets/pricing.js` returned `200`.
- `GET https://scout.chowmes.com/assets/hosted-keygen.js` returned `403`, as
  expected after removing the old direct keygen public path.
- `GET https://scout.chowmes.com/v1/billing/packages` returned `200`.
- VPS env still had hosted LLM disabled:
  `HOSTED_LLM_MODE=disabled`, `LLM_API_KEY=` empty, and
  `HOSTED_ASYNC_FIRST=true`.

Fresh public HTTPS 250-user hosted acceptance load on `e0c956f`:

- Command target: `https://scout.chowmes.com`
- Users/concurrency: 250/250
- Requests: 4,000 across `/v1/hosted/me`, hosted scrape/crawl/products,
  hosted intelligence runs, and hosted run listing.
- Result file: `/tmp/scout-load-e0c956f-result.json`
- Duration: 80.99s
- Throughput: 49.39 req/s
- P95 latency: 4,929ms
- Error rate: 0.00%
- Result: passed `p95 <= 15000ms` and `error_rate <= 2%`.
- Post-test container: CPU 0.20%, memory 150.7MiB, PIDs 23.

Final production cleanup:

- Revoked the 250 temporary `load250_e0c956f_%@chowmes.internal` load-test
  keys; all load-test keys now show `revoked`.
- Restarted the Scout container to flush the in-process acceptance queue.
- Verified public health after cleanup:
  `{"status":"ok","crawl4ai_version":"0.9.0","scout_version":"0.1.0"}`.
- Post-cleanup container: CPU 0.16%, memory 104.9MiB, PIDs 7.

Boundary: this is a successful hosted async-acceptance load test. It is still
not proof that the 2-vCPU VPS can execute 250 simultaneous long-running browser
or crawler jobs to completion without separate worker capacity.

## Hosted Account Snapshot Monitoring Slice

Implemented:

- `/v1/hosted/me` now returns compact `usage_summary`, `purchase_summary`, and
  stable account links alongside plan limits and balances.
- The payment provisioning dependency now has a safe no-lifespan fallback for
  tests and local direct app construction, while production still uses the
  app-state service created during FastAPI lifespan startup.
- Hosted operations docs now identify `/v1/hosted/me` as the account snapshot
  surface and `/v1/hosted/usage` plus `/v1/hosted/purchases` as deeper ledgers.

Verification:

```bash
python3 -m pytest tests/unit/api/test_hosted_purchases.py tests/unit/api/test_hosted_scrape.py tests/unit/api/test_hosted_crawl.py tests/unit/api/test_hosted_products.py tests/unit/api/test_hosted_run.py -q
```

Result: 33 passed, 2 warnings.

```bash
python3 -m pyright scout/
ruff check scout/ tests/ scripts/*.py scripts/scout-hosted-load-test
ruff format --check scout/ tests/ scripts/*.py scripts/scout-hosted-load-test
```

Result: pyright 0 errors; Ruff passed; format check passed.

```bash
python3 -m pytest tests/unit/ -q
```

Result: 705 passed, 8 warnings.

Production deployment verification for this slice:

- Commit deployed: `e7d8da8`.
- Public smoke returned `200` for `/health`, `/pricing`, `/quickstart`,
  `/assets/pricing.js`, and `/v1/billing/packages`.
- Old `/assets/hosted-keygen.js` returned `403`, as expected.
- VPS env still had `HOSTED_LLM_MODE=disabled`, empty `LLM_API_KEY`,
  `HOSTED_ASYNC_FIRST=true`, and `HOSTED_JOB_QUEUE_WORKERS=0`.
- Fresh public HTTPS 250-user hosted acceptance load:
  `/tmp/scout-load-e7d8da8-result.json`.
- Users/concurrency: 250/250.
- Requests: 4,000.
- Duration: 84.36s.
- Throughput: 47.42 req/s.
- P95 latency: 5,601ms.
- Error rate: 0.00%.
- Result: passed `p95 <= 15000ms` and `error_rate <= 2%`.
- Post-test container: CPU 0.20%, memory 149.9MiB, PIDs 26.
- Final cleanup revoked the 250 `load250_e7d8da8_%@chowmes.internal` keys,
  restarted Scout to flush the in-process queue, verified public health `200`,
  and left the container idle at CPU 0.19%, memory 104.9MiB, PIDs 7.

Boundary: this remains hosted async-acceptance capacity evidence, not proof of
250 simultaneous completed crawler/browser executions on the 2-vCPU VPS.

## Hosted Admin Wrapper And Checkout Name Slice

Implemented:

- Added `scripts/scout-generate-api-key` as the short operator wrapper for the
  common hosted key-provisioning action.
- Removed the generic `generate-secret` command from `scripts/scout-hosted-admin`
  and removed admin-token/password generator copy from docs.
- Pricing and beta checkout forms now collect `name` or app name.
- `/v1/billing/stripe/checkout-session` carries `name` into Stripe metadata.
- Stripe webhook provisioning carries customer name into the hosted tenant and
  hosted API-key delivery email request.

Verification:

```bash
python3 -m pytest tests/unit/scripts/test_vps_admin_scripts.py tests/unit/test_hosted_pricing_docs.py -q
```

Result: 9 passed.

```bash
python3 -m pytest tests/unit/api/test_billing_stripe_checkout.py tests/unit/api/test_billing_stripe_webhook.py tests/unit/core/platform/test_payment_provisioning.py tests/unit/core/platform/test_stripe_checkout.py tests/unit/website/test_launch_website.py -q
```

Result: 50 passed, 2 warnings.

```bash
python3 -m pyright scout/
ruff check scout/ tests/ scripts/*.py scripts/scout-hosted-load-test
ruff format --check scout/ tests/ scripts/*.py scripts/scout-hosted-load-test
bash -n scripts/scout-hosted-admin scripts/scout-generate-api-key scripts/scout-vps-list-hosted-accounts scripts/scout-vps-provision-hosted-key scripts/scout-vps-list-hosted-purchases scripts/scout-hosted-load-test
python3 -m pytest tests/unit/ -q
```

Result: pyright 0 errors; Ruff passed; format check passed; shell syntax
passed; unit suite 705 passed, 8 warnings.

Production deployment verification for this slice:

- Commit deployed: `5a35b9b`.
- Public smoke returned `200` for `/health`, `/pricing`, `/beta`,
  `/quickstart`, `/assets/pricing.js`, and `/v1/billing/packages`.
- Old `/assets/hosted-keygen.js` returned `403`, as expected.
- `POST /v1/billing/stripe/checkout-session` with name, email, and
  `package_id=beta_trial` returned `503 {"detail":"Stripe Checkout is not configured."}`,
  as expected for the current production env.
- Fresh public HTTPS 250-user hosted acceptance load:
  `/tmp/scout-load-5a35b9b-result.json`.
- Users/concurrency: 250/250.
- Requests: 4,000.
- Duration: 89.39s.
- Throughput: 44.75 req/s.
- P95 latency: 5,643ms.
- Error rate: 0.03%.
- Result: passed `p95 <= 15000ms` and `error_rate <= 2%`.
- Caveat: one request returned `502 Bad Gateway` for
  `POST /v1/hosted/run/docs`; this is not a zero-hiccup result.
- Final cleanup revoked the 250 `load250_5a35b9b_%@chowmes.internal` keys,
  restarted Scout to flush the in-process queue, verified public health `200`,
  and left the container idle at CPU 0.18%, memory 105.1MiB, PIDs 7.

## Payment-Method-First Beta Access Slice

Implemented:

- `website/quickstart.html` no longer exposes the direct hosted beta key form.
- Docs now point testers to `/beta#hosted-checkout`, where the `$0` Stripe
  beta trial flow collects payment method details before key delivery.
- Removed the unused `website/assets/hosted-keygen.js` script and removed it
  from the launch-site public asset allowlist and auth public-path allowlist.
- The quickstart API reference now lists
  `POST /v1/billing/stripe/checkout-session` instead of
  `POST /v1/hosted/beta-key` as the tester-facing access path.
- Hosted operations and public-hosted launch docs now mark direct
  `/v1/hosted/beta-key` as a disabled legacy/operator exception path, not the
  public beta path.

Verification:

```bash
python3 -m pytest tests/unit/website/test_launch_website.py::test_launch_website_has_beta_onboarding_pages tests/unit/website/test_launch_website.py::test_docs_beta_access_is_payment_method_first tests/unit/website/test_launch_website.py::test_api_serves_launch_website_static_assets_without_auth tests/unit/api/test_auth.py::test_public_hosted_only_allows_product_docs_but_blocks_api_docs -q
```

Result: 4 passed, 2 warnings.

```bash
python3 -m pytest tests/unit/core/platform/test_key_delivery.py tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_hosted_purchases.py tests/unit/api/test_billing_stripe_checkout.py tests/unit/api/test_auth.py tests/unit/website/test_launch_website.py tests/unit/test_hosted_pricing_docs.py -q
```

Result: 58 passed, 2 warnings.

```bash
python3 -m pytest tests/unit/ -q
```

Result: 704 passed, 8 warnings.

```bash
python3 -m pyright scout/
ruff check scout/ tests/ scripts/*.py
ruff format --check scout/ tests/ scripts/*.py
```

Result: pyright 0 errors; Ruff passed; format check passed.

## Pricing Checkout UX Slice

Implemented:

- `website/pricing.html` now includes a hosted credit checkout form on the
  pricing page instead of leaving paid packages as read-only copy.
- The form lets a user enter the API-key delivery email and choose
  `standard_1000`, `standard_3000`, or `standard_15000`.
- `website/assets/pricing.js` posts `{email, package_id}` to
  `/v1/billing/stripe/checkout-session` and redirects only when the API returns
  a Stripe `checkout_url`.
- Hosted operations docs now state the precise boundary: checkout initiation
  exists, but real Stripe test-mode completion, signed webhook delivery, SMTP
  key email, and post-purchase hosted account verification are still pending.

Verification:

```bash
python3 -m pytest tests/unit/website/test_launch_website.py::test_pricing_page_explains_credit_packages_and_unit_economics -q
```

Result: 1 passed, 2 warnings.

## Hosted Async Acceptance Load Evidence

Production commit deployed: `458603d`.

Runtime guardrails verified on the VPS:

```bash
SCOUT_PUBLIC_HOSTED_ONLY=true
HOSTED_LLM_MODE=disabled
LLM_API_KEY=
HOSTED_RATE_LIMIT_MAX_REQUESTS=40
HOSTED_RATE_LIMIT_WINDOW_SECONDS=60
HOSTED_JOB_QUEUE_MAX_SIZE=5000
HOSTED_JOB_QUEUE_WORKERS=0
HOSTED_ASYNC_FIRST=true
```

Important boundary:

- This test proves the hosted API can accept a 250-user burst across the hosted
  HTTP surface when expensive work is accepted asynchronously.
- It does not prove that the current 2-vCPU VPS can execute 250 concurrent
  scrape/crawl/product jobs to completion at the same time.
- With `HOSTED_JOB_QUEUE_WORKERS=0`, queued work is intentionally not drained
  in-process during the load test. A production-ready execution path still needs
  a durable queue and separate worker capacity before claiming 250 simultaneous
  long-running jobs are supported.

Failed/noisy intermediate probes:

- Public async-first probe with in-process workers enabled:
  `/tmp/scout-load-results/hosted-250-async-1783049074.json`.
  Result: 4,000 requests, 250 users, p95 43,453ms, error rate 21.45%.
  Root cause: worker execution in the API container saturated the 2-vCPU box.
- Public acceptance-only probe before queue flush:
  `/tmp/scout-load-results/hosted-250-accept-only-1783049379.json`.
  Result: 4,000 requests, 250 users, p95 42,080ms, error rate 22.95%.
  Root cause: stale accepted jobs remained in the in-memory queue because
  workers were disabled.
- VPS-local acceptance-only probe before queue flush:
  `/tmp/scout-load-vpslocal-result.json`.
  Result: 4,000 requests, 250 users, p95 6,090ms, error rate 29.68%.
  Root cause: same pre-filled in-memory queue, returning retryable 429s.

Clean VPS-local 250-user hosted probe after revoking temp keys and restarting
Scout:

- Command target: `http://127.0.0.1:8421`
- Users/concurrency: 250/250
- Requests: 4,000 across `/v1/hosted/me`, hosted scrape/crawl/products,
  hosted intelligence runs, and hosted run listing.
- Result file: `/tmp/scout-load-cleanlocal-result.json`
- Duration: 71.81s
- Throughput: 55.70 req/s
- P95 latency: 5,805ms
- Error rate: 0.00%
- Result: passed `p95 <= 15000ms` and `error_rate <= 2%`.
- Post-test container: CPU 0.18%, memory 152.8MiB, PIDs 45.

Clean public HTTPS 250-user hosted probe after another restart:

- Command target: `https://scout.chowmes.com`
- Users/concurrency: 250/250
- Requests: 4,000 across `/v1/hosted/me`, hosted scrape/crawl/products,
  hosted intelligence runs, and hosted run listing.
- Result file: `/tmp/scout-load-cleanpublic-result.json`
- Duration: 82.32s
- Throughput: 48.59 req/s
- P95 latency: 5,677ms
- Error rate: 0.00%
- Result: passed `p95 <= 15000ms` and `error_rate <= 2%`.
- Post-test container: CPU 0.19%, memory 148.8MiB, PIDs 27.

Cleanup:

- Revoked all `load250_%@chowmes.internal` hosted load-test keys.
- Restarted the Scout container to flush the in-process acceptance queue.
- Verified public health after cleanup:
  `{"status":"ok","crawl4ai_version":"0.9.0","scout_version":"0.1.0"}`.
- Post-cleanup container: CPU 0.17%, memory 104.8MiB, PIDs 7.

```bash
python3 -m pytest tests/unit/core/platform/test_key_delivery.py tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_hosted_purchases.py tests/unit/api/test_billing_stripe_checkout.py tests/unit/website/test_launch_website.py tests/unit/test_hosted_pricing_docs.py -q
```

Result: 46 passed, 2 warnings.

```bash
python3 -m pytest tests/unit/ -q
```

Result: 703 passed, 8 warnings.

```bash
python3 -m pyright scout/
ruff check scout/ tests/ scripts/*.py
ruff format --check scout/ tests/ scripts/*.py
```

Result: pyright 0 errors; Ruff passed; format check passed.

## Pricing Checkout Return Slice

Implemented:

- `website/pricing.html` now includes a hidden Stripe checkout return status
  region with explicit `checkout=success` and `checkout=cancelled` markers.
- `website/assets/pricing.js` now displays paid-checkout success/cancel copy on
  the pricing page, matching the beta page behavior.
- `.env.example` now points hosted Stripe redirects at
  `https://scout.chowmes.com/pricing?checkout=success` and
  `https://scout.chowmes.com/pricing?checkout=cancelled` instead of localhost.
- `docs/product/stripe-test-mode-readiness-2026-06-29.md` now uses the same
  hosted pricing redirect URLs for the real Stripe test-mode smoke.

Verification:

```bash
python3 -m pytest tests/unit/website/test_launch_website.py::test_launch_website_handles_stripe_checkout_return_states_without_secrets tests/unit/website/test_launch_website.py::test_pricing_page_explains_credit_packages_and_unit_economics tests/unit/test_hosted_pricing_docs.py::test_stripe_redirect_examples_use_hosted_pricing_page_not_localhost -q
```

Result: 3 passed, 2 warnings.

```bash
python3 -m pytest tests/unit/api/test_billing_stripe_checkout.py tests/unit/website/test_launch_website.py tests/unit/test_hosted_pricing_docs.py -q
```

Result: 34 passed, 2 warnings.

```bash
python3 -m pytest tests/unit/ -q
```

Result: 703 passed, 8 warnings.

```bash
python3 -m pyright scout/
ruff check scout/ tests/ scripts/*.py
ruff format --check scout/ tests/ scripts/*.py
```

Result: pyright 0 errors; Ruff passed; format check passed.

## Hosted Key Email Onboarding Slice

Implemented:

- The hosted API-key email now tells beta users exactly what they received:
  100 standard credits for 30 days.
- The email explains credit meaning: one scrape, one returned crawl page, or
  one product/intelligence record equals one standard credit.
- The email links to hosted docs and pricing, and asks users to reply with their
  use case, target site, and failing run ID for support.
- The delivery test now parses the generated email body with the modern email
  policy so it verifies decoded user-visible copy instead of raw MIME wrapping.

Verification:

```bash
python3 -m pytest tests/unit/core/platform/test_key_delivery.py::test_smtp_delivery_service_sends_one_time_key_email -q
```

Result: 1 passed, 2 warnings.
