# Hosted Payment Provisioning Strategy

## Does This Fit The Product Vision?

Yes. Hosted Scout needs a safe bridge between payment and API-key access. The
product promise is still local-first Scout with an optional hosted API. This
module enables the optional hosted path without making payment code leak into
the crawler, scraper, or intelligence modules.

## Target Segment

Early hosted beta users who want a hosted Scout endpoint immediately after
payment, without running local infrastructure.

## Trade-Off

We are choosing not to build a full dashboard or Stripe webhook route yet. The
domain contract comes first so webhook retries, manual beta provisioning, and
future checkout events all share the same idempotent account-provisioning core.

## Key Metric

A paid checkout event provisions exactly one tenant/key pair, can be retried
without duplicating access, and never persists the raw API key.

## Defensibility

This is not a defensibility feature by itself. It makes Scout commercially
operable by enforcing the product's security and usage economics boundary.

