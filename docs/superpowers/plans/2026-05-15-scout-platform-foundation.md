# Scout Platform Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared Scout platform foundation needed for all required use cases: products, jobs, PRISM company intelligence, investor intelligence, research, website quality, docs, news, social normalization, and locations.

**Architecture:** Add a provider-agnostic content ingestion layer below existing modes. New domain modules will consume normalized `FetchResult` and `SourceEvidence` objects instead of Crawl4AI-specific responses. Existing scrape/crawl/map/product behavior should keep working while the new `scout run <use-case>` surface is added incrementally.

**Tech Stack:** Python 3.11+, Pydantic v2, Typer, pytest, pyright, ruff, existing Crawl4AI integration.

---

## Scope

This plan builds the platform foundation and the test harness. It does not fully implement every vertical use case. It creates the contracts, CLI structure, artifact format, and fixture workflow required to build every use case without one-off scraper logic.

## File Structure

Create:

- `scout/core/platform/__init__.py`: exports platform contracts.
- `scout/core/platform/types.py`: provider, evidence, manifest, validation, and artifact Pydantic models.
- `scout/core/platform/providers.py`: provider protocol and provider capability model.
- `scout/core/platform/artifacts.py`: generic artifact writer.
- `scout/core/platform/registry.py`: use-case registry.
- `scout/core/platform/content.py`: content-ingest helpers for saved HTML/markdown/DOM/provider JSON.
- `scout/core/platform/run.py`: high-level run dispatcher.
- `scout/core/use_cases/__init__.py`: use-case package.
- `scout/core/use_cases/base.py`: use-case protocol and base request/response types.
- `scout/core/use_cases/jobs.py`: initial schemas for job hunter records.
- `scout/core/use_cases/prism.py`: initial schemas for PRISM evidence records.
- `scout/core/use_cases/products_v2.py`: product records aligned to platform source evidence.
- `tests/unit/core/platform/test_types.py`
- `tests/unit/core/platform/test_artifacts.py`
- `tests/unit/core/platform/test_registry.py`
- `tests/unit/core/platform/test_content.py`
- `tests/unit/core/use_cases/test_jobs_contracts.py`
- `tests/unit/core/use_cases/test_prism_contracts.py`
- `tests/unit/core/use_cases/test_products_v2_contracts.py`

Modify:

- `scout/cli.py`: add `run`, `validate`, and `replay` command groups without removing existing commands.
- `scout/core/types.py`: only if shared aliases are needed; prefer keeping new platform models in `platform/types.py`.
- `docs/distribution.md`: document skill-host vs standalone provider differences.
- `README.md`: update high-level positioning from crawler-first to web-to-record engine.

## Task 1: Platform Type Contracts

**Files:**
- Create: `scout/core/platform/__init__.py`
- Create: `scout/core/platform/types.py`
- Test: `tests/unit/core/platform/test_types.py`

- [ ] **Step 1: Write failing contract tests**

Create `tests/unit/core/platform/test_types.py`:

