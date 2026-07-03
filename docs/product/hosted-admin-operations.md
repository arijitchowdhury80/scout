# Scout Hosted Admin Operations

Date: 2026-07-03
Status: private beta operations

## What Exists Today

Scout hosted beta has API-key based access, not a login system.

- Public beta testers start access through the hosted beta registration form on
  `/beta`, which posts name and email to `POST /v1/hosted/beta-key`. The route
  records the tester, provisions beta credits, and emails the raw API key once
  when SMTP delivery is configured. Without SMTP, self-service signup fails
  closed with `503`.
- Operators can provision a key from the Mac with `scripts/scout-hosted-admin generate-api-key`, which wraps the VPS `scout hosted-provision` command. The older `provision-key` alias remains available.
- Hosted tenants, API-key metadata, credit balances, and credit usage ledger entries are stored in SQLite at `/data/hosted_accounts.sqlite` in the running Scout container.
- Self-service signup emails the raw API key when SMTP delivery is configured.
  If SMTP is unavailable, `/v1/hosted/beta-key` fails closed with `503`.
  Public browser/API signup never returns `raw_api_key`; operator CLI
  provisioning is the only flow that prints the raw key once. Scout stores only
  a hash.
- Stripe checkout registration is available from `/pricing` for `$0` beta trial
  payment-method verification and paid credit packages once Stripe settings are
  configured. The `$0` beta trial uses Stripe Checkout `mode=setup` with card
  payment-method collection, so beta testers can verify the billing pipeline
  without paying during the trial. Scout asks Stripe Checkout to create a
  Customer for both setup-mode beta checkouts and paid credit-pack checkouts.
  A signed checkout webhook writes the customer name/email and Stripe reference
  IDs onto the hosted tenant and includes them in one-time API-key delivery.
- The key-delivery email is signed by Arijit, explains the 100-credit/30-day
  beta boundary, includes credit meaning, links to docs/pricing, and asks users
  to reply with their use case, target site, and failing run ID for support.
- Hosted calls use `Authorization: Bearer scout_live_...`.
- Users can inspect their current hosted account with `/v1/hosted/me`, which
  returns balances, limits, usage totals, purchase totals, and links to deeper
  `/v1/hosted/usage` and `/v1/hosted/purchases` records.
- Public pricing and credit metadata is available through
  `/v1/billing/packages`; it contains no Stripe secrets.
- The public pricing page can start Stripe Checkout for hosted credit packages
  through `/v1/billing/stripe/checkout-session` when Stripe price IDs and
  checkout settings are configured.
- Hosted Stripe success/cancel redirects should land on
  `https://scout.chowmes.com/pricing?checkout=success` or
  `https://scout.chowmes.com/pricing?checkout=cancelled` so users see a clear
  post-checkout status on the same page that initiated purchase.

## What Does Not Exist Yet

- No email/password login.
- No user dashboard.
- No self-serve password reset.
- No invoice dashboard, revenue dashboard, or cost-of-goods dashboard.
- No verified production Stripe loop yet: real test-mode Checkout completion,
  signed webhook delivery, email key delivery, and post-purchase `/v1/hosted/me`
  verification are still required before calling the hosted purchase path ready.
- No formal public self-serve account portal or Stripe customer portal.

Direct beta registration, Stripe checkout, webhook, and key-delivery scaffolding
exist in code and tests. Production still needs live SMTP for beta signup, plus
Stripe settings before the paid checkout path is operational end to end.

## Admin Scripts

Run these from the Scout repo on the Mac:

```bash
cd /Users/arijitchowdhury/Dropbox/AI-Development/Scout
```

### Enable Or Disable Beta Signup

Set `HOSTED_BETA_SIGNUP_ENABLED=true` only when SMTP delivery is configured.
Set it to `false` to stop new direct beta keys without disabling existing
Bearer keys. The public beta form should not be considered live until this flag
and SMTP key delivery are both present.

Required delivery settings:

```bash
HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.example.com
HOSTED_KEY_DELIVERY_SMTP_PORT=587
HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL="Arijit Chowdhury <scout@chowmes.com>"
HOSTED_KEY_DELIVERY_SMTP_USERNAME=...
HOSTED_KEY_DELIVERY_SMTP_PASSWORD=...
```

### Check Hosted SaaS Readiness

