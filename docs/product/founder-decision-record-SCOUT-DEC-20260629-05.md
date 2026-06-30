# Scout Founder Decision Record: Crawl4AI lxml private-beta exception

Decision ID: SCOUT-DEC-20260629-05
Date: 2026-06-29
Decision owner: Arijit Chowdhury
Recorded by: Codex
Status: Approved
Related blocker type: risk_decision
Related release gate: Crawl4AI/lxml risk decision
Source prompt / meeting / approval note: Arijit asked Codex to resolve the launch-status blockers one by one and remove blockers from the current Scout beta release path.

## Approved decision

A limited private-beta exception is approved for Scout's current Crawl4AI dependency path resolving `lxml 5.4.0` while `PYSEC-2026-87` remains unresolved upstream. This approval is only for controlled private beta with documented limits, visible dependency-audit evidence, no security-clean claim, and no public registry publishing. Public self-serve launch still requires a clean dependency audit, a replacement/forked dependency path, or a separate public-launch security exception.

## Rejected alternatives

- Claiming Scout is security-clean while `pip-audit` reports the lxml advisory.
- Forcing `lxml>=6.1.0` in Scout while current Crawl4AI releases declare incompatible dependency constraints.
- Pausing all private-beta learning while waiting for upstream, as long as beta access remains controlled and honest.

## Scope and limits

- Applies to: controlled private beta, branch-qualified local install, Docker-from-source, and hosted API access for approved testers.
- Does not apply to: public launch, PyPI, GHCR, Docker Hub, unlimited hosted crawling, or security-clean marketing.
- Private beta only? Yes
- Public launch allowed by this decision? No

## Required Codex follow-up

- [x] Code/doc change: Keep dependency audit visible, document the exception, and keep public security-clean claims disallowed.
- [x] Verification command: scout launch-readiness --blocker-id crawl4ai-lxml-risk-decision
- [x] Evidence file to update: docs/product/launch-evidence-index-2026-06-29.md
- [x] Release checklist gate to update: Crawl4AI/lxml risk decision

## Expiration or revisit trigger

This decision expires or must be revisited when:

- Crawl4AI releases a version compatible with fixed `lxml`;
- Scout forks, patches, or replaces the dependency path;
- before any public registry publish;
- before public self-serve hosted launch;
- if exploitability or severity changes.

## Evidence links

- Release checklist: docs/product/release-checklist.md
- Decision packet: docs/security/crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md
- Supporting brief: docs/security/dependency-audit-refresh-2026-06-29.md
- Verification output: scout launch-readiness --blocker-id crawl4ai-lxml-risk-decision
