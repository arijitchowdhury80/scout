"""Regression tests for hosted readiness copy shown on the public site."""

from __future__ import annotations

from pathlib import Path


_WEBSITE_DIR = Path(__file__).resolve().parents[3] / "website"


def test_status_page_describes_pending_beta_delivery_queue() -> None:
    """Status copy must match /v1/hosted/beta-key behavior when SMTP is absent."""
    html = (_WEBSITE_DIR / "status.html").read_text(encoding="utf-8")
    normalized = " ".join(html.split())

    assert "register testers and queue API-key delivery" in normalized
    assert "pending delivery queue" in normalized
    assert "Direct hosted beta signup fails closed" not in normalized
    assert "Current blockers: 0" not in normalized
    assert "Current blockers: external configuration" in normalized
