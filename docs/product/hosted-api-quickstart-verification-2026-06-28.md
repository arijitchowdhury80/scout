# Hosted API Quickstart Verification

Date: 2026-06-28

Status: passed with a freshly generated hosted beta key.

## Scope

This verification tested the hosted API quickstart flow using current Scout code
and a temporary hosted-account SQLite database. It did not use a pre-existing
API key.

The smoke covered:

- operator key provisioning,
- hosted Bearer-key authentication,
- hosted account/credit summary,
- hosted scrape execution,
- credit debit after a successful request,
- no raw API key committed to docs or artifacts.

## Commands

Provision a fresh hosted beta key:

```bash
python3 -m scout.cli hosted-provision \
  --email scout-hosted-quickstart@example.com \
  --db "$TMPDIR_HOSTED/hosted_accounts.sqlite" \
  --key-name "Hosted quickstart smoke"
```

Start the hosted API against the same temporary database:

```bash
SCOUT_WORKDIR="$TMPDIR_HOSTED/runs" \
HOSTED_ACCOUNT_DB_PATH="$TMPDIR_HOSTED/hosted_accounts.sqlite" \
DB_PATH="$TMPDIR_HOSTED/scout.db" \
SCOUT_API_KEY=local-dev-key \
python3 -m uvicorn scout.api.main:app --host 127.0.0.1 --port 18424
```

Call the hosted API with the newly generated key:

```bash
curl -fsS http://127.0.0.1:18424/v1/hosted/me \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY"

curl -fsS -X POST http://127.0.0.1:18424/v1/hosted/scrape \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"],"timeout_ms":30000}'
```

## Evidence

Fresh key provisioning produced:

```text
success: true
tenant_id: tenant_d307e68b00ca4a01b1d41c222d84f7ed
key_id: key_2bb7177f9b454e4ca5a36421cead5bf2
plan: hosted_beta_pass
scopes: ["runs:create"]
standard_credits_remaining: 2000
browser_credits_remaining: 100
raw_api_key_masked: scout_live_v8S-d...feG378
```

Hosted API smoke result:

```text
me_before_status: active
plan: hosted_beta_pass
before_standard: 2000
before_browser: 100
scrape_success: true
credits_charged: 1
credit_type: standard
provider: crawl4ai
final_url: https://example.com
quality_score: 1.0
markdown_len: 166
after_standard: 1999
after_browser: 100
```

Server log confirmation:

```text
GET /health HTTP/1.1 200 OK
GET /v1/hosted/me HTTP/1.1 200 OK
POST /v1/hosted/scrape HTTP/1.1 200 OK
GET /v1/hosted/me HTTP/1.1 200 OK
```

## Result

The hosted API quickstart path works with a newly generated key. The key can:

- authenticate to `/v1/hosted/me`,
- run `/v1/hosted/scrape`,
- receive provider/content-quality metadata,
- debit one standard credit for the scrape,
- preserve browser credits.

## Notes

- The raw key was generated only for this smoke and was not written to tracked
  docs.
- The global `scout` command on this workstation was stale and broken outside
  the repository checkout, so verification used `python3 -m scout.cli` from the
  current checkout. Clean install of the branch-qualified package was already
  verified separately in `docs/product/local-install-verification-2026-06-28.md`.
- Public hosted launch still requires Stripe test-mode smoke, live key delivery
  provider smoke, support channel confirmation, and final legal/pricing
  decisions.

