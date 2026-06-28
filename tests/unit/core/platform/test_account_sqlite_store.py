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
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )

    second_service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    auth = second_service.authenticate_key(provisioned.raw_api_key, required_scope="runs:create")
    balance = second_service.get_balance(provisioned.tenant.tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)

    assert auth.allowed is True
    assert auth.tenant_id == provisioned.tenant.tenant_id
    assert auth.key_id == provisioned.api_key.key_id
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
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)

    assert decision.allowed is True
    assert balance.standard_credits_remaining == limits.standard_credits
    assert balance.browser_credits_remaining == (
        limits.browser_credits - HostedAction.BROWSER_RENDER.credit_cost
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
