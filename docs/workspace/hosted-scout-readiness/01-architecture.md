# Hosted Scout Production Architecture

Date: 2026-06-28

## Product Decision

Scout should launch local-first. Hosted Scout should be optional and metered.

Local Scout:

- free beta/default path,
- user owns compute, browser session, keys, and artifacts,
- best for private acquisition and browser/user-session capture.

Hosted Scout:

- convenience API,
- API keys provisioned after signup/payment,
- strict quotas,
- async run model,
- short artifact retention,
- no unlimited one-time access.

## Hosted Architecture

```text
Website
  -> Auth / account creation
  -> Stripe Checkout / Customer Portal
  -> API key provisioning
  -> Hosted API Gateway
       -> Auth middleware
       -> Tenant resolver
       -> Quota / credit middleware
       -> SSRF guard
       -> Run creation
  -> Queue
       -> scrape workers
       -> crawl workers
       -> browser workers
  -> Storage
       -> Postgres: users, api_keys, plans, credits, runs
       -> Object storage: artifacts by tenant/run
       -> Redis: rate limits, job locks, event streams
  -> Observability
       -> logs, metrics, traces, abuse alerts
```

## Data Model

Minimum tables:

- `users`
- `tenants`
- `api_keys`
- `plans`
- `credit_balances`
- `usage_events`
- `runs`
- `run_events`
- `artifacts`
- `stripe_customers`
- `stripe_events`

## API Key Model

Hosted API keys must be:

- generated once,
- shown once,
- stored hashed,
- scoped to tenant,
- revocable,
- last-used timestamped,
- rate-limited,
- never returned by `/api/config`.

Implementation seed:

- raw key generation, hashing, masking, verification, status metadata, and
  scope checks now exist in `scout.core.platform.api_keys`.
- tenant provisioning, scoped API-key authentication, hosted plan credit
  seeding, and standard/browser credit debit now exist in
  `scout.core.platform.account_service` with an in-memory store for local domain
  testing.
- hosted request admission now exists in `scout.core.platform.hosted_admission`;
  it authenticates first, validates URL safety second, and debits credits last.
- durable local hosted account persistence now exists in
  `scout.core.platform.account_sqlite_store`; it stores tenants, hashed API-key
  metadata, and credit balances in SQLite without storing raw API keys.
- the first hosted HTTP proof endpoint now exists at `/v1/hosted/scrape`; it
  accepts `Authorization: Bearer scout_live_...`, uses hosted admission, and
  returns non-secret usage metadata with the scrape response.
- a private-beta operator CLI now exists as `scout hosted-provision`; it creates
  hosted tenant/key/balance records in the hosted account SQLite DB and prints
  the raw API key exactly once for the operator to store.
- the current HTTP middleware has not yet been migrated to the hosted key model.
- URL safety primitives for the SSRF guard now exist in
  `scout.core.platform.url_safety`.

The current local `SCOUT_API_KEY=dev-key` middleware is not hosted-safe. It is
acceptable for local development only.

The SQLite account store is a local/dev durable repository, not the final
production persistence layer. Hosted launch still needs Postgres or equivalent,
login/user identity, Stripe provisioning, quota middleware, and object storage
isolation.

The hosted scrape endpoint is a proof boundary, not the full hosted API. Hosted
crawl, products, run orchestration, key provisioning endpoints, payment
webhooks, and async worker execution remain pending.

The `hosted-provision` CLI is an operator bridge, not a public self-serve key
dashboard. Public key generation still needs user identity, payment
confirmation, abuse controls, and audit logging.

## Run Model

Hosted runs should be async:

1. `POST /v1/runs`
2. return `run_id`
3. poll/SSE `GET /v1/runs/{id}`
4. retrieve records/artifacts after completion

Synchronous long crawls should not hold request threads open.

## Credits

Credits should be charged by action cost:

- direct scrape: low cost,
- crawl page: low cost per page,
- screenshot: medium cost,
- browser render: higher cost,
- browser minute: highest cost,
- LLM extraction: separate/pass-through or metered.

## Hosted Beta Plan

The `$22` one-time plan should be a beta credit bundle, not unlimited lifetime
usage.

Recommended:

- 2,000 standard credits,
- 100 browser credits,
- 7-day artifact retention,
- 1 concurrent run,
- max 100 pages/run,
- no guarantee of bypassing bot protection.
