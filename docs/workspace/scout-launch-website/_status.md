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

## 2026-06-28 Launch-Truth Checkpoint

The launch homepage now includes a visible `Launch status` section. This is
deliberate: Scout should not look more production-ready than the current
security evidence supports.

The new page copy states:

- Public launch is blocked by the unresolved Crawl4AI/lxml dependency audit
  finding.
- Private beta is limited, approved-tester only, capped, and metered.
- Local install remains the primary path for beta use.
- Hosted beta is finite credit, not unlimited hosted scraping.
- Scout makes no clean hosted-production security claim until the launch gates
  close.

Verification:

- `python3 -m pytest tests/unit/website/test_launch_website.py -q`
  - Result: `4 passed, 2 warnings`.
- Live `scout serve` browser smoke:
  `python3 -m scout.cli serve --host 127.0.0.1 --port 8783`
  - desktop `1440x1000`: root website loaded, launch-status section visible,
    checkout readiness endpoint returned 200, console errors/warnings: 0
  - mobile `390x844`: root website loaded, launch-status section visible,
    checkout readiness endpoint returned 200, console errors/warnings: 0
  - screenshots:
    - `validation-output/website-scout-launch/desktop-launch-status-scout-serve.png`
    - `validation-output/website-scout-launch/mobile-launch-status-scout-serve.png`

## 2026-06-28 Beta-Onboarding Pages Checkpoint

The website now has reachable onboarding pages beyond the homepage:

- `/quickstart` and `/quickstart.html` for local install, Docker, workdir, and
  first-run artifact inspection.
- `/pricing` and `/pricing.html` for the local-free / hosted-metered pricing
  posture.
- `/beta` and `/beta.html` for local-vs-hosted beta paths plus the hosted beta
  checkout form.

Decision: keep `/docs` as FastAPI/Swagger API docs for now. The website uses
`/quickstart` for user-facing onboarding so we do not break the developer API
documentation path.

Verification:

- `python3 -m pytest tests/unit/website/test_launch_website.py -q`
  - Result: `7 passed, 2 warnings`.
- Live `scout serve` browser smoke:
  `python3 -m scout.cli serve --host 127.0.0.1 --port 8784`
  - routes checked: `/`, `/quickstart`, `/pricing`, `/beta`
  - viewports checked: desktop `1440x1000`, mobile `390x844`
  - all pages rendered required headings
  - `/beta` and `/` checkout readiness endpoint returned 200
  - console errors/warnings: 0
  - screenshots:
    - `validation-output/website-scout-launch/home-beta-onboarding-desktop.png`
    - `validation-output/website-scout-launch/home-beta-onboarding-mobile.png`
    - `validation-output/website-scout-launch/quickstart-beta-onboarding-desktop.png`
    - `validation-output/website-scout-launch/quickstart-beta-onboarding-mobile.png`
    - `validation-output/website-scout-launch/pricing-beta-onboarding-desktop.png`
    - `validation-output/website-scout-launch/pricing-beta-onboarding-mobile.png`
    - `validation-output/website-scout-launch/beta-beta-onboarding-desktop.png`
    - `validation-output/website-scout-launch/beta-beta-onboarding-mobile.png`
- Explicit-route smoke after removing the catch-all route:
  `python3 -m scout.cli serve --host 127.0.0.1 --port 8785`
  - routes checked: `/`, `/quickstart`, `/pricing`, `/beta`, `/docs`
  - `/docs` page title remained `Scout - Swagger UI`
  - console errors/warnings: 0
  - screenshots:
    - `validation-output/website-scout-launch/home-beta-onboarding-routes.png`
    - `validation-output/website-scout-launch/quickstart-beta-onboarding-routes.png`
    - `validation-output/website-scout-launch/pricing-beta-onboarding-routes.png`
    - `validation-output/website-scout-launch/beta-beta-onboarding-routes.png`
    - `validation-output/website-scout-launch/api-docs-preserved-routes.png`

## 2026-06-28 Legal And Third-Party Notices Checkpoint

The website now has a public `/legal` and `/legal.html` page for beta users and
distributors. It covers:

- Crawl4AI attribution.
- Apache License, Version 2.0 notice for Crawl4AI.
- Not-legal-advice warning.
- Responsible acquisition and user permission boundaries.
- Scout license not final.
- Public launch still blocked by the unresolved dependency audit gate.

Decision: this is a readiness/notice page, not final legal terms or a privacy
policy. Terms/privacy placeholders remain open in the release checklist until
the hosted beta policy is approved.

Verification:

- `python3 -m pytest tests/unit/website/test_launch_website.py -q`
  - Result: `8 passed, 2 warnings`.
- Live `scout serve` browser smoke:
  `python3 -m scout.cli serve --host 127.0.0.1 --port 8786`
  - route checked: `/legal`
  - viewports checked: desktop `1440x1000`, mobile `390x844`
  - legal page rendered required notices and attribution
  - console errors/warnings: 0
  - screenshots:
    - `validation-output/website-scout-launch/legal-notices-desktop.png`
    - `validation-output/website-scout-launch/legal-notices-mobile.png`

## 2026-06-28 Notices Packaging Checkpoint

The third-party notices are now part of the distribution artifact contract:

- `pyproject.toml` force-includes `THIRD_PARTY_NOTICES.md` in the wheel.
- Docker build context preserves `THIRD_PARTY_NOTICES.md`.
- Dockerfile copies `THIRD_PARTY_NOTICES.md` before `pip install .`.
- Scout serves the notices locally at `/third-party-notices` and
  `/THIRD_PARTY_NOTICES.md`.

Verification:

- `python3 -m pytest tests/unit/test_package_metadata.py tests/unit/test_docker_distribution.py tests/unit/website/test_launch_website.py -q`
  - Result: `17 passed, 2 warnings`.
- Focused launch-route regression:
  `python3 -m pytest tests/unit/test_package_metadata.py tests/unit/test_docker_distribution.py tests/unit/website/test_launch_website.py tests/unit/api/test_auth.py tests/unit/api/test_app_frontend.py -q`
  - Result: `37 passed, 2 warnings`.
- `python3 -m build`
  - Result: successfully built `scout_web-0.1.0.tar.gz` and
    `scout_web-0.1.0-py3-none-any.whl`.
- Artifact inspection confirmed:
  - wheel contains `THIRD_PARTY_NOTICES.md` and `website/legal.html`.
  - sdist contains `THIRD_PARTY_NOTICES.md` and `website/legal.html`.
- Live `scout serve` route smoke:
  `python3 -m scout.cli serve --host 127.0.0.1 --port 8787`
  - `curl -fsS http://127.0.0.1:8787/third-party-notices`
  - Result: `200 OK`, `text/plain`, includes `Third-Party Notices`,
    `Crawl4AI`, and `Apache License, Version 2.0`.

## 2026-06-28 Dependency License Inventory Checkpoint

Generated a runtime dependency license inventory from a clean virtual
environment:

```bash
rm -rf /tmp/scout-license-inventory-venv
python3 -m venv /tmp/scout-license-inventory-venv
/tmp/scout-license-inventory-venv/bin/python -m pip install --upgrade pip
/tmp/scout-license-inventory-venv/bin/python -m pip install .
/tmp/scout-license-inventory-venv/bin/python scripts/generate_dependency_license_inventory.py
```

Output:

- `docs/legal/dependency-license-inventory-2026-06-28.md`

The inventory is explicitly metadata-derived and not legal advice. It flags
packages with missing license metadata for manual upstream review and keeps the
`lxml` / `PYSEC-2026-87` Crawl4AI dependency risk visible.
