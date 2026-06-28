# Hosted Scout Security And Scale Audit

Date: 2026-06-28

## Launch-Blocking Security Risks

### SSRF

Hosted Scout accepts URLs. Without protection, users could request:

- localhost,
- private network addresses,
- cloud metadata endpoints,
- internal admin services.

Required controls:

- scheme allowlist: `http`, `https`,
- block private, loopback, link-local, multicast, reserved IP ranges,
- validate every redirect target,
- DNS rebinding protections,
- egress network policy,
- response size limits.

Implementation seed:

- deterministic URL safety checks now exist in `scout.core.platform.url_safety`;
- the guard rejects unsafe schemes, missing hostnames, URL credentials,
  localhost, unsafe IP literals, unsafe resolved IPs, and unsafe redirect hops;
- hosted scrape, crawl, products, and high-level run endpoints now enforce
  admission-layer URL safety before crawler invocation or credit debit;
- high-level runs validate URL-like values in `url`, `targets`, and `job_urls`;
- public hosted launch still needs deployment egress policy and proof that every
  crawler redirect/retry path is revalidated.

### Secret Exposure

Current local app exposes the configured API key through `/api/config` to make
the local browser UI easy. This cannot ship in hosted mode.

Required controls:

- no API-key echo,
- hashed API keys,
- redacted logs,
- secret scanning in artifacts,
- separate local and hosted auth middleware.

### Browser Abuse

Hosted browser automation is expensive and abusable.

Required controls:

- browser-session quotas,
- max run duration,
- per-tenant concurrency limits,
- domain denylist/allowlist policy,
- acceptable-use policy,
- abuse monitoring.

### User Browser Capture

User-browser capture should remain local-first until a separate security review.
Hosted Scout should not connect to a user's browser session.

## Scale Risks

### Unlimited One-Time Plan

Unsafe. A $22 unlimited hosted plan can be destroyed by a small number of high
usage customers.

Required controls:

- finite credits,
- monthly subscriptions for ongoing use,
- hard run/page/browser-minute limits.

### Artifact Storage

Artifacts can grow quickly with screenshots and DOM captures.

Recommended:

- hosted beta: 7-day retention,
- paid starter: 14-day retention,
- paid pro: 30-day retention,
- local: user controls retention.

### Queue Saturation

Hosted runs should go through a queue with separate worker pools:

- standard fetch workers,
- crawl workers,
- browser workers,
- LLM extraction workers.

Browser workers need the strictest concurrency limits.

## Current Code Gap

Current Scout has:

- local static API-key middleware,
- in-memory app run registry,
- local artifact writing,
- no tenant model,
- no quota model,
- no hosted API-key lifecycle,
- no Stripe integration,
- SSRF admission controls exist for hosted HTTP endpoints, but deployment-level
  egress policy and crawler redirect/retry enforcement remain open,
- no hosted object storage abstraction.

This is fine for local beta. It is not yet production-hosted SaaS.
