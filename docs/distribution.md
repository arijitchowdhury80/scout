# Distribution

Scout is distributed as a standalone Python package and can also be installed
as a Claude/Codex skill integration.

## Standalone Package

```bash
pip install scout-web
# or until the first package release:
pip install git+https://github.com/arijitchowdhury80/scout.git
playwright install chromium
```

## Development Install

```bash
git clone https://github.com/arijitchowdhury80/scout.git
cd scout
pip install -e ".[dev]"
playwright install chromium
```

## Local Configuration

Use `.env.local` for private keys and machine-specific defaults:

```bash
cp .env.example .env.local
```

Supported local settings:

```text
SCOUT_API_KEY=change-me
LLM_API_KEY=
SCOUT_WORKDIR=scout-runs
DB_PATH=
HOSTED_ACCOUNT_DB_PATH=
HOSTED_RATE_LIMIT_MAX_REQUESTS=60
HOSTED_RATE_LIMIT_WINDOW_SECONDS=60
HOST=0.0.0.0
PORT=8421
```

`.env.local` is ignored by git. Store API keys, local working directories, and
developer-only overrides there. For shared deployment defaults, use environment
variables or a deployment-managed `.env`.

`SCOUT_WORKDIR` is the base directory for generated run folders when a caller
does not pass an exact `--output-dir` or JSON `output_dir`.

## Hosted Beta Configuration

Local use does not require Stripe or SMTP. Paid hosted beta does.

Minimum Stripe Checkout settings:

```text
STRIPE_SECRET_KEY=sk_test_...
STRIPE_BETA_PRICE_ID=price_...
STRIPE_SUCCESS_URL=https://your-domain.example/?checkout=success
STRIPE_CANCEL_URL=https://your-domain.example/?checkout=cancelled
```

Payment-confirmed provisioning also needs:

```text
STRIPE_WEBHOOK_SECRET=whsec_...
HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.example.com
HOSTED_KEY_DELIVERY_SMTP_PORT=587
HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL=scout@example.com
HOSTED_KEY_DELIVERY_SMTP_USERNAME=
HOSTED_KEY_DELIVERY_SMTP_PASSWORD=
HOSTED_KEY_DELIVERY_SMTP_USE_TLS=true
```

Hosted API requests also have a private-beta per-key throttle:

```text
HOSTED_RATE_LIMIT_MAX_REQUESTS=60
HOSTED_RATE_LIMIT_WINDOW_SECONDS=60
```

`/v1/hosted/*` requests that exceed the configured window return `429` with a
`Retry-After` header and do not spend hosted credits. The current limiter is
in-memory and process-local. It is enough for a single-node private beta, but a
multi-instance hosted launch still needs a shared limiter such as Redis or an
API-gateway/WAF policy.

Scout exposes a non-secret readiness check for the website:

```bash
curl http://localhost:8421/v1/billing/stripe/status
```

It returns only booleans for checkout, webhook, key delivery, and end-to-end
paid key delivery readiness. It never returns Stripe, SMTP, or Scout API
secrets.

After a hosted beta user receives a `scout_live_...` API key, they can inspect
their plan limits and remaining credits:

```bash
curl http://localhost:8421/v1/hosted/me \
  -H "Authorization: Bearer ${SCOUT_HOSTED_API_KEY}"
```

The response includes tenant/key IDs, plan, account status, remaining standard
and browser credits, max pages per run, max concurrent runs, and retention days.
It does not return the raw API key.

Hosted beta work endpoints currently include:

