from scout.core.use_cases.prism import CompanyRecord, CompanySocialRecord, ExecutiveRecord


def test_company_record_contract() -> None:
    company = CompanyRecord(
        objectID="company_nike",
        name="Nike",
        website="https://www.nike.com/",
        linkedin_url="https://www.linkedin.com/company/nike/",
    )

    assert company.name == "Nike"
    assert company.linkedin_url.endswith("/nike/")


def test_company_social_record_contract() -> None:
    social = CompanySocialRecord(
        objectID="social_nike_x",
        company="Nike",
        platform="x",
        url="https://x.com/Nike",
    )

    assert social.platform == "x"


def test_executive_record_contract() -> None:
    executive = ExecutiveRecord(
        objectID="exec_nike_example",
        company="Nike",
        name="Example Executive",
        title="Chief Example Officer",
        linkedin_url="https://www.linkedin.com/in/example/",
    )

    assert executive.title == "Chief Example Officer"
