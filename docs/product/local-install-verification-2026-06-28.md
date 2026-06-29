# Local Install Verification

Date: 2026-06-28
Status: Private-beta branch install path verified

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
| `pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation"` | Pass | Installs `scout-web==0.1.0`, exposes `scout`, serves website/docs, and runs `/scrape`. |
| `pip install git+https://github.com/arijitchowdhury80/scout.git` | Not accepted for beta docs | Installs older/default-branch package `scout==0.1.0` from commit `9831b7f75d80f6ca0b0f842ed531d09b6b9e9726`; `scout-web` metadata is absent. |

The beta quickstart now intentionally uses the branch-qualified command. The
release checklist item "Local install instructions tested on a fresh machine or
clean container" is satisfied for the current private-beta branch path. Public
PyPI/default-branch install remains a separate launch/publishing gate.

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

## Re-Run After Quickstart Correction

The branch-qualified command was re-run in a fresh virtual environment after the
quickstart docs were changed to use the verified private-beta branch:

```bash
rm -rf /tmp/scout-beta-doc-install-smoke /tmp/scout-beta-doc-runs
python3 -m venv /tmp/scout-beta-doc-install-smoke
/tmp/scout-beta-doc-install-smoke/bin/python -m pip install --upgrade pip
/tmp/scout-beta-doc-install-smoke/bin/python -m pip install \
  'git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation'
/tmp/scout-beta-doc-install-smoke/bin/python -m playwright install chromium
/tmp/scout-beta-doc-install-smoke/bin/python -c \
  "import scout; import scout.api.main; import importlib.metadata as m; print('import-ok'); print(m.version('scout-web'))"
/tmp/scout-beta-doc-install-smoke/bin/scout --help
```

Observed evidence:

- `import-ok`
- installed distribution version `0.1.0`
- `scout --help` listed the expected commands.

## Local Editable Install Remediation

Date: 2026-06-29

During launch-readiness verification on the development machine, the global
`scout` console command initially failed because an old editable install pointed
to `/Users/arijitchowdhury/AI-Development/Scout`, a sparse leftover directory,
instead of the current repository checkout:
`/Users/arijitchowdhury/Dropbox/AI-Development/Scout`.

Observed stale state:

```text
Name: scout
Version: 0.1.0
Editable project location: /Users/arijitchowdhury/AI-Development/Scout
ModuleNotFoundError: No module named 'scout'
```

Remediation command:

```bash
python3 -m pip uninstall -y scout scout-web
python3 -m pip install -e '.[dev]'
```

Post-remediation evidence:

```text
Name: scout-web
Version: 0.1.0
Editable project location: /Users/arijitchowdhury/Dropbox/AI-Development/Scout
```

Verification commands:

```bash
python3 - <<'PY'
import scout
import scout.api.main
import importlib.metadata as m
print("module", scout.__file__)
print("dist", m.version("scout-web"))
PY

scout --help
scout launch-readiness
```

Observed evidence:

- `import scout` and `import scout.api.main` succeeded from the current checkout.
- `importlib.metadata.version("scout-web")` returned `0.1.0`.
- `scout --help` listed the expected CLI commands.
- `scout launch-readiness` returned `Private beta: ready_with_limits` and
  `Public launch: blocked`.

Operational note: if a beta tester previously installed an older Scout checkout
editable, they should uninstall both possible distribution names and reinstall
from the current branch-qualified command. Fresh virtual environments remain the
recommended verification path.

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

## Rejected Public Default-Branch Check

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

The exact unqualified GitHub URL currently installs the repository default
branch, which has not caught up to the launch branch. It should not be used in
private-beta docs until one of these is true:

1. `codex/scout-platform-foundation` is merged into the repository default
   branch and the exact public quickstart command is re-tested, or
2. the private-beta quickstart remains branch-qualified and that
   branch-specific instruction is intentionally accepted.

For the current beta, option 2 is the accepted path.
