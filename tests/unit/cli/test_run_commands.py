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


def test_launch_readiness_command_reports_private_beta_and_public_status() -> None:
    runner = CliRunner()
    root = Path(__file__).resolve().parents[3]

    result = runner.invoke(app, ["launch-readiness", "--root", str(root)])

    assert result.exit_code == 0
    assert "Private beta: ready_with_limits" in result.output
    assert "Public launch: blocked" in result.output


def test_launch_readiness_command_outputs_json() -> None:
    runner = CliRunner()
    root = Path(__file__).resolve().parents[3]

    result = runner.invoke(app, ["launch-readiness", "--root", str(root), "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["private_beta"]["status"] == "ready_with_limits"
    assert data["public_launch"]["status"] == "blocked"


def test_launch_readiness_command_can_fail_public_gate() -> None:
    runner = CliRunner()
    root = Path(__file__).resolve().parents[3]

    result = runner.invoke(app, ["launch-readiness", "--root", str(root), "--require-public"])

    assert result.exit_code == 1
    assert "Public launch: blocked" in result.output


def test_launch_readiness_command_can_filter_by_blocker_id() -> None:
    runner = CliRunner()
    root = Path(__file__).resolve().parents[3]

    result = runner.invoke(
        app,
        [
            "launch-readiness",
            "--root",
            str(root),
            "--blocker-id",
            "license-decision",
        ],
    )

    assert result.exit_code == 0
    assert "Blocker summary: 1 total" in result.output
    assert "license-decision: license decision [founder_decision]" in result.output
    assert "stripe-real-test-mode-smoke" not in result.output


def test_launch_decision_draft_command_writes_prefilled_draft() -> None:
    runner = CliRunner()
    root = Path(__file__).resolve().parents[3]
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            [
                "launch-decision-draft",
                "--root",
                str(root),
                "--blocker-id",
                "license-decision",
                "--decision-id",
                "SCOUT-DEC-20260629-04",
                "--date",
                "2026-06-29",
            ],
        )

        assert result.exit_code == 0
        assert "founder-decision-draft-SCOUT-DEC-20260629-04.md" in result.output
        draft = Path(
            "docs/product/founder-decision-drafts/founder-decision-draft-SCOUT-DEC-20260629-04.md"
        )
        assert draft.exists()
        content = draft.read_text(encoding="utf-8")
        assert "Related blocker type: founder_decision" in content
        assert "Public launch allowed by this decision? No" in content


def test_launch_decision_drafts_command_writes_founder_packet() -> None:
    runner = CliRunner()
    root = Path(__file__).resolve().parents[3]
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            [
                "launch-decision-drafts",
                "--root",
                str(root),
                "--owner",
                "Arijit",
                "--include-shared-owner",
                "--decision-date",
                "20260629",
                "--date",
                "2026-06-29",
            ],
        )

        assert result.exit_code == 0
        assert "Wrote 6 founder decision drafts" in result.output
        draft_dir = Path("docs/product/founder-decision-drafts")
        drafts = sorted(draft_dir.glob("founder-decision-draft-SCOUT-DEC-20260629-*.md"))
        assert len(drafts) == 6
        combined = "\n".join(path.read_text(encoding="utf-8") for path in drafts)
        assert "Related release gate: license decision" in combined
        assert "Related release gate: Stripe real test-mode smoke" in combined
        assert "Public launch allowed by this decision? No" in combined


def test_launch_decision_check_command_validates_completed_record() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        record = Path("founder-decision-record-SCOUT-DEC-20260629-06.md")
        record.write_text(
            """# Scout Founder Decision Record: License

Decision ID: SCOUT-DEC-20260629-06
Date: 2026-06-29
Decision owner: Arijit Chowdhury
Recorded by: Codex
Status: Approved
Related blocker type: founder_decision
Related release gate: License decision recorded.
Source prompt / meeting / approval note: CLI test fixture

## Approved decision

Scout local/core is licensed as Apache-2.0.

## Rejected alternatives

- MIT

## Scope and limits

- Applies to: local package and source distribution
- Does not apply to: hosted service terms
- Private beta only? Yes
- Public launch allowed by this decision? No

## Required Codex follow-up

- [ ] Code/doc change: add LICENSE and pyproject license expression
- [ ] Verification command: scout launch-readiness --blocker-id license-decision
- [ ] Evidence file to update: docs/product/launch-evidence-index-2026-06-29.md
- [ ] Release checklist gate to update: License decision recorded.

## Expiration or revisit trigger

Before public launch.

## Evidence links

- Release checklist: docs/product/release-checklist.md
- Decision packet: docs/product/public-launch-action-packet-2026-06-29.md
- Supporting brief: docs/legal/scout-license-distribution-decision-brief-2026-06-29.md
- Verification output: pending
""",
            encoding="utf-8",
        )

        result = runner.invoke(app, ["launch-decision-check", str(record)])

        assert result.exit_code == 0
        assert "PASS: Scout founder decision record validation satisfied." in result.output
        assert "SCOUT-DEC-20260629-06: Approved" in result.output


def test_launch_decision_check_command_scans_existing_records() -> None:
    runner = CliRunner()
    root = Path(__file__).resolve().parents[3]

    result = runner.invoke(app, ["launch-decision-check", "--root", str(root), "--check-existing"])

    assert result.exit_code == 0
    assert "PASS: 0 founder decision records found." in result.output


def test_launch_decision_check_command_scans_existing_drafts() -> None:
    runner = CliRunner()
    root = Path(__file__).resolve().parents[3]

    result = runner.invoke(app, ["launch-decision-check", "--root", str(root), "--check-drafts"])

    assert result.exit_code == 0
    assert "PASS: 6 founder decision drafts are safe for review." in result.output
    assert "SCOUT-DEC-20260629-01: Deferred" in result.output
    assert "SCOUT-DEC-20260629-06: Deferred" in result.output


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


def test_product_export_command_writes_google_sheets_import_bundle() -> None:
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
                "google_sheets",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["files"]["google_sheets_csv"] == "exports/products.google-sheets.csv"
        assert data["files"]["google_sheets_instructions"] == (
            "exports/products.google-sheets-import.md"
        )
        assert Path("exports/products.google-sheets.csv").exists()
        assert Path("exports/products.google-sheets-import.md").exists()


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


def test_hosted_curl_command_prints_copyable_me_request() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "hosted-curl",
            "--base-url",
            "https://scout.example.com",
            "--endpoint",
            "me",
        ],
    )

    assert result.exit_code == 0
    assert 'curl "https://scout.example.com/v1/hosted/me"' in result.output
    assert "Authorization: Bearer $SCOUT_HOSTED_API_KEY" in result.output
    assert "X-API-Key" not in result.output


def test_hosted_curl_command_prints_copyable_scrape_request() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "hosted-curl",
            "--base-url",
            "https://scout.example.com/",
            "--endpoint",
            "scrape",
            "--url",
            "https://example.com",
        ],
    )

    assert result.exit_code == 0
    assert 'curl -X POST "https://scout.example.com/v1/hosted/scrape"' in result.output
    assert '-d \'{"url":"https://example.com","formats":["markdown"],"timeout_ms":30000}\'' in (
        result.output
    )


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
