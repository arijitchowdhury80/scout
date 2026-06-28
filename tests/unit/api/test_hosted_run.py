"""Tests for hosted bearer-auth high-level run endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from scout.api.config import settings
from scout.api.deps import get_hosted_account_service, get_hosted_rate_limiter
from scout.api.main import app
from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.hosted import HostedPlan, plan_limits
from scout.core.platform.hosted_rate_limit import HostedRateLimitConfig, HostedRateLimiter


def _account_service_with_key() -> tuple[HostedAccountService, str, str]:
    service = HostedAccountService(InMemoryHostedAccountStore())
    provisioned = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    return service, provisioned.raw_api_key, provisioned.tenant.tenant_id


def test_hosted_run_requires_bearer_token() -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/run/company",
            json={"query": "Adobe", "mode": "saved"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing Bearer token"


def test_hosted_run_derives_server_output_dir_and_debits_returned_records(
    tmp_path, monkeypatch
) -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    monkeypatch.setattr(settings, "scout_workdir", str(tmp_path / "hosted-runs"))
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/run/company",
            json={
                "query": "Adobe",
                "mode": "saved",
                "output_dir": "/tmp/user-controlled-output",
                "max_records": 10,
            },
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["hosted"]["tenant_id"] == tenant_id
    assert data["hosted"]["credits_charged"] == data["run"]["total_records"]
    assert data["hosted"]["credit_type"] == "standard"
    assert data["run"]["output_dir"].startswith(str(tmp_path / "hosted-runs"))
    assert data["run"]["output_dir"] != "/tmp/user-controlled-output"
    assert raw_key not in resp.text
    assert balance.standard_credits_remaining == (
        limits.standard_credits - data["run"]["total_records"]
    )


def test_hosted_run_rejects_max_records_above_plan_limit_without_debit() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/run/company",
            json={"query": "Adobe", "mode": "saved", "max_records": 101},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Plan allows at most 100 records per hosted run."
    assert balance.standard_credits_remaining == limits.standard_credits


def test_hosted_run_rejects_unsafe_url_targets_without_running(monkeypatch) -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/run/company",
            json={
                "query": "Adobe",
                "mode": "saved",
                "targets": ["http://169.254.169.254/latest/meta-data/"],
                "max_records": 2,
            },
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "URL targets unsafe IP address: 169.254.169.254."
    assert balance.standard_credits_remaining == limits.standard_credits


def test_hosted_run_rejects_unsafe_job_urls_without_running() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/run/jobs",
            json={
                "query": "partnerships",
                "mode": "saved",
                "job_urls": ["file:///etc/passwd"],
                "max_records": 2,
            },
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Unsupported URL scheme: file."
    assert balance.standard_credits_remaining == limits.standard_credits


def test_hosted_run_rejects_insufficient_preflight_credits_without_running() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    account_service.set_balance(tenant_id, standard_credits=1, browser_credits=100)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/run/company",
            json={"query": "Adobe", "mode": "saved", "max_records": 2},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Insufficient standard credits: need 2, have 1."
    assert balance.standard_credits_remaining == 1


def test_hosted_run_rate_limit_rejects_without_second_debit(tmp_path, monkeypatch) -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    limiter = HostedRateLimiter(HostedRateLimitConfig(max_requests=1, window_seconds=60))
    monkeypatch.setattr(settings, "scout_workdir", str(tmp_path / "hosted-runs"))
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_rate_limiter] = lambda: limiter
    try:
        client = TestClient(app)
        first = client.post(
            "/v1/hosted/run/company",
            json={"query": "Adobe", "mode": "saved", "max_records": 10},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        second = client.post(
            "/v1/hosted/run/company",
            json={"query": "Adobe", "mode": "saved", "max_records": 10},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert first.status_code == 200
    first_records = first.json()["run"]["total_records"]
    assert second.status_code == 429
    assert second.json()["detail"] == "Hosted API rate limit exceeded."
    assert second.headers["retry-after"] == "60"
    assert raw_key not in second.text
    assert balance.standard_credits_remaining == limits.standard_credits - first_records
