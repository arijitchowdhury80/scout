# Scout Founder Decision Record: Stripe real test-mode smoke

Decision ID: SCOUT-DEC-20260629-06
Date: 2026-06-29
Decision owner: Arijit Chowdhury
Recorded by: Codex
Status: Deferred
Related blocker type: external_smoke
Related release gate: Stripe real test-mode smoke
Source prompt / meeting / approval note: Pending founder review.

## Approved decision

[Replace this paragraph with the exact decision. Suggested next action: Configure Stripe test keys/webhook secret, complete a test checkout, deliver webhook, and verify hosted key access.]

## Rejected alternatives

- [Alternative considered and rejected]

## Scope and limits

- Applies to: [specific launch gate or private-beta scope]
- Does not apply to: public launch unless explicitly approved by a separate full launch gate.
- Private beta only? Yes
- Public launch allowed by this decision? No

## Required Codex follow-up

- [ ] Code/doc change: Configure Stripe test keys/webhook secret, complete a test checkout, deliver webhook, and verify hosted key access.
- [ ] Verification command: scout launch-readiness --blocker-id stripe-real-test-mode-smoke
- [ ] Evidence file to update: docs/product/launch-evidence-index-2026-06-29.md
- [ ] Release checklist gate to update: Stripe real test-mode smoke

## Expiration or revisit trigger

This decision expires or must be revisited when:

- Before public launch, material pricing/legal/security changes, or if the underlying blocker changes.

## Evidence links

- Release checklist: docs/product/release-checklist.md
- Decision packet: docs/product/public-launch-action-packet-2026-06-29.md
- Supporting brief: docs/product/release-checklist.md
- Verification output: scout launch-readiness --blocker-id stripe-real-test-mode-smoke
- Closure evidence expected: Stripe test-mode smoke report with checkout, webhook, hosted key delivery, and /v1/hosted/me verification.
