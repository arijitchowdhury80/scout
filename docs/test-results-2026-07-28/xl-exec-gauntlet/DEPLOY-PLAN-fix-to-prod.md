# Deploy the exec-extraction fix to prod — concrete runbook (2026-07-28)

**Goal:** get the reconcile.py + 4-source-waterfall fix live on `scout.chowmes.com` so the
hosted XL test measures the real fixed feature. Gated on founder "go" (prod deploy).

## State (verified this session)
- Local HEAD `ef04ee2` = the fix. **18 commits ahead of `origin`.** Fix is only on this machine.
- `origin` branch + **VPS deployed tree** both at `68a940a` — **pre-reconcile** (`reconcile.py` absent → confirmed STALE).
- VPS: `/opt/prism/scout`, pulls from GitHub, **passwordless sudo**, deploy via `docker/scout-deploy.sh`
  (versioned: snapshot-tags prior image, keeps current+previous, health check). **Reversible.**
- PR #2 OPEN + MERGEABLE (reflects stale origin until push).
- D0 gate: ruff ✓, ruff-format ✓, pyright 0 errors ✓, unit tests <pending→must be green>.

## Recommended path: deploy the branch (lowest risk, fastest to green hosted)
1. **Push the fix to GitHub** (backs it up + updates the deploy source):
   `git push origin fix/launch-readiness-fx1-fx7`
2. **On VPS** — advance the checkout + rebuild (all steps reversible):
   ```
   cd /opt/prism/scout && git fetch origin && git checkout fix/launch-readiness-fx1-fx7 && git pull --ff-only
   # /data ownership for non-root uid 10001 (FX-13a) — check, chown if needed:
   sudo chown -R 10001:10001 <the /data bind mount> 2>/dev/null || true
   cd docker && sudo bash scout-deploy.sh
   # nginx (FX-7): reload so /app blocks are gone at the edge
   sudo nginx -t && sudo systemctl reload nginx
   ```
3. **Health:** `curl -f http://127.0.0.1:8421/health` → ok.

## Post-deploy verify (D3 — the real gate)
Re-run the hosted probe (`scratchpad/hosted_run.py`) on **Stripe, Datadog, Anthropic**. PASS iff:
- Stripe→Lightspeed (Dax Dasilva) leak **GONE**; Datadog→MongoDB (Dev Ittycheria) leak **GONE**.
- `total_sources > 1` (waterfall runs: onsite + Wikidata/SEC/Wikipedia).
- Real CEO present (Datadog → Olivier Pomel).
- No prose sentences as titles / role-strings as names.
Only after D3 passes is the 500-company hosted XL meaningful.

## Rollback (if health fails or PRISM neighbor impacted)
`docker tag docker-scout:<prev-stamp> docker-scout:latest && cd /opt/prism/scout/docker && sudo docker compose up -d`

## Follow-up hygiene (not on critical path)
Merge PR #2 → main after the branch push so `main` (CI-gated) carries the fix and stops
being 29 commits behind. Can be done post-deploy.
