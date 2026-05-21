from pathlib import Path

from fastapi.testclient import TestClient

from scout.api.main import app


_HEADERS = {"X-API-Key": "dev-key"}


def test_app_serves_self_educating_frontend() -> None:
    client = TestClient(app)

    resp = client.get("/app")

    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Run Setup" in resp.text
    assert "Live Execution" in resp.text
    assert "Results Review" in resp.text
    assert 'data-mode="auto"' in resp.text
    assert 'fetchJson("/app/runs"' in resp.text
    assert 'data-copy-target="commandPreview"' in resp.text
    assert "Crawl Settings" in resp.text
    assert "Tune how Scout collects pages. Defaults are safe for most runs." in resp.text
    assert "Developer Details" in resp.text
    assert 'id="developerDetails"' in resp.text
    assert 'id="addOptionMenu"' in resp.text
    assert 'id="livePanel"' in resp.text
    assert 'id="resultsPanel"' in resp.text
    assert 'id="recordsTable"' in resp.text
    assert 'id="browserEvidence"' in resp.text
    assert 'id="detailDrawer"' in resp.text
    assert 'id="cancelRun"' in resp.text
    assert 'id="clearRun"' in resp.text
    assert 'id="runStatus"' in resp.text
    assert 'id="workdir"' in resp.text
    assert 'id="pickDir"' in resp.text
    assert 'id="workdirPicker"' not in resp.text
    assert 'id="workdirCandidate"' not in resp.text
    assert 'id="workdirDialog"' not in resp.text
    assert 'id="directoryList"' not in resp.text
    assert 'id="useCurrentDir"' not in resp.text
    assert 'id="nativeDirPicker"' not in resp.text
    assert "/workdir/pick-native" in resp.text
    assert "Working directory selected" in resp.text
    assert "Product Workbench - Estée Lauder" not in resp.text
    assert "412 / 412 records mapped" not in resp.text
    assert "not implemented yet" not in resp.text
    assert "coming next" not in resp.text
    assert "Advanced Night Repair Synchronized" not in resp.text
    assert "2025-05-15" not in resp.text
    assert "session-only-key" not in resp.text
    assert "sk_live_" not in resp.text
    assert "product-grid/skincare" not in resp.text
    assert 'id="clearStartUrl"' in resp.text


def test_favicon_probe_is_public_and_quiet() -> None:
    client = TestClient(app)

    resp = client.get("/favicon.ico")

    assert resp.status_code == 204
    assert resp.text == ""


def test_app_first_home_contains_three_state_workspace() -> None:
    client = TestClient(app)

    resp = client.get("/app")

    assert resp.status_code == 200
    expected_labels = [
        "Run",
        "History",
        "Presets",
        "Targets",
        "Data",
        "Integrations",
        "Settings",
        "Help",
        "Run Setup",
        "Live Execution",
        "Progress Timeline",
        "Browser Evidence",
        "Results Review",
        "Overview",
        "Records",
        "Sources",
        "Blocked",
        "Artifacts",
        "Logs",
    ]
    for label in expected_labels:
        assert label in resp.text


def test_app_first_home_has_selected_record_drawer() -> None:
    client = TestClient(app)

    resp = client.get("/app")

    assert resp.status_code == 200
    assert 'id="detailDrawer"' in resp.text
    assert 'id="drawerContent"' in resp.text
    assert "Selected Record" in resp.text
    assert "openRecordDrawer" in resp.text


def test_run_artifact_endpoints_return_records_sources_and_artifacts(tmp_path: Path) -> None:
    client = TestClient(app)
    output_dir = tmp_path / "company-run"
    run_resp = client.post(
        "/run/company",
        json={"query": "Adobe", "mode": "saved", "output_dir": str(output_dir)},
        headers=_HEADERS,
    )
    run_id = run_resp.json()["manifest"]["run_id"]

    records_resp = client.get(f"/runs/{run_id}/records", headers=_HEADERS)
    sources_resp = client.get(f"/runs/{run_id}/sources", headers=_HEADERS)
    artifacts_resp = client.get(f"/runs/{run_id}/artifacts", headers=_HEADERS)

    assert records_resp.status_code == 200
    assert records_resp.json()["total"] == 3
    assert records_resp.json()["records"][0]["citations"]
    assert sources_resp.status_code == 200
    assert sources_resp.json()["sources"][0]["source_id"].startswith("src_")
    assert artifacts_resp.status_code == 200
    assert artifacts_resp.json()["artifacts"]["records_json"].endswith("records.json")


def test_algolia_preview_validates_records_without_echoing_api_key() -> None:
    client = TestClient(app)
    resp = client.post(
        "/algolia/preview",
        headers=_HEADERS,
        json={
            "app_id": "APP123",
            "api_key": "secret-admin-key",
            "index_name": "products_dev",
            "records": [
                {
                    "objectID": "sku-1",
                    "name": "Advanced Night Repair",
                    "url": "https://www.esteelauder.com/product/1",
                    "brand": "Estee Lauder",
                    "price": 85,
                }
            ],
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["ready"] is True
    assert data["record_count"] == 1
    assert data["sample_object_ids"] == ["sku-1"]
    assert data["credentials"]["app_id_configured"] is True
    assert data["credentials"]["api_key_configured"] is True
    assert "secret-admin-key" not in resp.text


def test_algolia_preview_reports_missing_required_fields() -> None:
    client = TestClient(app)
    resp = client.post(
        "/algolia/preview",
        headers=_HEADERS,
        json={
            "app_id": "",
            "api_key": "",
            "index_name": "",
            "records": [{"name": "Nameless URL"}],
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["ready"] is False
    assert "index_name" in data["missing_required_fields"]
    assert "records[0].objectID" in data["missing_required_fields"]
    assert "records[0].url" in data["missing_required_fields"]
