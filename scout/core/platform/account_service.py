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
    name: str = ""
    plan: HostedPlan
    status: HostedAccountStatus = HostedAccountStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class HostedProvisioningResult(BaseModel):
    """Result returned when a hosted account is provisioned."""

    tenant: HostedTenantRecord
    api_key: ApiKeyRecord
    balance: HostedUsageBalance
    raw_api_key: str


class HostedUsageLedgerEntry(BaseModel):
    """Auditable record of a hosted credit debit."""

    ledger_id: str = Field(default_factory=lambda: f"usage_{uuid4().hex}")
    tenant_id: str
    key_id: str
    action: str
    credit_type: str
    credits: int
    standard_balance_after: int
    browser_balance_after: int
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class HostedSignupEvent(BaseModel):
    """Auditable non-secret record of a hosted beta signup attempt."""

    event_id: str = Field(default_factory=lambda: f"signup_{uuid4().hex}")
    email: EmailStr
    name: str = ""
    status: str
    source: str
    tenant_id: str = ""
    key_id: str = ""
    delivery_status: str = ""
    reason: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class HostedAccountSnapshot(BaseModel):
    """Non-secret account, key, and balance snapshot for operator monitoring."""

    tenant_id: str
    email: EmailStr
    name: str = ""
    plan: str
    account_status: str
    key_id: str
    key_name: str = ""
    key_status: str
    standard_credits_remaining: int
    browser_credits_remaining: int
    created_at: str
    last_used_at: str = ""


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

    def find_tenant_by_email(self, email: str) -> HostedTenantRecord | None: ...

    def delete_account(self, tenant_id: str) -> None: ...

    def get_balance(self, tenant_id: str) -> HostedUsageBalance: ...

    def set_balance(self, tenant_id: str, balance: HostedUsageBalance) -> None: ...

    def record_usage(self, entry: HostedUsageLedgerEntry) -> None: ...

    def list_usage(self, tenant_id: str, limit: int = 100) -> list[HostedUsageLedgerEntry]: ...

    def list_all_usage(self, limit: int = 500) -> list[HostedUsageLedgerEntry]: ...

    def record_signup_event(self, event: HostedSignupEvent) -> None: ...

    def list_signup_events(self, limit: int = 100) -> list[HostedSignupEvent]: ...

    def list_accounts(self, limit: int = 100) -> list[HostedAccountSnapshot]: ...

    def update_key_status(self, key_id: str, status: ApiKeyStatus) -> None: ...

    def update_tenant_status(self, tenant_id: str, status: HostedAccountStatus) -> None: ...


