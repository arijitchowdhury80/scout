# Docker Install Verification

Date: 2026-06-28

Status: passed after clearing a stale local port conflict.

## Scope

This verification tested the Docker install path exactly from the documented
compose workflow in `docs/distribution.md`:

```bash
docker compose -p scout-docs-smoke -f docker/docker-compose.yml up --build -d
```

The smoke covered the container build, HTTP service startup, public website
paths, API docs, authenticated scrape, and writable Docker data volume.

## Environment

```text
Docker version 29.1.3, build f52814d
Docker Compose version v5.0.1
```

## Results

| Check | Command | Result |
|---|---|---|
| Container build and start | `docker compose -p scout-docs-smoke -f docker/docker-compose.yml up --build -d` | Passed. Image built, Playwright Chromium installed, container started. |
| Container status | `docker compose -p scout-docs-smoke -f docker/docker-compose.yml ps` | Passed. `scout-docs-smoke-scout-1` was `Up` and `healthy`. |
| Health endpoint | `curl -fsS http://127.0.0.1:8421/health` | Passed. Returned `{"status":"ok","crawl4ai_version":"0.7.7","scout_version":"0.1.0"}`. |
| Launch website | `curl -fsS http://127.0.0.1:8421/ \| rg "Turn messy web pages\|Run ledger"` | Passed. Homepage returned launch copy and run-ledger positioning. |
| Static CSS | `curl -fsS http://127.0.0.1:8421/styles.css \| rg "beta-form\|site-shell\|hero"` | Passed. Public stylesheet served without auth. |
| Quickstart page | `curl -fsS http://127.0.0.1:8421/quickstart \| rg "Scout Quickstart\|codex/scout-platform-foundation"` | Passed. Quickstart served the branch-qualified beta install command. |
| API docs | `curl -fsS http://127.0.0.1:8421/docs \| rg "Swagger UI\|Scout"` | Passed. Swagger UI loaded. |
| OpenAPI | `curl -fsS http://127.0.0.1:8421/openapi.json` | Passed. Title was `Scout`; `/scrape` and `/health` were present. |
| Authenticated scrape | `POST /scrape` with `X-API-Key: dev-key` against `https://example.com` | Passed. Response used provider `crawl4ai`, final URL `https://example.com`, quality score `1.0`, and markdown length `166`. |
| Data volume | `docker compose ... exec scout sh -lc 'test -d /data/runs && test -w /data && test -f /data/scout.db && echo data-ok'` | Passed. Returned `data-ok`. |

## Port Conflict Finding

The first curl smoke hit a stale local Python/uvicorn Scout server that was also
listening on port `8421`, producing old app HTML and `403` responses for
`/styles.css` and `/quickstart`.

Diagnosis:

```text
Python ... -m uvicorn scout.api.main:app --host 0.0.0.0 --port 8421
com.docke ... TCP *:8421 (LISTEN)
```

After stopping the stale local process, Docker logs showed the expected
container requests:

```text
"GET / HTTP/1.1" 200 OK
"GET /styles.css HTTP/1.1" 200 OK
"GET /quickstart HTTP/1.1" 200 OK
```

The Docker path itself passed. The practical operator note is that port `8421`
must be free, or the user should change the host port mapping before running
the compose smoke.

## Cleanup

The verification container and named volume should be removed after smoke
testing:

```bash
docker compose -p scout-docs-smoke -f docker/docker-compose.yml down -v
```

