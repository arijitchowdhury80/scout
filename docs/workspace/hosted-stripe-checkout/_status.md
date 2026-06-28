# Hosted Stripe Checkout Status

Date: 2026-06-28
Status: Implemented

## Goal

Add the public checkout-session creation boundary required for the Scout website
to start the hosted beta payment flow. This creates Stripe Checkout Sessions
only; the existing signed Stripe webhook still performs all payment-confirmed
tenant provisioning and one-time API key delivery.

## Completed

- [x] TDD tests for Stripe Checkout Session creation service.
- [x] TDD tests for `/v1/billing/stripe/checkout-session`.
- [x] Stdlib Stripe form-post transport.
- [x] Secret-safe checkout result model.
- [x] FastAPI dependency and startup wiring.
- [x] Config flags for Stripe secret key, beta price, success URL, and cancel URL.
- [x] Non-secret Stripe readiness endpoint for launch website gating.

## Verification

- RED:
  `python3 -m pytest tests/unit/core/platform/test_stripe_checkout.py tests/unit/api/test_billing_stripe_checkout.py -q`
  - Result: failed with missing `scout.core.platform.stripe_checkout` and missing
    `get_stripe_checkout_service`.
- GREEN:
  `python3 -m pytest tests/unit/core/platform/test_stripe_checkout.py tests/unit/api/test_billing_stripe_checkout.py -q`
  - Result: 4 passed.
- Billing checkpoint:
  `python3 -m pytest tests/unit/api/test_billing_stripe_checkout.py tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  - Result: 15 passed.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q`
  - Result: 119 passed.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q`
  - Result: 470 passed.
- Static/lint checkpoint:
  `python3 -m pyright scout/` and
  `ruff check scout/ tests/ && ruff format --check scout/ tests/`
  - Result: pyright 0 errors; Ruff passed.
- Stripe readiness RED:
  `python3 -m pytest tests/unit/api/test_billing_stripe_checkout.py tests/unit/website/test_launch_website.py -q`
  - Result: failed because `/v1/billing/stripe/status` returned 404 and the
    website did not fetch readiness.
- Stripe readiness GREEN:
  `python3 -m pytest tests/unit/api/test_billing_stripe_checkout.py tests/unit/website/test_launch_website.py -q`
  - Result: 7 passed.

## Readiness Endpoint

`GET /v1/billing/stripe/status` returns only booleans:

- `checkout_configured`
- `webhook_configured`
- `key_delivery_configured`
- `ready_for_paid_key_delivery`

The endpoint intentionally never returns Stripe secrets, webhook secrets, SMTP
credentials, or Scout API keys.

## Still Missing

- Live Stripe sandbox Checkout Session smoke with real test-mode keys.
- Website button wiring to call the checkout route and redirect to
  `checkout_url`.
- Stripe Customer Portal and subscription management.
