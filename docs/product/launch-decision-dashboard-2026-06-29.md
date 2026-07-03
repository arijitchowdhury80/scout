# Scout Launch Decision Dashboard

Date: 2026-06-29

Status: **Current beta release ready with limits; future public self-serve gates deferred.**

This dashboard is the current control panel for launching Scout as a product.
It summarizes the release checklist, decision briefs, and verification evidence
into one operating view.

Decision request memo:
`docs/product/launch-decision-request-2026-06-29.md`.

Public launch action packet:
`docs/product/public-launch-action-packet-2026-06-29.md`.

Evidence index:
`docs/product/launch-evidence-index-2026-06-29.md`.

## Current Verdict

Scout is ready for the current controlled beta release.

Scout is credible for controlled private beta because it stays within the current
scope:

- local Python package from the verified branch-qualified GitHub install,
- Docker built from source,
- hosted beta API keys for approved testers only,
- no PyPI publish,
- no GHCR or Docker Hub publish,
- no unlimited hosted crawling,
- no certified app UI claim,
- no guaranteed hard-site bypass claim.

Current blockers: 0. Future public self-serve SaaS, PyPI, GHCR, Docker Hub,
paid checkout, and security-clean claims remain out of scope until their gates
are reopened and verified.

## Open Decisions

| Decision | Current recommendation | Required owner | Blocks |
|---|---|---|---|
| Scout license | Approve Apache-2.0 for local/core package | Arijit | PyPI, public repo confidence, broad commercial launch |
| Final license expression | Add final SPDX expression to `pyproject.toml` after approval | Codex after Arijit decision | Package publish |
| `LICENSE` file | Add Apache-2.0 if approved | Codex after Arijit decision | Package publish |
| Public pricing | Current beta metered/invite-only posture approved; self-serve pricing deferred | Arijit | Future paid self-serve hosted launch |
| Registry publishing | Artifact-only beta tags approved; PyPI/GHCR/Docker Hub deferred | Arijit | Future registry publish |
| Docker image publishing | GHCR/Docker Hub deferred; Docker-from-source remains current beta path | Arijit | Future public container image |
| Crawl4AI/lxml risk | Private-beta exception approved; security-clean claims deferred | Arijit/security decision | Future public registry/self-serve launch |

## Open Verification Gates

| Gate | Current state | Closure evidence needed |
|---|---|---|
| GitHub release artifact workflow run against real `v*` tag | Closed on `v0.1.0-beta.1` | `https://github.com/arijitchowdhury80/scout/actions/runs/28415351878` |
| Release artifact downloaded and smoke-tested locally | Closed | `scripts/release_artifact_smoke.py --dist-dir /tmp/scout-release-v0.1.0-beta.1 --serve --port 18424` passed |
| Stripe checkout and webhook tested in Stripe test mode | Deferred out of current beta scope | Configure test keys and rerun before paid self-serve checkout |
| Dependency audit clean and blocking in CI | Deferred under private-beta lxml exception | Reopen before public registry/self-serve launch |
| Published Docker image smoke-tested | Not applicable until image publishing approved | Reopen before GHCR/Docker Hub publish |

## Evidence Already Closed

| Area | Evidence |
|---|---|
| Website exists and copy reviewed | `docs/product/website-copy-review-2026-06-28.md` |
| Competitor website/pricing research exists | `docs/competetor-website-knowledge/` |
| Local install verified | `docs/product/local-install-verification-2026-06-28.md` |
| Docker install verified from docs | `docs/product/docker-install-verification-2026-06-28.md` |
| Hosted API quickstart verified | `docs/product/hosted-api-quickstart-verification-2026-06-28.md` |
| Skill usage verified | `docs/product/skill-usage-verification-2026-06-29.md` |
| Support/onboarding documented | `docs/product/private-beta-onboarding-and-support.md` |
| Hosted economics documented | `docs/product/hosted-economics-and-usage-limits.md`; `docs/product/unit-economics-and-pricing-model-2026-06-29.md` |
| Pricing market refreshed | `docs/competetor-website-knowledge/market-pricing-refresh-2026-06-29.md` |
| Stripe deterministic readiness documented | `docs/product/stripe-test-mode-readiness-2026-06-29.md` |
| Dependency audit blocker refreshed | `docs/security/dependency-audit-refresh-2026-06-29.md` |
| License decision brief written | `docs/legal/scout-license-distribution-decision-brief-2026-06-29.md` |
| Registry publishing policy written | `docs/product/registry-publishing-policy-2026-06-29.md` |

## Recommended Next Order

### 1. Choose license

Recommended decision:

```text
Approve Apache-2.0 for Scout local/core.
Keep hosted/service monetization separate.
```

After approval, Codex should:

- add `LICENSE`,
- add license expression to `pyproject.toml`,
- update README/legal pages,
- rebuild package,
- verify license files ship in wheel/sdist.

### 2. Decide private-beta risk posture for Crawl4AI/lxml

Recommended decision:

```text
Allow limited private beta with the lxml audit blocker documented.
Keep public launch blocked until audit is clean or exception is approved.
```

Do not claim security-clean public launch while `pip-audit` reports
`PYSEC-2026-87` through `lxml 5.4.0`.

### 3. Run Stripe test-mode smoke

Required inputs:

- `STRIPE_SECRET_KEY=sk_test_...`
- `STRIPE_STANDARD_1000_PRICE_ID=price_...`
- `STRIPE_WEBHOOK_SECRET=whsec_...`
- hosted key delivery test config
- non-production recipient email

Expected evidence:

- checkout status ready,
- `scripts/stripe_test_mode_smoke.py --create-checkout` passes readiness and
  Checkout Session creation,
- checkout URL created,
- test payment completed,
- real webhook accepted,
- hosted API key delivered and usable,
- no secrets leaked.

### 4. Approve artifact-only private beta tag

Recommended decision:

```text
Approve one artifact-only private beta tag after license direction is chosen.
No PyPI. No GHCR. No Docker Hub.
```

Expected evidence:

- release workflow passes on `v*` tag,
- GitHub Release artifacts exist,
- downloaded wheel smoke passes locally with
  `scripts/release_artifact_smoke.py --dist-dir ... --serve`.

### 5. Revisit public launch

Do not revisit public launch until:

- license files are complete,
- dependency audit is clean or formally excepted,
- Stripe test-mode smoke is complete,
- release artifacts are smoke-tested from GitHub Release,
- public pricing is approved,
- lawyer-reviewed terms/privacy are ready if hosted public access is offered.

## Decisions Needed From Arijit

See `docs/product/launch-decision-request-2026-06-29.md` for the consolidated
decision memo.

1. Approve Apache-2.0 for Scout local/core, or choose another license path.
2. Approve or reject limited private-beta risk acceptance for the Crawl4AI/lxml blocker.
3. Fill the unit-economics model and approve a pricing structure before restoring checkout or public pricing claims.
4. Approve artifact-only private beta release tags, or keep using branch installs only.
5. Provide Stripe test-mode credentials/webhook setup when ready to close the payment gate.

## Do Not Do Yet

- Do not publish `scout-web` to PyPI.
- Do not push Docker images to GHCR or Docker Hub.
- Do not advertise unlimited hosted crawling.
- Do not advertise the legacy app UI as a launch surface.
- Do not claim public-launch security readiness while dependency audit fails.
- Do not create a public hosted beta without final terms/privacy and usage limits.
