"""Anonymous hosted playground routes with strict demo limits."""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from scout.api.deps import get_crawler
from scout.core.crawler import ScoutCrawler
from scout.core.platform.run import run_use_case
from scout.core.platform.url_safety import validate_hosted_url_with_dns
from scout.core.platform.types import RunRequest
from scout.core.types import (
    CrawlRequest,
    ExtractRequest,
    MapRequest,
    ProductCrawlRequest,
    ScoutFormats,
    ScrapeRequest,
    ScreenshotRequest,
)


router = APIRouter(prefix="/v1/playground", tags=["playground"])

_MAX_PRODUCTS = 10
_MAX_PAGES = 5
_MAX_DEPTH = 1
_TIMEOUT_MS = 30_000
_RATE_WINDOW_SECONDS = 60 * 60
_RATE_MAX_REQUESTS = 5
_RATE_BUCKETS: dict[str, list[float]] = {}
_MAX_RECORDS = 10
_INTELLIGENCE_CAPABILITIES = {
    "company",
    "prism",
    "investor",
    "careers",
    "jobs",
    "news",
    "research",
    "docs",
    "social",
    "locations",
    "website-quality",
}

_CAPABILITIES: list[dict[str, str]] = [
    {
        "name": "scrape",
        "label": "Scrape",
        "category": "Acquire",
        "description": "Fetch one page and return clean markdown plus evidence metadata.",
    },
    {
        "name": "crawl",
        "label": "Crawl",
        "category": "Acquire",
        "description": "Crawl one site level and return up to five pages.",
    },
    {
        "name": "map",
        "label": "Map",
        "category": "Acquire",
        "description": "Discover URLs from a public site without extracting full content.",
    },
    {
        "name": "screenshot",
        "label": "Screenshot",
        "category": "Acquire",
        "description": "Capture one rendered page screenshot.",
    },
    {
        "name": "extract",
        "label": "Extract",
        "category": "Structure",
        "description": "Extract a small structured record from a page.",
    },
    {
        "name": "docs",
        "label": "Docs",
        "category": "Structure",
        "description": "Turn docs pages into reusable research records.",
    },
    {
        "name": "research",
        "label": "Research",
        "category": "Structure",
        "description": "Summarize target pages into cited research records.",
    },
    {
        "name": "products",
        "label": "Products",
        "category": "Commerce",
        "description": "Extract up to ten product records with source citations.",
    },
    {
        "name": "company",
        "label": "Company",
        "category": "Intelligence",
        "description": "Company overview, about evidence, socials, and leadership signals.",
    },
    {
        "name": "prism",
        "label": "PRISM",
        "category": "Intelligence",
        "description": "Company, careers, investor, news, and social evidence bundle.",
    },
    {
        "name": "investor",
        "label": "Investor",
        "category": "Intelligence",
        "description": "Investor relations pages, report signals, filings, and assets.",
    },
    {
        "name": "careers",
        "label": "Careers",
        "category": "Intelligence",
        "description": "Careers page, ATS, departments, and hiring signals.",
    },
    {
        "name": "jobs",
        "label": "Jobs",
        "category": "Intelligence",
        "description": "Job target/profile records and job evidence where supplied.",
    },
    {
        "name": "news",
        "label": "News",
        "category": "Intelligence",
        "description": "Newsroom and blog signal extraction.",
    },
    {
        "name": "social",
        "label": "Social",
        "category": "Intelligence",
        "description": "Social profile URL discovery and normalization.",
    },
    {
        "name": "locations",
        "label": "Locations",
        "category": "Intelligence",
        "description": "Store, office, or location page signals.",
    },
    {
        "name": "website-quality",
        "label": "Website Quality",
        "category": "Intelligence",
        "description": "UX, SEO, semantic HTML, and evidence-backed quality signals.",
    },
]
_CAPABILITY_NAMES = {capability["name"] for capability in _CAPABILITIES}


class PlaygroundRunRequest(BaseModel):
    """Public playground request for a small hosted Scout demo."""

    workflow: str
    url: str
    query: str = ""
    output_format: Literal["json", "markdown"] = "json"
    max_items: int = Field(default=5, ge=1)


class PlaygroundCapabilityResponse(BaseModel):
    """Capability catalog shown by the public playground."""

    capabilities: list[dict[str, str]]
    limits: dict[str, int]


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


@router.get("/capabilities", response_model=PlaygroundCapabilityResponse)
async def playground_capabilities() -> PlaygroundCapabilityResponse:
    """Return the public playground capability catalog."""
    return PlaygroundCapabilityResponse(
        capabilities=_CAPABILITIES,
        limits={
            "max_products": _MAX_PRODUCTS,
            "max_pages": _MAX_PAGES,
            "max_depth": _MAX_DEPTH,
            "max_records": _MAX_RECORDS,
            "timeout_ms": _TIMEOUT_MS,
            "requests_per_hour": _RATE_MAX_REQUESTS,
        },
    )


