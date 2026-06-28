# Scout Launch Website Status

Date: 2026-06-28
Status: In progress - positioning refresh

## Checklist

- [x] Design thinking written.
- [x] UI/UX constraints written.
- [x] Supadesign IndustrialGray direction selected.
- [x] Static homepage implemented.
- [x] Browser/static verification completed.
- [x] Final notes and next steps documented.
- [x] Hosted beta checkout form wired to `/v1/billing/stripe/checkout-session`.
- [x] Checkout form desktop/mobile smoke completed.
- [x] Scout API root now serves the launch website from the same origin.
- [x] Refresh homepage around evidence-grade records differentiation.
- [x] Verify refreshed homepage across desktop/mobile.
- [x] Commit refreshed website checkpoint.

## Scope

Build the first private-beta Scout website surface, separate from the broken
Scout app UI. The website should position Scout, explain local vs hosted usage,
show the artifact/evidence model, and guide users to install locally or join the
hosted beta.

The hosted beta section now contains an email capture + Stripe Checkout Session
form. It calls the Scout API route `/v1/billing/stripe/checkout-session`, then
redirects to the returned `checkout_url`. The page does not include Stripe
secret keys and shows a clear configuration/error state if the route is not
ready.

The page also reads `/v1/billing/stripe/status` on load. When checkout is not
configured, the hosted beta submit button is disabled and the page tells users
to install locally or check back for hosted access. This avoids a silent or
surprising first-click failure.

The Scout API now serves `website/index.html` at `/`, plus `/styles.css` and the
bundled IndustrialGray design-system CSS under
`/assets/warm-industrial-design-system/`. That means `scout serve` exposes the
marketing site and checkout form from the same origin as the billing API.

## 2026-06-28 Positioning Refresh

The competitor research refresh found that Scout should not depend on
"local-owned data" as the main differentiation. Other crawler APIs also return
private copies of public data. The refreshed launch page must lead with
evidence-grade records:

- target acquisition,
- acquisition ladder,
- source/blocked evidence,
- typed records,
- citations and validation,
- exports to downstream workflows.

Acceptance for this slice:

- above-the-fold copy answers "why Scout, not just another crawler?",
- homepage includes a visible ledger/pipeline of evidence -> records -> exports,
- pricing copy frames `$22` as finite hosted beta credits,
- checkout form remains wired to same-origin Stripe routes,
- tests and browser smoke still pass.

## Verification

Command run through Playwright against `python3 -m http.server 8766 --directory
website`:

- desktop viewport: `1440x1000`
- mobile viewport: `390x844`
- required content assertions passed
- link inventory found 14 links
- console errors/warnings: 0

Screenshots:

- `validation-output/website-scout-launch/desktop.png`
- `validation-output/website-scout-launch/mobile.png`

Additional checkout smoke:

- `python3 -m pytest tests/unit/website/test_launch_website.py tests/unit/api/test_billing_stripe_checkout.py -q`
  - Result: 3 passed.
- Playwright against `python3 -m http.server 8767 --directory website`:
  - desktop viewport: checkout form visible, email input visible, no console errors
  - mobile viewport: checkout form visible, email input visible, no console errors
  - screenshots:
    - `validation-output/website-scout-launch/desktop-checkout.png`
    - `validation-output/website-scout-launch/mobile-checkout.png`
- Same-origin serving checkpoint:
  `python3 -m pytest tests/unit/website/test_launch_website.py tests/unit/api/test_auth.py -q`
  - Result: 10 passed.
- Live `scout serve` browser smoke:
  `python3 -m scout.cli serve --host 127.0.0.1 --port 8768`
  - `/health`: 200 with Scout `0.1.0` and Crawl4AI `0.7.7`
  - desktop `1440x1000`: root website loaded, hero visible, checkout form visible,
    no console errors
  - mobile `390x844`: root website loaded, hero visible, checkout form visible,
    no console errors
  - screenshots:
    - `validation-output/website-scout-launch/desktop-scout-serve-root.png`
    - `validation-output/website-scout-launch/mobile-scout-serve-root.png`
- Checkout missing-config browser smoke:
  - submitting the checkout form without Stripe config showed
    `Stripe Checkout is not configured.`
  - submit button re-enabled
  - server returned expected `503`
  - Chromium logged the expected failed-resource console message for that
    intentional `503`
  - screenshot:
    - `validation-output/website-scout-launch/checkout-error-scout-serve-root.png`
- Checkout readiness browser smoke:
  `python3 -m scout.cli serve --host 127.0.0.1 --port 8769`
  - page requested `/v1/billing/stripe/status`
  - hosted beta checkout button disabled when Stripe config is absent
  - status text showed `Hosted beta payment is not configured yet...`
  - console errors: 0
  - screenshot:
    - `validation-output/website-scout-launch/checkout-readiness-disabled.png`

## 2026-06-28 Positioning Refresh Verification

- Static/source checkpoint:
  `python3 -m pytest tests/unit/website/test_launch_website.py -q`
  - Result: 3 passed.
- Whitespace checkpoint:
  `git diff --check`
  - Result: passed.
- Static/lint checkpoint:
  `python3 -m pyright scout/`
  - Result: 0 errors, 0 warnings, 0 informations.
- Ruff checkpoint:
  `ruff check scout/ tests/ && ruff format --check scout/ tests/`
  - Result: all checks passed; 206 files already formatted.
- Live `scout serve` browser smoke:
  `python3 -m scout.cli serve --host 127.0.0.1 --port 8771`
  - `/health`: 200 with Scout `0.1.0` and Crawl4AI `0.7.7`
  - desktop `1440x1000`: root website loaded, evidence ledger visible,
    differentiation copy visible, export section visible, checkout form visible,
    no console errors
  - mobile `390x844`: root website loaded, evidence ledger visible,
    differentiation copy visible, export section visible, checkout form visible,
    no console errors
  - screenshots:
    - `validation-output/website-scout-launch/desktop-refresh-scout-serve.png`
    - `validation-output/website-scout-launch/mobile-refresh-scout-serve.png`
