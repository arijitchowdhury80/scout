# Distribution

Scout's beta distribution is intentionally narrow:

1. Hosted HTTP API at `https://scout.chowmes.com`.
2. Claude/Codex skill configured to call hosted HTTP.

The Python package, CLI, local HTTP service, and Docker image remain
operator/developer verification surfaces. They are not tester-facing beta
distribution paths.

## Hosted HTTP Beta

Beta testers request finite-credit hosted access from `/beta`. The recommended
public beta flow is `$0` card-backed setup through Stripe Checkout setup mode.
That verifies payment-method collection, signed webhook provisioning, and SMTP
API-key delivery without charging the tester. The email-only
`POST /v1/hosted/beta-key` route remains as a fallback request queue when
Stripe or SMTP setup is blocked. Public browser/API signup never returns raw API
keys.
The delivery email is signed by Arijit Chowdhury, Founder, Chowmes, and
includes the beta credit limit, account/balance link, usage ledger link,
purchase history link, docs, pricing, secret-handling warning, and support
reply instructions. First-time paid package key delivery uses paid package copy
instead of beta-trial copy and includes the purchased package ID plus actual
standard/browser credit counts.

```bash
export SCOUT_HOSTED_BASE_URL="https://scout.chowmes.com"
export SCOUT_HOSTED_API_KEY="paste-your-generated-key"

curl "$SCOUT_HOSTED_BASE_URL/v1/hosted/me" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY"
```

Operator-only key generation may still print a raw key once in a trusted admin
shell. That path is not exposed through the public beta website.

## Claude/Codex Skill

The skill is the agent-facing distribution surface. It should call hosted HTTP
for beta testers and preserve source evidence in responses. Local commands in
skill docs are internal package smoke examples, not public tester onboarding.

```bash
export SCOUT_HOSTED_BASE_URL="https://scout.chowmes.com"
export SCOUT_HOSTED_API_KEY="paste-your-generated-key"
```

## Operator-Only Local Package

```bash
pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-saas-prod-ready"
python -m playwright install chromium
```

`pip install scout-web` is the target command for the first package-registry
release. Do not publish or document it as the primary install path until the
license, PyPI visibility, and release gates are closed.

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
HOSTED_BETA_SIGNUP_RATE_LIMIT_MAX_REQUESTS=3
HOSTED_BETA_SIGNUP_RATE_LIMIT_WINDOW_SECONDS=3600
SCOUT_PUBLIC_HOSTED_ONLY=false
HOST=0.0.0.0
PORT=8421
```

`.env.local` is ignored by git. Store API keys, local working directories, and
developer-only overrides there. For shared deployment defaults, use environment
variables or a deployment-managed `.env`.

`SCOUT_WORKDIR` is the base directory for generated run folders when a caller
does not pass an exact `--output-dir` or JSON `output_dir`.

## Hosted Beta Configuration

Local use does not require Stripe or SMTP. Public hosted beta starts at `/beta`.
When the hosted stack is fully ready, testers should use the `$0` card-backed
beta setup through Stripe Checkout setup mode. Card-backed beta readiness is
true when `ready_for_beta_checkout` is true. Email-only beta readiness is true
when `ready_for_beta_key_delivery` is true, but that path is the fallback
request queue, not the preferred beta onboarding pipeline. If SMTP is not
configured, `/beta` can still record a name/email request through
`/v1/hosted/beta-key`, but no completed API-key delivery has happened. Public
signup never returns raw API keys in the browser.

Hosted beta setup requires:

```text
# Optional kill switch. Omit or set true for normal self-service beta signup.
# HOSTED_BETA_SIGNUP_ENABLED=false
HOSTED_BETA_SIGNUP_RATE_LIMIT_MAX_REQUESTS=3
HOSTED_BETA_SIGNUP_RATE_LIMIT_WINDOW_SECONDS=3600
HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.example.com
HOSTED_KEY_DELIVERY_SMTP_PORT=587
HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL=scout@example.com
HOSTED_KEY_DELIVERY_SMTP_USERNAME=
HOSTED_KEY_DELIVERY_SMTP_PASSWORD=
HOSTED_KEY_DELIVERY_SMTP_USE_TLS=true

