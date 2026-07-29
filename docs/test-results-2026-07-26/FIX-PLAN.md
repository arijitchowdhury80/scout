# Scout Launch-Readiness — Fix Plan (2026-07-26)

Prioritized, owner-ready. **No fixes applied yet** — this is the ⛳2 gate input. Each item: root-cause hypothesis, fix approach, verify step, model routing, gate tag. Order = launch-critical first.

Legend: 🔴 fatal · 🟠 risk · 🟡 polish · ⚠ gated (needs explicit "go": prod/destructive/auth/payment/hardware).

---

## Tier 0 — Product actually works (do first; nothing else matters without these)

### FX-1 🔴 Crawler reliability + silent failures — **UPDATED with 2026-07-27 repro (systematic-debugging done for triage)**
Root cause corrected: NOT a universal HTTP/2 config bug (adobe/salesforce succeed on an idle box, clean crawl4ai and hosted path both). Three real sub-issues:
- **FX-1a — reliability under resource pressure:** transient `ERR_HTTP2_PROTOCOL_ERROR` under memory stress + **no retry**. Fix: add bounded retry/backoff on transient nav/network errors (defense-in-depth) AND size hardware (see FX-12). Verify: run N scrapes under load; transient blips retry and recover.
- **FX-1b — commerce sites fail + fallback dead:** lacoste/eyebuydirect render empty; the browser fallback path never engages. Fix: make fallback trigger on empty/blocked render; confirm on a rendered commerce page. Verify: lacoste + eyebuydirect return non-empty content or an honest "protected" verdict. (Merges with FX-2/FX-3.)
- **FX-1c — silent failures:** failed scrape returns `status_code=None`, `error_message=None`. Fix: surface the real status code + error from the fetch layer up through the response model + logs. Verify: a forced-fail scrape returns a populated error_message + status.
- **Route:** `superpowers:systematic-debugging` → Sonnet/high. Triage already falsified the HTTP/1.1 theory — do NOT force HTTP/1.1 blindly.

