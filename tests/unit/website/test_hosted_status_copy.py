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


def test_status_page_loads_live_hosted_readiness_panel() -> None:
    """The public status page should expose the live hosted readiness endpoint."""
    html = (_WEBSITE_DIR / "status.html").read_text(encoding="utf-8")
    status_js = (_WEBSITE_DIR / "assets" / "status.js").read_text(encoding="utf-8")
    normalized = " ".join(html.split())

    assert 'id="liveHostedReadiness"' in html
    assert 'data-status-endpoint="/v1/billing/stripe/status"' in html
    assert 'id="liveReadinessCards"' in html
    assert 'id="liveMissingKeys"' in html
    assert 'id="liveOperatorActions"' in html
    assert 'src="./assets/status.js"' in html
    assert "Live hosted readiness" in normalized
    assert "/v1/billing/stripe/status" in status_js
    assert "operator_next_actions" in status_js
    assert "missing_environment_keys" in status_js
    assert "sk_live_" not in status_js
    assert "sk_test_" not in status_js
    assert "whsec_" not in status_js
