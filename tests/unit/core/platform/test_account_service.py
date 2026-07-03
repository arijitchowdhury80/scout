"""Tests for hosted account provisioning and usage admission."""

from __future__ import annotations

import pytest

from scout.core.platform.account_service import (
    HostedAccountService,
    HostedAccountStatus,
    InMemoryHostedAccountStore,
)
from scout.core.platform.api_keys import ApiKeyStatus, verify_api_key
from scout.core.platform.hosted import HostedAction, HostedPlan, plan_limits


def test_provision_account_creates_tenant_key_and_plan_credits() -> None:
    service = HostedAccountService(InMemoryHostedAccountStore())

    result = service.provision_account(
        email="builder@example.com",
        name="Builder Person",
        plan=HostedPlan.HOSTED_BETA_PASS,
        key_name="Beta key",
        scopes=["runs:create"],
    )

    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    assert result.raw_api_key.startswith("scout_live_")
    assert result.tenant.email == "builder@example.com"
    assert result.tenant.name == "Builder Person"
    assert result.tenant.status is HostedAccountStatus.ACTIVE
    assert result.balance.standard_credits_remaining == limits.standard_credits
    assert result.balance.browser_credits_remaining == limits.browser_credits
    assert result.api_key.name == "Beta key"
    assert result.api_key.scopes == ["runs:create"]
    assert result.raw_api_key not in result.api_key.model_dump_json()
    assert verify_api_key(result.raw_api_key, result.api_key.key_hash)


def test_provision_account_rejects_local_free_for_hosted() -> None:
    service = HostedAccountService(InMemoryHostedAccountStore())

    with pytest.raises(ValueError, match="not hosted-enabled"):
        service.provision_account(
            email="local@example.com",
            plan=HostedPlan.LOCAL_FREE,
            scopes=["runs:create"],
        )


def test_authenticate_key_rejects_wrong_scope() -> None:
    service = HostedAccountService(InMemoryHostedAccountStore())
    result = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )

    decision = service.authenticate_key(result.raw_api_key, required_scope="admin:keys")

    assert decision.allowed is False
    assert decision.reason == "API key does not have required scope: admin:keys."
    assert decision.tenant_id == result.tenant.tenant_id
    assert decision.key_id == result.api_key.key_id


def test_authenticate_key_rejects_revoked_key() -> None:
    store = InMemoryHostedAccountStore()
    service = HostedAccountService(store)
    result = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    store.update_key_status(result.api_key.key_id, ApiKeyStatus.REVOKED)

    decision = service.authenticate_key(result.raw_api_key, required_scope="runs:create")

    assert decision.allowed is False
    assert decision.reason == "API key is not active."


def test_disable_api_key_rejects_future_authentication() -> None:
    service = HostedAccountService(InMemoryHostedAccountStore())
    result = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )

    service.disable_api_key(result.api_key.key_id)
    decision = service.authenticate_key(result.raw_api_key, required_scope="runs:create")

    assert decision.allowed is False
    assert decision.reason == "API key is not active."
    assert decision.tenant_id == result.tenant.tenant_id
    assert decision.key_id == result.api_key.key_id


def test_disable_account_disables_tenant_and_key_authentication() -> None:
    store = InMemoryHostedAccountStore()
    service = HostedAccountService(store)
    result = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )

    service.disable_account(result.tenant.tenant_id)
    decision = service.authenticate_key(result.raw_api_key, required_scope="runs:create")
    tenant = service.get_tenant(result.tenant.tenant_id)

    assert decision.allowed is False
    assert decision.reason == "API key is not active."
    assert tenant is not None
    assert tenant.status is HostedAccountStatus.DISABLED
    assert store.api_keys[result.api_key.key_id].status is ApiKeyStatus.DISABLED


def test_consume_action_debits_standard_and_denies_browser_when_beta_has_no_browser_credits() -> (
    None
):
    service = HostedAccountService(InMemoryHostedAccountStore())
    result = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )

    standard = service.consume_action(
        result.raw_api_key,
        HostedAction.SCRAPE,
        required_scope="runs:create",
    )
    browser = service.consume_action(
        result.raw_api_key,
        HostedAction.BROWSER_RENDER,
        required_scope="runs:create",
    )
    balance = service.get_balance(result.tenant.tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)

    assert standard.allowed is True
    assert browser.allowed is False
    assert browser.reason == "Insufficient browser credits: need 5, have 0."
    assert (
        balance.standard_credits_remaining
        == limits.standard_credits - HostedAction.SCRAPE.credit_cost
    )
    assert balance.browser_credits_remaining == limits.browser_credits
    entries = service.list_usage(result.tenant.tenant_id)
    assert len(entries) == 1
    assert entries[0].action == HostedAction.SCRAPE.value
    assert entries[0].key_id == result.api_key.key_id
    assert entries[0].credit_type == "standard"
    assert entries[0].credits == 1
    assert entries[0].standard_balance_after == limits.standard_credits - 1
    assert entries[0].browser_balance_after == limits.browser_credits


def test_consume_action_denies_without_mutating_when_credits_insufficient() -> None:
    service = HostedAccountService(InMemoryHostedAccountStore())
    result = service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    service.set_balance(result.tenant.tenant_id, standard_credits=1, browser_credits=0)

    decision = service.consume_action(
        result.raw_api_key,
        HostedAction.BROWSER_RENDER,
        required_scope="runs:create",
    )
    balance = service.get_balance(result.tenant.tenant_id)

    assert decision.allowed is False
    assert decision.reason == "Insufficient browser credits: need 5, have 0."
    assert balance.standard_credits_remaining == 1
    assert balance.browser_credits_remaining == 0


def test_delete_account_removes_tenant_key_and_balance() -> None:
    store = InMemoryHostedAccountStore()
    service = HostedAccountService(store)
    result = service.provision_account(
        email="rollback@example.com",
        name="Rollback User",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )

    service.delete_account(result.tenant.tenant_id)

    assert store.find_tenant_by_email("rollback@example.com") is None
    assert (
        service.authenticate_key(result.raw_api_key, required_scope="runs:create").allowed is False
    )
