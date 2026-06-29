# Scout Public Launch Action Packet

Date: 2026-06-29
Status: Public launch blocked; next actions grouped by executable blocker type

Generated from `scout launch-readiness --json` after the readiness checker was
updated to classify public-launch blockers.

The readiness JSON now includes a remediation map on every public-launch
blocker:

- `id`
- `summary`
- `owner`
- `next_action`
- `closure_evidence`
- `codex_actionable_now`

That means the action list is machine-readable as well as human-readable; the
plain-English tables below are a dashboard over the same blocker contract.
`id` is the stable machine key, while `summary` is the human label. The report
now includes both blocker-type and owner summaries, so it is clear whether the
next bottleneck is a founder decision, Codex implementation, shared Stripe
smoke, or a risk decision.

Useful slices:

```bash
scout launch-readiness --owner Arijit
scout launch-readiness --owner Codex
scout launch-readiness --blocker-type founder_decision
scout launch-readiness --blocker-type engineering
scout launch-readiness --blocker-id license-decision
scout launch-readiness --json --owner Arijit
```

Filters change the displayed blocker list and summary only. They do not change
the underlying public-launch verdict. Use `--blocker-id` when a decision,
handoff, or release note needs to reference one stable gate exactly.

Founder decision record template:
`docs/product/founder-decision-record-template-2026-06-29.md`.

Generate a prefilled draft for any stable blocker ID before editing the
decision:

```bash
scout launch-decision-drafts \
  --owner Arijit \
  --include-shared-owner \
  --decision-date YYYYMMDD

scout launch-decision-draft \
  --blocker-id license-decision \
  --decision-id SCOUT-DEC-YYYYMMDD-NN

python3 scripts/founder_decision_record_draft.py \
  --blocker-id license-decision \
  --decision-id SCOUT-DEC-YYYYMMDD-NN
```

Drafts are written under `docs/product/founder-decision-drafts/` so they do not
count as completed launch evidence until reviewed, moved into the completed
record naming pattern, and validated.

Generated founder decision draft packet:
`docs/product/founder-decision-drafts/index.md`.

Draft packet is not approval evidence. It is the review queue for the six
founder, risk, and shared external-smoke decisions that currently block public
launch. Each draft remains `Status: Deferred` and keeps
`Public launch allowed by this decision? No` until Arijit reviews and approves a
completed decision record.

Validate completed founder decision records before using them as launch
evidence:

```bash
scout launch-decision-check docs/product/founder-decision-record-SCOUT-DEC-YYYYMMDD-NN.md
scout launch-decision-check --check-existing

python3 scripts/founder_decision_record_check.py docs/product/founder-decision-record-SCOUT-DEC-YYYYMMDD-NN.md
```

## Current Readiness Truth

Private beta remains `ready_with_limits`.

Public launch remains `blocked`.

Current blocker count:

| Blocker type | Count | Meaning |
|---|---:|---|
| `founder_decision` | 4 | Arijit must approve the business, pricing, or publishing direction. |
| `legal_implementation` | 4 | Codex can implement after the license/legal direction is approved. |
| `engineering` | 4 | Codex can execute after the prerequisite approval/artifact exists. |
| `risk_decision` | 1 | Arijit/security must accept, mitigate, or wait for a clean dependency path. |
| `external_smoke` | 1 | A real external sandbox flow must be tested with credentials/webhooks. |

## Decision Packet For Arijit

These answers are enough to unlock the next private-beta packaging steps without
approving public launch.

```text
1. License: Approve Apache-2.0 for Scout local/core.
2. Pricing: Keep $22 as a finite-credit hosted beta pass.
3. Publishing: Approve artifact-only private-beta v* tag after license files land.
4. Docker publishing: Defer GHCR and Docker Hub image publishing.
5. Crawl4AI/lxml: Approve limited private-beta exception only, or require clean audit first.
6. Public hosted: Do not approve public self-serve hosted launch yet.
```

Recommended answers:

| Decision | Recommended answer | Why |
|---|---|---|
| License | Approve Apache-2.0 for Scout local/core | Aligns with Crawl4AI Apache-2.0 dependency posture and keeps local trust high. |
| Hosted beta pricing | Keep $22 as a finite-credit hosted beta pass | Avoids unlimited hosted crawling economics and keeps the offer honest. |
| Artifact-only tag | Approve one private-beta `v*` tag after license implementation | Lets testers install from a GitHub Release artifact without PyPI/GHCR. |
| Docker publishing | Defer GHCR and Docker Hub | Docker-from-source is already verified; public images widen distribution before legal/security gates close. |
| Crawl4AI/lxml risk | Approve limited private-beta exception only, or keep beta branch install and wait | Public launch should stay blocked while dependency audit is not clean. |
| Public hosted signup | Do not approve yet | Needs final legal terms, real Stripe smoke, production storage, distributed throttling, and support readiness. |

