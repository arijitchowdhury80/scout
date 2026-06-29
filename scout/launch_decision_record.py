"""Validation for completed Scout founder decision records."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


class FounderDecisionRecordError(RuntimeError):
    """Raised when a founder decision record is incomplete or malformed."""


@dataclass(frozen=True)
class FounderDecisionRecordResult:
    """Result of validating a founder decision record."""

    path: Path
    decision_id: str
    status: str


REQUIRED_FIELDS = [
    "Decision ID:",
    "Date:",
    "Decision owner:",
    "Recorded by:",
    "Status:",
    "Related blocker type:",
    "Related release gate:",
    "Source prompt / meeting / approval note:",
]

REQUIRED_SECTIONS = [
    "## Approved decision",
    "## Rejected alternatives",
    "## Scope and limits",
    "## Required Codex follow-up",
    "## Expiration or revisit trigger",
    "## Evidence links",
]

REQUIRED_FOLLOWUP_LABELS = [
    "Code/doc change:",
    "Verification command:",
    "Evidence file to update:",
    "Release checklist gate to update:",
]

ALLOWED_STATUSES = {"Approved", "Rejected", "Deferred", "Superseded"}


def validate_decision_record(path: Path) -> FounderDecisionRecordResult:
    """Validate a completed founder decision record."""
    if not path.exists():
        raise FounderDecisionRecordError(f"Decision record is missing: {path}")
    content = path.read_text(encoding="utf-8")
    _require_contains(content, "# Scout Founder Decision Record:")
    for field in REQUIRED_FIELDS:
        _require_contains(content, field)
    for section in REQUIRED_SECTIONS:
        _require_contains(content, section)
    for label in REQUIRED_FOLLOWUP_LABELS:
        _require_contains(content, label)

    decision_id = _field_value(content, "Decision ID")
    if not re.fullmatch(r"SCOUT-DEC-\d{8}-\d{2}", decision_id):
        raise FounderDecisionRecordError("Decision ID must match SCOUT-DEC-YYYYMMDD-NN.")

    status = _field_value(content, "Status")
    if status not in ALLOWED_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_STATUSES))
        raise FounderDecisionRecordError(f"Status must be one of: {allowed}.")

    if "Public launch allowed by this decision? Yes" in content:
        raise FounderDecisionRecordError(
            "Founder decision records must not approve public launch implicitly."
        )

    return FounderDecisionRecordResult(path=path, decision_id=decision_id, status=status)


def existing_decision_records(root: Path) -> list[Path]:
    """Return completed founder decision records under a Scout repo root."""
    records_dir = root / "docs" / "product"
    return sorted(records_dir.glob("founder-decision-record-SCOUT-DEC-*.md"))


def validate_decision_records(
    records: list[Path],
    *,
    root: Path,
    check_existing: bool,
) -> list[FounderDecisionRecordResult]:
    """Validate explicit records plus optional records discovered under root."""
    paths = list(records)
    if check_existing:
        paths.extend(existing_decision_records(root))
    return [validate_decision_record(path) for path in paths]


def format_validation_success(results: list[FounderDecisionRecordResult]) -> str:
    """Return the standard success message for decision record validation."""
    if not results:
        return "PASS: 0 founder decision records found."
    lines = [
        "PASS: Scout founder decision record validation satisfied.",
        f"Validated {len(results)} founder decision records.",
    ]
    for result in results:
        lines.append(f"{result.decision_id}: {result.status} ({result.path})")
    return "\n".join(lines)


def _require_contains(content: str, needle: str) -> None:
    if needle not in content:
        raise FounderDecisionRecordError(f"Missing required text: {needle}")


def _field_value(content: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}:\s*(.+)$", content, re.MULTILINE)
    if not match:
        raise FounderDecisionRecordError(f"Missing required field: {label}:")
    value = match.group(1).strip()
    if not value:
        raise FounderDecisionRecordError(f"Field must not be empty: {label}:")
    return value
