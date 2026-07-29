"""FX-5a: the hosted beta-key endpoints must never leak a raw provider
delivery error (e.g. a literal SMTP response) to the client. The real
reason is logged server-side via structlog; the client gets a generic,
friendly message.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from scout.api.deps import (
    get_hosted_account_service,
    get_hosted_beta_signup_rate_limiter,
    get_hosted_key_delivery_service,
)
from scout.api.main import app
from scout.core.platform.account_service import HostedAccountService, InMemoryHostedAccountStore
from scout.core.platform.hosted import HostedPlan
from scout.core.platform.hosted_rate_limit import HostedRateLimitConfig, HostedRateLimiter
from scout.core.platform.key_delivery import (
    HostedApiKeyDeliveryRequest,
    HostedApiKeyDeliveryResult,
)

_RAW_SMTP_ERROR = "SMTP delivery failed: (550, b'Invalid `to` field: fake@@bad')"


class _FailingDeliveryService:
    """Delivery service stub that always fails with a raw provider error."""

    enabled = True

    def deliver(self, request: HostedApiKeyDeliveryRequest) -> HostedApiKeyDeliveryResult:
        return HostedApiKeyDeliveryResult(
            delivered=False,
            delivery_status="failed",
            reason=_RAW_SMTP_ERROR,
        )


def setup_function() -> None:
    app.state.hosted_beta_signup_rate_limiter = HostedRateLimiter(
        HostedRateLimitConfig(enabled=False)
    )


def test_beta_key_delivery_failure_returns_friendly_message_no_raw_smtp_text() -> None:
    account_service = HostedAccountService(InMemoryHostedAccountStore())
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: _FailingDeliveryService()
    app.dependency_overrides[get_hosted_beta_signup_rate_limiter] = lambda: HostedRateLimiter(
        HostedRateLimitConfig(enabled=False)
    )
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/beta-key",
            json={"name": "Tester", "email": "tester@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 502
    body_text = resp.text
    assert "SMTP" not in body_text
    assert "550" not in body_text
    assert "Invalid `to` field" not in body_text
    detail = resp.json()["detail"]
    assert detail == (
        "We could not send your key right now. Please try again shortly or "
        "contact support@scout.chowmes.com."
    )


def test_beta_key_reissue_delivery_failure_returns_friendly_message_no_raw_smtp_text() -> None:
    account_service = HostedAccountService(InMemoryHostedAccountStore())
    provisioned = account_service.provision_account(
        email="reissue@example.com",
        name="Reissue Tester",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    assert provisioned.tenant.tenant_id

    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: _FailingDeliveryService()
    app.dependency_overrides[get_hosted_beta_signup_rate_limiter] = lambda: HostedRateLimiter(
        HostedRateLimitConfig(enabled=False)
    )
    try:
        client = TestClient(app)
        resp = client.post(
            "/v1/hosted/beta-key/reissue",
            json={"email": "reissue@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 502
    body_text = resp.text
    assert "SMTP" not in body_text
    assert "550" not in body_text
    detail = resp.json()["detail"]
    assert detail == (
        "We could not send your key right now. Please try again shortly or "
        "contact support@scout.chowmes.com."
    )
