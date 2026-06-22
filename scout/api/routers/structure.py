"""POST /structure — structure raw HTML into markdown + typed records.

PRISM-callable: takes HTML a consumer already holds, runs it through Crawl4AI
via the raw:// scheme (no network fetch), returns clean markdown and optional
typed records when a CSS or LLM schema is supplied.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from scout.core.capture_extract import structure_capture
from scout.core.types import CaptureExtraction

router = APIRouter()


class StructureRequest(BaseModel):
    html: str
    source_url: str = ""
    css_schema: dict | None = None
    llm_schema: dict | None = None


@router.post("/structure", response_model=CaptureExtraction)
async def structure_html(req: StructureRequest) -> CaptureExtraction:
    """Structure held HTML into markdown + records via Crawl4AI (no fetch)."""
    return await structure_capture(
        req.html,
        source_url=req.source_url,
        css_schema=req.css_schema,
        llm_schema=req.llm_schema,
    )
