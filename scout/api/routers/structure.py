"""POST /structure — structure raw HTML into markdown + typed records.

PRISM-callable: takes HTML a consumer already holds, runs it through Crawl4AI
via the raw:// scheme (no network fetch), returns clean markdown and optional
typed records when a CSS or LLM schema is supplied.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from scout.core.capture_extract import structure_capture
from scout.core.products.captured import product_records_from_captured_html
from scout.core.types import CaptureExtraction

router = APIRouter()


class StructureRequest(BaseModel):
    html: str
    source_url: str = ""
    css_schema: dict | None = None
    llm_schema: dict | None = None
    record_type: str = ""
    category_name: str = ""
    links: list[str] = Field(default_factory=list)
    limit: int = 25


@router.post("/structure", response_model=CaptureExtraction)
async def structure_html(req: StructureRequest) -> CaptureExtraction:
    """Structure held HTML into markdown + records via Crawl4AI (no fetch)."""
    structured = await structure_capture(
        req.html,
        source_url=req.source_url,
        css_schema=req.css_schema,
        llm_schema=req.llm_schema,
    )
    if not structured.success or req.record_type.lower() not in {"product", "products"}:
        return structured

    records = product_records_from_captured_html(
        html=req.html,
        source_url=req.source_url,
        category_name=req.category_name,
        links=req.links,
        limit=req.limit,
    )
    structured.records = records
    structured.record_count = len(records)
    return structured
