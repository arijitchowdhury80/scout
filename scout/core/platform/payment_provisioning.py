"""Hosted payment provisioning primitives."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, EmailStr, Field

from scout.core.platform.account_service import HostedAccountService, HostedProvisioningResult
from scout.core.platform.hosted import HostedPlan
from scout.core.platform.pricing import get_credit_package


class HostedPaymentProvider(str, Enum):
    """Supported payment provider identifiers."""

    STRIPE = "stripe"


class HostedCheckoutPaymentStatus(str, Enum):
    """Checkout payment status values accepted by provisioning."""

    PAID = "paid"
    UNPAID = "unpaid"
    NO_PAYMENT_REQUIRED = "no_payment_required"


class HostedCheckoutProvisioningRequest(BaseModel):
    """Payment checkout data needed to provision hosted Scout access."""

    provider: HostedPaymentProvider = HostedPaymentProvider.STRIPE
    checkout_session_id: str = Field(min_length=1)
    customer_id: str = ""
    payment_intent_id: str = ""
    email: EmailStr
    package_id: str = "beta_trial"
    amount_total_cents: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    plan: HostedPlan = HostedPlan.HOSTED_BETA_PASS
    scopes: list[str] = Field(default_factory=lambda: ["runs:create"])
    status: HostedCheckoutPaymentStatus = HostedCheckoutPaymentStatus.PAID


class HostedCheckoutProvisioningRecord(BaseModel):
    """Persisted checkout-to-hosted-account mapping."""

    provider: HostedPaymentProvider
    checkout_session_id: str
    tenant_id: str
    key_id: str
    email: EmailStr
    package_id: str = "beta_trial"
    plan: HostedPlan
    amount_total_cents: int
    currency: str
    customer_id: str = ""
    payment_intent_id: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class HostedCheckoutProvisioningResult(BaseModel):
    """Provisioning result returned to a payment/webhook caller."""

    success: bool
    already_processed: bool = False
    tenant_id: str = ""
    key_id: str = ""
    plan: HostedPlan | None = None
    raw_api_key: str = ""
    reason: str = ""


class HostedPaymentStore(Protocol):
    """Persistence contract for payment provisioning idempotency."""

    def get_checkout(
        self,
        provider: HostedPaymentProvider,
        checkout_session_id: str,
    ) -> HostedCheckoutProvisioningRecord | None: ...

    def save_checkout(self, record: HostedCheckoutProvisioningRecord) -> None: ...


class SQLiteHostedPaymentStore:
    """SQLite payment event store for hosted checkout idempotency."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def get_checkout(
        self,
        provider: HostedPaymentProvider,
        checkout_session_id: str,
    ) -> HostedCheckoutProvisioningRecord | None:
        """Return a stored checkout mapping, if one exists."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT provider, checkout_session_id, tenant_id, key_id, email, package_id, plan,
                       amount_total_cents, currency, customer_id, payment_intent_id, created_at
                FROM hosted_payment_checkouts
                WHERE provider = ? AND checkout_session_id = ?
                """,
                (provider.value, checkout_session_id),
            ).fetchone()
        if row is None:
            return None
        return _record_from_row(row)

    def save_checkout(self, record: HostedCheckoutProvisioningRecord) -> None:
        """Persist a checkout mapping."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO hosted_payment_checkouts
                (provider, checkout_session_id, tenant_id, key_id, email, package_id, plan,
                 amount_total_cents, currency, customer_id, payment_intent_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _record_values(record),
            )

    def _connect(self) -> sqlite3.Connection:
        """Open a configured SQLite connection."""
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Create payment provisioning tables if they do not exist."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS hosted_payment_checkouts (
                  provider TEXT NOT NULL,
                  checkout_session_id TEXT NOT NULL,
                  tenant_id TEXT NOT NULL,
                  key_id TEXT NOT NULL,
                  email TEXT NOT NULL,
                  package_id TEXT NOT NULL DEFAULT 'beta_trial',
                  plan TEXT NOT NULL,
                  amount_total_cents INTEGER NOT NULL,
                  currency TEXT NOT NULL,
                  customer_id TEXT NOT NULL,
                  payment_intent_id TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  PRIMARY KEY (provider, checkout_session_id)
                )
                """
            )
            _ensure_column(
                conn,
                table="hosted_payment_checkouts",
                column="package_id",
                definition="TEXT NOT NULL DEFAULT 'beta_trial'",
            )


