# ADR: Scout ICP (layered) and the final use-case set

- **Date:** 2026-06-13
- **Status:** Accepted (decided with Arijit). Builds on `2026-06-12-scout-scope-boundary.md` (acquire + extract, never interpret).

## ICP — concentric rings, one engine

Scout serves an expanding ring of users over time; Phase C builds the innermost ring and keeps the outer doors cheap to open, not built.

| Ring | Who | When | Face used |
|---|---|---|---|
| **0** | Arijit (operator) + the `algolia-intel-*` / `algolia-search-audit` skills | **now — Phase C** | Intelligence |
| **1** | Algolia field team (SEs/AEs/BDRs) | next, on pull | Intelligence (multi-user added then) |
| **2** | External / sellable | horizon, doors-open | **Core** |

**Reconciliation of "all three ICPs" + "defer commercial":** build for Ring 0 now; do not build tenancy, pricing, or onboarding; but keep cheap-to-retrofit the seams that are expensive later — per-record provenance (have), secrets isolation (keychain, planned), a Core API surface kept distinct from Intelligence verticals, and tenant/run ids on storage.

## Two faces of one engine

- **Intelligence face** — typed, Algolia-sales-shaped verticals that feed PRISM/skills. Does NOT generalize to arbitrary buyers. This is Rings 0–1.
- **Core face** — general crawler primitives ("websites → typed records → evidence, with a human-in-the-loop unblock ladder"). This DOES generalize and is the external wedge (Ring 2). It is the Firecrawl/Apify-plus surface.

**Key consequence:** `docs` and `research` are NOT deprioritized-to-death — they are demoted out of the Intelligence verticals into the Core face, where they are the seeds of the sellable product. "Keep doors open" concretely means: keep Core primitives first-class, clean, and documented even though Phase C build effort goes to Intelligence verticals.

## Final use-case set

### Intelligence verticals (Phase C breadth-first; each has a committed consumer)
| # | Vertical | Consumer skill | Notes vs prior list |
|---|---|---|---|
| 1 | products | SE demo indexing | live; quality fixes pending |
| 2 | company | intel-company | **absorbs `social`** (URL verification = a `verified` flag on socials, not a use case) |
| 3 | careers | intel-hiring | |
| 4 | news | intel-news | |
| 5 | investor & filings | intel-investor | **merged**: IR asset inventory (discovery depth) + 10-K/10-Q sections & verbatim transcript quotes (read depth) |
| 6 | tech-stack | intel-techstack | **NEW** — DOM/network fingerprinting only; BuiltWith (paid) stays in skill |
| 7 | site-signals | search audit | **renamed** from "website-quality" — Scout measures, never grades |
| 8 | search-probe | audit-browser | **NEW** — run consumer-supplied queries on the prospect's own search via embedded browser; capture results+screenshots; rating stays in skill |

### Composition
- **bundle** — runs verticals across N targets; includes a **competitor-set variant** (consumer picks competitors; Scout runs the same contracts on each, emits comparison-ready merged output). Scout never selects or ranks competitors.

### Core face (kept clean; NOT built breadth-first in Phase C)
- scrape, crawl, map, extract, screenshot (exist as modes)
- `research` = fetch+extract a given URL list (was a "vertical"; it's a primitive)
- `docs` = doc-site taxonomy + page inventory (general crawler / RAG capability; no intel consumer)

## Boundary reminders for the new verticals
- **tech-stack:** detect vendors from page scripts / network calls / headers / cookies / global JS objects. NOT historical/removed tech, NOT market share, NOT paid-API enrichment.
- **search-probe:** capture behavior (result count, zero-results, top titles, timing, screenshot). NOT relevance rating, NOT query selection (consumer supplies the query mix), NOT scoring.
- **competitor bundle:** Scout runs contracts on a given list. Choosing/ranking competitors is interpretation — stays in the consumer.