## Blockers By Type

### `founder_decision`

| Gate | Current recommendation | Next action |
|---|---|---|
| License decision | Apache-2.0 for Scout local/core | Arijit approves or chooses another license path. |
| Public pricing and hosted usage limits | Keep private beta `$22` finite-credit; defer public pricing | Arijit approves beta offer and withholds public hosted launch approval. |
| Registry publishing policy | Artifact-only private-beta tag first; no PyPI/GHCR/Docker Hub yet | Arijit approves or rejects private-beta release tags. |
| Docker image publishing policy | Defer public image publishing | Arijit confirms Docker-from-source remains the only beta container path. |

### `legal_implementation`

| Gate | Dependency | Codex action after approval |
|---|---|---|
| Final license expression | License decision | Add final SPDX expression to `pyproject.toml`. |
| `LICENSE` file | License decision | Add the approved license file. |
| Pyproject license expression | License decision | Keep package metadata aligned with the approved license. |
| License file existence | License decision | Verify wheel/sdist contain license and third-party notices. |

### `engineering`

| Gate | Dependency | Codex action |
|---|---|---|
| GitHub release workflow run | Artifact-only tag approval and license implementation | Push approved `v*` tag and record workflow URL. |
| Release artifact smoke | GitHub Release artifacts exist | Download artifacts and run `scripts/release_artifact_smoke.py --dist-dir ... --serve`. |
| Published Docker image smoke | Docker publishing approval and image exists | Pull published image and run `scripts/docker_image_smoke.py ghcr.io/OWNER/IMAGE:TAG`. |
| Dependency audit blocking cleanly | Clean dependency path or accepted formal exception | Make CI dependency audit blocking only after the chosen dependency/risk path is viable. |

### `risk_decision`

| Gate | Choices | Recommendation |
|---|---|---|
| Crawl4AI/lxml risk decision | Wait for clean upstream, fork/replace dependency path, or approve formal exception | Approve private-beta exception only; keep public launch blocked until clean or formally accepted. |

### `external_smoke`

| Gate | Needs | Codex action |
|---|---|---|
| Stripe real test-mode smoke | `STRIPE_SECRET_KEY`, `STRIPE_BETA_PRICE_ID`, `STRIPE_WEBHOOK_SECRET`, test recipient/key delivery setup | Run `scripts/stripe_test_mode_smoke.py --create-checkout`, complete test payment, deliver webhook, verify hosted key works. |

## What Codex Can Do Immediately After Approval

### If license is approved

1. Add `LICENSE`.
2. Add `license = "Apache-2.0"` or approved equivalent to `pyproject.toml`.
3. Update README/legal website copy.
4. Rebuild wheel/sdist.
5. Run `scripts/license_release_gate_check.py --expected-license Apache-2.0 --dist-dir dist`.
6. Run package metadata, launch readiness, unit, Pyright, Ruff, and artifact-inspection checks.

### If artifact-only tag is approved

1. Create one approved private-beta `v*` tag.
2. Wait for GitHub release artifact workflow.
3. Record workflow URL and artifact names.
4. Download artifacts into a clean directory.
5. Run `scripts/release_artifact_smoke.py --dist-dir ... --serve`.

### If Stripe credentials are provided

1. Start Scout with test Stripe and key-delivery settings.
2. Run `scripts/stripe_test_mode_smoke.py --create-checkout`.
3. Complete Stripe Checkout test payment.
4. Deliver the real webhook to `/v1/billing/stripe/webhook`.
5. Confirm the delivered hosted key authenticates to `/v1/hosted/me`.

## Do Not Approve Yet

- Public launch.
- Public PyPI publish.
- Public GHCR or Docker Hub publish.
- Unlimited hosted crawling.
- Public self-serve hosted signup.
- Security-clean claim.
- Certified legacy `/app` UI claim.
- Hard-site bypass guarantee.

## Source Documents

- Release checklist: `docs/product/release-checklist.md`
- Launch dashboard: `docs/product/launch-decision-dashboard-2026-06-29.md`
- Gate burndown: `docs/product/launch-gate-burndown-2026-06-29.md`
- Decision request: `docs/product/launch-decision-request-2026-06-29.md`
- License brief: `docs/legal/scout-license-distribution-decision-brief-2026-06-29.md`
- Crawl4AI/lxml exception packet: `docs/security/crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md`
- Stripe readiness: `docs/product/stripe-test-mode-readiness-2026-06-29.md`
