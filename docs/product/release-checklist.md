# Scout Release Checklist

Date: 2026-06-28
Status: Private beta release gate

This checklist decides whether Scout is ready for a public or wider private
beta release. Public launch is blocked until every required gate is checked or a
documented exception exists.

## Release Scope

Current intended release surfaces:

- local Python package: `scout-web`, installed command `scout`,
- Docker HTTP service,
- hosted API for limited private beta users,
- Claude/Codex skill documentation.

The legacy app UI is not a launch surface until it is rebuilt and certified.

## Blocking Decisions

- [ ] License decision recorded.
- [ ] Final license expression added to `pyproject.toml`.
- [ ] `LICENSE` file added if Scout is open source or source-available.
- [ ] Public launch pricing and hosted usage limits approved.
- [ ] Hosted economics and usage limits documented against the `$22` beta pass
      and any subscription alternative.
- [ ] Registry publishing policy approved for PyPI, GHCR, Docker Hub, or other
      registries.

No public registry publish should happen until these decisions are closed.

## Package And Artifact Gates

- [x] Package metadata added for `scout-web`.
- [x] Clean wheel install smoke.
- [x] Installed `import scout` smoke.
- [x] Installed `scout --help` smoke.
- [x] GitHub release artifact workflow added.
- [ ] GitHub release artifact workflow run against a real `v*` tag.
- [ ] Release artifact downloaded from GitHub Release and smoke-tested locally.

## Docker Gates

- [x] Docker image builds.
- [x] Docker runtime smoke for `/health`.
- [x] Docker runtime smoke for `/`.
- [x] Docker runtime smoke for `/styles.css`.
- [ ] Docker image publishing policy approved.
- [ ] Published Docker image smoke-tested if GHCR, Docker Hub, or another
      registry is used.

## Security And Legal Gates

- [x] Third-party notices.
- [x] Security policy.
- [x] Dependency CVE scan run and recorded.
      Evidence: `docs/security/security-audit-2026-06-28.md`.
      Result: blocker remains for `lxml` via Crawl4AI.
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
- [ ] Hosted SSRF checks reviewed.
- [ ] Hosted artifact authorization and path confinement reviewed.
- [ ] Terms/privacy placeholders created before public hosted beta.

## Beta Operations Gates

- [x] Private beta feedback templates.
- [ ] Support contact/channel confirmed.
- [ ] Beta tester onboarding instructions verified.
- [ ] Hosted API key generation flow verified.
- [ ] Key delivery email flow verified with a non-production test recipient.
- [ ] Stripe checkout and webhook tested in Stripe test mode.

## Website And Documentation Gates

- [x] Launch website exists.
- [ ] Website copy reviewed against competitor research.
- [ ] Local install instructions tested on a fresh machine or clean container.
- [ ] Docker install instructions tested from docs only.
- [ ] Hosted API quickstart tested with a newly generated API key.
- [ ] Skill usage docs tested from current package.

## Explicit Non-Goals For Current Release

- PyPI publish before license and package visibility decision.
- GHCR or Docker Hub publish before image visibility decision.
- Public hosted API without usage limits.
- Certified app UI.
- Guaranteed hard-site bypass.
