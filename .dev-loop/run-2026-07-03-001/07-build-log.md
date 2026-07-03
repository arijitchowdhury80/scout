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
python3 -m pyright scout/
ruff check scout/ tests/ scripts/scout-hosted-load-test
ruff format --check scout/ tests/
bash -n scripts/scout-hosted-admin
bash -n scripts/scout-vps-list-hosted-accounts
bash -n scripts/scout-vps-provision-hosted-key
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

## Still Pending

- No email/password login, user dashboard, or password reset.
- No public paid self-serve Stripe purchase flow enabled in production.
- No invoice ledger, revenue dashboard, COGS dashboard, or packaged per-customer analytics.
- Stripe checkout still needs to map to the new package model; old deterministic checkout scaffolding is not yet the production pay-as-you-go flow.
- Unit-economics assumptions still need live cost validation from hosting, browser workers, LLM usage, support, firewall/security, and payment operations.
- The beta signup path currently emails one hosted key; account management beyond that is still admin/manual.
