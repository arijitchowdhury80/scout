# Production Readiness And Distribution

Date: 2026-06-28
Status: Launch planning baseline

## Core Decision

Scout should launch **local-first** with an **optional hosted API**, not as a
hosted-only crawler SaaS.

Why:

- Scout's strongest value is owned acquisition, evidence, artifacts, and
  workflow control.
- Hosted scraping/browser execution has real variable cost and operational risk.
- One-time unlimited hosted access would be economically unsafe.
- Local distribution allows users to bring their own machine, browser session,
  proxy, keys, and storage.

## Distribution Model

### Local Free

Primary path for beta:

```bash
pipx install scout-web
scout serve
```

Alternative:

```bash
pip install scout-web
python -m scout.cli serve
```

Docker path:

```bash
docker run -p 8421:8421 -v "$PWD/scout-runs:/runs" scout:latest
```

Local requirements:

- Python package or Docker image.
- Optional Playwright/browser dependencies for browser capture.
- Optional API keys for LLMs/search providers/Algolia.
- User-selected workdir for artifacts.

### Hosted Paid

Hosted Scout should be positioned as convenience:

- no local install,
- API key generated on the website,
- limited monthly credits,
- hosted artifact retention,
- clear rate limits,
- paid upgrade for more usage.

Hosted architecture:

```text
Website / Dashboard
  -> Auth + Stripe customer
  -> API key service
  -> Quota/rate-limit middleware
  -> Job queue
  -> Worker pool
  -> Browser worker pool for expensive sessions
  -> Object storage for artifacts
  -> Postgres for users/runs/keys/usage
  -> Observability + audit logs
```

## Multi-Tenancy Requirements

Before hosted launch, Scout needs:

- user accounts,
- hashed API keys,
- per-user quotas,
- per-key scopes,
- request logging without secrets,
- run ownership isolation,
- artifact path isolation,
- object storage with tenant prefixes,
- retention policy,
- cancellation and timeout controls,
- abuse prevention,
- robots/ToS policy,
- proxy/browser cost controls.

## Security Risks

### SSRF

Hosted Scout accepts URLs. This creates server-side request forgery risk.

Controls:

- block private IP ranges,
- block link-local/cloud metadata endpoints,
- DNS rebinding defense,
- URL scheme allowlist,
- redirect validation,
- max response size,
- network egress policy.

### Secret Leakage

Controls:

- never log API keys,
- never return secrets in preview payloads,
- session-only credential fields where possible,
- `.env.local` ignored,
- explicit third-party key handling docs.

### User Browser Capture

User-browser/CDP capture is powerful and sensitive.

Controls:

- explicit consent,
- local-only by default,
- clear warning that Scout can inspect the active tab,
- no hosted CDP capture without stronger security review,
- redact cookies/headers from artifacts unless explicitly enabled.

### Hosted Browser Abuse

Browser automation can be abused for credential stuffing, scraping restricted
sites, or evading controls.

Controls:

- terms of use,
- domain allow/deny policy,
- rate limits,
- per-run timeouts,
- CAPTCHA and auth boundary rules,
- user/account suspension path.

## Scale Risks

### Variable Cost

Costs scale with:

- page fetches,
- browser minutes,
- proxies,
- screenshots,
- storage,
- LLM extraction,
- queue retries,
- support.

Implication:

Hosted Scout cannot be unlimited for a one-time fee. Even if local is free,
hosted must meter usage.

### Long-Running Jobs

Hosted runs should be asynchronous:

- create run,
- return run ID,
- poll/SSE events,
- retrieve artifacts,
- time out safely.

### Storage

Artifacts can grow quickly. Hosted retention should start conservative:

- free/local: user owns disk;
- hosted starter: 7-day retention;
- paid/pro: 30-day retention;
- enterprise: configurable.

## Product Data Generalization

Current Algolia product flow should become:

```text
Product extraction
  -> canonical product records
  -> export adapters
       - Algolia records
       - JSON/JSONL
       - CSV
       - SQLite
       - Google Sheets
       - webhook
```

Algolia should be an adapter, not the core product model.

Implementation status:

- Local JSON export: implemented.
- Local JSONL export: implemented.
- Local CSV export: implemented.
- Local SQLite export: implemented.
- CLI export command: implemented as `scout product-export`.
- Algolia adapter: existing preview/push path.
- Google Sheets adapter: deferred; requires credential and OAuth/service-account
  design.
- Hosted export jobs: deferred; requires tenant, storage, and quota model.

Recommended generic product schema fields:

- `objectID`
- `name`
- `brand`
- `category`
- `url`
- `image`
- `price`
- `currency`
- `sku`
- `description`
- `variants`
- `availability`
- `rating`
- `review_count`
- `source_url`
- `citations`
- `extraction_confidence`

## Production Readiness Gaps

Before paid hosted beta:

- [ ] tenant model,
- [x] initial API key lifecycle primitives,
- [ ] persisted API key lifecycle,
- [ ] quota/rate-limit middleware,
- [x] initial plan and credit policy model,
- [ ] persisted usage metering,
- [ ] Stripe checkout/webhook integration,
- [ ] async job queue,
- [ ] object storage,
- [x] initial SSRF URL safety primitives,
- [ ] hosted SSRF middleware enforcement,
- [ ] hosted browser cost controls,
- [ ] privacy/terms/acceptable-use docs,
- [ ] dependency/license notices,
- [ ] operational dashboards.

Before local public beta:

- [ ] package publishing decision/name,
- [ ] tested install path on fresh Mac/Linux,
- [ ] Docker image publish,
- [ ] quickstart docs,
- [ ] artifact folder docs,
- [ ] local browser dependency docs,
- [ ] legal attribution/third-party notices,
- [ ] examples that match certified features.
