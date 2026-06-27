# Scout

Scout is a provider-agnostic web-to-record intelligence engine. Crawl4AI is the
default standalone acquisition provider, but Scout can also process content
supplied by host tools, browser sessions, saved HTML/DOM, PDF parsers, ATS
adapters, and future provider integrations.

Scout can run as a Python package, CLI, local HTTP service, Docker service, or
Claude/Codex skill backend.

Scout extracts clean web content, crawls site sections, captures screenshots,
and prepares reusable records for product catalogs, company intelligence, job
monitoring, investor research, and other web intelligence workflows.

## What Scout Does

| Capability | CLI | HTTP |
|---|---|---|
| Scrape one page to markdown/raw HTML | `scout scrape` | `POST /scrape` |
| Discover URLs on a site | `scout map` | `POST /map` |
| Crawl multiple pages | `scout crawl` | `POST /crawl` |
| Extract structured fields | `scout extract` | `POST /extract` |
| Capture screenshots | `scout screenshot` | `POST /screenshot` |
| Build Algolia product records | `scout products` | `POST /products` |
| Run high-level use-case workflows | `scout run <use-case>` | `POST /run/{use_case}` |
| Benchmark acquisition methods | `scout benchmark URL --output-dir DIR` | n/a |

## Release 0.1.1: Shared Acquisition Metadata

Scout `0.1.1` adds a backward-compatible acquisition metadata profile to the existing `POST /scrape` primitive. It does not add a consumer-specific endpoint. There is intentionally no `/ci/scrape`. CI, PRISM, products, jobs, and future consumers should all use Scout through the shared scrape contract.

Opt-in request fields:

```json
{
  "quality_analysis": true,
  "cleanup": true,
  "expected_markers": ["AI Search", "Product updates"],
  "recommend_collector": true,
  "source_id": "optional-source-id"
}
```

When any profile field is used, Scout may return:

```json
{
  "markdown": "default markdown",
  "raw_markdown": "raw evidence markdown",
  "clean_markdown": "cleaned markdown",
  "acquisition": {
    "schema": "acquisition_metadata.v1",
    "source_id": "optional-source-id",
    "content_hash": "...",
    "quality_score": 0.82,
    "quality_reasons": [],
    "markers_found": [],
    "markers_missing": [],
    "recommended_collector": "scout_scrape",
    "recommended_collector_reason": "browser_rendered_page"
  }
}
```

Default `/scrape` behavior is preserved: if the caller does not opt in, acquisition metadata remains empty and existing callers keep the old shape.

Use the benchmark harness before promoting Scout as the primary collector for a source:

```bash
scout benchmark https://example.com \
  --output-dir ./scout-runs/benchmarks/example \
  --no-js \
  --expected-marker "Example Domain"
```

The benchmark writes `benchmark.json`, `comparison.md`, `direct_http.txt`, `scout_raw.md`, `scout_clean.md`, and `samples/`. Scout should recommend `direct_http` for simple static pages, `rss_feed` for feed-like URLs, and `scout_scrape` for pages that benefit from browser-grade acquisition.

## Install

```bash
pip install git+https://github.com/arijitchowdhury80/scout.git
playwright install chromium
```

For local development:

```bash
git clone https://github.com/arijitchowdhury80/scout.git
cd scout
pip install -e ".[dev]"
playwright install chromium
```

## Run as a CLI

CLI commands run directly through the Python package. You do not need to start
the HTTP server first.

```bash
scout scrape https://example.com/about
scout map https://example.com --pages 200
scout crawl https://example.com/products --depth 2 --pages 50
scout products "men shirts" --site example.com --output-dir ./scout-runs/men-shirts
scout run jobs --profile examples/job-hunter/job-profile.yaml --output-dir ./scout-runs/jobs
scout run prism --query "Nike prospect intelligence" --mode auto --output-dir ./scout-runs/nike-prism
```

### Working Directory And Local Keys

For local development, keep secrets and machine-specific settings in
`.env.local`:

```bash
cp .env.example .env.local
```

Set:

```text
SCOUT_API_KEY=change-me
LLM_API_KEY=
SCOUT_WORKDIR=scout-runs
```

`.env.local` is ignored by git. Use it for local keys, default run storage, and
developer-only configuration. Use `.env` only for shared deployment defaults.

When `--output-dir` is provided, Scout writes exactly there. When `--output-dir`
is omitted, high-level CLI workflows and `scout products` derive a timestamped
run folder under `--workdir`, `SCOUT_WORKDIR`, or `./scout-runs`. In an
interactive terminal, Scout prompts:

```text
Where should Scout save run outputs, interim status, and local configs?
```

HTTP, Docker, scheduled jobs, and skill-driven runs cannot rely on interactive
prompts, so they should pass `output_dir`, pass `--workdir` through the CLI, or
set `SCOUT_WORKDIR` in `.env.local` or the deployment environment.

`scout run` is the high-level workflow surface for company, careers, products,
jobs, PRISM, investor, research, website-quality, docs, news, social, and
locations. Every run writes the same artifact contract so CLI, HTTP, scheduled
jobs, and the Claude/Codex skill can consume the output the same way.

Execution modes are explicit:

```bash
scout run company --query Adobe --mode auto --output-dir ./scout-runs/adobe-company
scout run careers --query Algolia --mode crawl4ai --output-dir ./scout-runs/algolia-careers
scout run investor --query Salesforce --mode saved --output-dir ./scout-runs/salesforce-investor
scout run products --query "top skincare products" --mode browser --output-dir ./scout-runs/estee-products
```

Supported modes are `auto`, `crawl4ai`, `webfetch`, `websearch`, `browser`,
`saved`, and `api`. `auto` starts with standalone acquisition and uses browser
fallback only after cheaper providers are unavailable or blocked.

If `scout run <use-case>` or `scout products` is run interactively without
`--output-dir`, Scout prompts for a working directory. In non-interactive use,
it writes under `SCOUT_WORKDIR` or `./scout-runs/`.

## Job Hunter

Job Hunter starts from a YAML profile that describes the roles, salary range,
locations, skills, excluded terms, industries, and target companies you care
about.

```bash
scout run jobs \
  --profile examples/job-hunter/job-profile.yaml \
  --output-dir ./scout-runs/job-hunter-demo
```

Job Hunter can also accept seed job URLs:

```bash
scout run jobs \
  --profile ./private-job-profile.yaml \
  --job-url https://job-boards.greenhouse.io/eve/jobs/4245857009 \
  --output-dir ./scout-runs/job-hunter-demo
```

The current V1 implementation loads profiles, writes normalized target company
records, detects job source platforms, extracts saved/fixture job page evidence,
scores job postings, and writes match/reject reasons. Live HTTP acquisition for
public job URLs, ATS-specific network adapters, company discovery, careers page
detection, and scheduled daily monitoring are the next build slices.

Private candidate profiles should stay outside the public repository. Keep them
in a local ignored file or vault-backed config and pass them with `--profile`.

See [examples/job-hunter/README.md](examples/job-hunter/README.md).

## Run as an HTTP Service

```bash
cp .env.example .env.local
scout serve
```

Open:

- `http://localhost:8421/` for a small status page
- `http://localhost:8421/app` for the Scout frontend
- `http://localhost:8421/docs` for Swagger API docs
- `http://localhost:8421/health` for health/version info

All endpoints except `/` and `/health` require:

```text
X-API-Key: dev-key
```

Set `SCOUT_API_KEY` in `.env.local` or the deployment environment before
exposing Scout beyond local development.

High-level workflows are available over HTTP:

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

The response includes the manifest and paths for `records.json`,
`records.jsonl`, `source_pages.json`, `blocked_pages.json`, `validation.json`,
and `extraction_report.md`.

The frontend at `/app` provides a self-educating Run Console, Product
Workbench, Evidence Browser, Records Explorer, and Algolia preparation panel.
Algolia credentials entered there are session-only and are not persisted.

`source_pages.json` is the source registry. It stores deterministic
`source_id` values, source/final URLs, provider, fetch status, blocked/error
state, content hashes, and content availability flags. Records in
`records.json` and `records.jsonl` include `citations[]` entries that point
back to those `source_id` values.

## Product Catalog to Algolia

```bash
scout products "top products" \
  --site esteelauder.com \
  --limit-per-category 10 \
  --max-categories 10 \
  --output-dir ./scout-runs/estee-lauder
```

Scout writes a discoverable run folder:

```text
scout-runs/estee-lauder/
  manifest.json
  urls.json
  extracted/products.raw.jsonl
  algolia/products.json
  algolia/products.ndjson
  algolia/settings.json
  report.md
```

`algolia/products.json` is a JSON array for inspection.
`algolia/products.ndjson` is newline-delimited for bulk indexing pipelines.
Each record includes a stable `objectID`, product URL, name, brand,
description, image fields, price/currency when detected, categories, and
`_source` provenance.

See [docs/product-to-algolia.md](docs/product-to-algolia.md).

## Intelligence Use Cases

Scout is intentionally broader than product scraping. The supported platform
surface is:

| Use case | Record types |
|---|---|
| `company` | `company.v1`, `executive.v1`, `company_social.v1` |
| `prism` | company, executive, social, investor, careers, news bundle |
| `investor` | `investor_asset.v1` |
| `careers` | `career_site.v1` |
| `jobs` | `job_posting.v1` |
| `products` | product records for Algolia indexing |
| `news` | `news_signal.v1` |
| `research` | `research_record.v1` |

See [docs/use-cases.md](docs/use-cases.md) and
[docs/execution-modes.md](docs/execution-modes.md). Validation targets are
tracked in [docs/target-matrix.md](docs/target-matrix.md), with an executable
registry in `scout.core.platform.targets`.

## Docker

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml up --build
curl http://localhost:8421/health
```

## Claude/Codex Skill

Scout can also be used as an agent skill. The skill lives at
`scout/skill/scout.md` and teaches an agent when to call the local Scout
service or CLI.

```bash
bash install-skill.sh
```

The skill is an integration layer. Scout itself remains independently
installable and usable from terminal, Docker, HTTP, and Python.

## Development

```bash
python3 -m pytest tests/unit/ -v
python3 -m pyright scout/
ruff check scout/ tests/
ruff format --check scout/ tests/
```

## Architecture

See [docs/architecture.md](docs/architecture.md).

## Attribution

This product includes software developed by UncleCode as part of the
[Crawl4AI](https://github.com/unclecode/crawl4ai) project, licensed under the
Apache License 2.0.
