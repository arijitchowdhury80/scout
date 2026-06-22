"""POST /harvest — extract structured records from a live browser over CDP.

PRISM-callable: consumer provides a CDP URL pointing at an already-open,
already-cleared Chrome tab. Crawl4AI attaches over CDP (js_only=True — no
re-navigation, no wall re-trigger) and extracts markdown + typed records.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from scout.core.cdp_acquire import acquire_open_page
from scout.core.types import CaptureExtraction

router = APIRouter()


class HarvestRequest(BaseModel):
    cdp_url: str
    url: str
    css_schema: dict | None = None
    scan_full_page: bool = True


@router.post("/harvest", response_model=CaptureExtraction)
async def harvest_tab(req: HarvestRequest) -> CaptureExtraction:
    """Attach Crawl4AI to a live browser tab over CDP and extract records."""
    return await acquire_open_page(
        req.cdp_url,
        req.url,
        css_schema=req.css_schema,
        scan_full_page=req.scan_full_page,
    )
