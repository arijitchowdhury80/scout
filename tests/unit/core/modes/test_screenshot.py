"""Tests for screenshot mode — visual capture only."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from scout.core.modes.screenshot import screenshot
from scout.core.types import ScreenshotRequest


@pytest.mark.asyncio
async def test_screenshot_returns_base64():
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.url = "https://example.com"
    mock_result.screenshot = "iVBORw0KGgoAAAANSUhEUg=="

    with patch("scout.core.modes.screenshot.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun.return_value = mock_result
        MockCrawler.return_value.__aenter__.return_value = instance

        req = ScreenshotRequest(url="https://example.com")
        resp = await screenshot(req)

    assert resp.success is True
    assert resp.screenshot_base64 == "iVBORw0KGgoAAAANSUhEUg=="
    assert resp.url == "https://example.com"


@pytest.mark.asyncio
async def test_screenshot_failure_when_crawl_fails():
    mock_result = MagicMock()
    mock_result.success = False
    mock_result.url = "https://example.com"
    mock_result.error_message = "Page not found"

    with patch("scout.core.modes.screenshot.AsyncWebCrawler") as MockCrawler:
        instance = AsyncMock()
        instance.arun.return_value = mock_result
        MockCrawler.return_value.__aenter__.return_value = instance

        req = ScreenshotRequest(url="https://example.com")
        resp = await screenshot(req)

    assert resp.success is False
    assert "Page not found" in resp.error
    assert resp.screenshot_base64 == ""


@pytest.mark.asyncio
async def test_screenshot_handles_exception():
    with patch("scout.core.modes.screenshot.AsyncWebCrawler") as MockCrawler:
        MockCrawler.return_value.__aenter__.side_effect = RuntimeError("renderer crash")
        req = ScreenshotRequest(url="https://example.com")
        resp = await screenshot(req)

    assert resp.success is False
    assert "renderer crash" in resp.error


@pytest.mark.asyncio
async def test_screenshot_uses_viewport_dimensions():
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.url = "https://example.com"
    mock_result.screenshot = "abc123"

    with patch("scout.core.modes.screenshot.AsyncWebCrawler") as MockCrawler:
        with patch("scout.core.modes.screenshot.BrowserConfig") as MockBrowserConfig:
            instance = AsyncMock()
            instance.arun.return_value = mock_result
            MockCrawler.return_value.__aenter__.return_value = instance

            req = ScreenshotRequest(
                url="https://example.com", viewport_width=1920, viewport_height=1080
            )
            await screenshot(req)

            call_kwargs = MockBrowserConfig.call_args
            assert call_kwargs is not None
