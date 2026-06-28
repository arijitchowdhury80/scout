"""Tests for hosted request admission decisions."""

from __future__ import annotations

from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.hosted import HostedAction, HostedPlan, plan_limits
from scout.core.platform.hosted_admission import HostedAdmissionService


def _service_with_key() -> tuple[HostedAdmissionService, HostedAccountService, str, str]:
    account_service = HostedAccountService(InMemoryHostedAccountStore())
    provisioned = account_service.provision_account(
        email="builder@example.com",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    return (
        HostedAdmissionService(account_service),
        account_service,
        provisioned.raw_api_key,
        provisioned.tenant.tenant_id,
    )


def test_admit_url_action_allows_safe_url_and_debits_credits() -> None:
    admission, account_service, raw_key, tenant_id = _service_with_key()

    decision = admission.admit_url_action(
        raw_key=raw_key,
        url="https://example.com/products",
        action=HostedAction.SCRAPE,
        required_scope="runs:create",
    )
    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)

    assert decision.allowed is True
    assert decision.tenant_id == tenant_id
    assert decision.url_safety is not None
    assert decision.url_safety.allowed is True
    assert decision.usage is not None
    assert decision.usage.allowed is True
    assert (
        balance.standard_credits_remaining
        == limits.standard_credits - HostedAction.SCRAPE.credit_cost
    )


def test_admit_url_action_rejects_unknown_key_without_url_or_credit_checks() -> None:
    admission, _account_service, _raw_key, _tenant_id = _service_with_key()

    decision = admission.admit_url_action(
        raw_key="scout_live_unknown",
        url="http://localhost:8421/health",
        action=HostedAction.SCRAPE,
        required_scope="runs:create",
    )

    assert decision.allowed is False
    assert decision.reason == "API key was not found."
    assert decision.url_safety is None
    assert decision.usage is None


def test_admit_url_action_rejects_wrong_scope_without_url_or_credit_checks() -> None:
    admission, _account_service, raw_key, tenant_id = _service_with_key()

    decision = admission.admit_url_action(
        raw_key=raw_key,
        url="https://example.com/products",
        action=HostedAction.SCRAPE,
        required_scope="admin:keys",
    )

    assert decision.allowed is False
    assert decision.tenant_id == tenant_id
    assert decision.reason == "API key does not have required scope: admin:keys."
    assert decision.url_safety is None
    assert decision.usage is None


def test_admit_url_action_rejects_unsafe_url_without_debiting_credits() -> None:
    admission, account_service, raw_key, tenant_id = _service_with_key()

    decision = admission.admit_url_action(
        raw_key=raw_key,
        url="http://169.254.169.254/latest/meta-data/",
        action=HostedAction.SCRAPE,
        required_scope="runs:create",
    )
    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)

    assert decision.allowed is False
    assert decision.reason == "URL targets unsafe IP address: 169.254.169.254."
    assert decision.url_safety is not None
    assert decision.url_safety.allowed is False
    assert decision.usage is None
    assert balance.standard_credits_remaining == limits.standard_credits


def test_admit_url_action_rejects_resolved_private_ip_without_debiting_credits() -> None:
    admission, account_service, raw_key, tenant_id = _service_with_key()

    decision = admission.admit_url_action(
        raw_key=raw_key,
        url="https://public-name.example/page",
        action=HostedAction.SCRAPE,
        required_scope="runs:create",
        resolved_ips=["10.0.0.10"],
    )
    balance = account_service.get_balance(tenant_id)
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)

    assert decision.allowed is False
    assert decision.reason == "URL resolved to unsafe IP address: 10.0.0.10."
    assert decision.usage is None
    assert balance.standard_credits_remaining == limits.standard_credits


def test_admit_url_action_preserves_balance_when_credits_insufficient() -> None:
    admission, account_service, raw_key, tenant_id = _service_with_key()
    account_service.set_balance(tenant_id, standard_credits=0, browser_credits=0)

    decision = admission.admit_url_action(
        raw_key=raw_key,
        url="https://example.com/products",
        action=HostedAction.BROWSER_RENDER,
        required_scope="runs:create",
    )
    balance = account_service.get_balance(tenant_id)

    assert decision.allowed is False
    assert decision.reason == "Insufficient browser credits: need 5, have 0."
    assert decision.url_safety is not None
    assert decision.url_safety.allowed is True
    assert decision.usage is not None
    assert decision.usage.allowed is False
    assert balance.standard_credits_remaining == 0
    assert balance.browser_credits_remaining == 0
