# Scout Private Beta Security Policy

Scout is not public-production-ready yet. Treat this repository and any hosted
Scout endpoint as private beta software until the release checklist says
otherwise.

## Supported Versions

| Surface | Status | Security support |
| --- | --- | --- |
| Local Scout package | Private beta | Best-effort fixes on current branch |
| Docker Scout service | Private beta | Best-effort fixes on current branch |
| Hosted Scout | Private beta / limited users | Critical fixes prioritized before new features |
| Legacy app UI experiments | Not a launch surface | No security support unless reactivated |

## Reporting A Vulnerability

Do not open a public GitHub issue for security reports.

For now, report security issues privately to the project maintainer. Include:

- affected surface: Local Scout, Docker, Hosted Scout, CLI, API, or skill,
- Scout version, commit, or Docker tag,
- reproduction steps,
- relevant run ID or artifact path when safe to share,
- whether any secrets, API key values, cookies, private pages, or customer data
  were exposed.

The maintainer should acknowledge critical reports within 72 hours during the
private beta. Public disclosure timing will be coordinated case by case.

## Security Review Checklist

Before a public release or hosted beta expansion, Scout must verify:

- API key hashing, lookup, revocation, and tenant scoping,
- hosted run ownership checks for run summaries, records, sources, and artifact
  downloads,
- SSRF protections for all user-supplied URLs,
- artifact path confinement and blocked path traversal,
- secret handling for `.env`, hosted API keys, Stripe keys, Algolia keys, and
  user-provided integration credentials,
- no secrets in logs, validation output, source pages, records, or downloaded
  artifacts,
- crawler/browser timeouts and resource limits,
- hosted usage limits and admission checks,
- dependency CVE scan,
- third-party license review,
- security report process and response owner.

## Hosted Scout Boundaries

Hosted Scout is a stronger security responsibility than Local Scout. Hosted
Scout must enforce tenant isolation, API key authorization, usage limits, URL
safety checks, artifact confinement, and non-leaking errors before accepting
untrusted public users.

## Local Scout Boundaries

Local Scout runs on the user's machine and writes artifacts locally. Users are
responsible for where they point Scout, where they store artifacts, and which
credentials they provide. Scout should still avoid leaking secrets into records,
logs, or source evidence.

