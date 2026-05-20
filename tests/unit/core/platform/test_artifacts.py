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


def test_write_run_artifacts_updates_manifest_counts(tmp_path) -> None:
    manifest = RunManifest(
        run_id="run_456",
        use_case="jobs",
        started_at="2026-05-15T12:00:00Z",
        output_dir=str(tmp_path),
    )
    source = FetchResult(
        evidence=SourceEvidence(
            provider=FetchProviderKind.SAVED,
            source_url="https://example.com/jobs",
            final_url="https://example.com/jobs",
            fetched_at="2026-05-15T12:00:00Z",
        )
    )

    write_run_artifacts(
        output_dir=tmp_path,
        manifest=manifest,
        records=[{"objectID": "job_1"}, {"objectID": "job_2"}],
        sources=[source],
        blocked=[{"url": "https://example.com/blocked", "reason": "blocked"}],
        findings=[],
        report="Done.",
    )

    saved_manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert saved_manifest["total_records"] == 2
    assert saved_manifest["total_sources"] == 1
    assert saved_manifest["total_blocked"] == 1


def test_source_pages_json_is_citation_registry_with_hashes(tmp_path) -> None:
    manifest = RunManifest(
        run_id="run_sources",
        use_case="company",
        started_at="2026-05-15T12:00:00Z",
        output_dir=str(tmp_path),
    )
    source = FetchResult(
        evidence=SourceEvidence(
            provider=FetchProviderKind.SAVED,
            source_url="https://example.com/about",
            final_url="https://example.com/about",
            fetched_at="2026-05-15T12:00:00Z",
        ),
        markdown="# About Example",
        html="<main><h1>About Example</h1></main>",
        text="About Example",
        raw={"title": "About Example"},
    )

    write_run_artifacts(
        output_dir=tmp_path,
        manifest=manifest,
        records=[
            {
                "objectID": "company_example",
                "citations": [
                    {
                        "source_id": source.evidence.source_id,
                        "source_url": source.evidence.source_url,
                        "field": "description",
                        "claim": "About Example",
                        "snippet": "About Example",
                        "confidence": 0.9,
                    }
                ],
            }
        ],
        sources=[source],
        blocked=[],
        findings=[],
        report="Done.",
    )

    source_pages = json.loads((tmp_path / "source_pages.json").read_text())
    assert source_pages[0]["source_id"] == source.evidence.source_id
    assert source_pages[0]["provider"] == "saved"
    assert source_pages[0]["has_markdown"] is True
    assert source_pages[0]["has_html"] is True
    assert source_pages[0]["content_sha256"]
    assert source_pages[0]["title"] == "About Example"


def test_validation_warns_when_record_has_no_citations(tmp_path) -> None:
    manifest = RunManifest(
        run_id="run_missing_citations",
        use_case="company",
        started_at="2026-05-15T12:00:00Z",
        output_dir=str(tmp_path),
    )

    write_run_artifacts(
        output_dir=tmp_path,
        manifest=manifest,
        records=[{"objectID": "company_example"}],
        sources=[],
        blocked=[],
        findings=[],
        report="Done.",
    )

    validation = json.loads((tmp_path / "validation.json").read_text())
    assert validation[0]["code"] == "missing_citations"
    assert validation[0]["record_id"] == "company_example"


def test_report_includes_source_and_citation_coverage(tmp_path) -> None:
    manifest = RunManifest(
        run_id="run_report",
        use_case="company",
        started_at="2026-05-15T12:00:00Z",
        output_dir=str(tmp_path),
    )
    source = FetchResult(
        evidence=SourceEvidence(
            provider=FetchProviderKind.SAVED,
            source_url="https://example.com/about",
            final_url="https://example.com/about",
            fetched_at="2026-05-15T12:00:00Z",
        ),
        text="About Example",
    )

    write_run_artifacts(
        output_dir=tmp_path,
        manifest=manifest,
        records=[
            {
                "objectID": "company_example",
                "citations": [
                    {
                        "source_id": source.evidence.source_id,
                        "source_url": source.evidence.source_url,
                        "field": "description",
                        "claim": "About Example",
                    }
                ],
            }
        ],
        sources=[source],
        blocked=[],
        findings=[],
        report="Done.",
    )

    report = (tmp_path / "extraction_report.md").read_text()
    assert "## Source And Citation Coverage" in report
    assert "Records with citations: 1/1" in report
    assert "Source pages: 1" in report
