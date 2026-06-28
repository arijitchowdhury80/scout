"""Scout feature certification matrix and result writer.

This module is intentionally small and dependency-light: tests and scripts can use it
to turn feature validation runs into a consistent expected-vs-actual report.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
from typing import Any


REQUIRED_FEATURE_AREAS: set[str] = {
    "scrape",
    "crawl",
    "map",
    "extract",
    "screenshot",
    "products",
    "company",
    "prism",
    "investor",
    "careers",
    "jobs",
    "news_blogs",
    "research",
    "docs",
    "social",
    "locations",
    "website_quality",
    "browser_workbench",
    "cli",
    "api",
    "persistence_sse",
    "algolia",
    "docker_distribution",
    "docs_validation",
}


@dataclass(frozen=True)
class CertificationScenario:
    scenario_id: str
    area: str
    tier: str
    interface: str
    input_data: dict[str, Any]
    expected_output: dict[str, Any]
    acceptance_criteria: list[str]
    required_actual_fields: list[str]
    min_records: int = 0
    min_sources: int = 0
    min_citations: int = 0
    min_artifacts: int = 0
    allows_blocked: bool = False
    required_blocked_fields: list[str] | None = None


@dataclass(frozen=True)
class CertificationActual:
    status: str
    records: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    artifacts: list[str]
    blocked_pages: list[dict[str, Any]]
    raw_response: dict[str, Any]
    run_id: str | None = None
    screenshots: list[str] | None = None

    @property
    def record_count(self) -> int:
        return len(self.records)

    @property
    def source_count(self) -> int:
        return len(self.sources)

    @property
    def citation_count(self) -> int:
        return len(self.citations)

    @property
    def blocked_count(self) -> int:
        return len(self.blocked_pages)


@dataclass(frozen=True)
class CertificationResult:
    scenario: CertificationScenario
    status: str
    actual: CertificationActual
    failures: list[str]
    notes: list[str]


@dataclass(frozen=True)
class CertificationOutputs:
    run_dir: Path
    feature_results_json: Path
    actual_responses_dir: Path
    screenshots_dir: Path
    report_md: Path


def _scenario(
    scenario_id: str,
    area: str,
    tier: str,
    interface: str,
    input_data: dict[str, Any],
    expected_output: dict[str, Any],
    acceptance_criteria: list[str],
    required_actual_fields: list[str],
    *,
    min_records: int = 0,
    min_sources: int = 0,
    min_citations: int = 0,
    min_artifacts: int = 0,
    allows_blocked: bool = False,
    required_blocked_fields: list[str] | None = None,
) -> CertificationScenario:
    return CertificationScenario(
        scenario_id=scenario_id,
        area=area,
        tier=tier,
        interface=interface,
        input_data=input_data,
        expected_output=expected_output,
        acceptance_criteria=acceptance_criteria,
        required_actual_fields=required_actual_fields,
        min_records=min_records,
        min_sources=min_sources,
        min_citations=min_citations,
        min_artifacts=min_artifacts,
        allows_blocked=allows_blocked,
        required_blocked_fields=required_blocked_fields,
    )


_PRODUCT_FIELDS = ["records[].objectID", "records[].name", "records[].url"]
_SOURCE_FIELDS = ["sources[].source_id", "sources[].url"]
_CITATION_FIELDS = ["citations[].source_id"]


PRODUCT_LIVE_TARGETS: tuple[tuple[str, str], ...] = (
    ("estee_lauder", "https://www.esteelauder.com/products/681/product-catalog/skin-care"),
    ("lacoste", "https://www.lacoste.com/us/lacoste/men/clothing/polos"),
    ("nike", "https://www.nike.com/w/mens-shirts-tops-9om13znik1"),
    ("ll_bean", "https://www.llbean.com/llb/shop/502859"),
    ("patagonia", "https://www.patagonia.com/shop/mens/tops"),
    ("home_depot", "https://www.homedepot.com/s/cordless%20drill"),
)

USER_BROWSER_PRODUCT_LIVE_TARGETS: tuple[tuple[str, str], ...] = (
    ("estee_lauder", "https://www.esteelauder.com/products/681/product-catalog/skin-care"),
    ("patagonia", "https://www.patagonia.com/shop/mens/tops"),
    ("home_depot", "https://www.homedepot.com/s/cordless%20drill"),
)

INTELLIGENCE_LIVE_TARGETS: tuple[tuple[str, str, str], ...] = tuple(
    (use_case, slug, url)
    for use_case in ("company", "prism", "careers", "news_blogs")
    for slug, url in (
        ("algolia", "https://www.algolia.com/"),
        ("constructor", "https://constructor.com/"),
        ("adobe", "https://www.adobe.com/"),
        ("home_depot", "https://www.homedepot.com/"),
        ("nike", "https://www.nike.com/"),
        ("british_airways", "https://www.britishairways.com/"),
        ("estee_lauder", "https://www.esteelauder.com/"),
    )
)

INVESTOR_LIVE_TARGETS: tuple[tuple[str, str], ...] = (
    ("adobe", "https://www.adobe.com/investor-relations.html"),
    ("home_depot", "https://ir.homedepot.com/"),
    ("estee_lauder_parent", "https://www.elcompanies.com/en/investors"),
    ("british_airways_iag", "https://www.iairgroup.com/en/investors-and-shareholders"),
)

_BASE_CERTIFICATION_MATRIX: tuple[CertificationScenario, ...] = (
    _scenario(
        "scrape.example",
        "scrape",
        "L1",
        "api",
        {"url": "https://example.com"},
        {"content": "markdown/html/text", "metadata": ["final_url", "provider", "content_hash"]},
        ["returns content", "records final URL and provider", "preserves source evidence"],
        ["raw_response.final_url", "raw_response.provider", "raw_response.content_hash"],
        min_sources=1,
    ),
    _scenario(
        "crawl.fixture",
        "crawl",
        "L1",
        "fixture",
        {"site": "saved mini-site", "max_depth": 2},
        {"pages": "multiple pages", "links": "internal link graph"},
        ["respects max depth", "writes artifact contract"],
        ["raw_response.pages", "raw_response.links"],
        min_artifacts=2,
    ),
    _scenario(
        "map.fixture",
        "map",
        "L1",
        "fixture",
        {"site": "saved sitemap fixture"},
        {"urls": "URL map", "titles": "page titles"},
        ["extracts URL map", "includes titles where available"],
        ["raw_response.urls"],
    ),
    _scenario(
        "extract.fixture",
        "extract",
        "L1",
        "fixture",
        {"html": "saved product/job/company HTML"},
        {"records": "structured records with citations"},
        ["extracts typed records", "records contain citations"],
        ["records[].record_type", *_CITATION_FIELDS],
        min_records=1,
        min_citations=1,
    ),
    _scenario(
        "screenshot.example",
        "screenshot",
        "L1",
        "api",
        {"url": "https://example.com"},
        {"artifact": "screenshot", "metadata": ["width", "height", "source_url"]},
        ["writes screenshot artifact", "records dimensions"],
        ["raw_response.screenshot_path", "raw_response.width", "raw_response.height"],
        min_artifacts=1,
    ),
    _scenario(
        "products.fixture",
        "products",
        "L1",
        "fixture",
        {"site": "books.toscrape fixture"},
        {"records": "Algolia-ready product records", "fields": ["objectID", "name", "url"]},
        ["records are Algolia-previewable", "records cite listing/detail source"],
        [*_PRODUCT_FIELDS, *_SOURCE_FIELDS, *_CITATION_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
        min_artifacts=3,
    ),
    _scenario(
        "products.captured_dom.fixture",
        "products",
        "L1",
        "api",
        {
            "endpoint": "POST /structure",
            "record_type": "products",
            "source": "captured category DOM",
        },
        {
            "records": "Algolia-ready product records from already-captured HTML",
            "fields": ["objectID", "name", "url", "citations"],
        },
        [
            "does not re-fetch blocked hard-site URLs",
            "extracts listing product records from captured DOM",
            "records are Algolia-previewable",
        ],
        [*_PRODUCT_FIELDS, *_SOURCE_FIELDS, *_CITATION_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
        min_artifacts=3,
    ),
    _scenario(
        "products.user_browser_capture.fixture",
        "products",
        "L1",
        "api",
        {
            "endpoint": "POST /app/browser/capture",
            "record_type": "products",
            "source": "user-browser captured category DOM",
        },
        {
            "records": "Algolia-ready product records from a cleared user-browser capture",
            "fields": ["objectID", "name", "url", "citations"],
        },
        [
            "captures held browser DOM without requiring CSS selectors",
            "extracts product listing records from user-visible hard-site pages",
            "records are Algolia-previewable",
        ],
        [*_PRODUCT_FIELDS, *_SOURCE_FIELDS, *_CITATION_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
        min_artifacts=3,
    ),
    _scenario(
        "products.cdp_harvest.fixture",
        "products",
        "L1",
        "api",
        {
            "endpoint": "POST /harvest",
            "record_type": "products",
            "source": "CDP-attached user browser tab",
        },
        {
            "records": "Algolia-ready product records from a live CDP tab harvest",
            "fields": ["objectID", "name", "url", "citations"],
        },
        [
            "attaches to an already-open browser tab without re-navigation",
            "extracts product records from harvested hard-site DOM",
            "records are Algolia-previewable",
        ],
        [*_PRODUCT_FIELDS, *_SOURCE_FIELDS, *_CITATION_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
        min_artifacts=3,
    ),
    _scenario(
        "company.fixture",
        "company",
        "L1",
        "fixture",
        {"company": "Acme Corp", "url": "https://www.acme.com"},
        {"records": ["company", "company_social", "executive"], "citations": True},
        ["company overview exists", "key URLs/socials cite source evidence"],
        ["records[].record_type", "records[].name", *_SOURCE_FIELDS, *_CITATION_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
    ),
    _scenario(
        "prism.fixture",
        "prism",
        "L1",
        "fixture",
        {"company": "Acme Corp", "url": "https://www.acme.com"},
        {"bundle": ["company", "careers", "news", "investor where applicable"]},
        ["bundles multiple verticals", "each claim has provenance or warning"],
        ["records[].record_type", *_SOURCE_FIELDS],
        min_records=3,
        min_sources=2,
        min_citations=1,
    ),
    _scenario(
        "investor.fixture",
        "investor",
        "L1",
        "fixture",
        {"url": "https://www.acme.com/investors"},
        {"records": "investor assets, reports, filings, events"},
        ["finds investor page", "extracts report/filing assets"],
        ["records[].record_type", "records[].asset_type", *_SOURCE_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
    ),
    _scenario(
        "careers.fixture",
        "careers",
        "L1",
        "fixture",
        {"url": "https://www.acme.com/careers"},
        {"records": "career_site with ATS and hiring signals"},
        ["detects ATS where visible", "extracts departments/jobs where visible"],
        ["records[].record_type", *_SOURCE_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
    ),
    _scenario(
        "jobs.fixture",
        "jobs",
        "L1",
        "fixture",
        {"html": "saved ATS job fixture"},
        {"records": "job postings with match fields and source evidence"},
        ["extracts title/company/location", "captures compensation when present"],
        ["records[].record_type", "records[].title", *_SOURCE_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
    ),
    _scenario(
        "news_blogs.fixture",
        "news_blogs",
        "L1",
        "fixture",
        {"url": "https://www.acme.com/blog"},
        {"records": "latest news/blog entries with dates and URLs"},
        ["extracts recent posts", "captures date where available"],
        ["records[].record_type", "records[].title", *_SOURCE_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
    ),
    _scenario(
        "research.fixture",
        "research",
        "L1",
        "fixture",
        {"targets": ["https://www.acme.com/whitepaper"], "prompt": "AI enterprise research"},
        {"records": "research records, summary, source list, citations"},
        ["summarizes sourced material", "keeps source list"],
        ["records[].record_type", "records[].summary", *_SOURCE_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
    ),
    _scenario(
        "docs.fixture",
        "docs",
        "L1",
        "fixture",
        {"url": "https://docs.acme.com"},
        {"records": "documentation pages with sections and URLs"},
        ["extracts multiple docs pages", "preserves markdown/source evidence"],
        ["records[].record_type", "records[].title", *_SOURCE_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
    ),
    _scenario(
        "social.fixture",
        "social",
        "L1",
        "fixture",
        {"url": "https://www.acme.com"},
        {"records": "company social profile records"},
        ["finds platform URLs", "cites source that exposed the social profile"],
        ["records[].record_type", "records[].platform", *_SOURCE_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
    ),
    _scenario(
        "locations.fixture",
        "locations",
        "L1",
        "fixture",
        {"url": "https://www.acme.com/locations"},
        {"records": "location records or explicit unsupported/blocked evidence"},
        ["extracts address when available", "blocked/unsupported state is explicit"],
        ["records[].record_type", *_SOURCE_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
        allows_blocked=True,
        required_blocked_fields=["url", "reason", "evidence_artifact"],
    ),
    _scenario(
        "website_quality.fixture",
        "website_quality",
        "L1",
        "fixture",
        {"url": "https://www.acme.com"},
        {"records": "website quality findings with evidence snippets"},
        ["produces actionable findings", "findings cite source evidence"],
        ["records[].record_type", "records[].finding", *_SOURCE_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
    ),
    _scenario(
        "browser_workbench.estee_lauder",
        "browser_workbench",
        "L3",
        "manual",
        {"url": "https://www.esteelauder.com/products/681/product-catalog/skin-care"},
        {"evidence": "full-size screenshot/DOM/text and provider status"},
        ["browser workbench is not a tiny placeholder", "captures visible evidence"],
        ["raw_response.current_url", "raw_response.provider", "raw_response.screenshot_path"],
        min_sources=1,
        min_artifacts=1,
        allows_blocked=True,
        required_blocked_fields=["url", "provider_attempts", "reason", "evidence_artifact"],
    ),
    _scenario(
        "cli.smoke",
        "cli",
        "L1",
        "cli",
        {"commands": ["scout scrape", "scout crawl", "scout map", "scout products", "scout run"]},
        {"outputs": "JSON output, artifacts, exit codes"},
        ["commands exit predictably", "artifact paths are readable"],
        ["raw_response.commands"],
        min_artifacts=1,
    ),
    _scenario(
        "api.contract",
        "api",
        "L1",
        "api",
        {"routes": "public and authenticated Scout routes"},
        {"responses": "status codes, auth behavior, schemas, artifact retrieval"},
        ["public routes are reachable", "protected routes enforce API key"],
        ["raw_response.routes"],
    ),
    _scenario(
        "persistence_sse.restart",
        "persistence_sse",
        "L1",
        "api",
        {"run": "long deterministic app run with restart/reopen"},
        {"events": "SSE replay, run history, artifact retrieval"},
        ["events replay after reconnect", "history can reopen artifacts"],
        ["raw_response.events", "raw_response.history"],
    ),
    _scenario(
        "algolia.preview",
        "algolia",
        "L1",
        "api",
        {"records": "sample product records"},
        {"preview": "ready/not-ready, missing fields, sample objectIDs"},
        ["validates record shape", "does not echo API keys"],
        ["raw_response.ready", "raw_response.sample_object_ids"],
    ),
    _scenario(
        "docker_distribution.smoke",
        "docker_distribution",
        "L1",
        "manual",
        {"image": "scout:validation"},
        {"checks": ["/health", "/app", "one scrape", "volume persistence"]},
        ["container starts", "health endpoint passes", "volume preserves artifacts"],
        ["raw_response.health", "raw_response.volume_path"],
    ),
    _scenario(
        "docs_validation.snippets",
        "docs_validation",
        "L1",
        "manual",
        {"docs": ["README.md", "docs/**/*.md"]},
        {"checks": "commands, route list, CLI help, stale claim detection"},
        ["examples are executable", "docs do not claim unsupported features"],
        ["raw_response.checked_files"],
    ),
)


def _live_product_scenarios() -> tuple[CertificationScenario, ...]:
    return tuple(
        _scenario(
            f"products.{slug}.live",
            "products",
            "L2",
            "live",
            {"url": url, "mode": "auto"},
            {"records": "product records or complete blocked/fallback evidence"},
            [
                "extracts listing products when visible",
                "product records are Algolia-previewable",
                "blocked pass requires provider attempts, reason, evidence, and report",
            ],
            [*_PRODUCT_FIELDS, *_SOURCE_FIELDS],
            min_records=1,
            min_sources=1,
            min_citations=1,
            min_artifacts=3,
            allows_blocked=True,
            required_blocked_fields=["url", "provider_attempts", "reason", "evidence_artifact"],
        )
        for slug, url in PRODUCT_LIVE_TARGETS
    )


def _live_user_browser_product_scenarios() -> tuple[CertificationScenario, ...]:
    return tuple(
        _scenario(
            f"products.{slug}.user_browser.live",
            "products",
            "L3",
            "user-browser",
            {"url": url, "mode": "user-browser"},
            {"records": "Algolia-ready product records from a user-visible browser capture"},
            [
                "captures visible browser DOM without re-fetching the hard-site URL",
                "extracts product records from captured hard-site evidence",
                "records contain source citations",
            ],
            [*_PRODUCT_FIELDS, *_SOURCE_FIELDS, *_CITATION_FIELDS],
            min_records=1,
            min_sources=1,
            min_citations=1,
            min_artifacts=3,
        )
        for slug, url in USER_BROWSER_PRODUCT_LIVE_TARGETS
    )


def _live_intelligence_scenarios() -> tuple[CertificationScenario, ...]:
    scenarios: list[CertificationScenario] = []
    for use_case, slug, url in INTELLIGENCE_LIVE_TARGETS:
        area = "news_blogs" if use_case == "news_blogs" else use_case
        scenarios.append(
            _scenario(
                f"{use_case}.{slug}.live",
                area,
                "L2",
                "live",
                {"url": url, "mode": "auto"},
                {"records": f"{use_case} records with source evidence and citations"},
                [
                    "records are content-specific to the target",
                    "sources and citations are present",
                    "artifacts are written",
                ],
                ["records[].record_type", *_SOURCE_FIELDS, *_CITATION_FIELDS],
                min_records=1,
                min_sources=1,
                min_citations=1,
                min_artifacts=3,
            )
        )
    return tuple(scenarios)


def _live_investor_scenarios() -> tuple[CertificationScenario, ...]:
    return tuple(
        _scenario(
            f"investor.{slug}.live",
            "investor",
            "L2",
            "live",
            {"url": url, "mode": "auto"},
            {"records": "investor page/assets/reports/filings/events where available"},
            ["finds investor evidence", "records cite public parent/company sources"],
            ["records[].record_type", "records[].asset_type", *_SOURCE_FIELDS, *_CITATION_FIELDS],
            min_records=1,
            min_sources=1,
            min_citations=1,
            min_artifacts=3,
        )
        for slug, url in INVESTOR_LIVE_TARGETS
    )


FEATURE_CERTIFICATION_MATRIX: tuple[CertificationScenario, ...] = (
    *_BASE_CERTIFICATION_MATRIX,
    *_live_product_scenarios(),
    *_live_user_browser_product_scenarios(),
    *_live_intelligence_scenarios(),
    *_live_investor_scenarios(),
    _scenario(
        "docs.algolia.live",
        "docs",
        "L2",
        "live",
        {"url": "https://www.algolia.com/doc/", "mode": "auto"},
        {"records": "documentation pages with sections and URLs"},
        ["extracts docs pages", "preserves source markdown"],
        ["records[].record_type", "records[].title", *_SOURCE_FIELDS, *_CITATION_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
        min_artifacts=3,
    ),
    _scenario(
        "docs.constructor.live",
        "docs",
        "L2",
        "live",
        {"url": "https://docs.constructor.com/", "mode": "auto"},
        {"records": "documentation pages with sections and URLs"},
        ["extracts docs pages", "preserves source markdown"],
        ["records[].record_type", "records[].title", *_SOURCE_FIELDS, *_CITATION_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
        min_artifacts=3,
    ),
    _scenario(
        "research.public.live",
        "research",
        "L2",
        "live",
        {"url": "https://en.wikipedia.org/wiki/Web_scraping", "mode": "auto"},
        {"records": "research records, summary, source list, citations"},
        ["summarizes sourced material", "keeps source list"],
        ["records[].record_type", "records[].summary", *_SOURCE_FIELDS, *_CITATION_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
        min_artifacts=3,
    ),
    _scenario(
        "social.algolia.live",
        "social",
        "L2",
        "live",
        {"url": "https://www.algolia.com/", "mode": "auto"},
        {"records": "social profile records with platform and URL"},
        ["finds public social links", "cites source page"],
        ["records[].record_type", "records[].platform", *_SOURCE_FIELDS, *_CITATION_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
        min_artifacts=3,
    ),
    _scenario(
        "locations.home_depot.live",
        "locations",
        "L2",
        "live",
        {"url": "https://www.homedepot.com/l/", "mode": "auto"},
        {"records": "location records or explicit blocked/unsupported evidence"},
        ["extracts location evidence when public", "blocked/unsupported state is explicit"],
        ["records[].record_type", *_SOURCE_FIELDS, *_CITATION_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
        min_artifacts=3,
        allows_blocked=True,
        required_blocked_fields=["url", "reason", "evidence_artifact"],
    ),
    _scenario(
        "website_quality.british_airways.live",
        "website_quality",
        "L2",
        "live",
        {"url": "https://www.britishairways.com/content/information/about-ba", "mode": "auto"},
        {"records": "website quality findings with evidence snippets"},
        ["produces actionable findings", "findings cite source evidence"],
        ["records[].record_type", "records[].finding", *_SOURCE_FIELDS, *_CITATION_FIELDS],
        min_records=1,
        min_sources=1,
        min_citations=1,
        min_artifacts=3,
        allows_blocked=True,
        required_blocked_fields=["url", "reason", "evidence_artifact"],
    ),
)


def _list_has_field(items: list[dict[str, Any]], field: str) -> bool:
    return any(item.get(field) not in (None, "", [], {}) for item in items)


def _raw_has_field(raw_response: dict[str, Any], dotted: str) -> bool:
    current: Any = raw_response
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return current not in (None, "", [], {})


def _has_required_actual_field(actual: CertificationActual, field: str) -> bool:
    if field.startswith("records[]."):
        return _list_has_field(actual.records, field.removeprefix("records[]."))
    if field.startswith("sources[]."):
        return _list_has_field(actual.sources, field.removeprefix("sources[]."))
    if field.startswith("citations[]."):
        return _list_has_field(actual.citations, field.removeprefix("citations[]."))
    if field.startswith("blocked_pages[]."):
        return _list_has_field(actual.blocked_pages, field.removeprefix("blocked_pages[]."))
    if field.startswith("raw_response."):
        return _raw_has_field(actual.raw_response, field.removeprefix("raw_response."))
    return False


def _blocked_evidence_failures(
    scenario: CertificationScenario, actual: CertificationActual
) -> list[str]:
    failures: list[str] = []
    if not scenario.allows_blocked:
        return ["scenario does not allow blocked pass"]
    if not actual.blocked_pages:
        failures.append("blocked run has no blocked_pages evidence")
    required_fields = scenario.required_blocked_fields or ["url", "reason", "evidence_artifact"]
    for field in required_fields:
        if not _list_has_field(actual.blocked_pages, field):
            failures.append(f"blocked evidence missing {field}")
    if not actual.sources:
        failures.append("blocked run has no source evidence")
    if not actual.artifacts:
        failures.append("blocked run has no artifacts")
    return failures


def certify_actual(
    scenario: CertificationScenario,
    actual: CertificationActual,
    *,
    notes: list[str] | None = None,
) -> CertificationResult:
    """Compare a scenario's acceptance thresholds to captured actual output."""

    failures: list[str] = []

    if actual.status in {"blocked", "blocked_with_evidence"}:
        failures.extend(_blocked_evidence_failures(scenario, actual))
        status = "pass" if not failures else "fail"
        blocked_notes = ["blocked evidence accepted"] if not failures else []
        return CertificationResult(
            scenario=scenario,
            status=status,
            actual=actual,
            failures=failures,
            notes=[*(notes or []), *blocked_notes],
        )

    if actual.status not in {"success", "pass"}:
        failures.append(f"unexpected status {actual.status}")
    if actual.record_count < scenario.min_records:
        failures.append(f"records below minimum {actual.record_count} < {scenario.min_records}")
    if actual.source_count < scenario.min_sources:
        failures.append(f"sources below minimum {actual.source_count} < {scenario.min_sources}")
    if actual.citation_count < scenario.min_citations:
        failures.append(
            f"citations below minimum {actual.citation_count} < {scenario.min_citations}"
        )
    if len(actual.artifacts) < scenario.min_artifacts:
        failures.append(
            f"artifacts below minimum {len(actual.artifacts)} < {scenario.min_artifacts}"
        )

    for field in scenario.required_actual_fields:
        if not _has_required_actual_field(actual, field):
            failures.append(f"missing actual field {field}")

    return CertificationResult(
        scenario=scenario,
        status="pass" if not failures else "fail",
        actual=actual,
        failures=failures,
        notes=notes or [],
    )


