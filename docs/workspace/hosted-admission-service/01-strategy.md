# Hosted Admission Service Strategy

## Fit

Scout cannot safely launch a hosted API if auth, SSRF checks, scope checks, and
credit debit are scattered across routes. A single admission service keeps that
boundary coherent.

## Target Segment

Hosted Scout API users who want to submit URLs and receive managed acquisition
results. The system job is to decide whether a request should be accepted
before any crawler, browser, worker, or artifact path is touched.

## Trade-Off

We are still not building HTTP routes or a database repository in this slice.
That is deliberate. The admission rule should be tested before we attach it to
network-facing handlers.

## Key Metric

Every hosted URL/action request returns a deterministic allow/deny decision with
the exact reason and no accidental credit mutation on denied paths.

## Defensibility

This is product-specific cost control: Scout understands standard vs browser
credits, URL safety, and acquisition scopes together.
