"""Tests for hosted billing/admin monitoring metrics."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scout.api.config import settings
from scout.api.deps import (
    get_hosted_account_service,
    get_hosted_payment_provisioning_service,
)
from scout.api.main import app
from scout.core.platform.account_service import HostedAccountService
from scout.core.platform.account_sqlite_store import SQLiteHostedAccountStore
from scout.core.platform.hosted import HostedAction, HostedPlan
from scout.core.platform.payment_provisioning import (
    HostedCheckoutPaymentStatus,
    HostedCheckoutProvisioningRequest,
    HostedPaymentProvider,
    HostedPaymentProvisioningService,
    SQLiteHostedPaymentStore,
)


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> None:
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
    assert data["totals"]["standard_credits_used"] == 2
    assert data["totals"]["browser_credits_used"] == 0
    assert data["totals"]["purchases"] == 2
    assert data["totals"]["revenue_cents"] == 1000
    assert data["recent_accounts"][0]["email"] in {
        "first@example.com",
        "second@example.com",
    }
    assert data["recent_usage"][0]["action"] == "scrape"
    assert data["recent_purchases"][0]["checkout_session_id"] in {"cs_first", "cs_second"}
    assert raw_key not in response.text
    assert "key_hash" not in response.text
    assert "scout_live_" not in response.text


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
