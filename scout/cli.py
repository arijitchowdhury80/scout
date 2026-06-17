"""Scout CLI — run Scout modes directly without starting the HTTP server."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from scout.core.human_assisted import CaptureLike

from scout.core.modes.crawl import crawl as _crawl
from scout.core.modes.extract import extract as _extract
from scout.core.modes.map import map_urls as _map
from scout.core.modes.products import products as _products
from scout.core.modes.scrape import scrape as _scrape
from scout.core.modes.screenshot import screenshot as _screenshot
from scout.core.platform.run import run_use_case
from scout.core.platform.types import RunRequest
from scout.core.platform.workspace import default_workdir, resolve_run_output_dir
from scout.core.types import (
    CrawlRequest,
    ExtractRequest,
    MapRequest,
    ProductCrawlRequest,
    ScreenshotRequest,
    ScrapeRequest,
)

app = typer.Typer(
    name="scout",
    help=(
        "Scout web intelligence CLI.\n\n"
        "This product includes software developed by UncleCode (https://x.com/unclecode) "
        "as part of the Crawl4AI project (https://github.com/unclecode/crawl4ai), "
        "licensed under the Apache License 2.0."
    ),
    no_args_is_help=True,
)
run_app = typer.Typer(
    help=(
        "Run high-level Scout use cases: products, jobs, prism, investor, research, "
        "website-quality, docs, news, social, locations."
    )
)
app.add_typer(run_app, name="run")

_MODE_HELP = "Execution mode: auto, crawl4ai, webfetch, websearch, browser, saved, api"


def _out(data: dict) -> None:
    print(json.dumps(data, indent=2, default=str))


def _die(resp: object) -> None:
    """Print response and exit 1 if success=False."""
    d = resp.model_dump(by_alias=True)  # type: ignore[union-attr]
    _out(d)
    if not d.get("success", True):
        raise SystemExit(1)


def _run_high_level_use_case(
    use_case: str,
    query: str = "",
    output_dir: str = "",
    profile_path: str = "",
    job_urls: list[str] | None = None,
    mode: str = "auto",
    workdir: str = "",
) -> None:
    chosen_output = _choose_output_dir(
        output_dir=output_dir,
        workdir=workdir,
        use_case=use_case,
        query=query,
    )
    resp = run_use_case(
        RunRequest(
            use_case=use_case,
            query=query,
            mode=mode,
            profile_path=profile_path,
            job_urls=job_urls or [],
            output_dir=chosen_output,
        )
    )
    _out(resp.model_dump(mode="json"))


@run_app.command("products")
def run_products(
    query: str = typer.Option("", "--query", help="Use-case query"),
    mode: str = typer.Option("auto", "--mode", help=_MODE_HELP),
    workdir: str = typer.Option("", "--workdir", help="Base directory for Scout run outputs"),
    output_dir: str = typer.Option("", "--output-dir", help="Directory for run artifacts"),
) -> None:
    """Run product catalog extraction."""
    _run_high_level_use_case(
        "products", query=query, output_dir=output_dir, mode=mode, workdir=workdir
    )


@run_app.command("company")
def run_company(
    query: str = typer.Option("", "--query", help="Use-case query"),
    mode: str = typer.Option("auto", "--mode", help=_MODE_HELP),
    workdir: str = typer.Option("", "--workdir", help="Base directory for Scout run outputs"),
    output_dir: str = typer.Option("", "--output-dir", help="Directory for run artifacts"),
) -> None:
    """Run company intelligence extraction."""
    _run_high_level_use_case(
        "company", query=query, output_dir=output_dir, mode=mode, workdir=workdir
    )


@run_app.command("jobs")
def run_jobs(
    query: str = typer.Option("", "--query", help="Use-case query"),
    mode: str = typer.Option("auto", "--mode", help=_MODE_HELP),
    profile: str = typer.Option("", "--profile", help="Path to a JobSearchProfile YAML file"),
    workdir: str = typer.Option("", "--workdir", help="Base directory for Scout run outputs"),
    job_url: list[str] | None = typer.Option(
        None,
        "--job-url",
        help="Seed job URL to extract and score. Repeat for multiple jobs.",
    ),
    output_dir: str = typer.Option("", "--output-dir", help="Directory for run artifacts"),
) -> None:
    """Run job hunter extraction."""
    _run_high_level_use_case(
        "jobs",
        query=query,
        output_dir=output_dir,
        profile_path=profile,
        job_urls=job_url or [],
        mode=mode,
        workdir=workdir,
    )


@run_app.command("careers")
def run_careers(
    query: str = typer.Option("", "--query", help="Use-case query"),
    mode: str = typer.Option("auto", "--mode", help=_MODE_HELP),
    workdir: str = typer.Option("", "--workdir", help="Base directory for Scout run outputs"),
    output_dir: str = typer.Option("", "--output-dir", help="Directory for run artifacts"),
) -> None:
    """Run careers and hiring intelligence extraction."""
    _run_high_level_use_case(
        "careers", query=query, output_dir=output_dir, mode=mode, workdir=workdir
    )


@run_app.command("prism")
def run_prism(
    query: str = typer.Option("", "--query", help="Use-case query"),
    mode: str = typer.Option("auto", "--mode", help=_MODE_HELP),
    workdir: str = typer.Option("", "--workdir", help="Base directory for Scout run outputs"),
    output_dir: str = typer.Option("", "--output-dir", help="Directory for run artifacts"),
) -> None:
    """Run PRISM company intelligence extraction."""
    _run_high_level_use_case(
        "prism", query=query, output_dir=output_dir, mode=mode, workdir=workdir
    )


@run_app.command("investor")
def run_investor(
    query: str = typer.Option("", "--query", help="Use-case query"),
    mode: str = typer.Option("auto", "--mode", help=_MODE_HELP),
    workdir: str = typer.Option("", "--workdir", help="Base directory for Scout run outputs"),
    output_dir: str = typer.Option("", "--output-dir", help="Directory for run artifacts"),
) -> None:
    """Run investor intelligence extraction."""
    _run_high_level_use_case(
        "investor", query=query, output_dir=output_dir, mode=mode, workdir=workdir
    )


@run_app.command("research")
def run_research(
    query: str = typer.Option("", "--query", help="Use-case query"),
    mode: str = typer.Option("auto", "--mode", help=_MODE_HELP),
    workdir: str = typer.Option("", "--workdir", help="Base directory for Scout run outputs"),
    output_dir: str = typer.Option("", "--output-dir", help="Directory for run artifacts"),
) -> None:
    """Run generic web research extraction."""
    _run_high_level_use_case(
        "research", query=query, output_dir=output_dir, mode=mode, workdir=workdir
    )


@run_app.command("website-quality")
def run_website_quality(
    query: str = typer.Option("", "--query", help="Use-case query"),
    mode: str = typer.Option("auto", "--mode", help=_MODE_HELP),
    workdir: str = typer.Option("", "--workdir", help="Base directory for Scout run outputs"),
    output_dir: str = typer.Option("", "--output-dir", help="Directory for run artifacts"),
) -> None:
    """Run website quality assessment."""
    _run_high_level_use_case(
        "website-quality", query=query, output_dir=output_dir, mode=mode, workdir=workdir
    )


@run_app.command("docs")
def run_docs(
    query: str = typer.Option("", "--query", help="Use-case query"),
    mode: str = typer.Option("auto", "--mode", help=_MODE_HELP),
    workdir: str = typer.Option("", "--workdir", help="Base directory for Scout run outputs"),
    output_dir: str = typer.Option("", "--output-dir", help="Directory for run artifacts"),
) -> None:
    """Run documentation extraction."""
    _run_high_level_use_case("docs", query=query, output_dir=output_dir, mode=mode, workdir=workdir)


@run_app.command("news")
def run_news(
    query: str = typer.Option("", "--query", help="Use-case query"),
    mode: str = typer.Option("auto", "--mode", help=_MODE_HELP),
    workdir: str = typer.Option("", "--workdir", help="Base directory for Scout run outputs"),
    output_dir: str = typer.Option("", "--output-dir", help="Directory for run artifacts"),
) -> None:
    """Run newsroom and signal monitoring."""
    _run_high_level_use_case("news", query=query, output_dir=output_dir, mode=mode, workdir=workdir)


@run_app.command("social")
def run_social(
    query: str = typer.Option("", "--query", help="Use-case query"),
    mode: str = typer.Option("auto", "--mode", help=_MODE_HELP),
    workdir: str = typer.Option("", "--workdir", help="Base directory for Scout run outputs"),
    output_dir: str = typer.Option("", "--output-dir", help="Directory for run artifacts"),
) -> None:
    """Run social signal normalization."""
    _run_high_level_use_case(
        "social", query=query, output_dir=output_dir, mode=mode, workdir=workdir
    )


@run_app.command("locations")
def run_locations(
    query: str = typer.Option("", "--query", help="Use-case query"),
    mode: str = typer.Option("auto", "--mode", help=_MODE_HELP),
    workdir: str = typer.Option("", "--workdir", help="Base directory for Scout run outputs"),
    output_dir: str = typer.Option("", "--output-dir", help="Directory for run artifacts"),
) -> None:
    """Run store/location extraction."""
    _run_high_level_use_case(
        "locations", query=query, output_dir=output_dir, mode=mode, workdir=workdir
    )


@app.command()
def scrape(
    url: str = typer.Argument(..., help="URL to fetch"),
    js: bool = typer.Option(False, "--js", help="Enable JS rendering (Playwright)"),
    wait_for: str = typer.Option(
        "", "--wait-for", help="CSS selector or JS expression to wait for"
    ),
    timeout: int = typer.Option(30000, "--timeout", help="Page load timeout in ms"),
) -> None:
    """Fetch a single page and return clean markdown + metadata."""
    req = ScrapeRequest(url=url, use_js=js, wait_for=wait_for, timeout_ms=timeout)
    resp = asyncio.run(_scrape(req))
    _die(resp)


@app.command()
def crawl(
    url: str = typer.Argument(..., help="Start URL for BFS crawl"),
    depth: int = typer.Option(2, "--depth", help="Max BFS depth"),
    pages: int = typer.Option(10, "--pages", help="Max pages to crawl"),
    pattern: str = typer.Option("", "--pattern", help="URL substring filter"),
    js: bool = typer.Option(False, "--js", help="Enable JS rendering"),
    timeout: int = typer.Option(60000, "--timeout", help="Per-page timeout in ms"),
) -> None:
    """BFS deep crawl from a start URL — returns all pages up to depth/pages limit."""
    req = CrawlRequest(
        url=url,
        max_depth=depth,
        max_pages=pages,
        url_pattern=pattern,
        use_js=js,
        timeout_ms=timeout,
    )
    resp = asyncio.run(_crawl(req))
    _die(resp)


@app.command()
def map(
    url: str = typer.Argument(..., help="Site URL to discover URLs for"),
    pages: int = typer.Option(100, "--pages", help="Max URLs to return"),
    pattern: str = typer.Option(
        "", "--pattern", help="URL substring filter (applied after sitemap fetch)"
    ),
) -> None:
    """Discover all URLs on a site via sitemap, with BFS fallback."""
    req = MapRequest(url=url, max_pages=pages, url_pattern=pattern)
    resp = asyncio.run(_map(req))
    _die(resp)


@app.command()
def extract(
    url: str = typer.Argument(..., help="URL to extract structured data from"),
    schema: str = typer.Option("{}", "--schema", help="JSON Schema string for LLM extraction"),
    instruction: str = typer.Option(
        "", "--instruction", help="Natural language extraction instruction"
    ),
    css_schema: str = typer.Option(
        "", "--css-schema", help="CSS schema JSON string for selector-based extraction"
    ),
    llm_key: str = typer.Option(
        "", "--llm-key", envvar="LLM_API_KEY", help="LLM API key (or set LLM_API_KEY env var)"
    ),
    provider: str = typer.Option(
        "gemini/gemini-2.0-flash", "--provider", help="LiteLLM provider string"
    ),
    js: bool = typer.Option(False, "--js", help="Enable JS rendering"),
) -> None:
    """Extract structured data — LLM-based or CSS selector-based fallback."""
    try:
        schema_dict: dict = json.loads(schema)
    except json.JSONDecodeError:
        typer.echo(f"Error: --schema is not valid JSON: {schema}", err=True)
        raise SystemExit(1)

    css_schema_dict: dict | None = None
    if css_schema:
        try:
            css_schema_dict = json.loads(css_schema)
        except json.JSONDecodeError:
            typer.echo(f"Error: --css-schema is not valid JSON: {css_schema}", err=True)
            raise SystemExit(1)

    req = ExtractRequest.model_validate(
        {
            "url": url,
            "schema": schema_dict,
            "instruction": instruction,
            "llm_provider": provider,
            "css_schema": css_schema_dict,
            "use_js": js,
        }
    )
    resp = asyncio.run(_extract(req, llm_api_key=llm_key))
    _die(resp)


@app.command()
def products(
    query: str = typer.Argument(..., help="Product query or catalog label"),
    site: str = typer.Option("", "--site", help="Target domain, for example esteelauder.com"),
    start_url: str = typer.Option("", "--start-url", help="Explicit URL to start discovery from"),
    output_dir: str = typer.Option("", "--output-dir", help="Directory for run artifacts"),
    workdir: str = typer.Option("", "--workdir", help="Base directory for Scout run outputs"),
    limit_per_category: int = typer.Option(
        10, "--limit-per-category", help="Products per category"
    ),
    max_categories: int = typer.Option(10, "--max-categories", help="Maximum categories"),
    max_products: int = typer.Option(100, "--max-products", help="Maximum product records"),
    js: bool = typer.Option(True, "--js/--no-js", help="Enable JS rendering"),
    stealth: bool = typer.Option(False, "--stealth", help="Enable Crawl4AI stealth mode"),
    browser_fallback: bool = typer.Option(
        True,
        "--browser-fallback/--no-browser-fallback",
        help="Retry blocked product pages through a headed browser fallback channel",
    ),
    browser_fallback_headless: bool = typer.Option(
        False,
        "--browser-fallback-headless/--browser-fallback-headed",
        help="Run the fallback browser headless instead of visibly headed",
    ),
) -> None:
    """Crawl products and write Algolia-ready records to a run folder."""
    chosen_output = _choose_output_dir(
        output_dir=output_dir,
        workdir=workdir,
        use_case="products",
        query="-".join(part for part in [site, query] if part),
    )
    req = ProductCrawlRequest(
        query=query,
        site=site,
        start_url=start_url,
        output_dir=chosen_output,
        persist=True,
        limit_per_category=limit_per_category,
        max_categories=max_categories,
        max_products=max_products,
        use_js=js,
        stealth=stealth,
        browser_fallback=browser_fallback,
        browser_fallback_headless=browser_fallback_headless,
    )
    resp = asyncio.run(_products(req))
    _die(resp)


def _choose_output_dir(output_dir: str, workdir: str, use_case: str, query: str) -> str:
    if output_dir:
        return output_dir
    chosen_workdir = workdir or _prompt_workdir()
    return resolve_run_output_dir(use_case=use_case, query=query, workdir=chosen_workdir)


def _prompt_workdir() -> str:
    default = str(Path(default_workdir()))
    if sys.stdin.isatty():
        return str(
            typer.prompt(
                "Where should Scout save run outputs, interim status, and local configs?",
                default=default,
            )
        )
    return default


def _prompt_output_dir(query: str, site: str) -> str:
    return resolve_run_output_dir(
        use_case=site or "scout",
        query=query,
        workdir=_prompt_workdir(),
    )


@app.command()
def screenshot(
    url: str = typer.Argument(..., help="URL to screenshot"),
    full_page: bool = typer.Option(
        True, "--full-page/--viewport-only", help="Capture full scrollable page"
    ),
    width: int = typer.Option(1280, "--width", help="Viewport width in px"),
    height: int = typer.Option(800, "--height", help="Viewport height in px"),
    out: str = typer.Option(
        "", "--out", help="Save base64 PNG to this file path instead of stdout"
    ),
) -> None:
    """Capture a full-page screenshot and return base64 PNG."""
    req = ScreenshotRequest(
        url=url, full_page=full_page, viewport_width=width, viewport_height=height, use_js=True
    )
    resp = asyncio.run(_screenshot(req))
    if out and resp.screenshot_base64:
        import base64

        with open(out, "wb") as f:
            f.write(base64.b64decode(resp.screenshot_base64))
        typer.echo(f"Screenshot saved to {out} ({resp.width}x{resp.height}px)")
    else:
        _die(resp)


class _CDPBridge:
    """Adapter: lets the engine's human_assisted flow drive the Chrome CDP
    service without the engine importing the api layer (boundary stays clean)."""

    def __init__(self, service: object) -> None:
        self._svc = service

    async def open(self, url: str) -> object:
        from scout.api.user_browser import UserBrowserOpenRequest

        return await self._svc.open_browser(UserBrowserOpenRequest(url=url))  # type: ignore[attr-defined]

    async def capture(self, url: str) -> CaptureLike:
        return await self._svc.capture_active_tab(url)  # type: ignore[attr-defined,no-any-return]

    async def navigate_capture(self, url: str) -> CaptureLike:
        return await self._svc.navigate_capture(url)  # type: ignore[attr-defined,no-any-return]


@app.command()
def unblock(
    url: str = typer.Argument(..., help="URL to open in a real, visible browser"),
    out: str = typer.Option("", "--out", help="Directory to write the captured markdown + summary"),
    poll: float = typer.Option(2.0, "--poll", help="Seconds between checks while you solve the challenge"),
    max_wait: float = typer.Option(
        180.0, "--max-wait", help="Max seconds to wait for you to clear the challenge"
    ),
    crawl_from_here: bool = typer.Option(
        False,
        "--crawl-from-here/--no-crawl-from-here",
        help="After the page clears, visit the top detail links in the same session and extract each",
    ),
    link_contains: str = typer.Option(
        "", "--link-contains", help="Only follow detail links whose URL contains this (e.g. /homedetails/)"
    ),
    limit: int = typer.Option(5, "--limit", help="Max detail pages to crawl from the cleared page"),
) -> None:
    """Human-assisted capture: open a URL in a real browser, you clear any
    'press & hold' / login, and Scout captures the page the moment it's clear.
    With --crawl-from-here, Scout then walks the top detail links in that same
    cleared session and extracts each (markdown + JSON-LD) as a record."""
    from scout.api.user_browser import ChromeCDPService
    from scout.core.crawl_from_here import crawl_from_here as _crawl_from_here
    from scout.core.human_assisted import human_assisted_acquire

    bridge = _CDPBridge(ChromeCDPService())

    async def _sleep(seconds: float) -> None:
        await asyncio.sleep(seconds)

    typer.echo(
        f"Opening {url} in a real browser. Solve any press-and-hold / login when it appears; "
        "Scout will capture automatically once the page clears.",
        err=True,
    )
    outcome = asyncio.run(
        human_assisted_acquire(url, bridge, sleep=_sleep, poll_interval=poll, max_wait=max_wait)
    )
    summary = outcome.model_dump(mode="json")
    summary.pop("html", None)  # keep the JSON summary readable; html is large

    target = Path(out).expanduser() if out else None
    if target and outcome.status == "cleared":
        target.mkdir(parents=True, exist_ok=True)
        (target / "capture.md").write_text(outcome.markdown, encoding="utf-8")
        (target / "capture.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        typer.echo(f"Captured cleared page -> {target}", err=True)

    if crawl_from_here and outcome.status == "cleared":
        typer.echo(
            f"Crawling up to {limit} detail pages from the cleared session"
            + (f" (links containing '{link_contains}')" if link_contains else "")
            + " ...",
            err=True,
        )
        crawl_result = asyncio.run(
            _crawl_from_here(
                outcome.html, outcome.final_url or url, bridge,
                sleep=_sleep, contains=link_contains, limit=limit,
            )
        )
        summary["crawl_from_here"] = crawl_result.model_dump(mode="json")
        typer.echo(
            f"Crawled {crawl_result.crawled} pages "
            f"({crawl_result.blocked} re-challenged) from {crawl_result.discovered} discovered.",
            err=True,
        )
        if target:
            (target / "detail_records.json").write_text(
                crawl_result.model_dump_json(indent=2), encoding="utf-8"
            )
            for i, rec in enumerate(crawl_result.records, 1):
                (target / f"detail_{i:02d}.md").write_text(rec.markdown, encoding="utf-8")
            typer.echo(f"Wrote {len(crawl_result.records)} detail records -> {target}", err=True)

    _out(summary)
    if outcome.status != "cleared":
        raise SystemExit(1)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(8421, "--port", envvar="PORT", help="Port to listen on"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
) -> None:
    """Start the Scout HTTP server."""
    import uvicorn

    uvicorn.run("scout.api.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
