# Careers And Jobs Workflow

## User Intent

Discover careers pages, ATS platforms, hiring signals, and job postings that
match target role, seniority, compensation, and profile preferences.

## Required Inputs

- Careers URL, company domain, job URL, or company list.
- Optional titles, seniority, compensation threshold, locations, and profile path.
- Execution mode, default `auto`.
- Working directory.

## Run States

- **Setup**: form adapts between careers discovery and job matching.
- **Live Execution**: timeline shows careers discovery, ATS detection, job fetch,
  scoring, and artifacts.
- **Results Review**: jobs and hiring signals are shown with match/reject reasons.

## Result Tabs

- Overview: ATS, departments, hiring signal summary, match counts.
- Browser: captured careers/job evidence.
- Records: career site and job posting records.
- Sources: careers pages, ATS/API pages, job pages.
- Blocked: blocked ATS/job pages.
- Artifacts: records, source pages, reports.
- Logs: matching and provider events.

## Right Drawer

Job drawer shows title, company, location, salary/OTE if available, seniority,
match score, reject reasons, citations, and source page.

## Empty, Error, And Blocked States

No jobs is acceptable only with visible no-match criteria or blocked evidence.
No careers page or ATS evidence is a failure for careers runs.

## Expected Artifacts

Standard artifact contract with `career_site.v1` and `job_posting.v1`.

## Controls

Run controls, role filters, salary/seniority fields, match filters, selected job
drawer, source links, download/export, and artifact links.
