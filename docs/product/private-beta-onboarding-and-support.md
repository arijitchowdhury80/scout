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

- hosted beta API key and credit issues,
- hosted HTTP API and Claude/Codex skill usage questions,
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
| Hosted HTTP or skill blocker | acknowledge within 3 business days |
| Product/workflow bug | triage during beta review cycles |
| Feature request | review for roadmap fit, no SLA |

These are beta targets, not contractual support terms.

## Tester Onboarding

### 1. Choose A Path

Tester-facing beta distribution is limited to hosted HTTP and the Claude/Codex skill.
Docker is internal deployment infrastructure, not a beta tester onboarding path.
Source-install and command-line usage remain operator/developer verification surfaces.

- Hosted HTTP API: best for testers who need an API key and managed service; usage is
  finite and metered.
- Claude/Codex skill: best when an agent should call Scout through hosted HTTP and preserve
  source evidence.

### 2. Get A Hosted API Key

Hosted beta testers generate or receive a metered API key:

```bash
export SCOUT_HOSTED_BASE_URL="https://scout.chowmes.com"
export SCOUT_HOSTED_API_KEY="paste-your-delivered-key"
curl "$SCOUT_HOSTED_BASE_URL/v1/hosted/me" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY"
```

### 3. Run One Small Smoke

Hosted HTTP:

```bash
curl -s -X POST "$SCOUT_HOSTED_BASE_URL/v1/hosted/scrape" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"],"timeout_ms":30000}'
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

- hosted environment or skill package commit,
- hosted HTTP API, Claude/Codex skill, or documentation surface,
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
