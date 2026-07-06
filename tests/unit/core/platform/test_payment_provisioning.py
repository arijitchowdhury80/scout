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
from scout.core.platform.hosted import HostedAction, HostedPlan
from scout.core.platform.payment_provisioning import (
    HostedCheckoutPaymentStatus,
    HostedCheckoutProvisioningRequest,
    HostedPaymentProvider,
    HostedPaymentProvisioningService,
    HostedSubscriptionDeletedRequest,
    HostedSubscriptionInvoiceRequest,
    SQLiteHostedPaymentStore,
)


def test_process_checkout_beta_trial_setup_provisions_trial_credits(tmp_path: Path) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(account_service, payment_store)

    result = service.process_checkout(_beta_trial_checkout())
    auth = account_service.authenticate_key(result.raw_api_key, required_scope="runs:create")
    balance = account_service.get_balance(result.tenant_id)
    stored_event = payment_store.get_checkout(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id="cs_test_beta_001",
    )

    assert result.success is True
    assert result.already_processed is False
    assert result.raw_api_key.startswith("scout_live_")
    assert result.plan is HostedPlan.HOSTED_BETA_PASS
    assert auth.allowed is True
    assert balance.standard_credits_remaining == 10000
    assert balance.browser_credits_remaining == 100
    assert stored_event is not None
    assert stored_event.package_id == "beta_trial"
    assert stored_event.amount_total_cents == 0
    assert stored_event.tenant_id == result.tenant_id
    assert stored_event.key_id == result.key_id
    assert account_service.get_tenant(result.tenant_id).name == "Builder Person"
    assert result.raw_api_key not in db_path.read_text(encoding="utf-8", errors="ignore")


