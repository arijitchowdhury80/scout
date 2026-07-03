# Scout UI Workflow Specs

These workflow specs are the UX contract for the app-first Scout interface.
They are intentionally written before the next UI build pass so implementation,
validation, and vault documentation stay aligned.

## Approved Base Model

Scout uses one workspace with three run states:

1. **Run Setup**: configure use case, target, mode, crawl settings, and working
   directory.
2. **Live Execution**: show the run ID immediately, stream timeline/log events,
   show captured browser/source evidence, and allow cancel/clear.
3. **Results Review**: review records, sources, blocked pages, artifacts, logs,
   and selected record/source details in a right drawer.

## Workflow Pages

| Workflow | Spec |
|---|---|
| Products and Algolia prep | `products-and-algolia.md` |
| PRISM company intelligence | `prism-company-intelligence.md` |
| Company intelligence | `company-intelligence.md` |
| Investor intelligence | `investor-intelligence.md` |
| Careers and hiring signals | `careers-hiring-signals.md` |
| News and blogs | `news-and-blogs.md` |
| Research and documentation | `research-and-documentation.md` |
| History, presets, and targets | `history-presets-targets.md` |
| Data, integrations, settings, and help | `data-integrations-settings-help.md` |

## Mockup Status

The approved visual direction is stored at
`docs/design/scout-app-first-ux-approved-mockup-2026-05-21.png`. The individual
workflow pages below define screen behavior and data contracts; visual mockups
for each workflow remain the next design artifact before deeper UI implementation.
