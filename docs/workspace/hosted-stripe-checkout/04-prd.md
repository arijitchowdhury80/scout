# Hosted Stripe Checkout PRD

Date: 2026-06-28
Status: Implemented

## Problem

Hosted Scout beta needs a public payment entrypoint before the existing Stripe
webhook can provision and email API keys. The website should be able to request
a Stripe Checkout Session without exposing Stripe secrets and without creating
Scout accounts before payment is confirmed.

## Scope

- Add `POST /v1/billing/stripe/checkout-session`.
- Create one-time Stripe Checkout Sessions for the hosted beta pass.
- Keep the route public under the existing `/v1/billing/stripe/*` auth bypass.
- Return only non-secret session metadata:
  - `success`
  - `checkout_session_id`
  - `checkout_url`
  - `reason`
- Use the existing webhook as the only provisioning boundary.

## Configuration

- `STRIPE_SECRET_KEY`
- `STRIPE_BETA_PRICE_ID`
- `STRIPE_SUCCESS_URL`
- `STRIPE_CANCEL_URL`

If any value is missing, the route returns `503` and does not call Stripe.

## Non-Goals

- No Stripe Customer Portal.
- No hosted account provisioning from the checkout creation route.
- No raw Scout API keys in checkout responses.
- No Stripe SDK dependency in this slice.

## Acceptance Criteria

- Checkout creation posts Stripe's form-encoded `mode=payment`,
  `line_items[0][price]`, `line_items[0][quantity]`, `success_url`, and
  `cancel_url` fields.
- Optional customer email is passed through as `customer_email`.
- Beta metadata is attached to the Checkout Session.
- Missing config fails before any outbound request.
- The response never includes `sk_...` or raw `scout_live_...` secrets.
