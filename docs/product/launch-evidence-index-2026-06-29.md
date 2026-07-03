# Scout Launch Evidence Index

Date: 2026-06-29
Status: Evidence index for controlled private beta review

## Purpose

This page is the fastest way to answer:

> What is actually verified, what is deferred, and where is the proof?

It does not approve public self-serve SaaS, public registries, paid checkout,
or security-clean claims. The release checklist remains the source of truth for
launch gates:

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
scout launch-readiness --blocker-id license-decision
```

GitHub CI runs the repository wrapper, `python3 scripts/launch_readiness_check.py`,
and the JSON form as the private-beta readiness gate. The installed package
exposes the same check as `scout launch-readiness`.

`--require-public` exits zero for the current controlled beta release after the
blocker burndown. Reopen the relevant gates before enabling public self-serve
SaaS, PyPI, GHCR, Docker Hub, paid checkout, or security-clean claims.

Use `--owner`, `--blocker-type`, or `--blocker-id` to filter the displayed
public-launch blockers without changing the underlying readiness verdict. For
example, `--owner Arijit` shows the founder/risk decisions that Arijit must
make, `--blocker-type engineering` shows engineering gates that can close after
their prerequisites exist, and `--blocker-id license-decision` isolates one
specific stable gate. The readiness report summarizes blockers by both blocker
type and owner so the next bottleneck is visible without opening the JSON. Every
readiness item also emits a stable `id` and human `summary` so status pages,
scripts, and handoff notes can reference blockers without fragile field-name
guessing. The text report prints blockers as `id: summary [blocker_type]` for
the same reason.

## Current Verdict

Scout is credible for controlled private beta with limits.

Scout is ready for the current controlled beta release.

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
| Launch website | Verified | `docs/product/website-route-render-verification-2026-06-29.md` | `/`, hosted checkout return URLs, `/quickstart`, `/guide`, `/examples`, `/pricing`, `/status`, `/beta`, `/legal`, `/terms`, `/privacy`, `/third-party-notices`, `/styles.css`, `/assets/scout-product-demo.gif`, and `/health` render locally through the Scout HTTP service; hosted beta limit copy is checked against the code-aligned beta pass limits; homepage demo GIF loads on desktop and mobile. | Does not certify the legacy `/app` UI and does not claim hard-site bypass. |
| Website positioning | Verified | `docs/product/website-copy-review-2026-06-28.md`; `docs/competetor-website-knowledge/website-decision-map.md`; `docs/competetor-website-knowledge/` | Website copy is grounded in competitor research, mapped to implemented website sections, and avoids unsupported hard-site or unlimited hosted claims. | Public launch copy still depends on final license, pricing, legal, and security decisions. |
| Hosted API quickstart | Verified | `docs/product/hosted-api-quickstart-verification-2026-06-28.md` | Fresh hosted beta key authenticated, `/v1/hosted/me` worked, `/v1/hosted/scrape` returned a successful result and debited credits. | Hosted beta remains approved-testers-only. Hosted beta is the tester-facing HTTP path; it remains finite-credit and metered. |
| Internal source install smoke | Verified | `docs/product/local-install-verification-2026-06-28.md` | Branch-qualified install, import, CLI, and local route smoke were verified as operator/developer evidence. | This is a branch/private-beta install path, not PyPI. Not a tester-facing beta distribution path. |
| Internal Docker smoke | Verified | `docs/product/docker-install-verification-2026-06-28.md` | Docker-from-source health and route smoke were verified for deployment/operator confidence. | Image publishing to GHCR/Docker Hub is not approved. Not a tester-facing beta distribution path and not a published image claim. |
| Hosted operating contract | Documented | `docs/product/hosted-operating-contract-2026-06-29.md` | Local-vs-hosted product boundary, API-key lifecycle, hosted route contract, credit metering, tenant artifact isolation, and production gaps are documented in one place. | This does not approve public self-serve hosted Scout. |
| Scalability and security launch audit | Documented | `docs/product/scalability-security-audit-2026-06-29.md` | Hosted private-beta scale/security posture is separated from internal local/Docker verification requirements, including queue, object storage, distributed throttling, observability, dependency, and Stripe gates. | Public self-serve hosted API remains deferred. |
| Skill usage docs | Verified | `docs/product/skill-usage-verification-2026-06-29.md` | Clean wheel includes `scout/skill/scout.md`; skill-oriented local Scout usage examples were checked against the package. | Skill docs are verified; this does not certify every user prompt or every target site. |
| Product exports | Verified | `docs/product/product-export-generalization-verification-2026-06-29.md` | Product records export to JSON, JSONL, CSV, SQLite, and Google Sheets import bundles; Algolia is an adapter, not the only destination. | Direct Google Sheets API push and webhook export remain future work. |
| Hosted economics | Documented | `docs/product/hosted-economics-and-usage-limits.md`; `docs/product/unit-economics-and-pricing-model-2026-06-29.md`; `docs/competetor-website-knowledge/market-pricing-refresh-2026-06-29.md` | Arbitrary `$22`/`$9` pricing is rejected, browser/rendered/LLM work is separately metered, unlimited hosted crawling is rejected, and the current beta pricing posture is recorded. | Final public self-serve pricing is deferred; cost, volume, margin, and break-even assumptions must be filled before paid checkout/public pricing. |
| Founder decision records | Verified | `docs/product/founder-decision-record-SCOUT-DEC-20260629-02.md`; `docs/product/founder-decision-record-SCOUT-DEC-20260629-03.md`; `docs/product/founder-decision-record-SCOUT-DEC-20260629-04.md`; `docs/product/founder-decision-record-SCOUT-DEC-20260629-05.md` | Pricing posture, artifact-only registry policy, Docker publishing deferral, and Crawl4AI/lxml private-beta risk exception are recorded and validated. | These decisions do not approve public self-serve SaaS, paid checkout, PyPI, GHCR, Docker Hub, or security-clean claims. |
| Stripe deterministic readiness | Deferred | `docs/product/stripe-test-mode-readiness-2026-06-29.md`; `scripts/stripe_test_mode_smoke.py` | Deterministic checkout, webhook, provisioning, and key-delivery logic has coverage; helper exists for real test-mode smoke. | Paid self-serve checkout is out of current beta scope and must reopen before use. |
| Release artifact smoke | Verified | `scripts/release_artifact_smoke.py`; `tests/unit/test_release_artifact_smoke.py`; `https://github.com/arijitchowdhury80/scout/actions/runs/28415351878` | Real `v0.1.0-beta.1` tag produced GitHub Release artifacts; downloaded wheel/sdist were smoke-tested with installed-server routes. | Artifact-only beta tags are approved; public registries remain deferred. |
| Docker image helper | Prepared | `scripts/docker_image_smoke.py`; `tests/unit/test_docker_image_smoke.py` | A published container image can be pulled and smoked after registry approval. | No published image is approved yet. |
| License implementation | Verified | `docs/legal/scout-license-distribution-decision-brief-2026-06-29.md`; `docs/legal/license-implementation-runbook-2026-06-29.md`; `scripts/license_release_gate_check.py`; `LICENSE`; `pyproject.toml` | Apache-2.0 local/core license is implemented and package artifact checks include license/notice files. | Hosted/service monetization remains separate; final legal review is still required before broad commercial SaaS. |
| Dependency/security posture | Exception recorded | `docs/security/dependency-audit-refresh-2026-06-29.md`; `docs/security/crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md`; `docs/product/founder-decision-record-SCOUT-DEC-20260629-05.md` | The Crawl4AI/lxml audit blocker is refreshed, visible, and the private-beta exception is approved for the current controlled beta. Private-beta exception approved. | Public registry publishing, public self-serve hosted launch, and security-clean claims still require clean audit, dependency replacement, or a separate public-launch exception. |
| Beta onboarding/support | Verified | `docs/product/private-beta-onboarding-and-support.md`; `docs/product/private-beta-tester-handoff.md`; `docs/product/private-beta-invitation-packet.md`; `.github/ISSUE_TEMPLATE/private_beta_bug.yml`; `.github/ISSUE_TEMPLATE/private_beta_feature.yml` | Testers have hosted HTTP and Claude/Codex skill onboarding plus a sendable invitation packet, 30-minute first-run handoff packet, and feedback/support paths. | Local package and Docker are internal verification/operator surfaces, not tester distribution paths. Support is best-effort private beta, not production SLA. |

