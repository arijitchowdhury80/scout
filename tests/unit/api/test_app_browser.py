from __future__ import annotations

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
