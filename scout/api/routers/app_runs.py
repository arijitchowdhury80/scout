"""App-first run session router for the Scout frontend."""

from __future__ import annotations

import asyncio
import base64
import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from scout.api.config import settings
from scout.api.deps import get_crawler
from scout.core.crawler import ScoutCrawler
from scout.core.platform.run import run_use_case
from scout.core.platform.types import RunRequest
from scout.core.platform.workspace import resolve_run_output_dir
from scout.core.types import ProductCrawlRequest, ProductCrawlResponse

router = APIRouter(prefix="/app/runs", tags=["app-runs"])


class AppRunEvent(BaseModel):
    stage: str
    message: str
    level: str = "info"
    timestamp: str = Field(default_factory=lambda: _now())


class AppRunRequest(BaseModel):
    use_case: str = "products"
    mode: str = "auto"
    url: str = ""
    query: str = ""
    output_dir: str = ""
    max_depth: int | None = Field(default=None, ge=1, le=10)
    respect_robots_txt: bool | None = None
    delay_seconds: float | None = Field(default=None, ge=0, le=30)
    browser_fallback: bool = True


class AppRunState(BaseModel):
    run_id: str
    status: str
    use_case: str
    mode: str
    target_url: str = ""
    output_dir: str = ""
    created_at: str = Field(default_factory=lambda: _now())
    updated_at: str = Field(default_factory=lambda: _now())
    events: list[AppRunEvent] = Field(default_factory=list)
    records: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    blocked_pages: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)
    browser_evidence: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


_APP_RUNS: dict[str, AppRunState] = {}
_APP_TASKS: dict[str, asyncio.Task[None]] = {}
_APP_WATCHDOGS: dict[str, asyncio.Task[None]] = {}


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _run_id() -> str:
    return f"app_run_{secrets.token_hex(6)}"


def _append(run_id: str, stage: str, message: str, level: str = "info") -> None:
    run = _APP_RUNS[run_id]
    run.events.append(AppRunEvent(stage=stage, message=message, level=level))
    run.updated_at = _now()


def _mark_run_timeout(run_id: str) -> None:
    run = _APP_RUNS.get(run_id)
    if run is None or run.status in {"complete", "failed", "cancelled"}:
        return
    run.blocked_pages = [
        {
            "url": run.target_url,
            "reason": "blocked_timeout",
            "category_url": run.target_url,
            "category_name": run.target_url,
            "title": "Run timed out",
            "fallback_attempted": True,
            "fallback_used": False,
            "fallback_error": "The app-run watchdog stopped waiting for the crawler.",
        }
    ]
    run.sources = [
        {
            "source_url": run.target_url,
            "provider": "watchdog",
            "status_code": None,
            "status": "blocked_timeout",
            "confidence": 0,
            "captured_at": _now(),
            "type": "blocked",
            "reason": "blocked_timeout",
        }
    ]
    run.browser_evidence = {
        "url": run.target_url,
        "title": "Blocked or timed out",
        "provider": run.mode,
        "note": (
            "Scout stopped waiting for this run and preserved blocked/fallback "
            "evidence instead of leaving the UI running."
        ),
    }
    run.status = "failed"
    run.artifacts = _write_app_artifacts(run)
    _append(run_id, "blocked", "Run timed out; blocked/fallback evidence was recorded", "warning")
    _append(run_id, "failed", "Run timed out with blocked evidence", "error")


async def _watch_run_timeout(run_id: str, timeout_seconds: int = 150) -> None:
    await asyncio.sleep(timeout_seconds)
    _mark_run_timeout(run_id)
    task = _APP_TASKS.get(run_id)
    if task is not None and not task.done():
        task.cancel()


def _artifacts_from_product(resp: ProductCrawlResponse) -> dict[str, str]:
    return {
        "manifest": resp.files.manifest,
        "urls": resp.files.urls,
        "raw_products": resp.files.raw_products,
        "records_json": resp.files.products_json,
        "records_jsonl": resp.files.products_ndjson,
        "blocked_pages_json": resp.files.blocked_pages_json,
        "report_md": resp.files.report,
        "output_dir": resp.output_dir,
    }


