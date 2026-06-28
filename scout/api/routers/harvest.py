"""POST /harvest — extract structured records from a live browser over CDP.

PRISM-callable: consumer provides a CDP URL pointing at an already-open,
already-cleared Chrome tab. Crawl4AI attaches over CDP (js_only=True — no
re-navigation, no wall re-trigger) and extracts markdown + typed records.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from scout.core.cdp_acquire import acquire_open_page
from scout.core.products.captured import product_records_from_captured_html
from scout.core.types import CaptureExtraction

router = APIRouter()


class HarvestRequest(BaseModel):
    cdp_url: str
    url: str
    css_schema: dict | None = None
    scan_full_page: bool = True
    record_type: str = ""
    category_name: str = ""
    links: list[str] = Field(default_factory=list)
    limit: int = 25


@router.post("/harvest", response_model=CaptureExtraction)
async def harvest_tab(req: HarvestRequest) -> CaptureExtraction:
    """Attach Crawl4AI to a live browser tab over CDP and extract records."""
    captured = await acquire_open_page(
        req.cdp_url,
        req.url,
        css_schema=req.css_schema,
        scan_full_page=req.scan_full_page,
    )
    if not captured.success or req.record_type.lower() not in {"product", "products"}:
        return captured

    records = product_records_from_captured_html(
        html=captured.raw_html,
        source_url=captured.source_url or req.url,
        category_name=req.category_name,
        links=req.links,
        limit=req.limit,
    )
    return captured.model_copy(update={"records": records, "record_count": len(records)})
