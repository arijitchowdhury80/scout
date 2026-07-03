"""Tests for durable hosted account SQLite persistence."""

from __future__ import annotations

from pathlib import Path

from scout.core.platform.account_service import HostedAccountService
from scout.core.platform.account_sqlite_store import SQLiteHostedAccountStore
from scout.core.platform.api_keys import ApiKeyStatus
from scout.core.platform.hosted import HostedAction, HostedPlan, plan_limits
from scout.core.platform.hosted_admission import HostedAdmissionService


def test_sqlite_store_persists_provisioned_account_without_raw_api_key(tmp_path: Path) -> None:
    db_path = tmp_path / "hosted.sqlite"
    first_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    provisioned = first_service.provision_account(
        email="builder@example.com",
        name="Builder Person",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )

    second_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    auth = second_service.authenticate_key(provisioned.raw_api_key, required_scope="runs:create")
    tenant = second_service.get_tenant(provisioned.tenant.tenant_id)
    balance = second_service.get_balance(provisioned.tenant.tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)

    assert auth.allowed is True
    assert auth.tenant_id == provisioned.tenant.tenant_id
    assert auth.key_id == provisioned.api_key.key_id
    assert tenant is not None
    assert tenant.name == "Builder Person"
    assert balance.standard_credits_remaining == limits.standard_credits
    assert balance.browser_credits_remaining == limits.browser_credits
    assert provisioned.raw_api_key not in db_path.read_text(encoding="utf-8", errors="ignore")


def test_sqlite_store_persists_admission_credit_debit(tmp_path: Path) -> None:
    db_path = tmp_path / "hosted.sqlite"
    first_account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    provisioned = first_account_service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )

    second_account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    decision = HostedAdmissionService(second_account_service).admit_url_action(
        raw_key=provisioned.raw_api_key,
        url="https://example.com/products",
        action=HostedAction.BROWSER_RENDER,
        required_scope="runs:create",
    )

    third_account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    balance = third_account_service.get_balance(provisioned.tenant.tenant_id)
    entries = third_account_service.list_usage(provisioned.tenant.tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)

    assert decision.allowed is False
    assert decision.reason == "Insufficient browser credits: need 5, have 0."
    assert balance.standard_credits_remaining == limits.standard_credits
    assert balance.browser_credits_remaining == limits.browser_credits
    assert entries == []


def test_sqlite_store_persists_credit_ledger_entries(tmp_path: Path) -> None:
    db_path = tmp_path / "hosted.sqlite"
    account_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    provisioned = account_service.provision_account(
        email="ledger@example.com",
        name="Ledger User",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )

    account_service.consume_action(
        provisioned.raw_api_key,
        HostedAction.SCRAPE,
        required_scope="runs:create",
    )
    fresh_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    entries = fresh_service.list_usage(provisioned.tenant.tenant_id)

    assert len(entries) == 1
    assert entries[0].tenant_id == provisioned.tenant.tenant_id
    assert entries[0].key_id == provisioned.api_key.key_id
    assert entries[0].action == "scrape"
    assert entries[0].credits == 1
    assert (
        entries[0].standard_balance_after
        == plan_limits(HostedPlan.HOSTED_BETA_PASS).standard_credits - 1
    )


def test_sqlite_store_persists_revoked_key_status(tmp_path: Path) -> None:
    db_path = tmp_path / "hosted.sqlite"
    store = SQLiteHostedAccountStore(db_path)
    service = HostedAccountService(store)
    provisioned = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    store.update_key_status(provisioned.api_key.key_id, ApiKeyStatus.REVOKED)

    fresh_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    decision = fresh_service.authenticate_key(
        provisioned.raw_api_key,
        required_scope="runs:create",
    )

    assert decision.allowed is False
    assert decision.reason == "API key is not active."


def test_sqlite_store_deletes_account_key_and_balance(tmp_path: Path) -> None:
    db_path = tmp_path / "hosted.sqlite"
    store = SQLiteHostedAccountStore(db_path)
    service = HostedAccountService(store)
    provisioned = service.provision_account(
        email="rollback@example.com",
        name="Rollback User",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )

    service.delete_account(provisioned.tenant.tenant_id)
    fresh_service = HostedAccountService(SQLiteHostedAccountStore(db_path))

    assert fresh_service.get_tenant(provisioned.tenant.tenant_id) is None
    assert (
        fresh_service.authenticate_key(
            provisioned.raw_api_key,
            required_scope="runs:create",
        ).allowed
        is False
    )
