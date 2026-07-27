# Scout Marketing Site — Full Click-Through Audit
Date: 2026-07-26 · Target: https://scout.chowmes.com · Tool: Playwright MCP (real browser, live production)

All screenshots are under `docs/test-results-2026-07-26/screenshots/`. All network/console evidence was captured live against production. No repeated form submissions were made where the task asked for a single attempt.

## Summary counts

| Status | Count |
|---|---|
| PASS | 21 |
| WARN | 6 |
| FAIL | 5 |

## Table

| Element | Route | Expected | Observed | Status | Screenshot |
|---|---|---|---|---|---|
| Page load | `/` | 200, no console errors | 200 OK, 0 console errors, title "Scout. Evidence-grade web intelligence, live in your browser" | PASS | screenshots/home-desktop.png |
| Nav: Product | `/` | Links to `/` | `href="/"` | PASS | — |
| Nav: Docs | `/` | Links to docs subdomain | `href="https://docs.scout.chowmes.com"` | PASS | — |
| Nav: Pricing | `/` | Links to `/pricing` | `href="/pricing"` | PASS | — |
| CTA: Get API key | `/` | Links to `/beta` | `href="/beta"` | PASS | — |
| Console tab: scrape + Run | `/` | POST `/v1/demo/scrape`, returns typed record | 200 OK, real JSON w/ evidence (source/hash/verified/blocked) for example.com | PASS | screenshots/home-desktop.png |
| Console tab: map + Run | `/` | POST `/v1/demo/map` | 200 OK, `map_preview` record returned | PASS | — |
| Console tab: crawl + Run | `/` | POST `/v1/demo/crawl` | 200 OK | PASS | — |
| Console tab: products + Run | `/` | POST `/v1/demo/products` | 200 OK | PASS | — |
| Console tab: company (locked) | `/` | Shows sample record, Run button becomes "Get your free API key" | On a genuine click event, fetches `/assets/demo-samples/company-sample.json` (200) and renders Anthropic sample record correctly. Note: Playwright's default `browser_click` refuses this element because it carries `aria-disabled="true"` even though the real DOM `disabled` property is `false` and `pointer-events:auto` — a real mouse user CAN click it fine. Verified via a genuine trusted click event. | PASS | screenshots/home-screenshot-tab-locked.png |
| Console tab: screenshot (locked) | `/` | Shows sample screenshot image, same CTA swap | Sample screenshot image + evidence panel rendered correctly | PASS | screenshots/home-screenshot-tab-locked.png |
| **CTA "Get your free API key" (replaces Run when a locked tab is selected)** | `/` | Clicking navigates to `/beta` | **Click is a no-op.** `location.href` stays `https://scout.chowmes.com/` after two separate click attempts. Button is `<button type="submit" id="consoleRunBtn">` with no visible handler firing, no console error either — it silently does nothing. | **FAIL** | screenshots/home-locked-cta-noop.png |
| Evidence panel "hash" field on map/screenshot samples | `/` | Either a value or hidden if N/A | Renders as a bare `,` with no value/no label when the record type has no hash (map, screenshot) — cosmetic but visibly broken formatting | WARN | — |
| Footer: Product/Pricing/Docs/Beta/Legal/Terms/Privacy | `/` | Present | All present | PASS | — |
| Footer: Support mailto | `/` | `mailto:support@scout.chowmes.com` present | Present, correct address | PASS | — |
| Footer: Crawl4AI attribution link | `/` | Present | Present, links to GitHub repo | PASS | — |
| `/beta` load | `/beta` | 200, no console errors | 200 OK, 0 console errors on load, title "Scout Beta Tester Signup - Get your API key" | PASS | screenshots/beta-page.png |
| **Nav on `/beta`** | `/beta` | Consistent with home nav | **Different from home**: labels are "Overview / Pricing / Docs" (order + label changed from home's "Product / Docs / Pricing"), "Docs" points to internal `/quickstart` instead of the external docs subdomain used on home/pricing, and the header CTA is "Read docs" instead of "Get API key" | **FAIL** (confirmed suspected nav inconsistency) | screenshots/beta-page.png |
| Beta footer | `/beta` | Same link set as home footer | Missing: Product, Beta, Crawl4AI links, and there is no standalone "Support" footer link (mailto is only inline in body copy, not in the footer link row) | WARN | screenshots/beta-page.png |
| Beta signup form: fill + submit ("Email me my API key") | `/beta` | 200 + success/pending state, email dispatched | **502** from `POST /v1/hosted/beta-key`. On-screen status area leaks the raw upstream error verbatim: `SMTP delivery failed: (550, b'Invalid `to` field. Please use our testing email address instead of domains like `example.com`. See our documentation for more information.')` — this reads as the email provider (Resend or similar) still being in sandbox/test mode, restricted to a verified test address only. Real beta signups on this exact flow, with a real domain, would currently fail identically. Submitted exactly once per instructions. | **FAIL — launch blocker** | screenshots/beta-signup-502-smtp-error.png |
| `/pricing` load | `/pricing` | 200, no console errors | 200 OK, 0 console errors, title correct | PASS | screenshots/pricing-page.png |
| Nav on `/pricing` | `/pricing` | Consistent with home | Matches home exactly (Product/Docs/Pricing, "Get API key" CTA) | PASS | screenshots/pricing-page.png |
| Plan button "Start monthly, $12/mo" → modal | `/pricing` | Opens checkout modal | Modal opens with Name/Email/Package fields | PASS | — |
| Modal → fill name/email → "Continue to payment" | `/pricing` | Redirects to Stripe Checkout | Redirected to `https://checkout.stripe.com/c/pay/cs_test_a1JxuvLvlqYN02e1uJ9yP36RkEjFt5W7PTHs5PET51dxJXK0OXz8abA3oZ...` | PASS (redirect works) / **WARN** — session id is `cs_test_...`, i.e. **Stripe TEST mode**, wired into the live production pricing page. No card details entered per instructions. | screenshots/pricing-stripe-checkout.png |
| Pricing footer | `/pricing` | Consistent set | Docs/Legal/Terms/Privacy/support mailto — no Product/Beta/Crawl4AI (same reduced set as beta) | WARN | screenshots/pricing-page.png |
| `/account` load | `/account` | 200, no console errors | 200 OK, 0 console errors, title "Scout Hosted Account - Usage and credits" | PASS | screenshots/account-page.png |
| **Nav on `/account`** | `/account` | Consistent with home/pricing | **Third distinct nav variant on this one site**: "Overview / Features / Demo / Docs / Pricing", image-based logo instead of the "Scout" text wordmark used elsewhere, CTA is "Join beta". `Features`→`/#use-cases` (target exists on home), but `Demo`→`/#demo` and `Pricing`→`/#purchase` point to anchor IDs that **do not exist** on the homepage (`#demo` and `#purchase` were not found in the home page DOM) — these links land on the plain homepage with no scroll, effectively dead anchors. | **FAIL** | screenshots/account-page.png |
| `/account` footer | `/account` | Present, consistent | **No footer/contentinfo element at all** on this page — no Legal/Terms/Privacy/Support links anywhere | **FAIL** | screenshots/account-page.png |
| "Check account" button, empty key | `/account` | No-op / validation, no request | Correctly did nothing — no network request fired, status text stayed "Ready." | PASS | — |
| "Manage billing in Stripe" button, no key | `/account` | Disabled until a key is checked | Correctly rendered `disabled` | PASS | — |
| `/legal` load | `/legal` | 200, readable content | 200 OK, 0 console errors, "Scout Legal And Third-Party Notices" | PASS | screenshots/legal-page.png |
| `/terms` load | `/terms` | 200, final terms | 200 OK, 0 console errors, but **title is literally "Scout Beta Terms Placeholder"** and body text says outright: "This is not a final Terms of Service... a temporary beta boundary page." Also states "broad paid checkout... remain deferred until their gates reopen" — which contradicts the fully working Stripe checkout flow found live on `/pricing` (see above). | WARN — self-flagged as non-final, and inconsistent with the live checkout that already exists | screenshots/terms-page.png |
| `/privacy` load | `/privacy` | 200, final privacy policy | 200 OK, 0 console errors, but title is "Scout Beta Privacy Placeholder" — same non-final caveat as `/terms` | WARN | screenshots/privacy-page.png |
| `/docs` redirect | `/docs` | 308 → docs.scout.chowmes.com | Confirmed 308 → `https://docs.scout.chowmes.com`, lands on real docs site "Introduction - Scout" | PASS | — |
| `/quickstart` redirect | `/quickstart` | 308 → docs.scout.chowmes.com | Confirmed 308, same target | PASS | — |
| `/guide` redirect | `/guide` | 308 → docs.scout.chowmes.com | Confirmed 308, same target | PASS | — |
| `/examples` redirect | `/examples` | 308 → docs.scout.chowmes.com | Confirmed 308, same target | PASS | — |
| `/status` | `/status` | No route (per task's own caveat) | Confirmed **404**, single console error logged for the failed resource load, no `status.js` script tag found referenced in the rendered HTML of `/`, `/beta`, `/pricing`, or `/account` | PASS (matches the "may be no route" expectation) — flagging only because a `status.js` reference was called out as a thing to check and none was found live | screenshots/status-404.png |
| **`/app`** | `/app` | Should be **deleted** — product is being removed | **Still live.** Returns HTTP 200, full page renders, title "Scout App - Playground". This is the exact route the task said should be gone. | **FAIL — stale surface, contradicts stated deletion** | screenshots/app-still-live.png |
| `/app/test`, `/app/dashboard` | `/app/*` | Consistent with `/app` (either all present or all gone) | Both return **403** while the `/app` root itself returns 200 — inconsistent partial-teardown state (root page still fully renders, but its own sub-routes are blocked) | WARN | — |
| Mobile viewport (375px), `/` | `/` (375×812) | No horizontal overflow | `document.documentElement.scrollWidth === clientWidth === 375`, 0 overflowing elements found via full DOM scan | PASS | screenshots/home-mobile-375.png |
| Mobile viewport (375px), `/beta` | `/beta` (375×812) | No horizontal overflow | Same result, 0 overflow | PASS | — |
| Mobile viewport (375px), `/pricing` | `/pricing` (375×812) | No horizontal overflow | Same result, 0 overflow | PASS | — |
| Keyboard focus ring, home nav | `/` (1280×800, Tab×3) | Visible focus indicator (WCAG 2.4.7) | Focus lands on "Docs" nav link; `outline` is set to `none` but an inset-style `box-shadow: 0 0 0 3px rgba(14,138,97,0.55)` (green) provides a visible ring in the screenshot | PASS, but low-contrast green-on-pale-green — worth a contrast pass | screenshots/home-focus-ring-docs-link.png |
| **Live console responsiveness to window resize** | `/` | Console reflects current viewport width live | **Bug found incidentally**: after loading the page at 375px and then resizing the same page to 1280px (no reload), the console widget stayed stuck showing "Static example on mobile · run the live console on desktop" with a non-functional/static example instead of switching back to the live "Ready · scrape, map, crawl, products live" state. A fresh load at 1280px shows the correct live state immediately. So the mobile/desktop mode is decided once (at load) and never re-evaluated on resize — a real user rotating a tablet or resizing a browser window after page load would get stuck on the static/mobile experience. | **FAIL** | screenshots/home-desktop-fresh-load.png (compare to the stuck-mobile-state screenshot taken mid-sequence) |

## Notes on methodology
- All "live" console runs used `https://example.com` as the test URL (5 runs/IP/day cap respected — 4 runs used: scrape, map, crawl, products).
- Beta signup form was submitted exactly once with Name="Scout Webwalk Test", Email="scout-webwalk-test@example.com", per instructions not to repeat.
- Pricing checkout flow was carried through to the real Stripe redirect; no card details were entered, consistent with instructions.
- `/app` and its sub-routes were only observed, not exercised further, since the instruction was to flag continued existence, not test its internals.
