# Scout Launch Evidence Index

Date: 2026-06-29
Status: Evidence index for controlled private beta review

## Purpose

This page is the fastest way to answer:

> What is actually verified, what is blocked, and where is the proof?

It does not approve public launch. The release checklist remains the source of
truth for launch gates:

- `docs/product/release-checklist.md`
- `docs/product/launch-decision-dashboard-2026-06-29.md`
- `docs/product/launch-gate-burndown-2026-06-29.md`
- `docs/product/launch-decision-request-2026-06-29.md`
- `docs/product/public-launch-action-packet-2026-06-29.md`

Executable readiness check:

```bash
scout launch-readiness
scout launch-readiness --json
scout launch-readiness --require-public
scout launch-readiness --owner Arijit
scout launch-readiness --blocker-type founder_decision
```

GitHub CI runs the repository wrapper, `python3 scripts/launch_readiness_check.py`,
and the JSON form as the private-beta readiness gate. The installed package
exposes the same check as `scout launch-readiness`.

`--require-public` intentionally exits nonzero while public launch blockers are
open.

Use `--owner` or `--blocker-type` to filter the displayed public-launch
blockers without changing the underlying readiness verdict. For example,
`--owner Arijit` shows the founder/risk decisions that Arijit must make, while
`--blocker-type engineering` shows engineering gates that can close after their
prerequisites exist. The readiness report summarizes blockers by both blocker
type and owner so the next bottleneck is visible without opening the JSON.

## Current Verdict

Scout is credible for controlled private beta with limits.

Scout is not public-launch-ready.

Do not claim:

- public registry availability,
- security-clean dependency audit,
- certified legacy `/app` UI,
- unlimited hosted crawling,
- guaranteed hard-site bypass,
- final commercial legal approval.

## Verified Evidence

