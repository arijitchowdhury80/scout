# ADR: Frontend moves from embedded Python string to a no-build static SPA

- **Date:** 2026-06-12
- **Status:** Accepted (Phase B design decision; implementation lands in Phase C2)

## Context

The entire Scout UI lives in `scout/api/frontend.py` as a ~1,600-line Python string containing HTML, CSS, and JavaScript. It has already hit maintainability limits (string-escaping, no syntax tooling, unit tests assert on substrings). Phase C adds per-use-case result views, SSE streaming, an embedded live browser pane, editable settings, run history, and an Algolia push flow — the surface roughly triples.

## Decision

Move the frontend to **plain static files served by FastAPI** — no build step, no npm, no framework:

```
scout/api/static/
  index.html
  app.css
  js/
    app.mjs          # entry; state + router
    api.mjs          # fetch wrapper, SSE client
    views/*.mjs      # one module per screen
```

- Served via `StaticFiles` mount; `/app` keeps serving `index.html` so URLs, tests, and the skill definition are unchanged.
- ES modules give file separation and browser-native imports without a toolchain.
- No React/Vue/Vite: a single-operator internal tool does not justify adding a Node toolchain to a Python project; the deployment story stays `pip install` + `scout serve`.

## Migration rule (regression safety)

The extraction is a **pure mechanical move commit**: current markup/CSS/JS lifted into files with zero behavior change, full e2e suite green before any restyling or new features. Only then does the redesign apply on top.

## Consequences

- Unit tests asserting on the HTML string move to asserting on served responses (same TestClient calls — `GET /app` still returns the markup).
- The API key currently interpolated into the HTML needs a serving change (template the key into `index.html` at request time, or move to a session-token endpoint — decided in C0.5 alongside settings/secrets work).
- Frontend code becomes reviewable, lintable, and diffable like any other code.

## Rejected alternatives

- **Keep the embedded string**: fails at Phase C scale; already failing.
- **React/Vite SPA**: build toolchain, dependency churn, and packaging complexity for one internal operator; nothing in the UI needs virtual-DOM scale.
- **Server-rendered templates (Jinja)**: the app is interaction-heavy (live runs, streaming, browser pane); client-side state is the natural model.
