# Competitor Website Patterns

Date: 2026-06-28

## Repeated Website Sections

Most competitor websites use a similar conversion path:

1. **Hero** - one-sentence outcome, short support copy, primary CTA, secondary
   docs/GitHub/demo CTA.
2. **Code sample or terminal demo** - proves developer utility immediately.
3. **Product primitives** - scrape, crawl, search, extract, browser, proxy,
   storage, structured data.
4. **Use cases** - AI agents, RAG, research, ecommerce/product data, monitoring,
   competitive intelligence, lead enrichment.
5. **Trust/social proof** - logos, GitHub stars, customer quotes, benchmark
   numbers, enterprise security.
6. **Docs path** - quickstart, API reference, SDKs, examples.
7. **Pricing** - free trial, usage credits, team plan, enterprise plan.
8. **FAQ** - blocking, legality, rate limits, proxies, data privacy, self-hosting.
9. **Final CTA** - sign up, get API key, book demo, or install locally.

## What This Means For Scout

Scout should use the familiar structure, but not the same generic promise.

Recommended website spine:

1. **Hero:** "Turn messy web pages into citable, downstream-ready records."
2. **Split CTA:** "Install locally" and "Try hosted beta."
3. **Proof block:** terminal/API example showing scrape -> records -> artifacts.
4. **Acquisition ladder:** Crawl4AI, direct fetch, scout browser, user browser,
   saved HTML, API adapters.
5. **Evidence model:** source pages, blocked pages, citations, screenshots,
   extraction report.
6. **Record outputs:** products, company, PRISM, investor, careers, news,
   research/docs, website quality.
7. **Local-first section:** runs on your machine, artifacts in your workdir,
   optional keys, no forced hosted dependency.
8. **Hosted option:** convenience API with limits and fair-use credits.
9. **Examples:** product catalog, CI acquisition, company intelligence,
   browser-capture hard site.
10. **Pricing:** free local, paid hosted, enterprise/self-host support later.
11. **Docs and GitHub:** quickstart before marketing fluff.

## Scout Website Differentiation Blocks

### Not Just Markdown

Competitors often lead with "LLM-ready markdown." Scout can say:

> Markdown is the start. Scout also writes records, citations, blocked-page
> evidence, and artifact folders your downstream workflow can inspect.

### Local First, Hosted Optional

This is stronger than "private data" by itself. The value is operational
ownership:

- choose acquisition mode,
- keep artifacts locally,
- run without a hosted vendor in the loop,
- replay saved HTML,
- inspect blocked evidence,
- connect to user browser capture when needed.

### Honest Hard-Site Handling

Scout should not claim universal unblock. Use honest copy:

> When a site blocks automation, Scout records what failed and can escalate to
> browser or user-session capture when you authorize it.

### Artifact Contract

Show the artifact folder visually:

```text
run/
  manifest.json
  records.json
  records.jsonl
  source_pages.json
  blocked_pages.json
  validation.json
  extraction_report.md
  raw/
  screenshots/
```

This is a concrete website section competitors often do not emphasize.

## Design Implications From Supadesign IndustrialGray

The Supadesign IndustrialGray system is not a soft SaaS-gradient look. It is:

- warm industrial canvas,
- 12-column grid,
- sharp rectangular sections,
- technical readouts,
- editorial display typography,
- restrained amber accent,
- tactile noise overlay.

Scout's site should feel like infrastructure: precise, tactile, inspectable.

Recommended visual motifs:

- terminal/readout strips,
- artifact-folder schematic,
- source-evidence cards,
- run ladder diagram,
- record table previews,
- dark footer with CLI install commands,
- minimal rounded elements except buttons/badges.

Avoid:

- giant purple gradients,
- fake AI robot imagery,
- over-polished dashboard screenshots of the broken app UI,
- claims that imply universal unblock or autonomous magic.

