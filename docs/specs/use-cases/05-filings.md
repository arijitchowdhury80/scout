# Acquisition Contract: filings & transcripts (NEW)

**Consumer:** `algolia-intel-investor` (quotes half — replaces its SEC EDGAR WebFetch, transcript hunting, and verbatim-quote extraction; the skill keeps quote_context, algolia_relevance judgment, staleness policy, and FACT/ESTIMATE confidence labeling of paraphrases).

The largest scope addition from the 2026-06-12 boundary ADR. Everything here is acquire + extract: fetch public documents, return verbatim sections and quotes with provenance. No meaning-making.

## Input contract

`url` or `query`: company domain, ticker, or a direct document/transcript URL. Options: `doc_types[]` (10-K, 10-Q, 8-K, transcript, interview), `lookback_quarters` (default 4), `topic_tags[]` (optional extra keyword sets). Accepts `targets[]`.

## Acquisition plan

1. **SEC EDGAR** (public API door): resolve ticker/company → CIK via EDGAR full-text/company endpoints; fetch latest 10-K/10-Q/8-K index; fetch primary document (HTML preferred over PDF when both exist).
2. **Section extraction** from filings: Item 1A (Risk Factors), Item 7 (MD&A) — by item-heading detection; returned as clean verbatim text blocks with char offsets.
3. **Earnings-call transcripts**: discover via the target's IR pages (spec 04 assets of type transcript/webcast) and public web search (`"{company}" Q{n} {year} earnings call transcript` — discovery only; found pages fetched directly). Fetch and extract speaker-segmented text where the page structure exposes speakers.
4. **Interviews/talks** (optional, query-driven): given or discovered URLs of interview articles/podcast pages; extract quoted passages attributed to named people.
5. **Quote extraction**: from transcripts/interviews — verbatim passages with speaker name, title (when stated in-source), and position in document. From filings — sentence-level extraction within target sections.
6. PDF handling: text-layer extraction; scanned/no-text PDFs flagged, not OCR'd in v1.

## Record types & fields

**`document.v1`** (per fetched document)
- doc_type (F: 10-K/10-Q/8-K/transcript/interview), title (F), url (F), source (F: EDGAR/IR/publication domain)
- period (F: fiscal period verbatim from doc), filed_or_published_at (F), sections[] {name, text (verbatim), char_range} (F)
- citations[], confidence

**`quote.v1`** (0..n)
- speaker (F — named in source; anonymous = not extracted), speaker_title (F: as stated in source, else null)
- text (F — strictly verbatim; Scout never paraphrases), context_before/context_after (F: surrounding sentences for the consumer's judgment)
- document_url (F — **required**), document_type (F), spoken_or_published_at (F), location (F: section/timestamp/paragraph ref)
- topic_tags[] (T: deterministic keyword tags — default set: search, discovery, personalization, digital, ecommerce, platform, AI, data, customer-experience, conversion; extendable via input `topic_tags`). **Additive only: ALL extracted quotes are returned; tags never filter.**

Out of scope (consumer keeps): which quotes matter, quote_context prose, algolia_relevance selection, paraphrase handling ("said that" notation), staleness rejection policy, Yahoo Finance.

## Confidence rules

document.v1: 0.95 EDGAR primary doc; 0.85 IR-hosted; 0.7 third-party transcript page. quote.v1: inherits document confidence; −0.1 if speaker title absent; speaker-segmentation by structure 0.9 vs regex fallback 0.7.

## Golden e2e flow

Run `filings` on ticker `ADBE`, doc_types [10-K] → complete; 1 `document.v1` with sections containing "Risk Factors" text block whose first sentence appears verbatim in the EDGAR source; ≥10 `quote.v1` from the latest transcript run (`doc_types [transcript]`) each with named speaker + verbatim text + working document_url; every quote's text is grep-findable in the fetched document artifact.
