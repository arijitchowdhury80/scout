# Company Intelligence Workflow

## User Intent

Extract a clean company profile with website, about evidence, key URLs,
leadership where available, socials, and citations.

## Required Inputs

- Company name, domain, about URL, or canonical website.
- Optional seed URLs.
- Execution mode, default `auto`.
- Working directory.

## Run States

- **Setup**: checklist validates company target and output directory.
- **Live Execution**: discovery and source capture are visible.
- **Results Review**: company profile is shown before raw records.

## Result Tabs

- Overview: company summary, industry, homepage, about page, key URLs.
- Browser: captured primary page evidence.
- Records: company, executive, and social records.
- Sources: homepage/about/source registry.
- Blocked: inaccessible pages.
- Artifacts: standard run files.
- Logs: discovery and extraction events.

## Right Drawer

Record drawer shows field-level citations for company name, description,
leadership claims, and URL evidence.

## Empty, Error, And Blocked States

No company record is a failure unless blocked evidence explains why. Missing
leadership or social links is a warning.

## Expected Artifacts

Standard artifact contract with `company.v1`, `executive.v1`, and
`company_social.v1` records where available.

## Controls

Run controls, source filters, record drawer, source drawer, download, copy source
URL, and artifact links.
