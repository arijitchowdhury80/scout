"""Scout CLI — run Scout modes directly without starting the HTTP server."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
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
from scout.core.crawler import ScoutCrawler
from scout.core.platform.account_service import HostedAccountService
from scout.core.platform.account_sqlite_store import SQLiteHostedAccountStore
from scout.core.platform.hosted import HostedPlan
from scout.core.platform.run import run_use_case
from scout.core.platform.types import RunRequest
from scout.core.platform.workspace import default_workdir, resolve_run_output_dir
from scout.core.products.exports import (
    ProductExportFormat,
    ProductExportRequest,
    export_product_records,
)
from scout.launch_decision_draft import (
    FounderDecisionRecordDraftError,
    default_decision_date,
    write_decision_record_draft,
    write_decision_record_drafts,
)
from scout.launch_decision_record import (
    FounderDecisionRecordError,
    format_validation_success,
    validate_decision_records,
)
from scout.launch_readiness import build_report, default_root, filter_report, print_text_report
from scout.core.types import (
    AlgoliaProductRecord,
    CrawlRequest,
    ExtractRequest,
    MapRequest,
    ProductCrawlRequest,
    ScreenshotRequest,
    ScrapeRequest,
)
from scout.validation.certification import (
    FEATURE_CERTIFICATION_MATRIX,
    CertificationActual,
    certification_results_from_evidence,
    certify_actual,
    load_certification_evidence,
    write_certification_outputs,
)
from scout.validation.evidence_generator import generate_service_certification_evidence

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


@app.command("launch-readiness")
def launch_readiness(
    root: str = typer.Option(
        "",
        "--root",
        help="Scout repo/package root containing launch evidence docs.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_public: bool = typer.Option(
        False,
        "--require-public",
        help="Exit nonzero unless public launch is ready.",
    ),
    owner: str = typer.Option(
        "",
        "--owner",
        help="Filter displayed public launch blockers by exact owner, case-insensitive.",
    ),
    blocker_type: str = typer.Option(
        "",
        "--blocker-type",
        help="Filter displayed public launch blockers by blocker type, case-insensitive.",
    ),
    blocker_id: str = typer.Option(
        "",
        "--blocker-id",
        help="Filter displayed public launch blockers by stable blocker ID, case-insensitive.",
    ),
) -> None:
    """Report private-beta and public-launch readiness from packaged evidence."""
    chosen_root = Path(root).expanduser().resolve() if root else default_root()
    report = build_report(chosen_root)
    display_report = filter_report(
        report,
        owner=owner or None,
        blocker_type=blocker_type or None,
        blocker_id=blocker_id or None,
    )

    if json_output:
        _out(display_report)
    else:
        print_text_report(display_report)

    if require_public and report["public_launch"]["status"] != "ready":
        raise SystemExit(1)
    if report["private_beta"]["status"] != "ready_with_limits":
        raise SystemExit(1)


@app.command("launch-decision-draft")
def launch_decision_draft(
    blocker_id: str = typer.Option(..., "--blocker-id", help="Stable launch blocker ID."),
    decision_id: str = typer.Option(
        ...,
        "--decision-id",
        help="Decision ID in the form SCOUT-DEC-YYYYMMDD-NN.",
    ),
    root: str = typer.Option(
        "",
        "--root",
        help="Scout repo/package root containing launch evidence docs.",
    ),
    output_root: str = typer.Option(
        ".",
        "--output-root",
        help="Root where docs/product/founder-decision-drafts will be written.",
    ),
    decision_date: str = typer.Option(
        default_decision_date(),
        "--date",
        help="Decision date to write into the draft.",
    ),
    recorded_by: str = typer.Option("Codex", "--recorded-by", help="Recorder name."),
) -> None:
    """Write a prefilled founder decision draft from a launch blocker ID."""
    chosen_root = Path(root).expanduser().resolve() if root else default_root()
    try:
        output_path = write_decision_record_draft(
            root=chosen_root,
            output_root=Path(output_root).expanduser().resolve(),
            blocker_id=blocker_id,
            decision_id=decision_id,
            date=decision_date,
            recorded_by=recorded_by,
        )
    except FounderDecisionRecordDraftError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc

    typer.echo(f"Wrote founder decision draft: {output_path}")


@app.command("launch-decision-drafts")
def launch_decision_drafts(
    blocker_id: list[str] | None = typer.Option(
        None,
        "--blocker-id",
        help="Stable launch blocker ID. Repeat to generate a packet in explicit order.",
    ),
    owner: str = typer.Option("", "--owner", help="Filter blockers by exact owner."),
    include_shared_owner: bool = typer.Option(
        False,
        "--include-shared-owner",
        help="When --owner is set, include shared owners containing that owner name.",
    ),
    blocker_type: str = typer.Option("", "--blocker-type", help="Filter by blocker type."),
    decision_date: str = typer.Option(
        ...,
        "--decision-date",
        help="Decision ID date segment in YYYYMMDD form.",
    ),
    start_index: int = typer.Option(1, "--start-index", help="First NN value for IDs."),
    root: str = typer.Option(
        "",
        "--root",
        help="Scout repo/package root containing launch evidence docs.",
    ),
    output_root: str = typer.Option(
        ".",
        "--output-root",
        help="Root where docs/product/founder-decision-drafts will be written.",
    ),
    date_text: str = typer.Option(
        default_decision_date(),
        "--date",
        help="Display date to write into each draft.",
    ),
    recorded_by: str = typer.Option("Codex", "--recorded-by", help="Recorder name."),
) -> None:
    """Write a filtered packet of founder decision drafts."""
    chosen_root = Path(root).expanduser().resolve() if root else default_root()
    try:
        output_paths = write_decision_record_drafts(
            root=chosen_root,
            output_root=Path(output_root).expanduser().resolve(),
            blocker_ids=blocker_id or [],
            owner=owner,
            include_shared_owner=include_shared_owner,
            blocker_type=blocker_type,
            decision_date=decision_date,
            date=date_text,
            start_index=start_index,
            recorded_by=recorded_by,
        )
    except FounderDecisionRecordDraftError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc

    typer.echo(f"Wrote {len(output_paths)} founder decision drafts:")
    for output_path in output_paths:
        typer.echo(f"  - {output_path}")


@app.command("launch-decision-check")
def launch_decision_check(
    records: list[str] | None = typer.Argument(
        None,
        help="Completed founder decision record files to validate.",
    ),
    root: str = typer.Option(
        ".",
        "--root",
        help="Scout repo/package root for --check-existing.",
    ),
    check_existing: bool = typer.Option(
        False,
        "--check-existing",
        help="Validate existing completed founder decision records under docs/product.",
    ),
) -> None:
    """Validate completed founder decision records before launch gates use them."""
    try:
        results = validate_decision_records(
            [Path(record).expanduser().resolve() for record in records or []],
            root=Path(root).expanduser().resolve(),
            check_existing=check_existing,
        )
    except FounderDecisionRecordError as exc:
        typer.echo(f"FAIL: {exc}", err=True)
        raise typer.Exit(2) from exc

    typer.echo(format_validation_success(results))


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
    import asyncio

    crawler = ScoutCrawler()
    resp = asyncio.run(
        run_use_case(
            RunRequest(
                use_case=use_case,
                query=query,
                mode=mode,
                profile_path=profile_path,
                job_urls=job_urls or [],
                output_dir=chosen_output,
            ),
            crawler,
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


@app.command("product-export")
def product_export(
    records_file: str = typer.Argument(..., help="Path to records.json or a JSON list of records"),
    output_dir: str = typer.Option(..., "--output-dir", help="Directory to write exports"),
    format: list[ProductExportFormat] | None = typer.Option(  # noqa: A002
        None,
        "--format",
        help="Export format. Repeat for multiple: json, jsonl, csv, sqlite, google_sheets",
    ),
    basename: str = typer.Option("products", "--basename", help="Export file basename"),
    sqlite_table: str = typer.Option("products", "--sqlite-table", help="SQLite table name"),
) -> None:
    """Export product records to JSON, JSONL, CSV, SQLite, or Google Sheets import files."""
    path = Path(records_file).expanduser()
    if not path.exists():
        typer.echo(f"Product records file does not exist: {path}", err=True)
        raise SystemExit(1)
    records = _load_product_records(path)
    result = export_product_records(
        ProductExportRequest(
            records=records,
            output_dir=Path(output_dir).expanduser(),
            formats=format or [ProductExportFormat.JSONL],
            basename=basename,
            sqlite_table=sqlite_table,
        )
    )
    _out(
        {
            "success": True,
            "record_count": result.record_count,
            "files": {key: str(value) for key, value in result.files.items()},
        }
    )


@app.command("hosted-provision")
def hosted_provision(
    email: str = typer.Option(..., "--email", help="Hosted beta user email"),
    db: str = typer.Option("", "--db", help="Hosted account SQLite DB path"),
    workdir: str = typer.Option("", "--workdir", help="Workdir used to derive DB path"),
    plan: HostedPlan = typer.Option(
        HostedPlan.HOSTED_BETA_PASS,
        "--plan",
        help="Hosted plan to provision",
    ),
    scope: list[str] | None = typer.Option(  # noqa: B008
        None,
        "--scope",
        help="API key scope. Repeat for multiple. Defaults to runs:create",
    ),
    key_name: str = typer.Option("Default key", "--key-name", help="Display name for the API key"),
) -> None:
    """Provision a hosted account key for private beta operators."""
    db_path = _hosted_account_db_path(db=db, workdir=workdir)
    service = HostedAccountService(SQLiteHostedAccountStore(db_path))
    try:
        result = service.provision_account(
            email=email,
            plan=plan,
            scopes=scope or ["runs:create"],
            key_name=key_name,
        )
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise SystemExit(1) from exc
    _out(
        {
            "success": True,
            "tenant_id": result.tenant.tenant_id,
            "key_id": result.api_key.key_id,
            "email": str(result.tenant.email),
            "plan": result.tenant.plan.value,
            "scopes": result.api_key.scopes,
            "standard_credits_remaining": result.balance.standard_credits_remaining,
            "browser_credits_remaining": result.balance.browser_credits_remaining,
            "db": str(db_path),
            "raw_api_key": result.raw_api_key,
            "warning": "Store this key now. Scout only stores its hash.",
        }
    )


@app.command()
def certify_generate(
    evidence_dir: str = typer.Option(
        "validation-output/current-evidence",
        "--evidence-dir",
        help="Directory where deterministic certification evidence files should be written",
    ),
) -> None:
    """Generate deterministic service/CLI/API evidence for Scout certification."""

    result = generate_service_certification_evidence(Path(evidence_dir))
    _out(
        {
            "success": True,
            "evidence_dir": str(result.evidence_dir),
            "scenario_count": len(result.scenario_files),
            "scenario_files": [str(path) for path in result.scenario_files],
        }
    )


@app.command()
def certify(
    output_root: str = typer.Option(
        "validation-output",
        "--output-root",
        help="Root folder for generated machine-readable certification artifacts",
    ),
    report: str = typer.Option(
        "",
        "--report",
        help="Markdown report path. Defaults to docs/validation/scout-feature-certification-<date>.md",
    ),
    timestamp: str = typer.Option(
        "",
        "--timestamp",
        help="ISO timestamp to use in output paths and report headings",
    ),
    evidence: str = typer.Option(
        "",
        "--evidence",
        help="JSON evidence file or directory with captured actuals. Omit to generate a scaffold.",
    ),
) -> None:
    """Create Scout feature-certification expected-vs-actual artifacts."""

    chosen_timestamp = timestamp or datetime.now(UTC).replace(microsecond=0).isoformat()
    report_path = Path(report) if report else _default_certification_report_path(chosen_timestamp)
    if evidence:
        results = certification_results_from_evidence(
            load_certification_evidence(Path(evidence)),
            include_missing=True,
        )
    else:
        results = [
            certify_actual(
                scenario,
                CertificationActual(
                    status="not_run",
                    records=[],
                    sources=[],
                    citations=[],
                    artifacts=[],
                    blocked_pages=[],
                    raw_response={
                        "status": "not_run",
                        "message": "Scenario has not been executed yet.",
                        "scenario_id": scenario.scenario_id,
                    },
                ),
                notes=["Generated from certification matrix; actual run evidence is pending."],
            )
            for scenario in FEATURE_CERTIFICATION_MATRIX
        ]
    outputs = write_certification_outputs(
        results,
        output_root=Path(output_root),
        report_path=report_path,
        timestamp=chosen_timestamp,
    )
    passed = sum(1 for result in results if result.status == "pass")
    blocked_evidence_pass = sum(
        1
        for result in results
        if result.status == "pass" and result.actual.status in {"blocked", "blocked_with_evidence"}
    )
    failed = sum(1 for result in results if result.status == "fail")
    _out(
        {
            "success": True,
            "scenario_count": len(results),
            "passed": passed,
            "blocked_evidence_pass": blocked_evidence_pass,
            "failed": failed,
            "mode": "evidence" if evidence else "scaffold",
            "feature_results_json": str(outputs.feature_results_json),
            "actual_responses_dir": str(outputs.actual_responses_dir),
            "screenshots_dir": str(outputs.screenshots_dir),
            "report": str(outputs.report_md),
        }
    )


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


def _default_certification_report_path(timestamp: str) -> Path:
    day = timestamp.split("T", maxsplit=1)[0]
    return Path("docs") / "validation" / f"scout-feature-certification-{day}.md"


def _hosted_account_db_path(db: str, workdir: str) -> Path:
    """Resolve hosted account DB path for operator commands."""
    if db:
        return Path(db).expanduser()
    chosen_workdir = Path(workdir).expanduser() if workdir else default_workdir()
    return Path(chosen_workdir) / "hosted_accounts.sqlite"


def _load_product_records(path: Path) -> list[AlgoliaProductRecord]:
    """Load product records from a JSON list or a ProductCrawlResponse-style envelope."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        typer.echo(f"Product records file is not valid JSON: {path}", err=True)
        raise SystemExit(1) from exc
    records = raw.get("records") if isinstance(raw, dict) else raw
    if not isinstance(records, list):
        typer.echo("Product records JSON must be a list or contain a 'records' list.", err=True)
        raise SystemExit(1)
    return [
        AlgoliaProductRecord.model_validate(_normalise_product_record(record)) for record in records
    ]


