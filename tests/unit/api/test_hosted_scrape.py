"""Tests for hosted bearer-auth scrape endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from scout.api.deps import (
    get_crawler,
    get_hosted_admission_controller,
    get_hosted_account_service,
    get_hosted_beta_signup_rate_limiter,
    get_hosted_job_queue,
    get_hosted_key_delivery_service,
    get_hosted_rate_limiter,
)
from scout.api.hosted_jobs import HostedJobQueue
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


def setup_function() -> None:
    """Reset module-shared app state that can leak between TestClient calls."""
    app.state.hosted_beta_signup_rate_limiter = HostedRateLimiter(
        HostedRateLimitConfig(enabled=False)
    )


def _enable_beta_email_registration(monkeypatch) -> None:
    """Opt tests into self-service hosted beta key email registration."""
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True, raising=False)


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
                "name": "Tester",
                "email": "tester@example.com",
                "key_name": "Tester key",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 503
    assert resp.json()["detail"] == "Hosted beta key generation is disabled."


def test_hosted_beta_key_generation_records_request_without_card_setup_bypass(
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
                "name": "Email Tester",
                "email": "email-registration@example.com",
                "key_name": "Email registration beta key",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["email"] == "email-registration@example.com"
    assert resp.json()["delivery_status"] == "delivered"
    tenant = account_service.store.find_tenant_by_email("email-registration@example.com")
    assert tenant is not None
    assert tenant.plan is HostedPlan.HOSTED_BETA_PASS
    assert resp.json()["tenant_id"] == tenant.tenant_id
    assert delivery.requests[0].email == "email-registration@example.com"
    assert delivery.requests[0].name == "Email Tester"
    assert delivery.requests[0].package_id == "beta_trial"
    assert delivery.requests[0].standard_credits == 100
    assert delivery.requests[0].browser_credits == 0
    assert delivery.requests[0].trial_days == 30
    signup_events = account_service.list_signup_events()
    assert signup_events[0].email == "email-registration@example.com"
    assert signup_events[0].status == "delivered"
    assert signup_events[0].source == "email_beta_registration"
    assert signup_events[0].tenant_id == tenant.tenant_id
    assert signup_events[0].key_id == resp.json()["key_id"]
    assert signup_events[0].delivery_status == "delivered"


def test_hosted_beta_key_generation_email_registration_never_exposes_raw_key(
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
                "name": "Self Service Tester",
                "email": "self-service@example.com",
                "key_name": "Self-service beta key",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "self-service@example.com"
    assert data["delivery_status"] == "delivered"
    assert account_service.store.find_tenant_by_email("self-service@example.com") is not None
    assert len(delivery.requests) == 1
    assert "scout_live_" not in resp.text


def test_hosted_beta_key_generation_requires_name_email_and_records_pending_request(
    monkeypatch,
) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    delivery = FakeDeliveryService()
    _enable_beta_email_registration(monkeypatch)
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
    assert data["standard_credits_remaining"] == 100
    assert data["browser_credits_remaining"] == 0
    assert account_service.store.find_tenant_by_email("new-tester@example.com") is not None
    signup_events = account_service.list_signup_events()
    assert signup_events[0].email == "new-tester@example.com"
    assert signup_events[0].name == "New Tester"
    assert signup_events[0].status == "delivered"
    assert signup_events[0].source == "email_beta_registration"
    assert signup_events[0].tenant_id
    assert signup_events[0].key_id
    assert signup_events[0].delivery_status == "delivered"
    assert len(delivery.requests) == 1


def test_hosted_beta_key_generation_requires_name_and_email(monkeypatch) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    delivery = FakeDeliveryService()
    _enable_beta_email_registration(monkeypatch)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    try:
        client = TestClient(app)
        missing_name = client.post(
            "/v1/hosted/beta-key",
            json={"email": "missing-name@example.com"},
        )
        blank_name = client.post(
            "/v1/hosted/beta-key",
            json={"name": "   ", "email": "blank-name@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert missing_name.status_code == 422
    assert blank_name.status_code == 422
    assert account_service.store.find_tenant_by_email("missing-name@example.com") is None
    assert account_service.store.find_tenant_by_email("blank-name@example.com") is None
    assert delivery.requests == []


def test_hosted_beta_key_generation_rejects_removed_invite_password_field(monkeypatch) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    delivery = FakeDeliveryService()
    _enable_beta_email_registration(monkeypatch)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    try:
        client = TestClient(app)
        response = client.post(
            "/v1/hosted/beta-key",
            json={
                "name": "Passwordless Tester",
                "email": "passwordless@example.com",
                "invite_password": "old-beta-password",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert account_service.store.find_tenant_by_email("passwordless@example.com") is None
    assert delivery.requests == []


def test_hosted_beta_key_generation_rate_limits_same_client(monkeypatch) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    delivery = FakeDeliveryService()
    signup_limiter = HostedRateLimiter(HostedRateLimitConfig(max_requests=1, window_seconds=60))
    _enable_beta_email_registration(monkeypatch)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    app.dependency_overrides[get_hosted_beta_signup_rate_limiter] = lambda: signup_limiter
    try:
        client = TestClient(app)
        first = client.post(
            "/v1/hosted/beta-key",
            json={"name": "First Tester", "email": "first-rate@example.com"},
            headers={"X-Forwarded-For": "203.0.113.10"},
        )
        second = client.post(
            "/v1/hosted/beta-key",
            json={"name": "Second Tester", "email": "second-rate@example.com"},
            headers={"X-Forwarded-For": "203.0.113.10"},
        )
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["retry-after"] == "60"
    assert second.json()["detail"] == "Hosted beta signup rate limit exceeded."
    assert account_service.store.find_tenant_by_email("first-rate@example.com") is not None
    assert account_service.store.find_tenant_by_email("second-rate@example.com") is None
    assert len(delivery.requests) == 1


def test_hosted_beta_key_generation_queues_request_when_delivery_is_not_configured(
    monkeypatch,
) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    _enable_beta_email_registration(monkeypatch)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/beta-key",
            json={"name": "Tester", "email": "no-email@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 202
    data = resp.json()
    assert data["success"] is True
    assert data["name"] == "Tester"
    assert data["email"] == "no-email@example.com"
    assert data["tenant_id"] == ""
    assert data["key_id"] == ""
    assert data["plan"] == "hosted_beta_pass"
    assert data["scopes"] == []
    assert data["standard_credits_remaining"] == 0
    assert data["browser_credits_remaining"] == 0
    assert data["delivery_status"] == "pending_delivery"
    assert "recorded" in data["warning"]
    assert account_service.store.find_tenant_by_email("no-email@example.com") is None
    signup_events = account_service.list_signup_events()
    assert signup_events[0].email == "no-email@example.com"
    assert signup_events[0].name == "Tester"
    assert signup_events[0].status == "pending_delivery"
    assert signup_events[0].reason == "Awaiting hosted API-key email delivery configuration."


def test_hosted_beta_key_generation_does_not_duplicate_pending_delivery_requests(
    monkeypatch,
) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    _enable_beta_email_registration(monkeypatch)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        first = client.post(
            "/v1/hosted/beta-key",
            json={"name": "Pending Tester", "email": "pending@example.com"},
        )
        second = client.post(
            "/v1/hosted/beta-key",
            json={"name": "Pending Tester Again", "email": "pending@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 202
    assert second.status_code == 202
    assert second.json()["delivery_status"] == "pending_delivery"
    assert second.json()["warning"] == (
        "Your beta registration is already recorded. Scout will email your API key "
        "after email delivery is configured."
    )
    assert account_service.store.find_tenant_by_email("pending@example.com") is None
    signup_events = account_service.list_signup_events()
    assert len(signup_events) == 1
    assert signup_events[0].email == "pending@example.com"
    assert signup_events[0].status == "pending_delivery"


def test_hosted_beta_key_status_reports_pending_request_without_raw_key(monkeypatch) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    _enable_beta_email_registration(monkeypatch)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        client.post(
            "/v1/hosted/beta-key",
            json={"name": "Pending Status", "email": "pending-status@example.com"},
        )
        response = client.post(
            "/v1/hosted/beta-key/status",
            json={"email": "pending-status@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["email"] == "pending-status@example.com"
    assert data["status"] == "pending_delivery"
    assert data["delivery_status"] == "pending_delivery"
    assert data["has_account"] is False
    assert data["tenant_id"] == ""
    assert data["key_id"] == ""
    assert "raw_api_key" not in data
    assert "scout_live_" not in response.text


def test_hosted_beta_key_status_reports_delivered_account_without_raw_key(monkeypatch) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    delivery = FakeDeliveryService()
    account_service.provision_account(
        email="delivered-status@example.com",
        name="Delivered Status",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
        key_name="Delivered status key",
    )
    _enable_beta_email_registration(monkeypatch)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    try:
        client = TestClient(app)
        response = client.post(
            "/v1/hosted/beta-key/status",
            json={"email": "delivered-status@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["email"] == "delivered-status@example.com"
    assert data["status"] == "account_exists"
    assert data["delivery_status"] == ""
    assert data["has_account"] is True
    assert data["tenant_id"].startswith("tenant_")
    assert data["key_id"].startswith("key_")
    assert "raw_api_key" not in data
    assert "scout_live_" not in response.text


def test_hosted_beta_key_status_unknown_email_is_non_enumerating() -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        response = client.post(
            "/v1/hosted/beta-key/status",
            json={"email": "unknown@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["email"] == "unknown@example.com"
    assert data["status"] == "not_found"
    assert data["delivery_status"] == ""
    assert data["has_account"] is False
    assert data["message"] == (
        "No hosted beta request is recorded for this email. You can register for beta access."
    )


def test_hosted_beta_key_response_schema_does_not_expose_raw_key() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")
    schema = response.json()["components"]["schemas"]["HostedBetaKeyResponse"]

    assert response.status_code == 200
    assert "raw_api_key" not in schema["properties"]


def test_hosted_beta_key_status_response_schema_does_not_expose_raw_key() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")
    schema = response.json()["components"]["schemas"]["HostedBetaKeyStatusResponse"]

    assert response.status_code == 200
    assert "raw_api_key" not in schema["properties"]


def test_hosted_beta_key_reissue_emails_new_key_without_exposing_it(monkeypatch) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    delivery = FakeDeliveryService()
    existing = account_service.provision_account(
        email="recover@example.com",
        name="Recoverable Tester",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
        key_name="Recoverable tester key",
    )
    _enable_beta_email_registration(monkeypatch)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    try:
        client = TestClient(app)
        original_key = existing.raw_api_key
        reissue = client.post(
            "/v1/hosted/beta-key/reissue",
            json={"email": "recover@example.com"},
        )
        new_key = delivery.requests[0].raw_api_key
        old_me = client.get(
            "/v1/hosted/me",
            headers={"Authorization": f"Bearer {original_key}"},
        )
        new_me = client.get(
            "/v1/hosted/me",
            headers={"Authorization": f"Bearer {new_key}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert reissue.status_code == 200
    data = reissue.json()
    assert data["success"] is True
    assert data["email"] == "recover@example.com"
    assert data["delivery_status"] == "delivered"
    assert data["has_account"] is True
    assert data["key_id"].startswith("key_")
    assert "Scout emailed a replacement API key" in data["message"]
    assert new_key != original_key
    assert original_key not in reissue.text
    assert new_key not in reissue.text
    assert "raw_api_key" not in data
    assert old_me.status_code == 403
    assert old_me.json()["detail"] == "API key is not active."
    assert new_me.status_code == 200
    assert delivery.requests[0].checkout_session_id == "beta_key_reissue"
    assert delivery.requests[0].email == "recover@example.com"
    signup_events = account_service.list_signup_events()
    assert signup_events[0].status == "reissued"
    assert signup_events[0].source == "email_beta_key_reissue"
    assert signup_events[0].email == "recover@example.com"
    assert signup_events[0].delivery_status == "delivered"


def test_hosted_beta_key_reissue_unknown_email_is_non_enumerating(monkeypatch) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    delivery = FakeDeliveryService()
    _enable_beta_email_registration(monkeypatch)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    try:
        client = TestClient(app)
        response = client.post(
            "/v1/hosted/beta-key/reissue",
            json={"email": "unknown-reissue@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    data = response.json()
    assert data["success"] is True
    assert data["email"] == "unknown-reissue@example.com"
    assert data["status"] == "not_found"
    assert data["delivery_status"] == "not_delivered"
    assert data["has_account"] is False
    assert data["tenant_id"] == ""
    assert data["key_id"] == ""
    assert data["message"] == (
        "If a hosted Scout account exists for this email, Scout will email a replacement API key."
    )
    assert delivery.requests == []
    assert "raw_api_key" not in data


def test_hosted_beta_key_reissue_requires_delivery_configuration(monkeypatch) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    _enable_beta_email_registration(monkeypatch)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    try:
        client = TestClient(app)
        response = client.post(
            "/v1/hosted/beta-key/reissue",
            json={"email": "builder@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "Hosted API key delivery is not configured."


def test_hosted_beta_key_reissue_response_schema_does_not_expose_raw_key() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")
    schema = response.json()["components"]["schemas"]["HostedBetaKeyReissueResponse"]

    assert response.status_code == 200
    assert "raw_api_key" not in schema["properties"]


def test_hosted_beta_key_request_schema_requires_name_email_and_no_invite_password() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")
    schema = response.json()["components"]["schemas"]["HostedBetaKeyRequest"]

    assert response.status_code == 200
    assert schema["required"] == ["name", "email"]
    assert set(schema["properties"]) == {"name", "email", "key_name"}
    assert "password" not in schema["properties"]
    assert "invite_password" not in schema["properties"]


def test_hosted_beta_key_generation_records_request_even_when_delivery_would_fail(
    monkeypatch,
) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    delivery = FakeDeliveryService(
        HostedApiKeyDeliveryResult(
            delivered=False,
            delivery_status="failed",
            reason="SMTP delivery failed: smtp down",
        )
    )
    _enable_beta_email_registration(monkeypatch)
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
    assert len(delivery.requests) == 1
    signup_events = account_service.list_signup_events()
    assert signup_events[0].email == "retry@example.com"
    assert signup_events[0].name == "Retry Tester"
    assert signup_events[0].status == "failed"
    assert signup_events[0].reason == "SMTP delivery failed: smtp down"
    assert signup_events[0].delivery_status == "failed"


def test_hosted_beta_key_generation_does_not_duplicate_pending_or_existing_email(
    monkeypatch,
) -> None:
    account_service, _raw_key, _tenant_id = _account_service_with_key()
    delivery = FakeDeliveryService()
    account_service.provision_account(
        email="existing@example.com",
        name="Existing User",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
        key_name="Existing beta key",
    )
    _enable_beta_email_registration(monkeypatch)
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
        existing = client.post(
            "/v1/hosted/beta-key",
            json={"name": "Existing User", "email": "existing@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 200
    assert second.status_code == 202
    assert second.json()["delivery_status"] == "account_exists"
    assert existing.status_code == 202
    assert existing.json()["delivery_status"] == "account_exists"
    signup_events = account_service.list_signup_events()
    assert [event.status for event in signup_events if str(event.email) == "dupe@example.com"] == [
        "duplicate",
        "delivered",
    ]
    assert account_service.store.find_tenant_by_email("existing@example.com") is not None
    assert len(delivery.requests) == 1


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
    queue = HostedJobQueue(max_queued=2, worker_count=1)
    mock_crawler = MagicMock()
    mock_crawler.scrape = AsyncMock()
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_admission_controller] = lambda: admission
    app.dependency_overrides[get_hosted_job_queue] = lambda: queue
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
