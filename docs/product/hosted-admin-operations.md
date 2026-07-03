# Scout Hosted Admin Operations

Date: 2026-07-03
Status: private beta operations

## What Exists Today

Scout hosted beta has API-key based access, not a login system.

- Public beta testers start access on `/beta`, which posts name and email to
  `POST /v1/hosted/beta-key`. Scout records the tester, provisions a
  finite-credit hosted beta account, and SMTP delivers the raw API key once.
  Public signup never shows the raw key in the browser.
- Paid hosted credit packages start from `/pricing`, which posts to
  `POST /v1/billing/stripe/checkout-session`. Stripe remains the paid
  purchase path and the future card-backed beta path if that policy is
  re-approved.
- Operators can provision a key from the Mac with `scripts/scout-hosted-admin generate-api-key`, which wraps the VPS `scout hosted-provision` command. The older `provision-key` alias remains available.
- Hosted tenants, API-key metadata, credit balances, and credit usage ledger entries are stored in SQLite at `/data/hosted_accounts.sqlite` in the running Scout container.
- Self-service signup emails the raw API key when SMTP delivery is configured.
  Public browser/API signup never returns `raw_api_key`; operator CLI
  provisioning is the only flow that prints the raw key once. Scout stores only
  a hash.
- Queued beta signups can be inspected with `list-signups` and processed after
  SMTP configuration with `process-pending-signups`.
- Testers can check non-secret registration state from `/beta` or
  `POST /v1/hosted/beta-key/status` using only the registration email. The
  status lookup never returns raw API keys or key hashes.
- Stripe checkout forms are available from `/pricing` for paid hosted credit
  packages. They are readiness-gated by `/v1/billing/stripe/status` and stay
  disabled until Stripe settings, signed webhook delivery, and SMTP key
  delivery are configured.
- The paid hosted purchase path uses Stripe Checkout with card collection,
  `customer_email`, and metadata. It intentionally does not send
  `customer_creation=always`, which is reserved for payment-mode customer
  creation. Paid credit packages use Checkout `mode=payment`,
  `customer_creation=always`, and package price line items.
- The key-delivery email subject is `Your Scout beta tester API key is ready`.
  It is signed by Arijit Chowdhury, Founder, Chowmes; explains the
  100-credit/30-day beta boundary; says hosted access is not unlimited
  crawling; includes credit meaning, account/balance, usage ledger, purchase
  history, docs, and pricing links; warns users not to paste keys into frontend
  code/screenshots/tickets/public repos; and asks testers to reply with their
  use case, target site, and failing run ID for support.
- Hosted calls use `Authorization: Bearer scout_live_...`.
- Users can inspect their current hosted account with `/v1/hosted/me`, which
  returns balances, limits, usage totals, purchase totals, and links to deeper
  `/v1/hosted/usage` and `/v1/hosted/purchases` records.
- Public pricing and credit metadata is available through
  `/v1/billing/packages`; it contains no Stripe secrets. The response includes
  `credit_policy`, a structured metering table with action, credit bucket,
  credits per unit, metered unit, `included_in_standard_1000`, and customer
  description fields so consuming apps do not have to parse pricing prose.
- The public pricing page can start Stripe Checkout for hosted credit packages
  through `/v1/billing/stripe/checkout-session` when Stripe price IDs,
  checkout settings, webhook signing, and SMTP key delivery are configured.
- The checkout API itself fails closed before creating paid Stripe sessions if
  the webhook secret or SMTP key delivery is missing.
- If a future `$0` `beta_trial` Checkout Session is created, Scout records a
  non-secret `hosted_signup_events` row with status `checkout_started`, source
  `stripe_checkout`, delivery status `checkout_session_created`, and the
  Stripe Checkout Session id as the reference.
- A successful paid Stripe webhook creates a hosted tenant for a first-time
  buyer, or adds the purchased credits to the existing tenant when the checkout
  email already has a hosted account. Existing-account top-ups do not email a
  second raw API key; they record the purchase against the tenant/key and update
  the credit balance.
- A `$0` `beta_trial` checkout for an email that already has a hosted account
  is recorded for auditability but does not add another 100 free beta credits.
  Only paid packages add credits to an existing tenant balance.
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

Stripe checkout, webhook, key delivery, and beta email registration exist in
code and tests. Production still needs live SMTP before beta key delivery is
operational end to end. Paid checkout additionally needs live Stripe settings.
Partial Stripe configuration is not enough: checkout creation intentionally
remains blocked until webhook verification and key delivery are also ready.

