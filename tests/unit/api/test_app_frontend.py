from pathlib import Path

from fastapi.testclient import TestClient

from scout.api.main import app


_HEADERS = {"X-API-Key": "dev-key"}


def test_app_serves_self_educating_frontend() -> None:
    client = TestClient(app)

    resp = client.get("/app")

    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "How to use me" in resp.text
    assert "Product Workbench" in resp.text
    assert 'data-mode="auto"' in resp.text
    assert "Algolia Preparation" in resp.text


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
