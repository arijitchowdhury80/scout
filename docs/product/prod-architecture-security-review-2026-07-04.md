# Scout Production Deployment — Architecture & Security Review
**Date:** 2026-07-04 · Reviewer: Claude (Opus 4.8) · Method: live read-only SSH audit of VPS
72.61.72.147 + external probes of https://scout.chowmes.com. No secret values were read or printed.

## Verdict in one line
The architecture (Docker container + Caddy + single VPS) is **correct and appropriate for a
250-user beta** — do not re-architect. The problems are **isolation and durability hardening**, not
the fundamental design. Two are effectively launch blockers: **no backup of Scout's data** and **no
container resource limits on a box shared with PRISM + Hermes**.

## First, the framing correction (your question)
Running Scout in Docker on your VPS is a **deployment** choice. Shipping a Docker image for testers
to self-host is a **distribution** choice. They are independent. Keep Docker as the internal runtime;
the two *tester-facing* distributions stay **hosted HTTP API + self-host skill**. Docker/CLI/pip are
internal tooling, not advertised downloads. So "prod uses Docker" does **not** obligate us to support
Docker as a product.

## Is Docker-on-a-single-VPS the best architecture?
For a beta: **yes.** Container = reproducible deploys, isolation, one-command rollback; Caddy =
automatic TLS. That's the right cost/complexity point — a managed cluster (k8s, RDS, etc.) would be
over-engineering at 250 users. The one genuine architectural weakness is **co-tenancy**: Scout,
PRISM, and Hermes share a single 2 vCPU / 8 GB box (Scout even lives at `/opt/prism/scout`) with **no
resource isolation between them.** A Scout incident (OOM, CPU spin, disk fill, fork bomb from 250
concurrent Chromium) can take down PRISM — your actual product — and Hermes. For a beta that's a
calculated risk; mitigate with container limits now, and plan to move Scout to its own ~$14/mo VPS if
the beta validates.

## What's GOOD (verified)
- **Network:** ufw default-deny; only 80/443 public; **SSH restricted to your Mac's IP**; fail2ban +
  unattended-upgrades active. Strong.
- **Exposure:** the container publishes only to `127.0.0.1:8421`; Caddy is the sole public edge with
  Let's Encrypt TLS. The app is never directly internet-facing.
- **Hosted-only enforcement works in production** (external probes): `/scrape`→403, `/extract`→403
  (LLM route sealed), `/api/docs`→403, `/openapi.json`→403, `/v1/hosted/me` no-key→401, `/beta`→200.
- **Secrets:** injected via `env_file` `/opt/prism/scout/.env`, perms **600 owner-only**, not baked
  into the image. LLM_API_KEY empty (confirmed). API keys stored as hashes.
- **Persistence:** data on a named Docker volume (`docker_scout-data` → `/data`); survives restarts.
- **Resilience:** `restart: unless-stopped`; healthcheck healthy, 0 restarts.

## ✅ FIXES APPLIED LIVE (2026-07-04, verified; PRISM stayed healthy after each)
- **Scout data now backed up** — `backup.sh` patched to snapshot `hosted_accounts.sqlite` + `scout.db`
  (sqlite hot-backup API) into the off-host `prism-data` git repo nightly; ran once manually →
  `commit OK → push OK`. Immediate pre-change snapshot also taken (integrity: ok, 4264 tenants).
- **Container resource limits** — `docker update --memory 5g --memory-swap 6g --cpus 1.5
  --pids-limit 512 scout`, also persisted to `docker-compose.yml` (validated). Verified live during a
  250-concurrent hammer: **PRISM stayed 200 throughout** — isolation works.
- **4 GB swap added** + `/etc/fstab` entry.
- **HTTP security headers** on scout.chowmes.com via Caddy — HSTS, X-Frame-Options: DENY,
  X-Content-Type-Options: nosniff, Referrer-Policy; `Server` header stripped. Validated + graceful
  reload; all sites still 200.
