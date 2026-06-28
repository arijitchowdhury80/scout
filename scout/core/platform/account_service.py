"""Hosted account domain service for API-key and credit admission."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field

from scout.core.platform.api_keys import (
    ApiKeyRecord,
    ApiKeyStatus,
    generate_api_key,
    hash_api_key,
    is_key_usable,
)
from scout.core.platform.hosted import (
    HostedAction,
    HostedPlan,
    HostedUsageBalance,
    HostedUsageDecision,
    check_hosted_usage,
    plan_limits,
)


class HostedAccountStatus(str, Enum):
    """Hosted tenant lifecycle status."""

    ACTIVE = "active"
    DISABLED = "disabled"


class HostedTenantRecord(BaseModel):
    """Hosted tenant metadata."""

    tenant_id: str = Field(default_factory=lambda: f"tenant_{uuid4().hex}")
    email: EmailStr
    plan: HostedPlan
    status: HostedAccountStatus = HostedAccountStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class HostedProvisioningResult(BaseModel):
    """Result returned when a hosted account is provisioned."""

    tenant: HostedTenantRecord
    api_key: ApiKeyRecord
    balance: HostedUsageBalance
    raw_api_key: str


class HostedAccountDecision(BaseModel):
    """Hosted authorization or usage decision."""

    allowed: bool
    reason: str = ""
    tenant_id: str = ""
    key_id: str = ""
    usage: HostedUsageDecision | None = None


class HostedAccountStore(Protocol):
    """Persistence contract used by hosted account services."""

    def save_account(
        self,
        tenant: HostedTenantRecord,
        api_key: ApiKeyRecord,
        balance: HostedUsageBalance,
    ) -> None: ...

    def find_key_by_hash(self, key_hash: str) -> ApiKeyRecord | None: ...

    def get_tenant(self, tenant_id: str) -> HostedTenantRecord | None: ...

    def get_balance(self, tenant_id: str) -> HostedUsageBalance: ...

    def set_balance(self, tenant_id: str, balance: HostedUsageBalance) -> None: ...

    def update_key_status(self, key_id: str, status: ApiKeyStatus) -> None: ...


class InMemoryHostedAccountStore:
    """In-memory hosted account store for tests and local development."""

    def __init__(self) -> None:
        self.tenants: dict[str, HostedTenantRecord] = {}
        self.api_keys: dict[str, ApiKeyRecord] = {}
        self.balances: dict[str, HostedUsageBalance] = {}

    def save_account(
        self,
        tenant: HostedTenantRecord,
        api_key: ApiKeyRecord,
        balance: HostedUsageBalance,
    ) -> None:
        """Persist a hosted tenant, key metadata, and credit balance."""
        self.tenants[tenant.tenant_id] = tenant
        self.api_keys[api_key.key_id] = api_key
        self.balances[tenant.tenant_id] = balance

    def find_key_by_hash(self, key_hash: str) -> ApiKeyRecord | None:
        """Find stored key metadata by hashed raw API key."""
        for record in self.api_keys.values():
            if record.key_hash == key_hash:
                return record
        return None

    def get_tenant(self, tenant_id: str) -> HostedTenantRecord | None:
        """Return tenant metadata."""
        return self.tenants.get(tenant_id)

    def get_balance(self, tenant_id: str) -> HostedUsageBalance:
        """Return tenant credit balance."""
        return self.balances[tenant_id]

    def set_balance(self, tenant_id: str, balance: HostedUsageBalance) -> None:
        """Replace tenant credit balance."""
        self.balances[tenant_id] = balance

    def update_key_status(self, key_id: str, status: ApiKeyStatus) -> None:
        """Update API-key lifecycle status."""
        record = self.api_keys[key_id]
        self.api_keys[key_id] = record.model_copy(update={"status": status})


class HostedAccountService:
    """Hosted account orchestration for provisioning, auth, and usage debit."""

    def __init__(self, store: HostedAccountStore) -> None:
        self.store = store

    def provision_account(
        self,
        email: str,
        plan: HostedPlan,
        scopes: list[str],
        key_name: str = "Default key",
    ) -> HostedProvisioningResult:
        """Provision a hosted tenant and return the raw API key once."""
        limits = plan_limits(plan)
        if not limits.hosted_enabled:
            raise ValueError(f"Plan {plan.value} is not hosted-enabled.")

        tenant = HostedTenantRecord(email=email, plan=plan)
        raw_key = generate_api_key()
        api_key = ApiKeyRecord(
            key_id=f"key_{uuid4().hex}",
            tenant_id=tenant.tenant_id,
            key_hash=hash_api_key(raw_key),
            name=key_name,
            scopes=scopes,
        )
        balance = HostedUsageBalance(
            standard_credits_remaining=limits.standard_credits,
            browser_credits_remaining=limits.browser_credits,
        )
        self.store.save_account(tenant, api_key, balance)
        return HostedProvisioningResult(
            tenant=tenant,
            api_key=api_key,
            balance=balance,
            raw_api_key=raw_key,
        )

    def authenticate_key(self, raw_key: str, required_scope: str = "") -> HostedAccountDecision:
        """Authenticate a hosted API key and scope."""
        record = self.store.find_key_by_hash(hash_api_key(raw_key))
        if record is None:
            return HostedAccountDecision(allowed=False, reason="API key was not found.")
        if record.status is not ApiKeyStatus.ACTIVE:
            return HostedAccountDecision(
                allowed=False,
                reason="API key is not active.",
                tenant_id=record.tenant_id,
                key_id=record.key_id,
            )
        if not is_key_usable(record, required_scope):
            return HostedAccountDecision(
                allowed=False,
                reason=f"API key does not have required scope: {required_scope}.",
                tenant_id=record.tenant_id,
                key_id=record.key_id,
            )
        tenant = self.store.get_tenant(record.tenant_id)
        if tenant is None or tenant.status is not HostedAccountStatus.ACTIVE:
            return HostedAccountDecision(
                allowed=False,
                reason="Hosted account is not active.",
                tenant_id=record.tenant_id,
                key_id=record.key_id,
            )
        return HostedAccountDecision(
            allowed=True,
            tenant_id=record.tenant_id,
            key_id=record.key_id,
        )

    def consume_action(
        self,
        raw_key: str,
        action: HostedAction,
        required_scope: str = "",
    ) -> HostedAccountDecision:
        """Authorize and debit a hosted action."""
        auth = self.authenticate_key(raw_key, required_scope)
        if not auth.allowed:
            return auth

        balance = self.store.get_balance(auth.tenant_id)
        usage = check_hosted_usage(balance, action)
        if not usage.allowed:
            return auth.model_copy(
                update={"allowed": False, "reason": usage.reason, "usage": usage}
            )

        self.store.set_balance(auth.tenant_id, _debit_balance(balance, action))
        return auth.model_copy(update={"usage": usage})

    def get_balance(self, tenant_id: str) -> HostedUsageBalance:
        """Return tenant credit balance."""
        return self.store.get_balance(tenant_id)

    def get_tenant(self, tenant_id: str) -> HostedTenantRecord | None:
        """Return hosted tenant metadata."""
        return self.store.get_tenant(tenant_id)

    def set_balance(
        self,
        tenant_id: str,
        standard_credits: int,
        browser_credits: int,
    ) -> None:
        """Set tenant credit balance; useful for admin flows and tests."""
        self.store.set_balance(
            tenant_id,
            HostedUsageBalance(
                standard_credits_remaining=standard_credits,
                browser_credits_remaining=browser_credits,
            ),
        )


def _debit_balance(balance: HostedUsageBalance, action: HostedAction) -> HostedUsageBalance:
    """Return a new balance after debiting an action."""
    if action.credit_type == "browser":
        return balance.model_copy(
            update={
                "browser_credits_remaining": balance.browser_credits_remaining - action.credit_cost
            }
        )
    return balance.model_copy(
        update={
            "standard_credits_remaining": balance.standard_credits_remaining - action.credit_cost
        }
    )
