# Scout E2E Launch Verification Matrix

Production-readiness instrument — every surface, endpoint, button, and click, verified against
LIVE prod (scout.chowmes.com) after each deploy. Status legend: ✅ pass (evidence) · ❌ fail ·
⬜ not yet run · 🔒 by-design gated. "Pass" requires observed evidence, not assumption.
Run 1 target: after the demo-expansion deploy (2026-07-06/07).

## A. Public API surface
| # | Check | How | Status |
|---|---|---|---|
| A1 | GET /health → 200 | curl | ⬜ |
| A2 | POST /v1/demo/scrape real URL → success+preview+evidence | curl | ⬜ |
| A3 | POST /v1/demo/map real URL → urls list | curl | ⬜ |
| A4 | POST /v1/demo/crawl → ≤3 pages, preview | curl | ⬜ |
| A5 | POST /v1/demo/products → ≤5 records, honest empty allowed | curl | ⬜ |
| A6 | Demo quota: 6th call same IP/day → 429 with clear message | curl loop | ⬜ |
| A7 | Demo rejects crawl-heavy abuse (bad target) cleanly | curl | ⬜ |
| A8 | POST /v1/hosted/beta-key (fresh email) → 200 provision + email delivered | curl + Gmail | ⬜ |
| A9 | Same email again → idempotent/no dup-credit behavior | curl | ⬜ |
| A10 | Invalid payloads → 422; garbage auth → 401/403; no 500s anywhere | curl | ⬜ |
| A11 | Authed: GET /v1/hosted/me with real key → account | curl (key from A8 email) | ⬜ |
| A12 | Authed: POST /v1/hosted/scrape → result + credit debited (me shows −1) | curl ×2 | ⬜ |
| A13 | Authed: GET /v1/hosted/usage → ledger row from A12 | curl | ⬜ |
| A14 | Authed: destinations/send webhook → delivers records to test receiver | curl | ⬜ |
| A15 | Authed: unknown destination → typed error, no 500 | curl | ⬜ |
| A16 | Credit hard-stop: exhausted balance → 402, never negative | needs drained test tenant | ⬜ |
| A17 | Stripe checkout-session (test-mode) for a pack → checkout_url returned | curl | ⬜ |
| A18 | Admin metrics auth-gated (no key → 403) | curl | ⬜ |

## B. Website pages (render + content + no secrets)
| # | Page | Checks | Status |
|---|---|---|---|
| B1 | / | 200, console present, 6 tabs, value headline, footer links | ⬜ |
| B2 | /pricing | locked model numbers, mix sums, no "unlimited", no Algolia-led copy | ⬜ |
| B3 | /beta | email-only form, support line, no reissue form | ⬜ |
| B4 | /app | shell renders | ⬜ |
| B5 | /docs (+/quickstart,/guide,/examples aliases) | 200 | ⬜ |
| B6 | /status /legal /terms /privacy /account | 200, titles | ⬜ |
| B7 | All pages: no sk_live_/sk_test_/whsec_/raw keys in HTML/JS | grep sweep | ⬜ |
| B8 | Assets: styles.css, JS files, logos, demo-samples load (200, right MIME) | curl | ⬜ |
| B9 | 404 route → clean handling (no stack trace) | curl | ⬜ |

## C. Interactive click-through (real browser on live site)
| # | Flow | Checks | Status |
|---|---|---|---|
| C1 | Homepage console: scrape tab → enter URL → Run → live result renders + evidence panel fills | ⬜ |
| C2 | map tab → Run → urls render | ⬜ |
| C3 | crawl tab → Run → ≤3-page preview renders | ⬜ |
| C4 | products tab → Run → records render (or honest empty) | ⬜ |
| C5 | company tab → real sample renders + Run routes to /beta | ⬜ |
| C6 | screenshot tab → sample image renders + Run routes to /beta | ⬜ |
| C7 | Nav links (Product/Docs/Pricing + CTA) all navigate correctly on every page | ⬜ |
| C8 | /beta signup form: happy path (fresh email) → success status message | ⬜ |
| C9 | /beta signup: invalid email / empty name → inline validation, no crash | ⬜ |
| C10 | Pricing CTAs: Get key → /beta; pack/monthly buttons behave (test-mode) | ⬜ |
| C11 | Footer mailto support@ present everywhere | ⬜ |
| C12 | Mobile (375px): homepage console fallback renders, pages don't overflow | ⬜ |
| C13 | Keyboard: tab through console + signup form, focus visible | ⬜ |

## D. Email + support loop
| # | Flow | Checks | Status |
|---|---|---|---|
| D1 | Signup email arrives, BRANDED (logo, key block, 5-min steps, support line) | Gmail | ⬜ (sent 2026-07-06, awaiting Arijit confirm) |
| D2 | Reply-To = support@scout.chowmes.com; replying reaches Arijit Gmail | Gmail | ⬜ |
| D3 | support@ inbound (external sender) lands in Gmail | live test | ✅ 2026-07-06 |
| D4 | Email renders in Gmail web + mobile (visual) | Arijit eyes | ⬜ |

## E. Neighbors + ops
| # | Check | Status |
|---|---|---|
| E1 | PRISM + Hermes healthy after each deploy | ⬜ (per-deploy) |
| E2 | Rollback image exists (previous snapshot) | ⬜ (per-deploy) |
| E3 | Container resource caps intact (docker inspect) | ⬜ |
| E4 | Nightly backup includes hosted_accounts.sqlite | ⬜ |

Execution notes: API checks via curl from local; click-throughs via the Chrome extension on the live
site; authed checks need one real key (from the A8 signup email — Arijit holds it). Update statuses
in place per run; failures get patched and re-run before any launch call.
