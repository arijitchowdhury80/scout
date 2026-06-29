from __future__ import annotations

from pathlib import Path

import pytest

from scripts import founder_decision_record_check


def _write_decision_record(path: Path, *, status: str = "Approved") -> None:
    path.write_text(
        f"""# Scout Founder Decision Record: License

Decision ID: SCOUT-DEC-20260629-01
Date: 2026-06-29
Decision owner: Arijit Chowdhury
Recorded by: Codex
Status: {status}
Related blocker type: founder_decision
Related release gate: License decision recorded.
Source prompt / meeting / approval note: Test fixture

## Approved decision

Scout local/core is licensed as Apache-2.0.

## Rejected alternatives

- MIT

## Scope and limits

- Applies to: local package and source distribution
- Does not apply to: hosted service terms
- Private beta only? Yes
- Public launch allowed by this decision? No

## Required Codex follow-up

- [ ] Code/doc change: add LICENSE and pyproject license expression
- [ ] Verification command: python3 scripts/license_release_gate_check.py --expected-license Apache-2.0
- [ ] Evidence file to update: docs/product/launch-evidence-index-2026-06-29.md
- [ ] Release checklist gate to update: License decision recorded.

## Expiration or revisit trigger

Before public launch.

## Evidence links

- Release checklist: docs/product/release-checklist.md
- Decision packet: docs/product/public-launch-action-packet-2026-06-29.md
- Supporting brief: docs/legal/scout-license-distribution-decision-brief-2026-06-29.md
- Verification output: pending
""",
        encoding="utf-8",
    )


def _write_decision_draft(path: Path, *, status: str = "Deferred") -> None:
    path.write_text(
        f"""# Scout Founder Decision Record: License

Decision ID: SCOUT-DEC-20260629-01
Date: 2026-06-29
Decision owner: Arijit Chowdhury
Recorded by: Codex
Status: {status}
Related blocker type: founder_decision
Related release gate: license decision
Source prompt / meeting / approval note: Pending founder review.

## Approved decision

[Replace this paragraph with the exact decision. Suggested next action: Approve Apache-2.0 for Scout local/core.]

## Rejected alternatives

- [Alternative considered and rejected]

## Scope and limits

- Applies to: [specific launch gate or private-beta scope]
- Does not apply to: public launch unless explicitly approved by a separate full launch gate.
- Private beta only? Yes
- Public launch allowed by this decision? No

## Required Codex follow-up

- [ ] Code/doc change: Approve Apache-2.0 for Scout local/core.
- [ ] Verification command: scout launch-readiness --blocker-id license-decision
- [ ] Evidence file to update: docs/product/launch-evidence-index-2026-06-29.md
- [ ] Release checklist gate to update: license decision

## Expiration or revisit trigger

Before public launch.

## Evidence links

- Release checklist: docs/product/release-checklist.md
- Decision packet: docs/product/public-launch-action-packet-2026-06-29.md
- Supporting brief: docs/product/release-checklist.md
- Verification output: scout launch-readiness --blocker-id license-decision
""",
        encoding="utf-8",
    )


def test_founder_decision_record_check_passes_for_complete_record(tmp_path: Path) -> None:
    record = tmp_path / "founder-decision-record-SCOUT-DEC-20260629-01.md"
    _write_decision_record(record)

    result = founder_decision_record_check.validate_decision_record(record)

    assert result.path == record
    assert result.decision_id == "SCOUT-DEC-20260629-01"
    assert result.status == "Approved"


def test_founder_decision_record_check_rejects_missing_required_followup(
    tmp_path: Path,
) -> None:
    record = tmp_path / "founder-decision-record-SCOUT-DEC-20260629-01.md"
    _write_decision_record(record)
    record.write_text(
        record.read_text(encoding="utf-8").replace(
            "- [ ] Verification command: python3 scripts/license_release_gate_check.py --expected-license Apache-2.0\n",
            "",
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        founder_decision_record_check.FounderDecisionRecordError,
        match="Verification command",
    ):
        founder_decision_record_check.validate_decision_record(record)


def test_founder_decision_record_check_main_reports_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing = tmp_path / "missing.md"

    assert founder_decision_record_check.main([str(missing)]) == 2

    assert "FAIL" in capsys.readouterr().err


def test_founder_decision_record_check_existing_records_passes_when_none_exist(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "docs" / "product").mkdir(parents=True)

    assert founder_decision_record_check.main(["--root", str(tmp_path), "--check-existing"]) == 0

    assert "0 founder decision records" in capsys.readouterr().out


def test_founder_decision_record_check_existing_records_validates_matching_records(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    records_dir = tmp_path / "docs" / "product"
    records_dir.mkdir(parents=True)
    _write_decision_record(records_dir / "founder-decision-record-SCOUT-DEC-20260629-01.md")
    (records_dir / "founder-decision-record-template-2026-06-29.md").write_text(
        "template is not a completed record", encoding="utf-8"
    )

    assert founder_decision_record_check.main(["--root", str(tmp_path), "--check-existing"]) == 0

    output = capsys.readouterr().out
    assert "1 founder decision records" in output
    assert "SCOUT-DEC-20260629-01" in output


def test_founder_decision_draft_check_accepts_safe_existing_drafts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    draft_dir = tmp_path / "docs" / "product" / "founder-decision-drafts"
    draft_dir.mkdir(parents=True)
    _write_decision_draft(draft_dir / "founder-decision-draft-SCOUT-DEC-20260629-01.md")

    assert founder_decision_record_check.main(["--root", str(tmp_path), "--check-drafts"]) == 0

    output = capsys.readouterr().out
    assert "PASS: 1 founder decision drafts are safe for review." in output
    assert "SCOUT-DEC-20260629-01: Deferred" in output


def test_founder_decision_draft_check_rejects_approval_like_draft(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    draft_dir = tmp_path / "docs" / "product" / "founder-decision-drafts"
    draft_dir.mkdir(parents=True)
    _write_decision_draft(
        draft_dir / "founder-decision-draft-SCOUT-DEC-20260629-01.md",
        status="Approved",
    )

    assert founder_decision_record_check.main(["--root", str(tmp_path), "--check-drafts"]) == 2

    assert "Draft records must keep Status: Deferred" in capsys.readouterr().err
