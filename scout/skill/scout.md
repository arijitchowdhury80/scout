---
name: scout
description: Use Scout to fetch, crawl, extract structured data from, map, or screenshot any URL. Scout is a self-hosted web intelligence platform running at http://localhost:8000. Use it whenever you need to read a webpage, discover URLs on a site, extract structured data, or capture a visual screenshot.
---

# Scout — Web Intelligence Skill

Scout is your self-hosted web crawler. It runs locally at `http://localhost:8000`. Use it to fetch web pages, crawl sites, extract structured data with a schema, discover URLs, or capture screenshots.

**All requests require the `X-API-Key` header.** Read the key from the `SCOUT_API_KEY` environment variable. Default for local dev: `dev-key`.

---

## When to use which endpoint

| Task | Endpoint |
|---|---|
| Read a single page → get clean markdown | `/scrape` |
| Read multiple pages across a site | `/crawl` |
| Extract structured fields (CEO name, job listings, etc.) | `/extract` |
| Discover all URLs on a site before crawling | `/map` |
| Capture a visual screenshot of a page | `/screenshot` |
| Check if Scout is running | `/health` |

---

## /scrape — Fetch a single URL

**When**: You need the content of one page as clean markdown.

```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{
    "url": "https://nike.com/about/leadership",
    "formats": ["markdown"],
    "use_js": false,
    "timeout_ms": 30000
  }'
```

**Request fields:**
- `url` (required) — the URL to fetch
- `formats` — list of `"markdown"`, `"raw_html"`, `"screenshot"`. Default: `["markdown"]`
- `use_js` — enable Playwright browser for JS-rendered pages. Default: `false`
- `wait_for` — CSS selector or JS expression to wait for before extracting. Default: `""`
- `timeout_ms` — page load timeout. Default: `30000`

**Response fields:**
- `success` — true/false
- `url` — final URL after redirects
- `markdown` — clean filtered content (always populated on success)
- `raw_html` — only if `"raw_html"` in formats
- `screenshot_base64` — base64 PNG, only if `"screenshot"` in formats
- `links` — list of all hrefs on the page
- `metadata` — `{url, crawled_at, title, description, language, word_count, token_estimate}`
- `error` — error message if `success=false`
- `duration_ms` — wall time

---

## /crawl — Recursively crawl a site

**When**: You need content from multiple pages (e.g., all docs pages, all blog posts).

```bash
curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{
    "url": "https://docs.example.com",
    "max_depth": 2,
    "max_pages": 20,
    "url_pattern": "*/docs/*",
    "include_external": false
  }'
```

**Request fields:**
- `url` (required) — start URL
- `max_depth` — BFS depth limit. Default: `2`
- `max_pages` — total page cap. Default: `10`
- `url_pattern` — glob pattern to filter which URLs to follow. Default: `""` (all internal)
- `include_external` — follow links to other domains. Default: `false`
- `use_js` — enable JS rendering for all pages. Default: `false`
- `timeout_ms` — per-page timeout. Default: `60000`

**Response fields:**
- `success`, `start_url`, `total_pages`, `error`, `duration_ms`
- `pages` — list of `{url, markdown, metadata, success, error}`

---

## /extract — Extract structured data with a schema

**When**: You need specific fields from a page (CEO name, list of job titles, investor names, etc.).

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{
    "url": "https://nike.com/about/leadership",
    "schema": {
      "type": "object",
      "properties": {
        "executives": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "title": {"type": "string"}
            }
          }
        }
      }
    },
    "instruction": "Extract the names and titles of all C-suite executives listed on this page.",
    "llm_provider": "gemini/gemini-2.0-flash"
  }'
```

**Request fields:**
- `url` (required)
- `schema` (required) — JSON Schema object describing the shape to extract
- `instruction` (required) — natural language instruction for the LLM
- `llm_provider` — LiteLLM provider string. Default: `"gemini/gemini-2.0-flash"`
- `use_js` — Default: `false`
- `timeout_ms` — Default: `45000`

**Response fields:**
- `success`, `url`, `error`, `duration_ms`
- `data` — dict matching your schema (empty `{}` if extraction failed)
- `markdown` — raw page content as fallback
- `metadata`

**Note:** Requires `LLM_API_KEY` set in Scout's environment.

---

## /map — Discover URLs without fetching content

**When**: You want to understand a site's structure before deciding what to crawl.

```bash
curl -X POST http://localhost:8000/map \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{
    "url": "https://example.com",
    "max_pages": 100,
    "url_pattern": "",
    "include_external": false
  }'
```

**Response fields:**
- `success`, `start_url`, `total`, `error`, `duration_ms`
- `urls` — list of discovered URL strings

---

## /screenshot — Capture a visual screenshot

**When**: You need to see what a page looks like, compare before/after, or verify a design.

```bash
curl -X POST http://localhost:8000/screenshot \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{
    "url": "https://example.com",
    "full_page": true,
    "viewport_width": 1280,
    "viewport_height": 800,
    "use_js": true
  }'
```

**Response fields:**
- `success`, `url`, `error`, `duration_ms`, `width`, `height`
- `screenshot_base64` — base64-encoded PNG

To view: decode and save as `.png`, or display inline if your tool supports it.

---

## /health — Check Scout is running

```bash
curl http://localhost:8000/health
# {"status": "ok", "crawl4ai_version": "0.7.7", "scout_version": "0.1.0"}
```

No `X-API-Key` required.

---

## Common patterns

**Read a page with JS rendering (SPAs, dynamic content):**
```json
{"url": "https://example.com", "use_js": true, "wait_for": ".main-content"}
```

**Extract a list of job postings:**
```json
{
  "url": "https://company.com/careers",
  "schema": {"type": "array", "items": {"type": "object", "properties": {"title": {"type": "string"}, "location": {"type": "string"}, "department": {"type": "string"}}}},
  "instruction": "Extract all job postings with title, location, and department."
}
```

**Crawl only specific sections of a site:**
```json
{"url": "https://docs.example.com", "url_pattern": "*/api/*", "max_depth": 3, "max_pages": 50}
```

---

## Starting Scout locally

```bash
cd /Users/arijitchowdhury/AI-Development/Scout

# Option 1: Direct (fastest for dev)
cp .env.example .env  # edit SCOUT_API_KEY and LLM_API_KEY
uvicorn scout.api.main:app --reload

# Option 2: Docker
cp .env.example .env
docker compose -f docker/docker-compose.yml up -d
```

---

## Error handling

All endpoints return `success: false` with an `error` string rather than HTTP error codes when the crawl itself fails (network error, timeout, blocked). Only auth failures (403) and malformed requests (422) return non-200 HTTP status codes.
