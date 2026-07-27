"""FX-1a/FX-1c regression tests — retry-on-transient-error and error surfacing.

Root-caused from docs/test-results-2026-07-26/FAILURE-REPORT.md (F1a/F1c) and
FIX-PLAN.md FX-1a/FX-1c: a failed hosted scrape was returning
success=False/status_code=None/error_message=None with no diagnostic, and a
single transient net::ERR_HTTP2_PROTOCOL_ERROR failed the whole run with no
retry.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scout.core.modes.scrape import scrape
from scout.core.types import ScrapeRequest


def _failed_result(*, status_code=None, error_message=None, url="https://example.com"):
    r = MagicMock()
    r.success = False
    r.url = url
    r.status_code = status_code
    r.error_message = error_message
    return r


def _success_result(url="https://example.com"):
    r = MagicMock()
    r.success = True
    r.url = url
    r.status_code = 200
    r.error_message = None
    r.markdown = "# Hello"
    r.fit_markdown = "# Hello"
    r.html = ""
    r.links = {"internal": [], "external": []}
    r.metadata = {"title": "Hello", "description": "", "language": "en"}
    r.screenshot = None
    return r


# ---------------------------------------------------------------------------
# FX-1c — failure reason must be surfaced, not silently swallowed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_failed_fetch_with_status_code_populates_status_and_error():
    """crawl4ai returns a real status_code but no error_message → both surface."""
    mock_result = _failed_result(status_code=403, error_message=None)

    with patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun = AsyncMock(return_value=mock_result)
        MockCrawler.return_value.__aenter__.return_value = instance

        resp = await scrape(ScrapeRequest(url="https://example.com"))

    assert resp.success is False
    assert resp.status_code == 403
    assert resp.error != ""
    assert "403" in resp.error


@pytest.mark.asyncio
async def test_failed_fetch_with_neither_status_nor_message_still_has_diagnostic():
    """The exact repro: status_code=None AND error_message=None. Must not be silent."""
    mock_result = _failed_result(status_code=None, error_message=None)

    with patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun = AsyncMock(return_value=mock_result)
        MockCrawler.return_value.__aenter__.return_value = instance

        resp = await scrape(ScrapeRequest(url="https://example.com"))

    assert resp.success is False
    assert resp.status_code is None
    assert resp.error != ""  # previously this was "" — the silent-failure bug


# ---------------------------------------------------------------------------
# FX-1a — bounded retry on transient network/protocol errors only
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transient_protocol_error_retries_then_succeeds():
    """net::ERR_HTTP2_PROTOCOL_ERROR is transient → retry → recover."""
    transient = _failed_result(status_code=None, error_message="net::ERR_HTTP2_PROTOCOL_ERROR")
    success = _success_result()

    with (
        patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler,
        patch("scout.core.modes.scrape.asyncio.sleep", new=AsyncMock()),
    ):
        instance = AsyncMock()
        instance.arun = AsyncMock(side_effect=[transient, success])
        MockCrawler.return_value.__aenter__.return_value = instance

        resp = await scrape(ScrapeRequest(url="https://example.com"))

    assert resp.success is True
    assert instance.arun.await_count == 2


@pytest.mark.asyncio
async def test_deterministic_4xx_does_not_retry():
    """A hard 4xx (anti-bot / access denied) must NOT be retried."""
    blocked = _failed_result(status_code=403, error_message="Access Denied")

    with (
        patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler,
        patch("scout.core.modes.scrape.asyncio.sleep", new=AsyncMock()) as mock_sleep,
    ):
        instance = AsyncMock()
        instance.arun = AsyncMock(return_value=blocked)
        MockCrawler.return_value.__aenter__.return_value = instance

        resp = await scrape(ScrapeRequest(url="https://example.com"))

    assert resp.success is False
    assert instance.arun.await_count == 1
    mock_sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_transient_error_retry_uses_a_fresh_crawler_context():
    """FX-4: under sustained load, net::ERR_HTTP2_PROTOCOL_ERROR can leave the
    browser context itself in a poisoned state — retrying `arun()` on that
    SAME context/instance just fails the same way again. The retry must
    construct a brand-new AsyncWebCrawler (fresh browser context) rather than
    reusing the one that just failed.
    """
    transient = _failed_result(status_code=None, error_message="net::ERR_HTTP2_PROTOCOL_ERROR")
    success = _success_result()

    with (
        patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler,
        patch("scout.core.modes.scrape.asyncio.sleep", new=AsyncMock()),
    ):
        first_instance = AsyncMock()
        first_instance.arun = AsyncMock(return_value=transient)
        second_instance = AsyncMock()
        second_instance.arun = AsyncMock(return_value=success)
        MockCrawler.return_value.__aenter__.side_effect = [first_instance, second_instance]

        resp = await scrape(ScrapeRequest(url="https://example.com"))

    assert resp.success is True
    # A fresh AsyncWebCrawler(config=...) must be constructed per attempt —
    # not just re-entered — so the retry gets a brand-new browser context.
    assert MockCrawler.call_count == 2
    first_instance.arun.assert_awaited_once()
    second_instance.arun.assert_awaited_once()


@pytest.mark.asyncio
async def test_retries_are_bounded_and_give_up():
    """Repeated transient failures exhaust the retry budget and return failure."""
    transient = _failed_result(status_code=None, error_message="net::ERR_CONNECTION_RESET")

    with (
        patch("scout.core.modes.scrape.AsyncWebCrawler") as MockCrawler,
        patch("scout.core.modes.scrape.asyncio.sleep", new=AsyncMock()),
    ):
        instance = AsyncMock()
        instance.arun = AsyncMock(return_value=transient)
        MockCrawler.return_value.__aenter__.return_value = instance

        resp = await scrape(ScrapeRequest(url="https://example.com"))

    assert resp.success is False
    # 1 initial attempt + MAX_TRANSIENT_RETRIES retries, bounded (not infinite).
    assert instance.arun.await_count >= 2
    assert instance.arun.await_count <= 4
