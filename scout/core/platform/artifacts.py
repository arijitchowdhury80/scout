"""Generic artifact writer for all Scout high-level runs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from scout.core.platform.types import (
    ArtifactFiles,
    FetchResult,
    RunManifest,
    ValidationFinding,
    ValidationSeverity,
)


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _sha256(value: str) -> str:
    if not value:
        return ""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _content_hash(source: FetchResult) -> str:
    content = "\n".join(
        part for part in [source.markdown, source.html, source.dom_snapshot, source.text] if part
    )
    return _sha256(content)


def _title(source: FetchResult) -> str:
    title = source.raw.get("title", "")
    return title if isinstance(title, str) else ""


def source_page_registry_entry(source: FetchResult) -> dict[str, Any]:
    evidence = source.evidence
    return {
        "source_id": evidence.source_id,
        "source_url": evidence.source_url,
        "final_url": evidence.final_url,
        "provider": evidence.provider.value,
        "fetched_at": evidence.fetched_at,
        "status_code": evidence.status_code,
        "blocked": evidence.blocked,
        "error": evidence.error,
        "confidence": evidence.confidence,
        "title": _title(source),
        "content_sha256": _content_hash(source),
        "markdown_sha256": _sha256(source.markdown),
        "html_sha256": _sha256(source.html),
        "text_sha256": _sha256(source.text),
        "dom_snapshot_sha256": _sha256(source.dom_snapshot),
        "has_markdown": bool(source.markdown),
        "has_html": bool(source.html),
        "has_text": bool(source.text),
        "has_dom_snapshot": bool(source.dom_snapshot),
        "links_count": len(source.links),
        "evidence": evidence.model_dump(mode="json"),
    }


def _record_has_citations(record: dict[str, Any]) -> bool:
    citations = record.get("citations")
    return isinstance(citations, list) and len(citations) > 0


def _citation_findings(records: list[dict[str, Any]]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    for record in records:
        if _record_has_citations(record):
            continue
        object_id = record.get("objectID", "")
        findings.append(
            ValidationFinding(
                severity=ValidationSeverity.WARNING,
                code="missing_citations",
                message="Record has no structured citations.",
                record_id=str(object_id) if object_id else "",
            )
        )
    return findings


def _citation_count(record: dict[str, Any]) -> int:
    citations = record.get("citations")
    return len(citations) if isinstance(citations, list) else 0


def _coverage_summary(
    records: list[dict[str, Any]],
    sources: list[FetchResult],
    blocked: list[dict[str, Any]],
) -> str:
    cited_records = sum(1 for record in records if _record_has_citations(record))
    total_citations = sum(_citation_count(record) for record in records)
    return (
        "\n\n## Source And Citation Coverage\n\n"
        f"- Source pages: {len(sources)}\n"
        f"- Blocked pages: {len(blocked)}\n"
        f"- Records with citations: {cited_records}/{len(records)}\n"
        f"- Total citations: {total_citations}\n"
    )


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
    all_findings = [*findings, *_citation_findings(records)]

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
        [source_page_registry_entry(source) for source in sources],
    )
    _write_json(output_dir / "blocked_pages.json", blocked)
    _write_json(
        output_dir / "validation.json",
        [finding.model_dump(mode="json") for finding in all_findings],
    )
    (output_dir / "extraction_report.md").write_text(
        report.rstrip() + _coverage_summary(records, sources, blocked) + "\n"
    )

    return files
