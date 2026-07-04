"""Tests for hosted billing/admin monitoring metrics."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scout.api.config import settings
from scout.api.deps import (
    get_hosted_account_service,
    get_hosted_key_delivery_service,
    get_hosted_payment_provisioning_service,
)
from scout.api.main import app
from scout.core.platform.account_service import HostedAccountService, HostedSignupEvent
from scout.core.platform.account_sqlite_store import SQLiteHostedAccountStore
from scout.core.platform.hosted import HostedAction, HostedPlan
from scout.core.platform.key_delivery import (
    HostedApiKeyDeliveryRequest,
    HostedApiKeyDeliveryResult,
)
from scout.core.platform.payment_provisioning import (
    HostedCheckoutPaymentStatus,
    HostedCheckoutProvisioningRequest,
    HostedPaymentProvider,
    HostedPaymentProvisioningService,
    SQLiteHostedPaymentStore,
)


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


def test_billing_admin_metrics_requires_service_api_key(tmp_path: Path) -> None:
    account_service, payment_service, _raw_key = _seed_services(tmp_path)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_payment_provisioning_service] = lambda: payment_service
    client = TestClient(app)

    response = client.get("/v1/billing/admin/metrics")

    assert response.status_code == 403
    assert response.json()["detail"] == "Unauthorized"


def test_billing_admin_metrics_returns_non_secret_metering_summary(tmp_path: Path) -> None:
    account_service, payment_service, raw_key = _seed_services(tmp_path)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_payment_provisioning_service] = lambda: payment_service
    client = TestClient(app)

    response = client.get(
        "/v1/billing/admin/metrics",
        headers={"X-API-Key": settings.scout_api_key},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["totals"]["accounts"] == 2
    assert data["totals"]["active_accounts"] == 2
    assert data["totals"]["usage_events"] == 1
    assert data["totals"]["signup_events"] == 4
    assert data["totals"]["signup_delivered"] == 1
    assert data["totals"]["signup_failed"] == 1
    assert data["totals"]["signup_reissued"] == 1
    assert data["totals"]["signup_pending_delivery_events"] == 1
    assert data["totals"]["signup_pending_delivery"] == 1
    assert data["totals"]["standard_credits_used"] == 2
    assert data["totals"]["browser_credits_used"] == 0
    assert data["totals"]["purchases"] == 2
    assert data["totals"]["revenue_cents"] == 1000
    assert data["funnel"] == {
        "beta_registration_events": 3,
        "beta_delivered_keys": 1,
        "beta_pending_delivery": 1,
        "beta_failed_delivery": 1,
        "beta_reissued_keys": 1,
        "active_accounts": 2,
        "beta_trial_checkouts": 1,
        "paid_purchases": 1,
        "paid_customers": 1,
        "signup_delivery_rate_percent": 33.3,
        "paid_account_conversion_percent": 50.0,
    }
    assert data["economics"] == {
        "revenue_cents": 1000,
        "estimated_package_loaded_cost_cents": 324,
        "estimated_package_gross_profit_cents": 676,
        "estimated_package_gross_margin_percent": 67.6,
        "standard_credits_used": 2,
        "browser_credits_used": 0,
        "standard_1000_break_even_packages_per_month": 17,
        "target_gross_margin_percent": 70.0,
    }
    assert data["metric_scope"] == {
        "scope": "recent_window",
        "totals_are_complete": False,
        "totals_note": (
            "Totals, funnel, and economics are calculated from recent bounded rows, "
            "not full lifetime aggregates."
        ),
        "accounts_limit": 100,
        "accounts_returned": 2,
        "accounts_may_be_truncated": False,
        "signup_events_limit": 100,
        "signup_events_returned": 4,
        "signup_events_may_be_truncated": False,
        "usage_limit": 500,
        "usage_returned": 1,
        "usage_may_be_truncated": False,
        "purchases_limit": 100,
        "purchases_returned": 2,
        "purchases_may_be_truncated": False,
    }
    assert data["recent_accounts"][0]["email"] in {
        "first@example.com",
        "second@example.com",
    }
    assert data["recent_usage"][0]["action"] == "scrape"
    recent_by_email = {event["email"]: event for event in data["recent_signup_events"]}
    assert recent_by_email["failed@example.com"]["status"] == "failed"
    assert recent_by_email["failed@example.com"]["reason"] == "SMTP delivery failed"
    assert recent_by_email["delivered@example.com"]["status"] == "delivered"
    assert recent_by_email["pending@example.com"]["status"] == "pending_delivery"
    assert data["recent_purchases"][0]["checkout_session_id"] in {"cs_first", "cs_second"}
    assert raw_key not in response.text
    assert "key_hash" not in response.text
    assert "scout_live_" not in response.text


def test_billing_admin_delivers_pending_beta_signups_without_exposing_raw_keys(
    tmp_path: Path,
) -> None:
    account_service, payment_service, _raw_key = _seed_services(tmp_path)
    delivery = FakeDeliveryService()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_payment_provisioning_service] = lambda: payment_service
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    client = TestClient(app)

    response = client.post(
        "/v1/billing/admin/deliver-pending-beta-keys",
        headers={"X-API-Key": settings.scout_api_key},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["attempted"] == 1
    assert data["delivered"] == 1
    assert data["failed"] == 0
    assert data["remaining_pending"] == 0
    assert data["results"][0]["email"] == "pending@example.com"
    assert data["results"][0]["status"] == "delivered"
    assert data["results"][0]["tenant_id"].startswith("tenant_")
    assert data["results"][0]["key_id"].startswith("key_")
    assert "raw_api_key" not in data["results"][0]
    assert delivery.requests[0].email == "pending@example.com"
    assert delivery.requests[0].name == "Pending Tester"
    assert delivery.requests[0].raw_api_key not in response.text
    assert "scout_live_" not in response.text
    assert account_service.find_tenant_by_email("pending@example.com") is not None
    latest_events = account_service.list_signup_events(limit=10)
    assert latest_events[0].email == "pending@example.com"
    assert latest_events[0].status == "delivered"
    assert latest_events[0].source == "admin_pending_beta_delivery"


def test_billing_admin_retries_failed_beta_signups_without_exposing_raw_keys(
    tmp_path: Path,
) -> None:
    account_service, payment_service, _raw_key = _seed_services(tmp_path)
    delivery = FakeDeliveryService()
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_payment_provisioning_service] = lambda: payment_service
    app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery
    client = TestClient(app)

    response = client.post(
        "/v1/billing/admin/retry-failed-beta-keys",
        headers={"X-API-Key": settings.scout_api_key},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["attempted"] == 1
    assert data["delivered"] == 1
    assert data["failed"] == 0
    assert data["remaining_failed"] == 0
    assert data["results"][0]["email"] == "failed@example.com"
    assert data["results"][0]["status"] == "delivered"
    assert data["results"][0]["tenant_id"].startswith("tenant_")
    assert data["results"][0]["key_id"].startswith("key_")
    assert "raw_api_key" not in data["results"][0]
    assert delivery.requests[0].email == "failed@example.com"
    assert delivery.requests[0].name == "Failed Tester"
    assert delivery.requests[0].raw_api_key not in response.text
    assert "scout_live_" not in response.text
    assert account_service.find_tenant_by_email("failed@example.com") is not None
    latest_events = account_service.list_signup_events(limit=10)
    assert latest_events[0].email == "failed@example.com"
    assert latest_events[0].status == "delivered"
    assert latest_events[0].source == "admin_failed_beta_delivery_retry"


def test_billing_admin_pending_beta_delivery_requires_email_delivery(
    tmp_path: Path,
) -> None:
    account_service, payment_service, _raw_key = _seed_services(tmp_path)
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_payment_provisioning_service] = lambda: payment_service
    client = TestClient(app)

    response = client.post(
        "/v1/billing/admin/deliver-pending-beta-keys",
        headers={"X-API-Key": settings.scout_api_key},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Hosted API key delivery is not configured."
    assert account_service.find_tenant_by_email("pending@example.com") is None


def _seed_services(
    tmp_path: Path,
) -> tuple[HostedAccountService, HostedPaymentProvisioningService, str]:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_service = HostedPaymentProvisioningService(
        account_service,
        SQLiteHostedPaymentStore(db_path),
    )
    first = payment_service.process_checkout(
        _checkout(
            checkout_session_id="cs_first",
            email="first@example.com",
            package_id="standard_1000",
            amount_total_cents=1000,
        )
    )
    payment_service.process_checkout(
        _checkout(
            checkout_session_id="cs_second",
            email="second@example.com",
            package_id="beta_trial",
            amount_total_cents=0,
            status=HostedCheckoutPaymentStatus.NO_PAYMENT_REQUIRED,
        )
    )
    account_service.debit_standard_credits(
        tenant_id=first.tenant_id,
        key_id=first.key_id,
        action=HostedAction.SCRAPE,
        credits=2,
    )
    account_service.record_signup_event(
        HostedSignupEvent(
            email="delivered@example.com",
            name="Delivered Tester",
            status="delivered",
            source="email_beta_registration",
            tenant_id=first.tenant_id,
            key_id=first.key_id,
            delivery_status="delivered",
        )
    )
    account_service.record_signup_event(
        HostedSignupEvent(
            email="failed@example.com",
            name="Failed Tester",
            status="failed",
            source="email_beta_registration",
            reason="SMTP delivery failed",
            delivery_status="failed",
        )
    )
    account_service.record_signup_event(
        HostedSignupEvent(
            email="pending@example.com",
            name="Pending Tester",
            status="pending_delivery",
            source="email_beta_registration",
            reason="SMTP delivery is not configured yet",
            delivery_status="pending_delivery",
        )
    )
    account_service.record_signup_event(
        HostedSignupEvent(
            email="recover@example.com",
            name="Recovery Tester",
            status="reissued",
            source="email_beta_key_reissue",
            tenant_id=first.tenant_id,
            key_id=first.key_id,
            delivery_status="delivered",
        )
    )
    return account_service, payment_service, first.raw_api_key


def _checkout(
    *,
    checkout_session_id: str,
    email: str,
    package_id: str,
    amount_total_cents: int,
    status: HostedCheckoutPaymentStatus = HostedCheckoutPaymentStatus.PAID,
) -> HostedCheckoutProvisioningRequest:
    return HostedCheckoutProvisioningRequest(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id=checkout_session_id,
        customer_id=f"cus_{checkout_session_id}",
        payment_intent_id=f"pi_{checkout_session_id}",
        email=email,
        package_id=package_id,
        amount_total_cents=amount_total_cents,
        currency="usd",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
        status=status,
    )


class FakeDeliveryService:
    """Fake hosted API-key delivery service for admin pending-delivery tests."""

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
