# Execution Modes

Scout separates acquisition from extraction. Acquisition gets evidence from the
web or saved sources. Extraction turns that evidence into typed records and
durable artifacts.

## Modes

| Mode | Default? | Works standalone? | Works in skill? | Use when |
|---|---:|---:|---:|---|
| `auto` | Yes | Yes | Yes | You want Scout to choose the provider ladder. |
| `crawl4ai` | Standalone default | Yes | Yes | Normal public pages, JS rendering, crawling, screenshots. |
| `webfetch` | No | No | Yes | The host agent can fetch a page that direct crawling cannot. |
| `websearch` | No | No | Yes | URLs are unknown and the host has search available. |
| `browser` | No | Host-dependent | Yes | Blocked pages, JS shells, interactive content, or visual verification. |
| `saved` | No | Yes | Yes | Deterministic replay from saved HTML, DOM, markdown, PDFs, or fixtures. |
| `api` | No | Yes | Yes | ATS, investor, commerce, social, or other provider APIs are available. |

## Auto Ladder

`auto` attempts providers in this order:

1. `crawl4ai`
2. `api`
3. `saved`
4. `webfetch`
5. `websearch`
6. `browser`

Browser is a fallback, not the default. It should be used when Scout sees
blocked pages, empty JS shells, insufficient markdown, or when visual browser
verification is explicitly requested.

## Examples

```bash
scout run company --query Adobe --mode auto --output-dir ./scout-runs/adobe-company
scout run careers --query Intuit --mode crawl4ai --output-dir ./scout-runs/intuit-careers
scout run jobs --profile ./private-job-profile.yaml --mode api --output-dir ./scout-runs/jobs
scout run investor --query Salesforce --mode saved --output-dir ./scout-runs/salesforce-investor
scout run products --query "top skincare products" --mode browser --output-dir ./scout-runs/estee-products
```

HTTP equivalent:

```bash
curl -s -X POST http://localhost:8421/run/company \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${SCOUT_API_KEY:-dev-key}" \
  -d '{"query":"Adobe","mode":"auto","output_dir":"./scout-runs/adobe-company"}'
```

## Output

All modes must produce normalized source evidence. All high-level workflows
then write the standard artifact set:

```text
manifest.json
records.json
records.jsonl
source_pages.json
blocked_pages.json
validation.json
extraction_report.md
```

The same records should be created from browser evidence, saved fixtures,
host-provided fetches, or Crawl4AI evidence whenever the visible page content is
equivalent.

## Citations

All provider modes normalize into `FetchResult` source evidence. Each source
gets a deterministic `source_id`, and each extracted record should include
`citations[]` pointing back to those source IDs. This keeps browser, WebFetch,
Crawl4AI, API, and saved evidence comparable in downstream PRISM and Algolia
workflows.
