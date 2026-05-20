from scout.core.use_cases.jobs import JobPostingRecord, JobSearchProfile
from scout.core.use_cases.jobs_scoring import score_job_posting


def test_scores_ai_enterprise_director_cs_role_high() -> None:
    profile = JobSearchProfile(
        desired_titles=["Director Enterprise Customer Success"],
        salary_min_usd=250000,
        seniority=["Director", "Senior Director", "VP"],
        role_keywords=["AI", "enterprise", "customer success", "renewals", "expansion"],
        reject_terms=["intern", "support representative"],
    )
    record = JobPostingRecord(
        objectID="job_eve_4245857009",
        company="Eve",
        title="Director of Enterprise Customer Success",
        url="https://job-boards.greenhouse.io/eve/jobs/4245857009",
        salary_min=225000,
        salary_max=280000,
        description=(
            "AI platform. Enterprise customer success, executive relationships, "
            "renewals, adoption, expansion."
        ),
    )

    scored = score_job_posting(record, profile)

    assert scored.match_score >= 85
    assert "Director-level role" in scored.match_reasons
    assert scored.reject_reasons == []


def test_rejects_below_compensation_threshold() -> None:
    profile = JobSearchProfile(salary_min_usd=250000, seniority=["Director"])
    record = JobPostingRecord(
        objectID="job_low_comp",
        company="Example",
        title="Director Customer Success",
        url="https://example.com/job",
        salary_min=150000,
        salary_max=180000,
        description="Enterprise customer success role.",
    )

    scored = score_job_posting(record, profile)

    assert scored.match_score < 70
    assert "Compensation below threshold" in scored.reject_reasons
