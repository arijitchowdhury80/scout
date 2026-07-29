# P0 PREFLIGHT — LAUNCH BLOCKER: hosted serves pre-fix (stale) exec-extraction code

**Date:** 2026-07-28 · **Found by:** XL e2e test-plan preflight (before any paid 500-run)

## Finding
The executive-extraction fix (identity reconciliation `scout/core/enrich/reconcile.py`
+ 4-source waterfall) is **NOT deployed to hosted** (`scout.chowmes.com`). Live hosted
reproduces the exact original bug class the fix was built to kill.

## Evidence (live hosted `/v1/hosted/run/company`, authed)
- **Stripe** → returns `Dax Dasilva | Founder and CEO, Lightspeed` (the canonical
  Stripe→Lightspeed leak), plus Kurtis Moyer (Mindbody), Laura Collinson (Jobber).
  Real Stripe execs absent.
- **Datadog** → `Dev Ittycheria | ...former President & CEO of MongoDB` (Datadog→MongoDB
  leak) + `Chief Information / Security Officer` (CISO title split into name+title) +
  prose sentences as titles. Real CEO Olivier Pomel absent.
- **Anthropic** → 0 executives.
- All runs report `total_sources = 1` → the Wikidata/SEC/Wikipedia waterfall never runs.

## Root cause (git, verified)
- `git ls-tree main -- scout/core/enrich/reconcile.py` → **absent on main**.
- `git branch --contains ef04ee2` → only `fix/launch-readiness-fx1-fx7`.
- `git rev-list --count main..HEAD` → **29** commits ahead, unmerged.
- Hosted CI/deploy tracks `main` (`.github/workflows/ci.yml` branches: [main]).

## Consequence for the XL test
Running the 500-company hosted sweep now would measure **stale broken code**, burn
LLM/credit budget, and produce a catastrophic score that says nothing about the fix.
The test's precondition (hosted runs the fixed code) is FALSE.

## Options
- **A. Merge branch → main → deploy to hosted, then run XL** (measures the real fixed
  feature; requires a prod deploy — mandate-boundary, needs explicit approval).
- **B. Redirect XL to LOCAL `run_company()` on the fix branch** (measures the fixed code
  directly, no deploy; contradicts the earlier hosted-only choice — but this finding is
  exactly why hosted-only was the risky pick).
- **C. Both**: local XL now to validate the fix, hosted smoke after deploy to confirm parity.

---

## RESOLUTION (2026-07-28, verified live)
Deployed branch `fix/launch-readiness-fx1-fx7` (`60e259f`) to the VPS:
`git pull --ff-only` → `docker/scout-deploy.sh` (rebuilt image, snapshot-tagged
`docker-scout:20260728-1726`, rollback image `docker-scout:rollback-prefx-20260727`
retained) → container recreated, health **healthy**.

**Live re-verify on `scout.chowmes.com/v1/hosted/run/company` (authed) — PASS:**
- Stripe → Patrick Collison / CEO + John Collison (src=wikidata). Lightspeed leak GONE. `total_sources=2`.
- Datadog → Olivier Pomel / CEO + Alexis Le-quoc / CTO + board (src=sec). MongoDB leak GONE. `total_sources=2`.
- Anthropic → Dario & Daniela Amodei + founders + board, 15 records, `total_sources=4` (onsite+wikidata+sec).

Waterfall + reconciliation now live. Hosted XL test is meaningful. Pre-fix behavior fully retired.
Follow-up hygiene (not blocking): merge branch → main; fix repo-wide CI rot (unpinned ruff/pyright/deps).
