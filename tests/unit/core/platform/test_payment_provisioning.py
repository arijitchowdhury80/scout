"""Tests for hosted payment provisioning.

# Scenario list:
# - paid beta checkout creates a hosted account and stores the checkout event
# - duplicate checkout processing is idempotent and does not reprint the raw API key
# - unpaid checkout is rejected without provisioning an account
# - wrong amount or currency is rejected without provisioning an account
# - stored payment/account data never contains the raw API key
# - saved checkout event can be read back by a fresh SQLite payment store
"""

from __future__ import annotations

from pathlib import Path

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


def test_process_checkout_paid_beta_pass_provisions_hosted_account(tmp_path: Path) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(account_service, payment_store)

    result = service.process_checkout(_paid_beta_checkout())
    auth = account_service.authenticate_key(result.raw_api_key, required_scope="runs:create")
    stored_event = payment_store.get_checkout(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id="cs_test_beta_001",
    )

    assert result.success is True
    assert result.already_processed is False
    assert result.raw_api_key.startswith("scout_live_")
    assert result.plan is HostedPlan.HOSTED_BETA_PASS
    assert auth.allowed is True
    assert stored_event is not None
    assert stored_event.tenant_id == result.tenant_id
    assert stored_event.key_id == result.key_id
    assert result.raw_api_key not in db_path.read_text(encoding="utf-8", errors="ignore")


def test_process_checkout_duplicate_session_is_idempotent_without_raw_key_reprint(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    service = HostedPaymentProvisioningService(
        HostedAccountService(SQLiteHostedAccountStore(db_path)),
        SQLiteHostedPaymentStore(db_path),
    )

    first = service.process_checkout(_paid_beta_checkout())
    second = service.process_checkout(_paid_beta_checkout())

    assert first.success is True
    assert second.success is True
    assert second.already_processed is True
    assert second.tenant_id == first.tenant_id
    assert second.key_id == first.key_id
    assert second.raw_api_key == ""


def test_process_checkout_unpaid_session_is_rejected_without_provisioning(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(
        HostedAccountService(SQLiteHostedAccountStore(db_path)),
        payment_store,
    )

    result = service.process_checkout(
        _paid_beta_checkout(status=HostedCheckoutPaymentStatus.UNPAID)
    )
    stored_event = payment_store.get_checkout(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id="cs_test_beta_001",
    )

    assert result.success is False
    assert result.reason == "Checkout session is not paid."
    assert result.raw_api_key == ""
    assert stored_event is None


def test_process_checkout_wrong_amount_is_rejected_without_provisioning(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(
        HostedAccountService(SQLiteHostedAccountStore(db_path)),
        payment_store,
    )

    result = service.process_checkout(_paid_beta_checkout(amount_total_cents=1))
    stored_event = payment_store.get_checkout(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id="cs_test_beta_001",
    )

    assert result.success is False
    assert result.reason == "Expected checkout amount 2200 usd for hosted_beta_pass."
    assert result.raw_api_key == ""
    assert stored_event is None


def test_process_checkout_wrong_currency_is_rejected_without_provisioning(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(
        HostedAccountService(SQLiteHostedAccountStore(db_path)),
        payment_store,
    )

    result = service.process_checkout(_paid_beta_checkout(currency="eur"))

    assert result.success is False
    assert result.reason == "Expected checkout amount 2200 usd for hosted_beta_pass."
    assert result.raw_api_key == ""


def test_sqlite_payment_store_persists_checkout_event_for_fresh_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    service = HostedPaymentProvisioningService(
        HostedAccountService(SQLiteHostedAccountStore(db_path)),
        SQLiteHostedPaymentStore(db_path),
    )
    result = service.process_checkout(_paid_beta_checkout())

    fresh_store = SQLiteHostedPaymentStore(db_path)
    stored_event = fresh_store.get_checkout(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id="cs_test_beta_001",
    )

    assert stored_event is not None
    assert stored_event.tenant_id == result.tenant_id
    assert stored_event.amount_total_cents == 2200
    assert stored_event.currency == "usd"
    assert stored_event.plan is HostedPlan.HOSTED_BETA_PASS


def _paid_beta_checkout(
    *,
    amount_total_cents: int = 2200,
    currency: str = "usd",
    status: HostedCheckoutPaymentStatus = HostedCheckoutPaymentStatus.PAID,
) -> HostedCheckoutProvisioningRequest:
    """Build a valid hosted beta checkout request for tests."""
    return HostedCheckoutProvisioningRequest(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id="cs_test_beta_001",
        customer_id="cus_test_001",
        payment_intent_id="pi_test_001",
        email="builder@example.com",
        amount_total_cents=amount_total_cents,
        currency=currency,
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
        status=status,
    )
