import pytest

from scout.core.platform.run import run_use_case
from scout.core.platform.types import RunRequest


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


@pytest.mark.asyncio
async def test_run_use_case_rejects_removed_website_quality_use_case(tmp_path) -> None:
    response = await run_use_case(
        RunRequest(
            use_case="website-quality",
            query="anything",
            output_dir=str(tmp_path / "website-quality-run"),
        )
    )

    assert response.success is False
    assert response.error == "Unsupported use case: website-quality"


@pytest.mark.asyncio
async def test_run_use_case_rejects_removed_jobs_use_case(tmp_path) -> None:
    response = await run_use_case(
        RunRequest(
            use_case="jobs",
            query="anything",
            output_dir=str(tmp_path / "jobs-run"),
        )
    )

    assert response.success is False
    assert response.error == "Unsupported use case: jobs"
