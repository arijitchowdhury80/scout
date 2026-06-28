import json
from pathlib import Path

from typer.testing import CliRunner

import scout.cli as cli
from scout.cli import app
from scout.core.platform.account_service import HostedAccountService
from scout.core.platform.account_sqlite_store import SQLiteHostedAccountStore
from scout.core.platform.hosted import HostedPlan, plan_limits
from scout.core.platform.types import RunResponse


def _product_record_payload() -> dict:
    return {
        "objectID": "prod_1",
        "name": "Advanced Night Repair Serum",
        "url": "https://shop.example.com/product/anr",
        "brand": "Estee Lauder",
        "price": 85.0,
        "currency": "USD",
        "categories": ["Skin Care"],
        "_source": {
            "url": "https://shop.example.com/product/anr",
            "extractor": "listing",
            "category_url": "https://shop.example.com/skin-care",
            "category_name": "Skin Care",
        },
        "citations": [
            {
                "source_id": "src_1",
                "source_url": "https://shop.example.com/skin-care",
                "field": "name",
                "claim": "Advanced Night Repair Serum",
                "snippet": "Advanced Night Repair Serum",
                "confidence": 0.75,
            }
        ],
        "completeness_score": 0.75,
    }


def test_run_command_lists_supported_use_cases() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["run", "--help"])

    assert result.exit_code == 0
    assert "products" in result.output
    assert "company" in result.output
    assert "careers" in result.output
    assert "jobs" in result.output
    assert "prism" in result.output
    assert "investor" in result.output
    assert "website-quality" in result.output


def test_product_export_command_writes_requested_formats() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        records_path = Path("records.json")
        records_path.write_text(json.dumps([_product_record_payload()]), encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "product-export",
                str(records_path),
                "--output-dir",
                "exports",
                "--format",
                "csv",
                "--format",
                "sqlite",
            ],
        )

        assert result.exit_code == 0
        assert '"record_count": 1' in result.output
        assert Path("exports/products.csv").exists()
        assert Path("exports/products.sqlite").exists()


def test_product_export_command_accepts_records_envelope() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        records_path = Path("records.json")
        records_path.write_text(
            json.dumps({"records": [_product_record_payload()]}),
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            [
                "product-export",
                str(records_path),
                "--output-dir",
                "exports",
                "--format",
                "jsonl",
            ],
        )

        assert result.exit_code == 0
        assert Path("exports/products.jsonl").exists()


def test_product_export_command_fails_for_missing_file() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["product-export", "missing.json", "--output-dir", "exports"],
        )

        assert result.exit_code == 1
        assert "Product records file does not exist" in result.output


def test_hosted_provision_command_creates_usable_key_without_storing_raw_key() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            [
                "hosted-provision",
                "--email",
                "builder@example.com",
                "--db",
                "hosted.sqlite",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        raw_key = data["raw_api_key"]
        service = HostedAccountService(SQLiteHostedAccountStore("hosted.sqlite"))
        auth = service.authenticate_key(raw_key, required_scope="runs:create")
        balance = service.get_balance(data["tenant_id"])
        limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)

        assert data["success"] is True
        assert data["plan"] == "hosted_beta_pass"
        assert data["email"] == "builder@example.com"
        assert raw_key.startswith("scout_live_")
        assert auth.allowed is True
        assert balance.standard_credits_remaining == limits.standard_credits
        assert balance.browser_credits_remaining == limits.browser_credits
        assert raw_key not in Path("hosted.sqlite").read_text(encoding="utf-8", errors="ignore")


def test_hosted_provision_command_rejects_local_free_plan() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            [
                "hosted-provision",
                "--email",
                "builder@example.com",
                "--plan",
                "local_free",
                "--db",
                "hosted.sqlite",
            ],
        )

        assert result.exit_code == 1
        assert "not hosted-enabled" in result.output


def test_run_jobs_placeholder_is_explicit() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            [
                "run",
                "jobs",
                "--query",
                "AI product marketing roles",
                "--output-dir",
                "jobs-run",
            ],
        )

    assert result.exit_code == 0
    assert '"success": true' in result.output
    assert '"use_case": "jobs"' in result.output


def test_run_jobs_writes_artifacts() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["run", "jobs", "--output-dir", "jobs-run"])

        assert result.exit_code == 0
        from pathlib import Path

        assert Path("jobs-run/manifest.json").exists()
        assert Path("jobs-run/records.jsonl").exists()


