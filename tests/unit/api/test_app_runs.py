from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scout.api.routers import app_runs
from scout.api.main import app


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


def test_app_run_user_browser_mode_records_bridge_setup_artifacts(tmp_path: Path) -> None:
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
            if data["status"] in {"failed", "complete"}:
                break
            time.sleep(0.05)

        assert data["status"] == "failed"
        assert data["blocked_pages"]
        assert data["sources"]
        assert data["browser_evidence"]["session_type"] == "User browser session"
        assert data["artifacts"]["manifest"].endswith("manifest.json")
        assert Path(data["artifacts"]["manifest"]).exists()
        assert Path(data["artifacts"]["blocked_pages_json"]).exists()


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
