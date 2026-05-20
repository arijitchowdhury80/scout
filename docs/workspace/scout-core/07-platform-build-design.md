# Scout Platform Build Design

Date: 2026-05-15

## Decision

All identified use cases are required, but they should not be implemented as separate one-off scrapers. Scout will be built as a shared web-to-record platform with domain modules on top.

The build target is:

```text
Intent -> Discovery -> Provider Fetch -> Extraction -> Enrichment -> Validation -> Records -> Artifacts
```

This design covers the UX, invocations, input data, validation, and output contracts for every major use case before implementation.

## Core Product Model

Scout is not a crawler-first tool. Scout is a web-to-record engine.

```text
Scout Core
  - provider contracts
  - source evidence model
  - run manifest
  - schema validation
  - artifact writer
  - quality scoring
  - extraction registry

Use-Case Modules
  - products
  - jobs
  - company intelligence
  - investor intelligence
  - generic research
  - website quality
  - docs extraction
  - news monitoring
  - social normalization
  - location/store extraction

Providers
  - websearch host provider
  - webfetch host provider
  - crawl4ai provider
  - browser/session provider
  - cdp/profile provider
  - saved html/dom provider
  - pdf/document provider
  - ATS provider adapters
  - social/provider import adapters
```

## UX Principles

### 1. One command family, multiple use cases

Scout should expose a small, predictable command surface:

```bash
scout run <use-case> [options]
scout plan <use-case> [options]
scout validate <run-dir>
scout replay <run-dir-or-fixture>
scout init-profile <profile-type>
```

Existing commands like `scrape`, `crawl`, `map`, and `products` can stay as low-level commands, but the main experience should become `scout run`.

### 2. Skill mode should feel conversational

Example:

```text
Use Scout to find AI product marketing jobs, salary above $160k, remote or New York. First find relevant companies, then find open jobs and save a daily watchlist.
```

The skill should:

1. Ask missing intake questions.
2. Create a typed profile.
3. Run discovery.
4. Present candidate companies for approval.
5. Run extraction.
6. Save artifacts.

### 3. CLI mode should be deterministic

Every workflow must be invokable without a chat agent:

```bash
scout run jobs --profile job-profile.yaml --output-dir scout-runs/jobs-ai-pm
scout run prism --company nike --output-dir scout-runs/prism-nike
scout run products --site esteelauder.com --query "top categories" --limit 10
```

### 4. Provider availability must be explicit

Skill-only providers such as WebFetch/WebSearch must be represented as host providers. Standalone CLI cannot pretend it has them.

Provider examples:

```bash
--provider auto
--provider crawl4ai
--provider saved
--provider cdp
--provider host-webfetch
--provider host-browser
```

## Global Input Model

Every high-level run should normalize user input into a `ScoutRunRequest`.

```json
{
  "use_case": "jobs",
  "query": "AI product marketing roles, remote or New York, salary above 160k",
  "targets": [],
  "profile_path": "job-profile.yaml",
  "providers": ["auto"],
  "output_dir": "scout-runs/jobs-ai-product-marketing",
  "limits": {
    "max_targets": 25,
    "max_records": 250
  },
  "schedule": {
    "enabled": true,
    "frequency": "daily"
  }
}
```

Validation:

- `use_case` is required.
- Either `query`, `targets`, or `profile_path` is required.
- `output_dir` is required in non-interactive mode or derived deterministically.
- Provider list must be supported by the runtime environment.
- Limits must be positive and bounded.

## Global Output Model

Every high-level run writes:

```text
run-dir/
  manifest.json
  records.json
  records.jsonl
  source_pages.json
  blocked_pages.json
  validation.json
  extraction_report.md
  raw/
```

`manifest.json` must include:

- run ID
- use case
- query
- started/finished timestamps
- providers attempted
- record counts
- validation summary
- errors and warnings

`records.jsonl` must contain one record per line for Algolia/RAG/indexing workflows.

`source_pages.json` must preserve provenance.

`blocked_pages.json` must include blocked/failed URLs and provider failures.

