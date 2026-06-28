"""SQLite-backed hosted account store."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scout.core.platform.account_service import HostedTenantRecord
from scout.core.platform.api_keys import ApiKeyRecord, ApiKeyStatus
from scout.core.platform.hosted import HostedUsageBalance


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
                (tenant_id, email, plan, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    tenant.tenant_id,
                    str(tenant.email),
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
                SELECT tenant_id, email, plan, status, created_at
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
            plan=row["plan"],
            status=row["status"],
            created_at=row["created_at"],
        )

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

    def update_key_status(self, key_id: str, status: ApiKeyStatus) -> None:
        """Update API-key lifecycle status."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE hosted_api_keys SET status = ? WHERE key_id = ?",
                (status.value, key_id),
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
                """
            )

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