```python
from scout.core.platform.types import (
    ArtifactFiles,
    FetchProviderKind,
    FetchResult,
    RunManifest,
    SourceEvidence,
    ValidationFinding,
    ValidationSeverity,
)


def test_source_evidence_requires_provider_and_url() -> None:
    evidence = SourceEvidence(
        provider=FetchProviderKind.SAVED,
        source_url="https://example.com/about",
        final_url="https://example.com/about",
        fetched_at="2026-05-15T12:00:00Z",
    )

    assert evidence.provider == FetchProviderKind.SAVED
    assert evidence.source_url == "https://example.com/about"
    assert evidence.blocked is False
    assert evidence.confidence == 1.0


def test_fetch_result_carries_multiple_content_shapes() -> None:
    result = FetchResult(
        evidence=SourceEvidence(
            provider=FetchProviderKind.HOST_WEBFETCH,
            source_url="https://example.com/product",
            final_url="https://example.com/product",
            fetched_at="2026-05-15T12:00:00Z",
        ),
        markdown="# Product",
        html="<h1>Product</h1>",
        links=["https://example.com/product/1"],
    )

    assert result.markdown == "# Product"
    assert result.html == "<h1>Product</h1>"
    assert result.links == ["https://example.com/product/1"]


def test_run_manifest_has_artifacts_and_counts() -> None:
    manifest = RunManifest(
        run_id="run_123",
        use_case="products",
        query="top categories",
        started_at="2026-05-15T12:00:00Z",
        finished_at="2026-05-15T12:01:00Z",
        providers_attempted=[FetchProviderKind.CRAWL4AI],
        output_dir="scout-runs/products",
        total_records=10,
        total_sources=5,
        total_blocked=1,
        artifacts=ArtifactFiles(
            manifest="manifest.json",
            records_json="records.json",
            records_jsonl="records.jsonl",
            source_pages_json="source_pages.json",
            blocked_pages_json="blocked_pages.json",
            validation_json="validation.json",
            report_md="extraction_report.md",
        ),
    )

    assert manifest.total_records == 10
    assert manifest.artifacts.records_jsonl == "records.jsonl"


def test_validation_finding_severity_enum() -> None:
    finding = ValidationFinding(
        severity=ValidationSeverity.WARNING,
        code="missing_optional_price",
        message="Price was not present on the source page.",
        record_id="product_1",
    )

    assert finding.severity == ValidationSeverity.WARNING
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest tests/unit/core/platform/test_types.py -v
```

Expected: fails because `scout.core.platform` does not exist.

- [ ] **Step 3: Implement platform types**

Create `scout/core/platform/types.py`:

```python
"""Provider-agnostic platform contracts for Scout."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class FetchProviderKind(str, Enum):
    WEBSEARCH = "websearch"
    HOST_WEBFETCH = "host_webfetch"
    CRAWL4AI = "crawl4ai"
    HOST_BROWSER = "host_browser"
    CDP = "cdp"
    SAVED = "saved"
    PDF = "pdf"
    ATS = "ats"
    SOCIAL = "social"
    API = "api"


class SourceEvidence(BaseModel):
    provider: FetchProviderKind
    source_url: str
    final_url: str = ""
    fetched_at: str
    status_code: int | None = None
    blocked: bool = False
    error: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class FetchResult(BaseModel):
    evidence: SourceEvidence
    markdown: str = ""
    html: str = ""
    dom_snapshot: str = ""
    text: str = ""
    links: list[str] = Field(default_factory=list)
    raw: dict = Field(default_factory=dict)


class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ValidationFinding(BaseModel):
    severity: ValidationSeverity
    code: str
    message: str
    record_id: str = ""
    source_url: str = ""


class ArtifactFiles(BaseModel):
    manifest: str = ""
    records_json: str = ""
    records_jsonl: str = ""
    source_pages_json: str = ""
    blocked_pages_json: str = ""
    validation_json: str = ""
    report_md: str = ""


class RunManifest(BaseModel):
    run_id: str
    use_case: str
    query: str = ""
    started_at: str
    finished_at: str = ""
    providers_attempted: list[FetchProviderKind] = Field(default_factory=list)
    output_dir: str
    total_records: int = 0
    total_sources: int = 0
    total_blocked: int = 0
    artifacts: ArtifactFiles = Field(default_factory=ArtifactFiles)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
```

Create `scout/core/platform/__init__.py`:

```python
"""Scout platform foundation contracts."""

from scout.core.platform.types import (
    ArtifactFiles,
    FetchProviderKind,
    FetchResult,
    RunManifest,
    SourceEvidence,
    ValidationFinding,
    ValidationSeverity,
)

__all__ = [
    "ArtifactFiles",
    "FetchProviderKind",
    "FetchResult",
    "RunManifest",
    "SourceEvidence",
    "ValidationFinding",
    "ValidationSeverity",
]
```

- [ ] **Step 4: Run contract tests**

Run:

```bash
python3 -m pytest tests/unit/core/platform/test_types.py -v
```

Expected: all tests pass.

