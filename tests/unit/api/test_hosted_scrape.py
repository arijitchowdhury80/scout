"""Tests for hosted bearer-auth scrape endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from scout.api.deps import (
    get_crawler,
    get_hosted_admission_controller,
    get_hosted_account_service,
    get_hosted_key_delivery_service,
    get_hosted_rate_limiter,
)
from scout.api.main import app
from scout.api.config import settings
from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.admission import AdmissionController
from scout.core.platform.hosted import HostedPlan, plan_limits
from scout.core.platform.hosted_rate_limit import HostedRateLimitConfig, HostedRateLimiter
from scout.core.platform.key_delivery import (
    HostedApiKeyDeliveryRequest,
    HostedApiKeyDeliveryResult,
)
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


def test_hosted_me_requires_bearer_token() -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.get("/v1/hosted/me")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing Bearer token"


def test_hosted_me_returns_plan_limits_and_balance_without_raw_key() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.get("/v1/hosted/me", headers={"Authorization": f"Bearer {raw_key}"})
    finally:
        app.dependency_overrides.clear()

    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tenant_id"] == tenant_id
    assert data["plan"] == "hosted_beta_pass"
    assert data["account_status"] == "active"
    assert data["balance"]["standard_credits_remaining"] == limits.standard_credits
    assert data["balance"]["browser_credits_remaining"] == limits.browser_credits
    assert data["limits"]["standard_credits"] == limits.standard_credits
    assert data["limits"]["browser_credits"] == limits.browser_credits
    assert data["limits"]["max_pages_per_run"] == limits.max_pages_per_run
    assert raw_key not in resp.text


def test_hosted_beta_key_generation_is_disabled_when_signup_disabled(monkeypatch) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", False, raising=False)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/beta-key",
            json={
                "email": "tester@example.com",
                "key_name": "Tester key",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 503
    assert resp.json()["detail"] == "Hosted beta key generation is disabled."


def test_hosted_beta_key_generation_requires_email_only_and_creates_usable_key(
    monkeypatch,
) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    delivery = FakeDeliveryService()
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True, raising=False)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/beta-key",
            json={
                "name": "New Tester",
                "email": "new-tester@example.com",
                "key_name": "New tester beta key",
            },
        )
        data = resp.json()
        me_resp = client.get(
            "/v1/hosted/me",
            headers={"Authorization": f"Bearer {delivery.requests[0].raw_api_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert data["success"] is True
    assert data["email"] == "new-tester@example.com"
    assert data["name"] == "New Tester"
    assert data["plan"] == "hosted_beta_pass"
    assert data["scopes"] == ["runs:create"]
    assert data["delivery_status"] == "delivered"
    assert "raw_api_key" not in data
    assert (
        data["standard_credits_remaining"]
        == plan_limits(HostedPlan.HOSTED_BETA_PASS).standard_credits
    )
    assert (
        data["browser_credits_remaining"]
        == plan_limits(HostedPlan.HOSTED_BETA_PASS).browser_credits
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["tenant_id"] == data["tenant_id"]
    assert delivery.requests[0].email == "new-tester@example.com"
    assert delivery.requests[0].name == "New Tester"
    assert delivery.requests[0].raw_api_key not in resp.text
    assert delivery.requests[0].raw_api_key not in me_resp.text


def test_hosted_beta_key_generation_requires_delivery_service(monkeypatch) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True, raising=False)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/beta-key",
            json={"name": "Tester", "email": "no-email@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 503
    assert resp.json()["detail"] == "Hosted API key email delivery is not configured."
    assert account_service.store.find_tenant_by_email("no-email@example.com") is None


def test_hosted_beta_key_generation_rolls_back_when_delivery_fails(monkeypatch) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    delivery = FakeDeliveryService(
        HostedApiKeyDeliveryResult(
            delivered=False,
            delivery_status="failed",
            reason="SMTP delivery failed: smtp down",
        )
    )
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True, raising=False)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/beta-key",
            json={"name": "Retry Tester", "email": "retry@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 502
    assert resp.json()["detail"] == "SMTP delivery failed: smtp down"
    assert account_service.store.find_tenant_by_email("retry@example.com") is None


def test_hosted_beta_key_generation_rejects_duplicate_email(monkeypatch) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    delivery = FakeDeliveryService()
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True, raising=False)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    try:
        client = TestClient(app)
        first = client.post(
            "/v1/hosted/beta-key",
            json={"name": "First User", "email": "dupe@example.com", "key_name": "First"},
        )
        second = client.post(
            "/v1/hosted/beta-key",
            json={"name": "Second User", "email": "dupe@example.com", "key_name": "Second"},
        )
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"] == "A hosted beta key already exists for this email."


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


def test_hosted_scrape_rejects_hostname_resolving_to_private_ip_without_calling_crawler(
    monkeypatch,
) -> None:
    def fake_getaddrinfo(*_args):
        return [(None, None, None, "", ("10.0.0.7", 443))]

    monkeypatch.setattr("socket.getaddrinfo", fake_getaddrinfo)
    account_service, raw_key, tenant_id = _account_service_with_key()
    mock_crawler = MagicMock()
    mock_crawler.scrape = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/scrape",
            json={"url": "https://public-name.example/products"},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "URL resolved to unsafe IP address: 10.0.0.7."
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
        usage_resp = client.get(
            "/v1/hosted/usage",
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
    assert usage_resp.status_code == 200
    usage = usage_resp.json()
    assert usage["total"] == 1
    assert usage["usage"][0]["action"] == "scrape"
    assert usage["usage"][0]["credits"] == 1
    assert usage["usage"][0]["tenant_id"] == tenant_id
    assert raw_key not in usage_resp.text


def test_hosted_scrape_rate_limit_rejects_without_second_debit_or_crawl() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    limiter = HostedRateLimiter(HostedRateLimitConfig(max_requests=1, window_seconds=60))
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
    app.dependency_overrides[get_hosted_rate_limiter] = lambda: limiter
    try:
        client = TestClient(app)
        first = client.post(
            "/v1/hosted/scrape",
            json={"url": "https://example.com"},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        second = client.post(
            "/v1/hosted/scrape",
            json={"url": "https://example.com"},
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
    assert mock_crawler.scrape.await_count == 1
    assert balance.standard_credits_remaining == limits.standard_credits - 1


def test_hosted_scrape_capacity_queues_without_debit_or_crawl() -> None:
    account_service, raw_key, tenant_id = _account_service_with_key()
    admission = AdmissionController(max_active=0, retry_after_seconds=3)
    mock_crawler = MagicMock()
    mock_crawler.scrape = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_admission_controller] = lambda: admission
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
    data = resp.json()
    assert resp.status_code == 202
    assert data["status"] == "queued"
    assert data["kind"] == "scrape"
    assert data["hosted"]["credits_charged"] == 0
    assert resp.headers["retry-after"] == "3"
    assert mock_crawler.scrape.await_count == 0
    assert balance.standard_credits_remaining == limits.standard_credits


class FakeDeliveryService:
    """Fake hosted API-key delivery service for beta signup route tests."""

    enabled = True

    def __init__(
        self,
        result: HostedApiKeyDeliveryResult | None = None,
    ) -> None:
        self.result = result or HostedApiKeyDeliveryResult(
            delivered=True,
            delivery_status="delivered",
        )
        self.requests: list[HostedApiKeyDeliveryRequest] = []

    def deliver(self, request: HostedApiKeyDeliveryRequest) -> HostedApiKeyDeliveryResult:
        self.requests.append(request)
        return self.result