def _normalise_product_record(record: object) -> object:
    """Accept Scout's serialized `_source` alias when loading records back in."""
    if not isinstance(record, dict):
        return record
    if "_source" not in record or "source" in record:
        return record
    return {**record, "source": record["_source"]}


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


def _write_unblock_artifacts(outcome: object, target: Path) -> dict:
    """Persist human-assisted capture artifacts, including reusable raw HTML."""

    from scout.core.products.captured import product_records_from_captured_html

    target.mkdir(parents=True, exist_ok=True)
    summary = outcome.model_dump(mode="json")  # type: ignore[attr-defined]
    html = str(summary.pop("html", "") or "")
    markdown = str(summary.get("markdown") or "")
    final_url = str(summary.get("final_url") or "")
    title = str(summary.get("title") or "")

    (target / "capture.md").write_text(markdown, encoding="utf-8")
    (target / "capture.html").write_text(html, encoding="utf-8")

    records = []
    if html and final_url:
        records = product_records_from_captured_html(
            html=html,
            source_url=final_url,
            category_name=title or final_url,
            limit=50,
        )
        (target / "product_records.json").write_text(
            json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    summary["html_artifact"] = str(target / "capture.html")
    summary["markdown_artifact"] = str(target / "capture.md")
    summary["product_records_artifact"] = str(target / "product_records.json") if records else ""
    summary["product_record_count"] = len(records)
    (target / "capture.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


@app.command()
def unblock(
    url: str = typer.Argument(..., help="URL to open in a real, visible browser"),
    out: str = typer.Option("", "--out", help="Directory to write the captured markdown + summary"),
    poll: float = typer.Option(
        2.0, "--poll", help="Seconds between checks while you solve the challenge"
    ),
    max_wait: float = typer.Option(
        180.0, "--max-wait", help="Max seconds to wait for you to clear the challenge"
    ),
    crawl_from_here: bool = typer.Option(
        False,
        "--crawl-from-here/--no-crawl-from-here",
        help="After the page clears, visit the top detail links in the same session and extract each",
    ),
    link_contains: str = typer.Option(
        "",
        "--link-contains",
        help="Only follow detail links whose URL contains this (e.g. /homedetails/)",
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
        summary = _write_unblock_artifacts(outcome, target)
        typer.echo(
            f"Captured cleared page -> {target} "
            f"({summary.get('product_record_count', 0)} product records)",
            err=True,
        )

    if crawl_from_here and outcome.status == "cleared":
        typer.echo(
            f"Crawling up to {limit} detail pages from the cleared session"
            + (f" (links containing '{link_contains}')" if link_contains else "")
            + " ...",
            err=True,
        )
        crawl_result = asyncio.run(
            _crawl_from_here(
                outcome.html,
                outcome.final_url or url,
                bridge,
                sleep=_sleep,
                contains=link_contains,
                limit=limit,
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
