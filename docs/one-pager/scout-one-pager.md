# Scout — Web Intelligence for the Algolia Field Team

**Scout turns any prospect's website into structured, citable sales intelligence — on your laptop, in minutes, with zero per-crawl SaaS fees.**

## What it is

Scout is a self-hosted web intelligence platform. You give it a company URL and a job to do — pull their product catalog, map their leadership team, find their careers page, collect their investor materials — and it crawls the site, extracts structured records, and saves everything with evidence: which page each fact came from, when it was fetched, and how confident the extraction is.

It runs entirely on your machine (one Python service + a browser engine). No Apify subscription, no per-result billing, no sending prospect research through a third-party scraping vendor.

## What it does

- **Product catalog extraction** — point Scout at a retailer's category page and get back **Algolia-ready product records** (objectID, name, brand, price, images, category hierarchy) as JSON, ready to index for a demo. *Live today.*
- **Company intelligence** — company profile, leadership, social presence, careers and ATS signals, investor relations assets, recent news. *Rolling out — UI and contracts are in place; live extraction is being built use case by use case.*
- **Hard-site handling** — when a WAF blocks the crawler (Estée Lauder, Nike-class sites), Scout says so honestly, preserves the blocked-page evidence, and offers a one-click escalation: it drives **your real Chrome browser**, captures what you see, and extracts records from that.
- **Evidence on everything** — every record carries source URLs, timestamps, and confidence scores. No naked numbers in front of a prospect.

## For Solutions Engineers

The slowest part of a killer demo is getting the prospect's own data into an index. Scout collapses that.

- "Build me a demo index from `prospect.com/collections/bestsellers`" → run Scout's products mode → records.json with names, prices, SKUs, images → push to an Algolia index. A morning of manual scraping becomes a coffee break.
- The blocked-page evidence is itself a talking point: you can show the prospect exactly which of their pages resist automated access — relevant to any data-ingestion conversation.
- Everything is reproducible: the same run config produces the same artifact set, so a demo built for discovery can be rebuilt for the POC.

## For Account Executives

Walk into the call knowing the account the way they know themselves.

- One run per prospect gives you a dossier folder: who runs the company, what they sell, where they're hiring, what they told investors — each fact linked to the page it came from, so nothing in your deck is hand-wavy.
- Catalog runs quantify the opportunity: "we extracted 4,000 SKUs across 12 categories from your site" is a concrete, evidence-backed opener about search and discovery scale.
- Because Scout is self-hosted, prospect research never leaves your machine — no vendor logs of which accounts you're working.

## For BDRs

Personalization at volume without the tab-hopping.

- Careers runs surface hiring signals (which teams are growing, which ATS they use) — natural relevance hooks for sequencing.
- News runs collect the last announcements with dates and links, so the "saw your launch last week" line is real and current.
- The target catalog and presets in the Scout app make repeat research a two-click operation: pick the account, pick the use case, run.

## Why it matters

| | Apify / SaaS scrapers | Manual research | **Scout** |
|---|---|---|---|
| Cost per run | Metered billing | Your afternoon | $0 marginal |
| Data residency | Vendor cloud | Your head | Your laptop |
| Output | Raw HTML/JSON | Notes | Typed records + citations |
| Repeatability | Per-actor config | None | Saved presets, same artifacts every run |

## Status & getting started

Scout is an internal tool under active development. Product catalog extraction is production-quality today; the company/careers/investor/news intelligence flows are being brought live use case by use case on the same engine. It runs locally: `scout serve`, open `http://localhost:8421/app`, pick a use case, paste a URL, Start Execution.

*Contact: Arijit Chowdhury · Repo: AI-Development/Scout · All extraction respects per-domain rate limits and robots.txt by default.*
