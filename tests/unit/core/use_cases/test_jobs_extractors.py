from pathlib import Path

from scout.core.use_cases.jobs_extractors import extract_job_posting_from_html
from scout.core.use_cases.jobs_sources import JobSourcePlatform


def test_extracts_greenhouse_director_cs_fixture() -> None:
    html = Path("tests/fixtures/jobs/greenhouse_eve_director_cs.html").read_text()

    record = extract_job_posting_from_html(
        html=html,
        url="https://job-boards.greenhouse.io/eve/jobs/4245857009",
        platform=JobSourcePlatform.GREENHOUSE,
    )

    assert record.company == "Eve"
    assert record.objectID == "job_eve_4245857009"
    assert record.title == "Director of Enterprise Customer Success"
    assert record.location == "Remote, United States"
    assert record.salary_min == 225000
    assert record.salary_max == 280000
    assert record.ats_platform == "greenhouse"
    assert "enterprise customer success" in record.description.lower()
