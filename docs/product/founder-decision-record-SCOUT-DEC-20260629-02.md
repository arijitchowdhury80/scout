# Scout Founder Decision Record: hosted beta pricing and usage limits

Decision ID: SCOUT-DEC-20260629-02
Date: 2026-06-29
Decision owner: Arijit Chowdhury
Recorded by: Codex
Status: Approved
Related blocker type: founder_decision
Related release gate: public pricing and hosted usage limits
Source prompt / meeting / approval note: Arijit asked Codex to resolve the launch-status blockers one by one and remove blockers from the current Scout beta release path.

## Approved decision

Scout's current beta pricing posture is approved as: local Scout is free, hosted Scout remains invite-only and metered, hosted usage uses finite credits and hard caps, and arbitrary `$22` one-time or `$9/month` prices are rejected. Public self-serve paid pricing is not approved yet; it must wait for unit-economics inputs, usage telemetry, Stripe smoke, and final hosted terms.

## Rejected alternatives

- Unlimited hosted crawling for a one-time or low recurring price.
- Showing arbitrary public prices before cost, volume, margin, and break-even assumptions are filled in.
- Treating hosted Scout as the primary beta path when local CLI/API/Docker usage is already available.

## Scope and limits

- Applies to: controlled private beta, website pricing posture, hosted beta usage limits, and manual/invite-only hosted API keys.
- Does not apply to: public self-serve checkout, public hosted launch, final commercial pricing, or enterprise contracts.
- Private beta only? Yes
- Public launch allowed by this decision? No

## Required Codex follow-up

- [x] Code/doc change: Keep website pricing copy metered and invite-only; do not restore arbitrary public prices.
- [x] Verification command: scout launch-readiness --blocker-id public-pricing-and-hosted-usage-limits
- [x] Evidence file to update: docs/product/launch-evidence-index-2026-06-29.md
- [x] Release checklist gate to update: public pricing and hosted usage limits

## Expiration or revisit trigger

This decision expires or must be revisited when:

- before public self-serve hosted launch;
- before enabling paid checkout;
- when beta usage telemetry is available;
- when hosting, LLM, security, storage, support, or payment costs materially change.

## Evidence links

- Release checklist: docs/product/release-checklist.md
- Decision packet: docs/product/public-launch-action-packet-2026-06-29.md
- Supporting brief: docs/product/unit-economics-and-pricing-model-2026-06-29.md
- Verification output: scout launch-readiness --blocker-id public-pricing-and-hosted-usage-limits
