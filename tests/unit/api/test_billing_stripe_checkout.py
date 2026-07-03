"""Tests for hosted Stripe Checkout Session creation.

# Scenario list:
# - public checkout route returns a Stripe Checkout URL and session id
# - route never returns Stripe secret material
# - missing checkout configuration returns a clear 503 without creating a session
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from scout.api.deps import (
    get_hosted_key_delivery_service,
    get_stripe_checkout_service,
    get_stripe_webhook_secret,
)
from scout.api.config import settings
from scout.api.main import app
from scout.core.platform.stripe_checkout import (
    StripeCheckoutResult,
    StripeCheckoutService,
)


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> Iterator[None]:
    """Clear FastAPI dependency overrides after each checkout route test."""
    yield
    app.dependency_overrides.clear()


def test_stripe_checkout_route_returns_checkout_url_without_static_api_key(monkeypatch) -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(
            success=True,
            checkout_session_id="cs_test_checkout_001",
            checkout_url="https://checkout.stripe.com/c/pay/cs_test_checkout_001",
        )
    )
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    client = _client(service)

    response = client.post(
        "/v1/billing/stripe/checkout-session",
        json={
            "email": "builder@example.com",
            "name": "Builder Person",
            "package_id": "beta_trial",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "checkout_session_id": "cs_test_checkout_001",
        "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_checkout_001",
        "reason": "",
    }
    assert service.requests == [("builder@example.com", "Builder Person", "beta_trial")]
    assert "sk_test" not in response.text


def test_stripe_checkout_route_blocks_when_webhook_is_not_configured(
    monkeypatch,
) -> None:
    service = RecordingStripeCheckoutService(StripeCheckoutResult(success=True))
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    client = _client(service, webhook_secret="")

    response = client.post(
        "/v1/billing/stripe/checkout-session",
        json={"email": "builder@example.com", "package_id": "standard_1000"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Stripe webhook secret is not configured."
    assert service.requests == []


def test_stripe_checkout_route_blocks_when_key_delivery_is_not_configured(
    monkeypatch,
) -> None:
    service = RecordingStripeCheckoutService(StripeCheckoutResult(success=True))
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    client = _client(service, delivery_enabled=False)

    response = client.post(
        "/v1/billing/stripe/checkout-session",
        json={"email": "builder@example.com", "package_id": "standard_1000"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Hosted API key delivery is not configured."
    assert service.requests == []


def test_stripe_checkout_route_blocks_beta_trial_when_beta_signup_disabled() -> None:
    service = RecordingStripeCheckoutService(StripeCheckoutResult(success=True))
    client = _client(service)

    response = client.post(
        "/v1/billing/stripe/checkout-session",
        json={"email": "builder@example.com", "package_id": "beta_trial"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Hosted beta signup is disabled."
    assert service.requests == []


def test_stripe_checkout_route_returns_503_when_checkout_is_not_configured(
    monkeypatch,
) -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(
            success=False,
            reason="Stripe Checkout is not configured.",
        )
    )
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    client = _client(service)

    response = client.post("/v1/billing/stripe/checkout-session", json={})

    assert response.status_code == 503
    assert response.json()["detail"] == "Stripe Checkout is not configured."
    assert service.requests == [("", "", "beta_trial")]


def test_stripe_status_returns_non_secret_readiness_flags() -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(success=True),
        enabled=True,
    )
    delivery = RecordingDeliveryService(enabled=True)
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: "whsec_test"
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    client = TestClient(app)

    response = client.get("/v1/billing/stripe/status")

    assert response.status_code == 200
    assert response.json() == {
        "beta_signup_enabled": False,
        "checkout_configured": True,
        "webhook_configured": True,
        "key_delivery_configured": True,
        "ready_for_beta_key_delivery": False,
        "ready_for_beta_checkout": False,
        "ready_for_paid_key_delivery": True,
    }
    assert "whsec_test" not in response.text
    assert "sk_" not in response.text


def test_stripe_status_reports_missing_checkout_and_delivery_configuration() -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(success=False),
        enabled=False,
    )
    delivery = RecordingDeliveryService(enabled=False)
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: ""
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    client = TestClient(app)

    response = client.get("/v1/billing/stripe/status")

    assert response.status_code == 200
    assert response.json() == {
        "beta_signup_enabled": False,
        "checkout_configured": False,
        "webhook_configured": False,
        "key_delivery_configured": False,
        "ready_for_beta_key_delivery": False,
        "ready_for_beta_checkout": False,
        "ready_for_paid_key_delivery": False,
    }


def test_stripe_status_requires_checkout_webhook_and_delivery_for_beta(monkeypatch) -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(success=False),
        enabled=False,
    )
    delivery = RecordingDeliveryService(enabled=True)
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: ""
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    client = TestClient(app)

    response = client.get("/v1/billing/stripe/status")

    assert response.status_code == 200
    assert response.json() == {
        "beta_signup_enabled": True,
        "checkout_configured": False,
        "webhook_configured": False,
        "key_delivery_configured": True,
        "ready_for_beta_key_delivery": True,
        "ready_for_beta_checkout": False,
        "ready_for_paid_key_delivery": False,
    }


def test_stripe_status_reports_beta_checkout_readiness(monkeypatch) -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(success=True),
        enabled=True,
    )
    delivery = RecordingDeliveryService(enabled=True)
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: "whsec_test"
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    client = TestClient(app)

    response = client.get("/v1/billing/stripe/status")

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "beta_signup_enabled": True,
        "checkout_configured": True,
        "webhook_configured": True,
        "key_delivery_configured": True,
        "ready_for_beta_key_delivery": True,
        "ready_for_beta_checkout": True,
        "ready_for_paid_key_delivery": True,
    }


def test_stripe_status_does_not_enable_beta_without_checkout_webhook_and_delivery(
    monkeypatch,
) -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(success=False),
        enabled=False,
    )
    delivery = RecordingDeliveryService(enabled=False)
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: ""
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    client = TestClient(app)

    response = client.get("/v1/billing/stripe/status")

    assert response.status_code == 200
    assert response.json() == {
        "beta_signup_enabled": True,
        "checkout_configured": False,
        "webhook_configured": False,
        "key_delivery_configured": False,
        "ready_for_beta_key_delivery": False,
        "ready_for_beta_checkout": False,
        "ready_for_paid_key_delivery": False,
    }


def test_billing_packages_returns_credit_meanings_and_unit_economics_without_secrets() -> None:
    client = TestClient(app)

    response = client.get("/v1/billing/packages")

    assert response.status_code == 200
    data = response.json()
    package_ids = {package["package_id"] for package in data["packages"]}
    standard_1000 = next(
        package for package in data["packages"] if package["package_id"] == "standard_1000"
    )

    assert "beta_trial" in package_ids
    assert "standard_1000" in package_ids
    assert "browser_100" in package_ids
    assert standard_1000["amount_cents"] == 1000
    assert standard_1000["standard_credits"] == 1000
    assert standard_1000["browser_credits"] == 0
    assert data["credit_costs"]["scrape"] == "1 standard credit"
    assert data["credit_costs"]["screenshot"] == "3 standard credits"
    assert data["unit_economics"]["standard_1000"]["gross_margin_percent"] == 74.1
    assert data["unit_economics"]["standard_1000"]["break_even_packages_per_month"] == 17
    assert "sk_" not in response.text
    assert "whsec_" not in response.text


def _client(
    service: StripeCheckoutService,
    *,
    webhook_secret: str = "whsec_test",
    delivery_enabled: bool = True,
) -> TestClient:
    """Build a test client with the checkout service dependency overridden."""
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: webhook_secret
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: RecordingDeliveryService(
        delivery_enabled
    )
    return TestClient(app)


class RecordingStripeCheckoutService:
    """Record checkout requests and return a deterministic result."""

    def __init__(self, result: StripeCheckoutResult, enabled: bool = True) -> None:
        self.result = result
        self.enabled = enabled
        self.requests: list[tuple[str, str, str]] = []

    def create_checkout_session(self, request: object) -> StripeCheckoutResult:
        self.requests.append(
            (
                str(getattr(request, "email", "")),
                str(getattr(request, "name", "")),
                str(getattr(request, "package_id", "")),
            )
        )
        return self.result


class RecordingDeliveryService:
    """Expose only delivery readiness for Stripe status tests."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
