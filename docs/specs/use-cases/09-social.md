# Acquisition Contract: social (URL-verification mode)

**Consumer:** `algolia-intel-social` (verification half only; its Apify post-scraping and scoring stay in the skill — ToS posture per boundary ADR; revisit after legal check).

## Input contract
`url`/`query`: company domain (uses company.v1 social_urls in bundle runs) or explicit profile URLs.

## Acquisition plan
1. Discover profile URLs from the target's own site (footer/header/contact).
2. Verify each URL: HEAD/GET reachability, canonical redirect resolution, profile-exists vs 404.
3. NO post scraping, NO login-walled fetching. Public profile page title/handle extracted only where the platform serves it unauthenticated.

## Record types & fields
**`company_social.v1`** — platform (F), url (F: canonical), verified (F: bool + status), handle (F: from URL/title), found_on (F: the page that linked it), citations[], confidence.

## Confidence rules
0.9 verified live profile linked from the company's own site; 0.5 unverified (network fail) — flagged.

## Golden e2e flow
Run `social` on `https://www.algolia.com/` → complete; ≥2 `company_social.v1` (e.g. LinkedIn, X) with verified=true and found_on citing the Algolia page that linked them. No invented URLs: every url either appeared in fetched HTML or was input.
