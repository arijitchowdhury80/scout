# Private Beta Onboarding And Support

Date: 2026-06-29

Status: private beta operating guide

## Support Channel

Scout private beta support uses GitHub issue templates in this repository for
non-security feedback:

- Bug reports: `.github/ISSUE_TEMPLATE/private_beta_bug.yml`
- Feature/workflow requests: `.github/ISSUE_TEMPLATE/private_beta_feature.yml`

Security reports must not be filed as public GitHub issues. Follow
`SECURITY.md` and report vulnerabilities privately to the project maintainer.

## Support Boundaries

Private beta support covers:

- local install and packaging issues,
- Docker service startup issues,
- hosted beta API key and credit issues,
- CLI, HTTP API, Docker, and skill usage questions,
- product extraction and artifact contract bugs,
- documentation gaps and confusing setup steps.

Private beta support does not promise:

- guaranteed hard-site bypass,
- legal permission to access restricted sites,
- production hosted uptime/SLA,
- unlimited hosted crawling,
- browser-session debugging for private accounts unless explicitly arranged,
- support for secrets, cookies, API keys, or private customer data pasted into
  public issues.

## Response Targets

Best-effort private beta targets:

| Type | Target |
|---|---|
| Critical security report | acknowledge within 72 hours |
| Hosted key/payment access issue | acknowledge within 2 business days |
| Local install or Docker blocker | acknowledge within 3 business days |
| Product/workflow bug | triage during beta review cycles |
| Feature request | review for roadmap fit, no SLA |

These are beta targets, not contractual support terms.

## Tester Onboarding

### 1. Choose A Path

Start locally unless the tester explicitly needs hosted convenience.

- Local package: best for first tests, private workflows, artifact inspection,
  and user-controlled storage.
- Docker: best for service-style local testing with a clean boundary.
- Hosted beta: best for users who need an API key and managed workers; usage is
  finite and metered.
- Skill: best when an agent should call Scout through CLI/HTTP and preserve
  source evidence.

### 2. Install Or Start Scout

Use the verified private-beta branch install path:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation"
playwright install chromium
export SCOUT_WORKDIR="$PWD/scout-runs"
scout serve
```

For Docker:

```bash
docker compose -f docker/docker-compose.yml up --build
curl http://127.0.0.1:8421/health
```

For hosted beta:

```bash
export SCOUT_HOSTED_BASE_URL="https://scout.chowmes.com"
export SCOUT_HOSTED_API_KEY="paste-your-delivered-key"
curl "$SCOUT_HOSTED_BASE_URL/v1/hosted/me" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY"
```

### 3. Run One Small Smoke

Local HTTP:

```bash
curl -s -X POST http://127.0.0.1:8421/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${SCOUT_API_KEY:-dev-key}" \
  -d '{"url":"https://example.com","formats":["markdown"],"timeout_ms":30000}'
```

Hosted HTTP:

```bash
curl -s -X POST "$SCOUT_HOSTED_BASE_URL/v1/hosted/scrape" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"],"timeout_ms":30000}'
```

CLI:

```bash
scout run company --query Adobe --mode auto --workdir ./scout-runs
```

### 4. Inspect Evidence

Ask testers to verify that they can find:

- `manifest.json`
- `records.json`
- `records.jsonl`
- `source_pages.json`
- `blocked_pages.json`
- `validation.json`
- `extraction_report.md`

Useful feedback includes record count, source count, citation count, blocked
page count, target URL, run ID, and non-sensitive artifact paths.

### 5. File Feedback

Use GitHub private beta issue templates:

- Use **Private beta bug** when Scout fails, produces confusing artifacts, blocks
  unexpectedly, or documentation does not match behavior.
- Use **Private beta feature request** when a workflow is missing or awkward.

Include:

- Scout version, commit, Docker tag, or hosted environment,
- local package / Docker / hosted API / skill surface,
- command or endpoint used,
- target type or public URL when safe,
- run ID or artifact path,
- expected vs actual behavior.

Do not include:

- API keys,
- cookies,
- private customer data,
- paid-site content,
- resume/private job profiles,
- screenshots containing secrets.

## Beta Success Criteria

A private beta tester is considered onboarded when they can:

- install or access Scout through one supported path,
- run one scrape or company workflow,
- find artifacts in the selected workdir or hosted response,
- understand that hosted credits are finite,
- file feedback through the right channel without sharing secrets.

