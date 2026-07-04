# Scout Launch Decision Request

Date: 2026-06-29
Status: Decisions requested from Arijit

## Purpose

This memo collects the owner decisions needed to move Scout from controlled
private beta toward public launch. It does not replace the release checklist;
it is the shortest path for Arijit to answer the open gates.

Decision record template:
`docs/product/founder-decision-record-template-2026-06-29.md`.

## Current Recommendation

Approve Scout for **controlled private beta only**.

Do not approve public launch yet.

## Decisions Requested

| # | Decision | Recommended answer | Why it matters | Codex action after approval |
|---:|---|---|---|---|
| 1 | Scout local/core license | Approve Apache-2.0 | Best fit for local-first trust, Crawl4AI alignment, company adoption, and hosted-service monetization | Add `LICENSE`, add `license = "Apache-2.0"` to `pyproject.toml`, update README/legal page, rebuild, run `scripts/license_release_gate_check.py --expected-license Apache-2.0 --dist-dir dist` |
| 2 | Crawl4AI/lxml private-beta risk | Approve limited private-beta exception only | Keeps beta learning moving while public launch remains blocked by `PYSEC-2026-87` through `lxml 5.4.0` | Record approval in `docs/security/crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md`; keep dependency audit visible/non-blocking; keep public launch blocked |
| 3 | Hosted beta offer | Reject arbitrary `$22`/`$9`; use the approved `$0` beta setup plus `$10/$25/$100` pay-as-you-go standard-credit packages | Protects hosting/browser/LLM/security/support economics and avoids unlimited crawling liability | Keep website/payment copy metered; do not advertise unlimited hosted crawling |
| 4 | Artifact-only release tag | Approve one private-beta `v*` tag after license path is chosen | Produces downloadable GitHub Release wheel/sdist without PyPI/GHCR/Docker Hub | Create approved tag, record workflow URL, download artifacts, run `scripts/release_artifact_smoke.py --dist-dir ... --serve` |
| 5 | Docker registry | Defer Docker image publishing until after private-beta artifact tag | Avoids broad container distribution before license/security/publishing posture is settled | Keep Docker-from-source path; do not add GHCR/Docker Hub publishing jobs |
| 6 | Stripe test-mode credentials | Provide when ready to close payment gate | Required to verify real Checkout Session, webhook, and hosted key delivery | Run `scripts/scout-hosted-admin stripe-smoke --create-checkout`, complete payment, deliver webhook, verify `/v1/hosted/me` |
| 7 | Final terms/privacy | Defer broad hosted launch until legal review | Beta placeholders are not final commercial legal terms | Keep `/terms` and `/privacy` as beta placeholders; do not broad-launch hosted API |

## If You Want The Fastest Private-Beta Path

Answer these five:

```text
1. License: Apache-2.0 approved for Scout local/core.
2. Crawl4AI/lxml: limited private-beta exception approved; public launch stays blocked.
3. Hosted beta: use self-service name/email registration, $0 card-backed beta setup when Stripe/SMTP are configured, and the approved `$10/$25/$100` pay-as-you-go standard-credit packages.
4. Release tag: approve one artifact-only private-beta v* tag after license files are added.
5. Docker registry: defer GHCR/Docker Hub.
```

Then Codex can execute:

1. license implementation,
2. package rebuild and license artifact smoke,
3. private-beta release tag,
4. GitHub Release artifact smoke,
5. keep public launch blocked until dependency audit, Stripe, final legal, and
   registry policy gates close.

## What Not To Approve Yet

- Public launch.
- PyPI publish.
- GHCR or Docker Hub publish.
- Unlimited hosted crawling.
- Production hosted SaaS without Stripe/SMTP live smoke.
- Security-clean claim.
- Certified legacy `/app` UI claim.
- Hard-site bypass guarantee.

## Evidence To Review

- Release checklist: `docs/product/release-checklist.md`
- Launch dashboard: `docs/product/launch-decision-dashboard-2026-06-29.md`
- Gate burndown: `docs/product/launch-gate-burndown-2026-06-29.md`
- License brief: `docs/legal/scout-license-distribution-decision-brief-2026-06-29.md`
- License implementation runbook: `docs/legal/license-implementation-runbook-2026-06-29.md`
- Crawl4AI/lxml exception packet: `docs/security/crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md`
- Stripe readiness: `docs/product/stripe-test-mode-readiness-2026-06-29.md`
- Registry policy: `docs/product/registry-publishing-policy-2026-06-29.md`
