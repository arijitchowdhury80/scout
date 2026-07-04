<context>
Scout is a self-hosted web-intelligence platform (Crawl4AI-based, FastAPI, SQLite RunDB,
SSE, Algolia push) at scout project root. All 9 build phases are code-complete
(367 tests, pyright clean). Recent commits already touched beta signup, hosted pricing,
card-backed beta, and key delivery — so SOME of this goal is partly built and committed.
Goal is to turn Scout into a production-ready multi-tenant SaaS for 250 beta testers
launching TOMORROW. Charter: self-service, measurement, metering, monitoring.

Decided context (from interview):
- Distributions = EXACTLY TWO: (a) hosted HTTP API, (b) claude/codex skill that
  self-hosts Scout locally on the tester's machine. Remove Docker, remove CLI as a
  distribution, remove "python code" as a distribution. GitHub releases ship only these two.
- Email delivery: NOT set up yet → wire Resend, sending from a domain Arijit owns.
- Stripe: NOT set up yet → build integration, launch in Stripe TEST mode, hand Arijit a
  checklist to create the live account + paste keys post-launch.
- Hosting: Hostinger VPS 72.61.72.147 (Hermes box, creds in Hermes workspace .env.local).
  Hardware check runs against its REAL specs via SSH (hostinger-vps-ssh skill).
</context>

<task>
First AUDIT what is already built vs. pending across all items below (read git log, code,
website, tests — do not assume). Then complete every pending item to make Scout a
production-ready SaaS for 250 concurrent beta testers, with a working self-service key
pipeline, real metering/monitoring, Stripe $0-card beta capture, finalized credit economics,
updated website, load-test evidence at 250 concurrent, and a verified LLM-cost audit —
before tomorrow's launch.
</task>

<requirements>
1. LLM COST AUDIT (do FIRST — blocking, highest priority). Grep the codebase for any
   embedded LLM model id + any LLM API key (Crawl4AI LLM extraction strategies, OpenAI,
   Anthropic, etc.). Report exactly: which model, which key, which code paths call it, and
   whether 250 testers could run up a large bill. Default target = NO LLM on any tester-
   reachable path. If an LLM is required somewhere, STOP and surface it to Arijit with the
   cost exposure before proceeding. Do not launch with an un-audited LLM path.

2. SELF-SERVICE KEY GENERATION. Delete the password/auth code entirely. Replace with a
   public "Register — get your Beta Tester API Key" flow: tester submits name + email →
   record in DB → generate API key → email them the key. Email is signed by Arijit; draft
   the subject + body copy for approval. Send via Resend from Arijit's domain.

3. METERING + MONITORING (net-new — treat as not existing). Build per-key request metering:
   count/record every API call per tester, enforce a credit balance, expose usage. Add
   monitoring so Arijit can watch all 250 testers live (per-key volume, errors, credit burn).

4. CREDIT ECONOMICS + BUSINESS MODEL. Compute unit economics: what 1000 credits = for the
   user, what 1000 credits COST Arijit (VPS + any per-call cost), and the margin at a
   $10/1000 reference point. Decide credits-per-beta-tester and the 30-day trial cost
   exposure (must at least break even). PRESENT the numbers to Arijit for sign-off before
   hardcoding — this is a shared decision. Store the finalized calc in the vault.

5. WEBSITE. Update with finalized pricing (what a credit is / what 1000 credits get).
   Fix the key-generation UI (register form), the playground, and ensure every endpoint is
   reachable and working from the site. Verify hosted HTTP path + local self-host path both work.

6. STRIPE (test mode for launch). Build end-to-end card capture: beta testers sign up WITH
   a credit card but are charged $0 (invited). Pipeline fully verified — card captured, no
   charge. Secured. Include the future paid-credit purchase flow ($ → credits). Hand Arijit
   a go-live checklist.

7. DISTRIBUTION CUT. Reduce to HTTP + self-host skill only. Remove Docker (Dockerfile,
   compose, nginx, systemd), remove CLI/python as advertised distributions. Update docs,
   skill definition, and GitHub release story to reflect the two paths.

8. HARDWARE CHECK. SSH into VPS 72.61.72.147, read real CPU/RAM/disk, and judge whether it
   can host 250 concurrent testers generating heavy call volume. Report headroom; flag if
   under-provisioned with a concrete upgrade rec.

9. LOAD + FUNCTIONAL TESTS. Write a functional test script hitting every Scout endpoint, and
   a LOAD test simulating 250 concurrent users hammering each endpoint simultaneously. Run
   against hosted path. Provide evidence it holds without failure (latency, error rate,
   metering accuracy under load). Validate the local self-host path separately.

10. NO FEATURE GATING. All features 100% available to all testers for the beta.
</requirements>

<constraints>
- No LLM on tester-reachable paths unless explicitly approved by Arijit (cost risk).
- TDD always; three test layers (unit + integration + contract) before "done"; pyright clean;
  ruff clean; structlog; Pydantic on every boundary (per project CLAUDE.md hard constraints).