class InMemoryHostedAccountStore:
    """In-memory hosted account store for tests and local development."""

    def __init__(self) -> None:
        self.tenants: dict[str, HostedTenantRecord] = {}
        self.api_keys: dict[str, ApiKeyRecord] = {}
        self.balances: dict[str, HostedUsageBalance] = {}
        self.usage_entries: list[HostedUsageLedgerEntry] = []
        self.signup_events: list[HostedSignupEvent] = []

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

    def find_tenant_by_email(self, email: str) -> HostedTenantRecord | None:
        """Return tenant metadata for a normalized email if it exists."""
        normalized = email.strip().lower()
        for tenant in self.tenants.values():
            if str(tenant.email).lower() == normalized:
                return tenant
        return None

    def delete_account(self, tenant_id: str) -> None:
        """Remove a hosted tenant, all keys, and its balance."""
        self.tenants.pop(tenant_id, None)
        self.balances.pop(tenant_id, None)
        for key_id, record in list(self.api_keys.items()):
            if record.tenant_id == tenant_id:
                self.api_keys.pop(key_id, None)
        self.usage_entries = [entry for entry in self.usage_entries if entry.tenant_id != tenant_id]

    def get_balance(self, tenant_id: str) -> HostedUsageBalance:
        """Return tenant credit balance."""
        return self.balances[tenant_id]

    def set_balance(self, tenant_id: str, balance: HostedUsageBalance) -> None:
        """Replace tenant credit balance."""
        self.balances[tenant_id] = balance

    def record_usage(self, entry: HostedUsageLedgerEntry) -> None:
        """Store a hosted usage ledger entry."""
        self.usage_entries.append(entry)

    def list_usage(self, tenant_id: str, limit: int = 100) -> list[HostedUsageLedgerEntry]:
        """Return recent usage entries for a tenant."""
        entries = [entry for entry in self.usage_entries if entry.tenant_id == tenant_id]
        return list(reversed(entries))[:limit]

    def list_all_usage(self, limit: int = 500) -> list[HostedUsageLedgerEntry]:
        """Return recent usage entries across tenants."""
        safe_limit = max(1, min(limit, 1000))
        return list(reversed(self.usage_entries))[:safe_limit]

    def record_signup_event(self, event: HostedSignupEvent) -> None:
        """Store a non-secret hosted signup event."""
        self.signup_events.append(event)

    def list_signup_events(self, limit: int = 100) -> list[HostedSignupEvent]:
        """Return recent hosted signup events."""
        safe_limit = max(1, min(limit, 1000))
        return list(reversed(self.signup_events))[:safe_limit]

    def list_accounts(self, limit: int = 100) -> list[HostedAccountSnapshot]:
        """Return non-secret account snapshots."""
        safe_limit = max(1, min(limit, 500))
        snapshots: list[HostedAccountSnapshot] = []
        for tenant in sorted(
            self.tenants.values(),
            key=lambda item: item.created_at,
            reverse=True,
        ):
            tenant_keys = [
                key for key in self.api_keys.values() if key.tenant_id == tenant.tenant_id
            ]
            if not tenant_keys:
                continue
            key = sorted(tenant_keys, key=lambda item: item.created_at, reverse=True)[0]
            balance = self.balances[tenant.tenant_id]
            snapshots.append(
                HostedAccountSnapshot(
                    tenant_id=tenant.tenant_id,
                    email=tenant.email,
                    name=tenant.name,
                    plan=tenant.plan.value,
                    account_status=tenant.status.value,
                    key_id=key.key_id,
                    key_name=key.name,
                    key_status=key.status.value,
                    standard_credits_remaining=balance.standard_credits_remaining,
                    browser_credits_remaining=balance.browser_credits_remaining,
                    created_at=tenant.created_at,
                    last_used_at=key.last_used_at,
                )
            )
        return snapshots[:safe_limit]

    def update_key_status(self, key_id: str, status: ApiKeyStatus) -> None:
        """Update API-key lifecycle status."""
        record = self.api_keys[key_id]
        self.api_keys[key_id] = record.model_copy(update={"status": status})

    def update_tenant_status(self, tenant_id: str, status: HostedAccountStatus) -> None:
        """Update hosted tenant lifecycle status."""
        tenant = self.tenants[tenant_id]
        self.tenants[tenant_id] = tenant.model_copy(update={"status": status})


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
        name: str = "",
        standard_credits: int | None = None,
        browser_credits: int | None = None,
    ) -> HostedProvisioningResult:
        """Provision a hosted tenant and return the raw API key once."""
        normalized_email = email.strip().lower()
        if self.store.find_tenant_by_email(normalized_email) is not None:
            raise ValueError("A hosted beta key already exists for this email.")
        limits = plan_limits(plan)
        if not limits.hosted_enabled:
            raise ValueError(f"Plan {plan.value} is not hosted-enabled.")

        tenant = HostedTenantRecord(email=normalized_email, name=name.strip(), plan=plan)
        raw_key = generate_api_key()
        api_key = ApiKeyRecord(
            key_id=f"key_{uuid4().hex}",
            tenant_id=tenant.tenant_id,
            key_hash=hash_api_key(raw_key),
            name=key_name,
            scopes=scopes,
        )
        balance = HostedUsageBalance(
            standard_credits_remaining=limits.standard_credits
            if standard_credits is None
            else standard_credits,
            browser_credits_remaining=limits.browser_credits
            if browser_credits is None
            else browser_credits,
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

        next_balance = _debit_balance(balance, action)
        self.store.set_balance(auth.tenant_id, next_balance)
        self.store.record_usage(
            _usage_entry(
                tenant_id=auth.tenant_id,
                key_id=auth.key_id,
                action=action,
                credits=action.credit_cost,
                balance=next_balance,
            )
        )
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

    def delete_account(self, tenant_id: str) -> None:
        """Remove a hosted account after failed one-time key delivery."""
        self.store.delete_account(tenant_id)

    def disable_account(self, tenant_id: str) -> None:
        """Disable a hosted account and all known keys for that tenant."""
        self.store.update_tenant_status(tenant_id, HostedAccountStatus.DISABLED)
        for account in self.store.list_accounts(limit=10_000):
            if account.tenant_id == tenant_id:
                self.store.update_key_status(account.key_id, ApiKeyStatus.DISABLED)

    def disable_api_key(self, key_id: str) -> None:
        """Disable one hosted API key without deleting non-secret audit metadata."""
        self.store.update_key_status(key_id, ApiKeyStatus.DISABLED)

    def find_tenant_by_email(self, email: str) -> HostedTenantRecord | None:
        """Return tenant metadata for a normalized email if it exists."""
        return self.store.find_tenant_by_email(email)

    def latest_key_id_for_tenant(self, tenant_id: str) -> str:
        """Return the most recent non-secret key id for a hosted tenant."""
        for account in self.store.list_accounts(limit=10_000):
            if account.tenant_id == tenant_id:
                return account.key_id
        return ""

    def issue_api_key_for_tenant(
        self,
        tenant_id: str,
        *,
        scopes: list[str],
        key_name: str = "Replacement hosted key",
    ) -> HostedProvisioningResult:
        """Issue an additional API key for an existing hosted tenant."""
        tenant = self.store.get_tenant(tenant_id)
        if tenant is None:
            raise ValueError("Hosted account was not found.")
        balance = self.store.get_balance(tenant_id)
        raw_key = generate_api_key()
        api_key = ApiKeyRecord(
            key_id=f"key_{uuid4().hex}",
            tenant_id=tenant.tenant_id,
            key_hash=hash_api_key(raw_key),
            name=key_name,
            scopes=scopes,
        )
        self.store.save_account(tenant, api_key, balance)
        return HostedProvisioningResult(
            tenant=tenant,
            api_key=api_key,
            balance=balance,
            raw_api_key=raw_key,
        )

    def add_credits(
        self,
        tenant_id: str,
        *,
        standard_credits: int,
        browser_credits: int,
    ) -> HostedUsageBalance:
        """Add hosted credits to an existing tenant balance."""
        balance = self.store.get_balance(tenant_id)
        next_balance = HostedUsageBalance(
            standard_credits_remaining=(balance.standard_credits_remaining + standard_credits),
            browser_credits_remaining=(balance.browser_credits_remaining + browser_credits),
        )
        self.store.set_balance(tenant_id, next_balance)
        return next_balance

    def debit_standard_credits(
        self,
        *,
        tenant_id: str,
        key_id: str,
        action: HostedAction,
        credits: int,
        metadata: dict[str, str] | None = None,
    ) -> HostedUsageBalance:
        """Debit a variable number of standard credits and record the usage event."""
        balance = self.store.get_balance(tenant_id)
        next_balance = balance.model_copy(
            update={"standard_credits_remaining": balance.standard_credits_remaining - credits}
        )
        self.store.set_balance(tenant_id, next_balance)
        self.store.record_usage(
            _usage_entry(
                tenant_id=tenant_id,
                key_id=key_id,
                action=action,
                credits=credits,
                balance=next_balance,
                metadata=metadata or {},
            )
        )
        return next_balance

    def list_usage(self, tenant_id: str, limit: int = 100) -> list[HostedUsageLedgerEntry]:
        """Return recent usage entries for a hosted tenant."""
        return self.store.list_usage(tenant_id, limit)

    def list_all_usage(self, limit: int = 500) -> list[HostedUsageLedgerEntry]:
        """Return recent usage entries across hosted tenants."""
        return self.store.list_all_usage(limit)

    def record_signup_event(self, event: HostedSignupEvent) -> None:
        """Record a non-secret hosted signup attempt for monitoring."""
        self.store.record_signup_event(event)

    def list_signup_events(self, limit: int = 100) -> list[HostedSignupEvent]:
        """Return recent hosted signup attempts for operator monitoring."""
        return self.store.list_signup_events(limit)

    def pending_signup_requests(self, limit: int = 100) -> list[HostedSignupEvent]:
        """Return newest pending beta signup requests that still need key delivery."""
        latest_by_email: dict[str, HostedSignupEvent] = {}
        for event in self.store.list_signup_events(limit=10_000):
            normalized = str(event.email).strip().lower()
            if normalized not in latest_by_email:
                latest_by_email[normalized] = event

        pending: list[HostedSignupEvent] = []
        for normalized, event in latest_by_email.items():
            if event.status != "pending_delivery":
                continue
            if self.store.find_tenant_by_email(normalized) is not None:
                continue
            pending.append(event)
            if len(pending) >= limit:
                break
        return pending

    def list_accounts(self, limit: int = 100) -> list[HostedAccountSnapshot]:
        """Return non-secret account snapshots for operator monitoring."""
        return self.store.list_accounts(limit)


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


def _usage_entry(
    *,
    tenant_id: str,
    key_id: str,
    action: HostedAction,
    credits: int,
    balance: HostedUsageBalance,
    metadata: dict[str, str] | None = None,
) -> HostedUsageLedgerEntry:
    """Build an auditable hosted usage event."""
    return HostedUsageLedgerEntry(
        tenant_id=tenant_id,
        key_id=key_id,
        action=action.value,
        credit_type=action.credit_type,
        credits=credits,
        standard_balance_after=balance.standard_credits_remaining,
        browser_balance_after=balance.browser_credits_remaining,
        metadata=metadata or {},
    )
