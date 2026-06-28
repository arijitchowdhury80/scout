# Local Install Verification

Date: 2026-06-28
Status: Current launch branch passes; public default-branch quickstart remains
open

## Scope

This check validates whether a beta user can install Scout locally from GitHub,
start the HTTP service, open the launch website/docs, and run one authenticated
scrape.

Test environment:

- macOS local clean virtual environments under `/tmp`
- Python 3.13
- no editable install
- no repository checkout on `PYTHONPATH`

## Result Summary

| Install path | Result | Notes |
|---|---|---|
| `pip install git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation` | Pass | Installs `scout-web==0.1.0`, exposes `scout`, serves website/docs, and runs `/scrape`. |
| `pip install git+https://github.com/arijitchowdhury80/scout.git` | Fail for current launch docs | Installs older/default-branch package `scout==0.1.0` from commit `9831b7f75d80f6ca0b0f842ed531d09b6b9e9726`; `scout-web` metadata is absent. |

The release checklist item "Local install instructions tested on a fresh
machine or clean container" remains open until the exact public/default-branch
quickstart command installs the current `scout-web` package.

## Passing Branch-Qualified Check

Commands:

```bash
rm -rf /tmp/scout-local-install-smoke /tmp/scout-local-install-runs
python3 -m venv /tmp/scout-local-install-smoke
/tmp/scout-local-install-smoke/bin/python -m pip install --upgrade pip
/tmp/scout-local-install-smoke/bin/python -m pip install \
  'git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation'
/tmp/scout-local-install-smoke/bin/python -m playwright install chromium
/tmp/scout-local-install-smoke/bin/python -c \
  "import scout; import scout.api.main; print('import-ok')"
/tmp/scout-local-install-smoke/bin/scout --help
```

Observed evidence:

- GitHub resolved `codex/scout-platform-foundation` to commit
  `04e2670ee4ea7dc1469fb047dd8d8d5c511bc6c4`.
- Wheel built as `scout_web-0.1.0-py3-none-any.whl`.
- Installed distribution version: `0.1.0`.
- `import scout` and `import scout.api.main` succeeded.
- `scout --help` showed the expected CLI commands, including `scrape`,
  `crawl`, `map`, `products`, `product-export`, `hosted-provision`, `serve`,
  and high-level `run`.
- Installed package metadata includes:
  - `website/index.html`
  - `website/quickstart.html`
  - `THIRD_PARTY_NOTICES.md`

## Passing Installed Server Check

Server command:

```bash
SCOUT_WORKDIR=/tmp/scout-local-install-runs \
SCOUT_API_KEY=dev-key \
/tmp/scout-local-install-smoke/bin/scout serve --host 127.0.0.1 --port 8439
```

Route checks:

```bash
curl http://127.0.0.1:8439/health
curl http://127.0.0.1:8439/
curl http://127.0.0.1:8439/quickstart
curl http://127.0.0.1:8439/docs
```

Observed evidence:

- `/health` returned HTTP 200 with `scout_version: 0.1.0`.
- `/` returned the launch homepage with "Turn messy web pages into citable,
  downstream-ready records" and "Run ledger".
- `/quickstart` returned "Scout Quickstart" and "Local install is the primary
  beta path."
- `/docs` returned Swagger UI.

Authenticated scrape check:

```bash
curl -sS -X POST http://127.0.0.1:8439/scrape \
  -H 'X-API-Key: dev-key' \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","formats":["markdown"],"timeout_ms":30000}'
```

Observed response facts:

- `success`: `true`
- `url`: `https://example.com`
- `provider`: `crawl4ai`
- `content_hash`: present
- `markdown`: present
- `duration_ms`: present

## Failing Public Default-Branch Check

Commands:

```bash
rm -rf /tmp/scout-local-install-default-smoke
python3 -m venv /tmp/scout-local-install-default-smoke
/tmp/scout-local-install-default-smoke/bin/python -m pip install --upgrade pip
/tmp/scout-local-install-default-smoke/bin/python -m pip install \
  'git+https://github.com/arijitchowdhury80/scout.git'
/tmp/scout-local-install-default-smoke/bin/python -c \
  "import scout; import importlib.metadata as m; print(m.version('scout-web'))"
```

Observed failure:

```text
importlib.metadata.PackageNotFoundError: No package metadata was found for scout-web
```

Additional evidence:

```text
scout @ git+https://github.com/arijitchowdhury80/scout.git@9831b7f75d80f6ca0b0f842ed531d09b6b9e9726
```

The exact public GitHub URL currently installs the repository default branch,
which has not caught up to the launch branch. The public quickstart should not
be called verified until one of these is true:

1. `codex/scout-platform-foundation` is merged into the repository default
   branch and the exact public quickstart command is re-tested, or
2. the private-beta quickstart is changed to a branch-qualified install command
   and that branch-specific instruction is intentionally accepted.

