---
name: scout
description: Use Scout to gather company intelligence from real websites. Scout is PRISM's purpose-built web intelligence platform at http://localhost:8421. It is NOT a general-purpose scraper — it is optimised for specific company intelligence use cases: About page, executive team, hiring openings, investor relations, and PDF reports/presentations. Always invoke Scout instead of WebFetch or raw curl when the goal is any of these five intelligence types, even when the user just says "find the leadership team" or "get their investor deck" without mentioning Scout explicitly. Scout handles JS-rendered pages, stealth mode, PDF extraction, and sitemap discovery that basic fetch tools cannot.
---

# Scout — Company Intelligence Platform

Scout is your intelligence layer for gathering specific, structured company data from websites. It runs locally at `http://localhost:8421` and wraps Crawl4AI with Playwright.

**Always check health first:**
```bash
curl -s http://localhost:8421/health
```
If not running: `cd /Users/arijitchowdhury/AI-Development/Scout && python3 -m uvicorn scout.api.main:app --host 0.0.0.0 --port 8421 &`

**Auth:** Every endpoint except `/health` needs `X-API-Key: dev-key`.

---

## Full Company Intelligence Profile

When asked to research a company, gather all five intelligence types in one run. **Map once, then scrape everything you need from that map.**

```bash
# Step 1: one map call — get the whole site structure
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com", "max_pages": 300}'

# Step 2: from the urls[] list, identify pages for each section:
#   - About/company: /about, /about-us, /company, /who-we-are
#   - Leadership: /team, /leadership, /management, /about/team, /about/leadership
#   - Careers: /careers, /jobs, /join-us
#   - Investors: /investors, /investor-relations, /ir
#   - PDFs: any urls ending in .pdf or /reports/, /presentations/

# Step 3: scrape each identified section — 5 scrape calls, one per intelligence type
```

**Output structure for a full profile:**
```markdown
## Company Intelligence — [Company] ([date])

### About
[mission, HQ, founding, size]

### Executive Team
| Name | Title |
|---|---|

### Open Roles
[department: role — location]

### Investor Relations
[IR page URL, stock ticker, earnings dates, SEC filings link]

### Reports & Documents
| Document | Type | URL |
|---|---|---|
```

---

## The Core Pattern: Map → Filter → Scrape

For a single intelligence type:
1. **Map** the domain to discover the URL structure
2. **Filter** results to the section you need
3. **Scrape** the relevant pages

Don't guess URLs. Map first — company sites vary wildly (`/team` vs `/about/leadership` vs `/company/management`).

```bash
# Step 1: discover the site
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com", "max_pages": 200}'

# Step 2: look through urls[] for the right section, then scrape it
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com/about/team", "use_js": true}'
```

---

## Intelligence Playbooks

### 1. About / Company Overview

**What you're looking for:** founding story, mission, product description, headquarters, company size.

**Common URL patterns:** `/about`, `/about-us`, `/company`, `/who-we-are`, `/our-story`

**Workflow:**
```bash
# Map with about filter
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com", "max_pages": 100, "url_pattern": "/about"}'

# Scrape the about page
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com/about", "use_js": true}'
```

If `/about` returns thin content (just a landing page), also scrape `/company` and `/mission`.

---

### 2. Executive / Leadership Team

**What you're looking for:** C-suite names + titles, board members, VP-level leadership.

**Common URL patterns:** `/team`, `/leadership`, `/management`, `/executives`, `/about/team`, `/about/leadership`, `/company/team`, `/company/leadership`

**Workflow:**
```bash
# Map and filter to team/leadership pages
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com", "max_pages": 100}'

# Then scrape the team page (try multiple URL patterns if needed)
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com/about/leadership", "use_js": true}'
```

Team pages often load via JS. If markdown is sparse, two options:
1. Add `"wait_for": ".team-grid"` (or similar selector) and retry
2. Use `"formats": ["raw_html"]` to get the full rendered HTML and parse names/titles from the markup — this reliably works when markdown conversion loses the structured card data:

```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com/about/leadership/", "use_js": true, "formats": ["raw_html"]}'
# Then parse the HTML: look for repeated card patterns, h3/h4 names, role/title spans
```

