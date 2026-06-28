# Scout Distribution Package Plan

Date: 2026-06-27
Status: Draft

## Distribution Goals

Scout should be usable in four ways:

1. local Python package,
2. CLI,
3. HTTP/Docker service,
4. agent/tool backend through skill or future MCP server.

## Local Install

Target command:

```bash
pip install scout-web
# or until the first package release:
pip install git+https://github.com/arijitchowdhury80/scout.git
playwright install chromium
scout serve
```

Required docs:

- [ ] Python version requirements.
- [ ] Playwright browser install.
- [ ] `.env.local` setup.
- [ ] `SCOUT_API_KEY`.
- [ ] `SCOUT_WORKDIR`.
- [ ] quick health check.
- [ ] quick scrape example.
- [ ] where artifacts are written.

## Docker Install

Target command:

```bash
docker compose -f docker/docker-compose.yml up -d
curl http://localhost:8421/health
```

Required docs:

- [x] environment variables,
- [x] volume mounts for `scout-runs`,
- [x] exposed ports,
- [x] API key configuration,
- [x] Playwright/browser dependencies,
- [x] production reverse proxy notes.

Latest Docker smoke:

- `docker build -f docker/Dockerfile -t scout:launch-smoke .` passed.
- Container smoke passed for `/health`, `/`, and `/styles.css` on port `18421`.

## Package Readiness

Current package state:

- `pyproject.toml` defines package name `scout-web`; the installed CLI command
  remains `scout`.
- CLI entrypoint exists: `scout = scout.cli:app`.
- Version is currently `0.1.0`.
- Crawl4AI, Playwright, FastAPI, Algolia, SQLite, Typer dependencies are present.
- Runtime dependency metadata includes `email-validator` for Pydantic email
  models used by hosted account, payment, and key-delivery flows.
- Hatch wheel packaging explicitly ships the `scout` module even though the
  distribution package name is `scout-web`.
- Hatch wheel packaging includes the launch website assets required by `/`.
- Docker packaging copies `README.md`, `scout/`, and `website/` before
  `pip install .`.
- Docker runtime uses `DB_PATH=/data/scout.db`, matching Scout settings.

Before public package release:

- [ ] Decide Scout's own license.
- [ ] Add `LICENSE` if open/source-available.
- [ ] Add `THIRD_PARTY_NOTICES.md`.
- [x] Add classifiers to `pyproject.toml`.
- [x] Add package metadata: authors, URLs, readme.
- [ ] Decide and add final license expression.
- [ ] Verify package includes `scout/skill` if intended.
- [x] Build wheel/sdist.
- [x] Install from built wheel in a clean venv.
- [x] Run quick smoke after install.
- [x] Verify launch website is served from a clean wheel install.

## GitHub Readiness

- [ ] Clean generated local residue.
- [ ] Remove accidental run artifacts from tracked status.
- [ ] Keep `.env` and `.env.local` ignored.
- [ ] Add website/docs paths intentionally.
- [ ] Add release checklist.
- [ ] Add issue templates for beta feedback.
- [ ] Add security policy before public launch.

## Hosted Scout

If Scout is hosted as a service, usage changes:

- users do not install locally,
- browser/user-session capture becomes harder,
- data residency and customer isolation become product requirements,
- infrastructure costs and abuse prevention become central,
- terms of service become mandatory.

Hosted Scout should probably be a later phase. The first public path should be
local/Docker/private beta.

## MCP Server

MCP is a strong next distribution surface because agents can call Scout as a
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