def test_run_jobs_accepts_profile_file() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        from pathlib import Path

        Path("job-profile.yaml").write_text(
            """
desired_titles:
  - AI Product Marketing Manager
target_companies:
  - name: Adobe
    website: https://www.adobe.com
""".strip()
        )

        result = runner.invoke(
            app,
            [
                "run",
                "jobs",
                "--profile",
                "job-profile.yaml",
                "--output-dir",
                "jobs-run",
            ],
        )

        assert result.exit_code == 0
        assert '"total_records": 1' in result.output


def test_run_jobs_accepts_job_url_option() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        from pathlib import Path

        Path("job-profile.yaml").write_text(
            """
desired_titles:
  - Director Enterprise Customer Success
salary_min_usd: 250000
seniority:
  - Director
role_keywords:
  - AI
  - enterprise
  - customer success
""".strip()
        )

        result = runner.invoke(
            app,
            [
                "run",
                "jobs",
                "--profile",
                "job-profile.yaml",
                "--job-url",
                "https://job-boards.greenhouse.io/eve/jobs/4245857009",
                "--output-dir",
                "jobs-run",
            ],
        )

        assert result.exit_code == 0
        assert '"success": true' in result.output


def test_run_company_accepts_mode_option() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            [
                "run",
                "company",
                "--query",
                "Adobe",
                "--mode",
                "browser",
                "--output-dir",
                "company-run",
            ],
        )

        assert result.exit_code == 0
        assert '"use_case": "company"' in result.output
        assert '"host_browser"' in result.output


def test_run_company_uses_workdir_option_when_output_dir_missing() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            [
                "run",
                "company",
                "--query",
                "Adobe",
                "--workdir",
                "scout-work",
            ],
        )

        assert result.exit_code == 0
        assert '"use_case": "company"' in result.output

        from pathlib import Path

        run_dirs = list(Path("scout-work").glob("company-adobe-*"))
        assert len(run_dirs) == 1
        assert (run_dirs[0] / "manifest.json").exists()


def test_run_website_quality_cli_passes_url_query_and_crawler(monkeypatch) -> None:
    captured = {}

    async def fake_run_use_case(req, crawler=None):
        captured["query"] = req.query
        captured["crawler_present"] = crawler is not None
        return RunResponse(
            success=True,
            use_case=req.use_case,
            output_dir=req.output_dir,
            total_records=1,
        )

    monkeypatch.setattr(cli, "run_use_case", fake_run_use_case)

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            [
                "run",
                "website-quality",
                "--query",
                "https://www.britishairways.com/content/information/about-ba",
                "--output-dir",
                "quality-run",
            ],
        )

    assert result.exit_code == 0
    assert captured == {
        "query": "https://www.britishairways.com/content/information/about-ba",
        "crawler_present": True,
    }


def test_certify_command_writes_feature_certification_report() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            [
                "certify",
                "--output-root",
                "validation-output",
                "--report",
                "docs/validation/scout-feature-certification-2026-06-27.md",
                "--timestamp",
                "2026-06-27T12:00:00Z",
            ],
        )

        assert result.exit_code == 0
        assert "feature-results.json" in result.output
        assert "scout-feature-certification-2026-06-27.md" in result.output

        from pathlib import Path

        results = list(Path("validation-output").glob("*/feature-results.json"))
        assert len(results) == 1
        report = Path("docs/validation/scout-feature-certification-2026-06-27.md")
        assert report.exists()
        assert "Expected vs Actual" in report.read_text()


def test_certify_command_accepts_actual_evidence() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        evidence = Path("evidence")
        evidence.mkdir()
        (evidence / "company.fixture.json").write_text(
            json.dumps(
                {
                    "scenario_id": "company.fixture",
                    "status": "success",
                    "records": [
                        {
                            "record_type": "company",
                            "name": "Acme",
                            "citations": [{"source_id": "src"}],
                        }
                    ],
                    "sources": [{"source_id": "src", "url": "https://example.com"}],
                    "citations": [{"source_id": "src"}],
                    "raw_response": {"source": "unit-test"},
                }
            ),
            encoding="utf-8",
        )
        result = runner.invoke(
            app,
            [
                "certify",
                "--output-root",
                "validation-output",
                "--report",
                "docs/validation/scout-feature-certification-2026-06-27.md",
                "--timestamp",
                "2026-06-27T12:00:00Z",
                "--evidence",
                str(evidence),
            ],
        )

        assert result.exit_code == 0
        assert '"mode": "evidence"' in result.output
        assert '"passed": 1' in result.output
        results = list(Path("validation-output").glob("*/feature-results.json"))
        payload = json.loads(results[0].read_text())
        company = next(r for r in payload["results"] if r["scenario_id"] == "company.fixture")
        assert company["status"] == "pass"