**Output format for exec intelligence:**
```markdown
## Executive Team — [Company]
| Name | Title |
|---|---|
| Jane Smith | CEO |
| John Doe | CTO |
```

---

### 3. Hiring / Open Roles

**What you're looking for:** open positions, departments, locations, job descriptions.

**Common URL patterns:** `/careers`, `/jobs`, `/work-with-us`, `/join-us`, `/join`, `/about/careers`

**Workflow:**
```bash
# Map careers section specifically
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com", "max_pages": 200, "url_pattern": "/careers"}'

# Crawl the careers section for individual job pages
curl -s --max-time 120 -X POST http://localhost:8421/crawl \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com/careers", "max_depth": 2, "max_pages": 30, "url_pattern": "/careers"}'
```

Many companies host jobs on third-party platforms (Greenhouse, Lever, Workday). Check if the careers page redirects to an external ATS — if so, note the ATS platform and scrape the careers landing page only (external job boards are not Scout's scope).

**Output format for hiring intelligence:**
```markdown
## Open Roles — [Company]
**[Department]**
- [Role Title] — [Location]
```

---

### 4. Investor Relations

**What you're looking for:** IR landing page, investor contact, financial calendar, press releases.

**Common URL patterns:** `/investors`, `/investor-relations`, `/ir`, `/financials`, `/shareholder-information`

**Workflow:**
```bash
# Map investor section
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com", "max_pages": 200, "url_pattern": "/investor"}'

# Scrape the IR landing page
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com/investors", "use_js": true}'
```

Extract: investor contact email, earnings call dates, stock ticker if public, links to SEC filings or annual reports.

---

### 5. Reports and PDF Documents

**What you're looking for:** annual reports, quarterly results, investor presentations, whitepapers, technical reports.

**Finding PDFs:**
```bash
# Map the full site or IR section to surface .pdf URLs
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com/investors", "max_pages": 200}'
# Then look for urls[] entries ending in .pdf or containing /reports/, /presentations/
```

**Scraping a PDF:**
Scout's /scrape handles PDFs natively — pass the direct PDF URL:
```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://company.com/reports/annual-2024.pdf"}'
```
Response includes extracted text as markdown.

**Output format for reports intelligence:**
```markdown
## Reports & Documents — [Company]
| Document | Type | URL |
|---|---|---|
| 2024 Annual Report | PDF | https://... |
| Q3 2024 Earnings Presentation | PDF | https://... |
```

---

## Multi-Company Intelligence (Batch)

When gathering the same intelligence type across multiple companies, run them sequentially — Scout is single-instance, not designed for parallel crawls:

```bash
for company in algolia.com adobe.com shopify.com; do
  echo "=== $company ===" 
  curl -s --max-time 60 -X POST http://localhost:8421/map \
    -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
    -d "{\"url\": \"https://$company\", \"max_pages\": 100}" | jq '.urls[] | select(test("team|leadership|about"))'
done
```

---

## API Quick Reference

| Endpoint | Use case | Timeout |
|---|---|---|
| `/scrape` | One page (including PDFs) | 45s |
| `/map` | Discover all URLs on a domain | 60s |
| `/crawl` | Multi-page deep crawl of a section | 120s |
| `/extract` | Structured fields via LLM or CSS selectors | 60s |
| `/screenshot` | Visual capture | 30s |

**When a page doesn't load:** add `"use_js": true`. For pages behind auth or aggressive bot detection, Scout's stealth mode activates automatically on retry.

**Error reference:**

| Error | Fix |
|---|---|
| `"Crawl failed"` / timeout | Add `"use_js": true`, increase `"timeout_ms"` |
| `"No LLM API key"` on /extract | Use `css_schema` instead, or set `LLM_API_KEY` in Scout's `.env` |
| HTTP 403 | Missing `X-API-Key: dev-key` header |
| HTTP 422 | Malformed request body — check JSON |
| Sparse/empty markdown | Page is JS-rendered — retry with `"use_js": true` |

---

## CLI Alternative

```bash
scout scrape https://company.com/about
scout map https://company.com --pages 200
scout crawl https://company.com/careers --depth 2 --pages 30
scout extract https://company.com/team --llm-key $GEMINI_API_KEY
```
