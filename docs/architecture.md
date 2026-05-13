# Scout Architecture

Scout has one engine and several front doors.

```mermaid
flowchart TD
    CLI["CLI: scout scrape/crawl/products"]
    HTTP["HTTP: scout serve :8421"]
    Skill["Claude/Codex Skill"]
    Python["Python Library"]

    Core["Scout Core\nPydantic contracts + async modes"]
    Crawl4AI["Crawl4AI + headless Playwright"]
    Artifacts["Run Artifacts\nmanifest, urls, raw, algolia, report"]
    Web["Public Websites"]

    Skill --> HTTP
    CLI --> Core
    HTTP --> Core
    Python --> Core
    Core --> Crawl4AI
    Crawl4AI --> Web
    Core --> Artifacts
```

## Runtime Modes

### CLI

CLI commands execute directly through the Python package. They do not require
the local HTTP server.

### HTTP Service

`scout serve` starts FastAPI on port `8421`. This mode is for agents, curl,
PRISM, external scripts, and browser-visible API docs.

### Skill

The skill is not the product. It is a playbook that tells Claude or Codex how
to use the running Scout service for research and product ingestion tasks.

### Browser Behavior

Scout does not depend on the user's visible browser. Crawl4AI launches headless
Chromium internally through Playwright when JavaScript rendering is needed.

## Product Crawl Flow

```mermaid
sequenceDiagram
    participant User
    participant Scout
    participant Map as Map Mode
    participant Scrape as Scrape Mode
    participant Export as Artifact Writer

    User->>Scout: scout products "men shirts" --site example.com
    Scout->>Map: discover URLs from sitemap/BFS
    Map-->>Scout: category and product URL candidates
    loop each product URL
        Scout->>Scrape: fetch markdown + raw HTML
        Scrape-->>Scout: metadata + JSON-LD HTML
        Scout->>Scout: normalize Algolia product record
    end
    Scout->>Export: write run folder
    Export-->>User: manifest + products.json + products.ndjson
```
