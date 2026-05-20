"""Deterministic V1 runners for Scout intelligence use cases."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from scout.core.platform.artifacts import write_run_artifacts
from scout.core.platform.execution import ExecutionMode, provider_ladder_for_mode
from scout.core.platform.types import (
    Citation,
    FetchProviderKind,
    FetchResult,
    RunManifest,
    RunRequest,
    RunResponse,
    SourceEvidence,
)
from scout.core.use_cases.intelligence import (
    CareerSiteRecord,
    InvestorAssetRecord,
    NewsSignalRecord,
    ResearchRecord,
)
from scout.core.use_cases.prism import CompanyRecord, CompanySocialRecord, ExecutiveRecord
from scout.core.use_cases.products_v2 import ProductRecord


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "unknown"


def _company_name(req: RunRequest) -> str:
    return req.query.strip() or (req.targets[0].strip() if req.targets else "unknown")


def _website(req: RunRequest, company: str) -> str:
    for target in req.targets:
        if target.startswith(("http://", "https://")):
            return target
    return f"https://www.{_slug(company).replace('_', '')}.com"


def _source_for_request(
    req: RunRequest, provider: FetchProviderKind, fetched_at: str
) -> FetchResult:
    topic = _company_name(req)
    url = req.url or (req.targets[0] if req.targets else _website(req, topic))
    return FetchResult(
        evidence=SourceEvidence(
            provider=provider,
            source_url=url,
            final_url=url,
            fetched_at=fetched_at,
            confidence=0.35,
        ),
        text=f"Derived Scout seed evidence for {topic}. Live acquisition is pending.",
        raw={"title": f"{topic} source seed"},
    )


def _citation(
    source: FetchResult,
    field: str,
    claim: str,
    snippet: str,
    confidence: float = 0.35,
) -> Citation:
    return Citation(
        source_id=source.evidence.source_id,
        source_url=source.evidence.source_url,
        field=field,
        claim=claim,
        snippet=snippet,
        confidence=confidence,
    )


def company_records(req: RunRequest, source: FetchResult) -> list[dict]:
    company = _company_name(req)
    slug = _slug(company)
    website = _website(req, company)
    records = [
        CompanyRecord(
            objectID=f"company_{slug}",
            name=company,
            website=website,
            linkedin_url=f"https://www.linkedin.com/company/{slug.replace('_', '-')}/",
            description=f"{company} company intelligence seed record.",
            source_urls=[website],
            confidence=0.65,
            citations=[
                _citation(
                    source=source,
                    field="website",
                    claim=website,
                    snippet=f"{company} company seed source: {website}",
                    confidence=0.35,
                )
            ],
        ),
        ExecutiveRecord(
            objectID=f"executive_{slug}_leadership",
            company=company,
            name="Leadership team",
            title="Executive leadership",
            source_url=website,
            confidence=0.35,
            citations=[
                _citation(
                    source=source,
                    field="title",
                    claim="Executive leadership",
                    snippet="Leadership seed record; live executive extraction is pending.",
                )
            ],
        ),
        CompanySocialRecord(
            objectID=f"social_{slug}_linkedin",
            company=company,
            platform="linkedin",
            url=f"https://www.linkedin.com/company/{slug.replace('_', '-')}/",
            provider="derived",
            confidence=0.45,
            citations=[
                _citation(
                    source=source,
                    field="url",
                    claim=f"https://www.linkedin.com/company/{slug.replace('_', '-')}/",
                    snippet="Derived LinkedIn company URL seed.",
                )
            ],
        ),
    ]
    return [record.model_dump(mode="json") for record in records]


def career_records(req: RunRequest, source: FetchResult) -> list[dict]:
    company = _company_name(req)
    slug = _slug(company)
    website = _website(req, company).rstrip("/")
    return [
        CareerSiteRecord(
            objectID=f"careers_{slug}",
            company=company,
            careers_url=f"{website}/careers",
            ats_platform="unknown",
            hiring_signal_summary="Careers run initialized; live role extraction requires acquisition.",
            source_url=website,
            confidence=0.4,
            citations=[
                _citation(
                    source=source,
                    field="careers_url",
                    claim=f"{website}/careers",
                    snippet="Derived careers URL seed; live careers extraction is pending.",
                )
            ],
        ).model_dump(mode="json")
    ]


def investor_records(req: RunRequest, source: FetchResult) -> list[dict]:
    company = _company_name(req)
    slug = _slug(company)
    website = _website(req, company).rstrip("/")
    return [
        InvestorAssetRecord(
            objectID=f"investor_{slug}_relations",
            company=company,
            asset_type="investor_page",
            url=f"{website}/investor-relations",
            title=f"{company} investor relations",
            source_url=website,
            confidence=0.4,
            citations=[
                _citation(
                    source=source,
                    field="url",
                    claim=f"{website}/investor-relations",
                    snippet="Derived investor relations URL seed; live investor extraction is pending.",
                )
            ],
        ).model_dump(mode="json")
    ]


def news_records(req: RunRequest, source: FetchResult) -> list[dict]:
    company = _company_name(req)
    slug = _slug(company)
    website = _website(req, company).rstrip("/")
    return [
        NewsSignalRecord(
            objectID=f"news_{slug}_latest",
            company=company,
            title=f"{company} latest news",
            url=f"{website}/news",
            topic="company_news",
            source_url=website,
            confidence=0.35,
            citations=[
                _citation(
                    source=source,
                    field="url",
                    claim=f"{website}/news",
                    snippet="Derived news URL seed; live news extraction is pending.",
                )
            ],
        ).model_dump(mode="json")
    ]


def research_records(req: RunRequest, source: FetchResult) -> list[dict]:
    topic = _company_name(req)
    slug = _slug(topic)
    url = _website(req, topic)
    return [
        ResearchRecord(
            objectID=f"research_{slug}",
            topic=topic,
            url=url,
            title=f"{topic} research",
            summary="Research run initialized; acquisition providers collect evidence in later slices.",
            source_url=url,
            confidence=0.35,
            citations=[
                _citation(
                    source=source,
                    field="summary",
                    claim="Research run initialized.",
                    snippet="Research seed record; acquisition providers collect evidence in later slices.",
                )
            ],
        ).model_dump(mode="json")
    ]


def product_records(req: RunRequest, source: FetchResult) -> list[dict]:
    query = req.query.strip() or "product catalog"
    slug = _slug(query)
    url = req.url or (req.targets[0] if req.targets else _website(req, query))
    record = ProductRecord(
        objectID=f"product_seed_{slug}",
        brand=_company_name(req) if req.query else "",
        name=query,
        url=url,
        category=query,
        description=(
            "Product run initialized; live catalog acquisition and enrichment happen "
            "through Crawl4AI/API/browser providers in production runs."
        ),
        completeness_score=0.2,
        citations=[
            _citation(
                source=source,
                field="url",
                claim=url,
                snippet="Product catalog seed URL; live product extraction is pending.",
            )
        ],
    ).model_dump(mode="json")
    record["record_type"] = "product"
    return [record]


def records_for_use_case(req: RunRequest, source: FetchResult) -> list[dict]:
    if req.use_case == "company":
        return company_records(req, source)
    if req.use_case == "careers":
        return career_records(req, source)
    if req.use_case == "investor":
        return investor_records(req, source)
    if req.use_case == "news":
        return news_records(req, source)
    if req.use_case in {"research", "docs", "website-quality", "social", "locations"}:
        return research_records(req, source)
    if req.use_case == "products":
        return product_records(req, source)
    if req.use_case == "prism":
        return [
            *company_records(req, source),
            *career_records(req, source),
            *investor_records(req, source),
            *news_records(req, source),
        ]
    return []


def run_intelligence_use_case(req: RunRequest, description: str = "") -> RunResponse:
    started_at = _now_iso()
    mode = ExecutionMode(req.mode)
    providers = provider_ladder_for_mode(mode)
    source = _source_for_request(
        req, providers[0] if providers else FetchProviderKind.SAVED, started_at
    )
    records = records_for_use_case(req, source)
    manifest = RunManifest(
        run_id=f"run_{uuid4().hex[:12]}",
        use_case=req.use_case,
        query=req.query,
        started_at=started_at,
        finished_at=_now_iso(),
        providers_attempted=providers,
        output_dir=req.output_dir,
        warnings=[] if records else [f"{req.use_case} produced no records."],
    )
    report = (
        f"# Scout {req.use_case.title()} Run\n\n"
        f"{description}\n\n"
        f"Execution mode: `{mode.value}`. Records written: {len(records)}.\n"
    )
    files = write_run_artifacts(
        output_dir=Path(req.output_dir),
        manifest=manifest,
        records=records,
        sources=[source],
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
        total_records=len(records),
    )
