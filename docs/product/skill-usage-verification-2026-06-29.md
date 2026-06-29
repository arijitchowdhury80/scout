# Skill Usage Verification

Date: 2026-06-29

Status: passed from the current built package.

## Scope

This verification tested the Claude/Codex skill wrapper from a freshly built
Scout wheel, not only from the source tree.

The smoke covered:

- wheel packaging includes `scout/skill/scout.md` and `scout/skill/README.md`,
- installed `scout` command exposes the documented `run`, `products`,
  `hosted-provision`, and `serve` commands,
- skill CLI examples create standard run artifacts,
- skill HTTP example works against the installed package,
- record/source/citation coverage exists for the smoke runs.

## Package Smoke

Build command:

```bash
python3 -m build --wheel --outdir /tmp/scout-skill-wheel-smoke
```

Install command:

```bash
python3 -m venv /tmp/scout-skill-docs-q27BG2/.venv
/tmp/scout-skill-docs-q27BG2/.venv/bin/pip install \
  /tmp/scout-skill-wheel-smoke/scout_web-0.1.0-py3-none-any.whl
```

Package checks:

```text
distribution: 0.1.0
skill_exists: True
readme_exists: True
skill_has_company_example: True
skill_has_artifact_contract: True
installed CLI contains: run, products, hosted-provision, serve
```

## CLI Examples Tested

```bash
scout run company --query Adobe --mode auto --output-dir "$RUN_ROOT/adobe-company"
scout run careers --query Algolia --mode auto --output-dir "$RUN_ROOT/algolia-careers"
scout run prism --query Nike --mode auto --workdir "$RUN_ROOT/workdir"
```

Results:

| Example | Status | Records | Sources | Citations | Artifact contract |
|---|---:|---:|---:|---:|---|
| company / Adobe | passed | 1 | 1 | 1 | present |
| careers / Algolia | passed | 1 | 1 | 1 | present |
| PRISM / Nike | passed | 6 | 5 | 5 | present |

Each run wrote:

```text
manifest.json
records.json
records.jsonl
source_pages.json
blocked_pages.json
validation.json
extraction_report.md
```

## HTTP Example Tested

Server command from installed package:

```bash
SCOUT_WORKDIR="$TMP_SKILL/http-runs" \
DB_PATH="$TMP_SKILL/http-scout.db" \
SCOUT_API_KEY=dev-key \
scout serve --host 127.0.0.1 --port 18425
```

Request:

```bash
curl -fsS -X POST http://127.0.0.1:18425/run/company \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{"query":"Adobe","mode":"auto","output_dir":"$TMP_SKILL/http-adobe-company"}'
```

Result:

```text
success: true
use_case: company
run_id: run_bf784776af45
records: 1
sources: 1
citations: 1
artifacts_exist: true
```

## Findings Fixed

- `scout/skill/README.md` used an unqualified GitHub install command. It now
  uses the verified private-beta branch install command.
- `scout/skill/scout.md` said only `/` and `/health` were public. It now
  distinguishes public launch/docs routes from protected local API routes.
- `scout/skill/scout.md` presented `/app` too strongly. It now says the legacy
  app UI is not a launch-certified surface and should be treated as a local
  service/status surface unless the user explicitly asks for it.

## Notes

- The workstation had a stale global `scout` console script outside the clean
  venv. The clean wheel install provided a working `scout` command, so the stale
  global script is an environment residue issue, not a current package failure.
- The CLI smoke used live public pages for Adobe, Algolia, and Nike. Future
  release certification should keep deterministic fixture coverage for offline
  tests and reserve live network checks for launch gates like this one.

