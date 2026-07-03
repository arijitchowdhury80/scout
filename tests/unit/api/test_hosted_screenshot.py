"""Tests for hosted bearer-auth screenshot endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from scout.api.deps import get_crawler, get_hosted_account_service, get_hosted_rate_limiter
from scout.api.main import app
from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.hosted import HostedAction, HostedPlan, plan_limits
from scout.core.platform.hosted_rate_limit import HostedRateLimitConfig, HostedRateLimiter
from scout.core.types import ScreenshotResponse


def _account_service_with_key() -> tuple[HostedAccountService, str, str]:
    service = HostedAccountService(InMemoryHostedAccountStore())
    provisioned = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    return service, provisioned.raw_api_key, provisioned.tenant.tenant_id


def _screenshot_response() -> ScreenshotResponse:
    return ScreenshotResponse(
        success=True,
        url="https://www.cnn.com/",
        screenshot_base64="iVBORw0KGgo=",
        width=1280,
        height=800,
        duration_ms=42,
    )


def test_hosted_screenshot_requires_bearer_token() -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    mock_crawler = MagicMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post("/v1/hosted/screenshot", json={"url": "https://www.cnn.com/"})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing Bearer token"


def test_hosted_screenshot_debits_screenshot_standard_credits() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    mock_crawler = MagicMock()
    mock_crawler.screenshot = AsyncMock(return_value=_screenshot_response())
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/screenshot",
            json={"url": "https://www.cnn.com/", "viewport_width": 1280},
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
    assert data["hosted"]["credits_charged"] == HostedAction.SCREENSHOT.credit_cost
    assert data["hosted"]["credit_type"] == "standard"
    assert data["screenshot"]["screenshot_base64"] == "iVBORw0KGgo="
    assert raw_key not in resp.text
    assert (
        balance.standard_credits_remaining
        == limits.standard_credits - HostedAction.SCREENSHOT.credit_cost
    )
    mock_crawler.screenshot.assert_awaited_once()


def test_hosted_screenshot_rejects_insufficient_credits_without_crawling() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    account_service.set_balance(tenant_id, standard_credits=2, browser_credits=0)
    mock_crawler = MagicMock()
    mock_crawler.screenshot = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/screenshot",
            json={"url": "https://www.cnn.com/"},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Insufficient standard credits: need 3, have 2."
    assert balance.standard_credits_remaining == 2
    assert mock_crawler.screenshot.await_count == 0


def test_hosted_screenshot_rate_limit_rejects_without_second_debit_or_capture() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    limiter = HostedRateLimiter(HostedRateLimitConfig(max_requests=1, window_seconds=60))
    mock_crawler = MagicMock()
    mock_crawler.screenshot = AsyncMock(return_value=_screenshot_response())
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_rate_limiter] = lambda: limiter
    try:
        client = TestClient(app)
        first = client.post(
            "/v1/hosted/screenshot",
            json={"url": "https://www.cnn.com/"},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        second = client.post(
            "/v1/hosted/screenshot",
            json={"url": "https://www.cnn.com/"},
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
    assert mock_crawler.screenshot.await_count == 1
    assert (
        balance.standard_credits_remaining
        == limits.standard_credits - HostedAction.SCREENSHOT.credit_cost
    )
