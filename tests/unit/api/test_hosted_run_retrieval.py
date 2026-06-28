"""Tests for hosted run artifact retrieval endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from scout.api.config import settings
from scout.api.deps import get_hosted_account_service
from scout.api.main import app
from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.hosted import HostedPlan


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
    assert raw_key not in summary.text
    assert raw_key not in records.text
    assert raw_key not in artifacts.text


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
