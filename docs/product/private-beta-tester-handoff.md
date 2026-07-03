# Private Beta Tester Handoff

Date: 2026-06-29

Status: sendable private beta tester packet

Send this packet to approved private beta testers. It is intentionally short:
the goal is to help a tester complete one 30-minute first run, find artifacts,
and report useful feedback without exposing secrets.

## Current Launch Truth

- Private beta: `ready_with_limits`
- Public launch: `ready`
- Hosted SaaS: `blocked` until SMTP key delivery and Stripe checkout/webhook
  smoke are complete.
- Hosted Scout is the primary beta path for testers.
- Claude/Codex skill usage is the second supported tester path.
- Local package and Docker instructions are no longer tester onboarding paths.
- Current source branch for operator verification: `codex/scout-saas-prod-ready`.
- No unlimited hosted crawling.
- No guaranteed hard-site bypass.

Before inviting a tester, operators should run:

```bash
scout launch-readiness
scout launch-readiness --require-hosted-saas
scout launch-decision-check --check-existing --check-drafts
```

## Which Path Should You Choose?

### Hosted HTTP path

Choose this for normal beta testing. Hosted beta is capped and metered while
unit economics are validated. Final credits, price,
retention, and overage rules are not approved yet. Do not treat hosted beta as
unlimited crawling or lifetime API access.

```bash
export SCOUT_HOSTED_BASE_URL="https://scout.chowmes.com"
export SCOUT_HOSTED_API_KEY="paste-your-delivered-key"

curl "$SCOUT_HOSTED_BASE_URL/v1/hosted/me" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY"
```

For hosted deployments, Scout should run with
`SCOUT_PUBLIC_HOSTED_ONLY=true` so consumers use `/v1/hosted/*` Bearer auth
instead of local `X-API-Key` routes. See
`docs/product/hosted-saas-api-guide.md`.

### Skill/agent path

Choose this if you want Claude, Codex, or another agent to call Scout through
the hosted HTTP API. The agent should preserve source evidence and reference
the artifact paths it created.

## 30-Minute First Run

### 1. Confirm hosted access

```bash
curl "$SCOUT_HOSTED_BASE_URL/v1/hosted/me" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY"
```

### 2. Run one small scrape

```bash
curl -s -X POST "$SCOUT_HOSTED_BASE_URL/v1/hosted/scrape" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY" \
  -d '{"url":"https://example.com","formats":["markdown"],"timeout_ms":30000}'
```

### 3. Run one structured workflow

```bash
curl -s -X POST "$SCOUT_HOSTED_BASE_URL/v1/hosted/run/company" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY" \
  -d '{"query":"Adobe","mode":"saved","max_records":10}'
```

### 4. Inspect artifacts

Look for:

- `manifest.json`
- `records.json`
- `records.jsonl`
- `source_pages.json`
- `blocked_pages.json`
- `validation.json`
- `extraction_report.md`

## What Good Feedback Looks Like

Please include:

- Hosted environment or skill package commit.
- Surface used: hosted HTTP API, Claude/Codex skill, or documentation.
- Command or endpoint used.
- Public target URL or target type, if safe to share.
- Run ID or non-sensitive artifact path.
- Expected result.
- Actual result.
- Whether records, sources, citations, and blocked evidence were present.

Use:

- Bug reports: `.github/ISSUE_TEMPLATE/private_beta_bug.yml`
- Feature/workflow requests: `.github/ISSUE_TEMPLATE/private_beta_feature.yml`

## What Not To Share

Do not paste API keys, cookies, private customer data, paid-site content, secret
environment variables, screenshots containing secrets, or regulated personal
data into public issues.

Security reports should not be filed as public issues. Follow `SECURITY.md`.

## Tester Is Onboarded When

Tester is onboarded when they can:

- access Scout through hosted HTTP or a supported skill workflow,
- run one scrape or company workflow,
- find the artifact folder or hosted response,
- understand hosted credits are finite,
- understand public self-serve SaaS, paid checkout, and public registries remain deferred,
- file useful feedback without sharing secrets.
