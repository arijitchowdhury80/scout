# Crawl4AI/lxml Risk Decision

Date: 2026-06-28
Status: Decision required

## Context

Scout depends on Crawl4AI for core acquisition. The current installable
Crawl4AI release line resolves `lxml 5.4.0`, and the dependency audit reports
`PYSEC-2026-87`. The fixed lxml version is `lxml 6.1.0`.

Refresh on 2026-06-29:

- `crawl4ai 0.9.0` is available.
- `lxml 6.1.1` is available.
- A fresh Scout install with eager upgrades still resolves `crawl4ai 0.9.0`
  with `lxml 5.4.0`.
- Installing `crawl4ai==0.9.0` with `lxml>=6.1.0` still fails dependency
  resolution.
- Evidence: `docs/security/dependency-audit-refresh-2026-06-29.md`.

Attempted mitigation:

- Adding `lxml>=6.1.0` directly to Scout was tested.
- The package became uninstallable because current Crawl4AI releases require
  `lxml~=5.3`.
- Therefore Scout cannot force the fixed lxml version without changing the
  Crawl4AI dependency strategy.

## Product Impact

Private beta and Public launch should be treated differently:

- Private beta may proceed only with explicit maintainer acceptance, limited
  users, clear beta language, no clean-audit claim, and CI visibility.
- Public launch remains blocked until the dependency audit is clean or a formal
  security exception is approved with compensating controls.

## Options

### Option A: Private beta risk acceptance only

Allow a limited private beta while keeping public launch blocked.

Conditions:

- no public registry publish,
- no clean security claim,
- hosted access limited to approved testers,
- dependency audit remains visible in CI,
- release checklist continues to show the blocker,
- retest Crawl4AI releases before every beta expansion.

Pros:

- keeps beta learning moving,
- avoids destabilizing the core acquisition layer,
- honestly communicates risk.

Cons:

- known CVE remains in the dependency tree,
- not acceptable for public launch,
- requires disciplined beta limits.

### Option B: Wait for Crawl4AI upstream

Do not expand beta or publish until Crawl4AI supports `lxml 6.1.0` or later.

Pros:

- cleanest dependency story,
- least maintenance burden,
- avoids fork/vendor complexity.

Cons:

- timeline depends on upstream,
- may slow all launch learning.

### Option C: Fork, patch, vendor, or replace dependency path

Patch the Crawl4AI dependency strategy or replace the lxml-dependent path.

Pros:

- can unblock public launch sooner,
- puts the fix under Scout control.

Cons:

- increases maintenance load,
- risks diverging from Crawl4AI,
- requires deeper compatibility testing of acquisition behavior.

## Recommended decision

Recommended decision for the next milestone:

- approve Option A for limited private beta only,
- keep Public launch blocked,
- keep CI `dependency-audit` non-blocking but visible,
- add a scheduled/manual check for new Crawl4AI releases,
- revisit Option B or Option C before public launch, package registry publish,
  or broader hosted API access.

This document is not an approval. It is the decision record that Arijit must
approve or revise before private beta expansion.

## Required Approval

- [ ] Maintainer explicitly approves private beta risk acceptance.
- [ ] Beta limits documented.
- [ ] Public launch remains blocked in `docs/product/release-checklist.md`.
- [ ] Dependency audit converted to blocking before public launch or a formal
      exception is approved.
