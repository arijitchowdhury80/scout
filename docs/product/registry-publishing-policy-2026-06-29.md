# Registry Publishing Policy

Date: 2026-06-29

Status: **Policy recommended; approval required before registry publishing.**

## Summary

Scout should keep the current release workflow artifact-only for private beta:

- `v*` tags may build wheel/sdist artifacts.
- `v*` tags may create a GitHub Release with those artifacts attached.
- `v*` tags must **not** publish to PyPI.
- `v*` tags must **not** push Docker images to GHCR or Docker Hub.

Public registry publishing should wait until the license, dependency/security,
pricing/usage, and release smoke gates are closed.

## Current Automation

`.github/workflows/release.yml` currently:

1. builds the Python wheel and sdist,
2. installs the built wheel into a clean virtual environment,
3. runs `import scout`,
4. runs `scout --help`,
5. builds a Docker image locally,
6. starts the image and smokes `/health`, `/`, and `/styles.css`,
7. uploads `dist/*` as GitHub Actions artifacts,
8. creates a GitHub Release and attaches `dist/*`.

It does not run:

- `twine upload`,
- `pypa/gh-action-pypi-publish`,
- `docker login`,
- `docker push`,
- `docker/build-push-action` with push enabled,
- GHCR publish,
- Docker Hub publish.

That is the right posture for private beta.

## Recommended Publishing Phases

### Phase 0: Private beta, current state

Distribution:

- branch-qualified GitHub install,
- Docker build from source,
- GitHub Release artifacts only after a real `v*` tag smoke,
- hosted beta keys for approved testers.

No public registries.

Required before leaving Phase 0:

- license decision approved,
- final license expression added to `pyproject.toml`,
- `LICENSE` file added if open-source or source-available,
- dependency audit clean or formal security exception approved,
- Stripe test-mode checkout/webhook smoke completed if hosted payment remains in scope,
- hosted usage limits/pricing approved.

### Phase 1: PyPI first, if local/core is open source

Publish `scout-web` to PyPI only after:

- Scout license is Apache-2.0, MIT, or another approved license compatible with
  public package distribution,
- package name ownership is confirmed,
- wheel/sdist include required license and third-party notices,
- GitHub release artifact downloaded and smoke-tested locally,
- dependency audit is clean or exception is approved,
- README install instructions are updated from branch-qualified install to
  `pip install scout-web`.

Rationale:

- PyPI is the lowest-friction local install path.
- Local-first Scout should be easy to install before broad hosted scale is sold.

### Phase 2: GHCR Docker image

Publish Docker images to GHCR before Docker Hub.

Required before GHCR:

- image visibility decision approved,
- image labels include source, version, and license metadata,
- image digest is recorded in release notes,
- published image is pulled fresh and smoke-tested,
- volume, `SCOUT_WORKDIR`, `DB_PATH`, and API-key docs are current.

Rationale:

- GHCR ties image provenance to the GitHub repo.
- Docker Hub can follow if there is meaningful user demand.

### Phase 3: Docker Hub, optional

Publish to Docker Hub only if:

- beta users ask for it,
- namespace ownership is confirmed,
- the GHCR image process is already stable,
- support expectations for Docker users are documented.

Docker Hub is not needed for the first private beta.

## Release Workflow Guardrails

The release workflow must stay artifact-only until this policy is approved and
the prerequisite gates close.

Do not add these steps yet:

```yaml
- uses: pypa/gh-action-pypi-publish@...
- uses: docker/login-action@...
- uses: docker/build-push-action@...
  with:
    push: true
```

When publishing is approved, add separate jobs with:

- explicit environment protection,
- manual approval if available,
- least-privilege publishing tokens,
- version/tag consistency checks,
- post-publish smoke tests from the public registry.

## Recommended Decision

Approve this policy:

- **Private beta:** GitHub Release artifacts only, no public registries.
- **Public developer preview:** PyPI first if license/security gates close.
- **Container publishing:** GHCR before Docker Hub.
- **Hosted API:** sold separately through keys/quotas, not through Docker/PyPI.

## Gates This Supports

This policy supports but does not close:

- `Registry publishing policy approved for PyPI, GHCR, Docker Hub, or other registries`
- `GitHub release artifact workflow run against a real v* tag`
- `Release artifact downloaded from GitHub Release and smoke-tested locally`
- `Docker image publishing policy approved`
- `Published Docker image smoke-tested if GHCR, Docker Hub, or another registry is used`

## Decision Needed

- [ ] Approve artifact-only private beta release tags.
- [ ] Approve PyPI as first public registry after license/security gates close.
- [ ] Approve GHCR as first container registry after image policy gates close.
- [ ] Defer Docker Hub until there is user demand.
