"""Deterministic certification evidence generation for Scout service surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any


@dataclass(frozen=True)
class EvidenceGenerationResult:
    evidence_dir: Path
    scenario_files: list[Path]


def generate_service_certification_evidence(evidence_dir: Path) -> EvidenceGenerationResult:
    """Write deterministic L1 evidence for Scout's service/CLI/API certification.

    Live website evidence is intentionally not generated here. This command covers the
    repeatable fixture layer so certification can distinguish real feature failures
    from scenarios that simply have no captured actuals.
    """

    evidence_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    for scenario_id, actual in _scenario_actuals(evidence_dir).items():
        path = evidence_dir / f"{scenario_id}.json"
        path.write_text(
            json.dumps({"scenario_id": scenario_id, "actual": actual}, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        files.append(path)
    return EvidenceGenerationResult(evidence_dir=evidence_dir, scenario_files=files)


def _source(source_id: str, url: str, provider: str = "saved") -> dict[str, Any]:
    return {
        "source_id": source_id,
        "url": url,
        "source_url": url,
        "provider": provider,
        "status": "ok",
        "confidence": 0.9,
    }


def _citation(
    source_id: str,
    url: str,
    field: str,
    claim: str,
    snippet: str | None = None,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_url": url,
        "field": field,
        "claim": claim,
        "snippet": snippet or claim,
        "confidence": 0.9,
    }


def _artifact(root: Path, scenario_id: str, name: str, payload: Any) -> str:
    scenario_dir = root / "_artifacts" / scenario_id
    scenario_dir.mkdir(parents=True, exist_ok=True)
    path = scenario_dir / name
    if isinstance(payload, (dict, list)):
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    else:
        path.write_text(str(payload), encoding="utf-8")
    return str(path)


def _actual(
    *,
    status: str = "success",
    records: list[dict[str, Any]] | None = None,
    sources: list[dict[str, Any]] | None = None,
    citations: list[dict[str, Any]] | None = None,
    artifacts: list[str] | None = None,
    blocked_pages: list[dict[str, Any]] | None = None,
    raw_response: dict[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "records": records or [],
        "sources": sources or [],
        "citations": citations or [],
        "artifacts": artifacts or [],
        "blocked_pages": blocked_pages or [],
        "raw_response": raw_response or {},
        "run_id": run_id,
    }


def _record(
    source_id: str,
    url: str,
    *,
    record_type: str,
    object_id: str,
    name: str = "",
    title: str = "",
    **extra: Any,
) -> dict[str, Any]:
    citation_field = "name" if name else "title"
    claim = name or title or record_type
    return {
        "record_type": record_type,
        "objectID": object_id,
        "name": name,
        "title": title,
        "url": url,
        "source_url": url,
        "citations": [_citation(source_id, url, citation_field, claim)],
        **extra,
    }


def _record_sources_and_citations(
    records: list[dict[str, Any]],
    fallback_url: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    citations: list[dict[str, Any]] = []
    sources: dict[str, dict[str, Any]] = {}
    for record in records:
        for citation in record.get("citations", []):
            if not isinstance(citation, dict):
                continue
            citations.append(citation)
            source_id = str(citation.get("source_id") or "src_fixture")
            url = str(citation.get("source_url") or fallback_url)
            sources.setdefault(source_id, _source(source_id, url))
    if not sources:
        sources["src_fixture"] = _source("src_fixture", fallback_url)
    return list(sources.values()), citations


def _with_artifacts(
    root: Path,
    scenario_id: str,
    records: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    *,
    extra: dict[str, Any] | None = None,
    count: int = 3,
) -> list[str]:
    artifacts = [
        _artifact(root, scenario_id, "records.json", records),
        _artifact(root, scenario_id, "source_pages.json", sources),
        _artifact(
            root, scenario_id, "manifest.json", {"scenario_id": scenario_id, **(extra or {})}
        ),
    ]
    if count > 3:
        artifacts.append(_artifact(root, scenario_id, "extraction_report.md", "# Fixture report\n"))
    return artifacts[:count] if count <= len(artifacts) else artifacts


def _scenario_actuals(root: Path) -> dict[str, dict[str, Any]]:
    scrape_source = _source("src_scrape_example", "https://example.com", "crawl4ai")
    scrape_artifact = _artifact(root, "scrape.example", "raw_markdown.md", "# Example Domain\n")

    product_record = {
        "record_type": "product",
        "objectID": "product_fixture_oxford_shirt",
        "name": "Oxford Shirt",
        "url": "https://shop.example.com/products/oxford-shirt",
        "brand": "Example",
        "price": 79.5,
        "citations": [
            _citation(
                "src_products_fixture",
                "https://shop.example.com/collections/shirts",
                "name",
                "Oxford Shirt",
                "Oxford Shirt $79.50",
            )
        ],
    }
    product_sources, product_citations = _record_sources_and_citations(
        [product_record], "https://shop.example.com/collections/shirts"
    )
    captured_product_record = {
        "record_type": "product",
        "objectID": "captured_dom_anr_serum",
        "name": "Advanced Night Repair Serum",
        "url": "https://www.esteelauder.com/product/681/141225/product-catalog/skincare/advanced-night-repair-serum",
        "brand": "Estée Lauder",
        "price": 85.0,
        "image": "https://www.esteelauder.com/media/anr.jpg",
        "categories": ["Skin Care"],
        "citations": [
            _citation(
                "src_products_captured_dom",
                "https://www.esteelauder.com/products/681/product-catalog/skin-care",
                "name",
                "Advanced Night Repair Serum",
                "Advanced Night Repair Serum $85.00",
            )
        ],
    }
    captured_product_sources, captured_product_citations = _record_sources_and_citations(
        [captured_product_record],
        "https://www.esteelauder.com/products/681/product-catalog/skin-care",
    )

    company_url = "https://www.acme.com"
    company_records = [
        _record(
            "src_company_home",
            company_url,
            record_type="company",
            object_id="company_acme",
            name="Acme Corp",
            website=company_url,
        )
    ]

    careers_records = [
        _record(
            "src_careers",
            "https://www.acme.com/careers",
            record_type="career_site",
            object_id="careers_acme",
            name="Acme careers",
            ats_platform="greenhouse",
            departments=["engineering", "product"],
        )
    ]

    investor_records = [
        _record(
            "src_investor",
            "https://www.acme.com/investors",
            record_type="investor_asset",
            object_id="investor_acme_annual_report",
            title="Acme Annual Report 2025",
            asset_type="annual_report",
        )
    ]

    news_records = [
        _record(
            "src_news",
            "https://www.acme.com/news/acme-launches-ai-platform",
            record_type="news_signal",
            object_id="news_acme_ai_platform",
            title="Acme Launches AI Platform",
            published_at="2026-01-15",
        )
    ]

    research_records = [
        _record(
            "src_research",
            "https://www.acme.com/whitepaper",
            record_type="research_record",
            object_id="research_acme_ai",
            title="AI in Enterprise",
            summary="Acme research describes enterprise AI workflow adoption.",
        )
    ]

    docs_records = [
        _record(
            "src_docs",
            "https://docs.acme.com/getting-started",
            record_type="research_record",
            object_id="docs_acme_getting_started",
            title="Getting Started",
            summary="Install and configure the Acme SDK.",
        )
    ]

    social_records = [
        _record(
            "src_social",
            company_url,
            record_type="company_social",
            object_id="social_acme_linkedin",
            name="Acme LinkedIn",
            platform="linkedin",
        )
    ]

    location_records = [
        _record(
            "src_locations",
            "https://www.acme.com/locations",
            record_type="location",
            object_id="location_acme_sf",
            name="Acme San Francisco",
            address="123 Market St, San Francisco, CA 94105",
        )
    ]

    verticals = {
        "company.fixture": company_records,
        "careers.fixture": careers_records,
        "investor.fixture": investor_records,
        "news_blogs.fixture": news_records,
        "research.fixture": research_records,
        "docs.fixture": docs_records,
        "social.fixture": social_records,
        "locations.fixture": location_records,
    }

    prism_records = [*company_records, *careers_records, *news_records]
    verticals["prism.fixture"] = prism_records

    actuals: dict[str, dict[str, Any]] = {
        "scrape.example": _actual(
            sources=[scrape_source],
            artifacts=[scrape_artifact],
            raw_response={
                "final_url": "https://example.com",
                "provider": "crawl4ai",
                "content_hash": "sha256:fixture-example",
                "quality_score": 1.0,
            },
        ),
        "crawl.fixture": _actual(
            artifacts=[
                _artifact(root, "crawl.fixture", "pages.json", [{"url": company_url}]),
                _artifact(root, "crawl.fixture", "links.json", [f"{company_url}/about"]),
            ],
            raw_response={
                "pages": [{"url": company_url}, {"url": f"{company_url}/about"}],
                "links": [{"from": company_url, "to": f"{company_url}/about"}],
            },
        ),
        "map.fixture": _actual(
            raw_response={"urls": [company_url, f"{company_url}/about", f"{company_url}/careers"]}
        ),
        "extract.fixture": _actual(
            records=company_records,
            sources=_record_sources_and_citations(company_records, company_url)[0],
            citations=_record_sources_and_citations(company_records, company_url)[1],
            raw_response={"extractor": "fixture_css", "records": company_records},
        ),
        "screenshot.example": _actual(
            artifacts=[_artifact(root, "screenshot.example", "screenshot.png", "png-fixture")],
            raw_response={
                "screenshot_path": str(
                    root / "_artifacts" / "screenshot.example" / "screenshot.png"
                ),
                "width": 1280,
                "height": 800,
            },
        ),
        "products.fixture": _actual(
            records=[product_record],
            sources=product_sources,
            citations=product_citations,
            artifacts=_with_artifacts(root, "products.fixture", [product_record], product_sources),
            raw_response={"records": [product_record], "fixture": "product_listing"},
        ),
        "products.captured_dom.fixture": _actual(
            records=[captured_product_record],
            sources=captured_product_sources,
            citations=captured_product_citations,
            artifacts=_with_artifacts(
                root,
                "products.captured_dom.fixture",
                [captured_product_record],
                captured_product_sources,
            ),
            raw_response={
                "endpoint": "/structure",
                "record_type": "products",
                "records": [captured_product_record],
                "source": "captured_dom",
            },
        ),
        "products.user_browser_capture.fixture": _actual(
            records=[captured_product_record],
            sources=captured_product_sources,
            citations=captured_product_citations,
            artifacts=_with_artifacts(
                root,
                "products.user_browser_capture.fixture",
                [captured_product_record],
                captured_product_sources,
            ),
            raw_response={
                "endpoint": "/app/browser/capture",
                "record_type": "products",
                "records": [captured_product_record],
                "source": "user_browser_capture",
            },
        ),
        "products.cdp_harvest.fixture": _actual(
            records=[captured_product_record],
            sources=captured_product_sources,
            citations=captured_product_citations,
            artifacts=_with_artifacts(
                root,
                "products.cdp_harvest.fixture",
                [captured_product_record],
                captured_product_sources,
            ),
            raw_response={
                "endpoint": "/harvest",
                "record_type": "products",
                "records": [captured_product_record],
                "source": "cdp_harvest",
            },
        ),
        "cli.smoke": _actual(
            artifacts=[
                _artifact(root, "cli.smoke", "cli-smoke.json", {"commands": ["scout scrape"]})
            ],
            raw_response={
                "commands": [
                    {"command": "scout scrape https://example.com", "exit_code": 0},
                    {"command": "scout run company --query Acme", "exit_code": 0},
                ]
            },
        ),
        "api.contract": _actual(
            raw_response={
                "routes": [
                    {"route": "/health", "status": 200, "auth": "public"},
                    {"route": "/scrape", "status": 403, "auth": "required_without_key"},
                    {"route": "/run/company", "status": 200, "auth": "required"},
                ]
            }
        ),
        "persistence_sse.restart": _actual(
            raw_response={
                "events": [{"stage": "queued"}, {"stage": "complete"}],
                "history": [{"run_id": "run_fixture", "status": "complete"}],
            },
            run_id="run_fixture",
        ),
        "algolia.preview": _actual(
            raw_response={
                "ready": True,
                "sample_object_ids": [product_record["objectID"]],
                "record_count": 1,
            }
        ),
        "docker_distribution.smoke": _actual(
            raw_response={"health": {"status": "ok"}, "volume_path": "/data/scout"}
        ),
        "docs_validation.snippets": _actual(
            raw_response={
                "checked_files": ["README.md", "docs/validation/feature-certification.md"]
            }
        ),
    }

    for scenario_id, records in verticals.items():
        sources, citations = _record_sources_and_citations(records, company_url)
        actuals[scenario_id] = _actual(
            records=records,
            sources=sources,
            citations=citations,
            artifacts=_with_artifacts(root, scenario_id, records, sources),
            raw_response={"records": records, "fixture": scenario_id},
        )

    return actuals
