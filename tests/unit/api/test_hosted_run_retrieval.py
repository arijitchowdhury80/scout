"""Tests for hosted run artifact retrieval endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from scout.api.config import settings
from scout.api.deps import get_hosted_account_service
from scout.api.main import app
from scout.api.run_store import remember_run
from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.hosted import HostedPlan
from scout.core.platform.types import ArtifactFiles, RunManifest


def _account_service_with_two_keys() -> tuple[HostedAccountService, str, str]:
    service = HostedAccountService(InMemoryHostedAccountStore())
    first = service.provision_account(
        email="first@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    second = service.provision_account(
        email="second@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    return service, first.raw_api_key, second.raw_api_key


def _create_hosted_company_run(
    client: TestClient,
    raw_key: str,
    tmp_path: Path,
    monkeypatch,
) -> str:
    monkeypatch.setattr(settings, "scout_workdir", str(tmp_path / "hosted-runs"))
    resp = client.post(
        "/v1/hosted/run/company",
        json={"query": "Adobe", "mode": "saved", "max_records": 10},
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert resp.status_code == 200
    return resp.json()["run"]["manifest"]["run_id"]


async def _remember_malicious_hosted_run(
    *,
    run_id: str,
    tenant_id: str,
    output_dir: Path,
    records_json: Path,
) -> None:
    await remember_run(
        RunManifest(
            run_id=run_id,
            use_case="company",
            query="malicious",
            started_at="2026-06-28T00:00:00Z",
            finished_at="2026-06-28T00:00:01Z",
            output_dir=str(output_dir),
            total_records=1,
            artifacts=ArtifactFiles(records_json=str(records_json)),
        ),
        tenant_id=tenant_id,
        key_id="key_test",
    )


def test_hosted_run_summary_records_and_artifacts_are_retrievable_for_owner(
    tmp_path,
    monkeypatch,
) -> None:
    account_service, raw_key, _other_key = _account_service_with_two_keys()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        run_id = _create_hosted_company_run(client, raw_key, tmp_path, monkeypatch)
        summary = client.get(
            f"/v1/hosted/runs/{run_id}",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        records = client.get(
            f"/v1/hosted/runs/{run_id}/records",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        artifacts = client.get(
            f"/v1/hosted/runs/{run_id}/artifacts",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        artifact_download = client.get(
            f"/v1/hosted/runs/{run_id}/artifacts/records_json/download",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert summary.status_code == 200
    assert summary.json()["run_id"] == run_id
    assert summary.json()["tenant_id"].startswith("tenant_")
    assert summary.json()["key_id"].startswith("key_")
    assert summary.json()["output_dir"].startswith(str(tmp_path / "hosted-runs"))
    assert records.status_code == 200
    assert records.json()["total"] > 0
    assert records.json()["records"][0]["citations"]
    assert artifacts.status_code == 200
    assert artifacts.json()["artifacts"]["records_json"].endswith("records.json")
    assert artifacts.json()["download_urls"]["records_json"].endswith(
        f"/v1/hosted/runs/{run_id}/artifacts/records_json/download"
    )
    assert artifact_download.status_code == 200
    assert artifact_download.json()[0]["citations"]
    assert raw_key not in summary.text
    assert raw_key not in records.text
    assert raw_key not in artifacts.text
    assert raw_key not in artifact_download.text


async def test_hosted_records_endpoint_rejects_records_json_outside_output_dir(
    tmp_path,
) -> None:
    account_service, raw_key, _other_key = _account_service_with_two_keys()
    tenant = account_service.authenticate_key(raw_key, required_scope="runs:create")
    output_dir = tmp_path / "hosted-runs" / "run-owned"
    output_dir.mkdir(parents=True)
    outside_records = tmp_path / "outside-records.json"
    outside_records.write_text('[{"objectID":"leaked"}]', encoding="utf-8")
    run_id = "run_malicious_records_path"
    await _remember_malicious_hosted_run(
        run_id=run_id,
        tenant_id=tenant.tenant_id,
        output_dir=output_dir,
        records_json=outside_records,
    )
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        records = client.get(
            f"/v1/hosted/runs/{run_id}/records",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        download = client.get(
            f"/v1/hosted/runs/{run_id}/artifacts/records_json/download",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert records.status_code == 404
    assert records.json()["detail"] == "Artifact not found: records_json"
    assert "leaked" not in records.text
    assert download.status_code == 404
    assert download.json()["detail"] == "Artifact not found: records_json"
    assert "leaked" not in download.text


def test_hosted_run_list_returns_only_authenticated_tenant_runs(tmp_path, monkeypatch) -> None:
    account_service, owner_key, other_key = _account_service_with_two_keys()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        owner_run_id = _create_hosted_company_run(client, owner_key, tmp_path, monkeypatch)
        other_run_id = _create_hosted_company_run(client, other_key, tmp_path, monkeypatch)
        resp = client.get(
            "/v1/hosted/runs",
            headers={"Authorization": f"Bearer {owner_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    payload = resp.json()
    run_ids = {run["run_id"] for run in payload["runs"]}
    assert owner_run_id in run_ids
    assert other_run_id not in run_ids
    assert payload["total"] == len(payload["runs"])
    owner_item = next(run for run in payload["runs"] if run["run_id"] == owner_run_id)
    assert owner_item["summary_url"] == f"/v1/hosted/runs/{owner_run_id}"
    assert owner_item["records_url"] == f"/v1/hosted/runs/{owner_run_id}/records"
    assert owner_item["artifacts_url"] == f"/v1/hosted/runs/{owner_run_id}/artifacts"
    assert "output_dir" not in owner_item
    assert owner_key not in resp.text
    assert other_key not in resp.text


def test_hosted_run_retrieval_requires_bearer_token() -> None:
    account_service, _raw_key, _other_key = _account_service_with_two_keys()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.get("/v1/hosted/runs/run_missing")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing Bearer token"


def test_hosted_run_retrieval_hides_runs_from_other_tenants(tmp_path, monkeypatch) -> None:
    account_service, owner_key, other_key = _account_service_with_two_keys()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        run_id = _create_hosted_company_run(client, owner_key, tmp_path, monkeypatch)
        resp = client.get(
            f"/v1/hosted/runs/{run_id}",
            headers={"Authorization": f"Bearer {other_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == f"Run not found: {run_id}"


def test_hosted_artifact_download_hides_runs_from_other_tenants(tmp_path, monkeypatch) -> None:
    account_service, owner_key, other_key = _account_service_with_two_keys()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        run_id = _create_hosted_company_run(client, owner_key, tmp_path, monkeypatch)
        resp = client.get(
            f"/v1/hosted/runs/{run_id}/artifacts/records_json/download",
            headers={"Authorization": f"Bearer {other_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == f"Run not found: {run_id}"


def test_hosted_artifact_download_rejects_unknown_artifact(tmp_path, monkeypatch) -> None:
    account_service, raw_key, _other_key = _account_service_with_two_keys()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        run_id = _create_hosted_company_run(client, raw_key, tmp_path, monkeypatch)
        resp = client.get(
            f"/v1/hosted/runs/{run_id}/artifacts/secrets/download",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Artifact not found: secrets"
