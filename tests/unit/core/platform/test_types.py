from scout.core.platform.types import (
    ArtifactFiles,
    Citation,
    FetchProviderKind,
    FetchResult,
    RunRequest,
    RunResponse,
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
    assert evidence.source_id.startswith("src_")


def test_source_id_is_deterministic_for_same_provider_and_url() -> None:
    first = SourceEvidence(
        provider=FetchProviderKind.SAVED,
        source_url="https://example.com/about",
        final_url="https://example.com/about",
        fetched_at="2026-05-15T12:00:00Z",
    )
    second = SourceEvidence(
        provider=FetchProviderKind.SAVED,
        source_url="https://example.com/about",
        final_url="https://example.com/about",
        fetched_at="2026-05-16T12:00:00Z",
    )

    assert first.source_id == second.source_id


def test_citation_contract_links_claim_to_source() -> None:
    citation = Citation(
        source_id="src_abc123",
        source_url="https://example.com/about",
        field="description",
        claim="Example is a commerce company.",
        snippet="Example is a commerce company founded in 2020.",
        selector="main",
        confidence=0.82,
    )

    assert citation.source_id == "src_abc123"
    assert citation.field == "description"
    assert citation.confidence == 0.82


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


def test_run_request_and_response_contract() -> None:
    request = RunRequest(
        use_case="jobs",
        query="AI product marketing roles",
        output_dir="scout-runs/jobs",
        targets=["Adobe", "Salesforce"],
        providers=[FetchProviderKind.CRAWL4AI],
    )
    response = RunResponse(
        success=True,
        use_case="jobs",
        output_dir="scout-runs/jobs",
        manifest=RunManifest(
            run_id="run_789",
            use_case="jobs",
            query=request.query,
            started_at="2026-05-16T12:00:00Z",
            output_dir=request.output_dir,
        ),
    )

    assert request.targets == ["Adobe", "Salesforce"]
    assert response.success is True
    assert response.manifest.use_case == "jobs"
