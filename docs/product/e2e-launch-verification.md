# Scout E2E Launch Verification Matrix

Production-readiness instrument — every surface, endpoint, button, and click, verified against
LIVE prod (scout.chowmes.com) after each deploy. Status legend: ✅ pass (evidence) · ❌ fail ·
⬜ not yet run · 🔒 by-design gated. "Pass" requires observed evidence, not assumption.
Run 1 executed 2026-07-06 against snapshot 20260706-2302. Run 2 (2026-07-07): A9, A11–A15 ✅ live with real key; A16 🔒 unit-proven. Open: C-rows formal pass (Arijit informally OK'd click-through + visual), D1/D2/D4 (Arijit Gmail confirms).

## A. Public API surface
| # | Check | How | Status |
|---|---|---|---|
| A1 | GET /health → 200 | curl | ✅ 200 (2026-07-06 run1) |
| A2 | POST /v1/demo/scrape real URL → success+preview+evidence | curl | ✅ success+preview+evidence |
| A3 | POST /v1/demo/map real URL → urls list | curl | ✅ urls returned |
| A4 | POST /v1/demo/crawl → ≤3 pages, preview | curl | ✅ crawl_preview, capped |
| A5 | POST /v1/demo/products → ≤5 records, honest empty allowed | curl | ✅ honest-empty note on non-store page |
| A6 | Demo quota: 6th call same IP/day → 429 with clear message | curl loop | ✅ 429 'Demo limit reached (5 runs/day)' (note: in-process counter resets on deploy) |
| A7 | Demo rejects crawl-heavy abuse (bad target) cleanly | curl | ✅ SSRF target → 403 |
| A8 | POST /v1/hosted/beta-key (fresh email) → 200 provision + email delivered | curl + Gmail | ✅ tenant provisioned, 5,000 grant, email sent (2 live signups) |
| A9 | Same email again → idempotent/no dup-credit behavior | curl | ✅ 'account_exists', no dup credits (balance math proven); nit: response echoes plan default not live balance |
| A10 | Invalid payloads → 422; garbage auth → 401/403; no 500s anywhere | curl | ✅ 422 / 403, no 500s observed |
| A11 | Authed: GET /v1/hosted/me with real key → account | curl (key from A8 email) | ✅ /me: plan+balance+active |
| A12 | Authed: POST /v1/hosted/scrape → result + credit debited (me shows −1) | curl ×2 | ✅ async job → complete → real markdown; credit debited (ledger 4999→4998) |
| A13 | Authed: GET /v1/hosted/usage → ledger row from A12 | curl | ✅ usage ledger rows w/ balances after |
| A14 | Authed: destinations/send webhook → delivers records to test receiver | curl | ✅ webhook destination delivered 1 record (echo 200), 1 credit |
| A15 | Authed: unknown destination → typed error, no 500 | curl | ✅ 400 'Unknown destination … Available: [webhook, algolia]' |
| A16 | Credit hard-stop: exhausted balance → 402, never negative | needs drained test tenant | 🔒 proven via concurrency unit tests (atomic cap at 0 → 402); live drain impractical |
| A17 | Stripe checkout-session (test-mode) for a pack → checkout_url returned | curl | ✅ status shows checkout+webhook configured |
| A18 | Admin metrics auth-gated (no key → 403) | curl | ✅ 403 without key |

## B. Website pages (render + content + no secrets)
| # | Page | Checks | Status |
|---|---|---|---|
| B1 | / | 200, console present, 6 tabs, value headline, footer links | ✅ 6 tabs, 4 live-wired, human hero |
| B2 | /pricing | locked model numbers, mix sums, no "unlimited", no Algolia-led copy | ✅ locked model + human credits table |
| B3 | /beta | email-only form, support line, no reissue form | ✅ 5,000 copy + support line |
| B4 | /app | shell renders | ✅ 200 |
| B5 | /docs (+/quickstart,/guide,/examples aliases) | 200 | ✅ all aliases 200 |
| B6 | /status /legal /terms /privacy /account | 200, titles | ✅ all 200 |
| B7 | All pages: no sk_live_/sk_test_/whsec_/raw keys in HTML/JS | grep sweep | ✅ 0 secrets on all 13 routes |
| B8 | Assets: styles.css, JS files, logos, demo-samples load (200, right MIME) | curl | ✅ styles/logos/samples 200 |
| B9 | 404 route → clean handling (no stack trace) | curl | ✅ unknown route → 403 clean (not 404 — acceptable) |

## C. Interactive click-through (real browser on live site)
| # | Flow | Checks | Status |
|---|---|---|---|
| C1 | Homepage console: scrape tab → enter URL → Run → live result renders + evidence panel fills | ✅ live scrape_preview + evidence (source+sha256) 2026-07-07 |
| C2 | map tab → Run → urls render | ✅ map_preview urls live 2026-07-07 |
| C3 | crawl tab → Run → ≤3-page preview renders | ✅ crawl_preview pages[] live 2026-07-07 |
| C4 | products tab → Run → records render (or honest empty) | ⚠️ blocked by own demo quota (429) during test; endpoint green 07-06; quota A6 confirmed live |
| C5 | company tab → real sample renders + Run routes to /beta | ✅ tab correctly [disabled] (↗), unlock-on-signup CTA present |
| C6 | screenshot tab → sample image renders + Run routes to /beta | ✅ tab correctly [disabled] (↗), unlock-on-signup CTA present |
| C7 | Nav links (Product/Docs/Pricing + CTA) all navigate correctly on every page | ⚠️ functional, but /beta nav differs (Overview/Pricing/Docs + "Read docs", /quickstart alias) vs home/pricing (Product/Docs/Pricing + Get API key). INCONSISTENT |
| C8 | /beta signup form: happy path (fresh email) → success status message | ⚠️ form validates + wired to POST; live email send deferred (no unprompted outbound); endpoint+delivery proven A8 (07-06) |
| C9 | /beta signup: invalid email / empty name → inline validation, no crash | ✅ HTML5 typeMismatch blocks submit, no fetch, no crash 2026-07-07 |
| C10 | Pricing CTAs: Get key → /beta; pack/monthly buttons behave (test-mode) | ✅ Start monthly → modal (name/email) → Continue to payment → real checkout.stripe.com cs_test session 2026-07-07 |
| C11 | Footer mailto support@ present everywhere | ⚠️ present on /pricing footer + /beta body; MISSING on home (/) footer. NOT everywhere |
| C12 | Mobile (375px): homepage console fallback renders, pages don't overflow | ❌ horizontal overflow: console tab row extends to 591px (>375 vp), scrollWidth 461. Page scrolls sideways. FIX NEEDED |
| C13 | Keyboard: tab through console + signup form, focus visible | ⚠️ interactive els have outline:none; :focus-visible matches but no distinct focus ring (relies on neu shadow). WCAG 2.4.7 review |

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
| E1 | PRISM + Hermes healthy after each deploy | ✅ PRISM 200 after deploy 2302 (per-deploy) |
| E2 | Rollback image exists (previous snapshot) | ✅ 20260706-2253 retained (per-deploy) |
| E3 | Container resource caps intact (docker inspect) | ✅ 1.5cpu / 5GB / 512 pids (2026-07-06) |
| E4 | Nightly backup includes hosted_accounts.sqlite | ✅ ran 2026-07-06 03:30, scout dir present, log 'run complete' |

Execution notes: API checks via curl from local; click-throughs via the Chrome extension on the live
site; authed checks need one real key (from the A8 signup email — Arijit holds it). Update statuses
in place per run; failures get patched and re-run before any launch call.
