"""Tests for hosted Stripe Checkout Session creation.

# Scenario list:
# - public checkout route returns a Stripe Checkout URL and session id
# - route never returns Stripe secret material
# - missing checkout configuration returns a clear 503 without creating a session
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scout.api.deps import (
    get_hosted_account_service,
    get_hosted_key_delivery_service,
    get_hosted_payment_provisioning_service,
    get_stripe_checkout_service,
    get_stripe_customer_portal_service,
    get_stripe_webhook_secret,
)
from scout.api.config import settings
from scout.api.main import app
from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.account_sqlite_store import SQLiteHostedAccountStore
from scout.core.platform.hosted import HostedPlan
from scout.core.platform.payment_provisioning import (
    HostedCheckoutPaymentStatus,
    HostedCheckoutProvisioningRequest,
    HostedPaymentProvider,
    HostedPaymentProvisioningService,
    SQLiteHostedPaymentStore,
)
from scout.core.platform.stripe_checkout import (
    StripeCheckoutConfig,
    StripeCheckoutRequest,
    StripeCheckoutService,
    StripeCheckoutResult,
    StripeCheckoutSession,
    StripeCustomerPortalRequest,
    StripeCustomerPortalResult,
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


def test_beta_checkout_route_records_signup_attempt_before_webhook(monkeypatch) -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(
            success=True,
            checkout_session_id="cs_test_beta_signup_001",
            checkout_url="https://checkout.stripe.com/c/pay/cs_test_beta_signup_001",
        )
    )
    account_service = HostedAccountService(InMemoryHostedAccountStore())
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    client = _client(service, account_service=account_service)

    response = client.post(
        "/v1/billing/stripe/checkout-session",
        json={
            "email": "Beta.Builder@Example.com",
            "name": "Beta Builder",
            "package_id": "beta_trial",
        },
    )

    assert response.status_code == 200
    events = account_service.list_signup_events(limit=10)
    assert len(events) == 1
    event = events[0]
    assert str(event.email) == "Beta.Builder@example.com"
    assert event.name == "Beta Builder"
    assert event.status == "checkout_started"
    assert event.source == "stripe_checkout"
    assert event.delivery_status == "checkout_session_created"
    assert event.reason == "cs_test_beta_signup_001"
    assert event.tenant_id == ""
    assert event.key_id == ""
    assert "scout_live_" not in response.text


def test_stripe_checkout_route_blocks_when_webhook_is_not_configured(
    monkeypatch,
) -> None:
    service = RecordingStripeCheckoutService(StripeCheckoutResult(success=True))
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    client = _client(service, webhook_secret="")

    response = client.post(
        "/v1/billing/stripe/checkout-session",
        json={
            "email": "builder@example.com",
            "name": "Builder Person",
            "package_id": "standard_1000",
        },
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
        json={
            "email": "builder@example.com",
            "name": "Builder Person",
            "package_id": "standard_1000",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Hosted API key delivery is not configured."
    assert service.requests == []


def test_stripe_checkout_route_blocks_beta_trial_when_beta_signup_disabled() -> None:
    service = RecordingStripeCheckoutService(StripeCheckoutResult(success=True))
    client = _client(service)

    response = client.post(
        "/v1/billing/stripe/checkout-session",
        json={
            "email": "builder@example.com",
            "name": "Builder Person",
            "package_id": "beta_trial",
        },
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

    response = client.post(
        "/v1/billing/stripe/checkout-session",
        json={
            "email": "builder@example.com",
            "name": "Builder Person",
            "package_id": "beta_trial",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Stripe Checkout is not configured."
    assert service.requests == [("builder@example.com", "Builder Person", "beta_trial")]


def test_stripe_checkout_route_rejects_missing_self_service_identity(
    monkeypatch,
) -> None:
    service = RecordingStripeCheckoutService(StripeCheckoutResult(success=True))
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    client = _client(service)

    response = client.post("/v1/billing/stripe/checkout-session", json={})

    assert response.status_code == 422
    assert service.requests == []


def test_stripe_checkout_route_rejects_invalid_email_before_checkout(
    monkeypatch,
) -> None:
    service = RecordingStripeCheckoutService(StripeCheckoutResult(success=True))
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    client = _client(service)

    response = client.post(
        "/v1/billing/stripe/checkout-session",
        json={
            "email": "not-an-email",
            "name": "Builder Person",
            "package_id": "beta_trial",
        },
    )

    assert response.status_code == 422
    assert service.requests == []


def test_stripe_status_returns_non_secret_readiness_flags() -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(success=True),
        enabled=True,
    )
    delivery = RecordingDeliveryService(enabled=True)
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    app.dependency_overrides[get_stripe_customer_portal_service] = lambda: (
        RecordingStripeCustomerPortalService(StripeCustomerPortalResult(success=True), enabled=True)
    )
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: "whsec_test"
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    client = TestClient(app)

    response = client.get("/v1/billing/stripe/status")

    assert response.status_code == 200
    _assert_status_subset(
        response.json(),
        {
            "beta_signup_enabled": False,
            "checkout_configured": True,
            "webhook_configured": True,
            "key_delivery_configured": True,
            "ready_for_beta_key_delivery": False,
            "ready_for_beta_checkout": False,
            "ready_for_paid_key_delivery": True,
            "missing_configuration": ["hosted_beta_signup"],
            "blocking_reasons": ["Hosted beta signup is disabled."],
            "operator_next_actions": [
                "Set HOSTED_BETA_SIGNUP_ENABLED=true when beta signup should be open."
            ],
        },
    )
    assert "whsec_test" not in response.text
    assert "sk_" not in response.text


def test_stripe_status_reports_missing_checkout_and_delivery_configuration() -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(success=False),
        enabled=False,
        paid_packages_configured=False,
    )
    delivery = RecordingDeliveryService(enabled=False)
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    app.dependency_overrides[get_stripe_customer_portal_service] = lambda: (
        RecordingStripeCustomerPortalService(
            StripeCustomerPortalResult(success=False), enabled=False
        )
    )
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: ""
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    client = TestClient(app)

    response = client.get("/v1/billing/stripe/status")

    assert response.status_code == 200
    data = response.json()
    _assert_status_subset(
        data,
        {
            "beta_signup_enabled": False,
            "checkout_configured": False,
            "customer_portal_configured": False,
            "webhook_configured": False,
            "key_delivery_configured": False,
            "ready_for_beta_key_delivery": False,
            "ready_for_beta_checkout": False,
            "ready_for_paid_key_delivery": False,
            "missing_configuration": [
                "hosted_beta_signup",
                "stripe_checkout",
                "stripe_customer_portal",
                "stripe_webhook_secret",
                "hosted_key_delivery_smtp",
            ],
            "blocking_reasons": [
                "Hosted beta signup is disabled.",
                "Stripe Checkout is not configured.",
                "Stripe Customer Portal is not configured.",
                "Stripe webhook secret is not configured.",
                "Hosted API-key email delivery is not configured.",
            ],
            "operator_next_actions": [
                "Set HOSTED_BETA_SIGNUP_ENABLED=true when beta signup should be open.",
                "Configure Stripe secret key, price IDs, success URL, and cancel URL.",
                "Configure STRIPE_PORTAL_RETURN_URL for customer billing management.",
                "Configure STRIPE_WEBHOOK_SECRET from the signed Stripe endpoint.",
                "Configure hosted API-key SMTP delivery settings.",
            ],
        },
    )
    assert "sk_" not in response.text
    assert "whsec_" not in response.text


def test_stripe_status_exposes_self_service_path_and_exact_missing_env_keys(
    monkeypatch,
) -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(success=False),
        enabled=False,
        paid_packages_configured=False,
    )
    delivery = RecordingDeliveryService(enabled=False)
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    monkeypatch.setattr(settings, "stripe_success_url", "")
    monkeypatch.setattr(settings, "stripe_cancel_url", "")
    monkeypatch.setattr(settings, "stripe_portal_return_url", "")
    monkeypatch.setattr(settings, "stripe_standard_1000_price_id", "")
    monkeypatch.setattr(settings, "stripe_standard_3000_price_id", "")
    monkeypatch.setattr(settings, "stripe_standard_15000_price_id", "")
    monkeypatch.setattr(settings, "hosted_key_delivery_smtp_host", "")
    monkeypatch.setattr(settings, "hosted_key_delivery_smtp_from_email", "")
    monkeypatch.setattr(settings, "hosted_key_delivery_smtp_username", "")
    monkeypatch.setattr(settings, "hosted_key_delivery_smtp_password", "")
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    app.dependency_overrides[get_stripe_customer_portal_service] = lambda: (
        RecordingStripeCustomerPortalService(
            StripeCustomerPortalResult(success=False), enabled=False
        )
    )
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: ""
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    client = TestClient(app)

    response = client.get("/v1/billing/stripe/status")

    assert response.status_code == 200
    data = response.json()
    assert data["public_self_service_path"] == "email_beta_registration_with_checkout_hook"
    assert data["public_beta_key_endpoint"] == "/v1/hosted/beta-key"
    assert data["public_beta_checkout_endpoint"] == "/v1/billing/stripe/checkout-session"
    assert data["public_customer_portal_endpoint"] == ("/v1/billing/stripe/customer-portal-session")
    assert data["customer_next_actions"] == [
        "Use /beta for email-first beta registration; Scout may route through $0 Stripe setup once checkout is fully configured.",
        "Use /pricing to buy paid credit packages when paid checkout readiness is true.",
    ]
    assert data["missing_environment_keys"] == [
        "STRIPE_SECRET_KEY",
        "STRIPE_SUCCESS_URL",
        "STRIPE_CANCEL_URL",
        "STRIPE_PORTAL_RETURN_URL",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_STANDARD_1000_PRICE_ID",
        "STRIPE_STANDARD_3000_PRICE_ID",
        "STRIPE_STANDARD_15000_PRICE_ID",
        "HOSTED_KEY_DELIVERY_SMTP_HOST",
        "HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL",
        "HOSTED_KEY_DELIVERY_SMTP_USERNAME",
        "HOSTED_KEY_DELIVERY_SMTP_PASSWORD",
    ]
    assert "sk_" not in response.text
    assert "whsec_" not in response.text


def test_stripe_status_requires_checkout_webhook_and_delivery_for_beta(monkeypatch) -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(success=False),
        enabled=False,
    )
    delivery = RecordingDeliveryService(enabled=True)
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    app.dependency_overrides[get_stripe_customer_portal_service] = lambda: (
        RecordingStripeCustomerPortalService(
            StripeCustomerPortalResult(success=False), enabled=False
        )
    )
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: ""
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    client = TestClient(app)

    response = client.get("/v1/billing/stripe/status")

    assert response.status_code == 200
    _assert_status_subset(
        response.json(),
        {
            "beta_signup_enabled": True,
            "checkout_configured": False,
            "customer_portal_configured": False,
            "webhook_configured": False,
            "key_delivery_configured": True,
            "ready_for_beta_key_delivery": True,
            "ready_for_beta_checkout": False,
            "ready_for_paid_key_delivery": False,
            "missing_configuration": [
                "stripe_checkout",
                "stripe_customer_portal",
                "stripe_webhook_secret",
            ],
            "blocking_reasons": [
                "Stripe Checkout is not configured.",
                "Stripe Customer Portal is not configured.",
                "Stripe webhook secret is not configured.",
            ],
            "operator_next_actions": [
                "Configure Stripe secret key, price IDs, success URL, and cancel URL.",
                "Configure STRIPE_PORTAL_RETURN_URL for customer billing management.",
                "Configure STRIPE_WEBHOOK_SECRET from the signed Stripe endpoint.",
            ],
        },
    )


def test_stripe_status_reports_beta_checkout_readiness(monkeypatch) -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(success=True),
        enabled=True,
    )
    delivery = RecordingDeliveryService(enabled=True)
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    app.dependency_overrides[get_stripe_customer_portal_service] = lambda: (
        RecordingStripeCustomerPortalService(StripeCustomerPortalResult(success=True), enabled=True)
    )
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: "whsec_test"
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    client = TestClient(app)

    response = client.get("/v1/billing/stripe/status")

    assert response.status_code == 200
    data = response.json()
    _assert_status_subset(
        data,
        {
            "beta_signup_enabled": True,
            "checkout_configured": True,
            "customer_portal_configured": True,
            "webhook_configured": True,
            "key_delivery_configured": True,
            "ready_for_beta_key_delivery": True,
            "ready_for_beta_checkout": True,
            "ready_for_paid_key_delivery": True,
            "missing_configuration": [],
            "blocking_reasons": [],
            "operator_next_actions": [],
        },
    )


def test_stripe_status_keeps_paid_checkout_blocked_without_paid_price_ids(
    monkeypatch,
) -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(success=True),
        enabled=True,
        paid_packages_configured=False,
    )
    delivery = RecordingDeliveryService(enabled=True)
    monkeypatch.setattr(settings, "hosted_beta_signup_enabled", True)
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    app.dependency_overrides[get_stripe_customer_portal_service] = lambda: (
        RecordingStripeCustomerPortalService(
            StripeCustomerPortalResult(success=True), enabled=False
        )
    )
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: "whsec_test"
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    client = TestClient(app)

    response = client.get("/v1/billing/stripe/status")

    assert response.status_code == 200
    data = response.json()
    assert data["checkout_configured"] is True
    assert data["customer_portal_configured"] is False
    assert data["ready_for_beta_checkout"] is True
    assert data["ready_for_paid_key_delivery"] is False
    assert "stripe_customer_portal" in data["missing_configuration"]
    assert "Stripe Customer Portal is not configured." in data["blocking_reasons"]
    assert (
        "Configure STRIPE_PORTAL_RETURN_URL for customer billing management."
        in data["operator_next_actions"]
    )
    assert "stripe_paid_price_ids" in data["missing_configuration"]
    assert "Stripe paid package price IDs are not configured." in data["blocking_reasons"]
    assert "Configure Stripe price IDs for public paid packages." in data["operator_next_actions"]


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
    _assert_status_subset(
        response.json(),
        {
            "beta_signup_enabled": True,
            "checkout_configured": False,
            "webhook_configured": False,
            "key_delivery_configured": False,
            "ready_for_beta_key_delivery": False,
            "ready_for_beta_checkout": False,
            "ready_for_paid_key_delivery": False,
            "missing_configuration": [
                "stripe_checkout",
                "stripe_customer_portal",
                "stripe_webhook_secret",
                "hosted_key_delivery_smtp",
            ],
            "blocking_reasons": [
                "Stripe Checkout is not configured.",
                "Stripe Customer Portal is not configured.",
                "Stripe webhook secret is not configured.",
                "Hosted API-key email delivery is not configured.",
            ],
            "operator_next_actions": [
                "Configure Stripe secret key, price IDs, success URL, and cancel URL.",
                "Configure STRIPE_PORTAL_RETURN_URL for customer billing management.",
                "Configure STRIPE_WEBHOOK_SECRET from the signed Stripe endpoint.",
                "Configure hosted API-key SMTP delivery settings.",
            ],
        },
    )


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
    assert data["credit_policy"] == [
        {
            "action": "scrape",
            "credit_type": "standard",
            "credits_per_unit": 1,
            "metered_unit": "request",
            "included_in_standard_1000": 1000,
            "customer_description": "Fetch one public URL and return the requested hosted scrape formats.",
        },
        {
            "action": "crawl_page",
            "credit_type": "standard",
            "credits_per_unit": 1,
            "metered_unit": "returned page",
            "included_in_standard_1000": 1000,
            "customer_description": "Return one discovered crawl/map page within hosted plan limits.",
        },
        {
            "action": "screenshot",
            "credit_type": "standard",
            "credits_per_unit": 3,
            "metered_unit": "screenshot",
            "included_in_standard_1000": 333,
            "customer_description": "Capture one screenshot artifact for a public URL.",
        },
        {
            "action": "browser_render",
            "credit_type": "browser",
            "credits_per_unit": 5,
            "metered_unit": "browser render",
            "included_in_standard_1000": 0,
            "customer_description": "Run one hosted browser render when browser credits are enabled.",
        },
        {
            "action": "browser_minute",
            "credit_type": "browser",
            "credits_per_unit": 10,
            "metered_unit": "browser minute",
            "included_in_standard_1000": 0,
            "customer_description": "Consume one minute of hosted browser execution when browser credits are enabled.",
        },
    ]
    assert data["unit_economics"]["standard_1000"]["gross_margin_percent"] == 74.1
    assert data["unit_economics"]["standard_1000"]["break_even_packages_per_month"] == 17
    assert data["unit_economics_assumptions"] == {
        "fixed_monthly_cost_cents": 12000,
        "standard_credit_cost_cents": 0.15,
        "browser_credit_cost_cents": 2.0,
        "allocated_support_cost_cents": 50,
        "payment_percent_fee": 2.9,
        "payment_fixed_fee_cents": 30,
        "target_gross_margin_percent": 70.0,
    }
    assert "sk_" not in response.text
    assert "whsec_" not in response.text


def test_beta_trial_checkout_uses_stripe_setup_mode_without_payment_only_customer_creation() -> (
    None
):
    transport = RecordingStripeTransport()
    service = StripeCheckoutService(
        StripeCheckoutConfig(
            secret_key="sk_test_redacted",
            success_url="https://scout.chowmes.com/pricing?checkout=success",
            cancel_url="https://scout.chowmes.com/pricing?checkout=cancelled",
        ),
        transport=transport,
    )

    result = service.create_checkout_session(
        StripeCheckoutRequest(
            email="beta@example.com",
            name="Beta Tester",
            package_id="beta_trial",
        )
    )

    assert result.success is True
    assert transport.data[0] == {
        "mode": "setup",
        "payment_method_types[0]": "card",
        "success_url": "https://scout.chowmes.com/pricing?checkout=success",
        "cancel_url": "https://scout.chowmes.com/pricing?checkout=cancelled",
        "metadata[package_id]": "beta_trial",
        "metadata[plan]": "hosted_beta_pass",
        "metadata[product]": "scout_hosted",
        "customer_email": "beta@example.com",
        "metadata[name]": "Beta Tester",
    }
    assert "customer_creation" not in transport.data[0]
    assert transport.headers[0]["Authorization"] == "Bearer sk_test_redacted"


def test_paid_checkout_uses_payment_mode_price_line_item_and_customer_creation() -> None:
    transport = RecordingStripeTransport()
    service = StripeCheckoutService(
        StripeCheckoutConfig(
            secret_key="sk_test_redacted",
            standard_1000_price_id="price_standard_1000",
            success_url="https://scout.chowmes.com/pricing?checkout=success",
            cancel_url="https://scout.chowmes.com/pricing?checkout=cancelled",
        ),
        transport=transport,
    )

    result = service.create_checkout_session(
        StripeCheckoutRequest(
            email="buyer@example.com",
            name="Buyer Person",
            package_id="standard_1000",
        )
    )

    assert result.success is True
    assert transport.data[0] == {
        "mode": "payment",
        "customer_creation": "always",
        "line_items[0][price]": "price_standard_1000",
        "line_items[0][quantity]": "1",
        "success_url": "https://scout.chowmes.com/pricing?checkout=success",
        "cancel_url": "https://scout.chowmes.com/pricing?checkout=cancelled",
        "metadata[package_id]": "standard_1000",
        "metadata[plan]": "hosted_beta_pass",
        "metadata[product]": "scout_hosted",
        "customer_email": "buyer@example.com",
        "metadata[name]": "Buyer Person",
    }


def test_customer_portal_route_returns_stripe_portal_for_authenticated_customer(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_service = HostedPaymentProvisioningService(
        account_service,
        SQLiteHostedPaymentStore(db_path),
    )
    provisioned = payment_service.process_checkout(
        _checkout(
            checkout_session_id="cs_portal_customer",
            email="buyer@example.com",
            package_id="standard_1000",
            amount_total_cents=1000,
            customer_id="cus_portal_customer",
        )
    )
    portal_service = RecordingStripeCustomerPortalService(
        StripeCustomerPortalResult(
            success=True,
            portal_session_id="bps_test_123",
            portal_url="https://billing.stripe.com/p/session/test_123",
        )
    )
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_payment_provisioning_service] = lambda: payment_service
    app.dependency_overrides[get_stripe_customer_portal_service] = lambda: portal_service
    client = TestClient(app)

    response = client.post(
        "/v1/billing/stripe/customer-portal-session",
        headers={"Authorization": f"Bearer {provisioned.raw_api_key}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "portal_session_id": "bps_test_123",
        "portal_url": "https://billing.stripe.com/p/session/test_123",
        "reason": "",
    }
    assert portal_service.requests == ["cus_portal_customer"]
    assert provisioned.raw_api_key not in response.text
    assert "sk_" not in response.text


def test_customer_portal_route_requires_a_stripe_customer_id(tmp_path: Path) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_service = HostedPaymentProvisioningService(
        account_service,
        SQLiteHostedPaymentStore(db_path),
    )
    provisioned = payment_service.process_checkout(
        _checkout(
            checkout_session_id="cs_no_customer",
            email="buyer@example.com",
            package_id="standard_1000",
            amount_total_cents=1000,
            customer_id="",
        )
    )
    portal_service = RecordingStripeCustomerPortalService(
        StripeCustomerPortalResult(
            success=True,
            portal_session_id="bps_should_not_exist",
            portal_url="https://billing.stripe.com/p/session/should-not-exist",
        )
    )
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_payment_provisioning_service] = lambda: payment_service
    app.dependency_overrides[get_stripe_customer_portal_service] = lambda: portal_service
    client = TestClient(app)

    response = client.post(
        "/v1/billing/stripe/customer-portal-session",
        headers={"Authorization": f"Bearer {provisioned.raw_api_key}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "No Stripe customer is linked to this hosted account."
    assert portal_service.requests == []


def _client(
    service: object,
    *,
    webhook_secret: str = "whsec_test",
    delivery_enabled: bool = True,
    account_service: HostedAccountService | None = None,
) -> TestClient:
    """Build a test client with the checkout service dependency overridden."""
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: webhook_secret
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: RecordingDeliveryService(
        delivery_enabled
    )
    app.dependency_overrides[get_hosted_account_service] = lambda: (
        account_service or HostedAccountService(InMemoryHostedAccountStore())
    )
    return TestClient(app)


def _assert_status_subset(actual: dict[str, object], expected: dict[str, object]) -> None:
    """Assert important readiness fields while allowing additive status metadata."""
    assert {key: actual.get(key) for key in expected} == expected


class RecordingStripeCheckoutService:
    """Record checkout requests and return a deterministic result."""

    def __init__(
        self,
        result: StripeCheckoutResult,
        enabled: bool = True,
        paid_packages_configured: bool = True,
    ) -> None:
        self.result = result
        self.enabled = enabled
        self.paid_packages_configured = paid_packages_configured
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


class RecordingStripeCustomerPortalService:
    """Record Stripe Customer Portal requests and return a deterministic result."""

    def __init__(self, result: StripeCustomerPortalResult, enabled: bool = True) -> None:
        self.result = result
        self.enabled = enabled
        self.requests: list[str] = []

    def create_portal_session(
        self,
        request: StripeCustomerPortalRequest,
    ) -> StripeCustomerPortalResult:
        self.requests.append(request.customer_id)
        return self.result


class RecordingDeliveryService:
    """Expose only delivery readiness for Stripe status tests."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled


class RecordingStripeTransport:
    """Capture Stripe form posts without making network calls."""

    def __init__(self) -> None:
        self.urls: list[str] = []
        self.data: list[dict[str, str]] = []
        self.headers: list[dict[str, str]] = []

    def post_form(
        self,
        url: str,
        data: dict[str, str],
        headers: dict[str, str],
    ) -> StripeCheckoutSession:
        self.urls.append(url)
        self.data.append(data)
        self.headers.append(headers)
        return StripeCheckoutSession(
            id="cs_test_payload",
            url="https://checkout.stripe.com/c/pay/cs_test_payload",
        )


def _checkout(
    *,
    checkout_session_id: str,
    email: str,
    package_id: str,
    amount_total_cents: int,
    customer_id: str,
) -> HostedCheckoutProvisioningRequest:
    return HostedCheckoutProvisioningRequest(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id=checkout_session_id,
        customer_id=customer_id,
        payment_intent_id=f"pi_{checkout_session_id}",
        email=email,
        package_id=package_id,
        amount_total_cents=amount_total_cents,
        currency="usd",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
        status=HostedCheckoutPaymentStatus.PAID,
    )
