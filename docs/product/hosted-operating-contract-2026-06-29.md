# Hosted Scout Operating Contract

Date: 2026-06-29
Status: Private-beta hosted operating contract; public hosted launch remains blocked

## Purpose

This document answers the production-readiness question:

> If someone does not run Scout locally, how does hosted Scout work and what is
> actually safe to promise today?

It is a private-beta contract, not a public SaaS launch approval.

## Product Boundary

Scout has two operating modes:

| Mode | Primary user | Cost posture | Data/artifact posture | Launch status |
|---|---|---|---|---|
| Local Scout | Builders who want ownership and low marginal cost | Free beta; user brings compute/browser/storage | Artifacts stay in the user's selected workdir | Primary private-beta path |
| Hosted Scout | Approved testers who want managed API convenience | Paid finite credits; no unlimited usage | Server writes tenant-owned run artifacts with limited retention | Limited private beta only |

Hosted Scout should be described as managed convenience, not the main value
wedge. The strongest Scout promise remains owned acquisition plus evidence:

```text
URL or captured page -> source evidence -> typed records -> portable artifacts
```

## Hosted Beta Lifecycle

### 1. Provision

Private-beta operators can provision a hosted account with:

```bash
scout hosted-provision --email tester@example.com --db hosted.sqlite
```

The command returns the raw hosted API key exactly once. The persistence layer
stores the API key hash, not the raw key.

Stripe flow status:

- deterministic checkout, signed webhook, idempotent provisioning, and key
  delivery coverage exists;
- real Stripe test-mode payment and webhook smoke remain open.

### 2. Authenticate

Hosted API requests use:

```http
Authorization: Bearer scout_live_...
```

The current hosted read/write scope is `runs:create`. The API authenticates by
hashed key, checks account status, and returns non-secret account data through:

```http
GET /v1/hosted/me
```

### 3. Admit Work

Hosted routes enforce URL safety, per-key rate limits, plan limits, and credit
preflight before work is accepted.

Current hosted routes:

| Route | Purpose | Current billing unit |
|---|---|---|
| `POST /v1/hosted/scrape` | Fetch one URL | 1 standard credit |
| `POST /v1/hosted/crawl` | Crawl up to plan page limit | 1 standard credit per returned page |
| `POST /v1/hosted/products` | Extract product records | 1 standard credit per returned product record |
| `POST /v1/hosted/run/{use_case}` | Run high-level workflow | 1 standard credit per returned record |
| `GET /v1/hosted/runs` | List tenant-owned runs | no run credit charge |
| `GET /v1/hosted/runs/{run_id}` | Read tenant-owned run summary | no run credit charge |
| `GET /v1/hosted/runs/{run_id}/records` | Read tenant-owned records | no run credit charge |
| `GET /v1/hosted/runs/{run_id}/artifacts` | Read artifact metadata and private download URLs | no run credit charge |

### 4. Meter Usage

Current private-beta plan defaults:

| Plan | Standard credits | Browser credits | Retention | Max pages/records | Concurrency |
|---|---:|---:|---:|---:|---:|
| `hosted_beta_pass` | 2,000 | 100 | 7 days | 100 | 1 |
| `hosted_starter` | 5,000 | 250 | 14 days | 250 | 2 |
| `hosted_pro` | 25,000 | 1,500 | 30 days | 1,000 | 5 |

Current action costs:

| Action | Bucket | Cost |
|---|---|---:|
| scrape | standard | 1 |
| crawl page | standard | 1 |
| screenshot | standard | 3 |
| browser render | browser | 5 |
| browser minute | browser | 10 |

The `$22` hosted beta pass maps only to finite private-beta credits. It must
not be marketed as unlimited hosted crawling, lifetime API usage, or public
self-serve scale.

### 5. Store And Retrieve Artifacts

Hosted high-level runs ignore caller-provided `output_dir` and write under the
server `SCOUT_WORKDIR`.

Run ownership is persisted with non-secret `tenant_id` and `key_id` metadata.
Hosted retrieval is authorized from persisted tenant ownership, not from local
path names.

Artifact download behavior:

- only known artifact names can be downloaded;
- artifact files must resolve inside the persisted run output directory;
- another tenant receives `404`, not cross-tenant existence information;
- raw hosted API keys are not echoed in run, records, artifacts, or download
  responses.

## Current Security Controls

Implemented or reviewed for private beta:

- hashed API key persistence;
- per-key scopes;
- hosted account status checks;
- finite credits and per-action debit;
- process-local per-key rate limiting;
- SSRF URL safety primitives and hosted route admission checks;
- tenant-owned run listing and retrieval;
- artifact path confinement;
- private artifact download URLs that still require Bearer auth;
- non-secret `/v1/hosted/me` account/limit/balance response;
- deterministic Stripe/webhook/key-delivery coverage.

## Production Gaps

Hosted Scout is **not** a broad public SaaS yet.

Required before public hosted launch:

- distributed/global rate limiting;
- production database such as Postgres instead of SQLite/local process state;
- async job queue and worker pool;
- object storage with tenant-scoped keys and signed URLs;
- automated artifact retention/deletion;
- production observability dashboards and alerts;
- abuse detection and suspension workflow;
- real Stripe test-mode checkout and webhook smoke;
- final hosted terms/privacy;
- Crawl4AI/lxml launch-risk decision or clean dependency audit;
- load testing against target hosted concurrency and run durations.

## Website Copy Boundary

Allowed:

```text
Hosted Scout is a limited private-beta convenience API with finite credits.
Local Scout remains the primary free path.
```

Not allowed:

```text
Public self-serve hosted Scout.
Unlimited hosted crawling.
Production-ready multi-tenant SaaS.
Guaranteed hard-site bypass.
```

## Evidence Links

- Hosted economics: `docs/product/hosted-economics-and-usage-limits.md`
- Hosted API quickstart: `docs/product/hosted-api-quickstart-verification-2026-06-28.md`
- Stripe readiness: `docs/product/stripe-test-mode-readiness-2026-06-29.md`
- Hosted artifact authorization: `docs/security/hosted-artifact-authorization-review-2026-06-28.md`
- Hosted SSRF review: `docs/security/hosted-ssrf-review-2026-06-28.md`
- Hosted key delivery review: `docs/security/hosted-key-generation-delivery-review-2026-06-28.md`
- Production readiness planning: `docs/competetor-website-knowledge/production-readiness-and-distribution.md`