### FX-2 🔴 Products vertical returns 0 on commerce sites (F3) + browser fallback never fires
- **Root cause:** same nav-block as FX-1 + `fallback_used=false` — the anti-bot/browser fallback path is not triggering when the primary fetch is blocked.
- **Fix:** make fallback trigger on block/empty-records; verify listing-card + JSON-LD extraction on a rendered commerce page.
- **Verify:** lacoste + eyebuydirect return real product records (count > 0; aim for a page's worth).
- **Route:** Sonnet/high (after FX-1).

### FX-3 🟠 Akamai / anti-bot handling (R1)
- **Fix:** confirm stealth/browser-fallback engages on Akamai (eyebuydirect); document sites Scout can/can't do (set honest expectations — do not over-promise anti-bot).
- **Verify:** eyebuydirect renders or is honestly reported as protected. **Route:** Sonnet/high.

### FX-4 🟠 Exec extraction returns 0 (R2)
- **Root cause:** regex-title heuristic misses modern team-page markup.
- **Fix:** broaden extraction (structured team blocks + JSON-LD Person); verify on algolia.com. **Route:** Sonnet/high.

---

## Tier 1 — Signup + payment funnel (a launch needs a working front door)

### FX-5 🔴 ⚠ Beta signup broken — Resend sandbox (F2)
- **Root cause:** Resend domain/account not verified for arbitrary recipients → sandbox. **Config, not code** (mostly).
- **Fix:** verify the sending domain in Resend (SPF/DKIM/DMARC already noted), move out of sandbox; **also** stop leaking raw SMTP errors to the UI (catch → friendly message) and wire the approved **branded** key-delivery email (currently plain copy).
- **Verify:** signup with a REAL external inbox → key email arrives (Done-Means-Live, real inbox).
- **Route:** ⚠ founder go (touches prod email). Config = founder/ops; UI error-handling = Sonnet/high.

### FX-6 🟠 ⚠ Stripe live + real-payment proof (R3)
- **Fix:** swap `sk_test`→live keys + live price IDs + webhook; run a **real card charge** → confirm it lands in the founder's balance and credits issue; align terms copy (FX-10).
- **Verify:** one real payment visible in Stripe + `hosted_payment_events` row + credits granted.
- **Route:** ⚠ founder go (money). Founder supplies live keys; Sonnet verifies e2e.

---

## Tier 2 — Surface cleanup (what testers see)

### FX-7 🔴 Delete `/app` entirely (F4)
- **Fix:** remove `/app*` routes (`launch_site.py`), `website/app.html`, `app_runs.py`, `app_browser.py`, all nav links; ensure HTTP + skill are the only surfaces; add the **skill email→support→download-link** distro flow + verify its email sequence.
- **Verify:** `/app` → 404; no dead links; skill distro downloadable; distro email arrives. **Route:** Sonnet/high.

### FX-8 🟠 Nav + dead-link + footer consistency (R4)
- **Fix:** one canonical nav + footer across all pages; fix `/account` dead `#demo`/`#purchase` links; add footer/legal to `/account`. **Verify:** re-walk; zero dead links. **Route:** Sonnet/high.

### FX-9 🟡 Console polish (P1,P3), focus contrast (P2), footer parity (P4) — batch. **Route:** Sonnet/high.

---

## Tier 3 — Legal / trust / capability-truth

### FX-10 🟠 Publish real ToS/Privacy/AUP + enforce robots (R5,R6)
- **Fix:** replace placeholder terms/privacy with the drafted `docs/legal/launch/` docs (after lawyer review, tag-gated); **enforce `respect_robots_txt` default in the crawl path** so the policy is true; add `website/robots.txt`.
- **Verify:** live pages non-placeholder; a robots-disallowed URL is skipped by default. **Route:** Sonnet/high (code) + ⚠ lawyer review (legal).

### FX-11 🟡 Capability-truth builds (drift) — PDF extraction, CSV/JSON download, 24h-jobs filter, drop website-quality, fix credit copy (P5) after sizing validation.
- **Route:** Sonnet/high, TDD each. Each is build-or-correct-claim per the plan.

### FX-12 🔴 ⚠ Capacity for 150 concurrent (F5,F6)
- **Fix:** decide hardware (dedicated box or bigger VPS; current shares 2 vCPU with 9 containers); raise `HOSTED_MAX_ACTIVE_REQUESTS`/workers to a load-proven value; reconcile the 25-record plan cap vs the product volume promise (raise cap or correct marketing).
- **Verify:** **load test to 150 concurrent runs** with acceptable latency + PRISM neighbors healthy.
- **Route:** ⚠ founder go (hardware $ + prod). Sonnet builds load test; founder approves resize.

---

## Tier 4 — Hardening (before public exposure)

### FX-13 🔴 ⚠ Container non-root `scoutadmin:scoutgroup` (R7)
- **Fix:** add non-root user/group in Dockerfile + compose; `no-new-privileges`, `cap_drop`, read-only rootfs where feasible; chown `/data`. **Verify:** `docker exec scout id` → non-root; health green. **Route:** ⚠ founder go (prod deploy). Sonnet/high.

### FX-14 🔴 ⚠ Purge junk tenants + signup abuse protection (R7)
- **Fix:** purge ~4.2k junk tenants (**destructive — back up first**); keep the e2e test tenant; add email-verify/captcha to signup. **Verify:** tenant count sane; a scripted signup flood is blocked. **Route:** ⚠ founder go (destructive). Sonnet/high.

---

## Suggested execution order
1. FX-1 → FX-2 → FX-3 → FX-4 (make the product work).
2. FX-5, FX-6 (funnel).
3. FX-7, FX-8, FX-9 (surface).
4. FX-10, FX-11 (truth/legal).
5. FX-12, FX-13, FX-14 (capacity + hardening).
6. Re-run harness + website walk + full prod e2e → evaluate Beta Readiness Bar → go/no-go.

**Reality check:** FX-1 alone could be days of debugging; capacity + payment + legal each carry founder decisions and external dependencies. This is a multi-week program, not a pre-launch checklist. The PH date should gate on FX-1..FX-14 clearing, per the approved plan.
