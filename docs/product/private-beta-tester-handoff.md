# Private Beta Tester Handoff

Date: 2026-06-29

Status: sendable private beta tester packet

Send this packet to approved private beta testers. It is intentionally short:
the goal is to help a tester complete one 30-minute first run, find artifacts,
and report useful feedback without exposing secrets.

## Current Launch Truth

- Private beta: `ready_with_limits`
- Public launch: `blocked`
- Local Scout is the primary beta path.
- Hosted Scout is a finite-credit convenience API for approved testers only.
- No unlimited hosted crawling.
- No guaranteed hard-site bypass.

Before inviting a tester, operators should run:

```bash
scout launch-readiness
scout launch-decision-check --check-existing --check-drafts
```

## Which Path Should You Choose?

### Local-first path

Choose this if you want the simplest, safest beta experience. Scout runs on
your machine and writes artifacts into your selected workdir.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation"
playwright install chromium
export SCOUT_WORKDIR="$PWD/scout-runs"
scout serve
```

Then open:

```text
http://127.0.0.1:8421/
http://127.0.0.1:8421/docs
```

### Docker path

Choose this if you want Scout as a local service boundary.

```bash
docker compose -f docker/docker-compose.yml up --build
curl http://127.0.0.1:8421/health
```

### Hosted convenience path

Choose this only after you receive a hosted beta API key. Hosted beta is capped
and metered while unit economics are validated. Final credits, price,
retention, and overage rules are not approved yet. Do not treat hosted beta as
unlimited crawling or lifetime API access.

```bash
export SCOUT_HOSTED_BASE_URL="https://your-hosted-scout.example"
export SCOUT_HOSTED_API_KEY="paste-your-delivered-key"

curl "$SCOUT_HOSTED_BASE_URL/v1/hosted/me" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY"
```

### Skill/agent path

Choose this if you want Claude, Codex, or another agent to call Scout through
the CLI or HTTP API. The agent should preserve source evidence and reference
the artifact paths it created.

## 30-Minute First Run

### 1. Confirm Scout is alive

```bash
curl http://127.0.0.1:8421/health
```

### 2. Run one small scrape

```bash
curl -s -X POST http://127.0.0.1:8421/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${SCOUT_API_KEY:-dev-key}" \
  -d '{"url":"https://example.com","formats":["markdown"],"timeout_ms":30000}'
```

### 3. Run one structured workflow

```bash
scout run company --query Adobe --mode auto --workdir ./scout-runs
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

- Scout version, commit, Docker tag, or hosted environment.
- Surface used: local package, Docker, hosted API, or skill.
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

- install or access Scout through one supported path,
- run one scrape or company workflow,
- find the artifact folder or hosted response,
- understand hosted credits are finite,
- understand public launch remains blocked,
- file useful feedback without sharing secrets.
