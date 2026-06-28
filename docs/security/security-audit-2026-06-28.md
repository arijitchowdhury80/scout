# Scout Security Audit

Date: 2026-06-28
Status: Scan evidence recorded; dependency CVE remains open

No secret values are reproduced in this report.

## Scope

This audit covers the current launch branch package state:

- local Python package install from the current checkout,
- tracked source files in git,
- release readiness gates for private beta.

It does not certify hosted production readiness, Stripe production readiness, or
public registry publishing.

## Dependency CVE Scan

Command:

```bash
rm -rf /tmp/scout-security-audit-venv
python3 -m venv /tmp/scout-security-audit-venv
/tmp/scout-security-audit-venv/bin/python -m pip install --upgrade pip
/tmp/scout-security-audit-venv/bin/python -m pip install .
/tmp/scout-security-audit-venv/bin/python -m pip install pip-audit
/tmp/scout-security-audit-venv/bin/python -m pip_audit --local
```

Equivalent module form: `python3 -m pip_audit --local` inside the clean audit
environment.

Result:

- `pip-audit` found 2 known vulnerability rows in 1 package.
- Package: `lxml`
- Installed version: `5.4.0`
- Vulnerability: `PYSEC-2026-87`
- Fixed version: `6.1.0`
- Source of dependency: `Crawl4AI` currently requires `lxml~=5.3`.
- Attempting to add `lxml>=6.1.0` directly to Scout caused pip resolution to
  fail because the current Crawl4AI releases in the tested range require
  `lxml~=5.3`.
- `pip-audit` also skipped `scout-web` because the local package is not
  published on PyPI.

Launch impact:

- This is a public-launch blocker.
- Private beta can continue only with this risk documented and with no claim
  that the dependency audit is clean.

Next action:

- Track Crawl4AI releases for an `lxml>=6.1.0` compatible version.
- If no upstream fix is available before public launch, evaluate whether to:
  - vendor/patch the affected dependency path,
  - pin a fixed Crawl4AI fork,
  - remove the dependency path that requires vulnerable `lxml`,
  - delay public release.

## Secret Scan

Command:

```bash
pattern='(sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|AIza[0-9A-Za-z_-]{35}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----|stripe_(live|test)_[A-Za-z0-9_]+)'
git grep -n -I -E "$pattern" -- $(git ls-files) >/tmp/scout-secret-scan.txt
```

Result:

- High-risk tracked-file token/private-key pattern matches: `0`.
- `.env` is present locally but is not tracked by git in this checkout.

Limitations:

- This was a targeted tracked-file pattern scan, not a full entropy-based
  secret scanner.
- It does not inspect untracked local files, ignored run artifacts, shell
  history, GitHub Actions secrets, Stripe dashboard settings, or hosted
  infrastructure variables.

## Remaining Risks

- Dependency CVE remains unresolved because of Crawl4AI's current `lxml~=5.3`
  constraint.
- Hosted Scout still needs a production security review for:
  - SSRF controls,
  - tenant isolation,
  - API key handling,
  - artifact authorization,
  - rate limits and abuse limits,
  - Stripe webhook secret handling.
- A full secret scan using an entropy-aware tool should run before public
  release.
- Terms, privacy, and acceptable-use language are still required before a
  public hosted beta.

## Verdict

Security evidence has been recorded, but Scout is not public-launch-ready.