- **Boot resilience confirmed** — Docker enabled at boot; scout + caddy both `restart: unless-stopped`
  (finding #6 was a false alarm — Caddy is a container with a restart policy, not a bare process).

### ⚠️ New findings surfaced during hardening
- **PRISM postgres has `restart: no`** — your product's DB will NOT auto-recover after a reboot/crash.
  Outside Scout's scope but worth fixing.
- **Prod account DB already holds 4,264 tenants pre-launch** (only 442 ledger rows → mostly unused).
  Beta signup is public + only IP-rate-limited, so this is likely bot/spam or prior test signups.
  Recommend cleaning test/spam rows and adding signup abuse protection (email verify / captcha) before
  the real beta.

## What needs FIXING (prioritized)
| # | Severity | Finding | Fix |
|---|---|---|---|
| 1 | **HIGH** | **Scout data is NOT backed up.** `/opt/prism-backup/backup.sh` has no Scout reference. If the volume is lost, every beta tester account + API-key hash + usage ledger is gone. | Add `docker_scout-data` (or the sqlite files) to the daily backup; verify a restore. |
| 2 | **HIGH** | **No container resource limits** (`Memory=0 NanoCpus=0`, no pids limit). A Scout spike can OOM/starve PRISM + Hermes on the shared box. | Set `mem_limit: 5g`, `cpus: 1.5`, `pids_limit: 512` in compose. |
| 3 | MED | **No swap** on the 8 GB box → OOM = hard process kill, not graceful. | Add 4 GB swapfile. |
| 4 | MED | **Container runs as root**, no `cap_drop`, writable rootfs, no `no-new-privileges`. Weak container-escape posture. | Dockerfile `USER scout`; compose `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`, `read_only: true` + tmpfs. |
| 5 | MED | **No HTTP security headers** — no HSTS, X-Frame-Options, X-Content-Type-Options, CSP; `Server: uvicorn` leaks the backend. | Add a headers block to the Caddy scout site. |
| 6 | MED | **Caddy runs as a bare process, not a systemd service** (unit inactive). Reboot resilience unverified — the site may not come back after a reboot. | Confirm/enable a `caddy.service` (or run Caddy in a restart-policy container). |
| 7 | LOW (beta) | **SQLite** for multi-tenant billing/accounts. Safe now (atomic debit + WAL + busy_timeout), but single-writer; a bottleneck and a single-file risk at scale. | Fine for beta. Plan Postgres for GA. |
| 8 | LOW-MED | Disk **79% used (21 GB free)**; `runs/` already has 513 artifact dirs accumulating. | Cron-prune artifacts past retention; alert at 90%. |
| 9 | LOW | Stale unused `nginx.conf` in the deploy dir (Caddy is the real proxy) — confusing artifact. | Remove. |

## Recommended pre-launch action set (fast, high-value)
Do #1 (backup), #2 (resource limits), #3 (swap), #5 (security headers) before launch — all low-risk,
all protect either your data or your other products. #4 (non-root/cap_drop) and #6 (Caddy service)
next. #7–#9 are follow-ups. None require re-architecting.

> Caveat: every fix above changes the **shared prod box that also runs PRISM + Hermes**, so each
> should be applied deliberately (backup first, one change at a time, verify PRISM stays up).

## Load & capacity evidence (local + prod, 2026-07-04)
- **Stability: PASS.** Across every run — local 50/250-user (260 distinct keys) and prod
  250-concurrent — the server returned **zero HTTP 500s and never crashed.** Overload is handled by
  clean backpressure: 429 (rate limit), 503/202 (capacity/async-queue), then client timeouts. This is
  a correctly-behaving backpressure system, not a fragile one.
- **Throughput: the bottleneck is by design.** A single uvicorn worker + an 8-active-request cap means
  heavy real-site crawls (which take 10–190s each externally) queue under concurrency. p95 for even a
  trivial endpoint hit ~8.6s at 250 concurrent. Local numbers were further inflated by running three
  competing load tests on one laptop + crawling real sites from one IP.
- **Isolation: PASS (post-hardening).** During the prod 250-concurrent hammer, **PRISM stayed 200
  before and after** — the new CPU/memory caps prevent Scout from starving neighbors.

### Scaling path (NOT a quick config change — flagged to avoid a metering-breaking edit)
Adding uvicorn `--workers N` would **break** the current backpressure: the admission controller
(8-active) and the rate limiter hold **in-process** state, so N workers = N× the intended global
limits. The credit debit is safe across workers (atomic SQLite), but the concurrency controls are not.
So: single-worker is *correct* for today's design. To raise concurrent throughput, first move
admission + rate-limit state to a shared store (SQLite table / Redis), then add workers — or scale the
VPS vertically. For a 250-user beta whose heavy work runs through the async job queue, the current
config is acceptable; this is a documented GA scaling task.

## Non-root container (#4) — ready-to-apply patch, NOT yet applied (needs a test build)
Deferred deliberately: switching `USER` naively breaks two things — Playwright installs Chromium under
`/root/.cache/ms-playwright`, and the existing `/data` volume is root-owned. Correct change for the
next deploy:
1. Set `ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright` and `playwright install chromium` into that path,
   then `chown -R scout:scout /ms-playwright /app`.
2. `useradd -u 1000 scout`; add an entrypoint that (as root) `chown scout:scout /data` then `exec gosu
   scout uvicorn ...` — because the mounted volume's ownership can't be fixed at build time.
3. Compose: `cap_drop: [ALL]`, `security_opt: ["no-new-privileges:true]`.
Requires one test build + a staging boot against a copy of the volume before deploying to prod.