def _write_app_artifacts(run: AppRunState) -> dict[str, str]:
    """Write minimal app-run artifacts for blocked/fallback UI states."""
    output_dir = Path(run.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    records_path = output_dir / "records.json"
    sources_path = output_dir / "source_pages.json"
    blocked_path = output_dir / "blocked_pages.json"
    report_path = output_dir / "extraction_report.md"

    records_path.write_text(json.dumps(run.records, indent=2), encoding="utf-8")
    sources_path.write_text(json.dumps(run.sources, indent=2), encoding="utf-8")
    blocked_path.write_text(json.dumps(run.blocked_pages, indent=2), encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": run.run_id,
                "status": run.status,
                "use_case": run.use_case,
                "mode": run.mode,
                "target_url": run.target_url,
                "created_at": run.created_at,
                "updated_at": run.updated_at,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report_path.write_text(
        "\n".join(
            [
                f"# Scout App Run {run.run_id}",
                "",
                f"- Status: {run.status}",
                f"- Use case: {run.use_case}",
                f"- Mode: {run.mode}",
                f"- Target: {run.target_url}",
                f"- Records: {len(run.records)}",
                f"- Sources: {len(run.sources)}",
                f"- Blocked pages: {len(run.blocked_pages)}",
            ]
        ),
        encoding="utf-8",
    )
    artifacts = {
        "manifest": str(manifest_path),
        "records_json": str(records_path),
        "source_pages_json": str(sources_path),
        "blocked_pages_json": str(blocked_path),
        "report_md": str(report_path),
        "output_dir": str(output_dir),
    }
    for evidence_key, artifact_key in (
        ("screenshot_path", "browser_screenshot"),
        ("dom_path", "browser_dom"),
        ("text_path", "browser_text"),
        ("links_path", "browser_links"),
    ):
        value = run.browser_evidence.get(evidence_key)
        if value:
            artifacts[artifact_key] = str(value)
    return artifacts


async def _capture_scout_browser_evidence(
    *, run_id: str, url: str, output_dir: str
) -> dict[str, Any]:
    browser_dir = Path(output_dir) / "browser"
    browser_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = browser_dir / "screenshot.png"
    dom_path = browser_dir / "dom.html"
    text_path = browser_dir / "text.txt"
    links_path = browser_dir / "links.json"
    console_errors: list[str] = []
    network_failures: list[str] = []
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:  # pragma: no cover - dependency boundary
        return {
            "url": url,
            "title": "Scout browser unavailable",
            "provider": "scout-browser",
            "session_type": "Scout browser session",
            "status": "unavailable",
            "note": f"Playwright is not available in this environment: {exc}",
            "captured_at": _now(),
        }

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()
            page.on(
                "console",
                lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
            )
            page.on("requestfailed", lambda request: network_failures.append(request.url))
            _append(run_id, "browser", "Scout Browser opening target page")
            response = await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
            try:
                await page.wait_for_load_state("networkidle", timeout=8_000)
            except Exception:
                _append(run_id, "browser", "Network did not become idle; capturing current page")
            await page.screenshot(path=str(screenshot_path), full_page=True)
            title = await page.title()
            html = await page.content()
            text = await page.locator("body").inner_text(timeout=5_000)
            current_url = page.url
            links = await page.eval_on_selector_all(
                "a[href]",
                """anchors => anchors.slice(0, 200).map((a) => ({
                    text: (a.innerText || '').trim().slice(0, 180),
                    href: a.href
                }))""",
            )
            dom_path.write_text(html, encoding="utf-8")
            text_path.write_text(text, encoding="utf-8")
            links_path.write_text(json.dumps(links, indent=2), encoding="utf-8")
            await context.close()
            await browser.close()
            encoded = base64.b64encode(screenshot_path.read_bytes()).decode("ascii")
            return {
                "url": current_url,
                "title": title or "Scout browser capture",
                "provider": "scout-browser",
                "session_type": "Scout browser session",
                "status": "captured",
                "status_code": response.status if response else None,
                "screenshot_path": str(screenshot_path),
                "screenshot_data_url": f"data:image/png;base64,{encoded}",
                "dom_path": str(dom_path),
                "text_path": str(text_path),
                "links_path": str(links_path),
                "text_preview": text[:4000],
                "links": links[:25],
                "console_errors": console_errors[:25],
                "network_failures": network_failures[:25],
                "viewport": "1440x900",
                "captured_at": _now(),
                "note": "Scout Browser captured a rendered page snapshot for extraction review.",
            }
    except Exception as exc:
        return {
            "url": url,
            "title": "Scout browser capture failed",
            "provider": "scout-browser",
            "session_type": "Scout browser session",
            "status": "failed",
            "error": str(exc),
            "console_errors": console_errors[:25],
            "network_failures": network_failures[:25],
            "captured_at": _now(),
            "note": "Scout Browser could not capture this page. The run preserves the failure as evidence.",
        }


def _sources_from_product(resp: ProductCrawlResponse) -> list[dict[str, Any]]:
    sources: dict[str, dict[str, Any]] = {}
    fetched_at = _now()
    for record in resp.records:
        data = record.model_dump(mode="json", by_alias=True)
        source = data.get("_source") or data.get("source") or {}
        url = source.get("category_url") or data.get("url") or resp.start_url
        if not url:
            continue
        sources.setdefault(
            url,
            {
                "source_url": url,
                "provider": source.get("extractor") or "crawl4ai",
                "status_code": 200,
                "status": "ok",
                "confidence": data.get("completeness_score", 0.6),
                "captured_at": fetched_at,
                "type": "listing" if source.get("extractor") == "listing_card" else "detail",
            },
        )
    for blocked in resp.blocked_pages:
        item = blocked.model_dump(mode="json")
        url = item.get("url")
        if not url:
            continue
        sources.setdefault(
            url,
            {
                "source_url": url,
                "provider": "blocked_page",
                "status_code": None,
                "status": "blocked",
                "confidence": 0,
                "captured_at": fetched_at,
                "type": "blocked",
                "reason": item.get("reason", ""),
            },
        )
    return list(sources.values())


def _browser_evidence_for_product(resp: ProductCrawlResponse) -> dict[str, Any]:
    record_count = len(resp.records)
    blocked_count = len(resp.blocked_pages)
    if record_count and blocked_count:
        note = (
            "Listing records found. Some detail pages were blocked during enrichment, "
            "so Scout preserved listing-level evidence and reported blocked details separately."
        )
    elif blocked_count:
        note = (
            "Scout's crawler session was blocked. Your normal browser session may still view "
            "the page because it has different cookies, headers, reputation, or session state."
        )
    elif record_count:
        note = "Product records were extracted from source evidence."
    else:
        note = "No product records or blocked evidence were produced."
    return {
        "url": resp.start_url,
        "title": resp.categories[0] if resp.categories else resp.site or resp.query or "Scout run",
        "provider": "crawl4ai",
        "viewport": "1280x900",
        "session_note": "Scout uses its own crawler/browser context, separate from your personal browser.",
        "note": note,
    }


async def _execute_products(run_id: str, req: AppRunRequest, crawler: ScoutCrawler) -> None:
    run = _APP_RUNS[run_id]
    if run.status == "cancelled":
        return
    if run.status in {"failed", "complete"}:
        return
    run.status = "running"
    _append(run_id, "discovering", "Discovering category and product URLs")
    product_req = ProductCrawlRequest(
        query=req.query,
        site="",
        start_url=req.url,
        limit_per_category=10,
        max_categories=3,
        max_products=30,
        output_dir=req.output_dir,
        persist=True,
        use_js=True,
        stealth=req.mode in {"auto", "browser", "crawl4ai"},
        browser_fallback=req.browser_fallback,
    )
    _append(run_id, "rendering", "Rendering pages and collecting source evidence")
    if req.mode in {"scout-browser", "browser"}:
        run.browser_evidence = await _capture_scout_browser_evidence(
            run_id=run_id, url=req.url, output_dir=req.output_dir
        )
        captured = run.browser_evidence.get("status") == "captured"
        status_code = run.browser_evidence.get("status_code")
        text_preview = str(run.browser_evidence.get("text_preview", "")).lower()
        blocked_capture = bool(
            (isinstance(status_code, int) and status_code >= 400)
            or "access denied" in text_preview
            or "permission to access" in text_preview
            or "blocked" in text_preview
        )
        run.sources = [
            {
                "source_url": run.browser_evidence.get("url") or req.url,
                "provider": "scout-browser",
                "status_code": status_code,
                "status": "blocked"
                if blocked_capture
                else run.browser_evidence.get("status") or "captured",
                "confidence": 0.2 if blocked_capture else 0.7 if captured else 0.2,
                "captured_at": run.browser_evidence.get("captured_at") or _now(),
                "type": "browser_snapshot",
                "session_type": "Scout browser session",
            }
        ]
        if blocked_capture:
            run.blocked_pages = [
                {
                    "url": req.url,
                    "reason": "scout_browser_access_denied",
                    "category_url": req.url,
                    "category_name": req.query or req.url,
                    "title": run.browser_evidence.get("title", "Access denied"),
                    "fallback_attempted": True,
                    "fallback_used": True,
                    "fallback_error": "Scout Browser captured a rendered blocked/access-denied page.",
                }
            ]
            run.status = "failed"
            _append(
                run_id,
                "blocked",
                "Scout Browser captured a blocked/access-denied page and saved the evidence",
                "warning",
            )
        elif not captured:
            run.blocked_pages = [
                {
                    "url": req.url,
                    "reason": "scout_browser_capture_failed",
                    "category_url": req.url,
                    "category_name": req.query or req.url,
                    "title": run.browser_evidence.get("title", "Scout Browser capture failed"),
                    "fallback_attempted": True,
                    "fallback_used": False,
                    "fallback_error": run.browser_evidence.get("error")
                    or run.browser_evidence.get("note"),
                }
            ]
            run.status = "failed"
            _append(run_id, "blocked", "Scout Browser could not capture the page", "warning")
        else:
            _append(
                run_id,
                "browser",
                "Scout Browser captured screenshot, DOM, text, and links",
                "success",
            )
            run.warnings.append(
                "Scout Browser capture completed. Product record extraction from browser DOM is the next parser pass."
            )
            run.status = "complete"
        run.artifacts = _write_app_artifacts(run)
        _append(run_id, "artifacts", "Browser evidence artifacts written")
        _append(
            run_id,
            run.status,
            "Scout Browser captured blocked evidence"
            if blocked_capture
            else "Scout Browser evidence captured"
            if captured
            else "Scout Browser capture failed",
            "warning" if blocked_capture else "success" if captured else "error",
        )
        run.updated_at = _now()
        return
    if req.mode == "user-browser":
        run.blocked_pages = [
            {
                "url": req.url,
                "reason": "user_browser_bridge_not_connected",
                "category_url": req.url,
                "category_name": req.query or req.url,
                "title": "User browser bridge not connected",
                "fallback_attempted": True,
                "fallback_used": False,
                "fallback_error": (
                    "User Browser mode needs a Chrome CDP or extension bridge. "
                    "Scout preserved this as an explicit setup requirement instead "
                    "of pretending it can access your browser session."
                ),
            }
        ]
        run.sources = [
            {
                "source_url": req.url,
                "provider": "user-browser",
                "status_code": None,
                "status": "blocked",
                "confidence": 0,
                "captured_at": _now(),
                "type": "blocked",
                "reason": "user_browser_bridge_not_connected",
            }
        ]
        run.browser_evidence = {
            "url": req.url,
            "title": "User browser bridge not connected",
            "provider": "user-browser",
            "session_type": "User browser session",
            "note": (
                "This mode is for pages visible in your own browser session. It requires a "
                "Chrome remote-debugging or extension bridge before Scout can capture it."
            ),
        }
        run.status = "failed"
        run.artifacts = _write_app_artifacts(run)
        _append(
            run_id,
            "blocked",
            "User Browser mode requires a connected bridge",
            "warning",
        )
        _append(run_id, "failed", "User browser bridge is not connected", "error")
        return
    try:
        resp = await asyncio.wait_for(crawler.products(product_req), timeout=120)
    except TimeoutError:
        if run.status == "cancelled":
            return
        run.blocked_pages = [
            {
                "url": req.url,
                "reason": "blocked_timeout",
                "category_url": req.url,
                "category_name": req.query or req.url,
                "title": "Run timed out",
                "fallback_attempted": True,
                "fallback_used": False,
                "fallback_error": "Product extraction exceeded the app run timeout.",
            }
        ]
        run.sources = [
            {
                "source_url": req.url,
                "provider": "timeout",
                "status_code": None,
                "status": "blocked_timeout",
                "confidence": 0,
                "captured_at": _now(),
                "type": "blocked",
                "reason": "blocked_timeout",
            }
        ]
        run.browser_evidence = {
            "url": req.url,
            "title": "Blocked or timed out",
            "provider": req.mode,
            "note": (
                "Scout stopped this product run after the app timeout and preserved "
                "blocked/fallback evidence instead of leaving the UI running."
            ),
        }
        run.status = "failed"
        run.artifacts = _write_app_artifacts(run)
        _append(
            run_id,
            "blocked",
            "Product extraction timed out; blocked/fallback evidence was recorded",
            "warning",
        )
        _append(run_id, "failed", "Run timed out with blocked evidence", "error")
        return
    if run.status == "cancelled":
        _append(run_id, "cancelled", "Run cancelled before results were committed", "warning")
        return
    if run.status in {"failed", "complete"}:
        return
    _append(run_id, "extracting", f"Extracted {len(resp.records)} product records")
    run.records = [record.model_dump(mode="json", by_alias=True) for record in resp.records]
    run.blocked_pages = [item.model_dump(mode="json") for item in resp.blocked_pages]
    run.sources = _sources_from_product(resp)
    run.artifacts = _artifacts_from_product(resp)
    run.browser_evidence = _browser_evidence_for_product(resp)
    if run.records and run.blocked_pages:
        _append(
            run_id,
            "blocked",
            "Listing records found; detail-page enrichment had blocked pages",
            "warning",
        )
    elif run.blocked_pages:
        _append(
            run_id, "blocked", "Scout was blocked and preserved blocked-page evidence", "warning"
        )
    _append(run_id, "artifacts", "Artifacts written to the selected working directory")
    run.status = "complete" if resp.success else "failed"
    if resp.error:
        run.errors.append(resp.error)
    _append(
        run_id,
        run.status,
        "Run completed" if resp.success else resp.error or "Run failed",
        "success" if resp.success else "error",
    )
    run.updated_at = _now()


def _read_json_file(path: str) -> Any:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        return None
    return json.loads(file_path.read_text(encoding="utf-8"))


async def _execute_use_case(run_id: str, req: AppRunRequest) -> None:
    run = _APP_RUNS[run_id]
    if run.status == "cancelled":
        return
    run.status = "running"
    _append(run_id, "discovering", "Resolving target pages and providers")
    data = RunRequest(
        use_case=req.use_case,
        query=req.query or req.url,
        mode=req.mode,
        url=req.url,
        targets=[req.url] if req.url else [],
        output_dir=resolve_run_output_dir(
            use_case=req.use_case,
            query=req.query or req.url,
            output_dir=req.output_dir,
            workdir=settings.scout_workdir,
        ),
    )
    _append(run_id, "extracting", f"Running {req.use_case} processor")
    resp = await asyncio.to_thread(run_use_case, data)
    if run.status == "cancelled":
        _append(run_id, "cancelled", "Run cancelled before results were committed", "warning")
        return
    artifacts = resp.manifest.artifacts if resp.manifest else None
    run.output_dir = resp.output_dir
    run.artifacts = (
        artifacts.model_dump(mode="json") if artifacts else {"output_dir": resp.output_dir}
    )
    records = _read_json_file(run.artifacts.get("records_json", ""))
    sources = _read_json_file(run.artifacts.get("source_pages_json", ""))
    blocked = _read_json_file(run.artifacts.get("blocked_pages_json", ""))
    run.records = (
        records
        if isinstance(records, list)
        else records.get("records", [])
        if isinstance(records, dict)
        else []
    )
    run.sources = (
        sources
        if isinstance(sources, list)
        else sources.get("sources", [])
        if isinstance(sources, dict)
        else []
    )
    run.blocked_pages = (
        blocked
        if isinstance(blocked, list)
        else blocked.get("blocked_pages", [])
        if isinstance(blocked, dict)
        else []
    )
    run.browser_evidence = {
        "url": req.url,
        "title": req.use_case.title(),
        "provider": req.mode,
        "note": "High-level intelligence run completed and artifacts were loaded.",
    }
    run.status = "complete" if resp.success else "failed"
    if resp.error:
        run.errors.append(resp.error)
    _append(run_id, "artifacts", "Artifacts written to the selected working directory")
    _append(
        run_id,
        run.status,
        "Run completed" if resp.success else resp.error or "Run failed",
        "success" if resp.success else "error",
    )


async def _execute_run(run_id: str, req: AppRunRequest, crawler: ScoutCrawler) -> None:
    try:
        if req.use_case == "products":
            await _execute_products(run_id, req, crawler)
        else:
            await _execute_use_case(run_id, req)
    except asyncio.CancelledError:
        run = _APP_RUNS.get(run_id)
        if run is not None and run.status != "cancelled":
            run.status = "cancelled"
            _append(run_id, "cancelled", "Run task cancelled", "warning")
        raise
    except Exception as exc:  # pragma: no cover - defensive boundary
        run = _APP_RUNS[run_id]
        run.status = "failed"
        run.errors.append(str(exc))
        _append(run_id, "failed", str(exc), "error")
    finally:
        _APP_TASKS.pop(run_id, None)
        watchdog = _APP_WATCHDOGS.pop(run_id, None)
        if watchdog is not None and not watchdog.done():
            watchdog.cancel()


@router.post("", response_model=AppRunState)
async def create_app_run(
    req: AppRunRequest,
    crawler: ScoutCrawler = Depends(get_crawler),
) -> AppRunState:
    run_id = _run_id()
    output_dir = req.output_dir or str(Path(settings.scout_workdir) / "app-runs" / run_id)
    normalized = req.model_copy(update={"output_dir": output_dir})
    state = AppRunState(
        run_id=run_id,
        status="queued",
        use_case=normalized.use_case,
        mode=normalized.mode,
        target_url=normalized.url,
        output_dir=output_dir,
        events=[AppRunEvent(stage="queued", message="Run created and queued")],
    )
    _APP_RUNS[run_id] = state
    _APP_TASKS[run_id] = asyncio.create_task(_execute_run(run_id, normalized, crawler))
    _APP_WATCHDOGS[run_id] = asyncio.create_task(_watch_run_timeout(run_id))
    return state


@router.get("/{run_id}", response_model=AppRunState)
async def get_app_run(run_id: str) -> AppRunState:
    run = _APP_RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{run_id}/events")
async def get_app_run_events(run_id: str) -> dict[str, Any]:
    run = _APP_RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "events": [event.model_dump(mode="json") for event in run.events]}


@router.post("/{run_id}/cancel", response_model=AppRunState)
async def cancel_app_run(run_id: str) -> AppRunState:
    run = _APP_RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status not in {"complete", "failed"}:
        run.status = "cancelled"
        _append(run_id, "cancelled", "Run cancelled by user", "warning")
        task = _APP_TASKS.get(run_id)
        if task is not None and not task.done():
            task.cancel()
        watchdog = _APP_WATCHDOGS.pop(run_id, None)
        if watchdog is not None and not watchdog.done():
            watchdog.cancel()
    return run


@router.post("/{run_id}/reset")
async def reset_app_run(run_id: str) -> dict[str, Any]:
    if run_id not in _APP_RUNS:
        raise HTTPException(status_code=404, detail="Run not found")
    task = _APP_TASKS.pop(run_id, None)
    if task is not None and not task.done():
        task.cancel()
    watchdog = _APP_WATCHDOGS.pop(run_id, None)
    if watchdog is not None and not watchdog.done():
        watchdog.cancel()
    del _APP_RUNS[run_id]
    return {"run_id": run_id, "reset": True}
