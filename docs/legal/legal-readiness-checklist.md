# Scout Legal Readiness Checklist

Date: 2026-06-27
Status: Draft for private beta planning

## Crawl4AI And Open-Source Compliance

- [x] Keep Crawl4AI attribution in README and website.
- [ ] Keep Crawl4AI attribution in app Settings/About if the app UI becomes a
  launch surface.
- [x] Include `THIRD_PARTY_NOTICES.md` in source.
- [ ] Confirm `THIRD_PARTY_NOTICES.md` is included in all final package
  artifacts before public publishing.
- [x] Generate a dependency license inventory before public launch.
  Evidence: `docs/legal/dependency-license-inventory-2026-06-28.md`.
  This is a metadata-derived inventory and still requires manual review for
  packages with missing license metadata.
- [ ] Pin and audit dependency versions before release.
- [ ] Review whether Scout will be released as open source, source-available,
  commercial/proprietary, or dual-license.

## Scraping And Acquisition Risk

- [ ] Add customer-facing terms that users are responsible for lawful use.
- [ ] Avoid marketing language like "bypass bot protection."
- [ ] Prefer "browser-assisted acquisition", "blocked evidence", and
  "human-approved capture" language.
- [ ] Add robots/rate-limit configuration to docs and UI.
- [ ] Add site allowlist/blocklist configuration before external customers.
- [ ] Define which use cases are prohibited without separate legal review:
  LinkedIn capture, login-walled pages, job auto-apply, private account pages,
  regulated data, and personal-data enrichment.

## Data Handling

- [ ] Document where Scout writes artifacts.
- [ ] Add retention/deletion guidance for run folders.
- [ ] Make API-key handling explicit: `.env.local`, never committed.
- [ ] Confirm Algolia credentials are not written to artifacts or logs.
- [ ] Add privacy note for captured screenshots/DOM from user browser sessions.

## Public Beta Readiness

- [ ] Add "Beta" status language to website and README.
- [ ] Add known limitations for hard sites and bot walls.
- [ ] Add supported/unsupported use cases.
- [x] Add "not legal advice" note where acquisition workflows are discussed on
  the website legal page.
