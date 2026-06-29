# Scout Private Beta Launch Plan

Date: 2026-06-29
Status: Controlled private beta plan; public launch remains blocked

## Source Of Truth

Use these files together:

- Release checklist: `docs/product/release-checklist.md`
- Launch evidence index: `docs/product/launch-evidence-index-2026-06-29.md`
- Decision dashboard: `docs/product/launch-decision-dashboard-2026-06-29.md`
- Gate burndown: `docs/product/launch-gate-burndown-2026-06-29.md`
- Decision request: `docs/product/launch-decision-request-2026-06-29.md`

This plan is not a public-launch approval. It defines the bounded private beta
path that can be offered while the remaining launch gates are still open.

## Launch Principle

Do not launch Scout as a "Firecrawl killer." Launch it as an owned acquisition
workbench for teams who need evidence, browser capture, structured records, and
downstream artifacts.

Scout's launch wedge is:

```text
URL or captured page -> evidence ledger -> typed records -> portable artifacts
```

The beta promise is not "scrape anything." The beta promise is "get useful
records when possible, and preserve proof when acquisition is blocked."

## Approved Private-Beta Surfaces

| Surface | Status | Evidence | Boundary |
|---|---|---|---|
| Local branch-qualified install | Verified | `docs/product/local-install-verification-2026-06-28.md` | No PyPI claim until license and registry gates close. |
| Docker built from source | Verified | `docs/product/docker-install-verification-2026-06-28.md` | No GHCR or Docker Hub image until publishing policy is approved. |
| Hosted API for approved testers | Verified quickstart | `docs/product/hosted-api-quickstart-verification-2026-06-28.md` | Approved-testers-only; finite credits; no unlimited hosted crawling. |
| Claude/Codex skill docs | Verified | `docs/product/skill-usage-verification-2026-06-29.md` | Skill usage is documented; not every natural-language prompt/site is certified. |
| Launch website | Verified locally | `docs/product/website-route-render-verification-2026-06-29.md` | Website is a beta launch surface; legacy `/app` UI is not certified. |

## Audience

Primary private-beta audiences:

1. Solutions engineers building search/demo indexes.
2. AI-agent builders who need local web acquisition.
3. Competitive intelligence researchers.
4. RevOps/sales intelligence teams.
5. Internal product/data teams that need repeatable website-to-record workflows.

## Beta Promise

Scout helps testers:

- scrape and crawl public pages,
- capture screenshots and browser evidence where available,
- structure captured HTML,
- extract product records on friendly sites,
- export product records to JSON, JSONL, CSV, SQLite, Google Sheets import
  bundles, and Algolia adapters,
- preserve artifacts and source evidence.

Scout does not yet promise:

- reliable unblock for every hard site,
- perfect vertical intelligence on every domain,
- production hosted scale,
- legal clearance for restricted websites,
- hands-off LinkedIn/job-auto-apply workflows,
- certified legacy `/app` UI.

## Phase Status

### Phase 1: Internal Alpha

Goal: make the product understandable and repeatable.

| Task | Status | Evidence |
|---|---:|---|
| Stabilize current tracked code before beta | Done | Current branch is clean at each pushed checkpoint; launch evidence is linked from `docs/product/launch-evidence-index-2026-06-29.md`. |
| Add feature list and differentiation | Done | `docs/product/feature-list.md`; `docs/product/differentiation.md`. |
| Add legal readiness, third-party notices, and dependency license inventory | Done for beta review | `docs/legal/legal-readiness-checklist.md`; `THIRD_PARTY_NOTICES.md`; `docs/legal/dependency-license-inventory-2026-06-28.md`. |
| Add website with private-beta status and limitations | Done | `docs/product/website-route-render-verification-2026-06-29.md`; `docs/product/website-copy-review-2026-06-28.md`. |
| Add installation and Docker guide | Done | `README.md`; `docs/distribution.md`; `docs/product/local-install-verification-2026-06-28.md`; `docs/product/docker-install-verification-2026-06-28.md`. |
| Add API examples | Done | `README.md`; `docs/distribution.md`; hosted quickstart verification. |
| Add private beta support channel and onboarding guide | Done | `docs/product/private-beta-onboarding-and-support.md`; `docs/product/private-beta-tester-handoff.md`; `docs/product/private-beta-invitation-packet.md`; `.github/ISSUE_TEMPLATE/private_beta_bug.yml`; `.github/ISSUE_TEMPLATE/private_beta_feature.yml`. |
| Add quickstart demo script | Deferred | Current quickstart uses documented CLI/API commands. Add a video/GIF or scripted demo only after the beta flow stabilizes. |

