# Hosted Artifact Authorization Review

Date: 2026-06-28
Status: Current hosted API artifact authorization and local path confinement
implemented and tested; object-storage architecture still required before broad
hosted launch

## Scope

This review covers the current hosted artifact read path:

- `GET /v1/hosted/runs`
- `GET /v1/hosted/runs/{run_id}`
- `GET /v1/hosted/runs/{run_id}/records`
- `GET /v1/hosted/runs/{run_id}/artifacts`
- `GET /v1/hosted/runs/{run_id}/artifacts/{artifact_name}/download`

## Implemented Controls

- Every hosted run read endpoint requires a Bearer hosted API key.
- Run retrieval is authorized by persisted `tenant_id` ownership, not by local
  filesystem paths or caller-provided output directories.
- Listing endpoints return only runs owned by the authenticated tenant.
- Other tenants receive `404` for run summaries and artifact downloads so run
  existence is not disclosed across tenants.
- Artifact downloads are restricted to a known allowlist of artifact names:
  `manifest`, `records_json`, `records_jsonl`, `source_pages_json`,
  `blocked_pages_json`, `validation_json`, and `report_md`.
- Artifact file paths are resolved and must remain inside the persisted run
  `output_dir`.
- Symlink/path traversal escapes are blocked by resolving the final path before
  `relative_to(output_dir)`.
- `/records` now uses the same hosted artifact confinement helper as direct
  artifact downloads.
- Raw hosted API keys are not echoed in run, records, artifacts, or artifact
  download responses.

## Regression Fixed In This Checkpoint

Before this review, artifact downloads were path-confined, but the hosted
`/records` endpoint read `records_json` through a generic helper. A malicious or
corrupt stored run could point `records_json` outside the run output directory
and `/records` would return it. The regression test now confirms `/records` and
`/artifacts/records_json/download` both return `404` for records paths outside
the run directory.

## Current Limits

- Current hosted beta uses local filesystem artifacts. Broad hosted launch
  should move artifacts to object storage with tenant-scoped object keys,
  short-lived signed URLs, retention policy, and storage-level IAM boundaries.
- `/v1/hosted/runs/{run_id}/artifacts` still returns artifact path metadata to
  the authenticated owner. This is acceptable for controlled private beta but
  should be replaced with opaque artifact IDs or signed download links for
  production SaaS.
- Artifact deletion and retention enforcement are not yet automated.

## Evidence

Test coverage:

```bash
python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py -q
```

Expected result from the implementation checkpoint:

```text
7 passed
```

Broader hosted/security verification:

```bash
python3 -m pytest \
  tests/unit/api/test_hosted_scrape.py \
  tests/unit/api/test_hosted_crawl.py \
  tests/unit/api/test_hosted_products.py \
  tests/unit/api/test_hosted_run.py \
  tests/unit/api/test_hosted_run_retrieval.py \
  tests/unit/core/platform/test_url_safety.py \
  tests/unit/test_security_audit_docs.py -q
```

## Launch Impact

The release checklist item "Hosted artifact authorization and path confinement
reviewed" is satisfied for the current local-filesystem hosted beta API. Public
hosted launch still requires object storage, retention/deletion automation, and
production IAM review.

