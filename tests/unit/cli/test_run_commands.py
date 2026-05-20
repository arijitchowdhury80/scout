from typer.testing import CliRunner

from scout.cli import app


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
