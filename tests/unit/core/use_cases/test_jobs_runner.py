import json
from pathlib import Path

from scout.core.platform.types import RunRequest
from scout.core.use_cases.jobs_runner import run_jobs_use_case


def test_run_jobs_use_case_writes_target_company_records(tmp_path) -> None:
    profile_path = tmp_path / "job-profile.yaml"
    output_dir = tmp_path / "jobs-run"
    profile_path.write_text(
        """
desired_titles:
  - AI Product Marketing Manager
target_companies:
  - name: Adobe
    website: https://www.adobe.com
    careers_url: https://careers.adobe.com/us/en/
    linkedin_url: https://www.linkedin.com/company/adobe/
    industry: Software
  - name: Salesforce
    website: https://www.salesforce.com
    careers_url: https://www.salesforce.com/company/careers/
""".strip()
    )

    response = run_jobs_use_case(
        RunRequest(use_case="jobs", profile_path=str(profile_path), output_dir=str(output_dir))
    )

    assert response.success is True
    assert response.total_records == 2

    records = json.loads((output_dir / "records.json").read_text())
    assert records[0]["objectID"] == "target_company_adobe"
    assert records[0]["record_type"] == "target_company"
    assert records[0]["citations"][0]["field"] == "target_companies"
    assert records[1]["company"] == "Salesforce"


def test_run_jobs_use_case_reports_missing_targets(tmp_path) -> None:
    profile_path = tmp_path / "job-profile.yaml"
    output_dir = tmp_path / "jobs-run"
    profile_path.write_text(
        """
desired_titles:
  - AI Product Marketing Manager
role_keywords:
  - AI
""".strip()
    )

    response = run_jobs_use_case(
        RunRequest(use_case="jobs", profile_path=str(profile_path), output_dir=str(output_dir))
    )

    assert response.success is True
    assert response.total_records == 0

    validation = json.loads((output_dir / "validation.json").read_text())
    assert validation[0]["code"] == "no_target_companies"


def test_run_jobs_use_case_extracts_and_scores_seed_job_url(tmp_path) -> None:
    profile_path = tmp_path / "job-profile.yaml"
    fixture_path = Path("tests/fixtures/jobs/greenhouse_eve_director_cs.html")
    output_dir = tmp_path / "jobs-run"
    profile_path.write_text(
        f"""
desired_titles:
  - Director Enterprise Customer Success
salary_min_usd: 250000
seniority:
  - Director
role_keywords:
  - AI
  - enterprise
  - customer success
  - renewals
  - expansion
job_urls:
  - fixture://{fixture_path}
""".strip()
    )

    response = run_jobs_use_case(
        RunRequest(use_case="jobs", profile_path=str(profile_path), output_dir=str(output_dir))
    )

    assert response.success is True
    assert response.total_records == 1

    records = json.loads((output_dir / "records.json").read_text())
    assert records[0]["record_type"] == "job_posting"
    assert records[0]["objectID"] == "job_eve_4245857009"
    assert records[0]["company"] == "Eve"
    assert records[0]["ats_platform"] == "greenhouse"
    assert records[0]["match_score"] >= 85
    cited_fields = {citation["field"] for citation in records[0]["citations"]}
    assert {"title", "compensation", "location", "department"} <= cited_fields

    sources = json.loads((output_dir / "source_pages.json").read_text())
    assert sources[0]["provider"] == "saved"
    assert sources[0]["source_id"] == records[0]["citations"][0]["source_id"]
