# Hosted Payment Provisioning PRD

## Summary

Add a Stripe-compatible payment provisioning domain layer for hosted Scout. A
paid checkout event should create one hosted tenant and API key, record the
event durably, and make webhook retry behavior safe.

## Background

Hosted Scout now has plan limits, API keys, admission control, SQLite
persistence, a bearer scrape endpoint, and an operator provisioning CLI. Payment
is still missing. Before adding Stripe webhooks, Scout needs a provider-neutral
core that is easy to test and hard to misuse.

## Objective

- Provision one hosted beta account per paid checkout event.
- Reject unpaid or underpaid events.
- Never persist or reprint raw API keys after first processing.

## Market Segment

Hosted beta users who want an API key after checkout; future signup routes and
operators who need a safe provisioning primitive.

## Solution

### Key Features

- `HostedCheckoutProvisioningRequest` Pydantic input model.
- `HostedCheckoutProvisioningResult` Pydantic output model.
- `HostedPaymentProvisioningService.process_checkout`.
- `SQLiteHostedPaymentStore` with unique provider/session idempotency.
- Fixed beta-pass price validation for `$22.00 USD`.

### Acceptance Criteria

- Paid beta checkout provisions a tenant/key and authenticates through
  `HostedAccountService`.
- Duplicate checkout session returns the existing tenant/key metadata with
  `already_processed=True` and no raw API key.
- Unpaid checkout is rejected before provisioning.
- Wrong amount or currency is rejected before provisioning.
- Raw API keys are not stored in SQLite.

### Technical Approach

Keep Stripe SDK/webhook parsing out of this slice. The future HTTP webhook will
translate Stripe payloads into the domain request.

## Release Plan

V1: pure domain service + SQLite event store + tests.

Later: Stripe webhook route, signature verification, email delivery, dashboard
key display, Customer Portal, Postgres adapter.

## Open Questions

- Should the beta pass remain one-time or become a time-limited subscription?
- Should production use Postgres row transactions for account + event writes?
- How should first-time raw key delivery happen: browser page, email, or portal?

