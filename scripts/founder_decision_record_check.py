#!/usr/bin/env python3
"""Validate Scout founder decision records before launch gates use them."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scout.launch_decision_record import (
    FounderDecisionRecordError,
    existing_decision_records,
    format_validation_success,
    validate_decision_record,
    validate_decision_records,
)


__all__ = [
    "FounderDecisionRecordError",
    "existing_decision_records",
    "format_validation_success",
    "validate_decision_record",
    "validate_decision_records",
]


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
    try:
        results = validate_decision_records(
            list(args.records),
            root=args.root,
            check_existing=bool(args.check_existing),
        )
    except FounderDecisionRecordError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    print(format_validation_success(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
