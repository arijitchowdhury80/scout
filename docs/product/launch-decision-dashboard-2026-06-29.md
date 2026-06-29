# Scout Launch Decision Dashboard

Date: 2026-06-29

Status: **Private beta can continue with limits; public launch is blocked.**

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

Scout is not ready for public launch.

Scout is credible for controlled private beta if it stays within the current
scope:

- local Python package from the verified branch-qualified GitHub install,
- Docker built from source,
- hosted beta API keys for approved testers only,
- no PyPI publish,
- no GHCR or Docker Hub publish,
- no unlimited hosted crawling,
- no certified app UI claim,
- no guaranteed hard-site bypass claim.

Codex-actionable now: 0. Codex owns implementation gates, but the current
public-launch implementation work is intentionally blocked until founder,
risk, publishing, or Stripe setup decisions are approved and recorded.

## Open Decisions

| Decision | Current recommendation | Required owner | Blocks |
|---|---|---|---|
| Scout license | Approve Apache-2.0 for local/core package | Arijit | PyPI, public repo confidence, broad commercial launch |
| Final license expression | Add final SPDX expression to `pyproject.toml` after approval | Codex after Arijit decision | Package publish |
| `LICENSE` file | Add Apache-2.0 if approved | Codex after Arijit decision | Package publish |
| Public pricing | Do not approve `$22`/`$9`; build unit economics and likely test free local plus pay-as-you-go hosted credits | Arijit | Public hosted launch |
| Registry publishing | Private beta tags artifact-only; PyPI first later; GHCR before Docker Hub | Arijit | PyPI/GHCR/Docker Hub publish |
| Docker image publishing | GHCR first, Docker Hub only if needed | Arijit | Public container image |
| Crawl4AI/lxml risk | Public launch blocked unless audit clean or formal exception approved | Arijit/security decision | Public launch |

## Open Verification Gates

| Gate | Current state | Closure evidence needed |
|---|---|---|
| GitHub release artifact workflow run against real `v*` tag | Workflow exists; real tag run not executed/recorded | Push an approved `v*` tag, confirm workflow success, record run URL |
| Release artifact downloaded and smoke-tested locally | Not done because no approved release tag exists; helper exists | Download GitHub Release artifact into clean env, run `scripts/release_artifact_smoke.py --dist-dir ... --serve`, record output |
| Stripe checkout and webhook tested in Stripe test mode | Deterministic tests pass; real Stripe credentials/webhook secret absent; helper exists | Configure test Stripe keys, run `scripts/stripe_test_mode_smoke.py --create-checkout`, complete test payment, deliver real webhook, prove hosted key delivery |
| Dependency audit clean and blocking in CI | Not clean; CI job is visible but non-blocking | Crawl4AI/lxml fixed, or dependency strategy changed, or approved formal exception |
| Published Docker image smoke-tested | Not applicable until image publishing approved; helper exists | Pull published image fresh and run `scripts/docker_image_smoke.py ghcr.io/OWNER/IMAGE:TAG` |

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
- `STRIPE_BETA_PRICE_ID=price_...`
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