## Admin Scripts

Run these from the Scout repo on the Mac:

```bash
cd /Users/arijitchowdhury/Dropbox/AI-Development/Scout
```

### Enable Or Disable Beta Signup

Set `HOSTED_BETA_SIGNUP_ENABLED=true` to allow public beta email registration.
Set beta signup to `false` to stop new beta setup without disabling existing
Bearer keys. The public beta flow should not be considered ready until this
flag and SMTP key delivery are present.

Required delivery settings, stored in an ignored local file such as
`secrets/scout-production.env` before pushing to the VPS:

Create a starter template first so the required hosted keys are not assembled
from memory:

```bash
scripts/scout-hosted-admin write-config-template \
  --output secrets/scout-production.env
```

The template contains only placeholder values and safe defaults. It refuses to
overwrite an existing file unless `--force` is passed.

```bash
HOSTED_BETA_SIGNUP_ENABLED=true
HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.example.com
HOSTED_KEY_DELIVERY_SMTP_PORT=587
HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL="Arijit Chowdhury <scout@chowmes.com>"
HOSTED_KEY_DELIVERY_SMTP_USERNAME=...
HOSTED_KEY_DELIVERY_SMTP_PASSWORD=...
HOSTED_KEY_DELIVERY_SMTP_USE_TLS=true

STRIPE_SECRET_KEY=sk_test_...
STRIPE_STANDARD_1000_PRICE_ID=price_...
STRIPE_STANDARD_3000_PRICE_ID=price_...
STRIPE_STANDARD_15000_PRICE_ID=price_...
STRIPE_SUCCESS_URL=https://scout.chowmes.com/pricing?checkout=success
STRIPE_CANCEL_URL=https://scout.chowmes.com/pricing?checkout=cancelled
STRIPE_WEBHOOK_SECRET=whsec_...
```

Create the paid package price IDs from Scout's canonical package model instead
of hand-building mismatched Stripe prices:

```bash
scripts/scout-hosted-admin bootstrap-stripe-prices \
  --secrets-file secrets/scout-production.env \
  --dry-run

scripts/scout-hosted-admin bootstrap-stripe-prices \
  --secrets-file secrets/scout-production.env \
  --yes \
  --write-env
```

The bootstrap helper creates one-time Stripe prices for public paid packages
only: `standard_1000`, `standard_3000`, and `standard_15000`. It excludes
`beta_trial` because beta uses Stripe Checkout setup mode and excludes
`browser_100` because browser-credit economics remain private. The helper
prints price IDs and env key names only; it refuses to print Stripe secret
keys.

Install those values on the VPS with the allowlisted production env helper:

```bash
scripts/scout-hosted-admin validate-config \
  --secrets-file secrets/scout-production.env \
  --require all

scripts/scout-hosted-admin configure-production-env \
  --secrets-file secrets/scout-production.env \
  --require all \
  --restart
```

The helper updates `/opt/prism/scout/.env`, preserves unrelated existing env
lines, prints variable names only, never prints secret values, and recreates the
`scout` container when `--restart` is passed. It validates the local secrets
file before upload and refuses partial production config by default. Use
`--require beta` only when intentionally enabling email beta keys before paid
checkout.

After SMTP values are installed, send a smoke-test email before inviting real
testers:

```bash
scripts/scout-hosted-admin send-test-email \
  --email arijit@example.com \
  --name "Arijit"
```

The smoke email uses the same hosted key-delivery SMTP path, but it does not
create a hosted account, grant credits, issue a real API key, or print SMTP
secrets. The email body clearly says it is a smoke test and cannot be mistaken
for a real hosted Scout key.

### Process Queued Beta Signups

When beta signup is enabled before SMTP is configured, Scout records
`pending_delivery` signup events without creating accounts or API keys. After
SMTP is configured and the smoke email succeeds, inspect the queue first:

```bash
scripts/scout-hosted-admin process-pending-signups --dry-run
```

Then process queued requests:

```bash
scripts/scout-hosted-admin process-pending-signups --yes
```

The processor provisions one hosted beta account per newest pending email,
sends the raw API key by SMTP, records a `delivered` signup event on success,
and deletes the account plus records `failed` if delivery fails. It refuses to
mutate anything unless `--yes` or `--dry-run` is provided, and it never prints
raw API keys, key hashes, or SMTP passwords.

