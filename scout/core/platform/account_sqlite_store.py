"""SQLite-backed hosted account store."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scout.core.platform.account_service import (
    HostedAccountStatus,
    HostedAccountSnapshot,
    HostedSignupEvent,
    HostedTenantRecord,
    HostedUsageLedgerEntry,
)
from scout.core.platform.api_keys import ApiKeyRecord, ApiKeyStatus
from scout.core.platform.hosted import HostedPlan, HostedUsageBalance


class SQLiteHostedAccountStore:
    """Durable hosted account store for local and test deployments."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save_account(
        self,
        tenant: HostedTenantRecord,
        api_key: ApiKeyRecord,
        balance: HostedUsageBalance,
    ) -> None:
        """Persist a hosted tenant, key metadata, and credit balance."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO hosted_tenants
                (tenant_id, email, name, plan, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    tenant.tenant_id,
                    str(tenant.email),
                    tenant.name,
                    tenant.plan.value,
                    tenant.status.value,
                    tenant.created_at,
                ),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO hosted_api_keys
                (key_id, tenant_id, key_hash, name, scopes_json, status, created_at, last_used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    api_key.key_id,
                    api_key.tenant_id,
                    api_key.key_hash,
                    api_key.name,
                    json.dumps(api_key.scopes),
                    api_key.status.value,
                    api_key.created_at,
                    api_key.last_used_at,
                ),
            )
            self._set_balance(conn, tenant.tenant_id, balance)

    def find_key_by_hash(self, key_hash: str) -> ApiKeyRecord | None:
        """Find stored key metadata by hashed raw API key."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT key_id, tenant_id, key_hash, name, scopes_json, status, created_at, last_used_at
                FROM hosted_api_keys
                WHERE key_hash = ?
                """,
                (key_hash,),
            ).fetchone()
        if row is None:
            return None
        return _api_key_from_row(row)

    def get_tenant(self, tenant_id: str) -> HostedTenantRecord | None:
        """Return tenant metadata."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT tenant_id, email, name, plan, status, created_at
                FROM hosted_tenants
                WHERE tenant_id = ?
                """,
                (tenant_id,),
            ).fetchone()
        if row is None:
            return None
        return HostedTenantRecord(
            tenant_id=row["tenant_id"],
            email=row["email"],
            name=row["name"],
            plan=row["plan"],
            status=row["status"],
            created_at=row["created_at"],
        )

    def find_tenant_by_email(self, email: str) -> HostedTenantRecord | None:
        """Return tenant metadata for a normalized email if it exists."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT tenant_id, email, name, plan, status, created_at
                FROM hosted_tenants
                WHERE lower(email) = lower(?)
                """,
                (email.strip(),),
            ).fetchone()
        if row is None:
            return None
        return HostedTenantRecord(
            tenant_id=row["tenant_id"],
            email=row["email"],
            name=row["name"],
            plan=row["plan"],
            status=row["status"],
            created_at=row["created_at"],
        )

    def delete_account(self, tenant_id: str) -> None:
        """Remove a hosted tenant, all keys, and its balance."""
        with self._connect() as conn:
            conn.execute("DELETE FROM hosted_credit_ledger WHERE tenant_id = ?", (tenant_id,))
            conn.execute("DELETE FROM hosted_credit_balances WHERE tenant_id = ?", (tenant_id,))
            conn.execute("DELETE FROM hosted_api_keys WHERE tenant_id = ?", (tenant_id,))
            conn.execute("DELETE FROM hosted_tenants WHERE tenant_id = ?", (tenant_id,))

    def get_balance(self, tenant_id: str) -> HostedUsageBalance:
        """Return tenant credit balance."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT standard_credits_remaining, browser_credits_remaining
                FROM hosted_credit_balances
                WHERE tenant_id = ?
                """,
                (tenant_id,),
            ).fetchone()
        if row is None:
            raise KeyError(tenant_id)
        return HostedUsageBalance(
            standard_credits_remaining=row["standard_credits_remaining"],
            browser_credits_remaining=row["browser_credits_remaining"],
        )

    def set_balance(self, tenant_id: str, balance: HostedUsageBalance) -> None:
        """Replace tenant credit balance."""
        with self._connect() as conn:
            self._set_balance(conn, tenant_id, balance)

    def record_usage(self, entry: HostedUsageLedgerEntry) -> None:
        """Persist a hosted usage ledger entry."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO hosted_credit_ledger
                (ledger_id, tenant_id, key_id, action, credit_type, credits,
                 standard_balance_after, browser_balance_after, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.ledger_id,
                    entry.tenant_id,
                    entry.key_id,
                    entry.action,
                    entry.credit_type,
                    entry.credits,
                    entry.standard_balance_after,
                    entry.browser_balance_after,
                    json.dumps(entry.metadata, sort_keys=True),
                    entry.created_at,
                ),
            )

    def list_usage(self, tenant_id: str, limit: int = 100) -> list[HostedUsageLedgerEntry]:
        """Return recent usage ledger entries for a hosted tenant."""
        safe_limit = max(1, min(limit, 500))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT ledger_id, tenant_id, key_id, action, credit_type, credits,
                       standard_balance_after, browser_balance_after, metadata_json, created_at
                FROM hosted_credit_ledger
                WHERE tenant_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (tenant_id, safe_limit),
            ).fetchall()
        return [_ledger_entry_from_row(row) for row in rows]

    def list_all_usage(self, limit: int = 500) -> list[HostedUsageLedgerEntry]:
        """Return recent usage ledger entries across hosted tenants."""
        safe_limit = max(1, min(limit, 1000))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT ledger_id, tenant_id, key_id, action, credit_type, credits,
                       standard_balance_after, browser_balance_after, metadata_json, created_at
                FROM hosted_credit_ledger
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [_ledger_entry_from_row(row) for row in rows]

    def record_signup_event(self, event: HostedSignupEvent) -> None:
        """Persist a non-secret hosted beta signup event."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO hosted_signup_events
                (event_id, email, name, status, source, tenant_id, key_id,
                 delivery_status, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    str(event.email),
                    event.name,
                    event.status,
                    event.source,
                    event.tenant_id,
                    event.key_id,
                    event.delivery_status,
                    event.reason,
                    event.created_at,
                ),
            )

    def list_signup_events(self, limit: int = 100) -> list[HostedSignupEvent]:
        """Return recent hosted beta signup events."""
        safe_limit = max(1, min(limit, 1000))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT event_id, email, name, status, source, tenant_id, key_id,
                       delivery_status, reason, created_at
                FROM hosted_signup_events
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [_signup_event_from_row(row) for row in rows]

    def list_accounts(self, limit: int = 100) -> list[HostedAccountSnapshot]:
        """Return non-secret hosted account snapshots."""
        safe_limit = max(1, min(limit, 500))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                  t.tenant_id,
                  t.email,
                  t.name,
                  t.plan,
                  t.status AS account_status,
                  t.created_at,
                  k.key_id,
                  k.name AS key_name,
                  k.status AS key_status,
                  k.last_used_at,
                  b.standard_credits_remaining,
                  b.browser_credits_remaining
                FROM hosted_tenants t
                LEFT JOIN hosted_api_keys k ON k.tenant_id = t.tenant_id
                LEFT JOIN hosted_credit_balances b ON b.tenant_id = t.tenant_id
                ORDER BY t.created_at DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [_snapshot_from_row(row) for row in rows if row["key_id"] is not None]

    def update_key_status(self, key_id: str, status: ApiKeyStatus) -> None:
        """Update API-key lifecycle status."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE hosted_api_keys SET status = ? WHERE key_id = ?",
                (status.value, key_id),
            )

    def update_tenant_status(self, tenant_id: str, status: HostedAccountStatus) -> None:
        """Update hosted tenant lifecycle status."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE hosted_tenants SET status = ? WHERE tenant_id = ?",
                (status.value, tenant_id),
            )

    def update_tenant_plan(self, tenant_id: str, plan: HostedPlan) -> None:
        """Update hosted tenant commercial plan."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE hosted_tenants SET plan = ? WHERE tenant_id = ?",
                (plan.value, tenant_id),
            )

    def _connect(self) -> sqlite3.Connection:
        """Open a configured SQLite connection."""
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Create hosted account tables if they do not exist."""
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS hosted_tenants (
                  tenant_id TEXT PRIMARY KEY,
                  email TEXT NOT NULL,
                  name TEXT NOT NULL DEFAULT '',
                  plan TEXT NOT NULL,
                  status TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS hosted_api_keys (
                  key_id TEXT PRIMARY KEY,
                  tenant_id TEXT NOT NULL,
                  key_hash TEXT NOT NULL UNIQUE,
                  name TEXT NOT NULL,
                  scopes_json TEXT NOT NULL,
                  status TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  last_used_at TEXT NOT NULL,
                  FOREIGN KEY (tenant_id) REFERENCES hosted_tenants(tenant_id)
                );

                CREATE TABLE IF NOT EXISTS hosted_credit_balances (
                  tenant_id TEXT PRIMARY KEY,
                  standard_credits_remaining INTEGER NOT NULL,
                  browser_credits_remaining INTEGER NOT NULL,
                  FOREIGN KEY (tenant_id) REFERENCES hosted_tenants(tenant_id)
                );

                CREATE TABLE IF NOT EXISTS hosted_credit_ledger (
                  ledger_id TEXT PRIMARY KEY,
                  tenant_id TEXT NOT NULL,
                  key_id TEXT NOT NULL,
                  action TEXT NOT NULL,
                  credit_type TEXT NOT NULL,
                  credits INTEGER NOT NULL,
                  standard_balance_after INTEGER NOT NULL,
                  browser_balance_after INTEGER NOT NULL,
                  metadata_json TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY (tenant_id) REFERENCES hosted_tenants(tenant_id),
                  FOREIGN KEY (key_id) REFERENCES hosted_api_keys(key_id)
                );

                CREATE TABLE IF NOT EXISTS hosted_signup_events (
                  event_id TEXT PRIMARY KEY,
                  email TEXT NOT NULL,
                  name TEXT NOT NULL DEFAULT '',
                  status TEXT NOT NULL,
                  source TEXT NOT NULL,
                  tenant_id TEXT NOT NULL DEFAULT '',
                  key_id TEXT NOT NULL DEFAULT '',
                  delivery_status TEXT NOT NULL DEFAULT '',
                  reason TEXT NOT NULL DEFAULT '',
                  created_at TEXT NOT NULL
                );
                """
            )
            self._ensure_column(
                conn,
                table="hosted_tenants",
                column="name",
                definition="TEXT NOT NULL DEFAULT ''",
            )

    def _ensure_column(
        self,
        conn: sqlite3.Connection,
        *,
        table: str,
        column: str,
        definition: str,
    ) -> None:
        """Add a SQLite column if an existing deployment database lacks it."""
        columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
        if any(row["name"] == column for row in columns):
            return
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _set_balance(
        self,
        conn: sqlite3.Connection,
        tenant_id: str,
        balance: HostedUsageBalance,
    ) -> None:
        """Upsert a hosted credit balance."""
        conn.execute(
            """
            INSERT INTO hosted_credit_balances
            (tenant_id, standard_credits_remaining, browser_credits_remaining)
            VALUES (?, ?, ?)
            ON CONFLICT(tenant_id) DO UPDATE SET
              standard_credits_remaining = excluded.standard_credits_remaining,
              browser_credits_remaining = excluded.browser_credits_remaining
            """,
            (
                tenant_id,
                balance.standard_credits_remaining,
                balance.browser_credits_remaining,
            ),
        )


