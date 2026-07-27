# Product Hunt Launch — Mechanics Gap Analysis (Scout)

Date: 2026-07-26 · Track B, Phase 1 · Author: launch-research agent
Goal: POTD (ideally POTW) + 50–100 real beta testers for scout.chowmes.com

---

## 1. How ProductHunt ranking actually works in 2026

### 1.1 Ranking algorithm signals

- **Velocity over raw count.** Rank is a function of weighted upvotes over time, not the total. The 2026 algorithm weights **sustained hourly velocity across a ~20-hour window** rather than a first-2-hour spike; a launch pacing 100→200→200→100 across the day beats one that spikes 200 in hour one then stalls. Reported target: ~45–55 upvotes/hour on weekdays, ~30–35 on weekends. Sources: [LaunchPact algorithm breakdown](https://www.launchpact.io/blog/product-hunt-algorithm), [TrendGap 2026](https://trendgap.io/blog/product-hunt-launch-upvotes-rank-2026), [Poindeo ranking explainer](https://poindeo.com/blog/product-hunt-upvote-ranking).
- **Voter credibility weighting.** An upvote from an aged, active PH account (years old, has hunted/voted before, votes in first hours) is worth roughly 5–10x one from a fresh account. Bursts from accounts created in the past week trigger dampening. Source: [LaunchPact](https://www.launchpact.io/blog/product-hunt-algorithm).
- **Comments are a primary ranking input, not decoration.** Comment depth (multi-sentence, use-case specific) and maker responsiveness count; guides report 300 upvotes + 80 substantive comments commonly outranks 400 upvotes + 15 generic ones. Sources: [Blazon Agency](https://blazonagency.com/post/product-hunt-algorithm-2026-software-launch), [Foundra 2026 playbook](https://www.foundra.ai/key-reads/product-hunt-playbook-first-time-founders-2026-after-algorithm-shift).
- **Unnatural-pattern detection.** 50 votes in 3 minutes then silence gets flagged; PH removes non-genuine votes and monitors point fluctuation throughout the day. Sources: [Causo Hub realistic playbook](https://hub.causo.ai/guides/product-hunt-launch-2026-realistic-playbook), [PH help — fair voting](https://help.producthunt.com/en/articles/11869098-how-does-product-hunt-ensure-fair-voting-and-prevent-spam-or-vote-manipulation).
- **New-user acquisition bonus.** The 2026 algorithm reportedly rewards launches that bring new users to PH, not just ones that mobilize existing communities. Source: [LaunchList 2026 guide](https://getlaunchlist.com/blog/how-to-launch-on-product-hunt-2026).

### 1.2 Launch window

- Launch day = the 24h starting **12:01 AM Pacific**. PH's own guide: "a rule of thumb is to schedule your launch for 12:01am PST." First ~6 hours largely decide the ranking; treat launch day as a 12–16 hour marathon with outreach in three waves (midnight, morning, afternoon). Sources: [PH official — preparing for launch](https://www.producthunt.com/launch/preparing-for-launch), [TrendGap](https://trendgap.io/blog/product-hunt-launch-upvotes-rank-2026), [Waitlister checklist](https://waitlister.me/growth-hub/guides/product-hunt-launch-checklist).

### 1.3 "Upcoming" / Coming-Soon teaser — DISCONTINUED

- PH **discontinued Coming Soon / teaser pages in August 2025** (confirmed on PH's own forum; PH staffer Mike Kerzhner: "We are very much thinking of alternatives to Coming Soon!" — none specified). The old notify-me mechanic (followers emailed at launch) is gone; the old help article now 404s. Any 2026 guide telling you to "grow your notify-me list" is stale. Pre-launch warm-up now = your own channels (email list, X/LinkedIn, communities) starting ~14 days out. Sources: [PH forum thread on discontinuation](https://www.producthunt.com/p/general/product-hunt-discontinued-coming-soon-teaser-pages-did-they-work-for-you), [PH forum — promoting without Coming Soon](https://www.producthunt.com/p/producthunt/how-can-you-promote-your-launch-when-the-coming-soon-page-is-not-longer-available), [Monolit social playbook](https://monolit.sh/blog/product-hunt-launch-social-media-strategy-founders-playbook-2026).
- **Action: verify in the PH launch dashboard at posting time** whether a replacement pre-launch feature has shipped — PH said alternatives were coming.

### 1.4 Hunter vs self-launch (2026)

- The hunter auto-notification boost has been **retired**; makers self-post directly, and the algorithm reduced hunter impact on rank. A 10K+ follower hunter still adds some visibility, but it is no longer a ranking lever. PH's own guide says anyone can submit their own product and **advises against paying external hunters**. Verdict: **self-launch**. Sources: [LaunchList](https://getlaunchlist.com/blog/how-to-launch-on-product-hunt-2026), [PH official guide](https://www.producthunt.com/launch/preparing-for-launch), [Foundra](https://www.foundra.ai/key-reads/product-hunt-playbook-first-time-founders-2026-after-algorithm-shift).

### 1.5 First comment (maker story)

- "70% of products who achieved Product of the Day, Week, or Month had a first comment by the maker" (PH official). Format: 3–5 paragraphs — why you built it, who it's for, key features, and **ask for feedback, NOT upvotes** (PH's explicit wording). Humble/helpful tone beats marketing language. Sources: [PH official guide](https://www.producthunt.com/launch/preparing-for-launch), [Motionfly checklist](https://motionfly.co/blog/product-hunt-launch-checklist).

### 1.6 Media specs (official + corroborated)

| Asset | Spec | Source |
|---|---|---|
| Thumbnail/logo | 240×240 square, <3MB; GIF thumbnails popular but <1/3 of POTD winners use them | [PH official](https://www.producthunt.com/launch/preparing-for-launch) |
| Gallery images | **1270×760** recommended; minimum 2 to show gallery; up to ~8 slots — hero shot → features → social proof → CTA; PNG for UI, GIF <5MB only for short demos | [PH official](https://www.producthunt.com/launch/preparing-for-launch), [Framed-shot sizes guide](https://framed-shot.com/guides/product-hunt-gallery-screenshots-sizes/), [Poindeo assets guide](https://poindeo.com/blog/product-hunt-assets-guide) |
| Video | Optional but ~53% of POTD winners since 2021 have one; **YouTube link only** (full URL, not private); best practice 45–60s, works muted | [PH official](https://www.producthunt.com/launch/preparing-for-launch), [Motionfly](https://motionfly.co/blog/product-hunt-launch-checklist) |
| Tagline | ≤60 chars, clarity over cleverness | [PH official](https://www.producthunt.com/launch/preparing-for-launch) |
| Description | ≤500 chars (some third-party guides say 260 — official page says 500) | [PH official](https://www.producthunt.com/launch/preparing-for-launch) |
| Topics/tags | Up to **3 launch tags**, strongly related — drives category-page discovery | [PH official](https://www.producthunt.com/launch/preparing-for-launch) |

### 1.7 Anti-gaming rules (what gets you penalized)

- Prohibited: mass-messaging users, **asking for upvotes**, bots, **incentivized upvotes** (discounts/lifetime deals for votes), any artificial activity inflation. Penalty: votes stripped, rank dropped, launch unfeatured/removed, possible loss of contribution access. PH monitors point fluctuations live during launch day. Safe framing: "we launched, would love your feedback" — never "please upvote." Sources: [PH Community Guidelines](https://help.producthunt.com/en/articles/3615694-community-guidelines), [PH help — can I ask friends to upvote](https://help.producthunt.com/en/articles/484935-can-i-ask-my-community-friends-family-to-upvote-a-product), [PH help — fair voting](https://help.producthunt.com/en/articles/11869098-how-does-product-hunt-ensure-fair-voting-and-prevent-spam-or-vote-manipulation).

### 1.8 Day-of-week: the Tuesday lore, updated

- Tue–Thu = highest traffic AND highest competition. Q1 2026 data: #1 POTD needs ~1,050 net upvotes on Tuesday vs ~550 on Saturday; top-5 needs ~500–900 weekday vs ~300–500 weekend. PH's own guide notes weekend launches get **15% more Visit-button clicks**. Sources: [TrendGap](https://trendgap.io/blog/product-hunt-launch-upvotes-rank-2026), [Analook](https://www.analook.com/blog/product-hunt-launch-strategy.html), [PH official](https://www.producthunt.com/launch/preparing-for-launch), [PH forum — best day](https://www.producthunt.com/p/producthunt/the-best-day-to-launch-on-product-hunt).
- **POTW mechanics:** awarded to the launch with the most points (upvotes + meaningful engagement, per PH) among everything launched Mon–Sun — so a weekend #1 with 550 votes will NOT win the week against a Tuesday 1,000-vote launch. If POTW is a genuine goal you must launch early-week and clear ~1,000+; if POTD badge + 50–100 testers is the real goal, a lower-competition day is far higher-probability. Sources: [PH help — Product of the Day/Week/Month](https://help.producthunt.com/en/articles/11751186-product-of-the-day-week-month), [PH discussion](https://www.producthunt.com/p/producthunt/how-product-of-the-day-week-month-are-chosen).
- **Realistic read for Scout:** a solo maker without a large PH-native following sustaining ~1,050 Tuesday votes is unlikely. **Wednesday or Thursday** balances traffic vs the Tuesday pile-up; **Saturday/Sunday** maximizes POTD-badge probability but forfeits POTW. Given the stated goal ranks POTD ≥ POTW ≥ testers, recommend **Wednesday 12:01 AM PT**, with Sunday as the fallback if the supporter list turns out small (<150 committed).

---

## 2. Scout asset inventory (verified on disk 2026-07-26)

| Asset | State | Evidence |
|---|---|---|
| Demo video | `website/assets/scout-product-demo.mp4` — **9.0s, 1280×720, h264** (+ .webm, .gif) | ffprobe |
| Screenshots | Playwright captures in `artifacts/` — 1280×1500/1600 full-page, wrong aspect for PH | sips |
| Tagline | "Scout. Evidence-grade web intelligence, live in your browser" (site `<title>`); "Evidence-grade web intelligence, live in your browser" alone = 54 chars, fits ≤60 | `website/index.html` |
| Logo | `scout-mark.svg`, `scout-wordmark.svg`, `reticle-52.png` (52×52 only) | ls/sips |
| Live site | scout.chowmes.com live; beta signup flow exists (`beta.html`) | repo + memory |
| Design system | Locked mint-neumorphism (`docs/product/design-system.md`) — PH assets must comply | repo |

---

## 3. Gap list

| # | PH requirement | Status | Spec | Closes it |
|---|---|---|---|---|
| 1 | Maker account, aged & active | **MISSING/UNKNOWN** | Account age + activity history weight your own launch credibility; create/activate NOW — vote, comment, follow topics for 2–4 weeks pre-launch | Arijit, manual (cannot be delegated — PH accounts are personal) |
| 2 | Hunter | **NOT NEEDED** | Self-launch is the 2026 norm; hunter boost retired; PH advises against paying hunters | Decision: self-launch (this doc) |
| 3 | Pre-launch teaser/"Upcoming" page | **N/A — feature discontinued Aug 2025** | Replace with 14-day warm-up on own channels + email list; verify dashboard for any new PH pre-launch feature at setup time | Arijit + Track B content plan |
| 4 | Thumbnail 240×240 (<3MB) | **NEEDS-WORK** | Export scout-mark.svg at 240×240 PNG on mint-neumorphic tile; optional subtle GIF variant | 10-min asset task from existing SVG |
| 5 | Gallery images ×5–8 @ 1270×760 | **MISSING** | Hero (tagline + product shot) → skill-in-Claude flow → evidence/citations output → API example → pricing/beta CTA; PNG, design-system compliant | New asset task; recapture UI at 1270×760 viewport, add framing per locked design system |
| 6 | Gallery video 45–60s, muted-friendly, on YouTube | **NEEDS-WORK (biggest asset gap)** | Existing demo is **9 seconds** — far short of the 45–60s best practice; also PH accepts **YouTube links only**, so it must be uploaded to a (non-private) YouTube channel | Re-record/extend demo to ~50s with captions; create Scout YouTube channel; upload |
| 7 | Tagline ≤60 chars | **HAVE** | "Evidence-grade web intelligence, live in your browser" (54) — drop the "Scout." prefix in the tagline field (name field carries it) | Done, needs final pick |
| 8 | Description ≤500 chars | **MISSING** | Value prop + who it's for + skill/API distribution angle | Copy task, 30 min |
| 9 | First-comment maker story | **MISSING** | 3–5 paragraphs: why built, who for, what's different (evidence-grade + Claude/Codex skill distribution), feedback ask — never upvote ask | Copy task; draft pre-launch, post at 12:01 |
| 10 | Topics (3 launch tags) | **MISSING (decision)** | Candidates: Developer Tools, Artificial Intelligence, APIs / SaaS / Data & Analytics — pick the 3 with best traffic-to-competition fit at setup | Decision task |
| 11 | Supporter/outreach plan (compliant) | **MISSING** | Need 150–400 real humans reachable in 3 waves across 20h; "feedback not upvotes" wording; NO incentives, NO mass DMs | Track B Phase 2 — list building |
| 12 | Launch-day comment engine | **MISSING** | Maker replies to every comment within minutes for 12–16h; comment depth is a ranking input | Arijit calendar block, launch day |
| 13 | Launch date/time | **DECISION** | 12:01 AM PT; Wednesday recommended (Sunday fallback); avoid US holiday weeks | Arijit decision |
| 14 | Beta funnel ready for spike | **HAVE (verify)** | beta.html live; confirm signup + duplicate handling + credit provisioning survive a 1-day spike | Smoke test pre-launch |

## 4. Bottom line

Media assets (video length + gallery images) and the human layer (aged maker account, supporter list, 16-hour comment marathon) are the real gaps — the product, site, tagline, and funnel are essentially ready. The teaser page you planned for does not exist anymore; the pre-launch list must be built off-platform. Self-launch; do not pay a hunter.
