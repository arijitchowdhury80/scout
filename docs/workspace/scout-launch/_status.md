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
  - clean virtualenv wheel smoke passed.

## Next

- Decide Scout license.
- Add release checklist.
- Build MCP server plan.
- Add hosted artifact dashboard and object-storage/signed-URL production plan.
- Decide whether direct Google Sheets API push belongs in Scout core or a
  separate credentialed adapter.
- Run full private-beta launch verification.
