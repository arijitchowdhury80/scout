"""Anonymous PLG homepage demo endpoint — no auth, scaled-down modes only.

Spec: docs/product/plg-playground-ux.md ("Anonymous console limits").

This is the shallowest, most public-facing surface Scout has: the homepage
console visitors hit before signing up. It exposes four SCALED-DOWN core
modes — scrape single URL, map, crawl (hard-capped at 3 pages, http-first),
and products (hard-capped at 5 records, single-page http-first extraction) —
never full company/screenshot workflows, and never anything that touches
persistence (RunDB, Algolia). Output is always a truncated PREVIEW with an
explicit upsell message; nothing here is meant to be a durable artifact for
the caller.

crawl and products are intentionally NOT full-power here:
  - /v1/demo/crawl reuses the same crawl core mode as the authed API but caps
    max_pages=3 and forces use_js=False (http-first only, no browser) — a
    multi-page crawl is the single costliest anonymous surface, so it is
    capped hard.
  - /v1/demo/products does NOT reuse ProductCrawlRequest/the products runner —
    that request contract is built around multi-category, multi-page
    discovery with optional browser fallback (see
    scout/core/use_cases/products_v2.py), which has no "single page, N
    records" scaled-down knob and is too heavy to run anonymously. Instead
    this endpoint does a single http-first page scrape (requesting raw_html +
    links) and runs it through the existing listing-card extraction core
    (scout/core/products/listing.py + algolia.py) — the same building blocks
    the real products runner uses for category/listing pages — capped at 5
    cards. If extraction finds nothing, the response is still success=True
    with an empty records list and an explanatory `note` field. It never
    fabricates placeholder records.

Abuse controls (this box is shared with PRISM — a bot swarm must not be able
to starve it):
  1. Per-IP daily cap (MAX_RUNS_PER_IP_PER_DAY) — day-bucketed in-process
     counter, keyed by client IP (X-Forwarded-For first hop, else socket peer).
  2. Global daily ceiling (GLOBAL_DAILY_CEILING) — a shared day-bucketed
     counter across ALL anonymous callers, so no combination of IPs (e.g. a
     botnet rotating source addresses) can push unbounded load onto the
     shared host.
  3. A small concurrency admission gate (DemoAdmissionController), separate
     from the authed playground's, so a burst of demo traffic cannot starve
     PRISM or paying customers of crawler capacity.
  4. The existing hosted URL-safety check (validate_hosted_url_with_dns)
     blocks localhost/private/link-local/reserved IP targets — SSRF guard,
     reused as-is.

Both counters are process-local (in-memory), matching the existing pattern in
scout/api/routers/playground.py (_RATE_BUCKETS) and
scout/core/platform/hosted_rate_limit.py. If Scout ever runs multi-process,
these caps need a shared store (Redis) — documented here, not solved here,
per the existing single-process assumption elsewhere in the hosted API.

Wired into scout/api/main.py via app.include_router(demo.router). The
/v1/demo/ prefix is added to AuthMiddleware's public passthrough list —
this surface is intentionally anonymous/no-auth by design (see module intro).
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from scout.api.deps import get_crawler
from scout.core.crawler import ScoutCrawler
from scout.core.platform.url_safety import validate_hosted_url_with_dns
from scout.core.products.algolia import build_listing_algolia_record, is_junk_record
from scout.core.products.listing import extract_listing_cards
from scout.core.types import CrawlRequest, MapRequest, ScrapeRequest, ScoutFormats

router = APIRouter(prefix="/v1/demo", tags=["demo"])

# --- Scaled-down-endpoints-only invariant --------------------------------------------
# Documented allowlist. Never add company/screenshot here, and never let
# crawl/products run at full power — the anonymous console is explicitly
# restricted to fast/cheap/hard-capped modes.
ALLOWED_WORKFLOWS = {"scrape", "map", "crawl", "products"}

# --- Preview / truncation caps -------------------------------------------------------
MAX_PREVIEW_CHARS = 2_000
MAX_MAP_URLS = 15
MAX_CRAWL_PAGES = 3
MAX_PRODUCT_RECORDS = 5
_TIMEOUT_MS = 15_000

UPSELL_MESSAGE = "Sign up to unlock crawl, products, download, and saving."

# --- Abuse controls -------------------------------------------------------------------
MAX_RUNS_PER_IP_PER_DAY = 5
GLOBAL_DAILY_CEILING = 500  # shared ceiling across all anonymous callers, protects the box

_DAY_SECONDS = 24 * 60 * 60

# client_ip -> (day_bucket, count)
_IP_COUNTS: dict[str, tuple[int, int]] = {}
# single shared (day_bucket, count) for the global ceiling
_GLOBAL_COUNT: list[int] = [0, 0]  # [day_bucket, count]


def reset_state_for_tests() -> None:
    """Clear in-process counters. Test-only; production never calls this."""
    _IP_COUNTS.clear()
    _GLOBAL_COUNT[0] = 0
    _GLOBAL_COUNT[1] = 0


def _day_bucket(now: float) -> int:
    return int(now // _DAY_SECONDS)


def _check_and_increment_ip(client_ip: str, now: float) -> None:
    day = _day_bucket(now)
    bucket_day, count = _IP_COUNTS.get(client_ip, (day, 0))
    if bucket_day != day:
        bucket_day, count = day, 0
    if count >= MAX_RUNS_PER_IP_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Demo limit reached ({MAX_RUNS_PER_IP_PER_DAY} runs/day). "
                "Sign up for the free tier for more."
            ),
            headers={"Retry-After": str(_seconds_until_next_day(now))},
        )
    _IP_COUNTS[client_ip] = (bucket_day, count + 1)


def _check_and_increment_global(now: float) -> None:
    day = _day_bucket(now)
    if _GLOBAL_COUNT[0] != day:
        _GLOBAL_COUNT[0] = day
        _GLOBAL_COUNT[1] = 0
    if _GLOBAL_COUNT[1] >= GLOBAL_DAILY_CEILING:
        raise HTTPException(
            status_code=429,
            detail="Demo is at capacity for today. Sign up for the free tier for guaranteed access.",
            headers={"Retry-After": str(_seconds_until_next_day(now))},
        )
    _GLOBAL_COUNT[1] += 1


def _seconds_until_next_day(now: float) -> int:
    day = _day_bucket(now)
    next_boundary = (day + 1) * _DAY_SECONDS
    return max(1, int(next_boundary - now))


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"


def _enforce_demo_rate_limits(request: Request) -> None:
    now = time.time()
    client_ip = _client_key(request)
    _check_and_increment_global(now)
    _check_and_increment_ip(client_ip, now)


def _enforce_demo_url_safety(url: str) -> None:
    result = validate_hosted_url_with_dns(url)
    if result.allowed:
        return
    raise HTTPException(status_code=403, detail=f"Unsafe demo URL: {result.reason}")


def _normalize_public_url(url: str) -> str:
    value = url.strip()
    if not value:
        return value
    if "://" in value:
        return value
    return f"https://{value}"


# --- Concurrency admission (separate ceiling from the authed playground) -------------


class DemoAdmissionRejected(Exception):
    """Raised when no demo worker capacity is currently available."""

    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Demo capacity is full; retry shortly.")


class DemoAdmissionController:
    """Bound concurrent anonymous-demo work, independent of playground/hosted."""

    def __init__(self, max_active: int = 2, retry_after_seconds: int = 5) -> None:
        self.max_active = max(0, max_active)
        self.retry_after_seconds = max(1, retry_after_seconds)
        self._active = 0

    @asynccontextmanager
    async def admit(self) -> AsyncIterator[None]:
        if self._active >= self.max_active:
            raise DemoAdmissionRejected(self.retry_after_seconds)
        self._active += 1
        try:
            yield
        finally:
            self._active = max(0, self._active - 1)


_demo_admission_controller = DemoAdmissionController(max_active=2, retry_after_seconds=5)


def get_demo_crawler(request: Request) -> ScoutCrawler:
    """Return the ScoutCrawler instance stored on app.state at startup.

    Thin, demo-scoped wrapper around the shared get_crawler dependency so tests
    can override just the demo router's crawler without affecting other routers.
    """
    return get_crawler(request)


def get_demo_admission_controller() -> DemoAdmissionController:
    """Return the module-level demo admission controller."""
    return _demo_admission_controller


# --- Request / response contracts ----------------------------------------------------


class DemoScrapeRequest(BaseModel):
    """Anonymous demo scrape request — URL only, no configuration surface."""

    url: str = Field(min_length=1)


class DemoMapRequest(BaseModel):
    """Anonymous demo map request — URL only, no configuration surface."""

    url: str = Field(min_length=1)


class DemoEvidence(BaseModel):
    """Evidence panel shown alongside every demo preview."""

    source: str
    fetched_at: str = ""
    content_hash: str = ""
    verified: bool = False
    blocked: bool = False


class DemoScrapeResponse(BaseModel):
    """Preview-only response for POST /v1/demo/scrape."""

    success: bool
    preview: bool = True
    truncated: bool = False
    record: dict[str, Any]
    evidence: DemoEvidence
    upsell_message: str = UPSELL_MESSAGE
    error: str = ""


class DemoMapResponse(BaseModel):
    """Preview-only response for POST /v1/demo/map."""

    success: bool
    preview: bool = True
    truncated: bool = False
    record: dict[str, Any]
    evidence: DemoEvidence
    upsell_message: str = UPSELL_MESSAGE
    error: str = ""


class DemoCrawlRequest(BaseModel):
    """Anonymous demo crawl request — URL only, no configuration surface."""

    url: str = Field(min_length=1)


class DemoProductsRequest(BaseModel):
    """Anonymous demo products request — URL only, no configuration surface."""

    url: str = Field(min_length=1)


class DemoCrawlResponse(BaseModel):
    """Preview-only response for POST /v1/demo/crawl (hard-capped, http-first)."""

    success: bool
    preview: bool = True
    truncated: bool = False
    record: dict[str, Any]
    evidence: DemoEvidence
    upsell_message: str = UPSELL_MESSAGE
    error: str = ""


class DemoProductsResponse(BaseModel):
    """Preview-only response for POST /v1/demo/products (hard-capped, http-first)."""

    success: bool
    preview: bool = True
    truncated: bool = False
    record: dict[str, Any]
    evidence: DemoEvidence
    upsell_message: str = UPSELL_MESSAGE
    error: str = ""


@router.post("/scrape", response_model=DemoScrapeResponse)
async def demo_scrape(
    req: DemoScrapeRequest,
    request: Request,
    crawler: ScoutCrawler = Depends(get_demo_crawler),
    admission: DemoAdmissionController = Depends(get_demo_admission_controller),
) -> DemoScrapeResponse:
    """Anonymous single-URL scrape preview. No auth, no persistence."""
    url = _normalize_public_url(req.url)
    _enforce_demo_url_safety(url)
    _enforce_demo_rate_limits(request)

    try:
        async with admission.admit():
            response = await crawler.scrape(
                ScrapeRequest(
                    url=url,
                    formats=[ScoutFormats.MARKDOWN],
                    use_js=True,
                    timeout_ms=_TIMEOUT_MS,
                )
            )
    except DemoAdmissionRejected as exc:
        raise HTTPException(
            status_code=429,
            detail="Demo capacity is full; retry shortly.",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc

    markdown = response.markdown or ""
    truncated = len(markdown) > MAX_PREVIEW_CHARS
    preview_markdown = markdown[:MAX_PREVIEW_CHARS]

    record = {
        "record_type": "scrape_preview",
        "url": response.url,
        "final_url": response.final_url or response.url,
        "title": response.metadata.title,
        "markdown": preview_markdown,
        "word_count": response.metadata.word_count,
        "success": response.success,
    }

    return DemoScrapeResponse(
        success=response.success,
        truncated=truncated,
        record=record,
        evidence=DemoEvidence(
            source=response.final_url or response.url,
            fetched_at=response.fetched_at,
            content_hash=response.content_hash,
            verified=response.success,
            blocked=not response.success,
        ),
        error=response.error,
    )


@router.post("/map", response_model=DemoMapResponse)
async def demo_map(
    req: DemoMapRequest,
    request: Request,
    crawler: ScoutCrawler = Depends(get_demo_crawler),
    admission: DemoAdmissionController = Depends(get_demo_admission_controller),
) -> DemoMapResponse:
    """Anonymous URL-discovery preview. No auth, no persistence."""
    url = _normalize_public_url(req.url)
    _enforce_demo_url_safety(url)
    _enforce_demo_rate_limits(request)

    try:
        async with admission.admit():
            response = await crawler.map_urls(
                MapRequest(
                    url=url,
                    max_pages=MAX_MAP_URLS,
                    include_external=False,
                    stealth=True,
                )
            )
    except DemoAdmissionRejected as exc:
        raise HTTPException(
            status_code=429,
            detail="Demo capacity is full; retry shortly.",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc

    total_discovered = response.total
    preview_urls = response.urls[:MAX_MAP_URLS]
    truncated = total_discovered > len(preview_urls)

    record = {
        "record_type": "map_preview",
        "start_url": response.start_url,
        "urls": preview_urls,
        "total_discovered": total_discovered,
        "success": response.success,
    }

    return DemoMapResponse(
        success=response.success,
        truncated=truncated,
        record=record,
        evidence=DemoEvidence(
            source=response.start_url,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            verified=response.success,
            blocked=not response.success,
        ),
        error=response.error,
    )


@router.post("/crawl", response_model=DemoCrawlResponse)
async def demo_crawl(
    req: DemoCrawlRequest,
    request: Request,
    crawler: ScoutCrawler = Depends(get_demo_crawler),
    admission: DemoAdmissionController = Depends(get_demo_admission_controller),
) -> DemoCrawlResponse:
    """Anonymous scaled-down crawl preview: max_pages=3, http-first only. No auth, no persistence."""
    url = _normalize_public_url(req.url)
    _enforce_demo_url_safety(url)
    _enforce_demo_rate_limits(request)

    try:
        async with admission.admit():
            response = await crawler.crawl(
                CrawlRequest(
                    url=url,
                    max_pages=MAX_CRAWL_PAGES,
                    use_js=False,
                    stealth=False,
                    timeout_ms=_TIMEOUT_MS,
                )
            )
    except DemoAdmissionRejected as exc:
        raise HTTPException(
            status_code=429,
            detail="Demo capacity is full; retry shortly.",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc

    pages = response.pages[:MAX_CRAWL_PAGES]
    truncated = response.total_pages > len(pages)
    preview_pages = [
        {
            "url": page.url,
            "title": page.metadata.title,
            "markdown": (page.markdown or "")[:MAX_PREVIEW_CHARS],
            "success": page.success,
        }
        for page in pages
    ]
    if any(len(page.markdown or "") > MAX_PREVIEW_CHARS for page in pages):
        truncated = True

    record = {
        "record_type": "crawl_preview",
        "start_url": response.start_url,
        "pages": preview_pages,
        "total_pages": len(preview_pages),
        "success": response.success,
    }

    return DemoCrawlResponse(
        success=response.success,
        truncated=truncated,
        record=record,
        evidence=DemoEvidence(
            source=response.start_url,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            verified=response.success,
            blocked=not response.success,
        ),
        error=response.error,
    )


@router.post("/products", response_model=DemoProductsResponse)
async def demo_products(
    req: DemoProductsRequest,
    request: Request,
    crawler: ScoutCrawler = Depends(get_demo_crawler),
    admission: DemoAdmissionController = Depends(get_demo_admission_controller),
) -> DemoProductsResponse:
    """Anonymous scaled-down products preview.

    The full products runner (ProductCrawlRequest / products_v2.py) is built
    around multi-category, multi-page discovery with optional browser
    fallback — too heavy to run anonymously. Instead this does a single
    http-first page scrape and extracts up to MAX_PRODUCT_RECORDS product-ish
    cards via the same listing-extraction core the real runner uses for
    category pages. If nothing extractable is found, returns success with an
    empty records list and a `note` explaining why — never fake records.
    """
    url = _normalize_public_url(req.url)
    _enforce_demo_url_safety(url)
    _enforce_demo_rate_limits(request)

    try:
        async with admission.admit():
            response = await crawler.scrape(
                ScrapeRequest(
                    url=url,
                    formats=[ScoutFormats.MARKDOWN, ScoutFormats.RAW_HTML],
                    use_js=False,
                    timeout_ms=_TIMEOUT_MS,
                )
            )
    except DemoAdmissionRejected as exc:
        raise HTTPException(
            status_code=429,
            detail="Demo capacity is full; retry shortly.",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc

    note = ""
    preview_records: list[dict[str, Any]] = []
    total_cards = 0

    if not response.success:
        note = "Could not fetch this page to extract products."
    else:
        final_url = response.final_url or response.url
        cards = extract_listing_cards(
            category_url=final_url,
            category_name="",
            html=response.raw_html or "",
            links=response.links or [],
            limit=MAX_PRODUCT_RECORDS * 3,  # extract generously, then filter+cap below
        )
        usable_cards = [card for card in cards if not is_junk_record(card.name)]
        total_cards = len(usable_cards)
        capped_cards = usable_cards[:MAX_PRODUCT_RECORDS]
        preview_records = [
            build_listing_algolia_record(card).model_dump(by_alias=True) for card in capped_cards
        ]
        if not preview_records:
            note = (
                "No product-like items were found on this page. Scout's demo only "
                "scans a single page without a browser — try a category/listing "
                "page, or sign up for the full products crawl."
            )

    truncated = total_cards > len(preview_records)

    record = {
        "record_type": "products_preview",
        "start_url": response.final_url or response.url,
        "records": preview_records,
        "total_records": len(preview_records),
        "note": note,
        "success": response.success,
    }

    return DemoProductsResponse(
        success=response.success,
        truncated=truncated,
        record=record,
        evidence=DemoEvidence(
            source=response.final_url or response.url,
            fetched_at=response.fetched_at,
            content_hash=response.content_hash,
            verified=response.success,
            blocked=not response.success,
        ),
        error=response.error,
    )
