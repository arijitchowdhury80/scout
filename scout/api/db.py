"""Async SQLite persistence for Scout runs and events."""

from __future__ import annotations

from datetime import datetime, timezone

import aiosqlite
from pydantic import BaseModel, Field


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunRow(BaseModel):
    run_id: str
    use_case: str = ""
    query: str = ""
    status: str = "queued"
    mode: str = ""
    tenant_id: str = ""
    key_id: str = ""
    output_dir: str = ""
    artifacts_json: str = "{}"
    created_at: str = Field(default_factory=_now_iso)
    updated_at: str = Field(default_factory=_now_iso)
    finished_at: str = ""


class RunEventRow(BaseModel):
    run_id: str
    stage: str = ""
    message: str = ""
    level: str = "info"
    timestamp: str = Field(default_factory=_now_iso)


_CREATE_RUNS = """
CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY,
    use_case    TEXT NOT NULL DEFAULT '',
    query       TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'queued',
    mode        TEXT NOT NULL DEFAULT '',
    tenant_id   TEXT NOT NULL DEFAULT '',
    key_id      TEXT NOT NULL DEFAULT '',
    output_dir  TEXT NOT NULL DEFAULT '',
    artifacts_json TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    finished_at TEXT NOT NULL DEFAULT ''
)
"""

_CREATE_EVENTS = """
CREATE TABLE IF NOT EXISTS run_events (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id    TEXT NOT NULL,
    stage     TEXT NOT NULL DEFAULT '',
    message   TEXT NOT NULL DEFAULT '',
    level     TEXT NOT NULL DEFAULT 'info',
    timestamp TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
)
"""

_CREATE_EVENTS_IDX = """
CREATE INDEX IF NOT EXISTS idx_events_run_id ON run_events(run_id)
"""


class RunDB:
    """Async SQLite database for persisting run state and events."""

    def __init__(self, db_path: str) -> None:
        self._path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def init_db(self) -> None:
        self._conn = await aiosqlite.connect(self._path)
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._conn.execute(_CREATE_RUNS)
        await self._ensure_column("runs", "tenant_id", "TEXT NOT NULL DEFAULT ''")
        await self._ensure_column("runs", "key_id", "TEXT NOT NULL DEFAULT ''")
        await self._conn.execute(_CREATE_EVENTS)
        await self._conn.execute(_CREATE_EVENTS_IDX)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def _db(self) -> aiosqlite.Connection:
        assert self._conn is not None, "RunDB not initialised — call init_db() first"
        return self._conn

    async def save_run(self, row: RunRow) -> None:
        row.updated_at = _now_iso()
        await self._db.execute(
            """
            INSERT INTO runs (run_id, use_case, query, status, mode,
                              tenant_id, key_id, output_dir, artifacts_json,
                              created_at, updated_at, finished_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                use_case=excluded.use_case,
                query=excluded.query,
                status=excluded.status,
                mode=excluded.mode,
                tenant_id=excluded.tenant_id,
                key_id=excluded.key_id,
                output_dir=excluded.output_dir,
                artifacts_json=excluded.artifacts_json,
                updated_at=excluded.updated_at,
                finished_at=excluded.finished_at
            """,
            (
                row.run_id,
                row.use_case,
                row.query,
                row.status,
                row.mode,
                row.tenant_id,
                row.key_id,
                row.output_dir,
                row.artifacts_json,
                row.created_at,
                row.updated_at,
                row.finished_at,
            ),
        )
        await self._db.commit()

    async def get_run(self, run_id: str) -> RunRow | None:
        cursor = await self._db.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cursor.description]
        return RunRow(**dict(zip(cols, row)))

    async def list_runs(
        self,
        *,
        use_case: str | None = None,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[RunRow]:
        if use_case and tenant_id:
            cursor = await self._db.execute(
                """
                SELECT * FROM runs
                WHERE use_case = ? AND tenant_id = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (use_case, tenant_id, limit),
            )
        elif use_case:
            cursor = await self._db.execute(
                "SELECT * FROM runs WHERE use_case = ? ORDER BY created_at DESC LIMIT ?",
                (use_case, limit),
            )
        elif tenant_id:
            cursor = await self._db.execute(
                "SELECT * FROM runs WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?",
                (tenant_id, limit),
            )
        else:
            cursor = await self._db.execute(
                "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)
            )
        rows = await cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        return [RunRow(**dict(zip(cols, r))) for r in rows]

    async def delete_run(self, run_id: str) -> None:
        await self._db.execute("DELETE FROM run_events WHERE run_id = ?", (run_id,))
        await self._db.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
        await self._db.commit()

    async def append_event(self, event: RunEventRow) -> None:
        await self._db.execute(
            """
            INSERT INTO run_events (run_id, stage, message, level, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event.run_id, event.stage, event.message, event.level, event.timestamp),
        )
        await self._db.commit()

    async def get_events(self, run_id: str) -> list[RunEventRow]:
        cursor = await self._db.execute(
            "SELECT run_id, stage, message, level, timestamp FROM run_events WHERE run_id = ? ORDER BY id",
            (run_id,),
        )
        rows = await cursor.fetchall()
        return [
            RunEventRow(run_id=r[0], stage=r[1], message=r[2], level=r[3], timestamp=r[4])
            for r in rows
        ]

    async def _table_names(self) -> list[str]:
        cursor = await self._db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        rows = await cursor.fetchall()
        return [r[0] for r in rows]

    async def _ensure_column(self, table: str, column: str, definition: str) -> None:
        cursor = await self._db.execute(f"PRAGMA table_info({table})")
        rows = await cursor.fetchall()
        columns = {row[1] for row in rows}
        if column in columns:
            return
        await self._db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        await self._db.commit()
