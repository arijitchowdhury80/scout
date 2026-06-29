# Scout Release Checklist

Date: 2026-06-28
Status: Private beta release gate

This checklist decides whether Scout is ready for a public or wider private
beta release. Public launch is blocked until every required gate is checked or a
documented exception exists.

Current decision dashboard:
`docs/product/launch-decision-dashboard-2026-06-29.md`.

Current launch gate burndown:
`docs/product/launch-gate-burndown-2026-06-29.md`.

## Release Scope

Current intended release surfaces:

- local Python package: `scout-web`, installed command `scout`,
- Docker HTTP service,
- hosted API for limited private beta users,
- Claude/Codex skill documentation.

The legacy app UI is not a launch surface until it is rebuilt and certified.

## Blocking Decisions

- [ ] License decision recorded.
      Decision brief:
      `docs/legal/scout-license-distribution-decision-brief-2026-06-29.md`.
      Recommendation is Apache-2.0 for Scout local/core plus hosted/service
      monetization, but this is not approved yet.
- [ ] Final license expression added to `pyproject.toml`.
- [ ] `LICENSE` file added if Scout is open source or source-available.
- [ ] Public launch pricing and hosted usage limits approved.
- [x] Hosted economics and usage limits documented against the `$22` beta pass
      and any subscription alternative.
      Evidence: `docs/product/hosted-economics-and-usage-limits.md`.
      Result: local remains free, the `$22` hosted beta pass is finite credits,
      browser/rendered work is separately metered, and no unlimited hosted
      crawling should be sold. Final public pricing approval remains open.
- [ ] Registry publishing policy approved for PyPI, GHCR, Docker Hub, or other
      registries.
      Decision brief:
      `docs/legal/scout-license-distribution-decision-brief-2026-06-29.md`.
      Registry policy:
      `docs/product/registry-publishing-policy-2026-06-29.md`.
      Result: no PyPI, Docker Hub, GHCR, or broad public release artifact
      publishing until Scout's own license and package visibility are approved.

No public registry publish should happen until these decisions are closed.

## Package And Artifact Gates

- [x] Package metadata added for `scout-web`.
- [x] Clean wheel install smoke.
- [x] Installed `import scout` smoke.
- [x] Installed `scout --help` smoke.
- [x] GitHub release artifact workflow added.
- [ ] GitHub release artifact workflow run against a real `v*` tag.
- [ ] Release artifact downloaded from GitHub Release and smoke-tested locally.

## Product Capability Gates

- [x] Product records export beyond Algolia.
      Evidence:
      `docs/product/product-export-generalization-verification-2026-06-29.md`.
      Result: `scout product-export` writes JSON, JSONL, CSV, SQLite, and
      Google Sheets import bundles from the same product records. Algolia
      preview/push remains a supported adapter, not the only product data path.
      Direct Google Sheets API push and webhook export remain future work.

## Docker Gates

- [x] Docker image builds.
- [x] Docker runtime smoke for `/health`.
- [x] Docker runtime smoke for `/`.
- [x] Docker runtime smoke for `/styles.css`.
- [ ] Docker image publishing policy approved.
      Policy brief: `docs/product/registry-publishing-policy-2026-06-29.md`.
      Recommendation: GHCR before Docker Hub, after image visibility,
      provenance, and post-publish smoke gates are approved.
- [ ] Published Docker image smoke-tested if GHCR, Docker Hub, or another
      registry is used.

## Security And Legal Gates

- [x] Third-party notices.
- [x] Third-party notices included in wheel and sdist artifacts.
      Evidence: `python3 -m build` and artifact inspection confirmed
      `THIRD_PARTY_NOTICES.md` in `scout_web-0.1.0-py3-none-any.whl` and
      `scout_web-0.1.0.tar.gz`.
- [x] Dependency license inventory generated.
      Evidence: `docs/legal/dependency-license-inventory-2026-06-28.md`.
      Result: runtime inventory exists, but packages with missing license
      metadata still require manual upstream review before public launch.
- [x] Security policy.
- [x] Dependency CVE scan run and recorded.
      Evidence: `docs/security/security-audit-2026-06-28.md`.
      Additional refresh:
      `docs/security/dependency-audit-refresh-2026-06-29.md`.
      Result: blocker remains for `lxml` via Crawl4AI, including with the
      latest checked `crawl4ai 0.9.0` dependency resolution.
- [x] Dependency audit visible in GitHub CI.
      Evidence: `.github/workflows/ci.yml` `dependency-audit` job.
      Result: non-blocking while Crawl4AI/lxml CVE is unresolved.
- [ ] Crawl4AI/lxml risk decision approved.
      Evidence: `docs/security/crawl4ai-lxml-risk-decision-2026-06-28.md`,
      `docs/security/dependency-audit-refresh-2026-06-29.md`,
      `docs/security/crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md`.
      Public launch remains blocked until the dependency audit is clean or a
      formal exception is approved.
- [ ] Dependency audit clean and blocking in GitHub CI.
- [x] Secret scan run and recorded.
      Evidence: `docs/security/security-audit-2026-06-28.md`.
      Result: targeted tracked-file pattern scan found zero matches.
- [x] Entropy-aware secret scan run and recorded.
      Evidence: `docs/security/security-audit-2026-06-28.md`.
      Result: `detect-secrets` found 26 candidates across 18 tracked files;
      candidates are audited as false positives in `.secrets.baseline` and
      `docs/security/detect-secrets-audit-2026-06-28.md`.
- [x] Secret scan enforced in GitHub CI.
      Evidence: `.github/workflows/ci.yml` `secret-scan` job.
