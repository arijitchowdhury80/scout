# Acquisition Contract: investor & filings (merged)

**Consumer:** `algolia-intel-investor`. Merges the former `04-investor` (IR asset inventory) and `05-filings` (document/quote extraction) — same consumer, two depths of the same domain. The skill keeps: which quote matters, quote_context prose, value mapping, staleness policy, FACT/ESTIMATE labeling of paraphrases, Yahoo Finance metrics.

Two depths, selectable per run:
- **inventory** — map the IR surface (what documents/events exist and where).
- **read** — fetch and extract verbatim sections + quotes from those documents (+ EDGAR + transcripts).

## Input contract
`url`/`query`: company domain, ticker, IR URL, or a direct document/transcript URL. Options: `depth` (inventory|read, default inventory), `doc_types[]` (10-K, 10-Q, 8-K, transcript, interview), `lookback_quarters` (default 4), `topic_tags[]` (additive). Accepts `targets[]`.

## Acquisition plan
**Inventory depth:**
1. Probe `/investors`, `/investor-relations`, `/ir`, `investors.{domain}`, `ir.{domain}` + sitemap + company.v1 ir_url.
2. Harvest links to reports/presentations/press-releases/webcasts/governance with link text, file type, date context.

**Read depth (adds):**
3. **SEC EDGAR** (public API door): ticker/company → CIK → latest 10-K/10-Q/8-K index → primary document (HTML preferred over PDF).
4. **Section extraction** from filings: Item 1A (Risk Factors), Item 7 (MD&A) — verbatim text blocks with char offsets.
5. **Transcripts**: discover via IR pages + public search (discovery only; found pages fetched directly); extract speaker-segmented text.
6. **Quote extraction**: verbatim passages with named speaker + title (as stated in source) + position.
7. PDF: text-layer extraction; scanned/no-text PDFs flagged, not OCR'd in v1.

## Record types & fields (F = direct extraction, T = deterministic tag)
**`investor_asset.v1`** (inventory + read) — title (F), url (F, HEAD-verified), asset_type (T: annual-report/quarterly-report/presentation/press-release/transcript/webcast/governance/other), file_format (F), period (F: verbatim token), published_at (F), found_on (F), citations[], confidence.

**`document.v1`** (read) — doc_type (F), title (F), url (F), source (F: EDGAR/IR/publication), period (F), filed_or_published_at (F), sections[]{name, text verbatim, char_range} (F), citations[], confidence.

**`quote.v1`** (read) — speaker (F, named only), speaker_title (F or null), text (F, strictly verbatim), context_before/after (F), document_url (F, required), document_type (F), spoken_or_published_at (F), location (F), topic_tags[] (T: search/discovery/personalization/digital/ecommerce/platform/AI/data/customer-experience/conversion + input extras). **Additive only: ALL quotes returned; tags never filter.**

## Confidence rules
investor_asset 0.9 linked-from-fetched-IR-page with explicit type/date, 0.7 type-inferred-from-URL. document 0.95 EDGAR primary, 0.85 IR-hosted, 0.7 third-party transcript. quote inherits document; −0.1 if title absent; structural speaker-segmentation 0.9 vs regex 0.7.

## Golden e2e flow
`investor-filings` depth=inventory on adobe.com IR → ≥5 `investor_asset.v1` spanning ≥2 types, all HEAD-verified. depth=read ticker ADBE doc_types[10-K] → 1 `document.v1` with a "Risk Factors" section whose first sentence is verbatim in EDGAR source; doc_types[transcript] → ≥10 `quote.v1` each with named speaker + verbatim text grep-findable in the fetched artifact.
