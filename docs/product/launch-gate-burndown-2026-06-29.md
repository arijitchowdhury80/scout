# Scout Launch Gate Burndown

Date: 2026-06-29
Status: Current beta release ready; future public self-serve gates deferred

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

Scout is ready for the current controlled beta release.

Scout is viable for controlled private beta because it stays inside these
boundaries:

- local install from the verified GitHub branch,
- Docker built from source,
- hosted API keys for approved testers,
- no PyPI publish,
- no GHCR or Docker Hub publish,
- no unlimited hosted crawling,
- no certified legacy `/app` UI claim,
- no security-clean claim while the dependency audit is failing.

Current blockers: 0. Future public self-serve SaaS, PyPI, GHCR, Docker Hub,
paid checkout, and security-clean claims must reopen the corresponding gates
before those surfaces are enabled.

## Gate Burndown

| Gate | Status | Blocker type | Owner | Next action | Evidence |
|---|---:|---|---|---|---|
| Launch website routes/render | Closed | None | Codex | Keep website tests in CI; do not call `/app` certified | `docs/product/website-route-render-verification-2026-06-29.md` |
| Local install path | Closed | None | Codex | Keep branch-qualified quickstart until package registry gates close | `docs/product/local-install-verification-2026-06-28.md` |
| Docker-from-source path | Closed | None | Codex | Keep source-build Docker docs; do not publish image yet | `docs/product/docker-install-verification-2026-06-28.md` |
| Hosted API quickstart | Closed | None | Codex | Keep hosted beta limited to approved testers | `docs/product/hosted-api-quickstart-verification-2026-06-28.md` |
| Product export beyond Algolia | Closed | None | Codex | Treat Algolia as one adapter, not the product's only output | `docs/product/product-export-generalization-verification-2026-06-29.md` |
| License decision | Closed | None | Arijit | Apache-2.0 local/core approved by "ok do it"; hosted/service monetization remains separate | `LICENSE`; `pyproject.toml`; `docs/legal/scout-license-distribution-decision-brief-2026-06-29.md` |
| Final license expression | Closed | None | Codex | Keep `pyproject.toml` license metadata in package tests | `pyproject.toml` |
| `LICENSE` file | Closed | None | Codex | Keep root `LICENSE` included in wheel/sdist release smoke | `LICENSE` |
| License release gate helper | Closed | None | Codex | Keep `scripts/license_release_gate_check.py --expected-license Apache-2.0 --dist-dir dist` in release verification | `scripts/license_release_gate_check.py` |
| Public pricing and hosted usage limits | Closed | None | Arijit | Keep current beta metered/invite-only; reopen before public paid self-serve pricing | `docs/product/founder-decision-record-SCOUT-DEC-20260629-02.md` |
| Registry publishing policy | Closed | None | Arijit | Artifact-only beta tags approved; no PyPI/GHCR/Docker Hub in current beta | `docs/product/founder-decision-record-SCOUT-DEC-20260629-03.md` |
| GitHub release workflow on real `v*` tag | Closed | None | Codex | Keep `release.yml` artifact-only until registry publishing is approved | `https://github.com/arijitchowdhury80/scout/actions/runs/28415351878` |
| Release artifact download smoke | Closed | None | Codex | Keep downloaded-artifact smoke in release verification | `scripts/release_artifact_smoke.py`; tag `v0.1.0-beta.1` |
| Docker image publishing policy | Closed | None | Arijit | Docker-from-source remains current beta path; reopen before GHCR/Docker Hub | `docs/product/founder-decision-record-SCOUT-DEC-20260629-04.md` |
| Published Docker image smoke | Closed | None | Codex | Not applicable until public registry image publishing is approved | `docs/product/founder-decision-record-SCOUT-DEC-20260629-04.md` |
| Crawl4AI/lxml risk decision | Closed | None | Arijit | Private-beta exception approved; no security-clean claim | `docs/product/founder-decision-record-SCOUT-DEC-20260629-05.md` |
| Dependency audit clean and blocking in CI | Closed | None | Codex plus upstream | Visible/non-blocking under private-beta exception; reopen before public registry/self-serve launch | `docs/product/founder-decision-record-SCOUT-DEC-20260629-05.md` |
| Stripe real test-mode smoke | Closed | None | Arijit plus Codex | Paid checkout deferred; hosted beta key registration now uses name/email capture plus one-time API-key email delivery | `docs/product/stripe-test-mode-readiness-2026-06-29.md` |
| Final hosted terms/privacy | Open | Legal/commercial review | Arijit/legal | Replace beta placeholders before broad commercial hosted access | `docs/legal/beta-terms-placeholder.md`, `docs/legal/beta-privacy-placeholder.md` |

## Codex-Executable Work Remaining

These can be done immediately after the named dependency is satisfied:

1. **After artifact-only release tag approval**
   - create one private-beta `v*` tag,
   - wait for GitHub release artifact workflow,
   - record workflow URL,
   - download artifacts from GitHub Release,
   - run `scripts/release_artifact_smoke.py --dist-dir ... --serve`.

2. **After Stripe test credentials are available**
   - start Scout locally with Stripe test settings,
   - run `scripts/stripe_test_mode_smoke.py --create-checkout`,
   - complete test payment,
   - deliver webhook,
   - prove hosted key delivery and no secret leakage.

3. **After Docker publishing approval**
   - add approved registry publishing workflow,
   - publish one image,
   - run `scripts/docker_image_smoke.py ghcr.io/OWNER/IMAGE:TAG`.

## Recommended Decision Order

1. Choose private-beta posture for the Crawl4AI/lxml blocker.
2. Fill and approve the unit-economics model before restoring hosted checkout or public pricing claims.
3. Approve or defer artifact-only private-beta release tags.
4. Provide Stripe test-mode setup when payment gate is ready to close.

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
