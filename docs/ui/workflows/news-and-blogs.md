# News And Blogs Workflow

## User Intent

Find recent company news, newsroom posts, press releases, and blogs with dates,
URLs, summaries, and citations.

## Required Inputs

- Company domain, newsroom URL, blog URL, or search query.
- Optional recency window and max items.
- Execution mode, default `auto`.
- Working directory.

## Run States

- **Setup**: target and recency controls.
- **Live Execution**: discovery separates official pages, feeds, and search.
- **Results Review**: latest items appear in date order with source evidence.

## Result Tabs

- Overview: latest themes and coverage.
- Browser: captured source pages.
- Records: news and blog records.
- Sources: newsroom/blog/feed/search result sources.
- Blocked: blocked pages.
- Artifacts: records and reports.
- Logs: discovery and extraction events.

## Right Drawer

Selected item shows headline, date, URL, summary, source snippet, provider, and
confidence.

## Empty, Error, And Blocked States

If no official news/blog exists, Scout should show the searched sources and say
what was not found. Silent zero records is a failure.

## Expected Artifacts

Standard artifact contract with `news_signal.v1` records.

## Controls

Run controls, recency filters, type filters, source/citation drawer, export, and
artifact links.
