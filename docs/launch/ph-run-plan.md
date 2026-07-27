# Scout — Product Hunt Beta Launch Run Plan

**Track B, Phase 2 · Drafted 2026-07-26 · Owner: Arijit (founder) + orchestrator**
**Goal:** PH beta launch → 50–100 real beta signups, contend for Product of the Day/Week.
**Product surface:** scout.chowmes.com (live, commit 908f6d9) · signup = `/beta` → `POST /v1/hosted/beta-key` → key by email · skill users get the package via email → support@ → download link.
**Status legend used below:** each item carries an acceptance check. Nothing in this doc is posted or published by the orchestrator — every public action is founder-executed.

---

## 1. Pre-launch content/docs work

Order matters: docs → llms.txt → capability pages → teaser. All four must be DONE before the PH Upcoming page goes up (teaser links point at them).

### 1.1 Finish Mintlify docs at docs.scout.chowmes.com
Current state: `docs-site/` exists in-repo (index, quickstart, credits, endpoints/, destinations, support, account .mdx) but Mintlify is **not connected** and the subdomain is **not live** (SESSION.md: "Mintlify NOT started").

What to do:
1. Founder: create Mintlify project, connect the GitHub repo, set docs path = `docs-site/` (per `docs-site/README.md`).
2. Founder or orchestrator (via Hostinger DNS API, key in `Scout/.env.local`): add the CNAME Mintlify gives for `docs.scout.chowmes.com`.
3. Orchestrator: content pass on every `.mdx` — every endpoint documented with a copy-pasteable curl that works against prod with a beta key; quickstart must go email→key→first successful run in under 5 minutes.
4. Add a "Beta" banner/callout linking to scout.chowmes.com/beta on the docs index.

Acceptance check: `curl -sI https://docs.scout.chowmes.com` returns 200; quickstart curl executed against prod with a fresh beta key returns a real run result; every endpoint page's example verified live (Done-Means-Live: run each curl, capture output).

### 1.2 Add llms.txt
What to do: generate `llms.txt` (and ideally `llms-full.txt`) — Mintlify emits these automatically for hosted docs; verify, and additionally serve one at `https://scout.chowmes.com/llms.txt` from the website (nginx static) summarizing: what Scout is, API base URL, docs URL, beta signup URL, the skill install flow.

Acceptance check: `curl -s https://docs.scout.chowmes.com/llms.txt` and `curl -s https://scout.chowmes.com/llms.txt` both return non-empty, current content mentioning `/beta` and the API base.