Use the hosted readiness checker from the Mac before inviting testers:

```bash
python3 scripts/hosted_readiness_check.py \
  --base-url https://scout.chowmes.com \
  --require-beta-signup \
  --require-paid-checkout
```

The checker calls only non-secret endpoints: `/health`,
`/v1/billing/packages`, and `/v1/billing/stripe/status`. It fails if beta signup
is disabled, SMTP delivery is missing, Stripe Checkout is missing, webhook
verification is missing, required packages are absent, or a response contains
secret-looking material.

### Provision A Hosted API Key Directly

Shortest command:

```bash
scripts/scout-generate-api-key \
  --email tester@example.com \
  --name "Tester Name" \
  --key-name "PRISM beta key" \
  --plan hosted_beta_pass
```

Equivalent admin command:

```bash
scripts/scout-hosted-admin generate-api-key \
  --email tester@example.com \
  --name "Tester Name" \
  --key-name "PRISM beta key" \
  --plan hosted_beta_pass
```

Compatibility alias:

```bash
scripts/scout-hosted-admin provision-key \
  --email tester@example.com \
  --name "Tester Name" \
  --key-name "PRISM beta key" \
  --plan hosted_beta_pass
```

The command prints `raw_api_key` once. Store it immediately in the consuming app's secret manager or `.env.local`.

### List Hosted Tenants And Balances

```bash
scripts/scout-hosted-admin list-accounts
```

JSON output:

```bash
scripts/scout-hosted-admin list-accounts --format json --limit 100
```

This shows email, tenant, key metadata, and remaining credits. It does not print raw keys or stored key hashes.

### List Hosted Credit Usage

```bash
scripts/scout-hosted-admin list-usage
```

JSON output:

```bash
scripts/scout-hosted-admin list-usage --format json --limit 100
```

Aggregate usage by action:

```bash
scripts/scout-hosted-admin list-usage --summary
```

Filter one account:

```bash
scripts/scout-hosted-admin list-usage --email tester@example.com
```

This shows email, tenant, key id, metered action, credit bucket, credits spent,
remaining balances after each event, and event timestamps. It does not print raw
keys or stored key hashes.

### List Stripe Checkout And Package Purchase Records

```bash
scripts/scout-hosted-admin list-purchases
```

JSON output:

```bash
scripts/scout-hosted-admin list-purchases --format json --limit 100
```

This shows email, package id, amount, currency, Stripe checkout/customer/payment
references, tenant id, key id, and creation time. It does not print raw keys or
stored key hashes.

Hosted self-service key generation intentionally does not use a shared password
gate. The beta flow is name plus email capture, account registration, key
generation, and one-time API-key email delivery. Paid Stripe checkout remains
the separate credit-package path.

## Login And Signup Status

There is no hosted email/password login yet. Hosted Scout currently uses API
keys, not user sessions:

- self-service signup captures name and email, provisions one tenant, emails
  one raw API key, and stores only the key hash;
- self-service signup does not expose `raw_api_key` in the HTTP response or
  public OpenAPI schema;
- admin provisioning captures name and email through the operator command and
  prints the raw API key once;
- API callers identify themselves only by `Authorization: Bearer scout_live_...`;
- `/v1/hosted/me` is the current account snapshot surface; `/v1/hosted/usage`
  and `/v1/hosted/purchases` provide deeper ledger/history rows.

A future account portal should add email verification, login, key rotation,
downloadable invoices, credit top-up, and Stripe customer portal links.

## Current Credit Model

The current code defines two credit buckets:

- `standard` credits for normal hosted acquisition.
- `browser` credits for browser-heavy acquisition.

Current action costs:

| Action | Credit Bucket | Cost |
|---|---:|---:|
| Scrape | standard | 1 |
| Crawl page | standard | 1 per returned page |
| Product/intelligence record | standard | 1 per returned record |
| Screenshot | standard | 3 |
| Browser render | browser | 5 |
| Browser minute | browser | 10 |

Current plan balances:

| Plan | Standard Credits | Browser Credits | Retention | Max Pages/Records Per Run |
|---|---:|---:|---:|---:|
| `hosted_beta_pass` | 100 | 0 | 7 days | 25 |
| `hosted_starter` | 5,000 | 250 | 14 days | 250 |
| `hosted_pro` | 25,000 | 1,500 | 30 days | 1,000 |