```

`/beta` posts the recommended `$0` beta card setup to
`/v1/billing/stripe/checkout-session` with `package_id=beta_trial`. The
email-only fallback posts to `/v1/hosted/beta-key`. Public signup never returns
raw API keys in the browser; Scout emails the one-time key and stores only a
hash. If SMTP is temporarily unavailable, the fallback request is recorded for
queued delivery.

Paid checkout uses Stripe Checkout. `/pricing` contains the paid hosted-credit
checkout form, readiness-gated by `/v1/billing/stripe/status`; it requires
Stripe Checkout settings, signed webhook delivery, and SMTP key delivery before
it is live-ready:

```text
STRIPE_SECRET_KEY=sk_test_...
STRIPE_STANDARD_1000_PRICE_ID=price_...
STRIPE_SUCCESS_URL=https://your-domain.example/pricing?checkout=success
STRIPE_CANCEL_URL=https://your-domain.example/pricing?checkout=cancelled
STRIPE_BETA_SUCCESS_URL=https://your-domain.example/beta?checkout=success
STRIPE_BETA_CANCEL_URL=https://your-domain.example/beta?checkout=cancelled
STRIPE_PORTAL_RETURN_URL=https://your-domain.example/account
STRIPE_WEBHOOK_SECRET=whsec_...
```

The `$0` `beta_trial` package runs through Stripe Checkout setup mode when
`--package-id beta_trial` is used for test-mode smoke validation. That validates
payment-method collection and webhook provisioning without charging the beta
tester.

Paid customers can manage billing through the authenticated account page, which
creates a Stripe Customer Portal session through
`/v1/billing/stripe/customer-portal-session`.

When a paid checkout webhook uses an email that already has a hosted account,
Scout treats the checkout as a credit top-up: it adds the purchased credits to
the existing tenant, records the purchase, and does not send another raw API
key. First-time paid buyers still receive a one-time API key email after
webhook provisioning succeeds.

The `$0` `beta_trial` package is different: repeat beta-trial checkout sessions
for an existing hosted email are recorded but do not grant more free credits.
Only paid packages increase an existing hosted balance.

All key delivery paths use the same SMTP settings:

```text
HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.example.com
HOSTED_KEY_DELIVERY_SMTP_PORT=587
HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL=scout@example.com
HOSTED_KEY_DELIVERY_SMTP_USERNAME=
HOSTED_KEY_DELIVERY_SMTP_PASSWORD=
HOSTED_KEY_DELIVERY_SMTP_USE_TLS=true
```

For the ChowMes VPS deployment, place SMTP and Stripe values in an ignored local
file such as `secrets/scout-production.env`, then install only allowlisted
hosted billing/key-delivery variables with:

```bash
scripts/scout-hosted-admin configure-production-env \
  --secrets-file secrets/scout-production.env \
  --restart