### 1.3 Per-capability marketing pages
Current state: NOT built (SESSION.md remaining-work #8). Capabilities: scrape, crawl, map, screenshot, products, company intelligence (dossiers), destinations.

What to do: one page per capability under `website/` (e.g. `/scrape.html`, `/products.html`, …), each with: plain-English what-it-does, one live-looking example (input → evidence-grade output), credits cost, curl snippet, CTA to /beta. Must follow the LOCKED design system (`docs/product/design-system.md`) — mint neumorphism, amber = evidence marks only. Route through `frontend-builder` skill per house rules. These are also the PH-traffic landing targets and the pages the gallery images will screenshot.

Acceptance check: each page live at its URL (200), passes a visual QA pass with Arijit against design-system.md, each contains exactly one primary CTA to /beta, mobile 375px renders without horizontal overflow.

### 1.4 "Coming soon / notify me" teaser → PH Upcoming list
What to do:
1. Founder: create the product page on Product Hunt and enable a **Coming Soon / Upcoming** page (PH's built-in teaser — collects followers who get notified at launch). Needs: name, short blurb, one teaser image (reuse hero), planned launch window.
2. Add a small "We're launching on Product Hunt — get notified" strip to scout.chowmes.com index linking to the PH Upcoming page (founder pastes URL; orchestrator wires the strip).
3. Everyone who emails support@ or signs up pre-launch gets a PS line pointing at the Upcoming page (add to the enablement email template).

Acceptance check: PH Upcoming page live with ≥1 image; site strip live and visually QA'd; target ≥50 Upcoming followers by launch day (tracked in the T-14 sequence below).

**Blocking dependency also in this phase:** the branded enablement email must be wired into the key-delivery sender (SESSION.md item — template approved, NOT wired), and support@scout.chowmes.com DNS (ImprovMX MX+SPF) must be live and tested, because launch-day signups will hit both. Acceptance: send a real /beta signup to a personal address, receive the branded email, key works; test mail to support@ lands in Arijit's Gmail.

---

## 2. PH listing asset checklist (fill-in templates — copy is a separate content task)

| Asset | Spec | Template / notes |
|---|---|---|
| Product name | Exact, short | `Scout` (consider `Scout by chowmes` only if name collision on PH — check availability first) |
| Tagline | ≤60 chars, no punctuation tricks | `[VERB] [what] [differentiator]` — e.g. shape: "Evidence-grade web data for your agents and APIs" (57c). FILL: `________________________________` (count chars) |
| Description | ~260 chars visible; front-load first sentence | Para 1: what + who for. Para 2: the 6 capabilities in one line. Para 3: beta offer (10k credits) + how to start. FILL: `____` |
| Topics | 3 max, pick high-traffic | Candidates: `Developer Tools`, `APIs`, `Artificial Intelligence`, `SaaS`, `Web scraping` (if exists). Pick 3: `____` |
| Gallery images | 4–6 images, **1270×760 px** (PH standard), PNG/JPG <3MB each | Shot list: (1) hero: playground with a real run + evidence marks, (2) one capability page or output per remaining slot (products, dossier, map), (3) pricing card, (4) "works as a Claude/Codex skill" frame. First image doubles as social share — put the tagline on it. Design-system compliant. |
| Demo video | ≤60s, landscape, hosted on YouTube/Loom and added to gallery (video slots first position if strong) | Script skeleton: 0–5s problem, 5–20s anon playground run live, 20–40s signup→key→curl first run, 40–55s destination push / skill use, 55–60s CTA card. Reuse/extend the existing site demo video (commit 9f9ff2a) if it fits 60s. FILL: script `____` |
| Thumbnail/logo | 240×240 px, animated GIF allowed (subtle animation lifts CTR) | Use the reticle mark (the Scout "o" full-reticle with amber core, per design-system.md). Optional: 2-frame GIF of the reticle "locking on". |
| First maker comment | Posted at 12:01am PT, pinned by default | Structure: (1) why I built it — the Apify-replacement / evidence-grade origin story, 2–3 sentences; (2) what makes it different (evidence on every data point, skill-native distribution); (3) exactly what beta testers get (10k credits, direct founder support); (4) 2 questions inviting feedback; (5) beta link. FILL: `____` |

Also prepare (same content task): 3 canned comment replies (pricing question, "vs Firecrawl/Apify" question, "is there an API/SDK" question), and a launch-day social post pack (X, LinkedIn) — see §3/§4.

Acceptance check: all assets exist as files in `docs/launch/assets/` + copy doc reviewed by Arijit (HITL — design decisions are his call), image dimensions verified, video ≤60s verified.

---

## 3. Hunter and pre-launch warmup

### 3.1 Hunter decision
Reality in 2026: the hunter matters far less than it used to — PH's feed algorithm weighs engagement, not hunter follower counts, and self-hunting is normal and respected. **Default: Arijit self-hunts.** Only pursue an external hunter if one exists in-network who (a) genuinely uses/likes Scout and (b) will write an authentic first comment — cold "top hunter" outreach is low-yield and can look mercenary. If hunting externally: confirm 7+ days out, give them beta access + asset pack, agree on the 12:01am PT slot; you still write the maker comment.

Decision gate (T-10): named hunter confirmed in writing, or self-launch locked. No hunter search after T-7.

### 3.2 Warmup sequence T-14 → T-1 (all founder-posted; orchestrator drafts)
PH rewards accounts with real history and a warm audience that shows up organically. Rules throughout: never ask anyone to upvote; ask them to "check it out and leave honest feedback."

- **T-14:** PH Upcoming page live (§1.4). Arijit's PH profile dusted off: photo, bio, follow 20–30 relevant makers, leave genuine comments on 1–2 launches/day from now on (account warmth matters; a dormant account that only appears on launch day converts worse).
- **T-14 to T-8:** Build the notify list. Post 2 build-in-public pieces (X/LinkedIn): one on evidence-grade extraction (show a real dossier), one on "the API is the product; the skill is the distribution." Each links to the Upcoming page. Email existing contacts/beta-interest list: "launching on PH on [date], follow here."
- **T-7:** Freeze assets (§2 all done). Dry-run the full funnel end-to-end as a stranger (incognito: PH draft → site → /beta → email → first run). Fix leaks (§5). Confirm hunter/self-hunt.
- **T-5:** Line up 10–15 "first hour" friendlies — people who genuinely know Scout (beta users, peers). Message: "we go live 12:01am PT on [date]; if you find it useful, honest comments/questions in the first hours help a lot." (Comments and questions, never upvote asks.)
- **T-3:** Post demo video natively on X/LinkedIn as a teaser. Second email to the notify list with the date. Schedule launch-day posts as drafts.
- **T-1:** Final prod checks: /beta signup live-test, support@ live-test, VPS load headroom sanity check (anon playground limiter 5 runs/IP/day + global ceiling — confirm the ceiling won't throttle legit PH traffic; raise it for launch week if needed, and confirm rollback). Sleep plan: launch is 12:01am PT — decide who covers which hours (§4).

Acceptance check: Upcoming followers count logged at T-7 and T-1; funnel dry-run evidence (screenshots of each step) saved to `docs/launch/`; friendlies list of ≥10 names exists.

---

## 4. Launch day — hour-by-hour runbook (12:01am PT)

PH day runs 12:00am–11:59pm PT; ranking is engagement velocity-weighted, early sustained activity beats a late spike. **Never solicit upvotes anywhere** — no "upvote us" in emails, posts, DMs, communities, or the site; no upvote-exchange groups; no incentives (PH detects vote rings and de-ranks/bans). Ask for *feedback*, link the *PH page*, let votes happen.

| Time (PT) | Action |
|---|---|
| 12:01am | Launch goes live (scheduled in PH dashboard beforehand). Immediately post the first maker comment (§2). Verify listing renders (gallery, video, links). Site strip switches from "coming soon" to "We're live on Product Hunt today" linking the launch page. |
| 12:05am | PH auto-notifies Upcoming followers. Post launch announcement on X + LinkedIn ("we're live on PH today, here's what Scout does + link"). Message the 10–15 friendlies with the link. |
| 12:15am–2am | Respond to every comment within minutes (founder or orchestrator-drafted, founder-posted). Then sleep if solo — set the next block. |
| 6am–9am | Morning surge (US east coast + EU afternoon). Second social post: a concrete use-case thread (real dossier output, evidence marks). Reply to all overnight comments. Email the full notify/contact list: "we're live, would love your honest take" + PH link. Post to 1–2 communities where Arijit is a *member in good standing* (relevant Slack/Discord/subreddit) following each community's self-promo rules — share the story, not an upvote ask. |
| 9am–12pm | Peak comment window. Cadence: check PH every 20–30 min; answer every question substantively (comment replies are ranked content — treat each as micro-marketing). Anyone who says "trying it" gets a follow-up offering direct help. Watch signup feed; personally reply to early beta signups. |
| 12pm–3pm | Third social post: behind-the-scenes/build-in-public angle. Thank-you replies to notable commenters. If a competitor comparison thread appears, answer factually (differentiation doc: `docs/product/differentiation.md`) — never disparage. |
| 3pm–6pm | Engagement lull. Ship-something moment: post a maker comment update ("since this morning, N of you signed up — top question was X, here's the answer/fix"). This restarts comment velocity. |
| 6pm–9pm | West-coast evening push. Final social nudge ("last few hours, thanks for an amazing day + what we learned"). Keep replying. |
| 9pm–11:59pm | Wind-down. Final maker comment: thank-you + what happens next for beta testers. Log final metrics (§6). |
| Day+1 | Reply to stragglers (comments stay open), send the day-1 recap post, email new signups who haven't run anything yet (activation nudge). |

Comment response rules: answer everything, even hostile ones — brief, factual, generous; concede real gaps ("not built yet — on the list, here's the workaround"); never argue; questions you can turn into docs, do so same-day and link back.

Support flow on the day: skill-package requests arrive at support@ → founder replies with the download link (canned reply drafted at T-7). SLA: <2h during waking blocks.

---

## 5. Visitor → signup conversion plan (PH → /beta → email key → first run)

### Current flow (verified in `website/beta.html`)
PH listing → scout.chowmes.com (or capability page) → `/beta` page → form (name + email) → `POST /v1/hosted/beta-key` → key delivered **by email only** (never shown in browser) → user makes first curl / playground run. Beta grant = 10k credits. Duplicate signups are explicit (commit 41eb35f). Anonymous playground allows 5 runs/IP/day preview-only before signup.

### Known/likely leaks and fixes (pre-launch work items)
1. **Email-only key delivery is the biggest leak.** PH visitors are impulse-driven; any delay between submit and inbox kills activation, and the current sender still sends the **old plain-copy email** (branded template not wired). Fix: wire the approved branded email (SESSION.md item 3) — key in dark code block + "first 5 minutes" curl steps; verify delivery latency <60s via Resend; make the post-submit success state on /beta do work: "Key sent — while you wait, try the playground" + inline quickstart curl with a `YOUR_KEY` placeholder.
2. **Deliverability.** Resend domain SPF/DKIM must be green before launch; the exposed Resend key rotation (deferred backlog) should happen before, not after, PH-scale traffic. Check spam-folder placement to Gmail/Outlook test accounts at T-7.
3. **Homepage → /beta path.** During launch day, the site's primary CTA everywhere (index, capability pages, pricing, docs banner) should be the beta signup, one click away. Audit at T-7: from any page, /beta in ≤1 click.
4. **Anon playground as the bridge.** PH traffic that won't give an email yet should hit the anon demo first — it converts skeptics. Confirm the 5 runs/IP/day + **global ceiling** won't exhaust mid-morning under PH load (raise ceiling for launch week; this is a founder mandate-boundary call since it touches prod limits).
5. **No email verification = junk signups** (signup-abuse hardening is deferred). Accept for launch; measure real-vs-junk by activation, not raw count.
6. **Skill-flow friction.** The skill package requires email→support→download-link — a manual step. Fix for launch: dedicate a docs page "Use Scout as a Claude/Codex skill" that sets the expectation ("email support@, link within 2h") so it reads as white-glove beta, not brokenness.
7. **First-run failure = silent churn.** The enablement email's first curl must be tested against prod weekly through launch. Add a "stuck? reply to this email" line — replies go to support@ → Arijit.

### Funnel instrumentation (needed to know if any of this works — see §6)
Minimum: nginx/access-log counts per stage + backend counters. Stages: (a) site sessions with `ref=producthunt` (append `?ref=producthunt` to every PH-facing link), (b) /beta pageviews, (c) `POST /v1/hosted/beta-key` successes, (d) first authenticated run per new key within 24h/72h. If no analytics exists on the site, a log-parsing script is enough — do not add a tracking vendor for this.

Target math: Product-of-the-Day traffic is typically 2–10k visits. At 3k visits: 30% reach /beta (900), 20% submit (180), 50% activate (90) → the 50–100 goal needs roughly a top-5 finish OR better-than-baseline conversion. The conversion levers above matter more than the rank.

---

## 6. Launch-day success dashboard

One shared doc/terminal (orchestrator can maintain a live tally from logs + PH page polls). Log every 2h during the day.

| Metric | Source | Green | Yellow | Red |
|---|---|---|---|---|
| Upvote velocity | PH page (manual/poll) | top-5 at 9am PT | top-10 | below fold |
| Comments answered | PH page | 100% <1h | <3h | unanswered >3h |
| Site sessions (ref=producthunt) | access logs | ≥1,500 by 6pm | 500–1,500 | <500 |
| /beta submits (signups) | backend counter / DB | ≥60 by EOD | 25–60 | <25 |
| **Activation: first successful authenticated run** | RunDB / API logs per new key | ≥50% of signups within 24h | 25–50% | <25% |
| Key-email delivery latency + failures | Resend dashboard | <60s, 0 bounces to majors | isolated bounces | systemic bounces |
| support@ inbound + SLA | Gmail | all <2h | <6h | backlog |
| API error rate / p95 latency | VPS logs / health endpoint | normal | elevated | 5xx spike (drop everything — a down API on PH day is fatal) |
| Anon playground global-ceiling headroom | limiter counters | <50% used by noon | 50–80% | ceiling hit |

North-star for the launch: **activated beta testers (first successful run), not upvotes.** 100 signups with 20 activations is a worse outcome than 60 signups with 45.

Post-launch (Day+1 to Day+7): D1/D7 return-run rate per cohort, credits consumed per active key, support themes → docs fixes, and a written retro in `docs/launch/`.

---

## Consolidated pre-launch gate (all must be green before scheduling the PH date)

1. Mintlify docs live + every curl verified (§1.1)
2. llms.txt live both domains (§1.2)
3. Capability pages live + visual QA with Arijit (§1.3)
4. PH Upcoming page live, site strip live (§1.4)
5. Branded enablement email wired + live-tested; support@ DNS live-tested (§1 dep)
6. All §2 assets done + Arijit copy sign-off
7. Hunter/self-hunt decision locked (T-10)
8. Funnel dry-run clean end-to-end, instrumentation counting (§5)
9. Anon-demo ceiling + load headroom decision made (founder call)

Open founder decisions required before T-14: launch date (Tue–Thu PT generally strongest for Product of the Day contention; Sun/Mon weakest competition but least traffic — pick based on whether the goal is badge or bodies; for 50–100 testers, traffic wins → Tue/Wed), hunter vs self, launch-week ceiling raise.