## Use-Case Invocations

### UC-01 Products

Skill:

```text
Use Scout to find the top categories for Estee Lauder and get 10 products each with all attributes, price, color, review, and variants. Also get top 10 best sellers.
```

CLI:

```bash
scout run products \
  --site esteelauder.com \
  --query "top categories plus best sellers" \
  --limit-per-category 10 \
  --output-dir scout-runs/esteelauder-products
```

Input profile:

```yaml
use_case: products
site: esteelauder.com
query: top categories plus best sellers
categories:
  - skincare
  - makeup
  - fragrance
  - sets-gifts
  - best-sellers
limit_per_category: 10
required_fields:
  - name
  - url
  - price
  - category
  - review_count
  - rating
  - variants
  - colors
  - sizes
  - images
```

Output records:

- `ProductRecord`
- `CategoryRecord`

Validation:

- Product URL is not a category URL.
- Name and URL are required.
- Price must parse to number when present.
- Ratings must be numeric and bounded 0-5.
- Review count must be integer when present.
- Variants/colors/sizes must be arrays.

### UC-02 Jobs / Job Hunter

Skill:

```text
Use Scout as my job hunter. I am looking for AI product marketing, developer advocate, and solutions engineering roles, remote or New York, salary above $160k. First find companies in that area, then find open jobs at those companies. Run this daily.
```

CLI:

```bash
scout run jobs \
  --profile job-profile.yaml \
  --output-dir scout-runs/job-hunter-ai-pm
```

Input profile:

```yaml
use_case: jobs
desired_titles:
  - AI Product Marketing Manager
  - Developer Advocate
  - Solutions Engineer
role_keywords:
  - AI
  - search
  - developer platform
  - ecommerce
salary_min_usd: 160000
locations:
  - Remote
  - New York
seniority:
  - Senior
  - Principal
target_company_discovery:
  enabled: true
  max_companies: 50
monitoring:
  enabled: true
  frequency: daily
```

Output records:

- `JobSearchProfile`
- `TargetCompanyRecord`
- `JobPostingRecord`
- `JobDeltaRecord`

Validation:

- Job URL must be official company/ATS URL.
- Title must match at least one keyword/title rule or explain why it was included.
- Salary must include currency and range when present.
- Deltas must compare against previous run manifests.
- Scout must not apply to jobs or submit forms.

### UC-03 PRISM Company Intelligence

Skill:

```text
Use Scout for PRISM research on Nike. Find the company website, LinkedIn, company socials, executives and their LinkedIn profiles, investor page, careers page, newsroom, ecommerce/product pages, hiring signals, and relevant evidence for Algolia.
```

CLI:

```bash
scout run prism \
  --company nike \
  --output-dir scout-runs/prism-nike
```

Input profile:

```yaml
use_case: prism
company: Nike
required_sources:
  - canonical_website
  - linkedin
  - socials
  - about
  - leadership
  - executives
  - investor
  - careers
  - newsroom
  - products
  - hiring_signals
```

Output records:

- `CompanyRecord`
- `CompanySocialRecord`
- `ExecutiveRecord`
- `InvestorDocumentRecord`
- `JobPostingRecord`
- `ProductRecord`
- `NewsArticleRecord`
- `EvidenceBundle`

Validation:

- Official source URLs must be separated from third-party URLs.
- Executive LinkedIn URLs must not be invented.
- Every evidence claim must include a source URL.
- PRISM summaries must not contain naked claims without source records.

### UC-04 Investor Intelligence

CLI:

```bash
scout run investor --company salesforce --ticker CRM --output-dir scout-runs/investor-salesforce
```

Output records:

- `InvestorDocumentRecord`
- `FinancialMetricRecord`
- `RiskFactorRecord`
- `ExecutiveQuoteRecord`

Validation:

- Metrics require period, unit, currency where applicable, and source.
- PDF text extraction must be fixture-tested.
- 10-K/10-Q/annual report documents must be classified correctly.

### UC-05 Generic Research

CLI:

