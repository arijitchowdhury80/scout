# ADR: Scout scope boundary — acquire + extract, never interpret

- **Date:** 2026-06-12
- **Status:** Accepted (decided with Arijit in session; supersedes the implicit "Scout = target's own web presence" framing)
- **Context:** Scout had absorbed 9 intelligence use cases as stubs, raising the question of whether it was swallowing PRISM and the algolia-search-audit sub-skills. A boundary drawn by *topic* (company, hiring, finance) or by *source domain* (the target's own site) proved hazy — 10-Ks live on EDGAR, interviews on third-party sites, competitor signals on competitor sites, yet all are clearly "gathering."

## Decision

The boundary is drawn by **kind of work**, not by topic or source domain:

| Layer | Work | Owner |
|---|---|---|
| 1. **Acquire** | Find and fetch bytes from the open web: pages, PDFs, filings, transcripts, feeds. Discovery (sitemaps, search, EDGAR lookup) and unblocking (crawler → stealth browser → embedded live browser → user browser). | **Scout** |
| 2. **Extract** | Turn bytes into structured, verbatim, cited records: document sections, exec quotes (speaker/date/source), leadership lists, job listings, news items, product records. Deterministic; nothing invented; every field traceable to a source. | **Scout** |
| 3. **Interpret** | Decide meaning: which quote is a signal, Algolia value mapping, vertical classification, scoring, competitor selection and comparison, pitches, campaigns. | **PRISM / algolia-search-audit skills** |

**One-line rule: Scout gathers and structures evidence; it never has an opinion.**

## Sub-decisions

1. **Licensed/vendor data APIs stay out of Scout** (SimilarWeb, BuiltWith, Yahoo Finance, Crunchbase). Scout's doors are open-web only — including public APIs that are merely doors to public documents (SEC EDGAR, RSS/Atom, sitemaps). Vendor-analytics MCPs remain in the skills/PRISM layer.
2. **Document intelligence is IN, as a first-class use case**: filings & transcripts — EDGAR + IR discovery, 10-K/10-Q section extraction (MD&A, risk factors), earnings-call and interview transcript acquisition, verbatim quote records. This is the largest scope addition vs. today and is explicitly extraction, not interpretation.
3. **Quote topic-tagging is allowed, additive-only**: deterministic keyword/topic tags (e.g. search, digital, personalization) may be attached to extracted quotes. Tags never filter at source — all quotes are always returned; consumers may ignore tags. Significance ranking is interpretation and stays out.
4. **Scout is target-agnostic**: "competitor intelligence" is the same acquisition contracts run against more targets (`RunRequest.targets`). Choosing the competitor list is interpretation and happens upstream.
5. **The algolia-intel-* skills are committed consumers**: as each Scout use case goes live, the matching skill's fetch logic (WebFetch/Apify) is replaced by a Scout call. Skills keep their reasoning prompts. This is a *split* of each skill (fetch half → Scout contract, brain half → stays), not a port.

## Consequences for the use-case registry

- `company`, `careers`, `news`, `investor`, `docs`, `website-quality`, `products` — confirmed, scoped as acquisition contracts (fields mined from the matching algolia-intel-* skill specs, web-acquirable subset only).
- **NEW: `filings` (filings & transcripts)** — added per sub-decision 2.
- `research` — narrowed to "fetch + extract from given URLs"; open-ended research synthesis is out of scope.
- `social` — URL-verification mode only (ToS posture) until reviewed.
- `prism` — redefined as the *prospect bundle*: a composition that runs the acquisition contracts across a target list (prospect + competitors). No synthesis inside it.
- `locations` — remains descoped.

## What Scout will never contain

Vertical classification, signal scoring, Algolia value mapping, business cases, playbooks, outreach campaigns, search-quality judgment (query relevance rating), competitor selection, any LLM-generated narrative about what evidence means.

## Open (explicitly deferred)

- Monetization/productization direction (evidence-engine vs crawl-to-index vs agent backend) — the boundary above keeps all three open; decide when there is a reason to.
- Whether Scout's embedded live browser later hosts the interactive search-audit testing flow (judgment-laden; currently out).