def _actual_summary(actual: CertificationActual) -> dict[str, Any]:
    return {
        "status": actual.status,
        "run_id": actual.run_id,
        "record_count": actual.record_count,
        "source_count": actual.source_count,
        "citation_count": actual.citation_count,
        "artifact_count": len(actual.artifacts),
        "blocked_count": actual.blocked_count,
        "artifacts": actual.artifacts,
        "screenshots": actual.screenshots or [],
    }


def _result_to_json(result: CertificationResult) -> dict[str, Any]:
    return {
        "scenario_id": result.scenario.scenario_id,
        "area": result.scenario.area,
        "tier": result.scenario.tier,
        "interface": result.scenario.interface,
        "input_data": result.scenario.input_data,
        "expected_output": result.scenario.expected_output,
        "acceptance_criteria": result.scenario.acceptance_criteria,
        "actual": _actual_summary(result.actual),
        "status": result.status,
        "failures": result.failures,
        "notes": result.notes,
        "pass_fail_reason": result.status if not result.failures else "; ".join(result.failures),
    }


def _write_report(results: list[CertificationResult], report_path: Path, timestamp: str) -> None:
    passed = sum(1 for result in results if result.status == "pass")
    blocked = sum(
        1
        for result in results
        if result.status == "pass" and result.actual.status in {"blocked", "blocked_with_evidence"}
    )
    failed = sum(1 for result in results if result.status == "fail")

    lines = [
        f"# Scout Feature Certification - {timestamp}",
        "",
        "## Summary",
        "",
        f"- Total scenarios: {len(results)}",
        f"- Passed: {passed}",
        f"- Passed via accepted blocked/fallback evidence: {blocked}",
        f"- Failed: {failed}",
        "",
        "## Certification Scope",
        "",
        (
            "Scout is certified as a Skill, CLI, and HTTP API utility/service. "
            "A full application UI is not part of this certification gate; any "
            "`/app` route is treated as a local service/status surface only."
        ),
        "",
        "## Expected vs Actual",
        "",
        "| Scenario | Area | Tier | Interface | Status | Expected | Actual | Failures |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for result in results:
        expected = json.dumps(result.scenario.expected_output, sort_keys=True)
        actual = json.dumps(_actual_summary(result.actual), sort_keys=True)
        failures = "; ".join(result.failures) if result.failures else result.status
        lines.append(
            "| "
            + " | ".join(
                [
                    result.scenario.scenario_id,
                    result.scenario.area,
                    result.scenario.tier,
                    result.scenario.interface,
                    result.status,
                    expected.replace("|", "\\|"),
                    actual.replace("|", "\\|"),
                    failures.replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- A scenario is not validated unless its actual output was captured.",
            "- Blocked scenarios count as pass only when the scenario explicitly allows blocked/fallback evidence and that evidence is complete.",
            "- Live and manual scenarios should be refreshed before private beta claims.",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def write_certification_outputs(
    results: list[CertificationResult],
    *,
    output_root: Path,
    report_path: Path,
    timestamp: str,
) -> CertificationOutputs:
    """Write machine-readable results, raw responses, screenshots dir, and report."""

    run_dir = output_root / timestamp.replace(":", "").replace("-", "").replace("T", "-").rstrip(
        "Z"
    )
    actual_responses_dir = run_dir / "actual-responses"
    screenshots_dir = run_dir / "screenshots"
    actual_responses_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    for result in results:
        response_path = actual_responses_dir / f"{result.scenario.scenario_id}.json"
        response_path.write_text(
            json.dumps(result.actual.raw_response, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    payload = {
        "timestamp": timestamp,
        "summary": {
            "total": len(results),
            "pass": sum(1 for result in results if result.status == "pass"),
            "blocked_evidence_pass": sum(
                1
                for result in results
                if result.status == "pass"
                and result.actual.status in {"blocked", "blocked_with_evidence"}
            ),
            "fail": sum(1 for result in results if result.status == "fail"),
        },
        "required_feature_areas": sorted(REQUIRED_FEATURE_AREAS),
        "results": [_result_to_json(result) for result in results],
    }
    feature_results_json = run_dir / "feature-results.json"
    feature_results_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    _write_report(results, report_path, timestamp)

    return CertificationOutputs(
        run_dir=run_dir,
        feature_results_json=feature_results_json,
        actual_responses_dir=actual_responses_dir,
        screenshots_dir=screenshots_dir,
        report_md=report_path,
    )


def certification_actual_from_dict(data: dict[str, Any]) -> CertificationActual:
    """Build a CertificationActual from a JSON-friendly evidence object."""

    return CertificationActual(
        status=str(data.get("status") or "not_run"),
        records=_list_of_dicts(data.get("records")),
        sources=_list_of_dicts(data.get("sources")),
        citations=_list_of_dicts(data.get("citations")),
        artifacts=[str(item) for item in _as_list(data.get("artifacts"))],
        blocked_pages=_list_of_dicts(data.get("blocked_pages")),
        raw_response=_dict_or_empty(data.get("raw_response")),
        run_id=str(data.get("run_id")) if data.get("run_id") else None,
        screenshots=[str(item) for item in _as_list(data.get("screenshots"))],
    )


def load_certification_evidence(path: Path) -> dict[str, CertificationActual]:
    """Load scenario actuals from a JSON evidence file or directory.

    Supported shapes:
    - {"scenarios": {"scenario.id": {actual...}}}
    - {"results": [{"scenario_id": "scenario.id", "actual": {actual...}}]}
    - {"scenario_id": "scenario.id", ...actual...}
    - a directory containing any mix of the single-scenario JSON file shape above
    """

    if path.is_dir():
        merged: dict[str, CertificationActual] = {}
        for child in sorted(path.glob("*.json")):
            merged.update(load_certification_evidence(child))
        return merged

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Certification evidence must be a JSON object: {path}")

    if isinstance(payload.get("scenarios"), dict):
        return {
            str(scenario_id): certification_actual_from_dict(_dict_or_empty(actual))
            for scenario_id, actual in payload["scenarios"].items()
        }

    if isinstance(payload.get("results"), list):
        evidence: dict[str, CertificationActual] = {}
        for item in payload["results"]:
            if not isinstance(item, dict):
                continue
            scenario_id = str(item.get("scenario_id") or "")
            actual = item.get("actual", item)
            if scenario_id:
                evidence[scenario_id] = certification_actual_from_dict(_dict_or_empty(actual))
        return evidence

    scenario_id = str(payload.get("scenario_id") or "")
    if scenario_id:
        actual_payload = payload.get("actual", payload)
        return {scenario_id: certification_actual_from_dict(_dict_or_empty(actual_payload))}

    raise ValueError(f"Certification evidence does not include scenario data: {path}")


def certification_results_from_evidence(
    evidence: dict[str, CertificationActual],
    *,
    include_missing: bool = True,
) -> list[CertificationResult]:
    """Certify matrix scenarios from captured actuals."""

    results: list[CertificationResult] = []
    for scenario in FEATURE_CERTIFICATION_MATRIX:
        actual = evidence.get(scenario.scenario_id)
        if actual is None:
            if not include_missing:
                continue
            actual = CertificationActual(
                status="not_run",
                records=[],
                sources=[],
                citations=[],
                artifacts=[],
                blocked_pages=[],
                raw_response={
                    "status": "not_run",
                    "message": "No captured evidence was provided for this scenario.",
                    "scenario_id": scenario.scenario_id,
                },
            )
            notes = ["No captured evidence was provided for this scenario."]
        else:
            notes = ["Certified from captured evidence."]
        results.append(certify_actual(scenario, actual, notes=notes))
    return results


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in _as_list(value) if isinstance(item, dict)]


def matrix_as_dicts() -> list[dict[str, Any]]:
    """Return the matrix in a JSON/YAML-friendly shape for docs and tooling."""

    return [asdict(scenario) for scenario in FEATURE_CERTIFICATION_MATRIX]
