"""Algolia preparation, preview, and push endpoints."""

from __future__ import annotations

from typing import Any

from algoliasearch.search.client import SearchClientSync
from fastapi import APIRouter
from pydantic import BaseModel, Field, model_validator

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
    ingest_supported: bool = True
    message: str = "Preview records before pushing to Algolia via POST /algolia/push."


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


class AlgoliaPushRequest(BaseModel):
    app_id: str
    api_key: str
    index_name: str
    records: list[dict[str, Any]]
    batch_size: int = 1000

    @model_validator(mode="after")
    def _validate_non_empty(self) -> "AlgoliaPushRequest":
        if not self.app_id.strip():
            raise ValueError("app_id is required")
        if not self.api_key.strip():
            raise ValueError("api_key is required")
        if not self.index_name.strip():
            raise ValueError("index_name is required")
        if not self.records:
            raise ValueError("records must not be empty")
        return self


class AlgoliaPushResponse(BaseModel):
    success: bool
    index_name: str = ""
    records_pushed: int = 0
    object_ids: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


@router.post("/algolia/push", response_model=AlgoliaPushResponse)
async def push_to_algolia(req: AlgoliaPushRequest) -> AlgoliaPushResponse:
    try:
        client = SearchClientSync(app_id=req.app_id, api_key=req.api_key)
        responses = client.save_objects(
            index_name=req.index_name,
            objects=req.records,
            batch_size=req.batch_size,
        )
        all_ids: list[str] = []
        for batch_resp in responses:
            all_ids.extend(batch_resp.object_ids)
        return AlgoliaPushResponse(
            success=True,
            index_name=req.index_name,
            records_pushed=len(all_ids),
            object_ids=all_ids,
        )
    except Exception as exc:
        return AlgoliaPushResponse(
            success=False,
            index_name=req.index_name,
            errors=[str(exc)],
        )
