from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest


pytestmark = pytest.mark.live

HEADERS = {"Content-Type": "application/json", "X-API-Key": "dev-key"}

PRODUCT_TARGETS = [
    ("Estée Lauder", "https://www.esteelauder.com/products/681/product-catalog/skin-care"),
    ("Lacoste", "https://www.lacoste.com/us/lacoste/men/clothing/polos"),
    ("Nike", "https://www.nike.com/w/mens-shirts-tops-9om13znik1"),
    ("L.L.Bean", "https://www.llbean.com/llb/shop/502859"),
    ("Patagonia", "https://www.patagonia.com/shop/mens/tops"),
    ("Home Depot", "https://www.homedepot.com/s/cordless%20drill"),
]

SCENARIO_COMPANY_SLUGS = {
    "Estée Lauder": "estee_lauder",
    "Lacoste": "lacoste",
    "Nike": "nike",
    "L.L.Bean": "ll_bean",
    "Patagonia": "patagonia",
    "Home Depot": "home_depot",
    "Algolia": "algolia",
    "Constructor": "constructor",
    "Adobe": "adobe",
    "British Airways": "british_airways",
}

INTELLIGENCE_TARGETS = [
    ("company", "Algolia", "https://www.algolia.com/"),
    ("company", "Constructor", "https://constructor.com/"),
    ("company", "Adobe", "https://www.adobe.com/"),
    ("company", "Home Depot", "https://www.homedepot.com/"),
    ("company", "Nike", "https://www.nike.com/"),
    ("company", "British Airways", "https://www.britishairways.com/"),
    ("company", "Estée Lauder", "https://www.esteelauder.com/"),
    ("prism", "Algolia", "https://www.algolia.com/"),
    ("prism", "Constructor", "https://constructor.com/"),
    ("prism", "Adobe", "https://www.adobe.com/"),
    ("prism", "Home Depot", "https://www.homedepot.com/"),
    ("prism", "Nike", "https://www.nike.com/"),
    ("prism", "British Airways", "https://www.britishairways.com/"),
    ("prism", "Estée Lauder", "https://www.esteelauder.com/"),
    ("careers", "Algolia", "https://www.algolia.com/careers/"),
    ("careers", "Constructor", "https://constructor.com/careers/"),
    ("careers", "Adobe", "https://careers.adobe.com/"),
    ("careers", "Home Depot", "https://careers.homedepot.com/"),
    ("careers", "Nike", "https://jobs.nike.com/"),
    ("careers", "British Airways", "https://careers.ba.com/"),
    ("careers", "Estée Lauder", "https://www.elcompanies.com/en/careers"),
    ("news", "Algolia", "https://www.algolia.com/blog/"),
    ("news", "Constructor", "https://constructor.com/blog"),
    ("news", "Adobe", "https://news.adobe.com/"),
    ("news", "Home Depot", "https://corporate.homedepot.com/newsroom"),
    ("news", "Nike", "https://about.nike.com/en/newsroom"),
    ("news", "British Airways", "https://mediacentre.britishairways.com/"),
    ("news", "Estée Lauder", "https://www.elcompanies.com/en/news-and-media"),
    ("investor", "Adobe", "https://www.adobe.com/investor-relations.html"),
    ("investor", "Home Depot", "https://ir.homedepot.com/"),
    ("investor", "Estée Lauder", "https://www.elcompanies.com/en/investors"),
    ("investor", "British Airways", "https://www.iairgroup.com/en/investors-and-shareholders"),
]

ADDITIONAL_TARGETS = [
    ("docs", "Algolia", "https://www.algolia.com/doc/"),
    ("docs", "Constructor", "https://docs.constructor.com/"),
    ("research", "Algolia", "https://www.algolia.com/"),
    ("social", "Algolia", "https://www.algolia.com/"),
    ("locations", "Home Depot", "https://www.homedepot.com/l/"),
]


