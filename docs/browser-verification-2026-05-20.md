# Browser Verification — 2026-05-20

Purpose: validate Scout's browser fallback design using the Codex in-app browser.
Browser fallback is secondary and should only be used after regular acquisition
is blocked, sparse, JS-heavy, or explicitly requested for verification.

## Results

| Use case | Target | Browser result | Scout implication |
|---|---|---|---|
| Company/about | `https://www.adobe.com/about-adobe.html` | Success. Visible content included heading “Empowering everyone to create” and company overview copy. | Browser evidence can normalize into `company.v1` and source evidence. |
| Investor | `https://www.adobe.com/investor-relations.html` | Success. Visible content included FY2025 revenue, upcoming earnings call, quarterly result PDFs, presentation links, contact emails, and social links. | Browser evidence can normalize into `investor_asset.v1`, company/social records, and source pages. |
| Careers | `https://www.adobe.com/careers.html` | Success. Visible content included careers CTA, teams, culture, benefits, hiring process, and links to Adobe careers. | Browser evidence can normalize into `career_site.v1`. |
| Job page | Ashby Kong job URL | Success. Visible content included title “Director, Global Scaled CS,” location, employment type, department, compensation `$250K – $300K`, and application fields. | Browser evidence can normalize into `job_posting.v1`; no auto-apply. |
| Product/category | Lacoste men polos category | Partial success. Initial snapshot exposed a modal/accessibility shell, verbose snapshot exposed category links, product cards, prices, colors, result count, and product URLs. | Browser fallback can recover product evidence on JS-heavy retail pages, but extraction should filter noisy UI. |
| Hard-site product | Estée Lauder product URL | Blocked. Browser saw only “Access Denied” and an Akamai error reference. | Browser fallback is not a universal bypass; Scout must record blocked evidence and use alternate providers such as search, known URLs, cached/saved evidence, commerce APIs, or manual supplied page captures. |

## Design Conclusion

The browser fallback approach is valid, but it must remain a fallback. It adds
real value for JS-heavy pages and host-visible content, but some hard sites still
block the in-app browser. For those cases, Scout should:

1. record the blocked page in `blocked_pages.json`,
2. keep the attempted provider ladder in `manifest.json`,
3. preserve any error reference in source evidence,
4. continue with saved/API/host-fetch alternatives when available,
5. never claim product completeness when browser evidence is blocked.

## Next Build Work

- Add a normalized browser evidence adapter behind `mode=browser`.
- Add saved browser snapshot fixtures for Adobe, Ashby/Kong, Lacoste, and the
  Estée Lauder Access Denied page.
- Add extraction tests that turn those snapshots into typed records.