## Task 2: Provider Protocol And Capabilities

**Files:**
- Create: `scout/core/platform/providers.py`
- Test: `tests/unit/core/platform/test_providers.py`

- [ ] **Step 1: Write failing provider tests**

Create `tests/unit/core/platform/test_providers.py`:

```python
from scout.core.platform.providers import ProviderCapability, ProviderRuntime
from scout.core.platform.types import FetchProviderKind


def test_provider_capability_marks_skill_only_provider() -> None:
    capability = ProviderCapability(
        kind=FetchProviderKind.HOST_WEBFETCH,
        runtime=ProviderRuntime.SKILL_HOST,
        supports_discovery=False,
        supports_fetch=True,
        supports_browser_session=False,
        supports_documents=False,
    )

    assert capability.kind == FetchProviderKind.HOST_WEBFETCH
    assert capability.runtime == ProviderRuntime.SKILL_HOST
    assert capability.supports_fetch is True


def test_provider_capability_marks_cli_provider() -> None:
    capability = ProviderCapability(
        kind=FetchProviderKind.CRAWL4AI,
        runtime=ProviderRuntime.STANDALONE,
        supports_discovery=True,
        supports_fetch=True,
        supports_browser_session=False,
        supports_documents=False,
    )

    assert capability.supports_discovery is True
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/unit/core/platform/test_providers.py -v
```

Expected: fails because provider models do not exist.

- [ ] **Step 3: Implement provider capability models**

Create `scout/core/platform/providers.py`:

```python
"""Provider contracts and capability metadata."""

from __future__ import annotations

from enum import Enum
from typing import Protocol

from pydantic import BaseModel

from scout.core.platform.types import FetchProviderKind, FetchResult


class ProviderRuntime(str, Enum):
    SKILL_HOST = "skill_host"
    STANDALONE = "standalone"
    BOTH = "both"


class ProviderCapability(BaseModel):
    kind: FetchProviderKind
    runtime: ProviderRuntime
    supports_discovery: bool = False
    supports_fetch: bool = True
    supports_browser_session: bool = False
    supports_documents: bool = False


class FetchProvider(Protocol):
    kind: FetchProviderKind

    async def fetch(self, url: str) -> FetchResult:
        """Fetch one URL and return normalized content."""
        ...
```

- [ ] **Step 4: Run provider tests**

Run:

```bash
python3 -m pytest tests/unit/core/platform/test_providers.py -v
```

Expected: pass.

## Task 3: Generic Artifact Writer

**Files:**
- Create: `scout/core/platform/artifacts.py`
- Test: `tests/unit/core/platform/test_artifacts.py`

- [ ] **Step 1: Write failing artifact tests**

Create `tests/unit/core/platform/test_artifacts.py`:

```python
import json

from scout.core.platform.artifacts import write_run_artifacts
from scout.core.platform.types import (
    FetchProviderKind,
    FetchResult,
    RunManifest,
    SourceEvidence,
    ValidationFinding,
    ValidationSeverity,
)


def test_write_run_artifacts_creates_standard_files(tmp_path) -> None:
    manifest = RunManifest(
        run_id="run_123",
        use_case="generic",
        query="about page",
        started_at="2026-05-15T12:00:00Z",
        output_dir=str(tmp_path),
    )
    source = FetchResult(
        evidence=SourceEvidence(
            provider=FetchProviderKind.SAVED,
            source_url="https://example.com",
            final_url="https://example.com",
            fetched_at="2026-05-15T12:00:00Z",
        ),
        markdown="# Example",
    )
    records = [{"objectID": "example_1", "type": "generic_page_fact"}]
    findings = [
        ValidationFinding(
            severity=ValidationSeverity.INFO,
            code="ok",
            message="Record is valid.",
            record_id="example_1",
        )
    ]

    files = write_run_artifacts(
        output_dir=tmp_path,
        manifest=manifest,
        records=records,
        sources=[source],
        blocked=[],
        findings=findings,
        report="Run completed.",
    )

    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "records.json").exists()
    assert (tmp_path / "records.jsonl").exists()
    assert (tmp_path / "source_pages.json").exists()
    assert (tmp_path / "blocked_pages.json").exists()
    assert (tmp_path / "validation.json").exists()
    assert (tmp_path / "extraction_report.md").exists()
    assert files.records_jsonl.endswith("records.jsonl")

    jsonl_lines = (tmp_path / "records.jsonl").read_text().splitlines()
    assert json.loads(jsonl_lines[0])["objectID"] == "example_1"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/unit/core/platform/test_artifacts.py -v
```