class HostedPaymentProvisioningService:
    """Convert paid checkout events into hosted Scout accounts."""

    def __init__(
        self,
        account_service: HostedAccountService,
        payment_store: HostedPaymentStore,
    ) -> None:
        self.account_service = account_service
        self.payment_store = payment_store

    def process_checkout(
        self,
        request: HostedCheckoutProvisioningRequest,
    ) -> HostedCheckoutProvisioningResult:
        """Provision hosted access for a paid checkout exactly once."""
        existing = self.payment_store.get_checkout(
            request.provider,
            request.checkout_session_id,
        )
        if existing is not None:
            return _existing_result(existing)

        rejection = _validate_checkout(request)
        if rejection is not None:
            return rejection

        provisioned = self.account_service.provision_account(
            email=str(request.email),
            plan=request.plan,
            scopes=request.scopes,
            key_name=f"{request.provider.value} checkout {request.checkout_session_id}",
        )
        package = get_credit_package(request.package_id)
        self.account_service.set_balance(
            provisioned.tenant.tenant_id,
            standard_credits=package.standard_credits,
            browser_credits=package.browser_credits,
        )
        self.payment_store.save_checkout(_record_from_request(request, provisioned))
        return HostedCheckoutProvisioningResult(
            success=True,
            tenant_id=provisioned.tenant.tenant_id,
            key_id=provisioned.api_key.key_id,
            plan=request.plan,
            raw_api_key=provisioned.raw_api_key,
        )


def _validate_checkout(
    request: HostedCheckoutProvisioningRequest,
) -> HostedCheckoutProvisioningResult | None:
    """Return a rejection result when checkout data should not provision access."""
    package = get_credit_package(request.package_id)
    if package.amount_cents == 0:
        if request.status is not HostedCheckoutPaymentStatus.NO_PAYMENT_REQUIRED:
            return HostedCheckoutProvisioningResult(
                success=False,
                reason=f"Checkout session is not complete for package {package.package_id}.",
            )
    elif request.status is not HostedCheckoutPaymentStatus.PAID:
        return HostedCheckoutProvisioningResult(
            success=False,
            reason="Checkout session is not paid.",
        )
    price_reason = _price_reason(request)
    if price_reason != "":
        return HostedCheckoutProvisioningResult(success=False, reason=price_reason)
    return None


def _price_reason(request: HostedCheckoutProvisioningRequest) -> str:
    """Return a rejection reason when checkout price does not match the plan."""
    package = get_credit_package(request.package_id)
    expected = f"Expected checkout amount {package.amount_cents} {package.currency}"
    if request.plan is not HostedPlan.HOSTED_BETA_PASS:
        return "Payment provisioning currently supports hosted_beta_pass only."
    if request.amount_total_cents != package.amount_cents:
        return f"{expected} for package {package.package_id}."
    if request.currency.lower() != package.currency:
        return f"{expected} for package {package.package_id}."
    return ""


def _existing_result(
    record: HostedCheckoutProvisioningRecord,
) -> HostedCheckoutProvisioningResult:
    """Return an idempotent replay result without a raw API key."""
    return HostedCheckoutProvisioningResult(
        success=True,
        already_processed=True,
        tenant_id=record.tenant_id,
        key_id=record.key_id,
        plan=record.plan,
    )


def _record_from_request(
    request: HostedCheckoutProvisioningRequest,
    provisioned: HostedProvisioningResult,
) -> HostedCheckoutProvisioningRecord:
    """Build a persisted checkout mapping from request and account result."""
    return HostedCheckoutProvisioningRecord(
        provider=request.provider,
        checkout_session_id=request.checkout_session_id,
        tenant_id=provisioned.tenant.tenant_id,
        key_id=provisioned.api_key.key_id,
        email=request.email,
        package_id=request.package_id,
        plan=request.plan,
        amount_total_cents=request.amount_total_cents,
        currency=request.currency.lower(),
        customer_id=request.customer_id,
        payment_intent_id=request.payment_intent_id,
    )


def _record_from_row(row: sqlite3.Row) -> HostedCheckoutProvisioningRecord:
    """Build a payment checkout record from SQLite data."""
    return HostedCheckoutProvisioningRecord(
        provider=row["provider"],
        checkout_session_id=row["checkout_session_id"],
        tenant_id=row["tenant_id"],
        key_id=row["key_id"],
        email=row["email"],
        package_id=row["package_id"],
        plan=row["plan"],
        amount_total_cents=row["amount_total_cents"],
        currency=row["currency"],
        customer_id=row["customer_id"],
        payment_intent_id=row["payment_intent_id"],
        created_at=row["created_at"],
    )


def _record_values(record: HostedCheckoutProvisioningRecord) -> tuple[object, ...]:
    """Return SQLite insert values for a checkout record."""
    return (
        record.provider.value,
        record.checkout_session_id,
        record.tenant_id,
        record.key_id,
        str(record.email),
        record.package_id,
        record.plan.value,
        record.amount_total_cents,
        record.currency,
        record.customer_id,
        record.payment_intent_id,
        record.created_at,
    )


def _ensure_column(
    conn: sqlite3.Connection,
    *,
    table: str,
    column: str,
    definition: str,
) -> None:
    """Add a SQLite column when an older hosted payment DB lacks it."""
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
