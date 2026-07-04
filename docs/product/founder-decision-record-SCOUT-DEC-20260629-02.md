# Scout Founder Decision Record: hosted pay-as-you-go pricing and usage limits

Decision ID: SCOUT-DEC-20260629-02
Date: 2026-06-29
Updated: 2026-07-03
Decision owner: Arijit Chowdhury
Recorded by: Codex
Status: Approved
Related blocker type: founder_decision
Related release gate: public pricing and hosted usage limits
Source prompt / meeting / approval note: Arijit asked Codex to move Scout from
arbitrary beta pricing to a self-service, metered, pay-as-you-go hosted model
grounded in unit economics.

## Approved decision

Scout's current hosted pricing model is approved as:

- local Scout remains free;
- hosted Scout is finite-credit and metered from day one;
- beta testers use a $0 card-backed beta trial when Stripe setup mode and
  SMTP delivery are configured;
- beta fallback registration can record name/email requests when Stripe or SMTP
  is not ready;
- public pay-as-you-go hosted packages are:
  - `$10 for 1,000 standard credits`;
  - `$25 for 3,000 standard credits`;
  - `$100 for 15,000 standard credits`;
- browser-heavy work remains separately metered and is not included in the
  first public standard-credit packages.

Estimated loaded cost for 1,000 standard credits is $2.59. Estimated gross margin is 74.1%, and break-even is 17 packs/month against the current $120 monthly fixed-cost assumption. Stripe and SMTP configuration remains a separate operational gate before paid checkout or beta key delivery can pass live.

## Rejected alternatives

- Unlimited hosted crawling for a one-time or low recurring price.
- Restoring arbitrary `$22` one-time or `$9/month` pricing.
- Treating hosted Scout as the primary beta path when local CLI/API/Docker usage is already available.

## Scope and limits

- Applies to: public pricing page, hosted package definitions, beta trial
  limits, pay-as-you-go Stripe package shape, and customer-facing credit
  semantics.
- Does not apply to: enterprise contracts, future subscriptions, future browser
  credit pricing, tax/legal review, or live provider-secret configuration.
- Private beta only? Yes
- Public launch allowed by this decision? No. This approves pricing posture
  only; hosted SaaS launch still requires Stripe and SMTP live verification.

## Required Codex follow-up

- [x] Code/doc change: Keep website pricing copy metered and aligned to the
  approved `$10/$25/$100` pay-as-you-go packages.
- [x] Verification command: scout launch-readiness --blocker-id public-pricing-and-hosted-usage-limits
- [x] Evidence file to update: docs/product/launch-evidence-index-2026-06-29.md
- [x] Release checklist gate to update: public pricing and hosted usage limits

## Expiration or revisit trigger

This decision expires or must be revisited when:

- when beta usage telemetry is available;
- when hosting, LLM, security, storage, support, or payment costs materially change.
- when Stripe fees, tax handling, support model, or browser-worker costs change;
- before adding subscriptions, overages, enterprise contracts, or browser-credit
  public pricing.

## Evidence links

- Release checklist: docs/product/release-checklist.md
- Decision packet: docs/product/public-launch-action-packet-2026-06-29.md
- Supporting brief: docs/product/unit-economics-and-pricing-model-2026-06-29.md
- Verification output: scout launch-readiness --blocker-id public-pricing-and-hosted-usage-limits