| Area | Status | Proof | What It Proves | Boundary |
|---|---|---|---|---|
| Launch website | Verified | `docs/product/website-route-render-verification-2026-06-29.md` | `/`, hosted checkout return URLs, `/quickstart`, `/pricing`, `/status`, `/beta`, `/legal`, `/terms`, `/privacy`, `/third-party-notices`, `/styles.css`, and `/health` render locally through the Scout HTTP service; hosted beta limit copy is checked against the code-aligned beta pass limits. | Does not certify the legacy `/app` UI. |
| Website positioning | Verified | `docs/product/website-copy-review-2026-06-28.md`; `docs/competetor-website-knowledge/` | Website copy is grounded in competitor research and avoids unsupported hard-site or unlimited hosted claims. | Public launch copy still depends on final license, pricing, legal, and security decisions. |
| Local install | Verified | `docs/product/local-install-verification-2026-06-28.md` | Branch-qualified GitHub install, `import scout`, `scout --help`, Playwright Chromium install, `scout serve`, `/health`, website routes, `/docs`, and authenticated `/scrape` passed in a clean environment. | This is a branch/private-beta install path, not PyPI. |
| Docker from source | Verified | `docs/product/docker-install-verification-2026-06-28.md` | Documented compose build serves `/health`, website routes, OpenAPI, authenticated `/scrape`, and writable `/data` volume. | Image publishing to GHCR/Docker Hub is not approved. |
| Hosted API quickstart | Verified | `docs/product/hosted-api-quickstart-verification-2026-06-28.md` | Fresh hosted beta key authenticated, `/v1/hosted/me` worked, `/v1/hosted/scrape` returned a successful result and debited credits. | Hosted beta remains approved-testers-only. |
| Hosted operating contract | Documented | `docs/product/hosted-operating-contract-2026-06-29.md` | Local-vs-hosted product boundary, API-key lifecycle, hosted route contract, credit metering, tenant artifact isolation, and production gaps are documented in one place. | This does not approve public self-serve hosted Scout. |
| Scalability and security launch audit | Documented | `docs/product/scalability-security-audit-2026-06-29.md` | Local, Docker, and hosted private-beta scale/security posture is separated from public hosted launch requirements, including queue, object storage, distributed throttling, observability, dependency, and Stripe gates. | Public hosted API remains blocked. |
| Skill usage docs | Verified | `docs/product/skill-usage-verification-2026-06-29.md` | Clean wheel includes `scout/skill/scout.md`; skill-oriented local Scout usage examples were checked against the package. | Skill docs are verified; this does not certify every user prompt or every target site. |
| Product exports | Verified | `docs/product/product-export-generalization-verification-2026-06-29.md` | Product records export to JSON, JSONL, CSV, SQLite, and Google Sheets import bundles; Algolia is an adapter, not the only destination. | Direct Google Sheets API push and webhook export remain future work. |
| Hosted economics | Documented | `docs/product/hosted-economics-and-usage-limits.md`; `docs/competetor-website-knowledge/market-pricing-refresh-2026-06-29.md` | The `$22` beta pass is finite-credit, browser/rendered work is separately metered, unlimited hosted crawling is rejected, and `scout launch-readiness --json` now reports owner, next action, closure evidence, and Codex actionability for every public blocker. | Final public pricing is not approved. |
| Stripe deterministic readiness | Partially verified | `docs/product/stripe-test-mode-readiness-2026-06-29.md`; `scripts/stripe_test_mode_smoke.py` | Deterministic checkout, webhook, provisioning, and key-delivery logic has coverage; helper exists for real test-mode smoke. | Real Stripe test-mode payment and webhook are still open. |
| Release artifact helper | Prepared | `scripts/release_artifact_smoke.py`; `tests/unit/test_release_artifact_smoke.py` | Downloaded GitHub Release artifacts can be smoke-tested once a real approved `v*` tag exists, including installed-server smoke for `/`, `/quickstart`, `/status`, `/styles.css`, and `/health`. | No approved release tag has been run yet. |
| Docker image helper | Prepared | `scripts/docker_image_smoke.py`; `tests/unit/test_docker_image_smoke.py` | A published container image can be pulled and smoked after registry approval. | No published image is approved yet. |
| License implementation | Prepared | `docs/legal/scout-license-distribution-decision-brief-2026-06-29.md`; `docs/legal/license-implementation-runbook-2026-06-29.md`; `scripts/license_release_gate_check.py` | The recommended license path and implementation verification are documented. | No license decision is approved; no final license expression is set. |
| Dependency/security posture | Blocker recorded | `docs/security/dependency-audit-refresh-2026-06-29.md`; `docs/security/crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md` | The Crawl4AI/lxml audit blocker is refreshed, visible, and has a private-beta exception packet ready for decision. | Public launch remains blocked until the audit is clean or formal exception is approved. |
| Beta onboarding/support | Verified | `docs/product/private-beta-onboarding-and-support.md`; `.github/ISSUE_TEMPLATE/private_beta_bug.yml`; `.github/ISSUE_TEMPLATE/private_beta_feature.yml` | Testers have local, Docker, hosted API, and skill onboarding plus feedback/support paths. | Support is best-effort private beta, not production SLA. |

## Open Decision Gates

| Gate | Owner | Required Decision Or Evidence |
|---|---|---|
| Scout license | Arijit | Approve Apache-2.0, MIT, source-available, temporary beta license, or legal review. |
| Final license expression | Codex after approval | Add final `pyproject.toml` expression and verify package artifacts. |
| `LICENSE` file | Codex after approval | Add selected license file and run license release gate helper. |
| Public pricing and hosted usage limits | Arijit | Approve public pricing, or keep only the finite `$22` private-beta pass. |
| Registry publishing policy | Arijit | Approve artifact-only private-beta tag, PyPI, GHCR, Docker Hub, or defer all. |
| Crawl4AI/lxml risk | Arijit/security | Approve limited private-beta exception or block beta expansion until audit is clean. |
| Stripe real test-mode smoke | Arijit plus Codex | Provide Stripe test keys/webhook, complete test payment, verify hosted key delivery. |
| Final hosted terms/privacy | Arijit/legal | Replace beta placeholders before broad hosted access. |

## Suggested Review Order

1. Read `docs/product/launch-decision-request-2026-06-29.md`.
2. Decide Scout local/core license.
3. Decide Crawl4AI/lxml private-beta risk posture.
4. Confirm finite `$22` hosted beta offer or choose a different beta model.
5. Decide whether to approve one artifact-only private-beta release tag.
6. Provide Stripe test-mode setup when payment verification is ready to close.

## Operating Rule

If a claim is not listed here with a proof file, treat it as unverified.
