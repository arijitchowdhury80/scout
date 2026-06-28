# Hosted Account Service Strategy

## 1. Fit To Product Vision

Scout's hosted offering should be optional convenience, not the core product
identity. A hosted account service fits because it provides the minimum safe
commercial foundation: tenants, API keys, scopes, and finite usage credits.

## 2. Target Segment

Developers and teams who want Scout's acquisition API without running local
infrastructure for every job. Their job is: "get an API key and run limited,
metered acquisition jobs safely."

## 3. Trade-Off

We are not building a public dashboard, Stripe integration, or hosted worker
fleet in this slice. We are choosing the smaller domain layer first so payment
and API routes do not invent their own auth and credit logic.

## 4. Key Metric

Every hosted request can be admitted or rejected using a deterministic decision:
tenant, key status, scope, plan, credit bucket, and remaining credits.

## 5. Defensibility

The defensibility is not API-key CRUD. It is Scout-specific metering that
understands acquisition cost buckets: standard page credits vs browser/session
credits.
