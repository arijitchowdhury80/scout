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
