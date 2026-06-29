from __future__ import annotations

from pathlib import Path

import pytest

from scripts import founder_decision_record_draft
from scripts import founder_decision_record_check


ROOT = Path(__file__).resolve().parents[2]


def test_build_decision_record_draft_prefills_blocker_metadata() -> None:
    draft = founder_decision_record_draft.build_decision_record_draft(
        root=ROOT,
        blocker_id="license-decision",
        decision_id="SCOUT-DEC-20260629-01",
        date="2026-06-29",
        recorded_by="Codex",
    )

    assert "# Scout Founder Decision Record: license decision" in draft
    assert "Decision ID: SCOUT-DEC-20260629-01" in draft
    assert "Date: 2026-06-29" in draft
    assert "Recorded by: Codex" in draft
    assert "Status: Deferred" in draft
    assert "Related blocker type: founder_decision" in draft
    assert "Related release gate: license decision" in draft
    assert "Source prompt / meeting / approval note: Pending founder review." in draft
    assert "Approve Apache-2.0 for Scout local/core or choose another license path." in draft
    assert "Public launch allowed by this decision? No" in draft
    assert "docs/product/public-launch-action-packet-2026-06-29.md" in draft
    assert "scout launch-readiness --blocker-id license-decision" in draft


def test_write_decision_record_draft_uses_drafts_directory(tmp_path: Path) -> None:
    draft_path = founder_decision_record_draft.write_decision_record_draft(
        root=ROOT,
        output_root=tmp_path,
        blocker_id="crawl4ai-lxml-risk-decision",
        decision_id="SCOUT-DEC-20260629-02",
        date="2026-06-29",
        recorded_by="Codex",
    )

    assert draft_path == (
        tmp_path
        / "docs"
        / "product"
        / "founder-decision-drafts"
        / "founder-decision-draft-SCOUT-DEC-20260629-02.md"
    )
    content = draft_path.read_text(encoding="utf-8")
    assert "Related blocker type: risk_decision" in content
    assert "Related release gate: Crawl4AI/lxml risk decision" in content
    assert "Public launch allowed by this decision? No" in content


def test_write_decision_record_drafts_generates_sequential_filtered_packet(
    tmp_path: Path,
) -> None:
    draft_paths = founder_decision_record_draft.write_decision_record_drafts(
        root=ROOT,
        output_root=tmp_path,
        blocker_ids=[],
        owner="Arijit",
        include_shared_owner=True,
        blocker_type="",
        decision_date="20260629",
        date="2026-06-29",
        start_index=1,
        recorded_by="Codex",
    )

    assert [path.name for path in draft_paths] == [
        "founder-decision-draft-SCOUT-DEC-20260629-01.md",
        "founder-decision-draft-SCOUT-DEC-20260629-02.md",
        "founder-decision-draft-SCOUT-DEC-20260629-03.md",
        "founder-decision-draft-SCOUT-DEC-20260629-04.md",
        "founder-decision-draft-SCOUT-DEC-20260629-05.md",
        "founder-decision-draft-SCOUT-DEC-20260629-06.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in draft_paths)
    assert "Related release gate: license decision" in combined
    assert "Related release gate: Crawl4AI/lxml risk decision" in combined
    assert "Related release gate: Stripe real test-mode smoke" in combined
    assert "Public launch allowed by this decision? No" in combined


def test_write_decision_record_drafts_rejects_empty_filter_result(tmp_path: Path) -> None:
    with pytest.raises(
        founder_decision_record_draft.FounderDecisionRecordDraftError,
        match="No public-launch blockers matched",
    ):
        founder_decision_record_draft.write_decision_record_drafts(
            root=ROOT,
            output_root=tmp_path,
            blocker_ids=[],
            owner="Nobody",
            include_shared_owner=False,
            blocker_type="",
            decision_date="20260629",
            date="2026-06-29",
            start_index=1,
            recorded_by="Codex",
        )


def test_generated_drafts_are_not_completed_decision_records(tmp_path: Path) -> None:
    founder_decision_record_draft.write_decision_record_draft(
        root=ROOT,
        output_root=tmp_path,
        blocker_id="license-decision",
        decision_id="SCOUT-DEC-20260629-03",
        date="2026-06-29",
        recorded_by="Codex",
    )

    assert founder_decision_record_check.existing_decision_records(tmp_path) == []


def test_build_decision_record_draft_rejects_unknown_blocker_id() -> None:
    with pytest.raises(
        founder_decision_record_draft.FounderDecisionRecordDraftError,
        match="Unknown public-launch blocker ID",
    ):
        founder_decision_record_draft.build_decision_record_draft(
            root=ROOT,
            blocker_id="not-a-real-blocker",
            decision_id="SCOUT-DEC-20260629-99",
            date="2026-06-29",
            recorded_by="Codex",
        )
