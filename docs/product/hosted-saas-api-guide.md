# Scout Hosted SaaS API Guide

Date: 2026-06-29
Status: private-beta hosted API guide

## Purpose

This is the operating guide for PRISM and other consuming apps that need to
call Scout as a hosted HTTP API instead of running Scout locally.

The hosted API surface is:

```text
/v1/hosted/*
```

Current private-beta VPS base URL:

```text
https://judge.contentengagement.info/scout
```

The VPS keeps Scout bound to `127.0.0.1:8421`; Caddy exposes only the
`/scout/*` path publicly and strips that prefix before proxying to Scout.

Hosted API calls use:

```http
Authorization: Bearer scout_live_...
```

Do not give consuming apps the local `X-API-Key` unless they are running on the
same trusted private machine or network. Public consumers should use hosted
Bearer keys only.

## VPS/Public Deployment Guard

Set this on an internet-facing hosted Scout instance:

```bash
SCOUT_PUBLIC_HOSTED_ONLY=true
```

When enabled, Scout blocks local/admin routes even if a caller knows
`X-API-Key`:

- `/scrape`
- `/crawl`
- `/products`
- `/run/*`
- `/app`
- `/api/config`
- `/docs`
- `/openapi.json`
- `/redoc`

The following remain available:

- website/legal/status pages,
- `/health`,
- `/v1/hosted/*`,
- `/v1/billing/stripe/*`.

This is the expected posture for a hosted SaaS-style deployment.

Current VPS verification from 2026-06-29:

- `GET https://judge.contentengagement.info/scout/health` -> `200`.
- `GET /v1/hosted/me` without Bearer token -> `401 Missing Bearer token`.
- `POST /v1/hosted/scrape` without Bearer token -> `401 Missing Bearer token`.
- `GET /api/config` -> `403 Local Scout API is disabled in hosted-only mode`.
- `POST /scrape` with the real local `X-API-Key` -> `403 Local Scout API is disabled in hosted-only mode`.
- Direct public `http://72.61.72.147:8421/health` is unreachable; Scout listens only on `127.0.0.1:8421`.
- Hosted key smoke passed: `scout hosted-provision` created a beta key, `/v1/hosted/me` returned plan/balance/limits, and `/v1/hosted/scrape` returned `success: true` with `hosted.credits_charged: 1` and rendered scrape evidence under `scrape`.

## Operator: Provision A Hosted API Key

Use the same hosted account database used by the running service:

```bash
scout hosted-provision \
  --email tester@example.com \
  --db /data/hosted_accounts.sqlite \
  --key-name "PRISM private beta key"
```

The command returns `raw_api_key` once. Store it immediately in the consuming
app's secret manager or `.env.local`.

Scout stores only a hash of the raw key.

## Consumer: Configure PRISM Or Another App

```bash
SCOUT_HOSTED_BASE_URL=https://judge.contentengagement.info/scout
SCOUT_HOSTED_API_KEY=scout_live_paste_the_delivered_key
```

The consuming app should never commit or log the raw key.

## Generate Copyable cURL Commands

Operators and developers can generate copyable hosted cURL examples:

```bash
scout hosted-curl \
  --base-url https://your-scout-domain.example \
  --endpoint me
```

```bash
scout hosted-curl \
  --base-url https://your-scout-domain.example \
  --endpoint scrape \
  --url https://example.com
```

```bash
scout hosted-curl \
  --base-url https://your-scout-domain.example \
  --endpoint products \
  --url https://www.nike.com/w/mens-shirts-6ymx6znik1
```

```bash
scout hosted-curl \
  --base-url https://your-scout-domain.example \
  --endpoint run \
  --use-case company \
  --url https://www.adobe.com
```

## Direct cURL Examples

Check key/account status:

```bash
curl "$SCOUT_HOSTED_BASE_URL/v1/hosted/me" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY"
```

Scrape one page:

```bash
curl -X POST "$SCOUT_HOSTED_BASE_URL/v1/hosted/scrape" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"],"timeout_ms":30000}'
```

Crawl a small site section:

```bash
curl -X POST "$SCOUT_HOSTED_BASE_URL/v1/hosted/crawl" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","max_pages":5}'
```

Extract product records:

```bash
curl -X POST "$SCOUT_HOSTED_BASE_URL/v1/hosted/products" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"start_url":"https://shop.example.com/products","max_products":10}'
```

Run company intelligence:

```bash
curl -X POST "$SCOUT_HOSTED_BASE_URL/v1/hosted/run/company" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"Adobe","mode":"auto","max_records":25}'
```

List runs for the hosted tenant:

```bash
curl "$SCOUT_HOSTED_BASE_URL/v1/hosted/runs" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY"
```

Fetch records for a run:

```bash
curl "$SCOUT_HOSTED_BASE_URL/v1/hosted/runs/$RUN_ID/records" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY"
```

## Hosted Deployment Smoke Test

After deployment, verify:

```bash
curl "$SCOUT_HOSTED_BASE_URL/health"
```

```bash
curl -i "$SCOUT_HOSTED_BASE_URL/v1/hosted/me"
# Expect: 401 Missing Bearer token
```

```bash
curl "$SCOUT_HOSTED_BASE_URL/v1/hosted/me" \
  -H "Authorization: Bearer $SCOUT_HOSTED_API_KEY"
# Expect: 200 with plan, balance, and limits; no raw API key
```

```bash
curl -i -X POST "$SCOUT_HOSTED_BASE_URL/scrape" \
  -H "X-API-Key: $SCOUT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
# Expect when SCOUT_PUBLIC_HOSTED_ONLY=true:
# 403 Local Scout API is disabled in hosted-only mode.
```

```bash
curl -i "$SCOUT_HOSTED_BASE_URL/docs"
# Expect when SCOUT_PUBLIC_HOSTED_ONLY=true:
# 403 Local Scout API is disabled in hosted-only mode.
```

## Current Security Boundary

Implemented for private beta:

- generated `scout_live_...` hosted keys;
- raw keys returned once and stored hashed;
- Bearer authentication on `/v1/hosted/*`;
- tenant/account status checks;
- per-key scopes;
- finite standard/browser credits;
- per-key process-local rate limit;
- URL safety checks for hosted routes;
- hosted run tenant ownership checks;
- hosted artifact path confinement;
- hosted-only public deployment guard.

Still required before broad public SaaS launch:

- confirmed TLS/domain/firewall configuration on the VPS;
- distributed rate limiting for multi-instance production;
- Postgres or equivalent production account database;
- async worker queue for long hosted jobs;
- object storage with tenant-scoped keys and retention deletion;
- real Stripe test-mode smoke and key-delivery smoke;
- monitoring, alerting, and abuse controls.
