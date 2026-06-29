# Hosted SaaS API Verification

Date: 2026-06-29
Status: local hosted-only smoke passed; live VPS endpoint still needs domain/SSH verification

## Scope

This verification checked the SaaS-style hosted API behavior in a temporary
single-node deployment configuration:

- fresh hosted account database,
- fresh `scout_live_...` API key,
- `SCOUT_PUBLIC_HOSTED_ONLY=true`,
- isolated HTTP port,
- hosted Bearer-auth calls through cURL.

It verifies the software behavior required before exposing Scout to consuming
apps such as PRISM. It does not prove the current VPS firewall, TLS certificate,
domain, or environment variables because no current VPS host alias, SSH config,
or canonical hosted base URL was available in the repo/workstation context.

## Commands

Provision a fresh hosted key:

```bash
python3 -m scout.cli hosted-provision \
  --email prism-smoke@example.com \
  --db "$TMPDIR_HOSTED/hosted_accounts.sqlite" \
  --key-name "PRISM smoke"
```

Start Scout in hosted-only mode:

```bash
SCOUT_WORKDIR="$TMPDIR_HOSTED/runs" \
HOSTED_ACCOUNT_DB_PATH="$TMPDIR_HOSTED/hosted_accounts.sqlite" \
DB_PATH="$TMPDIR_HOSTED/scout.db" \
SCOUT_API_KEY=local-admin-smoke \
SCOUT_PUBLIC_HOSTED_ONLY=true \
python3 -m uvicorn scout.api.main:app --host 127.0.0.1 --port 18425
```

Smoke checks:

```bash
curl http://127.0.0.1:18425/health
curl -i http://127.0.0.1:18425/v1/hosted/me
curl http://127.0.0.1:18425/v1/hosted/me \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY"
curl -i -X POST http://127.0.0.1:18425/scrape \
  -H "X-API-Key: local-admin-smoke" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
curl -i http://127.0.0.1:18425/docs
curl -X POST http://127.0.0.1:18425/v1/hosted/scrape \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"],"timeout_ms":30000}'
```

## Results

| Check | Result |
|---|---|
| `/health` without auth | `200` |
| `/v1/hosted/me` without Bearer token | `401 Missing Bearer token` |
| `/v1/hosted/me` with fresh hosted key | `200` |
| `/scrape` with local admin `X-API-Key` while hosted-only is true | `403 Local Scout API is disabled in hosted-only mode.` |
| `/docs` while hosted-only is true | `403 Local Scout API is disabled in hosted-only mode.` |
| `/v1/hosted/scrape` with hosted key | `200`, provider `crawl4ai`, quality score `1.0`, one standard credit charged |
| Raw hosted key leaked in response bodies | No |

## Security Posture Verified

- Hosted consumers use `Authorization: Bearer scout_live_...`.
- Missing Bearer token fails before work starts.
- Hosted account responses expose tenant/key IDs, plan, limits, and balances,
  but not raw API keys.
- Public hosted-only mode blocks local/admin API routes even if the caller knows
  `X-API-Key`.
- Swagger/OpenAPI docs are not public in hosted-only mode.
- Hosted scrape executes and debits one standard credit.

## Remaining VPS Verification

Known workstation evidence:

- `~/.ssh/known_hosts` includes `72.61.72.147`.
- Non-interactive SSH with the available `~/.ssh/chowmes_ed25519` key failed
  for both `root@72.61.72.147` and `arijitchowdhury@72.61.72.147` with
  `Permission denied (publickey)`.
- `http://72.61.72.147/health` returned `308` from Caddy redirecting to HTTPS.
- `http://72.61.72.147:8421/health` did not connect.
- `https://72.61.72.147/health` did not complete on the raw IP within the
  smoke timeout.

To verify the actual VPS, use the real hosted domain or working SSH credential
and run the same smoke against the live hosted base URL after confirming:

- DNS and TLS are correct;
- `SCOUT_PUBLIC_HOSTED_ONLY=true`;
- `SCOUT_API_KEY` is not `dev-key`;
- `HOSTED_ACCOUNT_DB_PATH` points to durable server storage;
- only intended ports are open through the firewall;
- reverse proxy forwards `/v1/hosted/*` and `/v1/billing/stripe/*`;
- local/admin routes remain blocked from the public internet.

## Verdict

The code path now behaves like a private-beta hosted SaaS API. The live VPS
deployment still needs an environment-level smoke using its actual domain or
IP before PRISM or other apps should treat it as a reliable hosted dependency.
