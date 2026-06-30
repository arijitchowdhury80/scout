# Scout Founder Decision Record: defer public Docker image publishing

Decision ID: SCOUT-DEC-20260629-04
Date: 2026-06-29
Decision owner: Arijit Chowdhury
Recorded by: Codex
Status: Approved
Related blocker type: founder_decision
Related release gate: Docker image publishing policy
Source prompt / meeting / approval note: Arijit asked Codex to resolve the launch-status blockers one by one and remove blockers from the current Scout beta release path.

## Approved decision

Scout will not publish public Docker images to GHCR or Docker Hub for the current beta release. Docker-from-source remains the approved container distribution path. Published Docker image smoke is therefore not applicable until a future decision approves a registry image.

## Rejected alternatives

- Publishing a public container image before image visibility, provenance, registry ownership, and support expectations are approved.
- Treating Docker Hub as necessary for the first beta when Docker-from-source has already been verified.
- Running a published-image smoke against a locally built image and calling it registry evidence.

## Scope and limits

- Applies to: current private beta Docker distribution and release checklist interpretation.
- Does not apply to: future GHCR or Docker Hub publishing after explicit approval.
- Private beta only? Yes
- Public launch allowed by this decision? No

## Required Codex follow-up

- [x] Code/doc change: Mark public Docker image publishing deferred and published-image smoke not applicable until registry publishing is approved.
- [x] Verification command: scout launch-readiness --blocker-id docker-image-publishing-policy
- [x] Evidence file to update: docs/product/launch-evidence-index-2026-06-29.md
- [x] Release checklist gate to update: Docker image publishing policy

## Expiration or revisit trigger

This decision expires or must be revisited when:

- beta users need a registry image;
- GHCR or Docker Hub publishing is approved;
- Scout enters public developer preview planning.

## Evidence links

- Release checklist: docs/product/release-checklist.md
- Decision packet: docs/product/public-launch-action-packet-2026-06-29.md
- Supporting brief: docs/product/registry-publishing-policy-2026-06-29.md
- Verification output: scout launch-readiness --blocker-id docker-image-publishing-policy