### Run The Hosted Production Smoke Gate

Use the production smoke gate when checking whether the hosted SaaS path is
actually ready for beta signup and paid checkout. It checks `/health`,
`/v1/billing/packages`, `/v1/billing/stripe/status`, and, only when readiness
flags are green, the non-mutating Stripe smoke checks for both `$0` beta setup
and the paid `standard_1000` package.

```bash
scripts/scout-hosted-admin production-smoke --json
```

For a hard gate in release scripts:

```bash
scripts/scout-hosted-admin production-smoke --require-ready
```

The smoke output is deliberately non-secret. It prints readiness booleans,
blockers, and concrete next commands, but never prints Stripe secret keys,
webhook secrets, SMTP passwords, raw hosted API keys, or key hashes.

As of the latest hosted check, `https://scout.chowmes.com` has green health and
package metadata, but production self-service remains blocked until SMTP key
delivery, Stripe Checkout, and the Stripe webhook secret are configured.

### Let Testers Check Beta Request Status

The beta page includes a self-service status lookup for testers who submitted
the form but have not received a key yet. It calls:

```bash
curl -X POST https://scout.chowmes.com/v1/hosted/beta-key/status \
  -H "Content-Type: application/json" \
  -d '{"email":"tester@example.com"}'
```

Possible non-secret statuses include:

- `pending_delivery`: request recorded; API key will be emailed after delivery
  configuration is ready.
- `delivered`: Scout already emailed the key to that inbox.
- `failed`: delivery failed; support should inspect the signup event.
- `duplicate` or `account_exists`: an account/key already exists for that email.
- `not_found`: no request is recorded for that email.

The endpoint does not authenticate because it is used before a tester has an
API key. It is rate-limited through the same public beta signup limiter and
returns only non-secret metadata.

### Let Testers Reissue A Lost API Key

Scout stores only API-key hashes, so it cannot show an old raw key again. The
beta page includes a self-service recovery form that calls:

```bash
curl -X POST https://scout.chowmes.com/v1/hosted/beta-key/reissue \
  -H "Content-Type: application/json" \
  -d '{"email":"tester@example.com"}'
```

If a hosted account exists for that email and SMTP delivery is configured,
Scout issues a replacement key, emails it to the same inbox, and disables the
previous key only after delivery succeeds. The HTTP response never includes
the raw key or key hash.

If no account exists, Scout returns a non-enumerating accepted response:
"If a hosted Scout account exists for this email, Scout will email a
replacement API key." If SMTP delivery is not configured, the route fails
closed with `503` because creating a replacement key without an email channel
would lose the only raw copy.

### Disable Hosted Access

If a hosted API key is leaked, a tester abuses the beta, or a consuming app
must be cut off, disable access from the Mac without deleting audit records:

```bash
scripts/scout-hosted-admin disable-access \
  --email tester@example.com \
  --reason "leaked key" \
  --yes
```

You can also target a specific tenant or key:

```bash
scripts/scout-hosted-admin disable-access \
  --tenant-id tenant_... \
  --reason "customer requested shutdown" \
  --yes

scripts/scout-hosted-admin disable-access \
  --key-id key_... \
  --reason "rotated compromised key" \
  --yes
```

The command updates `/data/hosted_accounts.sqlite` inside the hosted Scout
container. Email and tenant targets disable the tenant plus all tenant keys.
Key targets disable only the selected key. The helper requires `--yes`, prints
only non-secret fields, and never prints raw API keys or stored key hashes.

After configuration, verify readiness:

```bash
scripts/scout-hosted-admin readiness \
  --require-beta-signup \
  --require-paid-checkout
```

Then run Stripe test-mode smoke:

```bash
python3 scripts/stripe_test_mode_smoke.py \
  --base-url https://scout.chowmes.com \
  --email scout-paid-smoke@example.com \
  --name "Scout Paid Smoke" \
  --package-id standard_1000 \
  --create-checkout

python3 scripts/stripe_test_mode_smoke.py \
  --base-url https://scout.chowmes.com \
  --email scout-beta-test@example.com \
  --name "Scout Beta Tester" \
  --package-id beta_trial \
  --create-checkout
```

### Check Hosted SaaS Readiness

Use the hosted readiness checker from the Mac before inviting testers:

