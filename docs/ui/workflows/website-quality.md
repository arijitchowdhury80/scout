# Website Quality Workflow

## User Intent

Analyze a website against UX, content, navigation, trust, speed/performance
signals, search/discovery, and competitor comparison where provided.

## Required Inputs

- Website URL.
- Optional competitor URL.
- Optional focus area such as ecommerce, B2B SaaS, travel, careers, or investor.
- Execution mode, default `auto`.
- Working directory.

## Run States

- **Setup**: website and optional competitor input.
- **Live Execution**: page capture, evidence collection, heuristic checks.
- **Results Review**: findings grouped by severity and evidence.

## Result Tabs

- Overview: quality score, top findings, benchmark notes.
- Browser: captured screenshots and page evidence.
- Records: findings and recommendations.
- Sources: pages used for findings.
- Blocked: unavailable pages.
- Artifacts: report and source files.
- Logs: checks run and warnings.

## Right Drawer

Finding drawer shows severity, affected page, evidence screenshot/snippet,
recommendation, and citation.

## Empty, Error, And Blocked States

A quality run fails if it cannot capture any source page. It can pass with
warnings if only competitor capture fails.

## Expected Artifacts

Standard artifact contract plus website-quality report.

## Controls

Run controls, severity filters, finding drawer, screenshot/source selector,
export report, and artifact links.
