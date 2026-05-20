"""High-level Scout run router."""

from __future__ import annotations

from fastapi import APIRouter

from scout.core.platform.run import run_use_case
from scout.core.platform.types import RunRequest, RunResponse

router = APIRouter(tags=["run"])


@router.post("/run/{use_case}", response_model=RunResponse)
async def run_high_level_use_case(use_case: str, req: RunRequest) -> RunResponse:
    data = req.model_copy(update={"use_case": use_case})
    return run_use_case(data)