Expected: fails because `write_run_artifacts` does not exist.

- [ ] **Step 3: Implement artifact writer**

Create `scout/core/platform/artifacts.py`:

```python
"""Generic artifact writer for all Scout high-level runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scout.core.platform.types import (
    ArtifactFiles,
    FetchResult,
    RunManifest,
    ValidationFinding,
)


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def write_run_artifacts(
    output_dir: Path,
    manifest: RunManifest,
    records: list[dict[str, Any]],
    sources: list[FetchResult],
    blocked: list[dict[str, Any]],
    findings: list[ValidationFinding],
    report: str,
) -> ArtifactFiles:
    output_dir.mkdir(parents=True, exist_ok=True)

    files = ArtifactFiles(
        manifest=str(output_dir / "manifest.json"),
        records_json=str(output_dir / "records.json"),
        records_jsonl=str(output_dir / "records.jsonl"),
        source_pages_json=str(output_dir / "source_pages.json"),
        blocked_pages_json=str(output_dir / "blocked_pages.json"),
        validation_json=str(output_dir / "validation.json"),
        report_md=str(output_dir / "extraction_report.md"),
    )

    manifest.artifacts = files
    manifest.total_records = len(records)
    manifest.total_sources = len(sources)
    manifest.total_blocked = len(blocked)

    _write_json(output_dir / "manifest.json", manifest.model_dump(mode="json"))
    _write_json(output_dir / "records.json", records)
    (output_dir / "records.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)
    )
    _write_json(
        output_dir / "source_pages.json",
        [source.model_dump(mode="json") for source in sources],
    )
    _write_json(output_dir / "blocked_pages.json", blocked)
    _write_json(
        output_dir / "validation.json",
        [finding.model_dump(mode="json") for finding in findings],
    )
    (output_dir / "extraction_report.md").write_text(report + "\n")

    return files
```

- [ ] **Step 4: Run artifact tests**

Run:

```bash
python3 -m pytest tests/unit/core/platform/test_artifacts.py -v
```

Expected: pass.

## Task 4: Use-Case Contract Models

**Files:**
- Create: `scout/core/use_cases/__init__.py`
- Create: `scout/core/use_cases/jobs.py`
- Create: `scout/core/use_cases/prism.py`
- Create: `scout/core/use_cases/products_v2.py`
- Test: `tests/unit/core/use_cases/test_jobs_contracts.py`
- Test: `tests/unit/core/use_cases/test_prism_contracts.py`
- Test: `tests/unit/core/use_cases/test_products_v2_contracts.py`

- [ ] **Step 1: Write failing contract tests for jobs**

Create `tests/unit/core/use_cases/test_jobs_contracts.py`:

```python
from scout.core.use_cases.jobs import JobPostingRecord, JobSearchProfile, TargetCompanyRecord


def test_job_search_profile_contract() -> None:
    profile = JobSearchProfile(
        desired_titles=["AI Product Marketing Manager"],
        salary_min_usd=160000,
        locations=["Remote", "New York"],
        role_keywords=["AI", "developer platform"],
    )

    assert profile.salary_min_usd == 160000
    assert "Remote" in profile.locations


def test_target_company_record_contract() -> None:
    company = TargetCompanyRecord(
        objectID="company_adobe",
        company="Adobe",
        website="https://www.adobe.com",
        careers_url="https://careers.adobe.com/us/en/",
        reason_matched="Company hires for AI product marketing and developer platform roles.",
        confidence=0.9,
    )

    assert company.company == "Adobe"
    assert company.confidence == 0.9


def test_job_posting_record_contract() -> None:
    job = JobPostingRecord(
        objectID="job_adobe_123",
        company="Adobe",
        title="Senior Product Marketing Manager, AI",
        url="https://careers.adobe.com/us/en/job/123",
        location="New York",
        matched_terms=["AI", "Product Marketing"],
    )

    assert job.company == "Adobe"
    assert job.matched_terms == ["AI", "Product Marketing"]
```