```

The helper writes `/opt/prism/scout/.env`, preserves unrelated deployment
settings, prints variable names only, and does not print secret values. When
`--restart` is passed, it rebuilds and recreates the `scout` container before
checking health so production does not keep serving a stale Docker image.

Hosted API requests also have a private-beta per-key throttle:

```text
HOSTED_RATE_LIMIT_MAX_REQUESTS=60
HOSTED_RATE_LIMIT_WINDOW_SECONDS=60
```

For an internet-facing VPS or hosted SaaS-style deployment, enable the public
hosted guard:

```text
SCOUT_PUBLIC_HOSTED_ONLY=true
```

This keeps the website, `/health`, `/v1/hosted/*`, and Stripe billing routes
available while blocking local/admin routes such as `/scrape`, `/crawl`,
`/products`, `/run/*`, `/docs`, `/openapi.json`, and
`/redoc` even if a caller knows `X-API-Key`. Consuming apps such as PRISM
should use hosted Bearer keys, not the local `X-API-Key`, when Scout is exposed
on the public web. See `docs/product/hosted-saas-api-guide.md`.

`/v1/hosted/*` requests that exceed the configured window return `429` with a
`Retry-After` header and do not spend hosted credits. The current limiter is
in-memory and process-local. It is enough for a single-node private beta, but a
multi-instance hosted launch still needs a shared limiter such as Redis or an
API-gateway/WAF policy.

Expensive hosted acquisition endpoints use a bounded async queue when worker
capacity is saturated. Configure it with:

```text
HOSTED_MAX_ACTIVE_REQUESTS=8
HOSTED_JOB_QUEUE_MAX_SIZE=250
HOSTED_JOB_QUEUE_WORKERS=2
HOSTED_ASYNC_FIRST=false
CAPACITY_RETRY_AFTER_SECONDS=5
```

When all synchronous workers are busy, `/v1/hosted/scrape`, `/crawl`,
`/products`, and `/run/{use_case}` return `202 Accepted` with a `job_id` and
`job_url`. Poll `/v1/hosted/jobs/{job_id}` with the same Bearer key for status
and result. Credits are charged only when the queued job actually executes.
If the queue is also full, Scout returns `429` with `Retry-After`.

For public beta bursts on a small VPS, set `HOSTED_ASYNC_FIRST=true`. In that
mode expensive hosted endpoints return `202 Accepted` immediately after auth,
URL safety, plan-limit, and credit-preflight checks. Worker processes then drain
the queue behind the HTTP request path.

Scout exposes a non-secret readiness check for the website:

```bash
curl http://localhost:8421/v1/billing/stripe/status
```

It returns booleans for checkout, webhook, key delivery, and end-to-end paid key
delivery readiness plus the public self-service path and exact non-secret
environment variable names that still need configuration. Production
self-service should report
`public_self_service_path: "email_beta_registration"`
for beta access. It never returns Stripe, SMTP, or Scout API secret values.

For a real Stripe test-mode smoke, start Scout with the Stripe and SMTP
settings above, then run:

```bash
scripts/scout-hosted-admin stripe-smoke \
  --base-url http://127.0.0.1:8421 \
  --email scout-beta-test@example.com \
  --name "Scout Beta Tester" \
  --package-id standard_1000 \
  --create-checkout
```

The helper verifies non-secret paid-readiness flags, creates a Checkout
Session, and prints the Checkout URL. Complete the test payment in Stripe Checkout,
deliver the webhook to `/v1/billing/stripe/webhook`, then confirm the delivered
hosted key works against `/v1/hosted/me`.

For the $0 beta setup path, run:

```bash
scripts/scout-hosted-admin stripe-smoke \
  --base-url http://127.0.0.1:8421 \
  --email scout-beta-test@example.com \
  --name "Scout Beta Tester" \
  --package-id beta_trial \
  --create-checkout
```

To verify the beta email-registration path instead:

```bash
curl -X POST http://127.0.0.1:8421/v1/hosted/beta-key \
  -H "Content-Type: application/json" \
  -d '{"name":"Scout Beta Tester","email":"scout-beta-test@example.com"}'
```

After a hosted beta user receives a `scout_live_...` API key, they can inspect
their plan limits and remaining credits:

```bash
curl http://localhost:8421/v1/hosted/me \
  -H "Authorization: Bearer ${SCOUT_HOSTED_API_KEY}"
```

The response includes tenant/key IDs, plan, account status, remaining standard
and browser credits, max pages per run, max concurrent runs, and retention days.
It does not return the raw API key.

Operators can print copyable cURL examples for consumers:

```bash
scout hosted-curl --base-url https://your-domain.example --endpoint me
scout hosted-curl --base-url https://your-domain.example --endpoint scrape --url https://example.com
scout hosted-curl --base-url https://your-domain.example --endpoint products --url https://shop.example.com/products
scout hosted-curl --base-url https://your-domain.example --endpoint run --use-case company --url https://www.adobe.com
```

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

## Internal Docker Infrastructure

Docker remains deployment/operator infrastructure for the VPS and CI smoke
tests. It is not a tester distribution path and Scout does not publish a public
Docker image for this beta.

```bash
docker compose -f docker/docker-compose.yml up --build
curl http://localhost:8421/health
```

The container listens on `8421`, stores run artifacts under `/data/runs`, and
uses `DB_PATH=/data/scout.db` for run persistence. The compose file mounts a
named `scout-data` volume and passes `SCOUT_API_KEY`, `LLM_API_KEY`,
`SCOUT_WORKDIR`, and `DB_PATH` into the service.

Latest local Docker verification:

```bash
docker build -f docker/Dockerfile -t scout:launch-smoke .
docker run --rm -p 18421:8421 \
  -e SCOUT_API_KEY=dev-key \
  -e SCOUT_WORKDIR=/data/runs \
  -e DB_PATH=/data/scout.db \
  scout:launch-smoke
```

`/health`, `/`, and `/styles.css` were smoke-tested from the built image. The
image includes Playwright Chromium and the bundled launch website assets.

## Skill Install For Operators

```bash
bash install-skill.sh
```

The skill wrapper should remain thin: it teaches the agent how to call hosted
Scout, but the scraper, crawler, product pipeline, tests, and docs live in the
Scout repository.

## Runtime Capability Matrix

| Capability | Hosted HTTP | Claude/Codex Skill | Operator Local |
|---|---:|---:|
| Crawl4AI fetch/crawl | Yes | Yes, through hosted HTTP | Yes |
| WebSearch/WebFetch host provider | No | Yes, when host exposes it | No |
| In-app browser/session | No | Host-dependent | Internal only |
| CDP/profile browser attach | No | No for hosted beta | Internal only |
| Saved HTML/DOM replay | Yes | Yes, through hosted HTTP | Yes |
| PDF/document parsing | Yes with optional extra | Yes with optional extra | Yes with optional extra |
| ATS adapters | Yes when implemented | Yes when implemented | Yes when implemented |
| Social provider imports | Yes when implemented | Yes when implemented | Yes when implemented |

Skill-host capabilities and standalone CLI capabilities are intentionally
different. Scout core should accept normalized provider output from either
environment and produce the same record and artifact contracts.

## High-Level Workflows

Scout's operator package exposes high-level workflow commands under
`scout run`. These commands remain useful for local verification and internal
debugging, but beta testers should use hosted HTTP or the skill.

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

Scout is shipped to beta testers as hosted HTTP plus Claude/Codex skill usage.
CLI, local HTTP API, and Docker-from-source remain operator verification and VPS
infrastructure surfaces. The previous experimental `/app` UI has been removed
from the supported product surface; use the launch website, quickstart, API
docs, hosted examples, and artifact outputs instead.

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