@router.post("/run", response_model=PlaygroundRunResponse)
async def playground_run(
    req: PlaygroundRunRequest,
    request: Request,
    crawler: ScoutCrawler = Depends(get_crawler),
) -> PlaygroundRunResponse:
    """Run a capped public demo without requiring a hosted API key."""
    req = req.model_copy(update={"workflow": _normalize_workflow(req.workflow)})
    if req.workflow not in _CAPABILITY_NAMES:
        raise HTTPException(
            status_code=400, detail=f"Unsupported playground workflow: {req.workflow}"
        )
    _enforce_playground_rate_limit(_client_key(request))
    _enforce_playground_url_safety(req.url)
    if req.workflow == "products":
        return await _run_products_playground(req, crawler)
    if req.workflow == "crawl":
        return await _run_crawl_playground(req, crawler)
    if req.workflow == "scrape":
        return await _run_scrape_playground(req, crawler)
    if req.workflow == "map":
        return await _run_map_playground(req, crawler)
    if req.workflow == "extract":
        return await _run_extract_playground(req, crawler)
    if req.workflow == "screenshot":
        return await _run_screenshot_playground(req, crawler)
    if req.workflow in _INTELLIGENCE_CAPABILITIES:
        return await _run_intelligence_playground(req, crawler)
    raise HTTPException(status_code=400, detail=f"Unsupported playground workflow: {req.workflow}")


def _normalize_workflow(workflow: str) -> str:
    value = workflow.strip().lower()
    if value == "website":
        return "crawl"
    return value


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


async def _run_crawl_playground(
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
        workflow="crawl",
        records=records,
        markdown=_website_markdown(records),
    )
    return PlaygroundRunResponse(
        success=response.success,
        workflow="crawl",
        url=req.url,
        output_format=req.output_format,
        limits={"max_pages": _MAX_PAGES, "max_depth": _MAX_DEPTH, "timeout_ms": _TIMEOUT_MS},
        summary={
            "record_count": len(records),
            "page_count": len(records),
            "duration_ms": response.duration_ms,
            "capped": True,
        },
        records=records,
        downloads=downloads,
        download_filenames=_download_filenames("crawl"),
        error=response.error,
    )


async def _run_scrape_playground(
    req: PlaygroundRunRequest, crawler: ScoutCrawler
) -> PlaygroundRunResponse:
    response = await crawler.scrape(
        ScrapeRequest(
            url=req.url,
            formats=[ScoutFormats.MARKDOWN, ScoutFormats.RAW_HTML],
            use_js=True,
            timeout_ms=_TIMEOUT_MS,
        )
    )
    record = {
        "record_type": "scrape_result",
        "url": response.url,
        "final_url": response.final_url or response.url,
        "title": response.metadata.title,
        "markdown": response.markdown,
        "content_hash": response.content_hash,
        "quality_score": response.quality_score,
        "quality_reasons": response.quality_reasons,
        "success": response.success,
        "error": response.error,
    }
    return _response_from_records(
        req=req,
        records=[record],
        duration_ms=response.duration_ms,
        success=response.success,
        markdown=_generic_markdown("Scout playground scrape", [record]),
        error=response.error,
        limits={"max_pages": 1, "timeout_ms": _TIMEOUT_MS},
    )


async def _run_map_playground(
    req: PlaygroundRunRequest, crawler: ScoutCrawler
) -> PlaygroundRunResponse:
    response = await crawler.map_urls(
        MapRequest(
            url=req.url,
            max_pages=_MAX_PAGES,
            include_external=False,
            stealth=True,
        )
    )
    records = [
        {"record_type": "mapped_url", "url": url, "position": i + 1}
        for i, url in enumerate(response.urls[:_MAX_PAGES])
    ]
    return _response_from_records(
        req=req,
        records=records,
        duration_ms=response.duration_ms,
        success=response.success,
        markdown=_generic_markdown("Scout playground map", records),
        error=response.error,
        limits={"max_pages": _MAX_PAGES, "timeout_ms": _TIMEOUT_MS},
    )