These are engineering limits, not final public pricing.

## Hosted Worker And Queue Limits

Hosted acquisition is intentionally bounded so beta testers cannot stampede the
VPS or create surprise crawl/browser/LLM cost. The key runtime controls are:

```text
HOSTED_RATE_LIMIT_MAX_REQUESTS=60
HOSTED_RATE_LIMIT_WINDOW_SECONDS=60
HOSTED_MAX_ACTIVE_REQUESTS=8
HOSTED_JOB_QUEUE_MAX_SIZE=250
HOSTED_JOB_QUEUE_WORKERS=2
HOSTED_ASYNC_FIRST=false
CAPACITY_RETRY_AFTER_SECONDS=5
```

Per-key rate-limit overflow returns `429` and spends no credits. Worker
saturation returns `202 Accepted` for expensive hosted acquisition endpoints
when queue space is available. The response includes `job_id`, `job_url`, and
`Retry-After`; callers poll `/v1/hosted/jobs/{job_id}` with the same Bearer key.
Queued jobs spend credits only when execution starts and produces the same
hosted result shape as the synchronous path. Queue overflow returns `429`.

For 250-user public beta bursts on the current small VPS, run with
`HOSTED_ASYNC_FIRST=true` and a queue large enough for the planned burst. That
keeps the HTTP path responsive by accepting expensive work as jobs before live
crawler/browser execution starts.

Do not run `HOSTED_ASYNC_FIRST=true` with `HOSTED_JOB_QUEUE_WORKERS=0`. That
configuration accepts hosted requests as `202 queued` jobs but no worker drains
the in-process queue, so callers see a successful-looking response that never
finishes. If no worker is running, keep `HOSTED_ASYNC_FIRST=false` so hosted
calls execute inline and fail visibly.

This queue is in-process and single-node. It is appropriate for the current VPS
private beta, but a larger public launch should replace it with a durable queue,
shared rate limiter, worker autoscaling, and external artifact storage.

## Measurement Today

Today, Scout can answer:

- who generated or received a key, based on tenant email,
- the name supplied during self-service or admin provisioning,
- which key belongs to which tenant,
- the plan attached to each tenant,
- current standard/browser credit balances,
- recent per-tenant usage through `/v1/hosted/usage`,
- usage totals in `/v1/hosted/me`,
- per-tenant Stripe checkout/package purchase history through `/v1/hosted/purchases`,
- purchase totals in `/v1/hosted/me`,
- every successful hosted credit debit in the `hosted_credit_ledger` table,
- Stripe checkout/package purchase records in `hosted_payment_checkouts`,
- hosted run ownership through stored `tenant_id` and `key_id`,
- per-response `credits_charged` for hosted API calls.
- public package/credit/unit-economics metadata through `/v1/billing/packages`.

Scout cannot yet answer, as a polished product feature:

- invoice history,
- cost of goods sold by run,
- margin by customer or plan,
- packaged per-customer usage analytics,
- conversion funnel from playground to paid account.

Those require a cost model, analytics dashboard, customer account portal, and
fully validated Stripe production flow.

## Pricing And Billing Gap

Pay-as-you-go pricing candidate:

- Beta trial: 30 days, 100 standard credits, $0 charge, payment method required through Stripe setup-mode once hosted billing is configured.
- First paid package: $10 for 1,000 standard credits.
- A standard credit means one scrape, one returned crawl page, or one product/intelligence record.
- Browser credits remain separately metered and are not included in the first public package.
- Current default economics estimate $2.59 loaded cost, $7.41 gross profit, 74.1% gross margin, and break-even at 17 packs/month for the $10 package.
- The pricing page exposes `$10`, `$25`, and `$100` hosted credit checkout
  options. Successful checkout provisioning depends on configured Stripe price
  IDs, signed webhook delivery, and SMTP key delivery.

A production billing model should still add:

- customer-facing purchase history and invoice links,
- hard monthly/user rate limits,
- low-balance alerts,
- refund/manual adjustment operations,
- unit-economics inputs: host cost, LLM cost, browser minutes, storage, bandwidth, support, maintenance, and target gross margin,
- admin usage exports.

Until that exists, Scout is a private hosted beta with manually controlled access, not a fully self-serve paid SaaS.
