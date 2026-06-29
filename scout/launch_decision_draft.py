"""Founder decision draft generation for Scout launch gates."""

from __future__ import annotations

from datetime import date
import re
from pathlib import Path
from typing import Any

from scout.launch_readiness import build_report


class FounderDecisionRecordDraftError(RuntimeError):
    """Raised when a founder decision draft cannot be generated."""


def default_decision_date() -> str:
    """Return today's ISO date for a generated decision draft."""
    return date.today().isoformat()


def build_decision_record_draft(
    *,
    root: Path,
    blocker_id: str,
    decision_id: str,
    date: str,
    recorded_by: str,
) -> str:
    """Return a prefilled founder decision record draft for a blocker ID."""
    _validate_decision_id(decision_id)
    blocker = _find_blocker(root, blocker_id)
    summary = str(blocker["summary"])
    blocker_type = str(blocker["blocker_type"])
    next_action = str(blocker.get("next_action", "Record the founder decision."))
    closure_evidence = str(blocker.get("closure_evidence", "Updated launch evidence."))

    return f"""# Scout Founder Decision Record: {summary}

Decision ID: {decision_id}
Date: {date}
Decision owner: Arijit Chowdhury
Recorded by: {recorded_by}
Status: Deferred
Related blocker type: {blocker_type}
Related release gate: {summary}
Source prompt / meeting / approval note: Pending founder review.

## Approved decision

[Replace this paragraph with the exact decision. Suggested next action: {next_action}]

## Rejected alternatives

- [Alternative considered and rejected]

## Scope and limits

- Applies to: [specific launch gate or private-beta scope]
- Does not apply to: public launch unless explicitly approved by a separate full launch gate.
- Private beta only? Yes
- Public launch allowed by this decision? No

## Required Codex follow-up

- [ ] Code/doc change: {next_action}
- [ ] Verification command: scout launch-readiness --blocker-id {blocker_id}
- [ ] Evidence file to update: docs/product/launch-evidence-index-2026-06-29.md
- [ ] Release checklist gate to update: {summary}

## Expiration or revisit trigger

This decision expires or must be revisited when:

- Before public launch, material pricing/legal/security changes, or if the underlying blocker changes.

## Evidence links

- Release checklist: docs/product/release-checklist.md
- Decision packet: docs/product/public-launch-action-packet-2026-06-29.md
- Supporting brief: {blocker.get("evidence", "docs/product/release-checklist.md")}
- Verification output: scout launch-readiness --blocker-id {blocker_id}
- Closure evidence expected: {closure_evidence}
"""


def write_decision_record_draft(
    *,
    root: Path,
    output_root: Path,
    blocker_id: str,
    decision_id: str,
    date: str,
    recorded_by: str,
) -> Path:
    """Write a prefilled founder decision record draft and return its path."""
    content = build_decision_record_draft(
        root=root,
        blocker_id=blocker_id,
        decision_id=decision_id,
        date=date,
        recorded_by=recorded_by,
    )
    output_dir = output_root / "docs" / "product" / "founder-decision-drafts"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"founder-decision-draft-{decision_id}.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def write_decision_record_drafts(
    *,
    root: Path,
    output_root: Path,
    blocker_ids: list[str],
    owner: str,
    include_shared_owner: bool,
    blocker_type: str,
    decision_date: str,
    date: str,
    start_index: int,
    recorded_by: str,
) -> list[Path]:
    """Write a filtered packet of sequential founder decision record drafts."""
    _validate_decision_date(decision_date)
    if start_index < 1 or start_index > 99:
        raise FounderDecisionRecordDraftError("Start index must be between 1 and 99.")

    blockers = _matching_blockers(
        root=root,
        blocker_ids=blocker_ids,
        owner=owner,
        include_shared_owner=include_shared_owner,
        blocker_type=blocker_type,
    )
    if not blockers:
        raise FounderDecisionRecordDraftError("No public-launch blockers matched the draft filter.")

    output_paths: list[Path] = []
    for offset, blocker in enumerate(blockers):
        decision_id = f"SCOUT-DEC-{decision_date}-{start_index + offset:02d}"
        output_paths.append(
            write_decision_record_draft(
                root=root,
                output_root=output_root,
                blocker_id=str(blocker["id"]),
                decision_id=decision_id,
                date=date,
                recorded_by=recorded_by,
            )
        )
    return output_paths


def _find_blocker(root: Path, blocker_id: str) -> dict[str, Any]:
    report = build_report(root)
    blockers = report["public_launch"]["blockers"]
    normalized_id = blocker_id.casefold()
    for blocker in blockers:
        if str(blocker.get("id", "")).casefold() == normalized_id:
            return dict(blocker)
    known_ids = ", ".join(str(blocker["id"]) for blocker in blockers)
    raise FounderDecisionRecordDraftError(
        f"Unknown public-launch blocker ID: {blocker_id}. Known IDs: {known_ids}"
    )


def _matching_blockers(
    *,
    root: Path,
    blocker_ids: list[str],
    owner: str,
    include_shared_owner: bool,
    blocker_type: str,
) -> list[dict[str, Any]]:
    report = build_report(root)
    blockers = [dict(blocker) for blocker in report["public_launch"]["blockers"]]
    if blocker_ids:
        requested_ids = [blocker_id.casefold() for blocker_id in blocker_ids]
        blocker_by_id = {str(blocker["id"]).casefold(): blocker for blocker in blockers}
        missing_ids = [
            blocker_id for blocker_id in requested_ids if blocker_id not in blocker_by_id
        ]
        if missing_ids:
            known_ids = ", ".join(str(blocker["id"]) for blocker in blockers)
            raise FounderDecisionRecordDraftError(
                f"Unknown public-launch blocker ID: {', '.join(missing_ids)}. "
                f"Known IDs: {known_ids}"
            )
        blockers = [blocker_by_id[blocker_id] for blocker_id in requested_ids]

    owner_filter = owner.casefold()
    if owner_filter:
        if include_shared_owner:
            blockers = [
                blocker
                for blocker in blockers
                if owner_filter in str(blocker.get("owner", "")).casefold()
            ]
        else:
            blockers = [
                blocker
                for blocker in blockers
                if str(blocker.get("owner", "")).casefold() == owner_filter
            ]

    type_filter = blocker_type.casefold()
    if type_filter:
        blockers = [
            blocker
            for blocker in blockers
            if str(blocker.get("blocker_type", "")).casefold() == type_filter
        ]

    return blockers


def _validate_decision_id(decision_id: str) -> None:
    if not re.fullmatch(r"SCOUT-DEC-\d{8}-\d{2}", decision_id):
        raise FounderDecisionRecordDraftError("Decision ID must match SCOUT-DEC-YYYYMMDD-NN.")


def _validate_decision_date(decision_date: str) -> None:
    if not re.fullmatch(r"\d{8}", decision_date):
        raise FounderDecisionRecordDraftError("Decision date must match YYYYMMDD.")
