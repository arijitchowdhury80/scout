# Scout Launch Workspace Status

Date: 2026-06-27
Updated: 2026-06-28
Status: In progress

## Purpose

This workspace captures the product strategy, website structure, and launch
readiness work needed to turn Scout from a working tool into a testable product.

## Completed

- Product strategy baseline drafted.
- Website design-thinking baseline drafted.
- Feature list documented.
- Differentiation documented.
- Private beta launch plan documented.
- Distribution package plan documented.
- Third-party notices added.
- Legal readiness checklist added.
- Competitor website/pricing research refreshed.
- Static Scout launch website refreshed around evidence-grade records.
- Hosted run ownership persistence implemented.
- Hosted run listing implemented for private-beta hosted API keys.
- Hosted owner-scoped artifact download URLs implemented for private-beta
  filesystem-backed runs.
- Product export adapters generalized beyond Algolia:
  - JSON,
  - JSONL,
  - CSV,
  - SQLite,
  - Google Sheets import bundle.
- SQLite product export table names are validated before SQL interpolation.
- Local package metadata aligned for launch distribution:
  - distribution name: `scout-web`,
  - installed CLI command: `scout`,
  - wheel explicitly ships the `scout` module,
  - wheel includes launch website assets,
  - clean virtualenv wheel smoke passed.
- Docker distribution smoke passed for built image:
  - `/health`,
  - `/`,
  - `/styles.css`.
- GitHub CI now includes:
  - package build,
  - clean wheel install/import/CLI smoke,
  - Docker build,
  - Docker `/health`, `/`, and `/styles.css` route smoke.
- Tag-driven GitHub release workflow added:
  - builds wheel and sdist,
  - installs the built wheel in a clean virtualenv,
  - smokes `import scout` and `scout --help`,
  - builds and smokes Docker,
  - uploads `dist/*` as workflow artifacts,
  - attaches `dist/*` to a GitHub Release.
- Release governance added:
  - private beta `SECURITY.md`,
  - GitHub private beta bug template,
  - GitHub private beta feature request template,
  - release checklist with explicit public-launch and registry-publish gates.
- Security scan evidence recorded:
  - dependency audit found `lxml 5.4.0` / `PYSEC-2026-87` through Crawl4AI's
    current `lxml~=5.3` constraint,
  - targeted tracked-file secret pattern scan found zero matches,
  - entropy-aware `detect-secrets` scan found 26 candidates across 18 tracked
    files that still need audit/allowlisting before public launch,
  - public launch remains blocked until the dependency CVE is resolved or an
    explicit risk decision is made.

## Next

- Decide Scout license.
- Run the tag workflow against a real `v*` release tag.
- Decide if/when to publish to PyPI, GHCR, Docker Hub, or another registry.
- Resolve or explicitly risk-accept the Crawl4AI/lxml dependency CVE before
  public launch.
- Audit or remove/allowlist `detect-secrets` candidate findings before public
  launch.
- Verify Stripe test-mode checkout/webhook before hosted beta.
- Verify hosted key delivery with a non-production test recipient.
- Build MCP server plan.
- Add hosted artifact dashboard and object-storage/signed-URL production plan.
- Decide whether direct Google Sheets API push belongs in Scout core or a
  separate credentialed adapter.
- Run full private-beta launch verification.
