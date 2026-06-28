# Scout Website

This folder contains the first static website structure for Scout's private beta
and public developer preview.

Open locally:

```bash
open website/index.html
```

The page intentionally positions Scout as an acquisition-to-record workbench,
not a generic crawler replacement.

Hosted beta checkout:

- The beta section posts to `/v1/billing/stripe/checkout-session`.
- The route must be served from the same origin as the Scout API or proxied to
  it.
- The page never contains Stripe secret keys; it only handles the returned
  `checkout_url` and redirects the user to Stripe.

Next website tasks:

- [x] Replace static hosted-beta CTA with checkout-session form.
- [ ] Add a short product demo GIF/video.
- [ ] Add docs links after public docs are organized.
- [ ] Add legal/third-party notices link.
- [x] Validate responsive layout in browser.
