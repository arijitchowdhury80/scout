# Stripe Test-Mode Readiness

Date: 2026-06-29

Status: **Deterministic coverage passed; real Stripe test-mode smoke is still open.**

## Summary

Scout has working deterministic coverage for the hosted beta payment path:

- Stripe Checkout Session request construction.
- Public checkout-session API route.
- Public Stripe readiness status route.
- Stripe webhook signature validation.
- Checkout completion provisioning.
- Duplicate checkout idempotency.
- Hosted API key delivery after paid checkout.
- Secret non-disclosure in route responses.

This does **not** close the release checklist gate for real Stripe test-mode checkout and webhook verification. The current checkout does not have real Stripe test-mode credentials configured.

## Verification Run

Command:

```bash
python3 -m pytest \
  tests/unit/core/platform/test_stripe_checkout.py \
  tests/unit/api/test_billing_stripe_checkout.py \
  tests/unit/api/test_billing_stripe_webhook.py \
  tests/unit/core/platform/test_payment_provisioning.py \
  tests/unit/core/platform/test_key_delivery.py \
  -q
```

Result:

```text
22 passed, 2 warnings in 1.54s
```

Warnings were from Crawl4AI/Pydantic deprecation warnings imported during test collection. They were not Stripe failures.

## Configuration Check

The following real Stripe test-mode settings were not configured in the process environment:

- `STRIPE_SECRET_KEY`
- `STRIPE_BETA_PRICE_ID`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_SUCCESS_URL`
- `STRIPE_CANCEL_URL`

The local `.env` file exists, but those settings are blank there as well. `.env.local` does not exist.

No secret values were printed during this check.

## What Is Verified

| Area | Status | Evidence |
|---|---:|---|
| Checkout service builds expected Stripe form request | Passed | `tests/unit/core/platform/test_stripe_checkout.py` |
| Checkout service fails closed when unconfigured | Passed | `tests/unit/core/platform/test_stripe_checkout.py` |
| `/v1/billing/stripe/status` returns non-secret readiness flags | Passed | `tests/unit/api/test_billing_stripe_checkout.py` |
| `/v1/billing/stripe/checkout-session` returns checkout URL when service succeeds | Passed | `tests/unit/api/test_billing_stripe_checkout.py` |
| Checkout route returns `503` when unconfigured | Passed | `tests/unit/api/test_billing_stripe_checkout.py` |
| Webhook rejects missing or invalid signatures | Passed | `tests/unit/api/test_billing_stripe_webhook.py` |
| Valid `checkout.session.completed` provisions hosted beta access | Passed | `tests/unit/api/test_billing_stripe_webhook.py` |
| Duplicate checkout session is idempotent | Passed | `tests/unit/api/test_billing_stripe_webhook.py` |
| Key delivery sends hosted key without route response leakage | Passed | `tests/unit/core/platform/test_key_delivery.py` |

## What Is Still Open

The release checklist item **"Stripe checkout and webhook tested in Stripe test mode"** remains open until the following is run against a real Stripe test account:

1. Configure:
   - `STRIPE_SECRET_KEY=sk_test_...`
   - `STRIPE_BETA_PRICE_ID=price_...`
   - `STRIPE_WEBHOOK_SECRET=whsec_...`
   - `STRIPE_SUCCESS_URL=http://127.0.0.1:8421/?checkout=success`
   - `STRIPE_CANCEL_URL=http://127.0.0.1:8421/?checkout=cancelled`
   - hosted key delivery settings for a non-production recipient.
2. Start Scout locally.
3. Verify `/v1/billing/stripe/status` reports:
   - `checkout_configured: true`
   - `webhook_configured: true`
   - `key_delivery_configured: true`
   - `ready_for_paid_key_delivery: true`
4. Create a real test-mode Checkout Session through `/v1/billing/stripe/checkout-session`.
5. Complete test payment in Stripe Checkout.
6. Deliver the real Stripe webhook to `/v1/billing/stripe/webhook`.
7. Confirm hosted API key is provisioned, delivered, and usable against `/v1/hosted/me`.
8. Confirm no raw hosted key or Stripe secret appears in HTTP responses, logs, artifacts, or website source.

## Release Decision

This gate is **not approved for public launch** yet.

The implementation is ready for a real test-mode smoke once Stripe test credentials and webhook delivery are configured.
