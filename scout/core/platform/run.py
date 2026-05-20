"""High-level Scout run dispatcher."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from scout.core.platform.artifacts import write_run_artifacts
from scout.core.platform.registry import get_use_case
from scout.core.platform.types import RunManifest, RunRequest, RunResponse


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_use_case(req: RunRequest) -> RunResponse:
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
