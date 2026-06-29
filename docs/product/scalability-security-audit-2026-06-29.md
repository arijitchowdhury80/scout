# Scout Scalability And Security Launch Audit

Date: 2026-06-29
Status: Private-beta scale/security audit; public launch remains blocked

## Purpose

This audit answers:

> Can Scout scale and stay secure if launched as a product?

Short answer:

- **Local Scout:** credible for private beta because the user owns compute,
  browser, storage, and artifacts.
- **Hosted Scout:** credible only for controlled private beta with finite
  credits, approved testers, and current limits.
- **Public hosted Scout:** blocked until production storage, distributed
  throttling, async workers, Stripe smoke, final legal, and dependency security
  gates close.

## Current Private-Beta Architecture

```text
Local Scout
  -> CLI / local HTTP / Docker / skill
  -> user workdir
  -> local artifacts
  -> optional user-managed browser and provider keys

Hosted Scout private beta
  -> website checkout/status
  -> Stripe Checkout plumbing
  -> hosted account/key provisioning
  -> Bearer key auth
  -> hosted route admission
  -> finite credits and per-key rate limits
  -> server SCOUT_WORKDIR artifacts
  -> tenant-owned run retrieval
```

## Scale Assessment

| Area | Current private-beta state | Public-launch risk | Required public-launch work |
|---|---|---|---|
| Compute | Synchronous local/hosted route execution works for small beta use | Long crawls/browser runs can tie up workers | Async queue, worker pools, cancellation, timeouts |
| Browser execution | Browser credits exist in policy; browser work is not unlimited | Browser sessions are expensive and abusable | Separate browser worker pool, concurrency controls, browser-minute telemetry |
| Storage | Local workdir and server `SCOUT_WORKDIR` artifacts work for beta | Local filesystem does not scale across instances | Object storage with tenant prefixes, signed URLs, retention jobs |
| Database | SQLite hosted account persistence works for dev/private beta | SQLite/local state is not a multi-instance production store | Postgres or managed SQL with migrations and transactions |
| Rate limiting | Process-local per-key rate limit exists for hosted routes | Multi-instance deployments can bypass process-local counters | Redis/distributed rate limit and abuse controls |
| Credits | Finite standard/browser credits exist | Cost attribution is still coarse for browser/LLM/support | Usage event ledger, per-action telemetry, cost reports |
| Observability | Evidence docs and tests exist; no production dashboards | Failures/cost spikes may be invisible | Metrics, logs, alerts, run duration dashboards, tenant usage dashboards |
| Support | Private beta issue templates exist | Public users need SLA/support workflow | Support queue, escalation, billing support, abuse process |

## Security Assessment

| Risk | Current control | Remaining gap |
|---|---|---|
| API key leakage | Hosted keys are hashed at rest; raw key returned/delivered once | Production secret-management and delivery audit still needed |
| Cross-tenant run access | Hosted run retrieval checks persisted `tenant_id`; other tenants receive `404` | Object-storage IAM and signed URL review before public hosted launch |
| Artifact path traversal | Hosted artifact reads are restricted to known files inside the run output dir | Move from local paths to tenant-scoped object keys |
| SSRF | Hosted scrape/crawl/products/run routes enforce URL safety before crawler work | Deployment egress policy and redirect/retry revalidation proof |
| Abuse and ToS violations | Hosted access is approved-testers-only and finite-credit | Public acceptable-use, suspension, and domain policy |
| Dependency CVE | Audit is visible; Crawl4AI/lxml blocker documented | Public launch blocked until clean audit or approved exception |
| Stripe/webhook security | Deterministic signature/provisioning tests exist | Real Stripe test-mode checkout and webhook smoke still open |
| Secrets in repo | Targeted and entropy-aware secret scans recorded | Maintain blocking secret scan on final release commits |
| User-browser capture | Local-first; not promised as hosted public feature | Separate consent/security review before hosted user-browser capture |

## Product Data Generalization Status

The product-data path is no longer Algolia-only.

Verified local export adapters:

- JSON
- JSONL
- CSV
- SQLite
- Google Sheets import CSV
- Google Sheets import instructions

Algolia remains one supported downstream adapter through preview/push paths.

Still intentionally not shipped:

- direct Google Sheets API push,
- webhook export adapter,
- hosted export jobs,
- public connector marketplace.

Reason: those require user credentials, tenant-scoped storage, quota controls,
and separate security review. The current generic local export path is the
right private-beta boundary.

## Hosted Launch Economics

The previous `$22` hosted beta pass is no longer approved pricing. Hosted
pricing must be derived from the unit-economics model in
`docs/product/unit-economics-and-pricing-model-2026-06-29.md`.

The old finite-credit policy values remain useful as engineering guardrail
examples, not as approved commercial terms:

| Bucket | Private-beta value |
|---|---:|
| Standard credits | 2,000 |
| Browser credits | 100 |
| Artifact retention | 7 days |
| Max pages/records per run | 100 |
| Max concurrent hosted runs | 1 |

Public launch must not offer unlimited hosted crawling. Before broader hosted
launch, Scout needs usage telemetry and cost inputs for:

- standard page cost,
- browser render cost,
- screenshot cost,
- LLM extraction/enrichment cost,
- artifact storage growth,
- failed/retried run cost,
- support cost per tester.

## Launch Verdict

| Launch surface | Verdict | Reason |
|---|---|---|
| Local package private beta | Acceptable with limits | User owns compute/storage; install path verified |
| Docker-from-source private beta | Acceptable with limits | Runtime smoke verified; no published image claim |
| Hosted API private beta | Acceptable with limits | Key auth, finite credits, route safety, and tenant retrieval exist |
| Public hosted API | Blocked | Needs distributed rate limits, object storage, async workers, Stripe smoke, final legal, dependency decision |
| Public registry/image distribution | Blocked | License and publishing policy not approved |

## Required Before Public Hosted Launch

1. Choose and implement final Scout license.
2. Resolve or formally except Crawl4AI/lxml dependency audit blocker.
3. Run real Stripe test-mode checkout and webhook smoke.
4. Replace beta terms/privacy with final hosted legal docs.
5. Move hosted run metadata to production database.
6. Move hosted artifacts to tenant-scoped object storage.
7. Add distributed/global rate limiting.
8. Add async job queue and worker pools.
9. Add observability dashboards for usage, failures, cost, and abuse.
10. Load-test hosted run limits against target concurrency.

## Evidence

- Hosted operating contract: `docs/product/hosted-operating-contract-2026-06-29.md`
- Hosted economics: `docs/product/hosted-economics-and-usage-limits.md`
- Hosted API quickstart: `docs/product/hosted-api-quickstart-verification-2026-06-28.md`
- Hosted artifact authorization: `docs/security/hosted-artifact-authorization-review-2026-06-28.md`
- Hosted SSRF review: `docs/security/hosted-ssrf-review-2026-06-28.md`
- Hosted key delivery review: `docs/security/hosted-key-generation-delivery-review-2026-06-28.md`
- Security audit: `docs/security/security-audit-2026-06-28.md`
- Dependency refresh: `docs/security/dependency-audit-refresh-2026-06-29.md`
- Product export generalization: `docs/product/product-export-generalization-verification-2026-06-29.md`
- Competitor pricing refresh: `docs/competetor-website-knowledge/market-pricing-refresh-2026-06-29.md`
