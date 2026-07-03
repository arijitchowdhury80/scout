# Scout Acquisition Contracts — Shared Rules

Governing ADR: `docs/decisions/2026-06-12-scout-scope-boundary.md` (acquire + extract, never interpret).
Field contracts are mined from the algolia-intel-* skills (their web-acquirable halves); those skills are committed consumers.

## What every use case must satisfy

1. **Evidence on every field.** Every non-null extracted value carries a citation: source URL, fetched-at timestamp, and (where applicable) a verbatim snippet. No naked values, no fabrication, no placeholder text ("Pending", "TBD"). A field Scout could not extract is `null` — never guessed.
2. **Verbatim or nothing.** Quotes and document sections are exact text from the fetched source. Scout never paraphrases. (Consumers may paraphrase; they mark it themselves.)
3. **Confidence is earned, not declared.** Confidence derives from acquisition quality (direct fetch of primary source > feed metadata > search-result snippet), computed by documented rules per use case. The 0.35 fake-seed era is over: a record with confidence < 0.5 must say *why* in its evidence.
4. **Tags are additive and deterministic.** Keyword/topic/role-pattern tags may be attached (greppable, unit-testable rules). Tags never filter output at source; all extracted items are always returned. No significance ranking, no ICP scoring, no "relevance" prose — those are consumer judgments.
5. **Target-agnostic.** Every contract accepts one target or a list (`RunRequest.targets`). Competitor coverage = same contract, more targets.
6. **Blocked is a result.** A blocked page produces a `BlockedPage` record with evidence and the escalation options (embedded live browser, user browser). Zero records + documented blocking is a valid, honest run.
7. **Standard artifact set** per run: `manifest.json`, `records.json` + `records.jsonl`, `source_pages.json`, `blocked_pages.json`, `extraction_report.md`, plus `browser/` evidence when a browser ladder rung was used.
8. **Acquisition etiquette:** robots.txt honored by default (logged override available), stable identifying user-agent, per-domain delay (default 1s), pages-per-run cap. (Compliance ADR to formalize in Phase C0.)

## Discovery doors available to all use cases

Sitemap.xml → homepage nav/footer parse → canonical path probing → RSS/Atom autodiscovery → public web search (discovery only — found URLs are then fetched directly) → SEC EDGAR (public API door, filings use case) → browser ladder for blocked fetches.

Out of bounds everywhere: vendor/licensed data APIs (BuiltWith, SimilarWeb, Yahoo Finance, Tavily, Apify actors), LinkedIn/Twitter scraping (URL verification only — ToS posture), any LLM-generated narrative about meaning.

## Spec format per use case

Each spec defines: **Input contract** (target forms accepted) · **Acquisition plan** (pages/documents fetched, discovery method, escalation) · **Record types & fields** (marked F = direct extraction; T = deterministic tag) · **Confidence rules** · **Golden e2e flow** (testable assertion, becomes a Playwright test in Phase C) · **Consumer** (which algolia-intel-* skill migrates onto it).

## Use-case index

Use-case set and ICP rationale: `docs/decisions/2026-06-13-scout-icp-and-use-case-set.md`. Two faces — **Intelligence verticals** (below, built breadth-first in Phase C) and **Core modes** (`docs/specs/core-modes.md`, the general-crawler / Ring-2 surface, not built breadth-first).

| Spec | Vertical | Status today | Consumer skill |
|---|---|---|---|
| 01 | company (incl. social URL-verification) | stub | algolia-intel-company (+ -social verify half) |
| 02 | careers | stub | algolia-intel-hiring |
| 03 | news | stub | algolia-intel-news |
| 04 | investor & filings (merged) | stub / absent | algolia-intel-investor |
| 05 | tech-stack (NEW, DOM/network only) | absent | algolia-intel-techstack (DOM half) |
| 06 | search-probe (NEW, needs embedded browser) | absent | algolia-audit-browser |
| 10 | products | LIVE | SE demo indexing |
| 11 | bundle (incl. competitor-set variant) | stub | PRISM / algolia-audit-research |

Demoted to Core modes (`core-modes.md`), not Intelligence verticals: `research` → list-fetch primitive; `docs` → docs-map (deferred). Folded in: `social` → company (`verified` flag on socials).
