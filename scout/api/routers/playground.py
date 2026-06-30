"""Anonymous hosted playground routes with strict demo limits."""

from __future__ import annotations

import json
import time
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from scout.api.deps import get_crawler
from scout.core.crawler import ScoutCrawler
from scout.core.platform.url_safety import validate_hosted_url_with_dns
from scout.core.types import CrawlRequest, ProductCrawlRequest


router = APIRouter(prefix="/v1/playground", tags=["playground"])

_MAX_PRODUCTS = 10
_MAX_PAGES = 5
_MAX_DEPTH = 1
_TIMEOUT_MS = 30_000
_RATE_WINDOW_SECONDS = 60 * 60
_RATE_MAX_REQUESTS = 5
_RATE_BUCKETS: dict[str, list[float]] = {}


class PlaygroundRunRequest(BaseModel):
    """Public playground request for a small hosted Scout demo."""

    workflow: Literal["products", "website"]
    url: str
    output_format: Literal["json", "markdown"] = "json"
    max_items: int = Field(default=5, ge=1)


class PlaygroundRunResponse(BaseModel):
    """Downloadable playground response shown directly in the docs page."""

    success: bool
    workflow: str
    url: str
    output_format: str
    limits: dict[str, int]
    summary: dict[str, int | str | bool]
    records: list[dict[str, Any]]
    blocked_pages: list[dict[str, Any]] = Field(default_factory=list)
    downloads: dict[str, str]
    download_filenames: dict[str, str]
    error: str = ""


@router.post("/run", response_model=PlaygroundRunResponse)
async def playground_run(
    req: PlaygroundRunRequest,
    request: Request,
    crawler: ScoutCrawler = Depends(get_crawler),
) -> PlaygroundRunResponse:
    """Run a capped public demo without requiring a hosted API key."""
    _enforce_playground_rate_limit(_client_key(request))
    _enforce_playground_url_safety(req.url)
    if req.workflow == "products":
        return await _run_products_playground(req, crawler)
    return await _run_website_playground(req, crawler)


async def _run_products_playground(
    req: PlaygroundRunRequest, crawler: ScoutCrawler
) -> PlaygroundRunResponse:
    max_products = min(req.max_items, _MAX_PRODUCTS)
    product_req = ProductCrawlRequest(
        query="playground products",
        start_url=req.url,
        max_categories=1,
        limit_per_category=_MAX_PRODUCTS,
        max_products=max_products,
        persist=False,
        use_js=True,
        timeout_ms=_TIMEOUT_MS,
        browser_fallback=False,
        browser_fallback_headless=True,
    )
    response = await crawler.products(product_req)
    records = [record.model_dump(mode="json", by_alias=True) for record in response.records]
    blocked = [page.model_dump(mode="json") for page in response.blocked_pages]
    downloads = _downloads_for_records(
        workflow="products",
        records=records,
        markdown=_product_markdown(records, blocked),
    )
    return PlaygroundRunResponse(
        success=response.success,
        workflow="products",
        url=req.url,
        output_format=req.output_format,
        limits={"max_products": _MAX_PRODUCTS, "timeout_ms": _TIMEOUT_MS},
        summary={
            "record_count": len(records),
            "blocked_count": len(blocked),
            "duration_ms": response.duration_ms,
            "capped": True,
        },
        records=records,
        blocked_pages=blocked,
        downloads=downloads,
        download_filenames=_download_filenames("products"),
        error=response.error,
    )


async def _run_website_playground(
    req: PlaygroundRunRequest, crawler: ScoutCrawler
) -> PlaygroundRunResponse:
    max_pages = min(req.max_items, _MAX_PAGES)
    crawl_req = CrawlRequest(
        url=req.url,
        max_depth=_MAX_DEPTH,
        max_pages=max_pages,
        include_external=False,
        use_js=True,
        timeout_ms=_TIMEOUT_MS,
    )
    response = await crawler.crawl(crawl_req)
    records = [
        {
            "url": page.url,
            "title": page.metadata.title,
            "markdown": page.markdown,
            "success": page.success,
            "error": page.error,
            "word_count": page.metadata.word_count,
        }
        for page in response.pages
    ]
    downloads = _downloads_for_records(
        workflow="website",
        records=records,
        markdown=_website_markdown(records),
    )
    return PlaygroundRunResponse(
        success=response.success,
        workflow="website",
        url=req.url,
        output_format=req.output_format,
        limits={"max_pages": _MAX_PAGES, "max_depth": _MAX_DEPTH, "timeout_ms": _TIMEOUT_MS},
        summary={
            "page_count": len(records),
            "duration_ms": response.duration_ms,
            "capped": True,
        },
        records=records,
        downloads=downloads,
        download_filenames=_download_filenames("website"),
        error=response.error,
    )


def _enforce_playground_url_safety(url: str) -> None:
    result = validate_hosted_url_with_dns(url)
    if result.allowed:
        return
    raise HTTPException(status_code=403, detail=f"Unsafe playground URL: {result.reason}")


def _enforce_playground_rate_limit(client_key: str) -> None:
    now = time.time()
    window_start = now - _RATE_WINDOW_SECONDS
    bucket = [ts for ts in _RATE_BUCKETS.get(client_key, []) if ts >= window_start]
    if len(bucket) >= _RATE_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Playground limit reached. Sign up for hosted beta for more runs.",
            headers={"Retry-After": str(_RATE_WINDOW_SECONDS)},
        )
    bucket.append(now)
    _RATE_BUCKETS[client_key] = bucket


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"


def _downloads_for_records(
    workflow: str, records: list[dict[str, Any]], markdown: str
) -> dict[str, str]:
    payload = {"workflow": workflow, "records": records}
    return {
        "json": json.dumps(payload, indent=2, ensure_ascii=False),
        "markdown": markdown,
    }


def _download_filenames(workflow: str) -> dict[str, str]:
    return {
        "json": f"scout-playground-{workflow}.json",
        "markdown": f"scout-playground-{workflow}.md",
    }


def _product_markdown(records: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> str:
    lines = ["# Scout playground products", ""]
    for record in records:
        name = record.get("name") or "Untitled product"
        url = record.get("url") or ""
        price = record.get("price")
        lines.append(f"- **{name}**")
        if price is not None:
            lines.append(f"  - Price: {price}")
        if url:
            lines.append(f"  - URL: {url}")
    if blocked:
        lines.extend(["", "## Blocked pages"])
        for page in blocked:
            lines.append(f"- {page.get('url', '')}: {page.get('reason', '')}")
    return "\n".join(lines).strip() + "\n"


def _website_markdown(records: list[dict[str, Any]]) -> str:
    lines = ["# Scout playground website crawl", ""]
    for record in records:
        title = record.get("title") or record.get("url") or "Untitled page"
        lines.extend([f"## {title}", "", str(record.get("markdown") or "").strip(), ""])
    return "\n".join(lines).strip() + "\n"
