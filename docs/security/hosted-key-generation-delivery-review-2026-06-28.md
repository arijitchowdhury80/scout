# Hosted API Key Generation And Delivery Review

Date: 2026-06-28
Status: Private-beta key generation and non-production delivery flow verified;
live SMTP/Stripe sandbox smoke remains pending

## Scope

This review covers the current hosted API key generation and delivery paths:

- operator CLI provisioning through `scout hosted-provision`,
- payment-confirmed provisioning through the Stripe webhook route,
- one-time raw key handoff through the key delivery adapter,
- non-secret readiness reporting through `/v1/billing/stripe/status`.

It does not certify production email provider deliverability, Stripe CLI/live
webhook forwarding, customer portal login, key recovery, or production support
operations.

## Implemented Controls

- Hosted API keys are generated with the `scout_live_` prefix.
- The raw API key is returned or delivered once; the raw API key is not stored
  in the account database.
- Stored API-key records keep a hash, tenant ID, key ID, name, scopes, and
  lifecycle status.
- Operator CLI provisioning creates a usable key, seeds hosted beta credits,
  and stores only hashed key metadata.
- Stripe webhook provisioning verifies the signed webhook, validates paid
  checkout amount/currency/status, provisions one hosted beta account, and does
  not return the raw key in the webhook response.
- Webhook replay is idempotent and does not redeliver or reprint the raw key.
- The webhook refuses to provision a new key when key delivery is disabled.
- SMTP key delivery can send the one-time raw key to the checkout customer.
- The deterministic non-production test recipient
  `scout-beta-test@example.com` receives the raw key through fake SMTP, and the
  delivered key authenticates for hosted `runs:create`.
- `/v1/billing/stripe/status` returns only booleans and does not expose Stripe,
  SMTP, webhook, or Scout API secrets.

## Evidence

Focused verification:

```bash
python3 -m pytest \
  tests/unit/cli/test_run_commands.py \
  tests/unit/core/platform/test_key_delivery.py \
  tests/unit/api/test_billing_stripe_webhook.py \
  tests/unit/api/test_billing_stripe_checkout.py -q
```

Key scenarios covered:

- `hosted-provision` creates a key that authenticates and is not stored raw.
- SMTP delivery sends a one-time key email through fake SMTP.
- Stripe webhook provisions, delivers, and returns only non-secret metadata.
- Delivered raw key authenticates after webhook provisioning.
- Replay returns idempotent metadata and does not redeliver the key.
- Disabled delivery blocks provisioning before key creation.

## Current Limits

- live SMTP provider smoke remains pending.
- Live Stripe test-mode checkout and webhook forwarding remain pending.
- Production key recovery, support, customer portal, and resend policy are not
  implemented.
- A production hosted launch should use Postgres-backed transactional
  persistence for payment event plus account creation.

## Launch Impact

The release checklist items "Hosted API key generation flow verified" and "Key
delivery email flow verified with a non-production test recipient" are satisfied
for private-beta deterministic verification. Stripe checkout/webhook test-mode
verification remains a separate open release gate.