- [ ] **Step 2: Write failing contract tests for PRISM**

Create `tests/unit/core/use_cases/test_prism_contracts.py`:

```python
from scout.core.use_cases.prism import CompanyRecord, CompanySocialRecord, ExecutiveRecord


def test_company_record_contract() -> None:
    company = CompanyRecord(
        objectID="company_nike",
        name="Nike",
        website="https://www.nike.com/",
        linkedin_url="https://www.linkedin.com/company/nike/",
    )

    assert company.name == "Nike"
    assert company.linkedin_url.endswith("/nike/")


def test_company_social_record_contract() -> None:
    social = CompanySocialRecord(
        objectID="social_nike_x",
        company="Nike",
        platform="x",
        url="https://x.com/Nike",
    )

    assert social.platform == "x"


def test_executive_record_contract() -> None:
    executive = ExecutiveRecord(
        objectID="exec_nike_example",
        company="Nike",
        name="Example Executive",
        title="Chief Example Officer",
        linkedin_url="https://www.linkedin.com/in/example/",
    )

    assert executive.title == "Chief Example Officer"
```

- [ ] **Step 3: Write failing contract tests for products v2**

Create `tests/unit/core/use_cases/test_products_v2_contracts.py`:

```python
from scout.core.use_cases.products_v2 import ProductRecord, ProductVariantRecord


def test_product_record_contract() -> None:
    product = ProductRecord(
        objectID="esteelauder_643_141225",
        brand="Estee Lauder",
        name="Double Wear",
        subtitle="Stay-in-Place Longwear Matte Foundation",
        url="https://www.esteelauder.com/product/643/141225/product-catalog/makeup/face/foundation/double-wear/stay-in-place-longwear-matte-foundation",
        category="Makeup",
        price=52.0,
        currency="USD",
        colors=["3N1 Ivory Beige"],
        variants=[
            ProductVariantRecord(name="3N1 Ivory Beige", color="3N1 Ivory Beige", size="1.0 oz.")
        ],
    )

    assert product.price == 52.0
    assert product.variants[0].size == "1.0 oz."
```

- [ ] **Step 4: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/unit/core/use_cases/ -v
```

Expected: fails because use-case models do not exist.

- [ ] **Step 5: Implement minimal use-case models**

Create `scout/core/use_cases/__init__.py`:

```python
"""Scout high-level use-case contracts."""
```

Create `scout/core/use_cases/jobs.py`:

```python
"""Job hunter and career monitoring contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class JobSearchProfile(BaseModel):
    desired_titles: list[str] = Field(default_factory=list)
    role_keywords: list[str] = Field(default_factory=list)
    salary_min_usd: int | None = None
    salary_max_usd: int | None = None
    locations: list[str] = Field(default_factory=list)
    seniority: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    excluded_terms: list[str] = Field(default_factory=list)


class TargetCompanyRecord(BaseModel):
    schema_version: str = "target_company.v1"
    objectID: str
    company: str
    website: str = ""
    careers_url: str = ""
    linkedin_url: str = ""
    industry: str = ""
    reason_matched: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class JobPostingRecord(BaseModel):
    schema_version: str = "job_posting.v1"
    objectID: str
    company: str
    title: str
    url: str
    location: str = ""
    remote_type: str = ""
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "USD"
    department: str = ""
    description: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    apply_url: str = ""
    ats_platform: str = ""
    posted_at: str = ""
    first_seen_at: str = ""
    last_seen_at: str = ""
    matched_terms: list[str] = Field(default_factory=list)
```

Create `scout/core/use_cases/prism.py`:

```python
"""PRISM company intelligence contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CompanyRecord(BaseModel):
    schema_version: str = "company.v1"
    objectID: str
    name: str
    website: str = ""
    linkedin_url: str = ""
    description: str = ""
    industry: str = ""
    source_urls: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class CompanySocialRecord(BaseModel):
    schema_version: str = "company_social.v1"
    objectID: str
    company: str
    platform: str
    url: str
    handle: str = ""
    provider: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ExecutiveRecord(BaseModel):
    schema_version: str = "executive.v1"
    objectID: str
    company: str
    name: str
    title: str = ""
    bio: str = ""
    linkedin_url: str = ""
    profile_url: str = ""
    source_url: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
