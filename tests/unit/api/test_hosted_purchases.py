"""Tests for hosted purchase-history endpoint."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scout.api.deps import (
    get_hosted_account_service,
    get_hosted_payment_provisioning_service,
)
from scout.api.main import app
from scout.core.platform.account_service import HostedAccountService
from scout.core.platform.account_sqlite_store import SQLiteHostedAccountStore
from scout.core.platform.hosted import HostedPlan
from scout.core.platform.hosted import HostedAction
from scout.core.platform.payment_provisioning import (
    HostedCheckoutPaymentStatus,
    HostedCheckoutProvisioningRequest,
    HostedPaymentProvider,
    HostedPaymentProvisioningService,
    SQLiteHostedPaymentStore,
)


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()


def test_hosted_purchase_history_returns_only_authenticated_tenant_records(
    tmp_path: Path,
) -> None:
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
    second = payment_service.process_checkout(
        _checkout(
            checkout_session_id="cs_second",
            email="second@example.com",
            package_id="standard_3000",
            amount_total_cents=2500,
        )
    )
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_payment_provisioning_service] = lambda: payment_service
    client = TestClient(app)

    response = client.get(
        "/v1/hosted/purchases",
        headers={"Authorization": f"Bearer {first.raw_api_key}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["purchases"][0]["checkout_session_id"] == "cs_first"
    assert data["purchases"][0]["package_id"] == "standard_1000"
    assert data["purchases"][0]["amount_total_cents"] == 1000
    assert data["purchases"][0]["currency"] == "usd"
    assert data["purchases"][0]["tenant_id"] == first.tenant_id
    assert data["purchases"][0]["key_id"] == first.key_id
    assert "cs_second" not in response.text
    assert second.raw_api_key not in response.text
    assert first.raw_api_key not in response.text


def test_hosted_purchase_history_requires_bearer_token(tmp_path: Path) -> None:
    db_path = tmp_path / "hosted.sqlite"
    app.dependency_overrides[get_hosted_account_service] = lambda: HostedAccountService(
        SQLiteHostedAccountStore(db_path)
    )
    app.dependency_overrides[get_hosted_payment_provisioning_service] = lambda: (
        HostedPaymentProvisioningService(
            HostedAccountService(SQLiteHostedAccountStore(db_path)),
            SQLiteHostedPaymentStore(db_path),
        )
    )
    client = TestClient(app)

    response = client.get("/v1/hosted/purchases")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing Bearer token"


def test_hosted_me_returns_usage_and_purchase_monitoring_summary(tmp_path: Path) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_service = HostedPaymentProvisioningService(
        account_service,
        SQLiteHostedPaymentStore(db_path),
    )
    provisioned = payment_service.process_checkout(
        _checkout(
            checkout_session_id="cs_summary",
            email="summary@example.com",
            package_id="standard_1000",
            amount_total_cents=1000,
        )
    )
    account_service.debit_standard_credits(
        tenant_id=provisioned.tenant_id,
        key_id=provisioned.key_id,
        action=HostedAction.SCRAPE,
        credits=1,
    )
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    app.dependency_overrides[get_hosted_payment_provisioning_service] = lambda: payment_service
    client = TestClient(app)

    response = client.get(
        "/v1/hosted/me",
        headers={"Authorization": f"Bearer {provisioned.raw_api_key}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["usage_summary"] == {
        "total_events": 1,
        "standard_credits_used": 1,
        "browser_credits_used": 0,
        "usage_url": "/v1/hosted/usage",
    }
    assert data["purchase_summary"] == {
        "total_purchases": 1,
        "total_amount_cents": 1000,
        "currency": "usd",
        "last_package_id": "standard_1000",
        "purchases_url": "/v1/hosted/purchases",
    }
    assert data["links"] == {
        "usage": "/v1/hosted/usage",
        "purchases": "/v1/hosted/purchases",
        "billing_portal": "/v1/billing/stripe/customer-portal-session",
        "docs": "https://scout.chowmes.com/docs",
        "pricing": "https://scout.chowmes.com/pricing",
    }
    assert provisioned.raw_api_key not in response.text


def test_hosted_usage_history_returns_charge_and_balance_after_for_customer_metering(
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
            checkout_session_id="cs_usage_metering",
            email="usage@example.com",
            package_id="standard_1000",
            amount_total_cents=1000,
        )
    )
    account_service.debit_standard_credits(
        tenant_id=provisioned.tenant_id,
        key_id=provisioned.key_id,
        action=HostedAction.SCRAPE,
        credits=3,
        metadata={"target_url": "https://example.com"},
    )
    app.dependency_overrides[get_hosted_account_service] = lambda: account_service
    client = TestClient(app)

    response = client.get(
        "/v1/hosted/usage",
        headers={"Authorization": f"Bearer {provisioned.raw_api_key}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    usage = data["usage"][0]
    assert usage["action"] == "scrape"
    assert usage["credit_type"] == "standard"
    assert usage["credits"] == 3
    assert usage["standard_balance_after"] == 997
    assert usage["browser_balance_after"] == 0
    assert usage["metadata"] == {"target_url": "https://example.com"}
    assert provisioned.raw_api_key not in response.text


def _checkout(
    *,
    checkout_session_id: str,
    email: str,
    package_id: str,
    amount_total_cents: int,
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
        status=HostedCheckoutPaymentStatus.PAID,
    )
