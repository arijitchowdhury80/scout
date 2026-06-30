# Scout Founder Decision Record: artifact-only beta publishing

Decision ID: SCOUT-DEC-20260629-03
Date: 2026-06-29
Decision owner: Arijit Chowdhury
Recorded by: Codex
Status: Approved
Related blocker type: founder_decision
Related release gate: registry publishing policy
Source prompt / meeting / approval note: Arijit asked Codex to resolve the launch-status blockers one by one and remove blockers from the current Scout beta release path.

## Approved decision

Scout may create artifact-only private-beta `v*` GitHub Release tags that build and attach wheel/sdist artifacts. Scout must not publish to PyPI, GHCR, Docker Hub, or any broad public registry in this beta release. Branch-qualified GitHub install, GitHub Release artifacts, Docker-from-source, and hosted beta keys are the approved distribution paths.

## Rejected alternatives

- Publishing Scout to PyPI before the dependency audit and public-launch gates are closed.
- Publishing Docker images to GHCR or Docker Hub before image visibility, provenance, and post-publish support are approved.
- Treating a GitHub Release artifact tag as public launch approval.

## Scope and limits

- Applies to: one or more private-beta GitHub Release artifact tags and release-artifact smoke tests.
- Does not apply to: PyPI publish, GHCR publish, Docker Hub publish, public launch, or public self-serve hosted signup.
- Private beta only? Yes
- Public launch allowed by this decision? No

## Required Codex follow-up

- [x] Code/doc change: Keep release workflow artifact-only and document no public registry publishing.
- [x] Verification command: scout launch-readiness --blocker-id registry-publishing-policy
- [x] Evidence file to update: docs/product/launch-evidence-index-2026-06-29.md
- [x] Release checklist gate to update: registry publishing policy

## Expiration or revisit trigger

This decision expires or must be revisited when:

- Scout is ready for a public developer preview;
- PyPI, GHCR, Docker Hub, or another registry becomes the desired distribution path;
- the dependency/security/legal gates materially change.

## Evidence links

- Release checklist: docs/product/release-checklist.md
- Decision packet: docs/product/public-launch-action-packet-2026-06-29.md
- Supporting brief: docs/product/registry-publishing-policy-2026-06-29.md
- Verification output: scout launch-readiness --blocker-id registry-publishing-policy
