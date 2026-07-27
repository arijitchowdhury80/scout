# Scout Launch-Readiness — Failure Report (2026-07-26)

Test target: **live prod** (scout.chowmes.com) + full website walk. Sources: `RESULTS-SUMMARY.md`, `verdicts.csv`, per-site JSON evidence, `website-clickthrough.md`, SSH prod inspection. Every claim is evidence-backed; failures were re-confirmed before counting.

## Headline

**Scout is not close to a public beta.** The core crawler fails on most large real-world sites, and self-serve signup is broken today. The friendly-site demo works; the general product does not.

- **Capability run:** 11 pass / 18 fail / 15 N/A (44 rows). Only algolia.com rendered.
- **Website walk:** 21 pass / 6 warn / 5 fail.
- **Payments:** 0 ever taken; Stripe in test mode on the live pricing page.

## 🔴 Launch-fatal

> **F1 CORRECTED 2026-07-27 after systematic-debugging repro.** The runner's "HTTP/2 failure on all major sites" conclusion was **only partly right**. Verified by re-running clean crawl4ai AND the live hosted path on an unloaded box: adobe.com and salesforce.com **succeed** (200, real markdown, 1 credit). So the `net::ERR_HTTP2_PROTOCOL_ERROR` was **transient resource contention** during the runner's 21-min window (box ~700 MB free RAM, shared with 9 containers; back-to-back Chromium renders momentarily OOM → HTTP/2 error). lacoste.com + eyebuydirect.com **do** fail deterministically (below). Net: F1 splits into F1a (transient/reliability) + F1b (deterministic commerce-site) + F1c (error opacity).

| # | Finding | Evidence | Why fatal |
|---|---|---|---|
| F1a | **Crawler intermittently fails under resource pressure** — `net::ERR_HTTP2_PROTOCOL_ERROR` appears when the shared box is memory-stressed; no retry, so one transient blip fails the whole run. Reproduces under load, not on an idle box. | runner JSON (fail) vs 2026-07-27 repro (adobe/salesforce succeed) | Under 150 concurrent this gets far worse; a launch-day crowd would see random failures. Ties to capacity (F5). |
| F1b | **Commerce sites fail deterministically** — lacoste.com + eyebuydirect.com return `success=False`, empty markdown, on repeat. Likely anti-bot/JS-SPA render returning nothing; the **browser fallback does not engage** (`fallback_attempted=true, fallback_used=false`). | lacoste job_44e76141086d4e80, eyebuydirect job_37b5cb402ea04e0a | Products/commerce is a headline use case; dead on real commerce targets. |
| F1c | **Failures are silent** — a failed scrape returns `success=False` with `status_code=None` AND `error_message=None` (markdown_len=0). No diagnostic surfaced to the user or logs. | lacoste job detail 2026-07-27 | Impossible to diagnose or support; users get an opaque failure. |
| F2 | **Beta signup broken** — `POST /v1/hosted/beta-key` → 502; Resend is in **sandbox mode** (rejects real domains: `550 … use our testing email address instead of domains like example.com`). Raw SMTP error leaks to the UI. | `screenshots/beta-signup-502-smtp-error.png` | No real user can get a key. The entire PH funnel dies at step one. |
| F3 | **Products vertical returns 0 records** on both commerce sites (lacoste, eyebuydirect); `blocked_pages: no_product_records`, `fallback_attempted=true, fallback_used=false` — the browser fallback never actually engages. | products JSON per site | Products/Algolia is a headline capability; dead on real commerce targets. |
| F4 | **`/app` still live** (200, "Scout App - Playground"); sub-routes 403 — half-torn-down. | `screenshots/app-still-live.png` | Founder decision: `/app` removed. Shipping a half-deleted app surface is a trust/attack-surface problem. |
| F5 | **Capacity cannot support 150 concurrent** — prod `HOSTED_MAX_ACTIVE_REQUESTS=2`, 2 workers, `max_concurrent_runs=1`/tenant, on a 2-vCPU/8 GB box shared with 9 containers. | SSH `printenv`, `/v1/hosted/me` | The stated launch goal (150 simultaneous) is physically unmet. |
| F6 | **25-record plan cap vs ">=100 products" promise** — hosted map/products capped at 25 records/call (`403 Plan allows at most 25 URLs`). | runner report | Even unblocked, the plan can't deliver the advertised catalog volume. Pricing-unit vs capability mismatch. |

## 🟠 Launch-risk

| # | Finding | Evidence |
|---|---|---|
| R1 | **Anti-bot (Akamai) block** on eyebuydirect page render; browser fallback not triggering (see F3). | eyebuydirect diagnostic scrape |
| R2 | **Exec extraction returns 0 execs** even on the one site that rendered (algolia.com company vertical: 1 company + 3 social, 0 executives). | algolia company JSON |
| R3 | **Stripe test mode on the live pricing page** (`cs_test_…` checkout session); 0 payments ever (`hosted_payment_events=0`). | web-walk; SSH DB |
| R4 | **Three inconsistent site navs** + **dead `/account` links** (`#demo`, `#purchase` don't exist on home) + **`/account` has no footer/legal links**. | `website-clickthrough.md` |
| R5 | **Terms/Privacy are self-labeled placeholders** and the terms text ("paid checkout deferred") contradicts the live working Stripe checkout. | web-walk |
| R6 | **robots.txt not enforced by default** in the crawl path — publishing a "we respect robots" policy would be a misrepresentation. | legal review; code |
| R7 | Container runs as **root**; **4,277 tenants / 33 real signups / 0 payments** (~99% junk); no signup abuse protection. | SSH `id`, DB counts |

## 🟡 Polish

- P1 Locked-tab console CTA ("Get your free API key") is a **no-op** (should route to /beta).
- P2 Focus ring low-contrast (WCAG technically passes; worth a contrast pass).
- P3 Live console mobile/desktop mode decided once at load, not re-evaluated on resize (stuck static if resized).
- P4 Footer link sets differ across home vs beta/pricing.
- P5 Free-credit copy: `app.html` "10,000" vs provisioned beta pass **5,000** std (+100 browser). Reconcile against the sizing exercise.

## Capability drift (build/claim decisions — dispositions locked in plan)

- `/app` → delete (F4). PDF extraction → build. CSV/JSON download → build. 24h-jobs filter → build. `website-quality` → drop + clean refs. "Top-selling" → no fabrication, best-seller proxy only.

## Confirmed GOOD (don't re-litigate)

- Home live console (scrape/map/crawl/products) returns real typed records with evidence on friendly sites.
- **Algolia push connector works end-to-end** (`destinations/send` → 4 records → verified searchable, nbHits=4).
- `/docs` `/quickstart` `/guide` `/examples` 308-redirect correctly to the docs site.
- Mobile-375 overflow **already fixed**; `/status` correctly 404s; hosted-only enforcement (no-key → 403) works.
- Overturned stale docs: lxml is **6.1.1** (CVE line cleared); email is *configured* (but sandbox-blocked); Stripe *wired* (test mode).

## N/A-on-hosted (not failures)

`/extract` (LLM disabled in prod), `/harvest` (needs local Chrome/CDP), `/app/*` (being deleted). 15 N/A rows are these + product/company rows that couldn't run because the page never rendered (blocked upstream by F1/F3).