@pytest.fixture()
def scout_server() -> Iterator[str]:
    if os.getenv("SCOUT_LIVE_TESTS") != "1":
        pytest.skip("Set SCOUT_LIVE_TESTS=1 to run live website certification tests")
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "scout.cli", "serve", "--host", "127.0.0.1", "--port", str(port)],
        cwd=Path(__file__).parents[2],
        env={**os.environ, "SCOUT_LIVE_TESTS": "1", "SCOUT_DISABLE_NATIVE_PICKER": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_for_health(base_url)
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.mark.parametrize(("company", "url"), PRODUCT_TARGETS)
def test_product_targets_run_from_service(
    scout_server: str, tmp_path: Path, company: str, url: str
) -> None:
    result = _run_service_workflow(
        base_url=scout_server,
        use_case="products",
        mode="auto",
        company=company,
        url=url,
        output_dir=tmp_path / _slug(company) / "products",
    )

    assert result["run_status"] in {"success", "blocked_with_evidence"}, result
    assert result["record_count"] > 0 or result["blocked_count"] > 0, result
    assert result["source_count"] > 0 or result["blocked_count"] > 0, result
    assert result["run_id"], result
    assert result["artifact_count"] > 0, result
    if result["record_count"] > 0:
        assert result["citation_count"] > 0 or result["source_count"] > 0, result


@pytest.mark.parametrize(("use_case", "company", "url"), INTELLIGENCE_TARGETS)
def test_intelligence_targets_run_from_service(
    scout_server: str, tmp_path: Path, use_case: str, company: str, url: str
) -> None:
    result = _run_service_workflow(
        base_url=scout_server,
        use_case=use_case,
        mode="auto",
        company=company,
        url=url,
        output_dir=tmp_path / _slug(company) / use_case,
    )

    assert result["run_status"] == "success", result
    assert result["record_count"] > 0, result
    assert result["source_count"] > 0, result
    assert result["citation_count"] > 0, result
    assert result["run_id"], result
    assert result["artifact_count"] > 0, result


def test_estee_lauder_hard_site_modes_from_service(scout_server: str, tmp_path: Path) -> None:
    results = [
        _run_service_workflow(
            base_url=scout_server,
            use_case="products",
            mode=mode,
            company="Estée Lauder",
            url="https://www.esteelauder.com/products/681/product-catalog/skin-care",
            output_dir=tmp_path / "estee-lauder-hard-site" / mode,
        )
        for mode in ["auto", "crawl4ai", "scout-browser"]
    ]

    for result in results:
        assert result["run_status"] in {"success", "blocked_with_evidence"}, result
        assert result["record_count"] > 0 or result["blocked_count"] > 0, result
        assert result["run_id"], result
        assert result["artifact_count"] > 0, result


@pytest.mark.parametrize(("use_case", "company", "url"), ADDITIONAL_TARGETS)
def test_additional_feature_targets_run_from_service(
    scout_server: str, tmp_path: Path, use_case: str, company: str, url: str
) -> None:
    result = _run_service_workflow(
        base_url=scout_server,
        use_case=use_case,
        mode="auto",
        company=company,
        url=url,
        output_dir=tmp_path / _slug(company) / use_case,
    )

    assert result["run_status"] in {"success", "blocked_with_evidence"}, result
    assert result["record_count"] > 0 or result["blocked_count"] > 0, result
    assert result["source_count"] > 0 or result["blocked_count"] > 0, result
    assert result["run_id"], result
    assert result["artifact_count"] > 0, result


def _run_service_workflow(
    *,
    base_url: str,
    use_case: str,
    mode: str,
    company: str,
    url: str,
    output_dir: Path,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    create_payload = {
        "use_case": use_case,
        "mode": mode,
        "url": url,
        "output_dir": str(output_dir),
    }
    create = _request_json(f"{base_url}/app/runs", method="POST", payload=create_payload)
    run_id = str(create["run_id"])
    state = _poll_run(base_url, run_id)
    records = state.get("records") if isinstance(state.get("records"), list) else []
    sources = state.get("sources") if isinstance(state.get("sources"), list) else []
    blocked = state.get("blocked_pages") if isinstance(state.get("blocked_pages"), list) else []
    artifacts = state.get("artifacts") if isinstance(state.get("artifacts"), dict) else {}
    citations = [
        citation
        for record in records
        if isinstance(record, dict)
        for citation in record.get("citations", [])
        if isinstance(citation, dict)
    ]
    status = str(state.get("status") or "")
    run_status = (
        "success"
        if status == "complete" and records
        else "blocked_with_evidence"
        if blocked or sources
        else "failed"
    )
    result = {
        "run_id": run_id,
        "company": company,
        "use_case": use_case,
        "url": url,
        "mode": mode,
        "status_text": status,
        "run_status": run_status,
        "record_count": len(records),
        "source_count": len(sources),
        "blocked_count": len(blocked),
        "citation_count": len(citations),
        "artifact_count": len([value for value in artifacts.values() if value]),
        "artifact_summary": json.dumps(artifacts, sort_keys=True)[:500],
    }
    (output_dir / "service-live-result.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    _write_certification_evidence(use_case, company, mode, output_dir, result)
    return result


def _poll_run(base_url: str, run_id: str) -> dict[str, Any]:
    deadline = time.time() + 180
    state: dict[str, Any] = {}
    while time.time() < deadline:
        state = _request_json(f"{base_url}/app/runs/{run_id}", method="GET")
        if state.get("status") in {"complete", "failed", "cancelled"}:
            return state
        time.sleep(1)
    return state


def _write_certification_evidence(
    use_case: str,
    company: str,
    mode: str,
    output_dir: Path,
    service_result: dict[str, object],
) -> None:
    evidence_root = os.getenv("SCOUT_CERTIFICATION_EVIDENCE_DIR", "")
    if not evidence_root:
        return
    evidence_dir = Path(evidence_root)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    scenario_id = _certification_scenario_id(use_case, company)
    writes_primary_scenario = not (
        use_case == "products" and company == "Estée Lauder" and mode != "auto"
    )
    if writes_primary_scenario:
        _write_scenario_evidence(
            evidence_dir / f"{scenario_id}.json", scenario_id, output_dir, service_result
        )
    if use_case == "products" and company == "Estée Lauder" and mode == "scout-browser":
        _write_scenario_evidence(
            evidence_dir / "browser_workbench.estee_lauder.json",
            "browser_workbench.estee_lauder",
            output_dir,
            service_result,
        )


def _write_scenario_evidence(
    path: Path,
    scenario_id: str,
    output_dir: Path,
    service_result: dict[str, object],
) -> None:
    records = _read_json_list(output_dir / "records.json")
    if not records:
        records = _read_json_list(output_dir / "algolia" / "products.json")
    sources = _normalize_sources(_read_json_list(output_dir / "source_pages.json"))
    blocked_pages = _normalize_blocked(_read_blocked_pages(output_dir / "blocked_pages.json"))
    if not blocked_pages and str(service_result.get("run_status") or "") == "blocked_with_evidence":
        blocked_pages = _normalize_blocked(
            [
                {
                    "url": service_result.get("url") or "",
                    "reason": "blocked_or_empty_live_result",
                    "evidence_artifact": "service-live-result.json",
                    "provider_attempts": [service_result.get("mode") or "auto"],
                }
            ]
        )
    if not sources:
        sources = _sources_from_records_and_blocked(records, blocked_pages)
    manifest = _read_json_object(output_dir / "manifest.json")
    citations = [
        citation
        for record in records
        for citation in record.get("citations", [])
        if isinstance(citation, dict)
    ]
    artifacts = [
        str(candidate)
        for candidate in [
            output_dir / "manifest.json",
            output_dir / "records.json",
            output_dir / "records.jsonl",
            output_dir / "source_pages.json",
            output_dir / "blocked_pages.json",
            output_dir / "validation.json",
            output_dir / "extraction_report.md",
            output_dir / "urls.json",
            output_dir / "report.md",
            output_dir / "algolia" / "products.json",
            output_dir / "algolia" / "products.ndjson",
            output_dir / "algolia" / "settings.json",
            output_dir / "extracted" / "products.raw.jsonl",
        ]
        if candidate.exists()
    ]
    status = "blocked" if blocked_pages and not records else "success"
    payload = {
        "scenario_id": scenario_id,
        "status": status,
        "run_id": service_result.get("run_id") or manifest.get("run_id"),
        "records": records,
        "sources": sources,
        "citations": citations,
        "artifacts": artifacts,
        "blocked_pages": blocked_pages,
        "raw_response": {
            **service_result,
            "artifact_dir": str(output_dir),
            "manifest": manifest,
            "current_url": service_result.get("url"),
            "provider": service_result.get("mode"),
        },
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _request_json(
    url: str, *, method: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=190) as resp:
            data = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        data = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"{method} {url} failed with {exc.code}: {data}") from exc
    return json.loads(data)


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _read_blocked_pages(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get("blocked_pages"), list):
        return [item for item in data["blocked_pages"] if isinstance(item, dict)]
    return []


def _normalize_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for index, source in enumerate(sources, start=1):
        item = dict(source)
        item.setdefault("url", item.get("source_url") or item.get("final_url") or "")
        item.setdefault("source_id", item.get("source_id") or f"src_{index}")
        normalized.append(item)
    return normalized


def _normalize_blocked(blocked_pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for blocked in blocked_pages:
        item = dict(blocked)
        item.setdefault("reason", item.get("error") or item.get("status") or "blocked")
        item.setdefault("evidence_artifact", "blocked_pages.json")
        item.setdefault("provider_attempts", [item.get("provider") or "unknown"])
        normalized.append(item)
    return normalized


def _sources_from_records_and_blocked(
    records: list[dict[str, Any]],
    blocked_pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        source = record.get("_source") or record.get("source") or {}
        url = ""
        if isinstance(source, dict):
            url = str(source.get("category_url") or source.get("detail_url") or "")
        url = url or str(record.get("url") or "")
        if not url or url in seen:
            continue
        seen.add(url)
        sources.append(
            {
                "source_id": f"src_{len(sources) + 1}",
                "url": url,
                "source_url": url,
                "provider": source.get("extractor", "product_artifact")
                if isinstance(source, dict)
                else "product_artifact",
                "status": "ok",
            }
        )
    for blocked in blocked_pages:
        url = str(blocked.get("url") or blocked.get("category_url") or "")
        if not url or url in seen:
            continue
        seen.add(url)
        sources.append(
            {
                "source_id": f"src_{len(sources) + 1}",
                "url": url,
                "source_url": url,
                "provider": blocked.get("provider") or "blocked",
                "status": "blocked",
                "reason": blocked.get("reason"),
            }
        )
    return sources


def _slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")


def _certification_scenario_id(use_case: str, company: str) -> str:
    area = {"news": "news_blogs"}.get(use_case, use_case)
    if area == "research":
        return "research.public.live"
    if area == "investor" and company == "Estée Lauder":
        return "investor.estee_lauder_parent.live"
    if area == "investor" and company == "British Airways":
        return "investor.british_airways_iag.live"
    return f"{area}.{SCENARIO_COMPANY_SLUGS.get(company, _slug(company).replace('-', '_'))}.live"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_health(base_url: str) -> None:
    deadline = time.time() + 60
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception as exc:  # pragma: no cover - startup race diagnostics
            last_error = exc
        time.sleep(1)
    raise AssertionError(f"Scout server did not become healthy: {last_error}")
