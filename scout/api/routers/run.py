"""High-level Scout run router."""

from __future__ import annotations

from fastapi import APIRouter

from scout.api.config import settings
from scout.api.run_store import remember_run
from scout.core.platform.run import run_use_case
from scout.core.platform.types import RunRequest, RunResponse
from scout.core.platform.workspace import resolve_run_output_dir

router = APIRouter(tags=["run"])


@router.post("/run/{use_case}", response_model=RunResponse)
async def run_high_level_use_case(use_case: str, req: RunRequest) -> RunResponse:
    data = req.model_copy(
        update={
            "use_case": use_case,
            "output_dir": resolve_run_output_dir(
                use_case=use_case,
                query=req.query,
                output_dir=req.output_dir,
                workdir=settings.scout_workdir,
            ),
        }
    )
    resp = run_use_case(data)
    if resp.manifest is not None:
        await remember_run(resp.manifest)
    return resp
