# Hosted Stripe Webhook PRD

## Summary

Add a Stripe-compatible webhook endpoint for hosted Scout beta checkout
completion events. The route must verify Stripe's signature, translate
`checkout.session.completed` into `HostedCheckoutProvisioningRequest`, call the
existing provisioning service, and return only non-secret metadata.

## Acceptance Criteria

- Missing or invalid `Stripe-Signature` rejects with no provisioning.
- Valid irrelevant event types are acknowledged as ignored and do not provision.
- Valid paid `checkout.session.completed` events provision a hosted beta account.
- Duplicate checkout session events return idempotent metadata.
- Webhook responses never include raw `scout_live_` API keys.
- The route does not require the local `X-API-Key`; Stripe signature is the auth
  boundary for this endpoint.

## Technical Contract

- Endpoint: `POST /v1/billing/stripe/webhook`
- Auth: `Stripe-Signature` header with HMAC SHA-256 signature.
- Secret source: `SCOUT_STRIPE_WEBHOOK_SECRET`.
- Local setting name: `stripe_webhook_secret`.
- Supported event: `checkout.session.completed`.
- Required session fields:
  - `id`
  - `amount_total`
  - `currency`
  - `payment_status`
  - customer email from `customer_details.email` or `customer_email`
- Response includes: `success`, `ignored`, `already_processed`, `tenant_id`,
  `key_id`, `reason`.
- Response excludes: raw API key, key hash, full customer payload.

## Design Decision

The webhook route calls the provisioning service, but it discards the raw API
key before returning the HTTP response. Stripe is not the customer-facing key
delivery channel. Secure key delivery remains a follow-up through email,
dashboard/portal, or a one-time customer handoff page.

## Remaining Work After This Slice

- Real Stripe CLI/webhook integration smoke.
- Secure key delivery through email or portal.
- Customer/subscription lifecycle handling.
- Production transactional persistence.
