from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from scout.api.main import app, get_crawler
from scout.api.routers import app_runs
from scout.api.user_browser import UserBrowserOpenRequest, UserBrowserSessionState
from scout.core.types import ProductCrawlResponse


_HEADERS = {"X-API-Key": "dev-key"}


def test_app_run_create_returns_run_id_and_events_immediately() -> None:
    with TestClient(app) as client:
        resp = client.post(
            "/app/runs",
            headers=_HEADERS,
            json={
                "use_case": "products",
                "mode": "saved",
                "url": "https://www.nike.com/w/mens-shirts",
                "output_dir": "/tmp/scout-app-run-test",
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"].startswith("app_run_")
        assert data["status"] in {"queued", "running", "complete"}
        assert data["events"][0]["stage"] == "queued"

        events_resp = client.get(f"/app/runs/{data['run_id']}/events", headers=_HEADERS)
        assert events_resp.status_code == 200
        assert events_resp.json()["events"]


def test_app_run_reset_removes_run() -> None:
    with TestClient(app) as client:
        create_resp = client.post(
            "/app/runs",
            headers=_HEADERS,
            json={"use_case": "company", "mode": "saved", "url": "https://www.algolia.com/"},
        )
        run_id = create_resp.json()["run_id"]

        reset_resp = client.post(f"/app/runs/{run_id}/reset", headers=_HEADERS)

        assert reset_resp.status_code == 200
        assert reset_resp.json() == {"run_id": run_id, "reset": True}
        assert client.get(f"/app/runs/{run_id}", headers=_HEADERS).status_code == 404


def test_app_run_cancel_marks_run_cancelled() -> None:
    with TestClient(app) as client:
        create_resp = client.post(
            "/app/runs",
            headers=_HEADERS,
            json={"use_case": "products", "mode": "saved", "url": "https://www.nike.com/"},
        )
        run_id = create_resp.json()["run_id"]

        cancel_resp = client.post(f"/app/runs/{run_id}/cancel", headers=_HEADERS)

        assert cancel_resp.status_code == 200
        time.sleep(0.05)
        run_resp = client.get(f"/app/runs/{run_id}", headers=_HEADERS)
        assert run_resp.status_code == 200
        assert run_resp.json()["status"] in {"cancelled", "complete"}


def test_app_run_auto_mode_does_not_open_user_browser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fail_if_user_browser_opens(_req: UserBrowserOpenRequest):
        raise AssertionError("Auto mode must not open the User Browser CDP bridge")

    mock_crawler = MagicMock()
    mock_crawler.products = AsyncMock(
        return_value=ProductCrawlResponse(
            success=True,
            query="Products",
            site="https://shop.example.com",
            start_url="https://shop.example.com",
            total_records=0,
            duration_ms=10,
        )
    )
    monkeypatch.setattr(app_runs.browser_service, "open_browser", fail_if_user_browser_opens)
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    try:
        with TestClient(app) as client:
            create_resp = client.post(
                "/app/runs",
                headers=_HEADERS,
                json={
                    "use_case": "products",
                    "mode": "auto",
                    "url": "https://shop.example.com",
                    "output_dir": str(tmp_path / "auto-products"),
                },
            )
            run_id = create_resp.json()["run_id"]

            deadline = time.time() + 5
            data = create_resp.json()
            while time.time() < deadline:
                run_resp = client.get(f"/app/runs/{run_id}", headers=_HEADERS)
                data = run_resp.json()
                if data["status"] == "complete":
                    break
                time.sleep(0.05)

        assert data["status"] == "complete"
        assert data["mode"] == "auto"
        assert data["browser_evidence"]["provider"] == "crawl4ai"
        assert data["browser_evidence"]["provider"] != "user-browser"
        mock_crawler.products.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()


def test_app_run_auto_mode_uses_scout_browser_when_products_are_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_crawler = MagicMock()
    mock_crawler.products = AsyncMock(
        return_value=ProductCrawlResponse(
            success=True,
            query="Nike shirts",
            site="https://www.nike.com",
            start_url="https://www.nike.com/w/mens-shirts-tops-9om13znik1",
            total_records=0,
            duration_ms=10,
        )
    )

    async def fake_capture(*, run_id: str, url: str, output_dir: str) -> dict[str, object]:
        browser_dir = Path(output_dir) / "browser"
        browser_dir.mkdir(parents=True, exist_ok=True)
        dom = browser_dir / "dom.html"
        text = browser_dir / "text.txt"
        screenshot = browser_dir / "screenshot.png"
        dom.write_text(
            """
            <html><body>
              <article class="product-card" aria-label="Nike Sportswear Men's T-Shirt">
                <a href="/t/sportswear-mens-t-shirt-fGt2fr43/IZ3157-121">
                  <img src="/shirt.jpg" alt="Nike Sportswear Men's T-Shirt">
                  <span>Nike Sportswear Men's T-Shirt</span>
                  <span>$45</span>
                </a>
              </article>
            </body></html>
            """,
            encoding="utf-8",
        )
        text.write_text("Nike Sportswear Men's T-Shirt $45", encoding="utf-8")
        screenshot.write_bytes(b"fake-png")
        return {
            "url": url,
            "title": "Men's Shirts & T-Shirts. Nike.com",
            "provider": "scout-browser",
            "session_type": "Scout browser session",
            "status": "captured",
            "status_code": 200,
            "dom_path": str(dom),
            "text_path": str(text),
            "screenshot_path": str(screenshot),
            "screenshot_data_url": "data:image/png;base64,ZmFrZS1wbmc=",
            "text_preview": "Nike Sportswear Men's T-Shirt $45",
            "links": [
                {
                    "text": "Nike Sportswear Men's T-Shirt",
                    "href": "https://www.nike.com/t/sportswear-mens-t-shirt-fGt2fr43/IZ3157-121",
                }
            ],
            "console_errors": [],
            "network_failures": [],
        }

    monkeypatch.setattr(app_runs, "_capture_scout_browser_evidence", fake_capture)
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    try:
        with TestClient(app) as client:
            create_resp = client.post(
                "/app/runs",
                headers=_HEADERS,
                json={
                    "use_case": "products",
                    "mode": "auto",
                    "url": "https://www.nike.com/w/mens-shirts-tops-9om13znik1",
                    "output_dir": str(tmp_path / "auto-browser-products"),
                },
            )
            run_id = create_resp.json()["run_id"]

            deadline = time.time() + 5
            data = create_resp.json()
            while time.time() < deadline:
                run_resp = client.get(f"/app/runs/{run_id}", headers=_HEADERS)
                data = run_resp.json()
                if data["status"] in {"failed", "complete"}:
                    break
                time.sleep(0.05)

        assert data["status"] == "complete"
        assert data["records"]
        assert data["records"][0]["name"] == "Nike Sportswear Men's T-Shirt"
        assert data["records"][0]["_source"]["extractor"] == "scout_browser_dom"
        assert data["sources"][0]["provider"] == "scout_browser_dom"
        assert any("Scout Browser" in event["message"] for event in data["events"])
        mock_crawler.products.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()


def test_app_run_auto_mode_preserves_scout_browser_blocked_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_crawler = MagicMock()
    mock_crawler.products = AsyncMock(
        return_value=ProductCrawlResponse(
            success=True,
            query="Patagonia tops",
            site="https://www.patagonia.com",
            start_url="https://www.patagonia.com/shop/mens/tops",
            total_records=0,
            duration_ms=10,
        )
    )

    async def fake_capture(*, run_id: str, url: str, output_dir: str) -> dict[str, object]:
        browser_dir = Path(output_dir) / "browser"
        browser_dir.mkdir(parents=True, exist_ok=True)
        dom = browser_dir / "dom.html"
        text = browser_dir / "text.txt"
        screenshot = browser_dir / "screenshot.png"
        dom.write_text("<title>Attention Required! | Cloudflare</title>", encoding="utf-8")
        text.write_text("Sorry, you have been blocked by Cloudflare", encoding="utf-8")
        screenshot.write_bytes(b"fake-png")
        return {
            "url": url,
            "title": "Attention Required! | Cloudflare",
            "provider": "scout-browser",
            "session_type": "Scout browser session",
            "status": "captured",
            "status_code": 403,
            "dom_path": str(dom),
            "text_path": str(text),
            "screenshot_path": str(screenshot),
            "screenshot_data_url": "data:image/png;base64,ZmFrZS1wbmc=",
            "text_preview": "Sorry, you have been blocked by Cloudflare",
            "links": [],
            "console_errors": [],
            "network_failures": [],
        }

    monkeypatch.setattr(app_runs, "_capture_scout_browser_evidence", fake_capture)
    app.dependency_overrides[get_crawler] = lambda: mock_crawler
    try:
        with TestClient(app) as client:
            create_resp = client.post(
                "/app/runs",
                headers=_HEADERS,
                json={
                    "use_case": "products",
                    "mode": "auto",
                    "url": "https://www.patagonia.com/shop/mens/tops",
                    "output_dir": str(tmp_path / "auto-browser-blocked"),
                },
            )
            run_id = create_resp.json()["run_id"]

            deadline = time.time() + 5
            data = create_resp.json()
            while time.time() < deadline:
                run_resp = client.get(f"/app/runs/{run_id}", headers=_HEADERS)
                data = run_resp.json()
                if data["status"] in {"failed", "complete"}:
                    break
                time.sleep(0.05)

        assert data["status"] == "failed"
        assert data["blocked_pages"][0]["reason"] == "scout_browser_access_denied"
        assert data["blocked_pages"][0]["provider_attempts"] == [
            "crawl4ai",
            "scout-browser",
        ]
        assert data["sources"][0]["provider"] == "scout-browser"
        assert data["sources"][0]["status"] == "blocked"
        assert data["browser_evidence"]["screenshot_path"].endswith("browser/screenshot.png")
        assert Path(data["artifacts"]["browser_screenshot"]).exists()
    finally:
        app.dependency_overrides.clear()


def test_app_run_user_browser_mode_opens_chrome_and_waits_for_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_open_browser(req: UserBrowserOpenRequest):
        return UserBrowserSessionState(
            connected=True,
            status="opened",
            debugging_port=49321,
            profile_dir="/tmp/scout-chrome-profile",
            chrome_pid=1234,
            active_url=req.url,
            title="",
            error="",
        )

    monkeypatch.setattr(app_runs.browser_service, "open_browser", fake_open_browser)

    with TestClient(app) as client:
        create_resp = client.post(
            "/app/runs",
            headers=_HEADERS,
            json={
                "use_case": "products",
                "mode": "user-browser",
                "url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
                "output_dir": str(tmp_path / "user-browser-blocked"),
            },
        )
        run_id = create_resp.json()["run_id"]

        deadline = time.time() + 5
        data = create_resp.json()
        while time.time() < deadline:
            run_resp = client.get(f"/app/runs/{run_id}", headers=_HEADERS)
            data = run_resp.json()
            if data["status"] == "waiting_for_user_capture":
                break
            time.sleep(0.05)

        assert data["status"] == "waiting_for_user_capture"
        assert data["blocked_pages"] == []
        assert data["sources"][0]["provider"] == "cdp"
        assert data["sources"][0]["status"] == "waiting_for_user_capture"
        assert data["browser_evidence"]["session_type"] == "User browser session"
        assert data["browser_evidence"]["status"] == "opened"
        assert data["browser_evidence"]["debugging_port"] == 49321
        assert "Capture Active Tab" in data["browser_evidence"]["note"]


def test_app_run_user_browser_capture_ingests_dom_and_extracts_product_records(
    tmp_path: Path,
) -> None:
    with TestClient(app) as client:
        create_resp = client.post(
            "/app/runs",
            headers=_HEADERS,
            json={
                "use_case": "products",
                "mode": "user-browser",
                "url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
                "output_dir": str(tmp_path / "user-browser-capture"),
            },
        )
        run_id = create_resp.json()["run_id"]

        capture_resp = client.post(
            f"/app/runs/{run_id}/user-browser-capture",
            headers=_HEADERS,
            json={
                "url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
                "title": "Skin Care",
                "html": """
                <div class="product-brief"
                     data-product-name="Revitalizing Supreme+ Moisturizer"
                     data-brand="Estée Lauder">
                  <a href="/product/688/97358/product-catalog/skincare/moisturizer">
                    <img src="/media/moisturizer.jpg" alt="">
                  </a>
                  <span>$72.00</span>
                </div>
                """,
                "text": "Revitalizing Supreme+ Moisturizer $72.00",
                "screenshot_data_url": "data:image/png;base64,ZmFrZS1wbmc=",
                "links": [
                    {
                        "text": "Revitalizing Supreme+ Moisturizer",
                        "href": "https://www.esteelauder.com/product/688/97358/product-catalog/skincare/moisturizer",
                    }
                ],
            },
        )

        assert capture_resp.status_code == 200
        data = capture_resp.json()
        assert data["status"] == "complete"
        assert data["records"][0]["name"] == "Revitalizing Supreme+ Moisturizer"
        assert data["records"][0]["_source"]["extractor"] == "user_browser_dom"
        assert data["browser_evidence"]["session_type"] == "User browser session"
        assert data["sources"][0]["provider"] == "user_browser_dom"
        assert Path(data["artifacts"]["browser_dom"]).exists()
        assert Path(data["artifacts"]["records_jsonl"]).exists()


def test_app_run_capture_active_tab_uses_cdp_capture_and_extracts_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_open_browser(req: UserBrowserOpenRequest):
        return UserBrowserSessionState(
            connected=True,
            status="opened",
            debugging_port=49321,
            profile_dir="/tmp/scout-chrome-profile",
            chrome_pid=1234,
            active_url=req.url,
            title="Skin Care",
            error="",
        )

    async def fake_capture_active_tab(target_url: str):
        assert target_url.endswith("/skin-care")
        return app_runs.UserBrowserCaptureRequest(
            url=target_url,
            title="Skin Care",
            html="""
            <div class="product-brief"
                 data-product-name="Advanced Night Repair Serum"
                 data-brand="Estée Lauder">
              <a href="/product/681/141225/product-catalog/skincare/advanced-night-repair-serum">
                <img src="/media/anr.jpg" alt="">
              </a>
              <span>$85.00</span>
            </div>
            """,
            text="Advanced Night Repair Serum $85.00",
            screenshot_data_url="data:image/png;base64,ZmFrZS1wbmc=",
            links=[],
        )

    monkeypatch.setattr(app_runs.browser_service, "open_browser", fake_open_browser)
    monkeypatch.setattr(app_runs.browser_service, "capture_active_tab", fake_capture_active_tab)

    with TestClient(app) as client:
        create_resp = client.post(
            "/app/runs",
            headers=_HEADERS,
            json={
                "use_case": "products",
                "mode": "user-browser",
                "url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
                "output_dir": str(tmp_path / "user-browser-active-tab"),
            },
        )
        run_id = create_resp.json()["run_id"]

        deadline = time.time() + 5
        while time.time() < deadline:
            run_resp = client.get(f"/app/runs/{run_id}", headers=_HEADERS)
            if run_resp.json()["status"] == "waiting_for_user_capture":
                break
            time.sleep(0.05)

        capture_resp = client.post(
            f"/app/runs/{run_id}/capture-active-tab",
            headers=_HEADERS,
        )

        assert capture_resp.status_code == 200
        data = capture_resp.json()
        assert data["status"] == "complete"
        assert data["records"][0]["name"] == "Advanced Night Repair Serum"
        assert data["records"][0]["_source"]["extractor"] == "user_browser_dom"
        assert data["sources"][0]["provider"] == "user_browser_dom"
        assert Path(data["artifacts"]["browser_screenshot"]).exists()


def test_app_run_scout_browser_mode_captures_evidence_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_capture(*, run_id: str, url: str, output_dir: str) -> dict[str, object]:
        browser_dir = Path(output_dir) / "browser"
        browser_dir.mkdir(parents=True, exist_ok=True)
        screenshot = browser_dir / "screenshot.png"
        dom = browser_dir / "dom.html"
        text = browser_dir / "text.txt"
        screenshot.write_bytes(b"fake-png")
        dom.write_text("<html><body>Skincare product listing</body></html>", encoding="utf-8")
        text.write_text("Skincare product listing", encoding="utf-8")
        return {
            "url": url,
            "title": "Skincare",
            "provider": "scout-browser",
            "session_type": "Scout browser session",
            "status": "captured",
            "screenshot_path": str(screenshot),
            "screenshot_data_url": "data:image/png;base64,ZmFrZS1wbmc=",
            "dom_path": str(dom),
            "text_path": str(text),
            "text_preview": "Skincare product listing",
            "links": [],
            "console_errors": [],
            "network_failures": [],
        }

    monkeypatch.setattr(app_runs, "_capture_scout_browser_evidence", fake_capture)

    with TestClient(app) as client:
        create_resp = client.post(
            "/app/runs",
            headers=_HEADERS,
            json={
                "use_case": "products",
                "mode": "scout-browser",
                "url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
                "output_dir": str(tmp_path / "scout-browser-run"),
            },
        )
        run_id = create_resp.json()["run_id"]

        deadline = time.time() + 5
        data = create_resp.json()
        while time.time() < deadline:
            run_resp = client.get(f"/app/runs/{run_id}", headers=_HEADERS)
            data = run_resp.json()
            if data["status"] in {"failed", "complete"}:
                break
            time.sleep(0.05)

        assert data["browser_evidence"]["session_type"] == "Scout browser session"
        assert data["browser_evidence"]["screenshot_data_url"].startswith("data:image/png")
        assert data["artifacts"]["browser_screenshot"].endswith("browser/screenshot.png")
        assert data["artifacts"]["browser_dom"].endswith("browser/dom.html")
        assert data["sources"][0]["provider"] == "scout-browser"


def test_app_run_scout_browser_mode_extracts_products_from_captured_dom(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_capture(*, run_id: str, url: str, output_dir: str) -> dict[str, object]:
        browser_dir = Path(output_dir) / "browser"
        browser_dir.mkdir(parents=True, exist_ok=True)
        screenshot = browser_dir / "screenshot.png"
        dom = browser_dir / "dom.html"
        text = browser_dir / "text.txt"
        links = browser_dir / "links.json"
        screenshot.write_bytes(b"fake-png")
        dom.write_text(
            """
            <html><body>
              <div class="product-brief"
                   data-product-name="Advanced Night Repair Serum"
                   data-brand="Estée Lauder">
                <a href="/product/681/141225/product-catalog/skincare/advanced-night-repair-serum">
                  <img src="/media/anr.jpg" alt="">
                </a>
                <span class="product-brief__price">$85.00</span>
              </div>
            </body></html>
            """,
            encoding="utf-8",
        )
        text.write_text("Advanced Night Repair Serum $85.00", encoding="utf-8")
        links.write_text("[]", encoding="utf-8")
        return {
            "url": url,
            "title": "Skin Care",
            "provider": "scout-browser",
            "session_type": "Scout browser session",
            "status": "captured",
            "status_code": 200,
            "screenshot_path": str(screenshot),
            "screenshot_data_url": "data:image/png;base64,ZmFrZS1wbmc=",
            "dom_path": str(dom),
            "text_path": str(text),
            "links_path": str(links),
            "text_preview": "Advanced Night Repair Serum $85.00",
            "links": [],
            "console_errors": [],
            "network_failures": [],
        }

    monkeypatch.setattr(app_runs, "_capture_scout_browser_evidence", fake_capture)

    with TestClient(app) as client:
        create_resp = client.post(
            "/app/runs",
            headers=_HEADERS,
            json={
                "use_case": "products",
                "mode": "scout-browser",
                "url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
                "output_dir": str(tmp_path / "scout-browser-dom-run"),
            },
        )
        run_id = create_resp.json()["run_id"]

        deadline = time.time() + 5
        data = create_resp.json()
        while time.time() < deadline:
            run_resp = client.get(f"/app/runs/{run_id}", headers=_HEADERS)
            data = run_resp.json()
            if data["status"] in {"failed", "complete"}:
                break
            time.sleep(0.05)

        assert data["status"] == "complete"
        assert data["records"]
        assert data["records"][0]["name"] == "Advanced Night Repair Serum"
        assert data["records"][0]["brand"] == "Estée Lauder"
        assert data["records"][0]["price"] == 85.0
        assert data["records"][0]["_source"]["extractor"] == "scout_browser_dom"
        assert data["sources"][0]["provider"] == "scout_browser_dom"
        assert Path(data["artifacts"]["records_json"]).exists()
