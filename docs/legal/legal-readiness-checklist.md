# Scout Legal Readiness Checklist

Date: 2026-06-27
Status: Draft for private beta planning

## Crawl4AI And Open-Source Compliance

- [x] Keep Crawl4AI attribution in README and website.
- [ ] Keep Crawl4AI attribution in app Settings/About if the app UI becomes a
  launch surface.
- [x] Include `THIRD_PARTY_NOTICES.md` in source.
- [x] Confirm `THIRD_PARTY_NOTICES.md` is included in all final package
  artifacts before public publishing.
- [x] Generate a dependency license inventory before public launch.
  Evidence: `docs/legal/dependency-license-inventory-2026-06-28.md`.
  This is a metadata-derived inventory and still requires manual review for
  packages with missing license metadata.
- [ ] Pin and audit dependency versions before release.
- [x] Review whether Scout will be released as open source, source-available,
  commercial/proprietary, or dual-license.
  Evidence brief:
  `docs/legal/scout-license-distribution-decision-brief-2026-06-29.md`.
  Implementation runbook:
  `docs/legal/license-implementation-runbook-2026-06-29.md`.
  Decision implemented: Apache-2.0 local/core plus hosted/service
  monetization as a separate commercial surface. Root `LICENSE` and
  `pyproject.toml` license metadata were added in the release-hardening pass.

## Scraping And Acquisition Risk

- [x] Add customer-facing terms that users are responsible for lawful use.
  Evidence: `docs/legal/beta-terms-placeholder.md` and `/terms`.
- [ ] Avoid marketing language like "bypass bot protection."
- [ ] Prefer "browser-assisted acquisition", "blocked evidence", and
  "human-approved capture" language.
- [ ] Add robots/rate-limit configuration to docs and UI.
- [ ] Add site allowlist/blocklist configuration before external customers.
- [ ] Define which use cases are prohibited without separate legal review:
  LinkedIn capture, login-walled pages, job auto-apply, private account pages,
  regulated data, and personal-data enrichment.

## Data Handling

- [x] Document where Scout writes artifacts.
  Evidence: `docs/legal/beta-privacy-placeholder.md` and `/privacy`.
- [x] Add retention/deletion guidance for run folders.
  Evidence: `docs/legal/beta-privacy-placeholder.md` and `/privacy`.
- [x] Make API-key handling explicit: `.env.local`, never committed.
  Evidence: `docs/legal/beta-privacy-placeholder.md` and `/privacy`.
- [ ] Confirm Algolia credentials are not written to artifacts or logs.
- [x] Add privacy note for captured screenshots/DOM from user browser sessions.
  Evidence: `docs/legal/beta-privacy-placeholder.md` and `/privacy`.

## Public Beta Readiness

- [x] Add "Beta" status language to website and README.
- [x] Add known limitations for hard sites and bot walls.
- [x] Add supported/unsupported use cases.
- [x] Add "not legal advice" note where acquisition workflows are discussed on
  the website legal page.
