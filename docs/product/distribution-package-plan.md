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
python3 scripts/launch_readiness_check.py
```

GitHub CI runs this checker to keep the verified private-beta distribution
evidence intact on every pull request.

## Distribution Goals

Scout should be usable in four ways:

1. local Python package,
2. CLI,
3. HTTP/Docker service,
4. agent/tool backend through the Claude/Codex skill, and later an MCP server.

The beta strategy is local-first. Hosted Scout is optional, finite-credit, and
approved-testers-only.

## Current Private-Beta Distribution Surfaces

| Surface | Status | Install Or Access Path | Evidence | Boundary |
|---|---|---|---|---|
| Local Python package from GitHub branch | Verified | `pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation"` | `docs/product/local-install-verification-2026-06-28.md` | Branch-qualified beta path only; no PyPI claim. |
| CLI | Verified through package smoke | installed command: `scout` | `docs/product/local-install-verification-2026-06-28.md`; `docs/product/skill-usage-verification-2026-06-29.md` | CLI supports beta workflows; not every live target is certified. |
| HTTP service | Verified through `scout serve` | `scout serve --host 127.0.0.1 --port 8421` | `docs/product/local-install-verification-2026-06-28.md`; `docs/product/website-route-render-verification-2026-06-29.md` | Legacy `/app` UI is not certified. |
| Docker from source | Verified | `docker compose -f docker/docker-compose.yml up --build -d` | `docs/product/docker-install-verification-2026-06-28.md` | No published GHCR/Docker Hub image yet. |
| Hosted API | Verified quickstart | provisioned beta API key, `/v1/hosted/*` | `docs/product/hosted-api-quickstart-verification-2026-06-28.md` | Approved testers only; finite credits; no public self-serve. |
| Skill docs | Verified | bundled `scout/skill/scout.md` | `docs/product/skill-usage-verification-2026-06-29.md` | Skill documentation is verified; broad prompt behavior remains beta. |

## Local Install Command

Current private-beta command:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation"
playwright install chromium
SCOUT_API_KEY=dev-key SCOUT_WORKDIR=/tmp/scout-runs scout serve
```

Smoke:

```bash
curl http://127.0.0.1:8421/health
curl -X POST http://127.0.0.1:8421/scrape \
  -H "X-API-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","persist":true,"output_dir":"/tmp/scout-runs/example"}'
```

Future package-registry command after approval:

```bash
pip install scout-web
```

Do not publish or document `pip install scout-web` as available until the
license, registry, release, and dependency gates close.

## Docker Install Command

Current private-beta Docker path:

```bash
docker compose -f docker/docker-compose.yml up --build -d
curl http://localhost:8421/health
```

The Docker path is source-build only for beta. Published image smoke is prepared
but blocked until image publishing is approved:

```bash
python3 scripts/docker_image_smoke.py ghcr.io/OWNER/IMAGE:TAG
```

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
- Docker packaging copies `README.md`, `THIRD_PARTY_NOTICES.md`, `scout/`, and
  `website/` before `pip install .`.
- Docker runtime uses `DB_PATH=/data/scout.db`, matching Scout settings.

Verified package gates:

- package metadata added for `scout-web`,
- clean wheel install smoke,
- installed `import scout` smoke,
- installed `scout --help` smoke,
- launch website served from a clean wheel install,
- GitHub CI package build and installed CLI smoke gate,
- tag-driven GitHub release artifact workflow,
- release workflow smoke for built wheel and Docker image.

Open package gates:

- license decision,
- final license expression in `pyproject.toml`,
- `LICENSE` file if Scout is open source or source-available,
- release artifact workflow run against an approved real `v*` tag,
- downloaded GitHub Release artifact smoke,
- public registry publishing approval.

## GitHub Release Workflow

Current release automation is intentionally artifact-first:

- pushing a `v*` tag runs `.github/workflows/release.yml`,
- the workflow builds wheel and sdist artifacts,
- installs the built wheel into a clean virtual environment,
- smokes `import scout` and `scout --help`,
- builds the Docker image,
- runs a container smoke for `/health`, `/`, and `/styles.css`,
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
python3 scripts/launch_readiness_check.py --require-public
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

- Scout license is approved and expressed,
- required license file is added,
- third-party notices remain included in wheel/sdist and Docker context,
- dependency audit blocker is resolved or formally excepted,
- final hosted terms/privacy are reviewed for broad hosted access,
- registry publishing policy is approved.

## Hosted Scout

Hosted Scout is a convenience path, not the primary beta distribution path.

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
