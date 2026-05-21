# Scout App-First UI Redesign

## Decision

Scout's primary product surface is now the standalone HTTP app. CLI, API, and
skill interfaces remain important, but the app drives the user experience first:
every run must be visible, cancellable, resettable, and evidence-driven.

## UX Model

The app is organized around three states:

1. **Run Setup**: use case, target URL, execution mode, crawl settings, working
   directory, checklist, Start Execution, Clear Run, and collapsed Developer
   Details.
2. **Live Execution**: active run ID, run state, progress timeline, inline
   browser evidence preview, event log, Cancel Run, and Clear Run.
3. **Results Review**: metrics plus a unified workspace for overview, browser
   evidence, records, sources, blocked pages, artifacts, and logs.

Product Workbench and Evidence Browser are intentionally merged. Records,
citations, source pages, blocked details, and artifacts belong to one run
review experience, with a right drawer for selected record/source context.

## Backend Model

The frontend uses `/app/runs` as the app run-session API:

- `POST /app/runs` creates a run ID immediately and queues execution.
- `GET /app/runs/{run_id}` polls state, records, sources, blocked pages,
  artifacts, browser evidence, warnings, and errors.
- `GET /app/runs/{run_id}/events` returns the timeline/event stream.
- `POST /app/runs/{run_id}/cancel` marks an in-flight run cancelled.
- `POST /app/runs/{run_id}/reset` removes a run from the in-memory app registry.

The app-run API is intentionally separate from the older `/run/{use_case}` and
`/products` endpoints so the frontend can provide live state without breaking
existing CLI/API contracts.

## Estée Lauder Hard-Site Behavior

Scout should not show an empty product table when listing-level products are
available. The product path preserves listing-derived records and reports
detail-page failures separately. If Scout's crawler context is blocked while the
user's normal browser can view the page, the UI must say that clearly and show
the attempted provider/fallback evidence.

## Verification Added

- Unit tests for `/app/runs` create, events, cancel, and reset.
- Browser E2E tests for the app-first shell, Start Execution, Cancel Run,
  Clear Run, selected-record drawer, Crawl Settings, and Developer Details.
- Frontend smoke tests updated to reject the old hardcoded workbench shell.

## Regression Guardrails

This redesign exposed a failure mode we must not repeat: a UI can look polished
while still being functionally dishonest. Scout should treat every visible
interactive element as a contract.

Rules going forward:

- No fake clickable controls. If a button, tab, menu, or nav item is visible and
  enabled, it must change state, call the backend, navigate, copy, download, or
  open a real control.
- Unimplemented controls must be visibly disabled with a clear reason.
- Browse must use one directory-selection path only. A native file/directory
  chooser cancellation must not trigger a second custom dialog.
- E2E tests must cover newly visible controls, not only happy-path run flow.
- After frontend changes, restart the local server and validate the actual
  running `/app` in a browser. Do not trust stale server output.
- Manual browser validation must include console errors, visual state changes,
  and at least one negative path such as canceling a picker or clearing a run.

Current regression tests cover:

- Native directory picker updates the single Working Directory field.
- No `workdirDialog` fallback is present after Browse.
- Disabled rail/top-nav controls are not clickable placeholders.
- Crawl Settings removal/restoration updates the UI.
- Developer Details remains secondary and copyable.
