"""Tests for hosted bearer-auth map endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from scout.api.deps import get_crawler, get_hosted_account_service, get_hosted_rate_limiter
from scout.api.main import app
from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.hosted import HostedPlan, plan_limits
from scout.core.platform.hosted_rate_limit import HostedRateLimitConfig, HostedRateLimiter
from scout.core.types import MapResponse


def _account_service_with_key() -> tuple[HostedAccountService, str, str]:
    service = HostedAccountService(InMemoryHostedAccountStore())
    provisioned = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    return service, provisioned.raw_api_key, provisioned.tenant.tenant_id


def _map_response(total: int = 2) -> MapResponse:
    urls = [f"https://www.wikimedia.org/page-{idx}" for idx in range(1, total + 1)]
    return MapResponse(
        success=True,
        start_url="https://www.wikimedia.org/",
        urls=urls,
        total=total,
        duration_ms=25,
    )


def test_hosted_map_requires_bearer_token() -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    mock_crawler = MagicMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post("/v1/hosted/map", json={"url": "https://www.wikimedia.org/"})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing Bearer token"


def test_hosted_map_debits_one_standard_credit_per_returned_url() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    mock_crawler = MagicMock()
    mock_crawler.map_urls = AsyncMock(return_value=_map_response(total=2))
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/map",
            json={"url": "https://www.wikimedia.org/", "max_pages": 5},
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
    assert data["hosted"]["credits_charged"] == 2
    assert data["hosted"]["credit_type"] == "standard"
    assert data["map"]["total"] == 2
    assert raw_key not in resp.text
    assert balance.standard_credits_remaining == limits.standard_credits - 2
    mock_crawler.map_urls.assert_awaited_once()


def test_hosted_map_rejects_max_pages_above_plan_limit_without_crawling() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    mock_crawler = MagicMock()
    mock_crawler.map_urls = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/map",
            json={"url": "https://www.wikimedia.org/", "max_pages": 101},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    balance = account_service.get_balance(tenant_id)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Plan allows at most 25 URLs per map."
    assert balance.standard_credits_remaining == limits.standard_credits
    assert mock_crawler.map_urls.await_count == 0


def test_hosted_map_rejects_insufficient_preflight_credits_without_crawling() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    account_service.set_balance(tenant_id, standard_credits=1, browser_credits=0)
    mock_crawler = MagicMock()
    mock_crawler.map_urls = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/map",
            json={"url": "https://www.wikimedia.org/", "max_pages": 2},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Insufficient standard credits: need 2, have 1."
    assert balance.standard_credits_remaining == 1
    assert mock_crawler.map_urls.await_count == 0


def test_hosted_map_rate_limit_rejects_without_second_debit_or_crawl() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    limiter = HostedRateLimiter(HostedRateLimitConfig(max_requests=1, window_seconds=60))
    mock_crawler = MagicMock()
    mock_crawler.map_urls = AsyncMock(return_value=_map_response(total=1))
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_rate_limiter] = lambda: limiter
    try:
        client = TestClient(app)
        first = client.post(
            "/v1/hosted/map",
            json={"url": "https://www.wikimedia.org/", "max_pages": 1},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        second = client.post(
            "/v1/hosted/map",
            json={"url": "https://www.wikimedia.org/", "max_pages": 1},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["detail"] == "Hosted API rate limit exceeded."
    assert second.headers["retry-after"] == "60"
    assert raw_key not in second.text
    assert mock_crawler.map_urls.await_count == 1
    assert balance.standard_credits_remaining == limits.standard_credits - 1
