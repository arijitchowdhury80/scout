# Scout Founder Decision Record Template

Date: 2026-06-29
Status: Template for launch-gate approvals and rejections

## Purpose

Use this template when Arijit approves, rejects, or defers a launch gate. The
goal is to turn chat decisions into durable evidence that Codex can safely act
on later.

Do not use this template to approve public launch by accident. Public launch
requires every release checklist gate to be closed or formally excepted.

## Decision Record

```markdown
# Scout Founder Decision Record: [short title]

Decision ID: SCOUT-DEC-[YYYYMMDD]-[NN]
Date:
Decision owner: Arijit Chowdhury
Recorded by:
Status: Approved | Rejected | Deferred | Superseded
Related blocker type: founder_decision | risk_decision | external_smoke
Related release gate:
Source prompt / meeting / approval note:

## Approved decision

[Exact decision in one paragraph. Be specific enough for Codex to implement.]

## Rejected alternatives

- [Alternative considered and rejected]
- [Alternative considered and rejected]

## Scope and limits

- Applies to:
- Does not apply to:
- Private beta only? Yes | No
- Public launch allowed by this decision? Yes | No

## Required Codex follow-up

- [ ] Code/doc change:
- [ ] Verification command:
- [ ] Evidence file to update:
- [ ] Release checklist gate to update:

## Expiration or revisit trigger

This decision expires or must be revisited when:

- [date / version / dependency release / pricing change / legal review]

## Evidence links

- Release checklist:
- Decision packet:
- Supporting brief:
- Verification output:
```

## Decision-Specific Notes

### License decision

Use when choosing Apache-2.0, MIT, source-available, private-beta-only license,
or legal review.

Minimum required text:

```text
Approved decision: Scout local/core is licensed as [license].
Scope and limits: This applies to the local package and source distribution.
Hosted/service monetization remains separate.
Required Codex follow-up: add LICENSE, update pyproject license expression,
update README/legal pages, rebuild artifacts, run license release gate.
```

### Crawl4AI/lxml risk decision

Use when accepting, rejecting, or deferring the Crawl4AI/lxml dependency risk.

Minimum required text:

```text
Approved decision: Limited private-beta exception [approved/rejected].
Scope and limits: Public launch remains blocked until dependency audit is clean
or a formal public-launch exception is approved.
Expiration or revisit trigger: next Crawl4AI release, lxml clean audit path, or
before any public launch.
```

### Hosted beta pricing

Use when approving the hosted beta commercial offer.

Minimum required text:

```text
Approved decision: Keep $22 as a finite-credit hosted beta pass.
Scope and limits: No unlimited hosted crawling; public pricing remains blocked.
Required Codex follow-up: keep website/pricing copy finite-credit and keep
readiness public pricing gate open until public pricing is approved.
```

### Artifact-only private beta tag

Use when approving one private-beta GitHub Release artifact tag.

Minimum required text:

```text
Approved decision: Create one artifact-only private-beta v* tag.
Scope and limits: No PyPI, GHCR, Docker Hub, or public launch approval.
Required Codex follow-up: create tag, record workflow URL, download artifacts,
run release artifact smoke.
```

### Docker image publishing policy

Use when approving or deferring GHCR/Docker Hub publishing.

Minimum required text:

```text
Approved decision: Defer GHCR and Docker Hub publishing.
Scope and limits: Docker-from-source remains the private-beta container path.
Required Codex follow-up: keep Docker image publishing gates open.
```

### Stripe real test-mode smoke

Use when Stripe sandbox credentials and webhook setup are ready for verification.

Minimum required text:

```text
Approved decision: Run real Stripe test-mode smoke with supplied sandbox config.
Scope and limits: Test mode only; no public hosted launch approval.
Required Codex follow-up: run checkout helper, complete payment, deliver webhook,
verify hosted key authentication, mask secrets in evidence.
```

## Storage

Completed records should be saved next to this template as:

```text
docs/product/founder-decision-record-[decision-id].md
```

After a record is created, update:

- `docs/product/release-checklist.md`
- `docs/product/public-launch-action-packet-2026-06-29.md`
- `docs/product/launch-decision-dashboard-2026-06-29.md`
- `docs/product/launch-gate-burndown-2026-06-29.md`
