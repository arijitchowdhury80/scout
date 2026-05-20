# Scout Use Cases

Scout is a multi-use-case web intelligence platform. These workflows share one
execution model, one artifact contract, and typed vertical records.

## Company Intelligence

Goal: discover and extract a company's official website, about page,
leadership, social profiles, and key URLs.

```bash
scout run company --query Adobe --mode auto --output-dir ./scout-runs/adobe-company
```

Records:

- `company.v1`
- `executive.v1`
- `company_social.v1`

Test targets: all primary targets in [docs/target-matrix.md](target-matrix.md).

## PRISM Prospect Research

Goal: create an Algolia prospect research bundle with company, executives,
socials, investor context, careers/hiring, and recent news.

```bash
scout run prism --query Nike --mode auto --output-dir ./scout-runs/nike-prism
```

Records: company, executive, company social, investor, career, and news records.

Test targets: all primary targets in [docs/target-matrix.md](target-matrix.md).

## Investor Intelligence

Goal: collect investor relations pages, reports, presentations, filings,
financial events, and source URLs.

```bash
scout run investor --query Salesforce --mode auto --output-dir ./scout-runs/salesforce-investor
```

Records:

- `investor_asset.v1`

Test targets: Adobe, Home Depot, Estée Lauder where public-parent evidence is
available, and British Airways where public-parent evidence is useful.

## Careers And Hiring

Goal: identify careers pages, ATS platform, departments, hiring signals, and
role categories.

```bash
scout run careers --query Algolia --mode auto --output-dir ./scout-runs/algolia-careers
```

Records:

- `career_site.v1`

Test targets: all primary targets in [docs/target-matrix.md](target-matrix.md).

## Job Hunter

Goal: find and score high-quality roles against a private profile. Scout should
first discover likely companies, then find roles at those companies, then score
jobs by title, seniority, compensation, location, skills, and strategic fit.

```bash
scout run jobs \
  --profile ./private-job-profile.yaml \
  --job-url https://job-boards.greenhouse.io/eve/jobs/4245857009 \
  --mode api \
  --output-dir ./scout-runs/job-hunter
```

Records:

- `job_posting.v1`

Boundaries:

- Scout does not auto-apply.
- Private resume-derived data belongs in ignored local profiles or vault files.
- Public fixtures must stay sanitized.

Test targets: all primary targets plus ATS fixtures for Greenhouse, Lever,
Ashby, and Workday.

## Product Catalogs

Goal: crawl product/category pages, extract product attributes, and prepare
records that can power Algolia indexing, search, and PDP experiences.

```bash
scout products "top products" \
  --site lacoste.com \
  --limit-per-category 10 \
  --max-categories 10 \
  --output-dir ./scout-runs/lacoste-products
```

High-level platform entry:

```bash
scout run products --query "top skincare products" --mode auto --output-dir ./scout-runs/products
```

Records:

- product records with stable `objectID`, URL, name, brand, image, price,
  categories, variants, rating/review fields, and provenance when available.

Test targets: L.L.Bean, Patagonia, Home Depot, Estée Lauder, and Nike.

## News And Signals

Goal: capture newsroom/blog/recent announcement signals and preserve source
links for later analysis.

```bash
scout run news --query "Adobe AI announcements" --mode websearch --output-dir ./scout-runs/adobe-news
```

Records:

- `news_signal.v1`

Test targets: all primary targets in [docs/target-matrix.md](target-matrix.md),
including latest 3-5 blog posts when available.

## Generic Research

Goal: retrieve and normalize page, site, or document evidence for broad web
research. Examples include website quality research, documentation extraction,
market mapping, and opportunity discovery.

```bash
scout run research --query "companies with weak ecommerce search UX" --mode auto --output-dir ./scout-runs/research
```

Records:

- `research_record.v1`

Test targets: British Airways, Algolia docs/blog, Constructor docs/blog,
Amplience site/docs, company about pages, PDFs, and simple marketing pages.

## Citation Requirements

Every use case should preserve citation-grade provenance:

- `source_pages.json` records fetched or supplied source evidence by
  deterministic `source_id`.
- `records.json` and `records.jsonl` include `citations[]` for fields and
  claims extracted from those sources.
- `validation.json` reports `missing_citations` when a record is emitted
  without structured citations.
