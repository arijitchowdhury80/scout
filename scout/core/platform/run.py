"""High-level Scout run dispatcher."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from scout.core.platform.artifacts import write_run_artifacts
from scout.core.platform.registry import get_use_case
from scout.core.platform.types import RunManifest, RunRequest, RunResponse

if TYPE_CHECKING:
    from scout.core.crawler import ScoutCrawler

_REAL_RUNNERS = {
    "company",
    "careers",
    "investor",
    "news",
    "research",
    "docs",
    "social",
    "locations",
    "website-quality",
    "products",
}
_LIVE_MODES = {"auto", "crawl4ai", "browser", "user-browser"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _should_use_real_runner(req: RunRequest, crawler: "ScoutCrawler | None") -> bool:
    return crawler is not None and req.use_case in _REAL_RUNNERS and req.mode in _LIVE_MODES


async def run_use_case(req: RunRequest, crawler: "ScoutCrawler | None" = None) -> RunResponse:
    use_case = get_use_case(req.use_case)
    if use_case is None:
        return RunResponse(
            success=False,
            use_case=req.use_case,
            output_dir=req.output_dir,
            error=f"Unsupported use case: {req.use_case}",
        )
    if req.use_case == "jobs":
        from scout.core.use_cases.jobs_runner import run_jobs_use_case

        return run_jobs_use_case(req)

    if _should_use_real_runner(req, crawler):
        assert crawler is not None
        return await _run_real_vertical(req, crawler, use_case.description)

    if req.use_case == "prism" and crawler is not None and req.mode in _LIVE_MODES:
        return await _run_prism(req, crawler, use_case.description)

    if req.use_case in {
        "company",
        "careers",
        "products",
        "prism",
        "investor",
        "research",
        "website-quality",
        "docs",
        "news",
        "social",
        "locations",
    }:
        from scout.core.use_cases.intelligence_runner import run_intelligence_use_case

        return run_intelligence_use_case(req, use_case.description)

    started_at = _now_iso()
    manifest = RunManifest(
        run_id=f"run_{uuid4().hex[:12]}",
        use_case=req.use_case,
        query=req.query,
        started_at=started_at,
        finished_at=_now_iso(),
        providers_attempted=req.providers,
        output_dir=req.output_dir,
        warnings=[
            (
                f"{use_case.name} run mode has a platform artifact contract; "
                "domain extraction implementation is pending."
            )
        ],
    )
    report = (
        f"# Scout {use_case.name} Run\n\n"
        f"{use_case.description}\n\n"
        "This run wrote the standard platform artifact set. Domain extraction is pending.\n"
    )
    files = write_run_artifacts(
        output_dir=Path(req.output_dir),
        manifest=manifest,
        records=[],
        sources=[],
        blocked=[],
        findings=[],
        report=report,
    )
    manifest.artifacts = files

    return RunResponse(
        success=True,
        use_case=req.use_case,
        output_dir=req.output_dir,
        manifest=manifest,
        total_records=0,
    )


async def _run_real_vertical(
    req: RunRequest, crawler: "ScoutCrawler", description: str
) -> RunResponse:
    from scout.core.platform.execution import ExecutionMode, provider_ladder_for_mode

    started_at = _now_iso()
    mode = ExecutionMode(req.mode)
    providers = provider_ladder_for_mode(mode)

    records: list[dict] = []
    errors: list[str] = []

    try:
        if req.use_case == "company":
            from scout.core.use_cases.runners.company import run_company

            records = await run_company(req, crawler)
        elif req.use_case == "careers":
            from scout.core.use_cases.runners.careers import run_careers

            records = await run_careers(req, crawler)
        elif req.use_case == "investor":
            from scout.core.use_cases.runners.investor import run_investor

            records = await run_investor(req, crawler)
        elif req.use_case == "news":
            from scout.core.use_cases.runners.news import run_news

            records = await run_news(req, crawler)
        elif req.use_case == "research":
            from scout.core.use_cases.runners.research import run_research

            records = await run_research(req, crawler)
        elif req.use_case == "docs":
            from scout.core.use_cases.runners.docs import run_docs

            records = await run_docs(req, crawler)
        elif req.use_case == "social":
            from scout.core.use_cases.runners.social import run_social

            records = await run_social(req, crawler)
        elif req.use_case == "locations":
            from scout.core.use_cases.runners.locations import run_locations

            records = await run_locations(req, crawler)
        elif req.use_case == "website-quality":
            from scout.core.use_cases.runners.website_quality import run_website_quality

            records = await run_website_quality(req, crawler)
        elif req.use_case == "products":
            from scout.core.types import ProductCrawlRequest

            prod_resp = await crawler.products(
                ProductCrawlRequest(site=req.url or "", query=req.query)
            )
            records = [r.model_dump(mode="json") for r in prod_resp.records]
    except Exception as exc:
        errors.append(str(exc))

    manifest = RunManifest(
        run_id=f"run_{uuid4().hex[:12]}",
        use_case=req.use_case,
        query=req.query,
        started_at=started_at,
        finished_at=_now_iso(),
        providers_attempted=providers,
        output_dir=req.output_dir,
        total_records=len(records),
        warnings=[] if records else [f"{req.use_case} produced no records."],
        errors=errors,
    )

    report = (
        f"# Scout {req.use_case.title()} Run\n\n"
        f"{description}\n\n"
        f"Execution mode: `{mode.value}`. Records: {len(records)}.\n"
    )
    files = write_run_artifacts(
        output_dir=Path(req.output_dir),
        manifest=manifest,
        records=records,
        sources=[],
        blocked=[],
        findings=[],
        report=report,
    )
    manifest.artifacts = files

    return RunResponse(
        success=len(records) > 0 and not errors,
        use_case=req.use_case,
        output_dir=req.output_dir,
        manifest=manifest,
        total_records=len(records),
        error=errors[0] if errors else "",
    )


async def _run_prism(req: RunRequest, crawler: "ScoutCrawler", description: str) -> RunResponse:
    """PRISM = all intelligence verticals combined."""
    from scout.core.use_cases.runners.careers import run_careers
    from scout.core.use_cases.runners.company import run_company
    from scout.core.use_cases.runners.investor import run_investor
    from scout.core.use_cases.runners.news import run_news
    from scout.core.use_cases.runners.social import run_social
    from scout.core.platform.execution import ExecutionMode, provider_ladder_for_mode

    started_at = _now_iso()
    mode = ExecutionMode(req.mode)
    providers = provider_ladder_for_mode(mode)
    all_records: list[dict] = []
    errors: list[str] = []

    # PRISM V1 is the prospect-intelligence bundle: company/executive/social,
    # careers, investor, and recent news. Keep broader research/docs/quality
    # workflows as explicit use cases so PRISM remains bounded for UI runs.
    for runner in [run_company, run_careers, run_investor, run_news, run_social]:
        try:
            records = await runner(req, crawler)
            all_records.extend(records)
        except Exception as exc:
            errors.append(f"{runner.__module__}: {exc}")

    manifest = RunManifest(
        run_id=f"run_{uuid4().hex[:12]}",
        use_case="prism",
        query=req.query,
        started_at=started_at,
        finished_at=_now_iso(),
        providers_attempted=providers,
        output_dir=req.output_dir,
        total_records=len(all_records),
        errors=errors,
    )

    report = (
        f"# Scout PRISM Run\n\n{description}\n\n"
        f"Execution mode: `{mode.value}`. Total records: {len(all_records)}.\n"
    )
    files = write_run_artifacts(
        output_dir=Path(req.output_dir),
        manifest=manifest,
        records=all_records,
        sources=[],
        blocked=[],
        findings=[],
        report=report,
    )
    manifest.artifacts = files

    return RunResponse(
        success=len(all_records) > 0,
        use_case="prism",
        output_dir=req.output_dir,
        manifest=manifest,
        total_records=len(all_records),
    )
