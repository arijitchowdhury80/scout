"""Job Hunter V1 runner."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from scout.core.platform.artifacts import write_run_artifacts
from scout.core.platform.types import (
    Citation,
    FetchProviderKind,
    FetchResult,
    RunManifest,
    RunRequest,
    RunResponse,
    SourceEvidence,
    ValidationFinding,
    ValidationSeverity,
)
from scout.core.use_cases.jobs import (
    JobSearchProfile,
    TargetCompanyInput,
    TargetCompanyRecord,
    load_job_search_profile,
)
from scout.core.use_cases.jobs_extractors import extract_job_posting_from_html
from scout.core.use_cases.jobs_scoring import score_job_posting
from scout.core.use_cases.jobs_sources import JobSourcePlatform, detect_job_source_platform


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "unknown"


def _citation(source: FetchResult, field: str, claim: str, snippet: str) -> Citation:
    return Citation(
        source_id=source.evidence.source_id,
        source_url=source.evidence.source_url,
        field=field,
        claim=claim,
        snippet=snippet,
        confidence=source.evidence.confidence,
    )


def _profile_source(req: RunRequest, fetched_at: str) -> FetchResult:
    source_url = req.profile_path or "run_request:jobs_profile"
    return FetchResult(
        evidence=SourceEvidence(
            provider=FetchProviderKind.SAVED,
            source_url=source_url,
            final_url=source_url,
            fetched_at=fetched_at,
            confidence=1.0 if req.profile_path else 0.5,
        ),
        text="Job search profile supplied target companies and preferences.",
        raw={"title": "Job search profile"},
    )


def _record_from_target_company(
    company: TargetCompanyInput, source: FetchResult
) -> TargetCompanyRecord:
    return TargetCompanyRecord(
        objectID=f"target_company_{_slug(company.name)}",
        company=company.name,
        website=company.website,
        careers_url=company.careers_url,
        linkedin_url=company.linkedin_url,
        industry=company.industry,
        reason_matched="Explicitly listed in the JobSearchProfile.",
        confidence=1.0,
        citations=[
            _citation(
                source=source,
                field="target_companies",
                claim=company.name,
                snippet="Company was explicitly listed in the JobSearchProfile.",
            )
        ],
    )


def build_target_company_records(
    profile: JobSearchProfile, source: FetchResult
) -> list[TargetCompanyRecord]:
    return [_record_from_target_company(company, source) for company in profile.target_companies]


def _profile_from_request(req: RunRequest) -> JobSearchProfile:
    if req.profile_path:
        profile = load_job_search_profile(Path(req.profile_path))
    else:
        profile = JobSearchProfile(
            desired_titles=[req.query] if req.query else [],
            target_companies=[TargetCompanyInput(name=target) for target in req.targets],
        )
    if req.job_urls:
        profile = profile.model_copy(update={"job_urls": [*profile.job_urls, *req.job_urls]})
    return profile


def _read_fixture_url(url: str) -> tuple[str, str]:
    path = Path(url.removeprefix("fixture://"))
    return path.read_text(), str(path)


def _platform_for_job_url(url: str, source_url: str) -> JobSourcePlatform:
    platform = (
        JobSourcePlatform.UNKNOWN
        if url.startswith("fixture://")
        else detect_job_source_platform(url)
    )
    if platform not in {JobSourcePlatform.UNKNOWN, JobSourcePlatform.NATIVE}:
        return platform
    if "greenhouse" in source_url.lower():
        return JobSourcePlatform.GREENHOUSE
    if "ashby" in source_url.lower():
        return JobSourcePlatform.ASHBY
    if "workday" in source_url.lower():
        return JobSourcePlatform.WORKDAY
    return JobSourcePlatform.NATIVE


def _extract_seed_jobs(
    profile: JobSearchProfile,
) -> tuple[list[dict], list[FetchResult], list[dict]]:
    records: list[dict] = []
    sources: list[FetchResult] = []
    blocked: list[dict] = []

    for job_url in profile.job_urls:
        if not job_url.startswith("fixture://"):
            blocked.append(
                {
                    "url": job_url,
                    "reason": "live_job_fetch_not_implemented",
                    "message": "Job Hunter Live V1 currently supports saved fixture ingestion.",
                }
            )
            continue

        html, source_url = _read_fixture_url(job_url)
        platform = _platform_for_job_url(job_url, source_url)
        record = extract_job_posting_from_html(html=html, url=job_url, platform=platform)
        scored = score_job_posting(record, profile)
        evidence = SourceEvidence(
            provider=FetchProviderKind.SAVED,
            source_url=job_url,
            final_url=source_url,
            fetched_at=_now_iso(),
            confidence=scored.source_confidence,
        )
        source = FetchResult(evidence=evidence, html=html, text=scored.description)
        sources.append(source)
        cited = scored.model_copy(
            update={
                "citations": [
                    _citation(source, "title", scored.title, scored.title),
                    _citation(source, "compensation", str(scored.salary_max or ""), ""),
                    _citation(source, "location", scored.location, scored.location),
                    _citation(source, "department", scored.department, scored.department),
                ]
            }
        )
        records.append(cited.model_dump(mode="json"))

    return records, sources, blocked


def run_jobs_use_case(req: RunRequest) -> RunResponse:
    started_at = _now_iso()
    profile = _profile_from_request(req)
    sources: list[FetchResult] = []
    blocked: list[dict] = []
    if profile.job_urls:
        records, sources, blocked = _extract_seed_jobs(profile)
    else:
        profile_source = _profile_source(req, started_at)
        sources = [profile_source] if profile.target_companies else []
        records = [
            record.model_dump(mode="json")
            for record in build_target_company_records(profile, profile_source)
        ]
    findings: list[ValidationFinding] = []
    if not records and not profile.job_urls:
        findings.append(
            ValidationFinding(
                severity=ValidationSeverity.WARNING,
                code="no_target_companies",
                message=(
                    "Job Hunter V1 requires explicit target_companies in the profile "
                    "or targets on the run request. Live company discovery is planned."
                ),
            )
        )
    if blocked:
        findings.append(
            ValidationFinding(
                severity=ValidationSeverity.WARNING,
                code="job_url_fetch_blocked",
                message="One or more job URLs could not be fetched by the current provider.",
            )
        )

    manifest = RunManifest(
        run_id=f"run_{uuid4().hex[:12]}",
        use_case="jobs",
        query=req.query or ", ".join(profile.desired_titles),
        started_at=started_at,
        finished_at=_now_iso(),
        providers_attempted=req.providers,
        output_dir=req.output_dir,
        warnings=[finding.message for finding in findings],
    )
    report = (
        "# Scout Jobs Run\n\n"
        "Job Hunter V1 loaded the search profile and created records from the available "
        "target companies or seed job URLs. Live company discovery and ATS-specific "
        "network adapters are planned next.\n"
    )
    files = write_run_artifacts(
        output_dir=Path(req.output_dir),
        manifest=manifest,
        records=records,
        sources=sources,
        blocked=blocked,
        findings=findings,
        report=report,
    )
    manifest.artifacts = files

    return RunResponse(
        success=True,
        use_case="jobs",
        output_dir=req.output_dir,
        manifest=manifest,
        total_records=len(records),
    )