```bash
scripts/scout-hosted-admin readiness \
  --require-beta-signup \
  --require-paid-checkout
```

The checker calls only non-secret endpoints: `/health`,
`/v1/billing/packages`, and `/v1/billing/stripe/status`. It fails if beta
email registration is not ready, paid checkout is not ready, SMTP delivery is
missing, required packages are absent, or a response contains secret-looking
material. Paid-readiness mode also reports Stripe Checkout and webhook
configuration gaps.

Machine-readable output for deployment logs:

```bash
scripts/scout-hosted-admin readiness --json
```

The underlying `GET /v1/billing/stripe/status` response is also operator
actionable. In addition to backward-compatible booleans such as
`ready_for_beta_checkout` and `ready_for_paid_key_delivery`, it returns:

- `public_self_service_path`: currently `email_beta_registration`; beta
  testers should start at `/beta` and receive the key by email.
- `public_beta_checkout_endpoint` and `public_paid_checkout_endpoint`: the
  endpoint the website uses to create setup/payment Checkout Sessions.
- `direct_beta_key_enabled`: deprecated compatibility flag retained for older
  diagnostics. `/v1/hosted/beta-key` now follows `HOSTED_BETA_SIGNUP_ENABLED`.
- `missing_environment_keys`: exact non-secret environment variable names still
  needed for checkout, webhook verification, paid price IDs, or SMTP delivery.
- `missing_configuration`: machine-readable missing capability names such as
  `stripe_checkout`, `stripe_webhook_secret`, and `hosted_key_delivery_smtp`.
- `blocking_reasons`: human-readable, non-secret reasons shown by the launch
  website when checkout is paused.
- `operator_next_actions`: non-secret setup steps for the operator to complete.
- `customer_next_actions`: stable user-facing routes such as `/beta` and
  `/pricing`.

The status route never returns Stripe secret keys, webhook secret values, SMTP
password values, API-key hashes, or raw hosted API keys. It may return
environment variable names such as `HOSTED_KEY_DELIVERY_SMTP_PASSWORD` so an
operator can configure the missing secret without exposing the secret itself.

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

### List Beta Signup Requests And Delivery Outcomes

```bash
scripts/scout-hosted-admin list-signups
```

JSON output:

```bash
scripts/scout-hosted-admin list-signups --format json --limit 100
```

Filter failed delivery attempts:

```bash
scripts/scout-hosted-admin list-signups --status failed
```

Filter one email:

```bash
scripts/scout-hosted-admin list-signups --email tester@example.com
```

This shows each self-service beta API-key request, including email, name,
status, source, delivery status, reason, tenant id, key id, event id, and
timestamp. It is the fastest operator view for answering who requested a hosted
key, whether it was delivered, whether it was a duplicate, and why it failed.
It does not print raw keys or stored key hashes.

### Send Hosted Key Delivery Smoke-Test Email

```bash
scripts/scout-hosted-admin send-test-email \
  --email tester@example.com \
  --name "Tester Name"
```

Use this after configuring SMTP and before enabling self-service beta testers.
It sends a smoke-test email through the same SMTP delivery service used by
`/v1/hosted/beta-key` and Stripe provisioning. It does not create an account,
grant credits, issue a real API key, or print SMTP secrets, raw API keys, or
stored key hashes.

### Hosted Billing Admin Metrics API

Operators can also inspect non-secret hosted beta metrics through the live
service. This is useful when Scout is running as a hosted SaaS service and the
operator wants API-level visibility without SSHing into the SQLite database.

```bash
curl https://scout.chowmes.com/v1/billing/admin/metrics \
  -H "X-API-Key: $SCOUT_SERVICE_API_KEY"
```

The endpoint is protected by the service API key and remains protected in
`SCOUT_PUBLIC_HOSTED_ONLY=true` mode. It returns signup/account counts, active
and disabled tenant counts, beta signup delivery/failed/duplicate counts,
remaining credit totals, usage event totals, standard/browser credits spent,
purchase count, revenue cents, and recent signup, account, usage, and purchase
records.

It does not return raw hosted API keys, key hashes, Stripe secrets, SMTP
secrets, or customer payment details.

### Drain Pending Beta Key Deliveries

If beta registration was open while SMTP delivery was not configured, Scout
records those requests as `pending_delivery` without creating accounts or
issuing raw API keys. After SMTP is configured and smoke-tested, drain the
pending queue through the protected admin API:

