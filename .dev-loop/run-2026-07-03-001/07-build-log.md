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

## Verified

```bash
python3 -m pytest tests/unit/ -q
```

Result: 678 passed, 8 warnings.

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

## Still Pending

- No email/password login, user dashboard, or password reset.
- No public paid self-serve Stripe purchase flow enabled in production.
- No invoice ledger, revenue dashboard, COGS dashboard, or packaged per-customer analytics.
- Pay-as-you-go pricing and unit economics remain a product decision, not finalized code.
- The beta signup path currently emails one hosted key; account management beyond that is still admin/manual.
