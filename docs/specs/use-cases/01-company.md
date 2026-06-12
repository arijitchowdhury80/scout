# Acquisition Contract: company

**Consumer:** `algolia-intel-company` (replaces its Scout-enrichment + WebFetch steps; the skill keeps vertical classification, parent/portfolio judgment, and WebSearch enrichment of facts Scout can't see).

## Input contract

`url` or `query`: company name, domain, or any company URL. Normalized to an https domain root. Accepts `targets[]` for multi-company runs.

## Acquisition plan

1. Homepage fetch (crawler; browser ladder on block).
2. Probe canonical paths: `/about`, `/about-us`, `/company`, `/our-story`, `/who-we-are`, `/team`, `/leadership`, `/about/team` (+ sitemap entries matching about|company|team|leadership).
3. Footer/header anchor harvest for: careers URL, IR URL, social profile URLs, contact/locations.
4. Meta extraction from each fetched page: `<title>`, meta description, og: tags, organization JSON-LD if present.
5. Leadership page extraction: names + titles from team/leadership page structure (headings, cards, alt text, person JSON-LD). LLM-extract mode is the fallback ONLY for the team page when structural parsing yields nothing — output still constrained to name/title/source fields.

## Record types & fields

**`company.v1`** (one per target)
- name (F: og:site_name / title / JSON-LD), legal_name (F: JSON-LD if present)
- website (F), description (F: meta/og description — verbatim), description_source (F)
- about_url, careers_url, ir_url, contact_url (F: discovered hrefs, each verified 200)
- social_urls{linkedin, x, instagram, facebook, youtube, tiktok} (F: footer/header hrefs — URL only, not fetched)
- logo_url (F: JSON-LD/og:image), locations[] (F: contact/footer addresses if structurally present)
- source_urls[], citations[] per field, confidence

**`executive.v1`** (0..n per target)
- name (F), title (F), profile_url (F: on-site bio link), image_url (F)
- linkedin_url (F: only if linked on the page — never constructed)
- source_url (F: the page the person appears on), citation snippet (F: surrounding text)

Out of scope (consumer keeps): vertical classification, business_model, hq/founded/employee_count via WebSearch, parent entity/portfolio mapping, ticker lookup.

## Confidence rules

company.v1: base 0.6 for homepage-only; +0.2 if about page fetched; +0.1 if JSON-LD organization present. executive.v1: 0.8 structural extraction from a leadership page; 0.6 LLM-extract fallback; never above 0.6 without a dedicated team/leadership page.

## Golden e2e flow

Run `company` on `https://www.algolia.com/` → status complete; ≥1 `company.v1` with non-null description AND citation whose snippet appears verbatim in the fetched page; ≥3 `executive.v1` records each with name, title, and source_url returning 200; zero records containing the string "seed" or "pending".
