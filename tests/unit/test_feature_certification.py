from __future__ import annotations

import json
from pathlib import Path

from scout.validation.certification import (
    REQUIRED_FEATURE_AREAS,
    FEATURE_CERTIFICATION_MATRIX,
    CertificationActual,
    CertificationResult,
    certification_results_from_evidence,
    certify_actual,
    load_certification_evidence,
    write_certification_outputs,
)
from scout.validation.evidence_generator import generate_service_certification_evidence


def test_feature_certification_matrix_covers_all_required_areas() -> None:
    areas = {scenario.area for scenario in FEATURE_CERTIFICATION_MATRIX}

    assert REQUIRED_FEATURE_AREAS <= areas
    assert len(FEATURE_CERTIFICATION_MATRIX) >= len(REQUIRED_FEATURE_AREAS)

    for scenario in FEATURE_CERTIFICATION_MATRIX:
        assert scenario.scenario_id
        assert scenario.area
        assert scenario.tier in {"L0", "L1", "L2", "L3"}
        assert scenario.interface in {
            "unit",
            "fixture",
            "api",
            "cli",
            "ui",
            "live",
            "manual",
            "user-browser",
        }
        assert scenario.input_data
        assert scenario.expected_output
        assert scenario.acceptance_criteria
        assert scenario.required_actual_fields


def test_certify_actual_fails_when_expected_counts_and_fields_are_missing() -> None:
    scenario = next(s for s in FEATURE_CERTIFICATION_MATRIX if s.scenario_id == "products.fixture")
    actual = CertificationActual(
        status="success",
        records=[],
        sources=[],
        citations=[],
        artifacts=[],
        blocked_pages=[],
        raw_response={"records": []},
    )

    result = certify_actual(scenario, actual)

    assert result.status == "fail"
    assert "records below minimum" in " ".join(result.failures)
    assert "citations below minimum" in " ".join(result.failures)


def test_certify_actual_accepts_blocked_run_only_with_complete_blocked_evidence() -> None:
    scenario = next(
        s for s in FEATURE_CERTIFICATION_MATRIX if s.scenario_id == "products.estee_lauder.live"
    )
    blocked_actual = CertificationActual(
        status="blocked",
        records=[],
        sources=[
            {
                "source_id": "src_1",
                "url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
            }
        ],
        citations=[],
        artifacts=["manifest.json", "blocked_pages.json", "extraction_report.md"],
        blocked_pages=[
            {
                "url": "https://www.esteelauder.com/products/681/product-catalog/skin-care",
                "provider_attempts": ["crawler", "scout-browser"],
                "reason": "403 blocked",
                "evidence_artifact": "blocked_pages.json",
            }
        ],
        raw_response={"status": "blocked"},
    )

    result = certify_actual(scenario, blocked_actual)

    assert result.status == "pass"
    assert result.failures == []
    assert "blocked evidence accepted" in " ".join(result.notes)


def test_write_certification_outputs_records_expected_vs_actual(tmp_path: Path) -> None:
    scenario = next(s for s in FEATURE_CERTIFICATION_MATRIX if s.scenario_id == "company.fixture")
    result = CertificationResult(
        scenario=scenario,
        status="pass",
        actual=CertificationActual(
            status="success",
            records=[
                {"record_type": "company", "name": "Acme", "citations": [{"source_id": "src"}]}
            ],
            sources=[{"source_id": "src", "url": "https://example.com"}],
            citations=[{"source_id": "src", "field": "name"}],
            artifacts=["manifest.json", "records.json", "source_pages.json"],
            blocked_pages=[],
            raw_response={"ok": True},
        ),
        failures=[],
        notes=["fixture accepted"],
    )

    outputs = write_certification_outputs(
        [result],
        output_root=tmp_path / "validation-output",
        report_path=tmp_path / "docs" / "validation" / "scout-feature-certification-2026-06-27.md",
        timestamp="2026-06-27T12:00:00Z",
    )

    feature_results = json.loads(outputs.feature_results_json.read_text())
    assert feature_results["summary"]["total"] == 1
    assert feature_results["results"][0]["expected_output"] == scenario.expected_output
    assert feature_results["results"][0]["actual"]["record_count"] == 1
    assert feature_results["results"][0]["pass_fail_reason"] == "pass"
    assert outputs.report_md.exists()
    assert "Expected vs Actual" in outputs.report_md.read_text()
    assert (outputs.actual_responses_dir / "company.fixture.json").exists()


