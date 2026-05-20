from scout.core.use_cases.jobs import JobPostingRecord, JobSearchProfile, TargetCompanyRecord


def test_job_search_profile_contract() -> None:
    profile = JobSearchProfile(
        desired_titles=["AI Product Marketing Manager"],
        salary_min_usd=160000,
        locations=["Remote", "New York"],
        role_keywords=["AI", "developer platform"],
    )

    assert profile.salary_min_usd == 160000
    assert "Remote" in profile.locations


def test_job_search_profile_accepts_seed_job_urls_and_strict_filters() -> None:
    profile = JobSearchProfile(
        desired_titles=["Director, Enterprise Customer Success"],
        salary_min_usd=250000,
        seniority=["Director", "Senior Director", "VP"],
        job_urls=["https://job-boards.greenhouse.io/eve/jobs/4245857009"],
        must_have_terms=["AI", "enterprise", "customer success"],
        reject_terms=["intern", "support representative"],
    )

    assert profile.salary_min_usd == 250000
    assert profile.job_urls == ["https://job-boards.greenhouse.io/eve/jobs/4245857009"]
    assert "AI" in profile.must_have_terms


def test_target_company_record_contract() -> None:
    company = TargetCompanyRecord(
        objectID="company_adobe",
        company="Adobe",
        website="https://www.adobe.com",
        careers_url="https://careers.adobe.com/us/en/",
        reason_matched="Company hires for AI product marketing and developer platform roles.",
        confidence=0.9,
    )

    assert company.company == "Adobe"
    assert company.confidence == 0.9


def test_job_posting_record_contract() -> None:
    job = JobPostingRecord(
        objectID="job_adobe_123",
        company="Adobe",
        title="Senior Product Marketing Manager, AI",
        url="https://careers.adobe.com/us/en/job/123",
        location="New York",
        matched_terms=["AI", "Product Marketing"],
    )

    assert job.company == "Adobe"
    assert job.matched_terms == ["AI", "Product Marketing"]


def test_job_posting_record_carries_match_and_reject_reasons() -> None:
    record = JobPostingRecord(
        objectID="job_eve_4245857009",
        company="Eve",
        title="Director of Enterprise Customer Success",
        url="https://job-boards.greenhouse.io/eve/jobs/4245857009",
        salary_min=225000,
        salary_max=280000,
        ats_platform="greenhouse",
        match_score=92,
        match_reasons=["Director-level enterprise CS role", "AI-native company"],
        reject_reasons=[],
        source_confidence=0.95,
    )

    assert record.match_score == 92
    assert "AI-native company" in record.match_reasons
    assert record.source_confidence == 0.95