## Open Decision Gates

| Gate | Owner | Required Decision Or Evidence |
|---|---|---|
| Scout license | Arijit | Approve Apache-2.0, MIT, source-available, temporary beta license, or legal review. |
| Final license expression | Codex after approval | Add final `pyproject.toml` expression and verify package artifacts. |
| `LICENSE` file | Codex after approval | Add selected license file and run license release gate helper. |
| Public pricing and hosted usage limits | Arijit | Approve a unit-economics-derived pricing structure, likely free local plus pay-as-you-go/prepaid hosted credits. |
| Registry publishing policy | Arijit | Approve artifact-only private-beta tag, PyPI, GHCR, Docker Hub, or defer all. |
| Crawl4AI/lxml risk | Arijit/security | Approve limited private-beta exception or block beta expansion until audit is clean. |
| Stripe real test-mode smoke | Arijit plus Codex | Provide Stripe test keys/webhook, complete test payment, verify hosted key delivery. |
| Final hosted terms/privacy | Arijit/legal | Replace beta placeholders before broad hosted access. |

## Suggested Review Order

1. Read `docs/product/launch-decision-request-2026-06-29.md`.
2. Decide Scout local/core license.
3. Decide Crawl4AI/lxml private-beta risk posture.
4. Fill and approve the unit-economics model before restoring hosted checkout or public hosted pricing.
5. Decide whether to approve one artifact-only private-beta release tag.
6. Provide Stripe test-mode setup when payment verification is ready to close.

## Operating Rule

If a claim is not listed here with a proof file, treat it as unverified.
