# Deploy branch to prod + live re-verify — runbook (ready to execute on founder's go)

Branch: `fix/launch-readiness-fx1-fx7` (PR #2). All 5 fix commits, 928 unit tests green. **Gated: needs founder "go" (prod deploy).**

## A. Deploy the fix branch to prod
On the VPS (`chowmes-vps`), the repo copy at `/opt/prism/scout/docker` + `scout-deploy.sh` build/run the container.
1. Pull the branch on the box (or copy the built image) → checkout `fix/launch-readiness-fx1-fx7`.
2. `docker compose build scout && docker compose up -d scout` (or run `scout-deploy.sh`).
3. **Non-root note (FX-13a):** new Dockerfile runs as uid/gid 10001. The `/data` volume on the host may be owned by root from the old container — must `chown -R 10001:10001` the volume/bind mount or the container can't write DBs. Check first; fix if needed.
4. **nginx (FX-7):** repo `nginx.conf` dropped the `/app` blocks; prod nginx still has them — reload prod nginx config after deploy so `/app/*` is fully gone at the edge.
5. Health check: `curl -f http://127.0.0.1:8421/health` → expect crawl4ai version + ok.

## B. Smoke the fixes are live
- `curl /` should NOT show `/app` in nav; `/app` → 404.
- `GET /v1/hosted/me` (test key) → `max_pages_per_run: 100` (was 25) confirms new plan cap deployed.
- A scrape of a robots-disallowed URL → honest 403 (FX-10a).
- `docker exec scout id` → non-root (FX-13a).

## C. Re-run the full e2e matrix on prod (chase 100%)
- Re-run the harness (`docs/test-results-2026-07-26/harness/scout_e2e.py`) against all 5 sites with the test key.
- Expect improvement: adobe/salesforce pass (retry), lacoste products via fallback + up to 100 records (cap), algolia execs now populated (FX-4).
- Honest watch item: eyebuydirect (Akamai) may still block even with fallback — classify honestly, don't force-pass.
- Write results to `docs/test-results-2026-07-27/` and diff against the 2026-07-26 run (11 pass / 18 fail baseline).

## D. Rollback
Keep the previous image tagged; if health fails or PRISM neighbor is impacted, `docker compose up -d` the prior image. The deploy is reversible.

## Stripe live wiring (when founder provides live keys) — separate, gated
Set on the box `.env` (founder places the secret; I never see raw sk_live):
`STRIPE_SECRET_KEY=sk_live_...`, `STRIPE_UNLIMITED_PRICE_ID`, `STRIPE_STANDARD_1000/3000/15000_PRICE_ID` (all live-mode price IDs), `STRIPE_WEBHOOK_SECRET=whsec_...`. Restart scout. Then one real card charge → confirm `hosted_payment_events` row + credits issued + funds in Stripe balance.
