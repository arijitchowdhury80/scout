"""Tests for the public /status page (rewritten 2026-07-06).

/status is a PUBLIC service-status page: API / playground / email delivery
health + support contact. The old internal launch-blocker burndown, founder
decision records, and operator CLI content must never reappear here
(Arijit's catch: internal information was exposed to the public).
"""

from __future__ import annotations

from pathlib import Path

_STATUS = Path(__file__).resolve().parents[3] / "website" / "status.html"


def test_status_page_is_public_service_health_only() -> None:
    html = _STATUS.read_text(encoding="utf-8")
    normalized = " ".join(html.split())

    assert "All systems operational." in normalized
    assert "API" in normalized
    assert "Playground" in normalized
    assert "email delivery" in normalized.lower()
    assert "support@scout.chowmes.com" in html


def test_status_page_never_exposes_internal_operator_content() -> None:
    html = _STATUS.read_text(encoding="utf-8").lower()

    for banned in (
        "blocker",
        "founder decision",
        "launch-readiness",
        "launch-decision",
        "scout launch-",
        "ready_with_limits",
        "burndown",
        "decision workflow",
    ):
        assert banned not in html, f"internal term on public status page: {banned}"
