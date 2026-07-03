# Scout Distribution Package Plan

Date: 2026-06-29
Status: Controlled private beta distribution plan; public registry publishing blocked

## Source Of Truth

Use this plan with:

- Release checklist: `docs/product/release-checklist.md`
- Launch evidence index: `docs/product/launch-evidence-index-2026-06-29.md`
- Registry policy: `docs/product/registry-publishing-policy-2026-06-29.md`
- License decision brief: `docs/legal/scout-license-distribution-decision-brief-2026-06-29.md`
- License implementation runbook: `docs/legal/license-implementation-runbook-2026-06-29.md`

Quick status command:

```bash
scout launch-readiness
```

GitHub CI runs the repository wrapper for this checker to keep the verified
private-beta distribution evidence intact on every pull request.

## Distribution Goals

Tester-facing beta distribution is hosted HTTP plus Claude/Codex skill.

1. Hosted HTTP API at the approved hosted base URL.
2. Agent/tool backend through the Claude/Codex skill.

Local package, CLI, Python package, and Docker remain internal verification/operator surfaces.
They are not beta tester distribution paths for this launch. Docker must not appear in tester onboarding copy; it remains VPS deployment infrastructure.

## Current Private-Beta Distribution Surfaces

| Surface | Status | Install Or Access Path | Evidence | Boundary |
|---|---|---|---|---|
| Hosted HTTP API | Verified quickstart | `https://scout.chowmes.com/v1/hosted/*` with `Authorization: Bearer scout_live_...` | `docs/product/hosted-api-quickstart-verification-2026-06-28.md` | Finite credits, metered usage, no unlimited hosted crawling. |
| Claude/Codex skill | Verified docs | bundled `scout/skill/scout.md` | `docs/product/skill-usage-verification-2026-06-29.md` | Skill documentation is verified; broad prompt behavior remains beta. |
| Launch website | Verified routes | `https://scout.chowmes.com` | `docs/product/website-route-render-verification-2026-06-29.md` | Website is a beta education surface; legacy `/app` UI is not certified. |

## Hosted HTTP Tester Path

Current beta base URL:

```bash
export SCOUT_HOSTED_BASE_URL="https://scout.chowmes.com"
export SCOUT_HOSTED_API_KEY="paste-your-generated-key"
curl "$SCOUT_HOSTED_BASE_URL/v1/hosted/me" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY"
```

Small smoke:

```bash
curl -X POST "$SCOUT_HOSTED_BASE_URL/v1/hosted/scrape" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"],"timeout_ms":30000}'
```

## Claude/Codex Skill Tester Path

The skill wrapper is bundled at `scout/skill/scout.md`. Tester-facing
instructions should tell agents to call the hosted HTTP API and preserve source
evidence. Local CLI commands in the skill verification docs are package smoke
evidence, not a tester distribution promise.

## Package Readiness

Current package state:

- `pyproject.toml` defines package name `scout-web`; installed CLI command remains `scout`.
- CLI entrypoint exists: `scout = scout.cli:app`.
- Version is currently `0.1.0`.
- Python requirement is `>=3.11`.
- Hatch wheel packaging explicitly ships the `scout` module even though the
  distribution package name is `scout-web`.
- Hatch wheel packaging includes the launch website assets required by `/`.
- Hatch wheel packaging includes `THIRD_PARTY_NOTICES.md`.
- Docker runtime remains VPS/internal infrastructure, not a tester distribution.

Verified internal package/operator gates:

- package metadata added for `scout-web`,
- clean wheel install smoke,
- installed `import scout` smoke,
- installed `scout --help` smoke,
- launch website served from a clean wheel install,
- GitHub CI package build and installed CLI smoke gate,
- tag-driven GitHub release artifact workflow,
- release workflow smoke for built wheel and internal Docker image.

Open package gates:

- release artifact workflow run against an approved real `v*` tag,
- downloaded GitHub Release artifact smoke,
- public registry publishing approval.

## GitHub Release Workflow

Current release automation is intentionally artifact-first:

- pushing a `v*` tag runs `.github/workflows/release.yml`,
- the workflow builds wheel and sdist artifacts,
- installs the built wheel into a clean virtual environment,
- smokes `import scout` and `scout --help`,
- builds the internal Docker image used for deployment smoke,
- runs an internal container smoke for `/health`, `/`, and `/styles.css`,
- uploads `dist/*` as workflow artifacts,
- creates a GitHub Release and attaches `dist/*`.

This does not publish to PyPI, GHCR, Docker Hub, or any other registry yet.
That is deliberate until Scout's license, package visibility, and hosted/local
distribution policy are final.

After artifact-only release tag approval:

```bash
python3 scripts/release_artifact_smoke.py --dist-dir /path/to/downloaded/dist --serve
```

To enforce that a public release is actually ready, run:

```bash
scout launch-readiness --require-public
```

This command must fail until public-launch blockers are closed.

## Registry Policy

Current recommendation:

- private beta tags should remain GitHub Release artifact-only,
- PyPI should be the first public package registry if Scout local/core is
  approved as Apache-2.0, MIT, or another publishable license,
- GHCR should be the first container registry if container publishing is
  approved,
- Docker Hub should be deferred until user demand justifies the extra support
  surface.

See `docs/product/registry-publishing-policy-2026-06-29.md`.

## GitHub Hygiene

Current expected state before every beta checkpoint:

- generated local residue removed,
- accidental run artifacts not tracked,
- `.env` and `.env.local` ignored,
- website/docs paths tracked intentionally,
- release checklist and evidence index current,
- package build, Docker build, route smoke, secret scan, and dependency audit
  workflows visible in CI.

## Security And Legal Distribution Boundaries

Do not distribute broadly until:

- third-party notices remain included in wheel/sdist and Docker context,
- dependency audit blocker is resolved or formally excepted,
- final hosted terms/privacy are reviewed for broad hosted access,
- registry publishing policy is approved.

## Hosted Scout

Hosted Scout is the primary tester-facing beta distribution path.

Hosted beta constraints:

- approved testers only,
- generated API keys,
- finite credits,
- separate metering for browser/rendered work,
- no unlimited hosted crawling,
- no public self-serve signup until Stripe and legal gates close.

Hosted production still needs:

- async jobs,
- object storage or signed artifact URLs,
- production retention policy,
- production egress policy,
- operational dashboards,
- final legal terms and privacy policy.

## MCP Server

MCP is a strong future distribution surface because agents can call Scout as a
tool. Candidate MCP tools:

- `scrape_page`
- `crawl_site`
- `map_site`
- `screenshot_page`
- `structure_html`
- `harvest_browser_page`
- `extract_products`
- `preview_algolia_records`
- `push_algolia_records`
- `run_company_intel`
- `run_careers_intel`
- `run_news_intel`
- `run_investor_intel`
- `get_run_artifacts`

MCP should come after the local API contract is stable and documented.

## Do Not Claim Yet

- PyPI availability.
- GHCR or Docker Hub image availability.
- Public self-serve hosted signup.
- Public launch readiness.
- Security-clean dependency audit.
- Certified legacy `/app` UI.
- Unlimited hosted crawling.
