"""Tests for scout.api.db — async SQLite persistence for runs and events."""

from __future__ import annotations

import pytest

from scout.api.db import RunDB, RunRow, RunEventRow


@pytest.fixture
async def db(tmp_path):
    """Yield an initialized RunDB backed by a temp SQLite file."""
    path = tmp_path / "scout-test.db"
    run_db = RunDB(str(path))
    await run_db.init_db()
    yield run_db
    await run_db.close()


async def test_init_creates_tables(db: RunDB) -> None:
    tables = await db._table_names()
    assert "runs" in tables
    assert "run_events" in tables


async def test_init_creates_hosted_ownership_columns(db: RunDB) -> None:
    cursor = await db._db.execute("PRAGMA table_info(runs)")
    rows = await cursor.fetchall()
    columns = {row[1] for row in rows}
    assert {"tenant_id", "key_id"}.issubset(columns)


async def test_save_and_get_run(db: RunDB) -> None:
    row = RunRow(
        run_id="run_abc123",
        use_case="company",
        query="Stripe",
        status="complete",
        output_dir="/tmp/runs/abc",
        artifacts_json="{}",
        tenant_id="tenant_123",
        key_id="key_123",
    )
    await db.save_run(row)
    got = await db.get_run("run_abc123")
    assert got is not None
    assert got.run_id == "run_abc123"
    assert got.use_case == "company"
    assert got.query == "Stripe"
    assert got.status == "complete"
    assert got.tenant_id == "tenant_123"
    assert got.key_id == "key_123"


async def test_get_run_returns_none_for_missing(db: RunDB) -> None:
    assert await db.get_run("nonexistent") is None


async def test_save_run_upserts_on_conflict(db: RunDB) -> None:
    row = RunRow(run_id="run_x", use_case="news", status="running", output_dir="/tmp")
    await db.save_run(row)
    row.status = "complete"
    row.query = "updated"
    await db.save_run(row)
    got = await db.get_run("run_x")
    assert got is not None
    assert got.status == "complete"
    assert got.query == "updated"


async def test_list_runs_returns_all(db: RunDB) -> None:
    for i in range(3):
        await db.save_run(RunRow(run_id=f"run_{i}", use_case="company", output_dir="/tmp"))
    rows = await db.list_runs()
    assert len(rows) == 3
    ids = {r.run_id for r in rows}
    assert ids == {"run_0", "run_1", "run_2"}


async def test_list_runs_filters_by_use_case(db: RunDB) -> None:
    await db.save_run(RunRow(run_id="a", use_case="company", output_dir="/tmp"))
    await db.save_run(RunRow(run_id="b", use_case="news", output_dir="/tmp"))
    rows = await db.list_runs(use_case="news")
    assert len(rows) == 1
    assert rows[0].run_id == "b"


async def test_append_and_get_events(db: RunDB) -> None:
    await db.save_run(RunRow(run_id="run_e", use_case="careers", output_dir="/tmp"))
    await db.append_event(RunEventRow(run_id="run_e", stage="fetch", message="scraping /careers"))
    await db.append_event(RunEventRow(run_id="run_e", stage="extract", message="found 12 roles"))
    events = await db.get_events("run_e")
    assert len(events) == 2
    assert events[0].stage == "fetch"
    assert events[1].message == "found 12 roles"


async def test_get_events_empty_for_unknown_run(db: RunDB) -> None:
    assert await db.get_events("ghost") == []


async def test_restart_recovery(tmp_path) -> None:
    """New RunDB instance on same file recovers previously saved runs."""
    path = str(tmp_path / "persist.db")
    db1 = RunDB(path)
    await db1.init_db()
    await db1.save_run(RunRow(run_id="run_survive", use_case="investor", output_dir="/tmp"))
    await db1.append_event(RunEventRow(run_id="run_survive", stage="done", message="finished"))
    await db1.close()

    db2 = RunDB(path)
    await db2.init_db()
    got = await db2.get_run("run_survive")
    assert got is not None
    assert got.use_case == "investor"
    events = await db2.get_events("run_survive")
    assert len(events) == 1
    assert events[0].message == "finished"
    await db2.close()


async def test_delete_run_removes_run_and_events(db: RunDB) -> None:
    await db.save_run(RunRow(run_id="run_del", use_case="docs", output_dir="/tmp"))
    await db.append_event(RunEventRow(run_id="run_del", stage="x", message="y"))
    await db.delete_run("run_del")
    assert await db.get_run("run_del") is None
    assert await db.get_events("run_del") == []