```bash
curl -X POST "https://scout.chowmes.com/v1/billing/admin/deliver-pending-beta-keys?limit=25" \
  -H "X-API-Key: $SCOUT_SERVICE_API_KEY"
```

This endpoint:

- requires the service API key;
- fails closed with `503` when hosted key delivery is not configured;
- provisions each pending beta tester as a hosted account;
- emails the raw API key exactly once;
- records a new `admin_pending_beta_delivery` signup event;
- returns only email, status, tenant ID, key ID, delivery status, reason, and
  batch counts.

It does not return raw hosted API keys, key hashes, SMTP secrets, Stripe
secrets, or customer payment details.

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
- self-service reissue emails a replacement key to the account email and
  disables the previous key only after email delivery succeeds;
- admin provisioning captures name and email through the operator command and
  prints the raw API key once;
- API callers identify themselves only by `Authorization: Bearer scout_live_...`;
- `/v1/hosted/me` is the current account snapshot surface; `/v1/hosted/usage`
  and `/v1/hosted/purchases` provide deeper ledger/history rows.

A future account portal should add email verification, login, key rotation,
downloadable invoices, explicit top-up history UX, and Stripe customer portal
links. The backend already records paid checkout purchases and can top up an
existing tenant balance when the Stripe checkout email matches an existing
hosted account. Repeated `$0` beta-trial checkouts are not credit top-ups.

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
HOSTED_BETA_SIGNUP_RATE_LIMIT_MAX_REQUESTS=3
HOSTED_BETA_SIGNUP_RATE_LIMIT_WINDOW_SECONDS=3600
HOSTED_MAX_ACTIVE_REQUESTS=8
HOSTED_JOB_QUEUE_MAX_SIZE=250
HOSTED_JOB_QUEUE_WORKERS=2
HOSTED_ASYNC_FIRST=false
CAPACITY_RETRY_AFTER_SECONDS=5
```

`HOSTED_BETA_SIGNUP_RATE_LIMIT_*` is keyed by the apparent client address
(`X-Forwarded-For` first hop when present, otherwise the request client host).
It limits public `/v1/hosted/beta-key` registration attempts before account
creation or email delivery.

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
- paid checkout top-ups for existing hosted tenants when Stripe webhook email
  matches an existing account,
- operator-level signup-attempt, delivery, duplicate, failure, credit, usage,
  purchase, and revenue summaries through `/v1/billing/admin/metrics`,
- self-service signup event review from the Mac with
  `scripts/scout-hosted-admin list-signups`,
- SMTP/key-delivery smoke testing from the Mac with
  `scripts/scout-hosted-admin send-test-email`,
- every beta key request outcome in the `hosted_signup_events` table,
- every successful hosted credit debit in the `hosted_credit_ledger` table,
- Stripe checkout/package purchase records in `hosted_payment_checkouts`,
- hosted run ownership through stored `tenant_id` and `key_id`,
- per-response `credits_charged` for hosted API calls,
- public package/credit/unit-economics metadata through `/v1/billing/packages`,
- structured metering policy through `/v1/billing/packages` field
  `credit_policy`, including `included_in_standard_1000` counts for the first
  public 1,000-credit package.

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

- Beta trial: 30 days, 100 standard credits, $0 charge, name/email registration, and API-key email delivery.
- First paid package: $10 for 1,000 standard credits.
- A standard credit means one scrape, one returned crawl page, or one product/intelligence record.
- Browser credits remain separately metered and are not included in the first public package.
- Current default economics estimate $2.59 loaded cost, $7.41 gross profit, 74.1% gross margin, and break-even at 17 packs/month for the $10 package.
- The pricing page exposes readiness-gated `$10`, `$25`, and `$100` hosted
  credit checkout options. The beta page exposes a separate readiness-gated
  beta key registration form. Successful beta delivery depends on SMTP key
  delivery; successful paid checkout additionally depends on configured Stripe
  price IDs and signed webhook delivery.

A production billing model should still add:

- customer-facing purchase history and invoice links,
- hard monthly/user rate limits,
- low-balance alerts,
- refund/manual adjustment operations,
- unit-economics inputs: host cost, LLM cost, browser minutes, storage, bandwidth, support, maintenance, and target gross margin,
- admin usage exports.

Until that exists, Scout is a private hosted beta with manually controlled access, not a fully self-serve paid SaaS.
