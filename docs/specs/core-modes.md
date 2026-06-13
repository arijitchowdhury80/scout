# Scout Core Modes — the general-crawler face

These are topic-agnostic acquisition primitives, NOT intelligence verticals. They emit generic structured output (markdown, links, screenshots, schema-extracted dicts), have no `algolia-intel-*` consumer, and are the **external/sellable (Ring 2) surface** per `docs/decisions/2026-06-13-scout-icp-and-use-case-set.md`. Kept first-class, clean, and documented — NOT built breadth-first in Phase C, but never starved by the Intelligence verticals.

| Mode | What it is | Status |
|---|---|---|
| scrape | single URL → markdown + metadata (+ screenshot) | exists |
| crawl | recursive BFS → pages | exists |
| map | URL discovery (sitemap-first) | exists |
| extract | LLM/CSS-schema structured extraction from a URL | exists |
| screenshot | rendered capture | exists |
| **list-fetch** (was use-case "research") | fetch + extract a GIVEN URL list → `research_page.v1` (markdown, title, word_count, optional schema extract). No discovery, no synthesis. | exists as scrape-over-list; expose as a named mode |
| **docs-map** (was use-case "docs") | doc-site taxonomy + page inventory → `doc_page.v1`. RAG/knowledge capability. | deferred from Phase C; revisit when a knowledge-base consumer exists |

Rationale for the demotions: `research` was redundant with scrape-over-a-list and produced untyped output — a primitive, not a vertical. `docs` had no consumer in the prospect-research flow; its natural home is RAG ingestion (Scout's general-crawler identity). Both remain valuable and become the seeds of the Ring-2 product; neither earns a launcher card in the Intelligence face.
