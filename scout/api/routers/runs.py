"""Run artifact lookup endpoints for the Scout frontend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from scout.api.run_store import artifact_path, get_run

router = APIRouter(tags=["runs"])


@router.get("/runs/{run_id}")
async def get_run_summary(run_id: str) -> dict[str, Any]:
    run = _require_run(run_id)
    return run.model_dump(mode="json")


@router.get("/runs/{run_id}/records")
async def get_run_records(run_id: str) -> dict[str, Any]:
    run = _require_run(run_id)
    records = _read_json_list(artifact_path(run, "records_json"))
    return {"run_id": run_id, "total": len(records), "records": records}


@router.get("/runs/{run_id}/sources")
async def get_run_sources(run_id: str) -> dict[str, Any]:
    run = _require_run(run_id)
    sources = _read_json_list(artifact_path(run, "source_pages_json"))
    return {"run_id": run_id, "total": len(sources), "sources": sources}


@router.get("/runs/{run_id}/artifacts")
async def get_run_artifacts(run_id: str) -> dict[str, Any]:
    run = _require_run(run_id)
    return {
        "run_id": run_id,
        "output_dir": run.output_dir,
        "artifacts": run.artifacts.model_dump(mode="json"),
    }


def _require_run(run_id: str):
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return run


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact not found: {path}")
    data = json.loads(path.read_text())
    return data if isinstance(data, list) else []
