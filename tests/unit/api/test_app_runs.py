from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

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


def test_app_run_browser_mode_records_blocked_artifacts(tmp_path: Path) -> None:
    with TestClient(app) as client:
        create_resp = client.post(
            "/app/runs",
            headers=_HEADERS,
            json={
                "use_case": "products",
                "mode": "browser",
                "url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
                "output_dir": str(tmp_path / "browser-blocked"),
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
        assert data["artifacts"]["manifest"].endswith("manifest.json")
        assert Path(data["artifacts"]["manifest"]).exists()
        assert Path(data["artifacts"]["blocked_pages_json"]).exists()
