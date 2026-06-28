"""Tests for beta terms/privacy placeholder documentation gates."""

from __future__ import annotations

from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_beta_terms_and_privacy_placeholder_docs_exist() -> None:
    terms = (_REPO_ROOT / "docs/legal/beta-terms-placeholder.md").read_text(encoding="utf-8")
    privacy = (_REPO_ROOT / "docs/legal/beta-privacy-placeholder.md").read_text(encoding="utf-8")

    assert "This is not a final Terms of Service." in terms
    assert "Use Scout only for websites and data you are allowed to access." in terms
    assert "Hosted beta is capped and metered." in terms
    assert "This is not a final Privacy Policy." in privacy
    assert "Local Scout keeps run artifacts on the user's machine" in privacy
    assert "Do not submit secrets or regulated personal data." in privacy


def test_release_checklist_records_terms_privacy_placeholder_gate() -> None:
    checklist = (_REPO_ROOT / "docs/product/release-checklist.md").read_text(encoding="utf-8")

    assert "[x] Terms/privacy placeholders created before public hosted beta." in checklist
    assert "docs/legal/beta-terms-placeholder.md" in checklist
    assert "docs/legal/beta-privacy-placeholder.md" in checklist


def test_legal_readiness_checklist_records_beta_data_handling_boundaries() -> None:
    checklist = (_REPO_ROOT / "docs/legal/legal-readiness-checklist.md").read_text(encoding="utf-8")

    assert "[x] Add customer-facing terms that users are responsible for lawful use." in checklist
    assert "[x] Document where Scout writes artifacts." in checklist
    assert "[x] Add retention/deletion guidance for run folders." in checklist
    assert "[x] Make API-key handling explicit: `.env.local`, never committed." in checklist
    assert (
        "[x] Add privacy note for captured screenshots/DOM from user browser sessions." in checklist
    )
