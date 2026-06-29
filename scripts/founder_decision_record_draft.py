#!/usr/bin/env python3
"""Generate editable Scout founder decision record drafts from blocker IDs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scout.launch_decision_draft import (
    FounderDecisionRecordDraftError,
    build_decision_record_draft,
    default_decision_date,
    write_decision_record_draft,
    write_decision_record_drafts,
)
from scout.launch_readiness import default_root


__all__ = [
    "FounderDecisionRecordDraftError",
    "build_decision_record_draft",
    "default_decision_date",
    "write_decision_record_draft",
    "write_decision_record_drafts",
]


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--output-root", type=Path, default=Path("."))
    parser.add_argument("--blocker-id", required=True)
    parser.add_argument("--decision-id", required=True)
    parser.add_argument("--date", default=default_decision_date())
    parser.add_argument("--recorded-by", default="Codex")
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the draft instead of writing docs/product/founder-decision-drafts/.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run founder decision record draft generation."""
    args = build_parser().parse_args(argv)
    try:
        if args.stdout:
            print(
                build_decision_record_draft(
                    root=args.root.resolve(),
                    blocker_id=args.blocker_id,
                    decision_id=args.decision_id,
                    date=args.date,
                    recorded_by=args.recorded_by,
                )
            )
            return 0
        output_path = write_decision_record_draft(
            root=args.root.resolve(),
            output_root=args.output_root.resolve(),
            blocker_id=args.blocker_id,
            decision_id=args.decision_id,
            date=args.date,
            recorded_by=args.recorded_by,
        )
    except FounderDecisionRecordDraftError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote founder decision draft: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