def _api_key_from_row(row: sqlite3.Row) -> ApiKeyRecord:
    """Build an API-key record from a SQLite row."""
    return ApiKeyRecord(
        key_id=row["key_id"],
        tenant_id=row["tenant_id"],
        key_hash=row["key_hash"],
        name=row["name"],
        scopes=json.loads(row["scopes_json"]),
        status=row["status"],
        created_at=row["created_at"],
        last_used_at=row["last_used_at"],
    )


def _ledger_entry_from_row(row: sqlite3.Row) -> HostedUsageLedgerEntry:
    """Build a usage ledger entry from SQLite data."""
    return HostedUsageLedgerEntry(
        ledger_id=row["ledger_id"],
        tenant_id=row["tenant_id"],
        key_id=row["key_id"],
        action=row["action"],
        credit_type=row["credit_type"],
        credits=row["credits"],
        standard_balance_after=row["standard_balance_after"],
        browser_balance_after=row["browser_balance_after"],
        metadata=json.loads(row["metadata_json"] or "{}"),
        created_at=row["created_at"],
    )


def _signup_event_from_row(row: sqlite3.Row) -> HostedSignupEvent:
    """Build a hosted signup event from a SQLite row."""
    return HostedSignupEvent(
        event_id=row["event_id"],
        email=row["email"],
        name=row["name"],
        status=row["status"],
        source=row["source"],
        tenant_id=row["tenant_id"],
        key_id=row["key_id"],
        delivery_status=row["delivery_status"],
        reason=row["reason"],
        created_at=row["created_at"],
    )


def _snapshot_from_row(row: sqlite3.Row) -> HostedAccountSnapshot:
    """Build a non-secret account snapshot from a joined SQLite row."""
    return HostedAccountSnapshot(
        tenant_id=row["tenant_id"],
        email=row["email"],
        name=row["name"],
        plan=row["plan"],
        account_status=row["account_status"],
        key_id=row["key_id"],
        key_name=row["key_name"],
        key_status=row["key_status"],
        standard_credits_remaining=row["standard_credits_remaining"],
        browser_credits_remaining=row["browser_credits_remaining"],
        created_at=row["created_at"],
        last_used_at=row["last_used_at"],
    )