def test_process_checkout_standard_1000_payment_provisions_1000_credits(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    service = HostedPaymentProvisioningService(
        account_service,
        SQLiteHostedPaymentStore(db_path),
    )

    result = service.process_checkout(_standard_1000_checkout())
    balance = account_service.get_balance(result.tenant_id)
    tenant = account_service.get_tenant(result.tenant_id)

    assert result.success is True
    assert result.plan is HostedPlan.HOSTED_STARTER
    assert tenant is not None
    assert tenant.plan is HostedPlan.HOSTED_STARTER
    assert balance.standard_credits_remaining == 10000
    assert balance.browser_credits_remaining == 0


def test_process_checkout_standard_15000_payment_provisions_pro_plan(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    service = HostedPaymentProvisioningService(
        account_service,
        SQLiteHostedPaymentStore(db_path),
    )

    result = service.process_checkout(
        _standard_15000_checkout(checkout_session_id="cs_test_pro_001")
    )
    balance = account_service.get_balance(result.tenant_id)
    tenant = account_service.get_tenant(result.tenant_id)

    assert result.success is True
    assert result.plan is HostedPlan.HOSTED_PRO
    assert tenant is not None
    assert tenant.plan is HostedPlan.HOSTED_PRO
    assert balance.standard_credits_remaining == 150000
    assert balance.browser_credits_remaining == 0


def test_process_checkout_standard_1000_tops_up_existing_beta_account_without_new_key(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(account_service, payment_store)
    beta = account_service.provision_account(
        email="builder@example.com",
        name="Builder Person",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
        key_name="Initial beta key",
    )
    account_service.set_balance(
        beta.tenant.tenant_id,
        standard_credits=75,
        browser_credits=0,
    )

    result = service.process_checkout(_standard_1000_checkout())
    balance = account_service.get_balance(beta.tenant.tenant_id)
    tenant = account_service.get_tenant(beta.tenant.tenant_id)
    stored_event = payment_store.get_checkout(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id="cs_test_beta_001",
    )

    assert result.success is True
    assert result.already_processed is False
    assert result.tenant_id == beta.tenant.tenant_id
    assert result.key_id == beta.api_key.key_id
    assert result.plan is HostedPlan.HOSTED_STARTER
    assert tenant is not None
    assert tenant.plan is HostedPlan.HOSTED_STARTER
    assert result.raw_api_key == ""
    assert balance.standard_credits_remaining == 10075
    assert balance.browser_credits_remaining == 0
    assert stored_event is not None
    assert stored_event.tenant_id == beta.tenant.tenant_id
    assert stored_event.key_id == beta.api_key.key_id
    assert stored_event.package_id == "standard_1000"


def test_process_checkout_beta_trial_for_existing_account_does_not_grant_extra_free_credits(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(account_service, payment_store)
    beta = account_service.provision_account(
        email="builder@example.com",
        name="Builder Person",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
        key_name="Initial beta key",
    )
    account_service.set_balance(
        beta.tenant.tenant_id,
        standard_credits=75,
        browser_credits=0,
    )

    result = service.process_checkout(
        _beta_trial_checkout(checkout_session_id="cs_test_beta_trial_repeat")
    )
    balance = account_service.get_balance(beta.tenant.tenant_id)
    stored_event = payment_store.get_checkout(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id="cs_test_beta_trial_repeat",
    )

    assert result.success is True
    assert result.already_processed is False
    assert result.tenant_id == beta.tenant.tenant_id
    assert result.key_id == beta.api_key.key_id
    assert result.raw_api_key == ""
    assert balance.standard_credits_remaining == 75
    assert balance.browser_credits_remaining == 0
    assert stored_event is not None
    assert stored_event.tenant_id == beta.tenant.tenant_id
    assert stored_event.key_id == beta.api_key.key_id
    assert stored_event.package_id == "beta_trial"


def test_process_checkout_duplicate_session_is_idempotent_without_raw_key_reprint(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    service = HostedPaymentProvisioningService(
        HostedAccountService(SQLiteHostedAccountStore(db_path)),
        SQLiteHostedPaymentStore(db_path),
    )

    first = service.process_checkout(_beta_trial_checkout())
    second = service.process_checkout(_beta_trial_checkout())

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
        _beta_trial_checkout(status=HostedCheckoutPaymentStatus.UNPAID)
    )
    stored_event = payment_store.get_checkout(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id="cs_test_beta_001",
    )

    assert result.success is False
    assert result.reason == "Checkout session is not complete for package beta_trial."
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

    result = service.process_checkout(_standard_1000_checkout(amount_total_cents=1))
    stored_event = payment_store.get_checkout(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id="cs_test_beta_001",
    )

    assert result.success is False
    assert result.reason == "Expected checkout amount 1000 usd for package standard_1000."
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

    result = service.process_checkout(_standard_1000_checkout(currency="eur"))

    assert result.success is False
    assert result.reason == "Expected checkout amount 1000 usd for package standard_1000."
    assert result.raw_api_key == ""


def test_sqlite_payment_store_persists_checkout_event_for_fresh_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    service = HostedPaymentProvisioningService(
        HostedAccountService(SQLiteHostedAccountStore(db_path)),
        SQLiteHostedPaymentStore(db_path),
    )
    result = service.process_checkout(_standard_1000_checkout())

    fresh_store = SQLiteHostedPaymentStore(db_path)
    stored_event = fresh_store.get_checkout(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id="cs_test_beta_001",
    )

    assert stored_event is not None
    assert stored_event.tenant_id == result.tenant_id
    assert stored_event.amount_total_cents == 1000
    assert stored_event.currency == "usd"
    assert stored_event.plan is HostedPlan.HOSTED_STARTER
    assert stored_event.package_id == "standard_1000"


def test_sqlite_payment_store_lists_checkout_purchase_records(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(account_service, payment_store)

    first = service.process_checkout(
        _standard_1000_checkout(
            checkout_session_id="cs_test_paid_001",
            email="paid@example.com",
        )
    )
    second = service.process_checkout(
        _beta_trial_checkout(
            checkout_session_id="cs_test_trial_001",
            email="trial@example.com",
        )
    )

    records = payment_store.list_checkouts(limit=10)

    assert [record.checkout_session_id for record in records] == [
        "cs_test_trial_001",
        "cs_test_paid_001",
    ]
    assert records[0].package_id == "beta_trial"
    assert records[0].amount_total_cents == 0
    assert records[0].tenant_id == second.tenant_id
    assert records[1].package_id == "standard_1000"
    assert records[1].amount_total_cents == 1000
    assert records[1].tenant_id == first.tenant_id
    assert first.raw_api_key not in db_path.read_text(encoding="utf-8", errors="ignore")
    assert second.raw_api_key not in db_path.read_text(encoding="utf-8", errors="ignore")


def test_process_checkout_unlimited_subscription_provisions_unlimited_plan(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(account_service, payment_store)

    result = service.process_checkout(
        _unlimited_subscription_checkout(checkout_session_id="cs_sub_001")
    )
    balance = account_service.get_balance(result.tenant_id)
    tenant = account_service.get_tenant(result.tenant_id)
    stored = payment_store.get_checkout(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id="cs_sub_001",
    )

    assert result.success is True
    assert result.plan is HostedPlan.HOSTED_UNLIMITED
    assert tenant is not None
    assert tenant.plan is HostedPlan.HOSTED_UNLIMITED
    assert balance.standard_credits_remaining == 50000
    assert balance.browser_credits_remaining == 0
    assert stored is not None
    assert stored.package_id == "unlimited_monthly"
    assert stored.customer_id == "cus_sub_001"
    assert stored.subscription_id == "sub_test_001"


def test_process_checkout_unlimited_upgrades_existing_beta_and_sets_credits(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(account_service, payment_store)
    beta = account_service.provision_account(
        email="builder@example.com",
        name="Builder Person",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
        key_name="Initial beta key",
    )
    account_service.set_balance(beta.tenant.tenant_id, standard_credits=42, browser_credits=7)

    result = service.process_checkout(
        _unlimited_subscription_checkout(checkout_session_id="cs_sub_002")
    )
    balance = account_service.get_balance(beta.tenant.tenant_id)
    tenant = account_service.get_tenant(beta.tenant.tenant_id)

    assert result.success is True
    assert result.tenant_id == beta.tenant.tenant_id
    assert result.plan is HostedPlan.HOSTED_UNLIMITED
    assert tenant is not None
    assert tenant.plan is HostedPlan.HOSTED_UNLIMITED
    # SET (not add): exactly 50000, browser bucket zeroed to the plan grant.
    assert balance.standard_credits_remaining == 50000
    assert balance.browser_credits_remaining == 0


def test_process_invoice_paid_resets_standard_credits_to_fifty_thousand(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(account_service, payment_store)
    checkout = service.process_checkout(
        _unlimited_subscription_checkout(checkout_session_id="cs_sub_003")
    )
    # Burn most of the month down to a partial balance.
    account_service.set_balance(checkout.tenant_id, standard_credits=12345, browser_credits=0)

    result = service.process_invoice_paid(_invoice(invoice_id="in_test_001"))
    balance = account_service.get_balance(checkout.tenant_id)

    assert result.success is True
    assert result.tenant_id == checkout.tenant_id
    # RESET, not add: 12345 -> 50000 exactly, NOT 62345.
    assert balance.standard_credits_remaining == 50000
    assert balance.browser_credits_remaining == 0


def test_process_invoice_paid_is_idempotent_per_invoice_id(tmp_path: Path) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(account_service, payment_store)
    checkout = service.process_checkout(
        _unlimited_subscription_checkout(checkout_session_id="cs_sub_004")
    )

    first = service.process_invoice_paid(_invoice(invoice_id="in_dup_001"))
    # Spend down again after the first reset.
    account_service.set_balance(checkout.tenant_id, standard_credits=3, browser_credits=0)
    second = service.process_invoice_paid(_invoice(invoice_id="in_dup_001"))
    balance = account_service.get_balance(checkout.tenant_id)

    assert first.success is True
    assert first.already_processed is False
    assert second.success is True
    assert second.already_processed is True
    # Replay must NOT re-reset; the second reset is suppressed, so balance stays at 3.
    assert balance.standard_credits_remaining == 3


def test_process_invoice_paid_persists_processed_id_across_fresh_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    service = HostedPaymentProvisioningService(account_service, SQLiteHostedPaymentStore(db_path))
    checkout = service.process_checkout(
        _unlimited_subscription_checkout(checkout_session_id="cs_sub_005")
    )
    service.process_invoice_paid(_invoice(invoice_id="in_persist_001"))
    account_service.set_balance(checkout.tenant_id, standard_credits=9, browser_credits=0)

    fresh = HostedPaymentProvisioningService(account_service, SQLiteHostedPaymentStore(db_path))
    replay = fresh.process_invoice_paid(_invoice(invoice_id="in_persist_001"))
    balance = account_service.get_balance(checkout.tenant_id)

    assert replay.already_processed is True
    assert balance.standard_credits_remaining == 9


def test_process_subscription_deleted_downgrades_and_zeros_grant(tmp_path: Path) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(account_service, payment_store)
    checkout = service.process_checkout(
        _unlimited_subscription_checkout(checkout_session_id="cs_sub_006")
    )

    result = service.process_subscription_deleted(_subscription_deleted())
    balance = account_service.get_balance(checkout.tenant_id)
    tenant = account_service.get_tenant(checkout.tenant_id)

    assert result.success is True
    assert result.tenant_id == checkout.tenant_id
    assert tenant is not None
    assert tenant.plan is not HostedPlan.HOSTED_UNLIMITED
    assert balance.standard_credits_remaining == 0
    assert balance.browser_credits_remaining == 0


def test_process_subscription_deleted_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(account_service, payment_store)
    checkout = service.process_checkout(
        _unlimited_subscription_checkout(checkout_session_id="cs_sub_007")
    )

    first = service.process_subscription_deleted(_subscription_deleted())
    # Operator grants some credits back manually; a replayed revoke must not re-zero.
    account_service.set_balance(checkout.tenant_id, standard_credits=5, browser_credits=0)
    second = service.process_subscription_deleted(_subscription_deleted())
    balance = account_service.get_balance(checkout.tenant_id)

    assert first.success is True
    assert first.already_processed is False
    assert second.already_processed is True
    assert balance.standard_credits_remaining == 5


def test_unlimited_subscriber_hard_stops_when_exhausted_until_next_invoice(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    payment_store = SQLiteHostedPaymentStore(db_path)
    service = HostedPaymentProvisioningService(account_service, payment_store)
    checkout = service.process_checkout(
        _unlimited_subscription_checkout(checkout_session_id="cs_sub_008")
    )
    account_service.set_balance(checkout.tenant_id, standard_credits=1, browser_credits=0)
    tenant = account_service.get_tenant(checkout.tenant_id)
    assert tenant is not None
    raw_key = account_service.issue_api_key_for_tenant(
        checkout.tenant_id, scopes=["runs:create"]
    ).raw_api_key

    first = account_service.consume_action(raw_key, HostedAction.SCRAPE, "runs:create")
    denied = account_service.consume_action(raw_key, HostedAction.SCRAPE, "runs:create")

    assert first.allowed is True
    assert denied.allowed is False
    assert account_service.get_balance(checkout.tenant_id).standard_credits_remaining == 0

    # Next invoice.paid refills the bucket back to the full monthly grant.
    service.process_invoice_paid(_invoice(invoice_id="in_refill_001"))
    refilled = account_service.consume_action(raw_key, HostedAction.SCRAPE, "runs:create")

    assert refilled.allowed is True
    assert account_service.get_balance(checkout.tenant_id).standard_credits_remaining == 49999


def _unlimited_subscription_checkout(
    *,
    checkout_session_id: str = "cs_sub_001",
    email: str = "builder@example.com",
    customer_id: str = "cus_sub_001",
    subscription_id: str = "sub_test_001",
) -> HostedCheckoutProvisioningRequest:
    """Build a valid unlimited-subscription checkout.session.completed request."""
    return HostedCheckoutProvisioningRequest(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id=checkout_session_id,
        customer_id=customer_id,
        subscription_id=subscription_id,
        payment_intent_id="",
        email=email,
        name="Builder Person",
        package_id="unlimited_monthly",
        amount_total_cents=1200,
        currency="usd",
        plan=HostedPlan.HOSTED_UNLIMITED,
        scopes=["runs:create"],
        status=HostedCheckoutPaymentStatus.PAID,
    )


def _invoice(
    *,
    invoice_id: str = "in_test_001",
    customer_id: str = "cus_sub_001",
    subscription_id: str = "sub_test_001",
) -> HostedSubscriptionInvoiceRequest:
    """Build a Stripe invoice.paid domain request for tests."""
    return HostedSubscriptionInvoiceRequest(
        provider=HostedPaymentProvider.STRIPE,
        invoice_id=invoice_id,
        customer_id=customer_id,
        subscription_id=subscription_id,
    )


def _subscription_deleted(
    *,
    customer_id: str = "cus_sub_001",
    subscription_id: str = "sub_test_001",
) -> HostedSubscriptionDeletedRequest:
    """Build a Stripe customer.subscription.deleted domain request for tests."""
    return HostedSubscriptionDeletedRequest(
        provider=HostedPaymentProvider.STRIPE,
        customer_id=customer_id,
        subscription_id=subscription_id,
    )


def _beta_trial_checkout(
    *,
    checkout_session_id: str = "cs_test_beta_001",
    email: str = "builder@example.com",
    amount_total_cents: int = 0,
    currency: str = "usd",
    status: HostedCheckoutPaymentStatus = HostedCheckoutPaymentStatus.NO_PAYMENT_REQUIRED,
) -> HostedCheckoutProvisioningRequest:
    """Build a valid hosted beta trial setup request for tests."""
    return _checkout(
        package_id="beta_trial",
        checkout_session_id=checkout_session_id,
        email=email,
        amount_total_cents=amount_total_cents,
        currency=currency,
        status=status,
    )


def _standard_1000_checkout(
    *,
    checkout_session_id: str = "cs_test_beta_001",
    email: str = "builder@example.com",
    amount_total_cents: int = 1000,
    currency: str = "usd",
    status: HostedCheckoutPaymentStatus = HostedCheckoutPaymentStatus.PAID,
) -> HostedCheckoutProvisioningRequest:
    """Build a valid paid standard credit package request for tests."""
    return _checkout(
        package_id="standard_1000",
        checkout_session_id=checkout_session_id,
        email=email,
        amount_total_cents=amount_total_cents,
        currency=currency,
        status=status,
    )


def _standard_15000_checkout(
    *,
    checkout_session_id: str = "cs_test_beta_001",
    email: str = "builder@example.com",
    amount_total_cents: int = 10000,
    currency: str = "usd",
    status: HostedCheckoutPaymentStatus = HostedCheckoutPaymentStatus.PAID,
) -> HostedCheckoutProvisioningRequest:
    """Build a valid paid pro-volume standard credit package request for tests."""
    return _checkout(
        package_id="standard_15000",
        checkout_session_id=checkout_session_id,
        email=email,
        amount_total_cents=amount_total_cents,
        currency=currency,
        status=status,
    )


def _checkout(
    *,
    package_id: str,
    checkout_session_id: str,
    email: str,
    amount_total_cents: int,
    currency: str,
    status: HostedCheckoutPaymentStatus,
) -> HostedCheckoutProvisioningRequest:
    """Build a hosted checkout request for tests."""
    return HostedCheckoutProvisioningRequest(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id=checkout_session_id,
        customer_id="cus_test_001",
        payment_intent_id="pi_test_001",
        email=email,
        name="Builder Person",
        package_id=package_id,
        amount_total_cents=amount_total_cents,
        currency=currency,
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
        status=status,
    )
