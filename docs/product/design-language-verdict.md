# Design-Language Verdict — Scout site, 2026-07-06

**Question Arijit asked:** the site "looks like a science project." Is the current design language the
problem — polish it, or replace it? Evidence base: `docs/competitor-crawl/firecrawl/` (Scout-crawled
Firecrawl) + live screenshots of Scout's own home + beta pages.

## The honest read
Scout's current language (the "Flux" system) is **brutalist/editorial**: giant black **condensed
uppercase** display type dominating every hero, grid-paper background, monochrome black-on-white with a
faint gold accent. It is *deliberate and competently executed* — this is not amateur CSS. But it is
**mis-targeted for a developer API product.** It signals "design-forward experiment / manifesto,"
not "production infrastructure you can bet your data pipeline on."

Side-by-side with Firecrawl (the category leader Scout is chasing), five gaps make Scout read as a
science project:

| Dimension | Firecrawl (works) | Scout (current) |
|---|---|---|
| **Hero** | A **working demo widget** (scrape box, tabs, "Start scraping") — the product IS the hero | A wall of giant uppercase text; no interactive element above the fold |
| **Tone** | Warm, calm, sentence-case, generous whitespace | Loud, shouting UPPERCASE, dense, intimidating |
| **Trust** | GitHub stars, "150,000+ companies", YC, SOC-2, customer logos | No social proof anywhere |
| **Color** | Near-white + one confident accent | Harsh monochrome + faint gold |
| **Depth** | 1,000–2,700-word landers, per-capability pages, deep docs | Thin pages, hand-rolled docs |

## Verdict: REPLACE the language (my recommendation — your call)
Polishing copy on top of the brutalist skin won't fix the trust problem; the skin itself is the
signal. Recommend moving to a **clean, warm, developer-trust aesthetic** — Firecrawl / Linear /
Mintlify-adjacent — while **keeping Scout's real differentiator** (evidence-grade, citable records)
and its **amber/gold accent** (a clean visual distinction from Firecrawl's orange).

Concretely:
1. **New skin:** light surface, one confident amber accent, humanist sans, **sentence-case** headers,
   lots of whitespace. Retire the condensed-uppercase-everything and grid-paper.
2. **Demo-as-hero:** surface Scout's existing playground above the fold with a URL box + "Run it."
3. **Trust scaffolding:** GitHub, "built on Crawl4AI," evidence/citation proof points, room for logos
   + testimonials as they arrive.
4. **Adopt Mintlify for docs** (or Fumadocs) instead of hand-rolled — buys search, copy-page,
   `llms.txt`, versioning, i18n, and category-standard credibility for near-zero effort.
5. **Per-capability landing pages** (scrape / crawl / map / products / intelligence) + a content engine
   (guides, use-cases, comparisons) to close the depth gap.

## What NOT to lose
The "**turn messy web pages into citable, downstream-ready records**" positioning is stronger than
Firecrawl's "clean markdown" — it's Scout's moat (proof, citations, blocked-page notes, typed records).
The redesign changes the *skin and structure*, not the *substance*. Keep the substance; make it look
like something a CTO would approve for production.

## Open decision for Arijit (HITL gate)
- **A. Full replace** (recommended): new design language + Mintlify docs, modeled on the trust-first
  category standard, keeping Scout's amber + evidence positioning.
- **B. Middle:** keep a toned-down version of Flux (kill the uppercase/grid, warm it up) but no full
  rebrand; still adopt Mintlify docs + demo-as-hero.
- **C. Polish only:** keep the current language, just fix copy + add content. (I do not recommend this —
  it leaves the core trust signal broken.)
