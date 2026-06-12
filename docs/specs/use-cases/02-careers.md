# Acquisition Contract: careers

**Consumer:** `algolia-intel-hiring` (replaces its Layer-1 careers-portal WebFetch; the skill keeps its Layer-2 job-board WebSearch, ICP tier scoring, and buying-committee judgment).

## Input contract

`url`: careers URL or company domain. Accepts `targets[]`.

## Acquisition plan

1. Careers URL discovery: provided URL, else probe `/careers`, `/jobs`, `/careers/jobs`, `careers.{domain}`, `jobs.{domain}` + company.v1 careers_url if a bundle run.
2. **ATS fingerprinting** (deterministic, by URL pattern + script/DOM markers): Greenhouse (`boards.greenhouse.io`, `grnhse`), Lever (`jobs.lever.co`), Ashby (`jobs.ashbyhq.com`), Workday (`myworkdayjobs.com`, `wd1/wd3/wd5`), iCIMS (`icims.com`), SmartRecruiters, Workable, BambooHR, Recruitee, Teamtailor, SuccessFactors, Taleo, PerimeterX-protected portals (flag as protected).
3. Job listing extraction: from the careers page and/or the ATS's public board (Greenhouse/Lever/Ashby expose public JSON endpoints — public API doors, in scope). Paginate up to pages-per-run cap.
4. Department/team taxonomy extraction where the board exposes it.
5. Blocked/login-walled portal → BlockedPage evidence + escalation note (matches the skill's "Layer 1 = 0, document and continue" rule).

## Record types & fields

**`career_site.v1`** (one per target)
- careers_url (F, verified), ats_platform (F: fingerprint), ats_board_url (F)
- total_open_roles (F: count of extracted listings), departments[] (F)
- protected (F: bool + protection vendor if detected), source_urls[], citations[], confidence

**`job_posting.v1`** (0..n)
- title (F — exact), job_id (F: from ATS), url (F — **required**, direct posting link; no posting without a URL)
- location (F), department (F), posted_at (F: if exposed), description_excerpt (F: first ~200 chars, verbatim)
- role_tags[] (T: deterministic title-pattern tags — engineering, product, design, data, digital-commerce, search-platform, leadership, operations)
- keyword_tags[] (T: deterministic description keyword matches — search, personalization, ecommerce, NLP, recommendation, platform, AI)

Out of scope (consumer keeps): ICP tier (1–4), 1–10 scoring, buying-committee assessment, algolia_relevance prose, job-board WebSearch sweep (Indeed/ZipRecruiter).

## Confidence rules

career_site.v1: 0.9 with ATS fingerprint + extracted listings; 0.7 careers page found but listings JS-walled; 0.5 derived URL only (must carry blocked/JS evidence). job_posting.v1: 0.9 from ATS JSON endpoint; 0.8 from parsed HTML listing.

## Golden e2e flow

Run `careers` on `https://www.algolia.com/careers/` → complete; 1 `career_site.v1` with non-null ats_platform; ≥5 `job_posting.v1` each with title + working url; departments[] non-empty; every record cites a fetched source.
