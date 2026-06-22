import pytest

from scout.core.platform.run import run_use_case
from scout.core.platform.types import RunRequest


@pytest.mark.asyncio
async def test_run_use_case_writes_standard_artifacts(tmp_path) -> None:
    response = await run_use_case(
        RunRequest(
            use_case="jobs",
            query="AI product marketing roles",
            output_dir=str(tmp_path / "jobs-run"),
        )
    )

    assert response.success is True
    assert response.use_case == "jobs"
    assert response.total_records == 0
    assert (tmp_path / "jobs-run" / "manifest.json").exists()
    assert (tmp_path / "jobs-run" / "records.jsonl").exists()
    assert (tmp_path / "jobs-run" / "extraction_report.md").exists()


@pytest.mark.asyncio
async def test_run_use_case_routes_jobs_to_job_runner(tmp_path) -> None:
    profile_path = tmp_path / "job-profile.yaml"
    output_dir = tmp_path / "jobs-run"
    profile_path.write_text(
        """
desired_titles:
  - AI Product Marketing Manager
target_companies:
  - name: Adobe
    website: https://www.adobe.com
""".strip()
    )

    response = await run_use_case(
        RunRequest(use_case="jobs", profile_path=str(profile_path), output_dir=str(output_dir))
    )

    assert response.success is True
    assert response.total_records == 1


@pytest.mark.asyncio
async def test_run_use_case_rejects_unknown_use_case(tmp_path) -> None:
    response = await run_use_case(
        RunRequest(
            use_case="unknown",
            query="anything",
            output_dir=str(tmp_path / "unknown-run"),
        )
    )

    assert response.success is False
    assert "Unsupported use case" in response.error