- No hardcoded secrets. Resend + Stripe keys via env only.
- Stripe launches in TEST mode; do not go live without Arijit's checklist sign-off.
- Credit economics are hardcoded ONLY after Arijit approves the numbers.
- Do not claim any item done without showing verification output.
- Launch is tomorrow — prioritize the blocking path: LLM audit → key pipeline → metering →
  hardware/load proof. Stripe test-mode + economics can finalize in parallel.
</constraints>

<deliverables>
- LLM audit report (model/key/paths + verdict) surfaced before any other work.
- Working self-service register→key→email flow (password code deleted), demoed end-to-end.
- Metering + monitoring live, accurate under load.
- Vault doc with finalized credit economics + margin math.
- Updated website (pricing + register + playground + all endpoints working).
- Stripe test-mode $0-card capture working end-to-end + go-live checklist.
- Distribution reduced to 2 paths; Docker/CLI removed; docs + GitHub release updated.
- VPS hardware verdict with headroom numbers.
- Load-test script + 250-concurrent run evidence; local self-host path validated.
- All verified with command output before any "done" claim.
</deliverables>

<out_of_scope>
- Stripe LIVE mode / real charges (post-launch, behind Arijit's checklist).
- Docker/CLI/pip distributions (being removed, not maintained).
- Paid GA pricing beyond the beta credit model.
- Feature gating / tiering (all features open for beta).
</out_of_scope>

<assumptions>
- "Local download path" = the skill self-hosting Scout locally (per interview).
- Resend is the email provider; Arijit will supply/verify a sending domain.
- Beta credit grant + trial length are proposed by the executor, approved by Arijit before hardcoding.
- Hosted Scout deploys to / runs on the Hostinger VPS for the beta.
</assumptions>

<original_input>
[Prompt 1]
ok so i am giving you the goal to build and implement things for production reasiness and your charter is all about self-service, measurement, metering and monitoring.
1) people will need a serl-service way to generate the key. Even that password thing, i think that is unnecessary. Please delete that code and remove that. Lets make it straight forward way for people to give their email addressed. We will send then an invite link to their email. They goto the email click the link and that will give them their API key. Or even better, in the screen they shoudl have a wau to "register - to get your Beta Tester API Key". People give their name and email. This will record them in our database, generate an API key and we will email them the API key. Lets work on the email format, body text etc. The email shoud be signed by me.
2) You need to fully compelte the API metering packaging and we need to add that to the website, what each credit is. Say of someone purchase 1000 credits for $10 then what will they get? and how much does 1000 credit cost me? how am i making money? so we need to fully decide on the business mdel and the commercial mechanics and we need to store this calcualtions in our vault too, after we have finalized. The webstie needs to be updated with pricing as well.
3) you need to fully compelte the Stripe integration. People shoudl be able to pay online, it shoudl be secured and should be fully functioning end to end. In fact even for beta people should sign up with credit card but since they are invited they will be $0. That way the pipeline is verified but that noone will pay anything, but we iwll have their credit card. I am going to give a free tiral for beta testes for say 30 sdays. but it will depend on the economics, as to how much it will cost me. I dont at least breakeven shoudl come back.
4) fully complete the self service side of things and the sef payment side of things and inviration beta customer side of things.
Ask me any question you have if you need my attention.
This is your goal to compelte

[Prompt 2]
ok so this is very critical. Your goal is to get scout fully production ready for SaaS multi-tanent use by 250 beta testers. The launch is tomorrow. Users will be testing everything, so we are not gating any features all features 100% will be availabel and should be availabel for people to use and test. They should be able to test hosted services and even if 250 peopel are all hitting at the same time the system should function without a hiccup. So you need to create test script and specifically load test script to test scout for 250 users all hitting simultaneously and testing each end point of scout. You also need to validate the local downlaod path. I also see we have mentioned docker, what is that? Are we saying that osmeone can download a docker instance or the CLI as a skill? I think we have too many options - HTTP, CLI, python code, Docker, that is way too many. Cut it down. Let is be HTTP and claude/codex skill. Thats it. I dont think we need docker. That is how we should even version on dithub with only these 2 distributions.
Check which LLM model is embedded and what is the LLM key. THis is crucially importatn. Ideally there should not be any LLM, and if ther eis then highlight it and bring that back to me, for i dont want 250 tester raising a 100k LLB bill for me, i cannot pay that. This is extremely importatn to verify before launch.
Testes should be able to generate their own key. Make that change that people can give their email address and generate their own key. We will need to store their email and also monitor them and meter then. We, meaning you and I need to decide how many credits a beta user will be given. We have not created the metering mechanism at all, how the hell are we going to measure people and bill them? You also need to do hardware check, is our VPS with the amount of hardware it has even capable of hosting an application that will generate millions of calls from 250 testes testing simultaneously and hitting it.
So this production preparadness is crucually important before the launch tomorrow and all missing things needs to be fixed and addressed incluing website fixes also like the key geneation pipeline, the measurement, the metering, the recording, the playground all end points wokring, the http hosted path fully working, the local download path fully working the dist ready and all that other things eveything we need for a beta launch
</original_input>
