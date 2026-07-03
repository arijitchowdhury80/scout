# Scout Hosted Admin Operations

Date: 2026-07-03
Status: private beta operations

## What Exists Today

Scout hosted beta has API-key based access, not a login system.

- Users can generate one hosted API key through `POST /v1/hosted/beta-key` when `HOSTED_BETA_SIGNUP_ENABLED=true`.
- Operators can provision a key directly on the VPS with `scout hosted-provision`.
- Hosted tenants, API-key metadata, and credit balances are stored in SQLite at `/data/hosted_accounts.sqlite` in the running Scout container.
- Raw API keys are returned once. Scout stores only a hash.
- Hosted calls use `Authorization: Bearer scout_live_...`.

## What Does Not Exist Yet

- No email/password login.
- No user dashboard.
- No self-serve password reset.
- No Stripe-backed public purchase flow enabled for production.
- No invoice ledger or revenue dashboard.
- No formal pay-as-you-go pricing package approved.

Stripe checkout, webhook, and key-delivery scaffolding exists in code and tests, but the paid production loop is not the current beta access path.

## Admin Scripts

Run these from the Scout repo on the Mac:

```bash
cd /Users/arijitchowdhury/Dropbox/AI-Development/Scout
```

### Enable Or Disable Email-Based Beta Signup

Set `HOSTED_BETA_SIGNUP_ENABLED=true` in `/opt/prism/scout/.env` only when
the launch operator is ready for public key generation. Set it back to `false`
to stop new keys without disabling existing Bearer keys.

### Provision A Hosted API Key Directly

```bash
scripts/scout-vps-provision-hosted-key \
  --email tester@example.com \
  --key-name "PRISM beta key" \
  --plan hosted_beta_pass
```

The command prints `raw_api_key` once. Store it immediately in the consuming app's secret manager or `.env.local`.

### List Hosted Tenants And Balances

```bash
scripts/scout-vps-list-hosted-accounts
```

JSON output:

```bash
scripts/scout-vps-list-hosted-accounts --format json --limit 100
```

This shows email, tenant, key metadata, and remaining credits. It does not print raw keys or stored key hashes.

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

## Measurement Today

Today, Scout can answer:

- who generated or received a key, based on tenant email,
- which key belongs to which tenant,
- the plan attached to each tenant,
- current standard/browser credit balances,
- hosted run ownership through stored `tenant_id` and `key_id`,
- per-response `credits_charged` for hosted API calls.

Scout cannot yet answer, as a polished product feature:

- total spend by customer,
- invoice history,
- cost of goods sold by run,
- detailed per-customer usage analytics,
- conversion funnel from playground to paid account.

Those require a billing/usage ledger and Stripe integration phase.

## Pricing And Billing Gap

Pay-as-you-go pricing is not finalized. A production model should add:

- a `credit_ledger` table with every debit/credit adjustment,
- Stripe customer and checkout-session records,
- package definitions such as `$10`, `$25`, `$100` credit bundles,
- hard monthly/user rate limits,
- low-balance alerts,
- refund/manual adjustment operations,
- admin usage exports.

Until that exists, Scout is a private hosted beta with manually controlled access, not a fully self-serve paid SaaS.
