#!/usr/bin/env python3
"""Validate Scout founder decision records before launch gates use them."""

from __future__ import annotations

import argparse
import re
import sys
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


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", nargs="*", type=Path)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--check-existing",
        action="store_true",
        help="Validate existing completed founder decision records under docs/product.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run founder decision record validation."""
    args = build_parser().parse_args(argv)
    records = list(args.records)
    if args.check_existing:
        records.extend(existing_decision_records(args.root))
    if not records:
        print("PASS: 0 founder decision records found.")
        return 0
    try:
        results = [validate_decision_record(path) for path in records]
    except FounderDecisionRecordError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    print("PASS: Scout founder decision record validation satisfied.")
    print(f"Validated {len(results)} founder decision records.")
    for result in results:
        print(f"{result.decision_id}: {result.status} ({result.path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
