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


def _citation_source_entry(citation: dict[str, Any]) -> dict[str, Any]:
    source_id = str(citation.get("source_id") or "")
    source_url = str(citation.get("source_url") or "")
    confidence = citation.get("confidence")
    return {
        "source_id": source_id,
        "source_url": source_url,
        "final_url": source_url,
        "provider": "citation",
        "fetched_at": "",
        "status_code": None,
        "blocked": False,
        "error": "",
        "confidence": confidence if isinstance(confidence, int | float) else None,
        "title": "Citation source",
        "content_sha256": "",
        "markdown_sha256": "",
        "html_sha256": "",
        "text_sha256": "",
        "dom_snapshot_sha256": "",
        "has_markdown": False,
        "has_html": False,
        "has_text": False,
        "has_dom_snapshot": False,
        "links_count": 0,
        "evidence": {
            "source_id": source_id,
            "provider": "citation",
            "source_url": source_url,
            "final_url": source_url,
            "fetched_at": "",
            "status_code": None,
            "blocked": False,
            "error": "",
            "confidence": confidence if isinstance(confidence, int | float) else None,
        },
    }


def _source_registry_entries(
    sources: list[FetchResult], records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    entries = [source_page_registry_entry(source) for source in sources]
    seen = {str(entry.get("source_id") or "") for entry in entries}

    for record in records:
        citations = record.get("citations")
        if not isinstance(citations, list):
            continue
        for citation in citations:
            if not isinstance(citation, dict):
                continue
            source_id = str(citation.get("source_id") or "")
            source_url = str(citation.get("source_url") or "")
            if not source_id or not source_url or source_id in seen:
                continue
            entries.append(_citation_source_entry(citation))
            seen.add(source_id)

    return entries


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
    source_count: int,
    blocked: list[dict[str, Any]],
) -> str:
    cited_records = sum(1 for record in records if _record_has_citations(record))
    total_citations = sum(_citation_count(record) for record in records)
    return (
        "\n\n## Source And Citation Coverage\n\n"
        f"- Source pages: {source_count}\n"
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
    source_entries = _source_registry_entries(sources, records)

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
    manifest.total_sources = len(source_entries)
    manifest.total_blocked = len(blocked)

    _write_json(output_dir / "manifest.json", manifest.model_dump(mode="json"))
    _write_json(output_dir / "records.json", records)
    (output_dir / "records.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)
    )
    _write_json(
        output_dir / "source_pages.json",
        source_entries,
    )
    _write_json(output_dir / "blocked_pages.json", blocked)
    _write_json(
        output_dir / "validation.json",
        [finding.model_dump(mode="json") for finding in all_findings],
    )
    (output_dir / "extraction_report.md").write_text(
        report.rstrip() + _coverage_summary(records, len(source_entries), blocked) + "\n"
    )

    return files
