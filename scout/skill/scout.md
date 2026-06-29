---
name: scout
description: Use Scout for provider-agnostic web intelligence: company research, PRISM prospect bundles, investor pages, careers/hiring, job extraction and scoring, product catalog records for Algolia, news signals, docs, and generic web research. Scout runs as a standalone CLI, local HTTP app, and skill-backed extraction engine. Use browser fallback only after normal providers are blocked, sparse, or JS-heavy.
layer: 0-infrastructure
type: server-backed
server_port: 8421
health_check: "curl -s http://localhost:8421/health"
start_command: "scout serve"
requires_install: true
version: 3.0
---

# Scout

Scout is a standalone web intelligence engine built on Crawl4AI with a
provider ladder for host WebFetch/WebSearch, saved replay, API adapters, and
browser fallback. This skill is the agent playbook. Scout itself must remain
usable from terminal, HTTP, Docker, and Python.

## First Decision

Use the lightest channel that can produce evidence:

1. CLI for local standalone runs.
2. HTTP when another process or agent needs a stable local service.
3. Host WebFetch/WebSearch when the host has stronger page/search access.
4. Browser fallback only when pages are blocked, JS-shell, interactive, or
   visual verification is needed.
5. Saved replay for deterministic tests and previously captured HTML/DOM/PDF.

Browser is a secondary channel, not the default.

## Health Check

```bash
curl -s http://localhost:8421/health
```

If not running:

```bash
scout serve
```

Public launch/docs routes are intentionally unauthenticated: `/`, `/health`,
`/quickstart`, `/pricing`, `/beta`, `/legal`, `/terms`, `/privacy`, `/docs`,
`/redoc`, `/openapi.json`, `/styles.css`, and `/third-party-notices`.

Local API routes such as `/scrape`, `/crawl`, `/products`, `/run/{use_case}`,
`/runs/{run_id}`, `/app/runs`, and `/algolia/preview` require:

```text
X-API-Key: dev-key
```

Use `$SCOUT_API_KEY` when configured.

## Working Directory And Local Config

Scout stores each run in a working directory so artifacts, interim status, and
local configs are findable. Prefer an explicit output path when the user gives
one. Otherwise:

1. For CLI runs, pass `--workdir` when the user names a workspace.
2. If the terminal is interactive and no path is provided, Scout prompts for the
   working directory.
3. For HTTP, Docker, scheduled, or skill-driven runs, set `SCOUT_WORKDIR` in
   `.env.local` or pass JSON `output_dir`.

Local keys and machine-specific defaults belong in `.env.local`:

```text
SCOUT_API_KEY=change-me
LLM_API_KEY=
SCOUT_WORKDIR=scout-runs
```

Do not put private API keys, job profiles, resume-derived preferences, or
personal research profiles in the public repository.

## Execution Modes

Use `--mode` or request JSON `"mode"`:

| Mode | Use |
|---|---|
| `auto` | Default provider ladder. |
| `crawl4ai` | Standalone Crawl4AI acquisition. |
| `webfetch` | Host-provided page fetch evidence. |
| `websearch` | Host-provided discovery/search evidence. |
| `browser` | In-app/internal browser fallback. |
| `saved` | Saved HTML, DOM, PDF, or fixture replay. |
| `api` | Provider adapters such as ATS, commerce, investor, and social APIs. |

## High-Level CLI

```bash
scout run company --query Adobe --mode auto --output-dir ./scout-runs/adobe-company
scout run careers --query Algolia --mode auto --output-dir ./scout-runs/algolia-careers
scout run investor --query Salesforce --mode auto --output-dir ./scout-runs/salesforce-investor
scout run prism --query Nike --mode auto --output-dir ./scout-runs/nike-prism
scout run news --query "Adobe AI announcements" --mode websearch --output-dir ./scout-runs/adobe-news
scout run research --query "companies with weak ecommerce search UX" --mode auto --output-dir ./scout-runs/research
scout run jobs --profile ./private-job-profile.yaml --mode api --output-dir ./scout-runs/jobs
scout run products --query "top skincare products" --mode auto --output-dir ./scout-runs/products
```

When the user wants Scout to choose a run folder:

```bash
scout run company --query Adobe --mode auto --workdir ./scout-runs
scout run prism --query Nike --mode auto --workdir ./scout-runs
```

Use the specialized product command for deeper product catalog crawling:

```bash
scout products "top products" \
  --site lacoste.com \
  --limit-per-category 10 \
  --max-categories 10 \
  --output-dir ./scout-runs/lacoste-products
```

## High-Level HTTP

```bash
curl -s -X POST http://localhost:8421/run/company \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${SCOUT_API_KEY:-dev-key}" \
  -d '{
    "query": "Adobe",
    "mode": "auto",
    "output_dir": "./scout-runs/adobe-company"
  }'
```

## Frontend

The legacy local app route exists at:

```text
http://localhost:8421/app
```

The app UI is not a launch-certified product surface. Use it only when the user
explicitly asks for the local visual/status surface. Prefer CLI, HTTP, Docker,
or hosted API examples for beta launch guidance.

## Use Cases

### Company

Use for official website, about page, leadership, socials, and key URLs.

Output records: `company.v1`, `executive.v1`, `company_social.v1`.

### PRISM

Use for Algolia prospect research bundles: company, exec, investor, careers,
hiring, and news.

### Investor

Use for investor relations pages, reports, presentations, filings, financial
events, and source URLs.

Output record: `investor_asset.v1`.

### Careers

Use for careers pages, ATS detection, departments, open role categories, and
hiring signals.

Output record: `career_site.v1`.

### Jobs

Use for job extraction, matching, scoring, monitoring, and quality filtering.
Do not auto-apply. Keep private profiles outside the public repo.

Output record: `job_posting.v1`.

### Products

Use for product/category extraction and Algolia-ready records. Prefer explicit
target domains or known category URLs. If a hard site is blocked, try:

1. `scout products ... --site <domain>` with Crawl4AI.
2. `--stealth` if normal rendering is blocked.
3. browser fallback only for blocked product pages.
4. host WebFetch/browser evidence when the skill host can see content.

### News

Use for newsroom/blog/recent announcement signal extraction.

Output record: `news_signal.v1`.

### Research

Use for generic page, site, document, website-quality, documentation, and market
research workflows.

Output record: `research_record.v1`.

## Validation Target Matrix

Use the balanced target matrix when designing tests or examples:

- Private B2B SaaS: Algolia, Constructor
- Private retail commerce: L.L.Bean, Patagonia
- Public companies: Adobe, Home Depot
- Specialized primary targets: Estée Lauder, British Airways
- Secondary targets: Nike, Amplience, Salesforce, Intuit

## Artifact Contract

Every `scout run` workflow writes:

```text
manifest.json
records.json
records.jsonl
source_pages.json
blocked_pages.json
validation.json
extraction_report.md
```

Product-specific deep crawls also write Algolia artifacts under `algolia/`.

## Citations

Treat `source_pages.json` as the source registry. It contains deterministic
`source_id` values, source/final URLs, provider, fetch status, blocked/error
state, title, content hashes, and content availability flags.

Treat record-level `citations[]` as the field-level bridge back to evidence.
Each citation should identify `source_id`, `source_url`, `field`, `claim`,
`snippet`, optional `selector`, and `confidence`.

If a record has no citations, mention that caveat. Scout also writes
`missing_citations` warnings to `validation.json`.

## Answering Users

When returning Scout results, include:

- command or endpoint used,
- output directory,
- record counts and artifact paths,
- source URLs, source IDs, and citation coverage,
- blocked-page or sparse-content caveats.
