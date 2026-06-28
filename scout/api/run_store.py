"""Run registry — write-through cache (in-memory + SQLite).

In-process dict for fast reads during active runs; SQLite for persistence
across restarts.  When RunDB is not wired in (e.g. unit tests that don't
start the full app), falls back to in-memory-only behaviour.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from scout.api.db import RunDB, RunRow
from scout.core.platform.types import ArtifactFiles, RunManifest


class StoredRun(BaseModel):
    run_id: str
    use_case: str
    query: str = ""
    status: str = "complete"
    tenant_id: str = ""
    key_id: str = ""
    output_dir: str
    artifacts: ArtifactFiles


_RUNS: dict[str, StoredRun] = {}
_DB: RunDB | None = None


def bind_db(db: RunDB) -> None:
    """Called once at startup to wire the SQLite backend."""
    global _DB
    _DB = db


def _db_ready() -> bool:
    return _DB is not None and _DB._conn is not None


async def remember_run(manifest: RunManifest, tenant_id: str = "", key_id: str = "") -> None:
    """Persist a completed run to both cache and DB."""
    if not manifest.run_id:
        return
    stored = StoredRun(
        run_id=manifest.run_id,
        use_case=manifest.use_case,
        query=manifest.query,
        tenant_id=tenant_id,
        key_id=key_id,
        output_dir=manifest.output_dir,
        artifacts=manifest.artifacts,
    )
    _RUNS[manifest.run_id] = stored
    if _db_ready():
        assert _DB is not None
        await _DB.save_run(
            RunRow(
                run_id=manifest.run_id,
                use_case=manifest.use_case,
                query=manifest.query,
                status="complete",
                tenant_id=tenant_id,
                key_id=key_id,
                output_dir=manifest.output_dir,
                artifacts_json=manifest.artifacts.model_dump_json(),
            )
        )


async def get_run(run_id: str) -> StoredRun | None:
    """Look up by run_id — cache first, then DB."""
    cached = _RUNS.get(run_id)
    if cached is not None:
        return cached
    if not _db_ready():
        return None
    assert _DB is not None
    row = await _DB.get_run(run_id)
    if row is None:
        return None
    stored = StoredRun(
        run_id=row.run_id,
        use_case=row.use_case,
        query=row.query,
        status=row.status,
        tenant_id=row.tenant_id,
        key_id=row.key_id,
        output_dir=row.output_dir,
        artifacts=ArtifactFiles(**json.loads(row.artifacts_json)),
    )
    _RUNS[run_id] = stored
    return stored


def artifact_path(run: StoredRun, artifact_name: str) -> Path:
    value = getattr(run.artifacts, artifact_name)
    return Path(value)
