"""Algolia preparation and preview endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["algolia"])


class AlgoliaPreviewRequest(BaseModel):
    app_id: str = ""
    api_key: str = ""
    index_name: str = ""
    records: list[dict[str, Any]] = Field(default_factory=list)


class AlgoliaCredentialStatus(BaseModel):
    app_id_configured: bool
    api_key_configured: bool


class AlgoliaPreviewResponse(BaseModel):
    ready: bool
    index_name: str = ""
    record_count: int = 0
    sample_object_ids: list[str] = Field(default_factory=list)
    missing_required_fields: list[str] = Field(default_factory=list)
    credentials: AlgoliaCredentialStatus
    ingest_supported: bool = False
    message: str = "Preview only. Real Algolia ingestion is a future extension."


@router.post("/algolia/preview", response_model=AlgoliaPreviewResponse)
async def preview_algolia_records(req: AlgoliaPreviewRequest) -> AlgoliaPreviewResponse:
    missing = _missing_fields(req)
    object_ids = [
        str(record.get("objectID")) for record in req.records if record.get("objectID") is not None
    ][:10]
    return AlgoliaPreviewResponse(
        ready=not missing,
        index_name=req.index_name,
        record_count=len(req.records),
        sample_object_ids=object_ids,
        missing_required_fields=missing,
        credentials=AlgoliaCredentialStatus(
            app_id_configured=bool(req.app_id.strip()),
            api_key_configured=bool(req.api_key.strip()),
        ),
    )


def _missing_fields(req: AlgoliaPreviewRequest) -> list[str]:
    missing: list[str] = []
    if not req.index_name.strip():
        missing.append("index_name")
    if not req.app_id.strip():
        missing.append("app_id")
    if not req.api_key.strip():
        missing.append("api_key")
    if not req.records:
        missing.append("records")
    for index, record in enumerate(req.records):
        for field in ("objectID", "name", "url"):
            if not record.get(field):
                missing.append(f"records[{index}].{field}")
    return missing
