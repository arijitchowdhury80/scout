# Scout Launch Website Status

Date: 2026-06-28
Status: In progress

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

The Scout API now serves `website/index.html` at `/`, plus `/styles.css` and the
bundled IndustrialGray design-system CSS under
`/assets/warm-industrial-design-system/`. That means `scout serve` exposes the
marketing site and checkout form from the same origin as the billing API.

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
