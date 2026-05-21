# PRISM Company Intelligence Workflow

## User Intent

Build a PRISM-ready company intelligence bundle for prospect research: company,
executives, socials, investor evidence, careers, hiring signals, news, blogs,
and provenance.

## Required Inputs

- Company name, domain, or canonical website URL.
- Optional seed URLs for about, investor, careers, newsroom, or social pages.
- Execution mode, default `auto`.
- Working directory.

## Run States

- **Setup**: expected outputs show company, executives, socials, investor,
  careers, news/blogs, and citations.
- **Live Execution**: timeline separates discovery, page capture, extraction,
  enrichment, and artifact writing.
- **Results Review**: overview summarizes PRISM coverage by module.

## Result Tabs

- Overview: company snapshot and coverage grid.
- Browser: captured evidence for canonical sources.
- Records: company, executive, social, investor, career, job, and news records.
- Sources: source registry grouped by module.
- Blocked: pages that could not be captured.
- Artifacts: PRISM bundle outputs and reports.
- Logs: provider attempts and warnings.

## Right Drawer

Selecting a record shows the exact claim, source URL, citation snippet, provider,
confidence, and related records.

## Empty, Error, And Blocked States

Missing a module is a warning, not a full failure, if core company evidence and
citations exist. A full PRISM run fails if no company-level record or source
evidence is produced.

## Expected Artifacts

Standard artifact contract plus PRISM coverage summary in the report.

## Controls

Use-case selector, target input, source seed editor, mode tabs, Start/Cancel/Clear,
coverage filters, record selection, source selection, artifact links, and export.
