from pathlib import Path

from scout.core.use_cases.jobs import load_job_search_profile


def test_load_job_search_profile_from_yaml(tmp_path) -> None:
    profile_path = tmp_path / "job-profile.yaml"
    profile_path.write_text(
        """
desired_titles:
  - AI Product Marketing Manager
  - Developer Advocate
salary_min_usd: 160000
locations:
  - Remote
  - New York
role_keywords:
  - AI
  - developer platform
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

    profile = load_job_search_profile(profile_path)

    assert profile.salary_min_usd == 160000
    assert profile.target_companies[0].name == "Adobe"
    assert profile.target_companies[1].careers_url == "https://www.salesforce.com/company/careers/"


def test_load_job_search_profile_rejects_non_mapping_yaml(tmp_path) -> None:
    profile_path = tmp_path / "job-profile.yaml"
    profile_path.write_text("- not\n- a\n- mapping\n")

    try:
        load_job_search_profile(profile_path)
    except ValueError as exc:
        assert "must contain a YAML mapping" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_example_job_hunter_profile_is_loadable() -> None:
    profile_path = Path("examples/job-hunter/job-profile.yaml")

    profile = load_job_search_profile(profile_path)

    assert "AI Product Marketing Manager" in profile.desired_titles
    assert profile.salary_min_usd == 160000
    assert [company.name for company in profile.target_companies] == ["Adobe", "Salesforce"]
