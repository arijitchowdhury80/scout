# Dependency Audit Refresh

Date: 2026-06-29

Status: **Audit still failing; public launch remains blocked.**

## Summary

A fresh clean-environment dependency audit was run after checking current package availability. The blocker remains:

- `crawl4ai` latest available version: `0.9.0`
- `lxml` latest available version: `6.1.1`
- Scout fresh install resolves: `crawl4ai 0.9.0` and `lxml 5.4.0`
- `pip-audit` reports `PYSEC-2026-87` against `lxml 5.4.0`
- forcing `lxml>=6.1.0` still conflicts with `crawl4ai==0.9.0`

This means the dependency audit cannot yet be made clean and blocking in CI without changing Scout's Crawl4AI strategy.

## Commands Run

Clean audit:

```bash
rm -rf /tmp/scout-dependency-audit-2026-06-29
python3 -m venv /tmp/scout-dependency-audit-2026-06-29
/tmp/scout-dependency-audit-2026-06-29/bin/python -m pip install --upgrade pip
/tmp/scout-dependency-audit-2026-06-29/bin/python -m pip install .
/tmp/scout-dependency-audit-2026-06-29/bin/python -m pip install pip-audit
/tmp/scout-dependency-audit-2026-06-29/bin/python -m pip_audit --local
```

Result:

```text
Found 2 known vulnerabilities in 1 package
Name Version ID            Fix Versions
---- ------- ------------- ------------
lxml 5.4.0   PYSEC-2026-87 6.1.0
lxml 5.4.0   PYSEC-2026-87 6.1.0
```

Package availability check:

```bash
python3 -m pip index versions crawl4ai
python3 -m pip index versions lxml
```

Result:

```text
crawl4ai (0.9.0)
  INSTALLED: 0.7.7
  LATEST:    0.9.0

lxml (6.1.1)
  INSTALLED: 5.4.0
  LATEST:    6.1.1
```

Latest dependency resolution probe:

```bash
rm -rf /tmp/scout-latest-deps-probe
python3 -m venv /tmp/scout-latest-deps-probe
/tmp/scout-latest-deps-probe/bin/python -m pip install --upgrade pip
/tmp/scout-latest-deps-probe/bin/python -m pip install '.[dev]' --upgrade --upgrade-strategy eager
/tmp/scout-latest-deps-probe/bin/python -m pip show crawl4ai lxml
```

Result:

```text
Name: Crawl4AI
Version: 0.9.0

Name: lxml
Version: 5.4.0
Required-by: Crawl4AI
```

Forced fixed-lxml probe:

```bash
rm -rf /tmp/scout-crawl4ai-09-probe
python3 -m venv /tmp/scout-crawl4ai-09-probe
/tmp/scout-crawl4ai-09-probe/bin/python -m pip install --upgrade pip
/tmp/scout-crawl4ai-09-probe/bin/python -m pip install 'crawl4ai==0.9.0' 'lxml>=6.1.0'
```

Result:

```text
ERROR: Cannot install crawl4ai==0.9.0 and lxml>=6.1.0 because these package versions have conflicting dependencies.
ERROR: ResolutionImpossible
```

## CI Decision

`.github/workflows/ci.yml` already includes a `dependency-audit` job. It remains `continue-on-error: true` because the current dependency tree is known to fail.

Do **not** flip this job to blocking until one of these is true:

1. Crawl4AI releases a version compatible with `lxml>=6.1.0`.
2. Scout replaces, forks, or patches the Crawl4AI dependency path.
3. A formal public-launch security exception is approved with compensating controls.

## Release Decision

The release checklist remains correct:

- `Dependency CVE scan run and recorded` is complete.
- `Dependency audit visible in GitHub CI` is complete.
- `Crawl4AI/lxml risk decision approved` is still open.
- `Dependency audit clean and blocking in GitHub CI` is still open.

Scout is not public-launch-ready while this dependency audit fails.
