from __future__ import annotations

import os
import sys
import types

from fastapi.testclient import TestClient

from scout.api import user_browser
from scout.api.main import app
from scout.api.routers import app_browser
from scout.api.user_browser import ChromeCDPService, UserBrowserOpenRequest


_HEADERS = {"X-API-Key": "dev-key"}


def test_app_browser_open_returns_cdp_session_state(monkeypatch) -> None:
    async def fake_open_browser(req: app_browser.UserBrowserOpenRequest):
        return app_browser.UserBrowserSessionState(
            connected=True,
            status="opened",
            debugging_port=49321,
            profile_dir="/tmp/scout-chrome-profile",
            chrome_pid=1234,
            active_url=req.url,
            title="",
            error="",
        )

    monkeypatch.setattr(app_browser.browser_service, "open_browser", fake_open_browser)

    with TestClient(app) as client:
        resp = client.post(
            "/app/browser/open",
            headers=_HEADERS,
            json={"url": "https://www.esteelauder.com/products/571/product-catalog/fragrance"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["connected"] is True
    assert data["status"] == "opened"
    assert data["debugging_port"] == 49321
    assert data["active_url"].endswith("/fragrance")


def test_app_browser_status_returns_current_session(monkeypatch) -> None:
    async def fake_status():
        return app_browser.UserBrowserSessionState(
            connected=True,
            status="opened",
            debugging_port=49321,
            profile_dir="/tmp/scout-chrome-profile",
            chrome_pid=1234,
            active_url="https://www.nike.com/w/mens-shirts",
            title="Nike Shirts",
            error="",
        )

    monkeypatch.setattr(app_browser.browser_service, "status", fake_status)

    with TestClient(app) as client:
        resp = client.get("/app/browser/status", headers=_HEADERS)

    assert resp.status_code == 200
    assert resp.json()["title"] == "Nike Shirts"


async def test_cdp_service_reports_unreachable_when_chrome_port_never_opens(
    monkeypatch, tmp_path
) -> None:
    class FakeProcess:
        pid = 4321

        def poll(self) -> int | None:
            return 1

    monkeypatch.setattr(user_browser.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(user_browser.Path, "exists", lambda _path: True)
    monkeypatch.setattr(user_browser.subprocess, "Popen", lambda *_args, **_kwargs: FakeProcess())
    monkeypatch.setattr(user_browser, "_free_port", lambda: 49999)
    monkeypatch.setattr(ChromeCDPService, "_wait_for_cdp", lambda _self, _port: False)

    service = ChromeCDPService()
    state = await service.open_browser(
        UserBrowserOpenRequest(url="https://example.com", profile_dir=str(tmp_path))
    )

    assert state.connected is False
    assert state.status == "cdp_unreachable"
    assert state.debugging_port == 49999
    assert state.chrome_pid == 4321
    assert "not reachable" in state.error


async def test_cdp_service_clears_stale_chrome_session_restore_before_launch(
    monkeypatch, tmp_path
) -> None:
    """Persistent profile cookies are useful; restored old target tabs are not."""

    default_dir = tmp_path / "Default"
    sessions_dir = default_dir / "Sessions"
    sessions_dir.mkdir(parents=True)
    (sessions_dir / "Session_123").write_text("old estee session", encoding="utf-8")
    for name in ("Current Session", "Current Tabs", "Last Session", "Last Tabs"):
        (default_dir / name).write_text("old restored tab", encoding="utf-8")
    for name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
        (tmp_path / name).symlink_to(f"dead-host-{999999}")

    class FakeProcess:
        pid = 4321

        def poll(self) -> int | None:
            return None

    chrome_path = tmp_path / "Google Chrome"
    chrome_path.write_text("fake chrome", encoding="utf-8")

    monkeypatch.setattr(user_browser.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(user_browser, "CHROME_PATH", str(chrome_path))
    monkeypatch.setattr(user_browser.subprocess, "Popen", lambda *_args, **_kwargs: FakeProcess())
    monkeypatch.setattr(user_browser, "_free_port", lambda: 49999)
    monkeypatch.setattr(ChromeCDPService, "_wait_for_cdp", lambda _self, _port: True)
    monkeypatch.setattr(
        ChromeCDPService,
        "_launched_process_is_stable",
        lambda _self, _process, _port: True,
    )

    service = ChromeCDPService()
    state = await service.open_browser(
        UserBrowserOpenRequest(url="https://www.nike.com/", profile_dir=str(tmp_path))
    )

    assert state.connected is True
    assert state.active_url == "https://www.nike.com/"
    assert not sessions_dir.exists()
    for name in ("Current Session", "Current Tabs", "Last Session", "Last Tabs"):
        assert not (default_dir / name).exists()
    for name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
        assert not (tmp_path / name).exists()


async def test_cdp_service_keeps_singleton_files_for_running_profile(monkeypatch, tmp_path) -> None:
    default_dir = tmp_path / "Default"
    default_dir.mkdir(parents=True)
    (tmp_path / "SingletonLock").symlink_to(f"live-host-{os.getpid()}")
    (tmp_path / "SingletonSocket").symlink_to("/tmp/scout-live-socket")
    (tmp_path / "SingletonCookie").symlink_to("live-cookie")

    class FakeProcess:
        pid = 4321

        def poll(self) -> int | None:
            return None

    chrome_path = tmp_path / "Google Chrome"
    chrome_path.write_text("fake chrome", encoding="utf-8")

    monkeypatch.setattr(user_browser.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(user_browser, "CHROME_PATH", str(chrome_path))
    monkeypatch.setattr(user_browser.subprocess, "Popen", lambda *_args, **_kwargs: FakeProcess())
    monkeypatch.setattr(user_browser, "_free_port", lambda: 49999)
    monkeypatch.setattr(ChromeCDPService, "_wait_for_cdp", lambda _self, _port: True)
    monkeypatch.setattr(
        ChromeCDPService,
        "_launched_process_is_stable",
        lambda _self, _process, _port: True,
    )

    service = ChromeCDPService()
    await service.open_browser(
        UserBrowserOpenRequest(url="https://www.nike.com/", profile_dir=str(tmp_path))
    )

    for name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
        assert (tmp_path / name).is_symlink()


async def test_cdp_status_persists_unreachable_state(monkeypatch, tmp_path) -> None:
    service = ChromeCDPService()
    service._state = app_browser.UserBrowserSessionState(
        connected=True,
        status="opened",
        debugging_port=45555,
        profile_dir=str(tmp_path),
        chrome_pid=1234,
        active_url="https://www.esteelauder.com/products/681/product-catalog/skin-care",
        title="",
        error="",
    )
    service._save_state(service._state)
    monkeypatch.setattr(ChromeCDPService, "_cdp_reachable", lambda _self, _port: False)

    state = await service.status()
    saved = app_browser.UserBrowserSessionState.model_validate_json(
        (tmp_path / "scout-cdp-session.json").read_text(encoding="utf-8")
    )

    assert state.connected is False
    assert state.status == "cdp_unreachable"
    assert saved.connected is False
    assert saved.status == "cdp_unreachable"


async def test_cdp_service_reuses_reachable_saved_profile_session(monkeypatch, tmp_path) -> None:
    opened_tabs: list[tuple[int, str]] = []
    service = ChromeCDPService()
    saved_state = app_browser.UserBrowserSessionState(
        connected=True,
        status="opened",
        debugging_port=45555,
        profile_dir=str(tmp_path),
        chrome_pid=1234,
        active_url="https://old.example",
        title="",
        error="",
    )
    (tmp_path / "scout-cdp-session.json").write_text(
        saved_state.model_dump_json(), encoding="utf-8"
    )

    monkeypatch.setattr(user_browser.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(user_browser.Path, "exists", lambda _path: True)
    monkeypatch.setattr(ChromeCDPService, "_cdp_reachable", lambda _self, _port: True)
    monkeypatch.setattr(
        ChromeCDPService,
        "_open_cdp_tab",
        lambda _self, port, url: opened_tabs.append((port, url)),
    )

    state = await service.open_browser(
        UserBrowserOpenRequest(url="https://new.example", profile_dir=str(tmp_path))
    )

    assert state.connected is True
    assert state.status == "opened"
    assert state.debugging_port == 45555
    assert state.chrome_pid == 1234
    assert state.active_url == "https://new.example"
    assert opened_tabs == [(45555, "https://new.example")]


async def test_cdp_capture_keeps_dom_when_screenshot_fails(monkeypatch) -> None:
    """Nike live finding: full-page screenshot can fail while DOM is usable.

    Capture must not abort in that case; DOM/text/links are the acquisition
    evidence product extraction needs.
    """

    class FakePage:
        url = "https://www.nike.com/w/mens-shirts-tops-9om13znik1"

        async def wait_for_load_state(self, *_args, **_kwargs):
            return None

        async def title(self):
            return "Nike Men's Shirts"

        async def content(self):
            return "<html><body><a href='/t/dri-fit-shirt-abc123'>Dri-FIT Shirt</a></body></html>"

        def locator(self, _selector):
            class FakeLocator:
                async def inner_text(self, **_kwargs):
                    return "Dri-FIT Shirt $45"

            return FakeLocator()

        async def screenshot(self, **_kwargs):
            raise RuntimeError("Unable to capture screenshot")

        async def eval_on_selector_all(self, *_args, **_kwargs):
            return [
                {"text": "Dri-FIT Shirt", "href": "https://www.nike.com/t/dri-fit-shirt-abc123"}
            ]

    class FakeBrowser:
        contexts = [types.SimpleNamespace(pages=[FakePage()])]

        async def close(self):
            return None

    class FakeChromium:
        async def connect_over_cdp(self, _url):
            return FakeBrowser()

    class FakePlaywright:
        chromium = FakeChromium()

    class FakeAsyncPlaywright:
        async def __aenter__(self):
            return FakePlaywright()

        async def __aexit__(self, *_args):
            return None

    fake_module = types.SimpleNamespace(async_playwright=lambda: FakeAsyncPlaywright())
    monkeypatch.setitem(sys.modules, "playwright.async_api", fake_module)

    service = ChromeCDPService()
    service._state = app_browser.UserBrowserSessionState(
        connected=True,
        status="opened",
        debugging_port=45555,
        active_url="https://www.nike.com/w/mens-shirts-tops-9om13znik1",
    )
    monkeypatch.setattr(ChromeCDPService, "_cdp_reachable", lambda _self, _port: True)

    capture = await service.capture_active_tab("https://www.nike.com/w/mens-shirts-tops-9om13znik1")

    assert capture.title == "Nike Men's Shirts"
    assert "Dri-FIT Shirt" in capture.html
    assert capture.text == "Dri-FIT Shirt $45"
    assert capture.screenshot_data_url == ""
    assert capture.links[0]["href"].endswith("abc123")
