# Scout Private Beta Launch Plan

Date: 2026-06-27
Status: Draft

## Launch Principle

Do not launch Scout as a "Firecrawl killer." Launch it as an owned acquisition
workbench for teams who need evidence, browser capture, structured records, and
downstream artifacts.

## Audience

Primary private-beta audiences:

1. Solutions engineers building search/demo indexes.
2. AI-agent builders who need local web acquisition.
3. Competitive intelligence researchers.
4. RevOps/sales intelligence teams.
5. Internal product/data teams that need repeatable website-to-record workflows.

## Beta Promise

Scout helps you:

- scrape and crawl public pages,
- capture screenshots and browser evidence,
- structure captured HTML,
- extract product records,
- push Algolia-ready records,
- preserve artifacts and source evidence.

Scout does not yet promise:

- reliable unblock for every hard site,
- perfect vertical intelligence,
- production hosted scale,
- legal clearance for restricted websites,
- hands-off LinkedIn/job-auto-apply workflows.

## Launch Phases

### Phase 1: Internal Alpha

Goal: make the product understandable and repeatable.

Tasks:

- [ ] Fix current Ruff failure in `tests/e2e_real_websites.py`.
- [ ] Commit or discard current product extraction changes.
- [ ] Run unit, pyright, Ruff, and real-website E2E tests.
- [ ] Add feature list, differentiation, legal readiness, and third-party notices.
- [ ] Add a private-beta website page.
- [ ] Add a quickstart demo script.

### Phase 2: Private Beta

Goal: test with 5-10 trusted users.

Users:

- 2 solutions engineers,
- 2 AI builders,
- 2 competitive/research users,
- 1-2 RevOps/data users.

Success criteria:

- user can install and run Scout locally,
- user can complete one scrape/crawl/screenshot flow,
- user can complete one product extraction or structuring flow,
- user can find output artifacts,
- user understands blocked evidence,
- user can explain Scout's value back in one sentence.

### Phase 3: Public Developer Preview

Goal: make Scout self-serve for technical users.

Tasks:

- [ ] Publish polished README.
- [ ] Add installation and Docker guide.
- [ ] Add API examples.
- [ ] Add website with status and limitations.
- [ ] Add video/GIF demo.
- [ ] Add MCP server plan or implementation.
- [ ] Add dependency/license inventory.

### Phase 4: Commercial Packaging

Goal: make Scout safe to sell/support.

Tasks:

- [ ] Decide license/model for Scout itself.
- [ ] Security review.
- [ ] Legal/ToS review.
- [ ] Credential handling review.
- [ ] Hosted-vs-local product decision.
- [ ] Support/update process.

## First Demo Flows

### Demo 1: Page To Markdown

Use `/scrape` on a public about/blog page and show clean markdown, links, and
metadata.

### Demo 2: Product Page To Algolia Records

Use `/products` on a friendly ecommerce site, inspect records, then preview/push
to Algolia.

### Demo 3: Captured HTML To Records

Use `/structure` with held HTML and a CSS schema to produce typed records
without refetching.

### Demo 4: Browser Handoff

Open a hard page in the browser path, capture evidence, and show whether it was
blocked or usable.

## Website CTA

Private beta CTA:

> Try Scout locally. Bring one website you currently research or scrape by hand.

Developer CTA:

> Install Scout, run `scout serve`, and turn a URL into records.
