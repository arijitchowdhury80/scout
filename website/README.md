# Scout Website

This folder contains the first static website structure for Scout's private beta
and public developer preview.

Open as a static file:

```bash
open website/index.html
```

Open through the Scout API server:

```bash
scout serve
open http://127.0.0.1:8421/
```

The page intentionally positions Scout as an acquisition-to-record workbench,
not a generic crawler replacement.

Public website paths served by `scout serve`:

- `/` - launch homepage.
- `/quickstart` - local install, Docker, workdir, and first-run guidance.
- `/pricing` - local-free and hosted-metered pricing posture.
- `/beta` - local-vs-hosted beta path and hosted checkout form.
- `/legal` - third-party notices, attribution, legal-readiness boundaries, and
  beta use cautions.
- `/docs` - FastAPI/Swagger API docs, intentionally preserved for developers.

Hosted beta checkout:

- The beta section posts to `/v1/billing/stripe/checkout-session`.
- The Scout API now serves this website at `/`, so the checkout form and billing
  API are same-origin when launched through `scout serve`.
- The page never contains Stripe secret keys; it only handles the returned
  `checkout_url` and redirects the user to Stripe.

Next website tasks:

- [x] Replace static hosted-beta CTA with checkout-session form.
- [x] Add quickstart, pricing, and private beta onboarding pages.
- [x] Add legal/third-party notices website page.
- [ ] Add a short product demo GIF/video.
- [ ] Add a separate docs-site if/when Swagger `/docs` is not enough.
- [x] Validate responsive layout in browser.