async def _run_extract_playground(
    req: PlaygroundRunRequest, crawler: ScoutCrawler
) -> PlaygroundRunResponse:
    response = await crawler.extract(
        ExtractRequest(
            url=req.url,
            instruction="Extract a concise title and summary for the public Scout playground.",
            css_schema={
                "name": "playground_extract",
                "baseSelector": "body",
                "fields": [
                    {"name": "title", "selector": "h1,title", "type": "text"},
                    {"name": "summary", "selector": "p", "type": "text"},
                ],
            },
            use_js=True,
            timeout_ms=_TIMEOUT_MS,
        )
    )
    record = {
        "record_type": "extract_result",
        "url": response.url,
        "data": response.data,
        "markdown": response.markdown,
        "title": response.metadata.title,
        "success": response.success,
        "error": response.error,
    }
    return _response_from_records(
        req=req,
        records=[record],
        duration_ms=response.duration_ms,
        success=response.success,
        markdown=_generic_markdown("Scout playground extract", [record]),
        error=response.error,
        limits={"max_pages": 1, "timeout_ms": _TIMEOUT_MS},
    )


async def _run_screenshot_playground(
    req: PlaygroundRunRequest, crawler: ScoutCrawler
) -> PlaygroundRunResponse:
    response = await crawler.screenshot(
        ScreenshotRequest(
            url=req.url,
            full_page=False,
            viewport_width=1280,
            viewport_height=800,
            use_js=True,
        )
    )
    record = {
        "record_type": "screenshot_result",
        "url": response.url,
        "width": response.width,
        "height": response.height,
        "screenshot_base64": response.screenshot_base64,
        "success": response.success,
        "error": response.error,
    }
    return _response_from_records(
        req=req,
        records=[record],
        duration_ms=response.duration_ms,
        success=response.success,
        markdown=_generic_markdown("Scout playground screenshot", [record]),
        error=response.error,
        limits={"max_pages": 1, "timeout_ms": _TIMEOUT_MS},
    )


async def _run_intelligence_playground(
    req: PlaygroundRunRequest, crawler: ScoutCrawler
) -> PlaygroundRunResponse:
    with tempfile.TemporaryDirectory(prefix=f"scout-playground-{req.workflow}-") as tmp:
        run_req = RunRequest(
            use_case=req.workflow,
            query=req.query or req.url,
            url=req.url,
            targets=[req.url],
            output_dir=tmp,
            mode="auto",
            max_targets=3,
            max_records=_MAX_RECORDS,
        )
        if req.workflow == "jobs":
            run_req = run_req.model_copy(update={"targets": [req.query or req.url]})
        response = await run_use_case(run_req, crawler)
        records = _read_records(Path(tmp))[:_MAX_RECORDS]
        blocked = _read_json_list(Path(tmp) / "blocked_pages.json")
        markdown = _read_text(Path(tmp) / "extraction_report.md") or _generic_markdown(
            f"Scout playground {req.workflow}", records
        )

    return PlaygroundRunResponse(
        success=response.success or bool(records),
        workflow=req.workflow,
        url=req.url,
        output_format=req.output_format,
        limits={"max_records": _MAX_RECORDS, "timeout_ms": _TIMEOUT_MS},
        summary={
            "record_count": len(records),
            "blocked_count": len(blocked),
            "duration_ms": 0,
            "capped": True,
        },
        records=records,
        blocked_pages=blocked,
        downloads=_downloads_for_records(req.workflow, records, markdown),
        download_filenames=_download_filenames(req.workflow),
        error=response.error,
    )


def _response_from_records(
    *,
    req: PlaygroundRunRequest,
    records: list[dict[str, Any]],
    duration_ms: int,
    success: bool,
    markdown: str,
    error: str,
    limits: dict[str, int],
) -> PlaygroundRunResponse:
    return PlaygroundRunResponse(
        success=success or bool(records),
        workflow=req.workflow,
        url=req.url,
        output_format=req.output_format,
        limits=limits,
        summary={
            "record_count": len(records),
            "blocked_count": 0,
            "duration_ms": duration_ms,
            "capped": True,
        },
        records=records,
        downloads=_downloads_for_records(req.workflow, records, markdown),
        download_filenames=_download_filenames(req.workflow),
        error=error,
    )


def _read_records(output_dir: Path) -> list[dict[str, Any]]:
    data = _read_json_list(output_dir / "records.json")
    return [record for record in data if isinstance(record, dict)]


def _read_json_list(path: Path) -> list[Any]:
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


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


def _generic_markdown(title: str, records: list[dict[str, Any]]) -> str:
    lines = [f"# {title}", ""]
    for i, record in enumerate(records, start=1):
        heading = (
            record.get("title")
            or record.get("name")
            or record.get("objectID")
            or record.get("url")
            or f"Record {i}"
        )
        lines.extend([f"## {heading}", "", "```json"])
        lines.append(json.dumps(record, indent=2, ensure_ascii=False))
        lines.extend(["```", ""])
    return "\n".join(lines).strip() + "\n"


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
