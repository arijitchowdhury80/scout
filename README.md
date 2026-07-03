# Scout

Scout is a self-hosted web intelligence platform built on [Crawl4AI](https://github.com/unclecode/crawl4ai). It extracts clean web content, crawls site sections, captures screenshots, structures raw HTML, and prepares reusable records for product catalogs, company intelligence, job monitoring, investor research, and other web intelligence workflows.

Scout's strongest promise is not "another crawler." Scout is an owned acquisition workbench: it helps teams acquire web evidence, preserve what happened, escalate to browser/user-session capture when needed, turn messy pages into typed records, and write artifacts that downstream tools can trust.

Scout's public beta distribution is intentionally narrow: hosted HTTP API and Claude/Codex skill. The local package remains available to run the HTTP service for verification and private development.

## Why Scout

Hosted crawlers are excellent when you want managed scale and a simple scrape API. Scout is different: it is for users who need to own the acquisition workflow around the scrape.

Scout focuses on:

- evidence-first acquisition: source pages, blocked evidence, screenshots, reports, and artifacts;
- browser/session handoff: structure pages visible in a browser without pretending every block can be magically bypassed;
- records, not blobs: product, company, careers, investor, news, docs, research, and website-quality records;
- downstream readiness: Algolia preview/push, JSON/JSONL records, run folders, and agent/tool integration;
- local and self-hosted operation for workflows where control matters.

See:

- [Feature list](docs/product/feature-list.md)
- [Differentiation](docs/product/differentiation.md)
- [Private beta launch plan](docs/product/private-beta-launch-plan.md)
- [Distribution package plan](docs/product/distribution-package-plan.md)
- [Feature certification](docs/validation/feature-certification.md)
- [Legal readiness checklist](docs/legal/legal-readiness-checklist.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

## Current Status

Scout is ready for private beta testing with technical users. Core scrape/crawl/map/screenshot, captured-HTML structuring, product extraction on friendly sites, run artifacts, and Algolia preview/push are the strongest paths today.

Still beta/experimental: hard-site extraction reliability, user-browser capture workflows, broad vertical intelligence depth, MCP server, and public/commercial packaging.

## Launch Readiness And Decision Workflow

Current launch gate truth:

- Private beta: `ready_with_limits`
- Public launch: `ready`
- Current blockers: `0`

Use the launch readiness commands before making release or website claims:

```bash
scout launch-readiness
scout launch-readiness --json
scout launch-readiness --require-public
scout launch-decision-check --check-existing --check-drafts
```

Founder decision drafts live at
`docs/product/founder-decision-drafts/index.md`. These drafts are not approvals,
launch evidence, or completed decision records. They are review aids
that must be copied into the completed decision-record pattern, have placeholders
removed, and pass `scout launch-decision-check` before any release gate changes.

Primary launch references:

- [Launch status page](website/status.html)
- [Launch decision dashboard](docs/product/launch-decision-dashboard-2026-06-29.md)
- [Public launch action packet](docs/product/public-launch-action-packet-2026-06-29.md)
- [Founder decision drafts](docs/product/founder-decision-drafts/index.md)
- [Private beta invitation packet](docs/product/private-beta-invitation-packet.md)
- [Private beta tester handoff](docs/product/private-beta-tester-handoff.md)

## Quick Start

```bash
# Private beta install
pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation"
playwright install chromium

# Configure
cp .env.example .env.local
# Edit .env.local: set SCOUT_API_KEY, LLM_API_KEY, SCOUT_WORKDIR

# Start the local HTTP server
scout serve
# or: python -m uvicorn scout.api.main:app --host 0.0.0.0 --port 8421

# Verify
curl http://localhost:8421/health
```

`pip install scout-web` is reserved for the first package-registry release
after the license and publishing gates close.

Open `http://localhost:8421/` for the Scout launch website, or
`http://localhost:8421/docs` for Swagger API docs.

For the initial static product website, open:

```bash
open website/index.html
```

## Authentication

All endpoints except `/health` and `/` require the `X-API-Key` header:

```
X-API-Key: dev-key
```

Set `SCOUT_API_KEY` in `.env.local` before exposing Scout beyond local development.

## License

Scout's local/core package and source distribution are licensed under the
Apache License, Version 2.0 (`Apache-2.0`). Hosted Scout, paid service access,
support, private beta admission, and any future enterprise terms remain
separate service and commercial arrangements.

See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Attribution

Scout includes software developed by UncleCode as part of the Crawl4AI project:

> This product includes software developed by UncleCode (https://x.com/unclecode) as part of the Crawl4AI project.

Project URL: https://github.com/unclecode/crawl4ai

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before distributing Scout.

---

## API Reference

Scout exposes **15 HTTP endpoints** organized into four groups: Core Extraction, Intelligence Verticals, Run Artifacts, and Algolia Integration.

### Core Extraction Endpoints

These are the building blocks — each does one thing well.

---

#### `POST /scrape` — Single-Page Content Extraction

Fetch a single URL and return clean markdown, raw HTML, links, and metadata.

**Use case:** Extract clean text from any URL for LLM consumption, research pipelines, content monitoring, or competitive analysis.

**Request:**
```json
{
  "url": "https://example.com/about",
  "formats": ["markdown"],
  "use_js": false,
  "wait_for": "",
  "timeout_ms": 30000,
  "stealth": false,
  "headless": true,
  "proxy": null,
  "user_agent": null,
  "user_agent_mode": null,
  "override_navigator": false,
  "mean_delay": null
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | **required** | URL to scrape |
| `formats` | list | `["markdown"]` | Output formats: `markdown`, `raw_html`, `screenshot` |
| `use_js` | bool | `false` | Enable JavaScript rendering |
| `wait_for` | string | `""` | CSS selector to wait for before capture |
| `timeout_ms` | int | `30000` | Request timeout in milliseconds |
| `stealth` | bool | `false` | Enable stealth mode (simulate_user + UA rotation) |
| `headless` | bool | `true` | Run browser in headless mode |
| `proxy` | string? | `null` | Proxy URL (e.g. `http://user:pass@host:port`) |
| `user_agent` | string? | `null` | Explicit User-Agent string |
| `user_agent_mode` | string? | `null` | `"random"` rotates realistic UA per run |
| `override_navigator` | bool | `false` | Patch navigator to defeat headless fingerprinting |
| `mean_delay` | float? | `null` | Human-like pacing between actions (seconds) |

**Response:**
```json
{
  "success": true,
  "url": "https://example.com/about",
  "markdown": "# About Us\n\nWe are...",
  "raw_html": "<html>...</html>",
  "screenshot_base64": "",
  "links": ["https://example.com/team", "https://example.com/contact"],
  "metadata": {
    "url": "https://example.com/about",
    "crawled_at": "2026-06-22T...",
    "title": "About Us",
    "description": "...",
    "language": "en",
    "word_count": 450,
    "token_estimate": 600
  },
  "error": "",
  "duration_ms": 1284
}
```

**Example:**
```bash
curl -X POST http://localhost:8421/scrape \
  -H "X-API-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://stripe.com/about", "formats": ["markdown", "raw_html"]}'
```

---

#### `POST /crawl` — Multi-Page Site Crawl

Recursively crawl a site via BFS and return all discovered pages as markdown.

**Use case:** Index entire sites for knowledge bases, documentation scraping, content audits, or building training datasets.

**Request:**
```json
{
  "url": "https://docs.example.com",
  "max_depth": 2,
  "max_pages": 10,
  "url_pattern": "",
  "include_external": false,
  "use_js": false,
  "timeout_ms": 60000,
  "stealth": false
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | **required** | Starting URL |
| `max_depth` | int | `2` | Maximum crawl depth |
| `max_pages` | int | `10` | Maximum pages to crawl |
| `url_pattern` | string | `""` | Regex filter for discovered URLs |
| `include_external` | bool | `false` | Include external domain links |
| `use_js` | bool | `false` | Enable JavaScript rendering |
| `timeout_ms` | int | `60000` | Total crawl timeout |
| `stealth` | bool | `false` | Enable stealth mode |

**Response:**
```json
{
  "success": true,
  "start_url": "https://docs.example.com",
  "pages": [
    {
      "url": "https://docs.example.com/intro",
      "markdown": "# Introduction\n...",
      "metadata": { "url": "...", "crawled_at": "...", "title": "...", "word_count": 320 },
      "success": true,
      "error": ""
    }
  ],
  "total_pages": 8,
  "error": "",
  "duration_ms": 12500
}
```

**Example:**
```bash
curl -X POST http://localhost:8421/crawl \
  -H "X-API-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://docs.stripe.com", "max_depth": 2, "max_pages": 20}'
```

---

#### `POST /map` — URL Discovery (Sitemap)

Discover all URLs on a site without extracting content. Faster and cheaper than a full crawl.

**Use case:** Discover all pages before selective crawling — build URL inventories, detect site structure changes, find orphaned pages.

**Request:**
```json
{
  "url": "https://example.com",
  "max_pages": 100,
  "url_pattern": "",
  "include_external": false,
  "stealth": false
}
```

**Response:**
```json
{
  "success": true,
  "start_url": "https://example.com",
  "urls": [
    "https://example.com/about",
    "https://example.com/products",
    "https://example.com/blog"
  ],
  "total": 47,
  "error": "",
  "duration_ms": 7946
}
```

**Example:**
```bash
curl -X POST http://localhost:8421/map \
  -H "X-API-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://stripe.com", "max_pages": 200}'
```

---

#### `POST /extract` — Structured Data Extraction

Crawl a URL and extract structured data using CSS selectors or an LLM strategy.

**Use case:** Pull typed records from pages — product prices, contact info, job listings, event details — for databases and downstream processing.

**Request:**
```json
{
  "url": "https://example.com/products",
  "css_schema": {
    "baseSelector": "div.product",
    "fields": [
      {"name": "title", "selector": "h2", "type": "text"},
      {"name": "price", "selector": ".price", "type": "text"},
      {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"}
    ]
  },
  "instruction": "",
  "extraction_schema": {},
  "llm_provider": "ollama/llama3.2:3b",
  "use_js": false,
  "timeout_ms": 45000
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | **required** | URL to extract from |
| `css_schema` | dict? | `null` | CSS-based extraction schema (no LLM needed) |
| `instruction` | string | `""` | Natural language extraction instruction (requires LLM) |
| `extraction_schema` | dict | `{}` | JSON Schema for LLM-based extraction (alias: `schema`) |
| `llm_provider` | string | `"ollama/llama3.2:3b"` | Local/open-source provider target for instruction-based extraction |
| `use_js` | bool | `false` | Enable JavaScript rendering |
| `timeout_ms` | int | `45000` | Request timeout |

**Response:**
```json
{
  "success": true,
  "url": "https://example.com/products",
  "data": {"products": [{"title": "Widget", "price": "$29.99"}]},
  "markdown": "...",
  "metadata": { "url": "...", "crawled_at": "...", "title": "..." },
  "error": "",
  "duration_ms": 1305
}
```

---

#### `POST /structure` — Structure Pre-Fetched HTML

Process HTML you already have through Crawl4AI's extraction engine — no network fetch. Uses the `raw://` scheme internally so it never re-triggers bot walls.

**Use case:** Process captured HTML from browser sessions, saved files, or third-party sources without re-fetching. Critical for PRISM integration where pages were cleared by a human.

**Request:**
```json
{
  "html": "<html><body><h1>Products</h1><div class='product'>...</div></body></html>",
  "source_url": "https://example.com/products",
  "css_schema": {
    "baseSelector": "div.product",
    "fields": [
      {"name": "name", "selector": "h2", "type": "text"},
      {"name": "price", "selector": ".price", "type": "text"}
    ]
  },
  "llm_schema": null
}
```

**Response:**
```json
{
  "success": true,
  "source_url": "https://example.com/products",
  "markdown": "# Products\n\n## Widget A\n$29.99...",
  "records": [
    {"name": "Widget A", "price": "$29.99"},
    {"name": "Widget B", "price": "$49.99"}
  ],
  "record_count": 2,
  "word_count": 45,
  "error": "",
  "duration_ms": 677
}
```

---

#### `POST /screenshot` — Visual Page Capture

Capture a screenshot of any URL as a base64-encoded PNG.

**Use case:** Visual evidence for audits, competitive analysis screenshots, visual regression testing, generating thumbnails.

**Request:**
```json
{
  "url": "https://example.com",
  "full_page": true,
  "viewport_width": 1280,
  "viewport_height": 800,
  "wait_for": "",
  "use_js": true
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "screenshot_base64": "iVBORw0KGgo...",
  "width": 1280,
  "height": 2400,
  "error": "",
  "duration_ms": 1271
}
```

---

#### `POST /harvest` — Live Browser Tab Extraction via CDP

Attach Crawl4AI to an already-open Chrome tab over the Chrome DevTools Protocol and extract structured content without navigating away.

**Use case:** Extract from browser tabs that a human has already cleared past bot walls. No re-navigation, no wall re-trigger.

**Request:**
```json
{
  "cdp_url": "http://127.0.0.1:9222",
  "url": "https://target-site.com/page",
  "css_schema": null,
  "scan_full_page": true
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `cdp_url` | string | **required** | CDP endpoint (e.g. `http://127.0.0.1:9222`) |
| `url` | string | **required** | URL of the page currently open in the tab |
| `css_schema` | dict? | `null` | Optional CSS extraction schema for typed records |
| `scan_full_page` | bool | `true` | Scroll the full page before extraction |

**Response:** Same as `/structure` (`CaptureExtraction` model).

---

### Product Catalog Endpoint

#### `POST /products` — Product Catalog Extraction

Discover product pages on an ecommerce site and return normalized product records with stable `objectID`s.

**Use case:** Build searchable and reusable product catalogs from ecommerce
sites. Records include name, brand, price, images, categories, variants,
citations, and completeness scores. Output can be exported to JSONL, CSV,
SQLite, Google Sheets import files, and Algolia preparation/push workflows.

**Request:**
```json
{
  "site": "https://books.toscrape.com",
  "query": "fiction",
  "max_products": 100,
  "max_categories": 10,
  "limit_per_category": 10,
  "output_dir": "",
  "persist": false,
  "use_js": true,
  "timeout_ms": 60000,
  "stealth": false,
  "browser_fallback": true
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `site` | string | `""` | Target ecommerce site |
| `query` | string | `""` | Product search query |
| `start_url` | string | `""` | Direct start URL (overrides site+query) |
| `max_products` | int | `100` | Maximum products to extract |
| `max_categories` | int | `10` | Maximum category pages to discover |
| `limit_per_category` | int | `10` | Products per category page |
| `output_dir` | string | `""` | Where to save artifacts |
| `persist` | bool | `false` | Write artifacts to disk |
| `browser_fallback` | bool | `true` | Fall back to browser on bot blocks |
| `stealth` | bool | `false` | Enable stealth mode |

**Response:**
```json
{
  "success": true,
  "query": "fiction",
  "site": "https://books.toscrape.com",
  "start_url": "https://books.toscrape.com",
  "output_dir": "",
  "records": [
    {
      "objectID": "abc123def456",
      "name": "A Light in the Attic",
      "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
      "brand": "Books To Scrape",
      "description": "...",
      "image": "https://...",
      "images": [],
      "price": 51.77,
      "currency": "GBP",
      "categories": ["Books"],
      "hierarchicalCategories": {},
      "sku": "",
      "variants": [],
      "in_stock": true,
      "_source": {
        "url": "...",
        "extractor": "listing_card",
        "category_url": "...",
        "category_name": "Books"
      },
      "completeness_score": 0.65
    }
  ],
  "total_records": 5,
  "categories": ["Books"],
  "blocked_pages": [],
  "total_blocked_pages": 0,
  "files": {},
  "error": "",
  "duration_ms": 18093
}
```

**Quality pipeline:** Records go through junk filtering (CAPTCHA pages, error pages), canonical URL deduplication (strips variant/color/size params), and brand fallback (domain name extraction when brand is missing).

---

### Intelligence Verticals

#### `POST /run/{use_case}` — Run Intelligence Vertical

Run a high-level intelligence workflow. Each use case has a dedicated runner that knows which URLs to check, what patterns to extract, and how to structure the output.

**Request:**
```json
{
  "url": "https://stripe.com",
  "query": "",
  "mode": "auto",
  "targets": [],
  "output_dir": "",
  "max_targets": 25,
  "max_records": 250
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | `""` | Target company website |
| `query` | string | `""` | Search query or company name |
| `mode` | string | `"auto"` | Execution mode: `auto`, `crawl4ai`, `webfetch`, `websearch`, `browser`, `user-browser`, `saved`, `api` |
| `targets` | list | `[]` | Specific URLs to process |
| `output_dir` | string | `""` | Where to save artifacts |
| `max_targets` | int | `25` | Maximum target URLs |
| `max_records` | int | `250` | Maximum output records |

**Available use cases:**

| Use Case | What It Extracts | Example Target |
|----------|-----------------|----------------|
| `company` | Company profile, leadership, founding info, social links | `https://stripe.com` |
| `careers` | Open job listings, departments, locations, apply links | `https://stripe.com` |
| `investor` | Executive quotes from earnings calls, SEC filings, financial signals | `https://stripe.com` |
| `news` | Press releases, media mentions, recent events (last 60 days) | `https://stripe.com` |
| `research` | Blog posts, whitepapers, technical documentation | `https://stripe.com` |
| `social` | Social media profiles — LinkedIn, Twitter, Facebook, YouTube | `https://stripe.com` |
| `locations` | Office addresses, phone numbers, GPS coordinates | `https://stripe.com` |
| `website-quality` | SEO signals, structured data, accessibility, performance indicators | `https://stripe.com` |
| `prism` | **All 8 verticals above in one call** — full company dossier | `https://stripe.com` |
| `products` | Product catalog (delegates to `/products` engine) | `https://books.toscrape.com` |

**Response:**
```json
{
  "success": true,
  "use_case": "company",
  "output_dir": "./scout-runs/stripe-company-20260622-051234",
  "manifest": {
    "run_id": "run_a1b2c3d4",
    "use_case": "company",
    "started_at": "2026-06-22T05:12:34",
    "finished_at": "2026-06-22T05:12:52",
    "total_records": 3,
    "total_sources": 2,
    "total_blocked": 0,
    "artifacts": {
      "manifest": ".../manifest.json",
      "records_json": ".../records.json",
      "records_jsonl": ".../records.jsonl",
      "source_pages_json": ".../source_pages.json"
    }
  },
  "total_records": 3,
  "error": ""
}
```

**Example — full company dossier:**
```bash
curl -X POST http://localhost:8421/run/prism \
  -H "X-API-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://stripe.com", "mode": "auto"}'
```

---

### Run Artifact Endpoints

After a run completes, retrieve its results:

#### `GET /runs/{run_id}` — Run Summary

Returns the full run manifest with metadata, record/source/blocked counts, and artifact file paths.

#### `GET /runs/{run_id}/records` — Extracted Records

```json
{
  "run_id": "run_a1b2c3d4",
  "total": 3,
  "records": [{"objectID": "...", "name": "...", "url": "..."}]
}
```

#### `GET /runs/{run_id}/sources` — Source Pages

```json
{
  "run_id": "run_a1b2c3d4",
  "total": 2,
  "sources": [{"source_id": "src_...", "provider": "crawl4ai", "source_url": "..."}]
}
```

#### `GET /runs/{run_id}/artifacts` — Artifact File Paths

```json
{
  "run_id": "run_a1b2c3d4",
  "output_dir": "./scout-runs/stripe-company-...",
  "artifacts": {
    "manifest": "manifest.json",
    "records_json": "records.json",
    "records_jsonl": "records.jsonl"
  }
}
```

---

### Algolia Integration

#### `POST /algolia/preview` — Validate Records Before Push

Check that records have the required fields (`objectID`, `name`, `url`) and credentials are configured, before pushing to Algolia.

**Request:**
```json
{
  "app_id": "YOUR_APP_ID",
  "api_key": "YOUR_ADMIN_API_KEY",
  "index_name": "products",
  "records": [
    {"objectID": "1", "name": "Widget", "url": "https://example.com/widget"}
  ]
}
```

**Response:**
```json
{
  "ready": true,
  "index_name": "products",
  "record_count": 1,
  "sample_object_ids": ["1"],
  "missing_required_fields": [],
  "credentials": {
    "app_id_configured": true,
    "api_key_configured": true
  },
  "ingest_supported": true,
  "message": "Preview records before pushing to Algolia via POST /algolia/push."
}
```

#### `POST /algolia/push` — Push Records to Algolia

Push validated records to an Algolia index. Supports batching.

**Request:**
```json
{
  "app_id": "YOUR_APP_ID",
  "api_key": "YOUR_ADMIN_API_KEY",
  "index_name": "products",
  "records": [{"objectID": "1", "name": "Widget", "url": "..."}],
  "batch_size": 1000
}
```

**Response:**
```json
{
  "success": true,
  "index_name": "products",
  "records_pushed": 1,
  "object_ids": ["1"],
  "errors": []
}
```

---

### Utility Endpoints

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /health` | No | Service liveness — returns `{"status": "ok", "scout_version": "...", "crawl4ai_version": "..."}` |
| `GET /` | No | Landing page |

---

## Endpoint Validation

Scout ships with endpoint validation and a feature-certification gate. Endpoint
validation proves HTTP route behavior; feature certification proves each Scout
capability with expected-vs-actual records, sources, citations, artifacts, UI
state, and blocked/fallback evidence.

```bash
# Start Scout, then:
python tests/validate_endpoints.py

# Generate the full feature-certification matrix/report scaffold:
scout certify --output-root validation-output
```

The endpoint suite covers:
- Multiple queries per endpoint (valid inputs, edge cases, error handling)
- Success/failure criteria for every response field
- Auth enforcement verification
- Graceful degradation (invalid domains, missing CDP, fake Algolia credentials)

Before a private beta or launch claim, run the full certification gate described
in [docs/validation/feature-certification.md](docs/validation/feature-certification.md).

---

## Hosted HTTP Beta

Hosted beta admin scripts for the Chowmes VPS live in `scripts/`:

```bash
scripts/scout-hosted-admin generate-secret --label HOSTED_ADMIN_TOKEN
scripts/scout-hosted-admin generate-api-key --email tester@example.com --name "Tester Name" --key-name "Beta key"
scripts/scout-hosted-admin provision-key --email tester@example.com --name "Tester Name" --key-name "Beta key"
scripts/scout-hosted-admin list-accounts --format table
scripts/scout-hosted-admin list-purchases --format table

# Lower-level direct helpers remain available:
scripts/scout-vps-provision-hosted-key --email tester@example.com --key-name "Beta key"
scripts/scout-vps-list-hosted-accounts --format table
scripts/scout-vps-list-hosted-purchases --format table
```

See [docs/product/hosted-admin-operations.md](docs/product/hosted-admin-operations.md)
for the current API-key, credit, and billing status.

Execution modes: `auto`, `crawl4ai`, `webfetch`, `websearch`, `browser`, `user-browser`, `saved`, `api`.

---

For an internet-facing hosted/private-beta API, set:

```bash
SCOUT_PUBLIC_HOSTED_ONLY=true
HOSTED_ACCOUNT_DB_PATH=/data/hosted_accounts.sqlite
SCOUT_API_KEY=<strong-admin-key-not-dev-key>
```

Then give consuming apps hosted Bearer keys created with
`scout hosted-provision`. Public consumers should call `/v1/hosted/*` with
`Authorization: Bearer scout_live_...`; do not expose the local `X-API-Key`
surface as the public SaaS API.

Current private-beta VPS base URL:

```bash
SCOUT_HOSTED_BASE_URL=https://scout.chowmes.com
```

The VPS deployment is expected to keep Scout bound to `127.0.0.1:8421` behind
Caddy. Public callers use hosted Bearer keys only; local/admin `X-API-Key`
routes are disabled when `SCOUT_PUBLIC_HOSTED_ONLY=true`.

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"
playwright install chromium

# Run tests
python -m pytest tests/unit/ -v          # 367 unit tests
python -m pytest tests/integration/ -v   # integration tests (needs network)

# Quality checks
python -m pyright scout/                 # 0 errors required
ruff check scout/ tests/                 # linting
ruff format --check scout/ tests/        # formatting

# Full endpoint validation (requires running server)
python tests/validate_endpoints.py
```

---

## Architecture

```
scout/
├── api/                    # FastAPI application
│   ├── main.py             # App factory, lifespan, middleware
│   ├── config.py           # Settings (env vars)
│   ├── deps.py             # DI helpers (get_crawler, get_run_db)
│   ├── db.py               # RunDB — async SQLite persistence
│   └── routers/            # One file per endpoint group
│       ├── scrape.py       # POST /scrape
│       ├── crawl.py        # POST /crawl
│       ├── map.py          # POST /map
│       ├── extract.py      # POST /extract
│       ├── structure.py    # POST /structure
│       ├── harvest.py      # POST /harvest
│       ├── screenshot.py   # POST /screenshot
│       ├── products.py     # POST /products
│       ├── run.py          # POST /run/{use_case}
│       ├── runs.py         # GET /runs/{run_id}/*
│       ├── algolia.py      # POST /algolia/preview, /algolia/push
│       ├── health.py       # GET /health
│       ├── app_runs.py     # Service run sessions + SSE
│       ├── app_browser.py  # User browser CDP bridge
│       └── live_browser.py # Browser message handlers
├── core/
│   ├── types.py            # All Pydantic contracts
│   ├── crawler.py          # ScoutCrawler wrapper around Crawl4AI
│   ├── blocking.py         # Bot wall detection (PerimeterX, Cloudflare, etc.)
│   ├── capture_extract.py  # Structure captured HTML via raw://
│   ├── cdp_acquire.py      # CDP-based live tab extraction
│   ├── products/           # Product discovery + Algolia record building
│   ├── modes/              # Execution mode strategies
│   ├── platform/           # Run dispatcher, workspace, types
│   └── use_cases/
│       └── runners/        # Intelligence vertical runners
│           ├── company.py
│           ├── careers.py
│           ├── investor.py
│           ├── news.py
│           ├── research.py
│           ├── social.py
│           ├── locations.py
│           └── website_quality.py
├── cli/                    # Internal command entry points
└── skill/                  # Claude/Codex skill definition
```

See [docs/architecture.md](docs/architecture.md) for the full architecture document.

---

## Attribution

This product includes software developed by UncleCode
(https://x.com/unclecode) as part of the Crawl4AI project.
Crawl4AI is licensed under the Apache License 2.0.