```bash
curl http://localhost:8421/v1/hosted/scrape \
  -H "Authorization: Bearer ${SCOUT_HOSTED_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'

curl http://localhost:8421/v1/hosted/crawl \
  -H "Authorization: Bearer ${SCOUT_HOSTED_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","max_pages":5}'

curl http://localhost:8421/v1/hosted/products \
  -H "Authorization: Bearer ${SCOUT_HOSTED_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"start_url":"https://shop.example.com/products","max_products":10}'

curl http://localhost:8421/v1/hosted/run/company \
  -H "Authorization: Bearer ${SCOUT_HOSTED_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"query":"Adobe","mode":"saved","max_records":25}'

curl http://localhost:8421/v1/hosted/runs \
  -H "Authorization: Bearer ${SCOUT_HOSTED_API_KEY}"

curl http://localhost:8421/v1/hosted/runs/${RUN_ID} \
  -H "Authorization: Bearer ${SCOUT_HOSTED_API_KEY}"

curl http://localhost:8421/v1/hosted/runs/${RUN_ID}/records \
  -H "Authorization: Bearer ${SCOUT_HOSTED_API_KEY}"

curl http://localhost:8421/v1/hosted/runs/${RUN_ID}/artifacts \
  -H "Authorization: Bearer ${SCOUT_HOSTED_API_KEY}"

curl http://localhost:8421/v1/hosted/runs/${RUN_ID}/artifacts/records_json/download \
  -H "Authorization: Bearer ${SCOUT_HOSTED_API_KEY}" \
  -o records.json
```

Hosted crawls are metered at one standard credit per returned page. Scout
preflights the requested `max_pages` against the plan limit and remaining
standard credits before starting the crawler, then debits the actual returned
page count after the run completes. This avoids accepting hosted crawls that
the account cannot afford.

Hosted product extraction is metered at one standard credit per returned product
record. Scout preflights the requested `max_products` against the plan limit and
remaining standard credits before starting product discovery, then debits the
actual returned product count after completion. The hosted products endpoint is
currently synchronous; async hosted product jobs and artifact object storage are
future production work.

Hosted high-level runs expose the same `RunRequest`/`RunResponse` shape as
`/run/{use_case}` under `/v1/hosted/run/{use_case}`. Hosted callers cannot
choose arbitrary server output paths: Scout ignores request `output_dir` and
derives a tenant-labeled folder under `SCOUT_WORKDIR`. Hosted runs are metered
at one standard credit per returned record, with preflight based on
`max_records`. This endpoint is synchronous in the private-beta foundation;
async hosted run jobs, artifact object storage, and dashboard browsing remain
production work.

Hosted run retrieval endpoints let a hosted key list its own runs, fetch a run
summary, retrieve records, inspect artifact paths, and download private-beta
artifact files. The run list returns dashboard-safe links and does not expose
server filesystem paths. Ownership is stored in run persistence with non-secret
`tenant_id` and `key_id` fields; retrieval checks the persisted tenant owner
rather than trusting caller-provided paths. Artifact downloads are restricted to
known artifact names under the run output directory. A production deployment
still needs async hosted jobs, object storage, signed artifact URLs, and a
hosted dashboard for browsing run outputs.

## Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Skill Install

```bash
bash install-skill.sh
```

The skill wrapper should remain thin: it teaches the agent how to call Scout,
but the scraper, crawler, product pipeline, tests, and docs live in the
standalone package.

## Runtime Capability Matrix

| Capability | Standalone CLI | Claude/Codex Skill |
|---|---:|---:|
| Crawl4AI fetch/crawl | Yes | Yes |
| WebSearch/WebFetch host provider | No | Yes, when host exposes it |
| In-app browser/session | No | Yes, when host exposes it |
| CDP/profile browser attach | Yes | Optional |
| Saved HTML/DOM replay | Yes | Yes |
| PDF/document parsing | Yes with optional extra | Yes with optional extra |
| ATS adapters | Yes when implemented | Yes when implemented |
| Social provider imports | Yes when implemented | Yes when implemented |

Skill-host capabilities and standalone CLI capabilities are intentionally
different. Scout core should accept normalized provider output from either
environment and produce the same record and artifact contracts.

## High-Level Workflows

Scout's standalone package exposes high-level workflow commands under
`scout run`. These commands are the stable distribution surface for use cases
that need more than one raw fetch.

