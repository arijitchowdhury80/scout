# Distribution

Scout is distributed as a standalone Python package and can also be installed
as a Claude/Codex skill integration.

## Standalone Package

```bash
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