### Phase 2: Controlled Private Beta

Goal: test with 5-10 trusted users under the current limits.

Candidate users:

- 2 solutions engineers,
- 2 AI builders,
- 2 competitive/research users,
- 1-2 RevOps/data users.

Tester entry paths:

1. Local package from the branch-qualified GitHub install.
2. Docker from source.
3. Hosted API key provisioned for an approved tester.
4. Claude/Codex skill instructions for agent-driven usage.

Success criteria:

- user can install and run Scout locally or via Docker,
- user can authenticate to hosted beta if assigned a key,
- user can complete one scrape/crawl/screenshot flow,
- user can complete one product extraction or structuring flow,
- user can find output artifacts,
- user understands blocked evidence,
- user can explain Scout's value back in one sentence,
- user can file feedback with non-sensitive run evidence through the private
  beta issue templates in `.github/ISSUE_TEMPLATE/`.

Support boundaries:

- non-security support uses the private beta issue templates,
- security reports must follow `SECURITY.md`,
- testers must not include API keys, cookies, private customer data, or raw
  secrets in issues,
- beta support is best-effort and not a production SLA.

### Phase 3: Public Developer Preview

Goal: make Scout self-serve for technical users.

This phase is blocked until the release checklist gates close or explicit
exceptions are recorded.

| Task | Status | Blocking Gate |
|---|---:|---|
| Publish package to PyPI | Blocked | License decision, final license expression, registry publishing policy, release artifact smoke. |
| Publish Docker image to GHCR or Docker Hub | Blocked | Docker image publishing policy and published-image smoke. |
| Run GitHub Release workflow against real `v*` tag | Blocked | Artifact-only release tag approval. |
| Smoke downloaded GitHub Release artifacts | Blocked | Requires real approved `v*` release artifacts. |
| Certify public hosted checkout | Blocked | Real Stripe test-mode checkout and webhook smoke. |
| Replace beta legal placeholders | Blocked | Final terms/privacy legal review. |
| Claim clean dependency security posture | Blocked | Crawl4AI/lxml risk decision and clean/blocking dependency audit. |

### Phase 4: Commercial Packaging

Goal: make Scout safe to sell/support.

Open decisions:

- Scout local/core license.
- Public pricing and hosted usage limits.
- Registry publishing policy.
- Docker image publishing policy.
- Crawl4AI/lxml risk posture.
- Final hosted terms/privacy.
- Production hosted operational model beyond controlled beta.

## First Demo Flows

### Demo 1: Page To Markdown

Use `/scrape` on a public about/blog page and show clean markdown, links,
quality score, final URL, provider, and content hash.

### Demo 2: Product Page To Portable Records

Use `/products` on a friendly ecommerce site, inspect records, then export to
JSON, JSONL, CSV, SQLite, Google Sheets import bundle, or Algolia adapter.

### Demo 3: Captured HTML To Records

Use `/structure` with held HTML and a CSS schema to produce typed records
without refetching.

### Demo 4: Browser Evidence / Blocked Evidence

Open a hard page in the browser path, capture evidence, and show whether it was
blocked or usable. If blocked, show `blocked_pages.json` and the extraction
report instead of claiming success.

## Website CTA

Private beta CTA:

> Try Scout locally. Bring one website you currently research or scrape by hand.

Developer CTA:

> Install Scout, run `scout serve`, and turn a URL into records.

## Do Not Claim During Private Beta

- PyPI availability.
- GHCR or Docker Hub image availability.
- Public self-serve hosted signup.
- Unlimited hosted crawling.
- Certified legacy `/app` UI.
- Guaranteed hard-site bypass.
- Security-clean dependency audit.
- Final commercial legal approval.
