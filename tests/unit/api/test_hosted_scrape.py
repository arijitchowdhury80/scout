"""Tests for hosted bearer-auth scrape endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from scout.api.deps import get_crawler, get_hosted_account_service
from scout.api.main import app
from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.hosted import HostedPlan, plan_limits
from scout.core.types import ScoutMetadata, ScrapeResponse

_TS = "2026-06-28T12:00:00Z"


def _meta(url: str = "https://example.com") -> ScoutMetadata:
    return ScoutMetadata(url=url, crawled_at=_TS)


def _account_service_with_key() -> tuple[HostedAccountService, str, str]:
    service = HostedAccountService(InMemoryHostedAccountStore())
    provisioned = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    return service, provisioned.raw_api_key, provisioned.tenant.tenant_id


def test_hosted_scrape_requires_bearer_token() -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    mock_crawler = MagicMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post("/v1/hosted/scrape", json={"url": "https://example.com"})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing Bearer token"


def test_hosted_scrape_rejects_unsafe_url_without_calling_crawler() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    mock_crawler = MagicMock()
    mock_crawler.scrape = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/scrape",
            json={"url": "http://169.254.169.254/latest/meta-data/"},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "URL targets unsafe IP address: 169.254.169.254."
    assert mock_crawler.scrape.await_count == 0
    assert balance.standard_credits_remaining == limits.standard_credits


def test_hosted_scrape_allows_valid_key_and_debits_credits() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    mock_crawler = MagicMock()
    mock_crawler.scrape = AsyncMock(
        return_value=ScrapeResponse(
            success=True,
            url="https://example.com",
            markdown="# Hello",
            metadata=_meta(),
            provider="test",
            duration_ms=10,
        )
    )
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/scrape",
            json={"url": "https://example.com"},
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
    assert data["hosted"]["credits_charged"] == 1
    assert data["hosted"]["credit_type"] == "standard"
    assert data["scrape"]["markdown"] == "# Hello"
    assert raw_key not in resp.text
    assert balance.standard_credits_remaining == limits.standard_credits - 1
    assert mock_crawler.scrape.await_count == 1
