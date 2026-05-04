# Scout

Standalone web intelligence platform. Exposes scrape, crawl, map, extract, and screenshot capabilities as a FastAPI HTTP service and a Python library.

## Capabilities

| Endpoint | What it does |
|---|---|
| `POST /scrape` | Fetch a single page — returns clean markdown + metadata |
| `POST /crawl` | BFS deep crawl from a start URL — returns all pages up to `max_depth` / `max_pages` |
| `POST /map` | URL discovery via robots.txt → sitemap.xml → sub-sitemaps, BFS fallback for sites without a sitemap |
| `POST /extract` | Structured data extraction — LLM-based (any schema, any page) or CSS selector-based (fast, no API key) |
| `POST /screenshot` | Full-page screenshot, returns base64 PNG |
| `GET /health` | Liveness check, no auth required |

## Quick Start

```bash
# Install
pip install -e .

# Configure
cp .env.example .env
# Edit .env: set SCOUT_API_KEY and optionally LLM_API_KEY

# Run
python3 -m uvicorn scout.api.main:app --host 0.0.0.0 --port 8421

# Verify
curl http://localhost:8421/health
```

## Authentication

All endpoints except `/health` require `X-API-Key: <your-key>` header.

## Extract Modes

Scout's `/extract` endpoint supports two strategies:

**LLM extraction** — works on any arbitrary page, no prior knowledge of DOM structure needed:
```json
{
  "url": "https://example.com",
  "schema": {"type": "object", "properties": {"title": {"type": "string"}}},
  "instruction": "Extract the page title and description",
  "llm_provider": "openai/gpt-4o-mini"
}
```
Requires `LLM_API_KEY` to be set server-side.

**CSS extraction** — fast, free, no API key, requires known page structure:
```json
{
  "url": "https://example.com",
  "css_schema": {
    "name": "page",
    "baseSelector": "body",
    "fields": [
      {"name": "title", "selector": "h1", "type": "text"}
    ]
  }
}
```
Used automatically when `LLM_API_KEY` is not configured.

## Running Tests

```bash
# Unit tests (mocked, fast)
python3 -m pytest tests/unit/ -v

# Integration tests (live network, real browser — ~30-60s)
python3 -m pytest tests/integration/ -v -m integration
```

## Docker

```bash
docker compose up
curl http://localhost:8421/health
```

## Attribution

This product includes software developed by UncleCode (https://x.com/unclecode) as part of the Crawl4AI project (https://github.com/unclecode/crawl4ai), licensed under the Apache License 2.0.