```

Create `scout/core/use_cases/products_v2.py`:

```python
"""Product catalog contracts for provider-agnostic extraction."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProductVariantRecord(BaseModel):
    sku: str = ""
    name: str = ""
    color: str = ""
    size: str = ""
    price: float | None = None
    currency: str = "USD"
    in_stock: bool | None = None


class ProductRecord(BaseModel):
    schema_version: str = "product.v2"
    objectID: str
    brand: str = ""
    name: str
    subtitle: str = ""
    url: str
    category: str = ""
    subcategory: str = ""
    product_type: str = ""
    price: float | None = None
    sale_price: float | None = None
    currency: str = "USD"
    rating: float | None = None
    review_count: int | None = None
    colors: list[str] = Field(default_factory=list)
    sizes: list[str] = Field(default_factory=list)
    variants: list[ProductVariantRecord] = Field(default_factory=list)
    badges: list[str] = Field(default_factory=list)
    description: str = ""
    benefits: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
```

- [ ] **Step 6: Run use-case contract tests**

Run:

```bash
python3 -m pytest tests/unit/core/use_cases/ -v
```

Expected: pass.

## Task 5: Content Ingest Helpers

**Files:**
- Create: `scout/core/platform/content.py`
- Test: `tests/unit/core/platform/test_content.py`

- [ ] **Step 1: Write failing content helper tests**

Create `tests/unit/core/platform/test_content.py`:

```python
from scout.core.platform.content import fetch_result_from_markdown
from scout.core.platform.types import FetchProviderKind


def test_fetch_result_from_markdown() -> None:
    result = fetch_result_from_markdown(
        markdown="# About Example",
        source_url="https://example.com/about",
        provider=FetchProviderKind.SAVED,
        fetched_at="2026-05-15T12:00:00Z",
    )

    assert result.markdown == "# About Example"
    assert result.evidence.source_url == "https://example.com/about"
    assert result.evidence.provider == FetchProviderKind.SAVED
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python3 -m pytest tests/unit/core/platform/test_content.py -v
```

Expected: fails because helper does not exist.

- [ ] **Step 3: Implement content helper**

Create `scout/core/platform/content.py`:

```python
"""Helpers for turning host/saved content into normalized FetchResult objects."""

from __future__ import annotations

from scout.core.platform.types import FetchProviderKind, FetchResult, SourceEvidence


def fetch_result_from_markdown(
    markdown: str,
    source_url: str,
    provider: FetchProviderKind,
    fetched_at: str,
    final_url: str = "",
) -> FetchResult:
    return FetchResult(
        evidence=SourceEvidence(
            provider=provider,
            source_url=source_url,
            final_url=final_url or source_url,
            fetched_at=fetched_at,
        ),
        markdown=markdown,
        text=markdown,
    )
```

- [ ] **Step 4: Run content tests**

Run:

```bash
python3 -m pytest tests/unit/core/platform/test_content.py -v
```

Expected: pass.

## Task 6: CLI Skeleton For `scout run`

**Files:**
- Modify: `scout/cli.py`
- Test: `tests/unit/cli/test_run_commands.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/unit/cli/test_run_commands.py`:

```python
from typer.testing import CliRunner

from scout.cli import app


def test_run_command_lists_supported_use_cases() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["run", "--help"])

    assert result.exit_code == 0
    assert "products" in result.output
    assert "jobs" in result.output
    assert "prism" in result.output
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python3 -m pytest tests/unit/cli/test_run_commands.py -v
```

Expected: fails because `run` command does not exist or test package path does not exist.

- [ ] **Step 3: Add CLI test package**

Create `tests/unit/cli/__init__.py`:

```python
"""CLI unit tests."""
```

- [ ] **Step 4: Implement `run` help skeleton**

Modify `scout/cli.py` by adding a Typer sub-app near the existing `app = typer.Typer(...)` definition:

```python
run_app = typer.Typer(help="Run high-level Scout use cases: products, jobs, prism, investor, research, website-quality, docs, news, social, locations.")
app.add_typer(run_app, name="run")
```

Add placeholder commands that report unsupported implementation clearly:

```python
@run_app.command("products")
def run_products() -> None:
    """Run product catalog extraction."""
    typer.echo("products run mode is planned; use `scout products` until platform run mode is implemented.")


@run_app.command("jobs")
def run_jobs() -> None:
    """Run job hunter extraction."""
    typer.echo("jobs run mode is planned.")


@run_app.command("prism")
def run_prism() -> None:
    """Run PRISM company intelligence extraction."""
    typer.echo("prism run mode is planned.")
```

- [ ] **Step 5: Run CLI test**

Run:

```bash
python3 -m pytest tests/unit/cli/test_run_commands.py -v
```

Expected: pass.

## Task 7: Documentation Updates

**Files:**
- Modify: `README.md`
- Modify: `docs/distribution.md`
- Test: manual grep validation

- [ ] **Step 1: Update README positioning**

Modify README to include:

```markdown
Scout is a provider-agnostic web-to-record intelligence engine. Crawl4AI is the default standalone acquisition provider, but Scout can also process content supplied by host tools, browser sessions, saved HTML/DOM, PDF parsers, ATS adapters, and future provider integrations.
```

- [ ] **Step 2: Update distribution docs**

Add a section to `docs/distribution.md`:

```markdown
## Runtime Capability Matrix

| Capability | Standalone CLI | Claude/Codex Skill |
|---|---:|---:|
| Crawl4AI fetch/crawl | Yes | Yes |
| WebSearch/WebFetch host provider | No | Yes, when host exposes it |
| In-app browser/session | No | Yes, when host exposes it |
| CDP/profile browser attach | Yes | Optional |
| Saved HTML/DOM replay | Yes | Yes |
| PDF/document parsing | Yes with optional extra | Yes with optional extra |
```

- [ ] **Step 3: Validate docs mention provider distinction**

Run:

```bash
rg -n "provider-agnostic|WebSearch/WebFetch|Runtime Capability Matrix" README.md docs/distribution.md
```

Expected: matching lines in both files.

## Task 8: Foundation Verification

**Files:**
- No new files

- [ ] **Step 1: Run targeted unit tests**

Run:

```bash
python3 -m pytest tests/unit/core/platform tests/unit/core/use_cases tests/unit/cli -v
```

Expected: all targeted tests pass.

- [ ] **Step 2: Run full unit tests**

Run:

```bash
python3 -m pytest tests/unit/ -v
```

Expected: all unit tests pass.

- [ ] **Step 3: Run type and lint gates**

Run:

```bash
python3 -m pyright scout/
ruff check scout tests
ruff format --check scout tests
```

Expected: pyright reports 0 errors, ruff passes.

## Follow-On Plans

After this foundation passes, create separate implementation plans for:

1. Product catalog extraction v2 with saved/WebFetch/Crawl4AI content providers.
2. Job hunter intake, company discovery, ATS detection, and daily delta records.
3. PRISM company intelligence source discovery and evidence bundle.
4. Investor/PDF parsing.
5. Generic research and website quality rubric.
6. Docs/news/social/location modules.

Each follow-on plan must include fixtures, expected records, live smoke tests, and artifact assertions.

