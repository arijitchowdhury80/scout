# Founder Decision Draft Packet

Date generated: 2026-06-29
Status: Draft packet for founder/risk/shared launch decisions

These files are editing aids. They are not launch approvals, not completed decision records, and not release evidence until Arijit reviews them, moves the approved content into the completed decision record naming pattern, and the record passes:

```bash
scout launch-decision-check docs/product/founder-decision-record-SCOUT-DEC-YYYYMMDD-NN.md
scout launch-decision-check --check-existing
```

## Drafts To Review

| Draft | Launch blocker | Owner | What to decide |
|---|---|---|---|
| `founder-decision-draft-SCOUT-DEC-20260629-01.md` | `license-decision` | Arijit | Approve Apache-2.0 for Scout local/core or choose another license path. |
| `founder-decision-draft-SCOUT-DEC-20260629-02.md` | `public-pricing-and-hosted-usage-limits` | Arijit | Approve finite hosted beta pricing/limits or choose a different beta model. |
| `founder-decision-draft-SCOUT-DEC-20260629-03.md` | `registry-publishing-policy` | Arijit | Approve artifact-only private-beta tag, public registries, or defer publishing. |
| `founder-decision-draft-SCOUT-DEC-20260629-04.md` | `docker-image-publishing-policy` | Arijit | Approve or defer GHCR/Docker Hub image publishing. |
| `founder-decision-draft-SCOUT-DEC-20260629-05.md` | `crawl4ai-lxml-risk-decision` | Arijit/security | Accept, mitigate, or defer the Crawl4AI/lxml private-beta risk. |
| `founder-decision-draft-SCOUT-DEC-20260629-06.md` | `stripe-real-test-mode-smoke` | Codex + Arijit | Confirm Stripe test-mode smoke can run with supplied sandbox configuration. |

## Safety Boundary

Every generated draft currently says:

- `Status: Deferred`
- `Public launch allowed by this decision? No`

Public launch remains blocked until the release checklist gates are actually
closed or formally excepted.
