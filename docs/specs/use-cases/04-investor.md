# Acquisition Contract: investor

**Consumer:** `algolia-intel-investor` (assets half — IR page inventory; quote extraction from those assets lives in spec 05-filings).

## Input contract

`url`: IR URL or company domain. Accepts `targets[]`. Works for public companies; for private companies returns whatever investor/press assets the site exposes (often none — honest empty).

## Acquisition plan

1. Probe `/investors`, `/investor-relations`, `/ir`, `investors.{domain}`, `ir.{domain}` + sitemap matches + company.v1 ir_url in bundle runs.
2. IR index harvest: links to annual/quarterly reports, presentations, press releases, webcast/event pages, governance docs — with link text, file type, and date context from surrounding markup.
3. One level of follow: "financial reports"/"events & presentations" subpages (cap-bounded).
4. No document content extraction here — that is spec 05. This contract inventories what exists and where.

## Record types & fields

**`investor_asset.v1`** (0..n)
- title (F: link text/heading, verbatim), url (F — **required**), asset_type (T: deterministic — annual-report, quarterly-report, presentation, press-release, transcript, webcast, governance, other; by URL/extension/link-text patterns)
- file_format (F: pdf/html/audio/video by extension or content-type HEAD), period (F: FY/Q+year when present in text — verbatim token, not inferred), published_at (F: when shown)
- found_on (F: the IR page URL), citations[], confidence

Out of scope: reading the documents (spec 05), Yahoo Finance news, financial metrics, quote relevance.

## Confidence rules

0.9 asset linked from a fetched IR page with explicit type/date text; 0.7 type inferred from URL pattern only; HEAD-verified URLs +0.05, dead links excluded (logged in report).

## Golden e2e flow

Run `investor` on `https://www.adobe.com/investor-relations.html` → complete; ≥5 `investor_asset.v1` spanning ≥2 asset_types; every url HEAD-verified; each record cites the IR page it was found on.
