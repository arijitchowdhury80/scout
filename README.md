# Scout

Scout is a standalone web scraping and product intelligence platform built on
Crawl4AI. It can run as a Python package, CLI, local HTTP service, Docker
service, or Claude/Codex skill backend.

Scout extracts clean web content, crawls site sections, captures screenshots,
and prepares Algolia-ready product records from public product catalogs.

## What Scout Does

| Capability | CLI | HTTP |
|---|---|---|
| Scrape one page to markdown/raw HTML | `scout scrape` | `POST /scrape` |
| Discover URLs on a site | `scout map` | `POST /map` |
| Crawl multiple pages | `scout crawl` | `POST /crawl` |
| Extract structured fields | `scout extract` | `POST /extract` |
| Capture screenshots | `scout screenshot` | `POST /screenshot` |
| Build Algolia product records | `scout products` | `POST /products` |

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
```

If `scout products` is run interactively without `--output-dir`, Scout prompts
for a directory. In non-interactive use, it writes under `./scout-runs/`.

## Run as an HTTP Service

```bash
cp .env.example .env
scout serve
```

Open:

- `http://localhost:8421/` for a small status page
- `http://localhost:8421/docs` for Swagger API docs
- `http://localhost:8421/health` for health/version info

All endpoints except `/` and `/health` require:

```text
X-API-Key: dev-key
```

Set `SCOUT_API_KEY` in `.env` before exposing Scout beyond local development.

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