- [x] Hosted SSRF checks reviewed.
      Evidence: `docs/security/hosted-ssrf-review-2026-06-28.md`.
      Result: hosted admission now blocks unsafe schemes, credentials,
      localhost, unsafe IP literals, DNS-resolved unsafe IPs, and URL-like
      fields in high-level runs before crawler invocation or credit debit.
      Remaining public-launch work: deployment egress policy and crawler
      redirect/retry validation.
- [x] Hosted artifact authorization and path confinement reviewed.
      Evidence:
      `docs/security/hosted-artifact-authorization-review-2026-06-28.md`.
      Result: hosted read endpoints require Bearer auth, enforce persisted
      tenant ownership, hide other-tenant runs, allow only known artifact names,
      and confine records/download paths to the stored run output directory.
      Remaining public-launch work: object storage, signed URLs, retention, and
      production IAM review.
- [x] Terms/privacy placeholders created before public hosted beta.
      Evidence: `docs/legal/beta-terms-placeholder.md`,
      `docs/legal/beta-privacy-placeholder.md`, `/terms`, and `/privacy`.
      These are beta placeholders only; final lawyer-reviewed terms and privacy
      policy remain required before broad commercial launch.

## Beta Operations Gates

- [x] Private beta feedback templates.
- [x] Support contact/channel confirmed.
      Evidence: `docs/product/private-beta-onboarding-and-support.md`.
      Result: non-security beta support uses GitHub private-beta bug and
      feature issue templates; security reports stay private through
      `SECURITY.md`; beta response targets and support boundaries are documented.
- [x] Beta tester onboarding instructions verified.
      Evidence: `docs/product/private-beta-onboarding-and-support.md`.
      Result: onboarding now covers local package, Docker, hosted API, and
      skill usage paths; first-run smoke commands; artifact inspection; and
      feedback expectations without secrets.
- [x] Hosted API key generation flow verified.
      Evidence:
      `docs/security/hosted-key-generation-delivery-review-2026-06-28.md`.
      Result: operator CLI and Stripe webhook provisioning create usable hosted
      keys without storing or returning raw keys from hosted webhook responses.
- [x] Key delivery email flow verified with a non-production test recipient.
      Evidence:
      `docs/security/hosted-key-generation-delivery-review-2026-06-28.md`.
      Result: deterministic fake SMTP delivery sends the one-time key to
      `scout-beta-test@example.com`, and the delivered key authenticates.
      Live SMTP provider smoke remains pending before broader hosted launch.
- [ ] Stripe checkout and webhook tested in Stripe test mode.
      Evidence: `docs/product/stripe-test-mode-readiness-2026-06-29.md`.
      Result: deterministic checkout, webhook, payment provisioning, and key
      delivery tests pass, but real Stripe test-mode credentials/webhook secret
      are not configured in this checkout, so the live Stripe smoke remains open.

## Website And Documentation Gates

- [x] Launch website exists.
- [x] Launch website routes and browser render smoke verified locally.
      Evidence: `docs/product/website-route-render-verification-2026-06-29.md`.
      Result: `/`, `/quickstart`, `/pricing`, `/beta`, `/legal`, `/terms`,
      `/privacy`, `/third-party-notices`, `/styles.css`, and `/health` served
      from the Scout HTTP service on a local port; Playwright screenshots were
      captured for home, quickstart, pricing, and beta. This does not certify
      the legacy `/app` UI.
- [x] Website copy reviewed against competitor research.
      Evidence: `docs/product/website-copy-review-2026-06-28.md`.
      Result: current website follows the competitor-informed spine for private
      beta, leads with local-first evidence-grade acquisition, keeps hosted
      access metered, and avoids unsupported claims such as unlimited hosted
      scraping or guaranteed hard-site bypass.
- [x] Local install instructions tested on a fresh machine or clean container.
      Evidence: `docs/product/local-install-verification-2026-06-28.md`.
      Result: the private-beta docs now use the verified branch-qualified
      GitHub install command. Clean venv smoke confirms `scout-web==0.1.0`,
      `import scout`, `scout --help`, Playwright Chromium install, `scout
      serve`, `/health`, `/`, `/quickstart`, `/docs`, and authenticated
      `/scrape` against `https://example.com`.
- [x] Docker install instructions tested from docs only.
      Evidence: `docs/product/docker-install-verification-2026-06-28.md`.
      Result: documented compose build starts a healthy container, serves
      `/health`, `/`, `/styles.css`, `/quickstart`, `/docs`, and OpenAPI,
      runs authenticated `/scrape` with `X-API-Key: dev-key`, and confirms the
      `/data` volume is writable. A stale local uvicorn process on port `8421`
      was detected and cleared before the final smoke, so operators should keep
      the host port free or change the compose port mapping.
- [x] Hosted API quickstart tested with a newly generated API key.
      Evidence: `docs/product/hosted-api-quickstart-verification-2026-06-28.md`.
      Result: a fresh `hosted_beta_pass` key authenticated to `/v1/hosted/me`,
      ran `/v1/hosted/scrape` against `https://example.com`, returned provider
      `crawl4ai`, quality score `1.0`, and debited standard credits from
      `2000` to `1999`. Raw key was masked in evidence.
- [x] Skill usage docs tested from current package.
      Evidence: `docs/product/skill-usage-verification-2026-06-29.md`.
      Result: clean wheel install includes `scout/skill/scout.md` and
      `scout/skill/README.md`; installed CLI exposes `run`, `products`,
      `hosted-provision`, and `serve`; skill CLI examples for company,
      careers, and PRISM wrote artifact contracts with citations; installed
      HTTP `/run/company` example passed. Stale skill docs were corrected.

## Explicit Non-Goals For Current Release

- PyPI publish before license and package visibility decision.
- GHCR or Docker Hub publish before image visibility decision.
- Public hosted API without usage limits.
- Certified app UI.
- Guaranteed hard-site bypass.
