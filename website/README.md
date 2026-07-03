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

Design system:

- Active system: Flux (`/assets/flux-design-system/fonts.css` and
  `/assets/flux-design-system/tokens.css`).
- `styles.css` contains a small compatibility bridge for existing `wi-*`
  markup, but the active tokens, fonts, accent, grid, and component direction
  are Flux.
- Do not reintroduce `warm-industrial-design-system` links; the old system was
  too heavy for the launch/docs pages.

Public website paths served by `scout serve`:

- `/` - launch homepage.
- `/assets/scout-product-demo.gif` - beta-safe product demo GIF used by the homepage.
- `/assets/flux-design-system/fonts.css` - Flux font imports.
- `/assets/flux-design-system/tokens.css` - Flux tokens and primitives.
- `/quickstart` - consolidated Docs page covering hosted API, the
  Claude/Codex skill path, examples, artifacts, first-run guidance, and the
  capped hosted playground. Local package references are operator verification
  only.
- `/guide` and `/examples` - compatibility aliases that serve the consolidated
  Docs page. Do not reintroduce them as primary navigation items.
- `/pricing` - hosted-metered pricing posture.
- `/beta` - hosted HTTP and Claude/Codex skill beta path plus email-delivered
  beta API key form.
- `/account` - API-key based hosted account lookup for credits, usage, and
  purchase history. It does not create a login and does not persist the pasted
  key in browser storage.
- `/legal` - third-party notices, attribution, legal-readiness boundaries, and
  beta use cautions.
- `/docs` - FastAPI/Swagger API docs, intentionally preserved for exact API
  schemas.

Hosted beta registration:

- The beta section posts to `/v1/hosted/beta-key` with name and email. Scout
  provisions the hosted beta account and emails the API key when SMTP delivery
  is configured.
- The Scout API now serves this website at `/`, so the registration form and
  hosted API are same-origin when launched through `scout serve`.
- The page never contains SMTP, Stripe, or Scout secret keys; it only collects
  signup inputs, then relies on server-side provisioning and SMTP key delivery.
- The beta page also describes support expectations: GitHub private-beta issue
  templates for non-security feedback, private reporting for vulnerabilities,
  and no secrets in public issues.
- Hosted users can open `/account`, paste their delivered API key, and inspect
  `/v1/hosted/me`, `/v1/hosted/usage`, and `/v1/hosted/purchases` without a
  password gate.

Hosted playground:

- The Docs page includes a public `/v1/playground/run` demo for try-before-buy
  usage across Scout's core acquisition, commerce, intelligence, and evidence
  workflows.
- Anonymous runs are intentionally capped: products return up to 10 records,
  crawl/map return up to 5 pages, intelligence workflows return up to 10
  records, and single-page workflows use a 30 second timeout.
- The playground rejects local/private network URLs, returns downloadable JSON
  and Markdown directly to the browser, and does not grant access to paid
  `/v1/hosted/*` API routes.

Next website tasks:

- [x] Replace static hosted-beta CTA with beta key generation form.
- [x] Add quickstart, pricing, and private beta onboarding pages.
- [x] Consolidate quickstart, guide, examples, and API-guide content into one
      Docs page while keeping `/docs` as Swagger.
- [x] Add legal/third-party notices website page.
- [x] Add private beta support and onboarding guidance.
- [x] Add a short product demo GIF/video.
- [x] Add a capped hosted playground to the Docs page.
- [x] Add a separate docs-site if/when Swagger `/docs` is not enough.
- [x] Validate responsive layout in browser.
