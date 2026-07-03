# Careers And Hiring Signals Workflow

## User Intent

Understand whether a target company is hiring, where the hiring evidence lives,
which teams are active, and what that suggests for PRISM/company intelligence.

## Required Inputs

- Company domain, careers URL, or company list.
- Execution mode, default `auto`.
- Working directory.

## Run States

- **Setup**: capture the company target and optional known careers URL.
- **Live Execution**: timeline shows careers page discovery, ATS detection,
  source capture, and artifact writing.
- **Results Review**: hiring signals are shown with citations and source links.

## Result Tabs

- Overview: ATS, careers URL, department themes, hiring signal summary.
- Browser: captured careers evidence when fallback rendering was needed.
- Records: `career_site.v1` records.
- Sources: careers pages, ATS pages, and company pages used as evidence.
- Blocked: blocked careers or ATS pages.
- Artifacts: records, source pages, reports.
- Logs: provider and extraction events.

## Right Drawer

Selected source or record drawer shows the company, careers URL, ATS/provider,
department themes, cited snippets, confidence, and source page.

## Empty, Error, And Blocked States

No careers page or ATS evidence is acceptable only when the run records searched
sources and cites the failure path. Blocked careers pages must create blocked
evidence instead of silently passing.

## Expected Artifacts

Standard artifact contract with `career_site.v1` records.

## Controls

Run controls, company target input, optional careers URL, mode selector, source
links, download/export, and artifact links.
