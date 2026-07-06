"""Anonymous PLG homepage demo endpoint — no auth, fast modes only.

Spec: docs/product/plg-playground-ux.md ("Anonymous console limits").

This is the shallowest, most public-facing surface Scout has: the homepage
console visitors hit before signing up. It intentionally exposes only the two
FAST core modes (scrape single URL, map) — never crawl/products/company/
screenshot, which are minutes-long and/or costly, and never anything that
touches persistence (RunDB, Algolia). Output is always a truncated PREVIEW
with an explicit upsell message; nothing here is meant to be a durable
artifact for the caller.

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
from scout.core.types import MapRequest, ScrapeRequest, ScoutFormats

router = APIRouter(prefix="/v1/demo", tags=["demo"])

# --- Fast-endpoints-only invariant --------------------------------------------------
# Documented allowlist. Never add crawl/products/company/screenshot here — the
# anonymous console is explicitly restricted to sub-second/low-second modes.
ALLOWED_WORKFLOWS = {"scrape", "map"}

# --- Preview / truncation caps -------------------------------------------------------
MAX_PREVIEW_CHARS = 2_000
MAX_MAP_URLS = 15
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