```bash
scout run company --query Adobe --mode auto --output-dir ./scout-runs/company
scout run careers --query Algolia --mode crawl4ai --output-dir ./scout-runs/careers
scout run products --query "men shirts" --mode auto --output-dir ./scout-runs/products
scout run jobs --profile examples/job-hunter/job-profile.yaml --mode api --output-dir ./scout-runs/jobs
scout run prism --query "Nike company intelligence" --mode auto --output-dir ./scout-runs/prism
scout run investor --query Salesforce --mode saved --output-dir ./scout-runs/investor
```

If `--output-dir` is omitted, the CLI uses `--workdir`, then `SCOUT_WORKDIR`,
then `./scout-runs`. In an interactive terminal, Scout prompts for the working
directory before creating a timestamped run folder:

```bash
scout run company --query Adobe --workdir ./scout-runs
scout products "top products" --site lacoste.com --workdir ./scout-runs
```

Product records are not Algolia-only. After a product run writes
`records.json`, export the same records to local and spreadsheet-friendly
formats:

```bash
scout product-export ./scout-runs/products/records.json \
  --output-dir ./scout-runs/products/exports \
  --format jsonl \
  --format csv \
  --format sqlite \
  --format google_sheets
```

`google_sheets` writes `products.google-sheets.csv` plus a short import guide
for Google Sheets. Direct Google Sheets API push is intentionally not enabled
by default because it requires user OAuth/service-account credentials and a
separate security review.

HTTP, Docker, scheduled jobs, and skill calls do not prompt. Configure
`SCOUT_WORKDIR` or send `output_dir` in the request body.

Job Hunter URL-seeded runs:

```bash
scout run jobs \
  --profile ./private-job-profile.yaml \
  --job-url https://job-boards.greenhouse.io/eve/jobs/4245857009 \
  --output-dir ./scout-runs/jobs
```

Candidate profiles often contain private career, compensation, and resume-derived
data. Keep those files outside the public repository and pass them by path at
runtime. Public examples should use generic/sanitized profiles only.

Every `scout run` workflow writes the same standard artifact set:

```text
manifest.json
records.json
records.jsonl
source_pages.json
blocked_pages.json
validation.json
extraction_report.md
```

This keeps the CLI, HTTP service, Claude/Codex skill, and future scheduled jobs
aligned around one portable output contract.

Citation-grade provenance is split across two artifacts:

- `source_pages.json` is the registry of fetched or supplied source evidence.
  Each page has a deterministic `source_id`, URLs, provider, status, blocked
  state, content hashes, title, and content availability flags.
- `records.json` and `records.jsonl` include `citations[]` entries that point
  to `source_id` and identify the field, claim, snippet, optional selector, and
  confidence.

`validation.json` includes `missing_citations` warnings for records that do not
have structured citations.

The HTTP app exposes the same run surface:

```bash
curl -s -X POST http://localhost:8421/run/prism \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${SCOUT_API_KEY:-dev-key}" \
  -d '{"query":"Nike","mode":"auto","output_dir":"./scout-runs/nike-prism"}'
```

If `output_dir` is omitted, the HTTP app derives a timestamped folder under
`SCOUT_WORKDIR`.

The standalone web UI is available at:

```text
http://localhost:8421/app
```

It provides the Run Console, execution mode tabs, Product Workbench, evidence
inspection, record preview, and Algolia preparation hooks. Algolia ingestion is
preview-only in Production V1; real indexing is a future extension.

Execution modes are stable package API values:

| Mode | Intended distribution path |
|---|---|
| `auto` | Default CLI, HTTP, and skill mode. Uses the provider ladder. |
| `crawl4ai` | Standalone package default for normal pages and JS rendering. |
| `webfetch` | Skill-host supplied page fetch evidence. |
| `websearch` | Skill-host supplied discovery evidence. |
| `browser` | Secondary fallback for blocked or JS-heavy pages in supported hosts. |
| `saved` | Replay saved HTML, DOM snapshots, PDFs, or fixtures. |
| `api` | Provider adapters such as ATS, investor feeds, social APIs, and commerce APIs. |
