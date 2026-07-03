# Scout Hosted Admin Operations

Date: 2026-07-03
Status: private beta operations

## What Exists Today

Scout hosted beta has API-key based access, not a login system.

- Users can register for one hosted API key through `POST /v1/hosted/beta-key` when `HOSTED_BETA_SIGNUP_ENABLED=true` and SMTP key delivery is configured.
- Operators can provision a key from the Mac with `scripts/scout-hosted-admin provision-key`, which wraps the VPS `scout hosted-provision` command.
- Hosted tenants, API-key metadata, credit balances, and credit usage ledger entries are stored in SQLite at `/data/hosted_accounts.sqlite` in the running Scout container.
- Self-service signup emails the raw API key and never returns it in the HTTP response. Operator CLI provisioning still prints the raw key once. Scout stores only a hash.
- Hosted calls use `Authorization: Bearer scout_live_...`.
- Users can inspect their current hosted account and recent usage with `/v1/hosted/me` and `/v1/hosted/usage`.

## What Does Not Exist Yet

- No email/password login.
- No user dashboard.
- No self-serve password reset.
- No Stripe-backed public purchase flow enabled for production.
- No invoice ledger, revenue dashboard, or cost-of-goods dashboard.
- No formal pay-as-you-go pricing package approved.

Stripe checkout, webhook, and key-delivery scaffolding exists in code and tests, but the paid production loop is not the current beta access path.

## Admin Scripts

Run these from the Scout repo on the Mac:

```bash
cd /Users/arijitchowdhury/Dropbox/AI-Development/Scout
```

### Enable Or Disable Email-Based Beta Signup

Set `HOSTED_BETA_SIGNUP_ENABLED=true` in `/opt/prism/scout/.env` only when
SMTP delivery is configured and the launch operator is ready for public key
generation. Set it back to `false` to stop new keys without disabling existing
Bearer keys.

Required delivery settings:

```bash
HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.example.com
HOSTED_KEY_DELIVERY_SMTP_PORT=587
HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL="Arijit Chowdhury <scout@chowmes.com>"
HOSTED_KEY_DELIVERY_SMTP_USERNAME=...
HOSTED_KEY_DELIVERY_SMTP_PASSWORD=...
```

### Provision A Hosted API Key Directly

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

### Generate A Strong Password Or Secret

For beta invite passwords, admin tokens, SMTP app secrets, or temporary shared
operator secrets, generate a strong local value and paste it into the target
environment file manually:

```bash
scripts/scout-hosted-admin generate-secret --label HOSTED_ADMIN_TOKEN
scripts/scout-hosted-admin generate-secret --label HOSTED_BETA_INVITE_PASSWORD
```

Current hosted self-service key generation does not require an invite password.
If an invite-password gate is reintroduced later, store that password only in
the VPS environment, not in Git.

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
- the name supplied during self-service or admin provisioning,
- which key belongs to which tenant,
- the plan attached to each tenant,
- current standard/browser credit balances,
- recent per-tenant usage through `/v1/hosted/usage`,
- every successful hosted credit debit in the `hosted_credit_ledger` table,
- hosted run ownership through stored `tenant_id` and `key_id`,
- per-response `credits_charged` for hosted API calls.

Scout cannot yet answer, as a polished product feature:

- total spend by customer,
- invoice history,
- cost of goods sold by run,
- margin by customer or plan,
- packaged per-customer usage analytics,
- conversion funnel from playground to paid account.

Those require a billing ledger, cost model, analytics dashboard, and Stripe integration phase.

## Pricing And Billing Gap

Pay-as-you-go pricing candidate:

- Beta trial: 30 days, 100 standard credits, $0 charge, payment method required later.
- First paid package: $10 for 1,000 standard credits.
- A standard credit means one scrape, one returned crawl page, or one product/intelligence record.
- Browser credits remain separately metered and are not included in the first public package.
- Current default economics estimate $2.59 loaded cost, $7.41 gross profit, 74.1% gross margin, and break-even at 17 packs/month for the $10 package.

A production billing model should still add:

- Stripe customer and checkout-session records,
- package definitions such as `$10`, `$25`, `$100` credit bundles,
- a paid-credit purchase ledger separate from the usage ledger,
- hard monthly/user rate limits,
- low-balance alerts,
- refund/manual adjustment operations,
- unit-economics inputs: host cost, LLM cost, browser minutes, storage, bandwidth, support, maintenance, and target gross margin,
- admin usage exports.

Until that exists, Scout is a private hosted beta with manually controlled access, not a fully self-serve paid SaaS.
