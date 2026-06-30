# Scout Founder Decision Record: Apache-2.0 Local/Core License

Decision ID: SCOUT-DEC-20260629-07
Date: 2026-06-29
Decision owner: Arijit Chowdhury
Recorded by: Codex
Status: Approved
Related blocker type: founder_decision
Related release gate: License decision
Source prompt / meeting / approval note: Arijit approved the recommended release-hardening path with "ok do it" after reviewing the remaining launch blockers.

## Approved Decision

Scout's local/core package and source distribution are licensed under the
Apache License, Version 2.0. Hosted Scout access, paid services, beta admission,
support, and future enterprise terms remain separate commercial/service
arrangements.

## Rejected Alternatives

- MIT was acceptable but not chosen because Apache-2.0 aligns better with
  Crawl4AI and includes explicit patent language.
- Proprietary/source-available-only was not chosen for the local/core package
  because it would add friction for private-beta technical users.
- Public launch was not approved by this license decision.

## Scope And Limits

- Applies to: local Python package, source distribution, CLI, local HTTP
  service, Docker-from-source distribution, and GitHub source artifacts.
- Does not apply to: hosted Scout pricing, SaaS terms, service-level
  agreements, paid support, enterprise agreements, or public registry
  publishing decisions.
- Private beta only? No. The license can support public distribution later.
- Public launch allowed by this decision? No. Other release gates remain open.

## Required Codex Follow-Up

- [x] Code/doc change: add root `LICENSE`.
- [x] Code/doc change: add Apache-2.0 metadata to `pyproject.toml`.
- [x] Code/doc change: update README and release gate docs.
- [x] Verification command: rebuild wheel/sdist and run license release gate.
- [x] Evidence file to update: release checklist after verification.
- [x] Release checklist gate to update: license decision, final license
  expression, and `LICENSE` file.

## Expiration Or Revisit Trigger

Revisit if Scout changes to a dual-license model, a proprietary desktop product,
an enterprise-only package, or legal counsel recommends a different license.

## Evidence Links

- Release checklist: `docs/product/release-checklist.md`
- Decision packet: `docs/product/launch-decision-request-2026-06-29.md`
- Supporting brief: `docs/legal/scout-license-distribution-decision-brief-2026-06-29.md`
- Verification output: `python3 -m build` rebuilt wheel/sdist and
  `python3 scripts/license_release_gate_check.py --expected-license Apache-2.0 --dist-dir dist`
  passed in this release-hardening pass.
