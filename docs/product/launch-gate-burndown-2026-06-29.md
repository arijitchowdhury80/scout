# Scout Launch Gate Burndown

Date: 2026-06-29
Status: Private beta can continue; public launch remains blocked

## Purpose

This is the execution view of the launch checklist. The release checklist is
the source of truth for gates; this page turns those gates into owners,
blocker types, and next actions.

Consolidated decision request:
`docs/product/launch-decision-request-2026-06-29.md`.

Public launch action packet:
`docs/product/public-launch-action-packet-2026-06-29.md`.

Launch evidence index:
`docs/product/launch-evidence-index-2026-06-29.md`.

## Current Verdict

Scout is not public-launch-ready.

Scout is viable for controlled private beta only if it stays inside these
boundaries:

- local install from the verified GitHub branch,
- Docker built from source,
- hosted API keys for approved testers,
- no PyPI publish,
- no GHCR or Docker Hub publish,
- no unlimited hosted crawling,
- no certified legacy `/app` UI claim,
- no security-clean claim while the dependency audit is failing.

## Gate Burndown

| Gate | Status | Blocker type | Owner | Next action | Evidence |
|---|---:|---|---|---|---|
| Launch website routes/render | Closed | None | Codex | Keep website tests in CI; do not call `/app` certified | `docs/product/website-route-render-verification-2026-06-29.md` |
| Local install path | Closed | None | Codex | Keep branch-qualified quickstart until package registry gates close | `docs/product/local-install-verification-2026-06-28.md` |
| Docker-from-source path | Closed | None | Codex | Keep source-build Docker docs; do not publish image yet | `docs/product/docker-install-verification-2026-06-28.md` |
| Hosted API quickstart | Closed | None | Codex | Keep hosted beta limited to approved testers | `docs/product/hosted-api-quickstart-verification-2026-06-28.md` |
| Product export beyond Algolia | Closed | None | Codex | Treat Algolia as one adapter, not the product's only output | `docs/product/product-export-generalization-verification-2026-06-29.md` |
| License decision | Open | Arijit decision | Arijit | Approve Apache-2.0, MIT, source-available, beta license, or legal review | `docs/legal/scout-license-distribution-decision-brief-2026-06-29.md` |
| Final license expression | Open | Depends on license decision | Codex | After approval, update `pyproject.toml`, rebuild artifacts, and run `scripts/license_release_gate_check.py` | `docs/legal/license-implementation-runbook-2026-06-29.md` |
| `LICENSE` file | Open | Depends on license decision | Codex | After approval, add the selected license file and run the license gate helper | `docs/legal/license-implementation-runbook-2026-06-29.md` |
| Public pricing and hosted usage limits | Open | Arijit decision | Arijit | Approve finite hosted beta pricing or choose subscription/credit model | `docs/product/hosted-economics-and-usage-limits.md` |
| Registry publishing policy | Open | Arijit decision | Arijit | Approve artifact-only beta tag policy or keep branch installs only | `docs/product/registry-publishing-policy-2026-06-29.md` |
| GitHub release workflow on real `v*` tag | Open | Depends on registry/tag approval | Codex | After approval, create one private-beta tag and record workflow URL | `docs/product/registry-publishing-policy-2026-06-29.md` |
| Release artifact download smoke | Open | Depends on `v*` release artifact | Codex | Download wheel/sdist from GitHub Release and run `scripts/release_artifact_smoke.py --dist-dir ... --serve` | `docs/product/registry-publishing-policy-2026-06-29.md` |
| Docker image publishing policy | Open | Arijit decision | Arijit | Approve GHCR-first policy or defer public image publishing | `docs/product/registry-publishing-policy-2026-06-29.md` |
| Published Docker image smoke | Open | Depends on image publishing approval | Codex | Pull published image fresh and run `scripts/docker_image_smoke.py ghcr.io/OWNER/IMAGE:TAG` | `docs/product/registry-publishing-policy-2026-06-29.md` |
| Crawl4AI/lxml risk decision | Open | Security/business risk decision | Arijit | Approve limited private-beta exception or require clean audit first | `docs/security/crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md` |
| Dependency audit clean and blocking in CI | Open | Upstream/dependency strategy | Codex plus upstream | Wait for Crawl4AI compatible with `lxml>=6.1.0`, replace/fork dependency path, or formal exception | `docs/security/dependency-audit-refresh-2026-06-29.md` |
| Stripe real test-mode smoke | Open | External credentials/webhook | Arijit plus Codex | Provide test Stripe keys/webhook setup; run `scripts/stripe_test_mode_smoke.py --create-checkout`, complete payment, deliver webhook | `docs/product/stripe-test-mode-readiness-2026-06-29.md` |
| Final hosted terms/privacy | Open | Legal/commercial review | Arijit/legal | Replace beta placeholders before broad commercial hosted access | `docs/legal/beta-terms-placeholder.md`, `docs/legal/beta-privacy-placeholder.md` |

## Codex-Executable Work Remaining

These can be done immediately after the named dependency is satisfied:

1. **After license approval**
   - add `LICENSE`,
   - update `pyproject.toml`,
   - update README/legal website copy,
   - rebuild wheel/sdist,
   - verify license files and third-party notices ship in artifacts.

2. **After artifact-only release tag approval**
   - create one private-beta `v*` tag,
   - wait for GitHub release artifact workflow,
   - record workflow URL,
   - download artifacts from GitHub Release,
   - run `scripts/release_artifact_smoke.py --dist-dir ... --serve`.

3. **After Stripe test credentials are available**
   - start Scout locally with Stripe test settings,
   - run `scripts/stripe_test_mode_smoke.py --create-checkout`,
   - complete test payment,
   - deliver webhook,
   - prove hosted key delivery and no secret leakage.

4. **After Docker publishing approval**
   - add approved registry publishing workflow,
   - publish one image,
   - run `scripts/docker_image_smoke.py ghcr.io/OWNER/IMAGE:TAG`.

## Recommended Decision Order

1. Choose license.
2. Choose private-beta posture for the Crawl4AI/lxml blocker.
3. Confirm whether `$22` finite hosted beta remains the private-beta offer.
4. Approve or defer artifact-only private-beta release tags.
5. Provide Stripe test-mode setup when payment gate is ready to close.

## Do Not Claim Yet

Do not claim:

- public launch readiness,
- public registry availability,
- unlimited hosted crawling,
- certified app UI,
- security-clean dependency audit,
- final legal terms/privacy,
- hard-site bypass guarantees.

## Next Best Work Without More Decisions

If no decision is available, the next useful Codex-owned work is to keep
hardening deterministic certification:

- expand launch docs tests,
- keep route/render verification current,
- rerun dependency audit refresh when Crawl4AI releases a new version,
- add a formal exception template for the Crawl4AI/lxml gate,
- prepare the exact license implementation patch behind the approval decision
  without applying a final license expression.
