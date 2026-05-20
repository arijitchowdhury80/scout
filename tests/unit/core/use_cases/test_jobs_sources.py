from scout.core.use_cases.jobs_sources import JobSourcePlatform, detect_job_source_platform


def test_detects_greenhouse_job_board_url() -> None:
    assert (
        detect_job_source_platform("https://job-boards.greenhouse.io/eve/jobs/4245857009")
        == JobSourcePlatform.GREENHOUSE
    )


def test_detects_ashby_job_url() -> None:
    assert (
        detect_job_source_platform(
            "https://jobs.ashbyhq.com/kong/21690b70-385c-49bf-9942-a949b65642fe/application"
        )
        == JobSourcePlatform.ASHBY
    )


def test_detects_workday_job_url() -> None:
    assert (
        detect_job_source_platform(
            "https://salesforce.wd12.myworkdayjobs.com/External_Career_Site/job/"
            "California---San-Francisco/Customer-Success-Manager--Director_JR341622"
        )
        == JobSourcePlatform.WORKDAY
    )


def test_unknown_native_careers_url_is_native() -> None:
    assert (
        detect_job_source_platform("https://jobs.intuit.com/job/-/-/27595/94741635984")
        == JobSourcePlatform.NATIVE
    )