def test_load_certification_evidence_from_single_file(tmp_path: Path) -> None:
    evidence_file = tmp_path / "company.fixture.json"
    evidence_file.write_text(
        json.dumps(
            {
                "scenario_id": "company.fixture",
                "status": "success",
                "records": [
                    {
                        "record_type": "company",
                        "name": "Acme",
                        "citations": [{"source_id": "src", "source_url": "https://example.com"}],
                    }
                ],
                "sources": [{"source_id": "src", "url": "https://example.com"}],
                "citations": [{"source_id": "src", "field": "name"}],
                "raw_response": {"source": "unit-test"},
            }
        ),
        encoding="utf-8",
    )

    evidence = load_certification_evidence(evidence_file)
    results = certification_results_from_evidence(evidence, include_missing=False)

    assert set(evidence) == {"company.fixture"}
    assert len(results) == 1
    assert results[0].status == "pass"


def test_load_certification_evidence_from_directory(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "company.fixture.json").write_text(
        json.dumps(
            {
                "scenario_id": "company.fixture",
                "actual": {
                    "status": "success",
                    "records": [{"record_type": "company", "name": "Acme"}],
                    "sources": [{"source_id": "src", "url": "https://example.com"}],
                    "citations": [{"source_id": "src"}],
                    "raw_response": {"source": "unit-test"},
                },
            }
        ),
        encoding="utf-8",
    )
    (evidence_dir / "careers.fixture.json").write_text(
        json.dumps(
            {
                "scenario_id": "careers.fixture",
                "status": "success",
                "records": [{"record_type": "career_site", "careers_url": "https://example.com/careers"}],
                "sources": [{"source_id": "src_careers", "url": "https://example.com/careers"}],
                "citations": [{"source_id": "src_careers"}],
                "raw_response": {"source": "unit-test"},
            }
        ),
        encoding="utf-8",
    )

    evidence = load_certification_evidence(evidence_dir)

    assert sorted(evidence) == ["careers.fixture", "company.fixture"]
    assert evidence["careers.fixture"].record_count == 1


def test_generate_service_certification_evidence_closes_l1_fixture_gaps(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"

    generated = generate_service_certification_evidence(evidence_dir)
    evidence = load_certification_evidence(generated.evidence_dir)
    results = certification_results_from_evidence(evidence, include_missing=False)
    by_id = {result.scenario.scenario_id: result for result in results}

    expected_ids = {
        "scrape.example",
        "crawl.fixture",
        "map.fixture",
        "extract.fixture",
        "screenshot.example",
        "products.fixture",
        "products.captured_dom.fixture",
        "products.user_browser_capture.fixture",
        "products.cdp_harvest.fixture",
        "company.fixture",
        "prism.fixture",
        "investor.fixture",
        "careers.fixture",
        "news_blogs.fixture",
        "research.fixture",
        "docs.fixture",
        "social.fixture",
        "locations.fixture",
        "cli.smoke",
        "api.contract",
        "persistence_sse.restart",
        "algolia.preview",
        "docker_distribution.smoke",
        "docs_validation.snippets",
    }

    assert expected_ids <= set(evidence)
    assert expected_ids <= set(by_id)
    failing = {
        scenario_id: result.failures
        for scenario_id, result in by_id.items()
        if scenario_id in expected_ids and result.status != "pass"
    }
    assert failing == {}