```bash
scout run research \
  --query "companies with poor websites in local dental clinics in Austin" \
  --output-dir scout-runs/research-dental-sites
```

Output records:

- `SearchResultRecord`
- `CompanyPageRecord`
- `WebsiteAssessmentRecord`
- `OpportunityEvidenceRecord`

Validation:

- Scout must separate objective signals from subjective assessment.
- Website quality scores must explain evidence.
- Candidate companies must include source URL and reason discovered.

### UC-06 Website Quality

CLI:

```bash
scout run website-quality \
  --urls urls.txt \
  --rubric website-rubric.yaml \
  --output-dir scout-runs/website-quality
```

Output records:

- `WebsiteAssessmentRecord`
- `PageQualitySignal`

Validation:

- Rubric must be explicit.
- Signals such as broken links, missing CTA, low content depth, mobile issues, or accessibility issues must be evidence-backed.
- Screenshots should be attached when browser provider is available.

### UC-07 Documentation Extraction

CLI:

```bash
scout run docs \
  --site https://www.algolia.com/doc/api-reference \
  --output-dir scout-runs/algolia-docs
```

Output records:

- `DocumentationPageRecord`
- `CodeExampleRecord`
- `APIMethodRecord`

Validation:

- Code blocks must be preserved.
- Heading hierarchy must be retained.
- Canonical URL is required.

### UC-08 News Monitoring

CLI:

```bash
scout run news \
  --company nike \
  --days 60 \
  --output-dir scout-runs/news-nike
```

Output records:

- `NewsArticleRecord`
- `CompanySignalRecord`

Validation:

- Dates must parse.
- Recency filter must be respected.
- Signal classification must cite article text.

### UC-09 Social Normalization

CLI:

```bash
scout run social \
  --provider-input linkedin-export.json \
  --company nike \
  --output-dir scout-runs/social-nike
```

Output records:

- `SocialSignalRecord`

Validation:

- Social provider must be explicit.
- Scout should not claim raw LinkedIn/X crawling unless a provider is validated.
- Every post must include platform, URL or ID, timestamp when available, and provider provenance.

### UC-10 Store Locator

CLI:

```bash
scout run locations \
  --site nike.com \
  --query "stores in New York" \
  --output-dir scout-runs/nike-ny-stores
```

Output records:

- `LocationRecord`

Validation:

- Address components must parse.
- Store URL or locator source is required.
- Hours/services are optional but must be structured when present.

## Test Strategy

### Test Layers

1. Unit tests:
   - schemas
   - validators
   - ID generation
   - field normalization
   - merge/dedupe logic

2. Fixture tests:
   - saved HTML
   - saved markdown
   - saved DOM snapshots
   - saved provider JSON
   - saved PDF text

3. Contract tests:
   - artifact shape
   - records.jsonl validity
   - manifest fields
   - blocked pages fields

4. Live smoke tests:
   - one or more representative websites per use case
   - marked separately from deterministic tests

5. Scheduled/delta tests:
   - previous run + current run diff
   - new/changed/closed jobs
   - new articles

## Build Phases

### Phase 0 - Platform Foundation

Build provider contracts, source evidence, run manifest, artifact writer, schema registry, and content-ingest mode.

This phase does not solve every use case. It makes every use case possible.

### Phase 1 - Three Vertical Slices

Build three high-pressure vertical slices in parallel design, sequential execution:

1. Products
2. Jobs
3. PRISM company intelligence

These validate listing/detail enrichment, scheduled deltas, and composite evidence bundles.

### Phase 2 - Investor, Docs, News

Add document/PDF parsing, docs chunking, and newsroom monitoring.

### Phase 3 - Website Quality, Generic Research, Locations, Social

Add rubric-based website quality, search-driven research, locator extraction, and social provider normalization.

## Non-Negotiables

- No raw dicts crossing module boundaries.
- Every provider result has provenance.
- Every record has schema version.
- Every run has artifacts.
- Every use case has fixture tests before live tests.
- Live tests can fail due to site changes; fixture tests define deterministic correctness.
- Skill-host capabilities and standalone CLI capabilities must be documented separately.

