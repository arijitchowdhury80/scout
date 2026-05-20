from scout.core.use_cases.intelligence import (
    CareerSiteRecord,
    InvestorAssetRecord,
    NewsSignalRecord,
    ResearchRecord,
)
from scout.core.use_cases.prism import CompanyRecord, CompanySocialRecord, ExecutiveRecord


def test_company_exec_and_social_contracts_have_record_types() -> None:
    company = CompanyRecord(objectID="company_adobe", name="Adobe", website="https://adobe.com")
    executive = ExecutiveRecord(objectID="exec_adobe_ceo", company="Adobe", name="CEO")
    social = CompanySocialRecord(
        objectID="social_adobe_linkedin",
        company="Adobe",
        platform="linkedin",
        url="https://linkedin.com/company/adobe",
    )

    assert company.record_type == "company"
    assert executive.record_type == "executive"
    assert social.record_type == "company_social"


def test_investor_careers_news_and_research_contracts() -> None:
    investor = InvestorAssetRecord(
        objectID="investor_adobe_overview",
        company="Adobe",
        asset_type="investor_page",
        url="https://www.adobe.com/investor-relations.html",
    )
    careers = CareerSiteRecord(
        objectID="careers_adobe",
        company="Adobe",
        careers_url="https://careers.adobe.com",
        ats_platform="workday",
    )
    news = NewsSignalRecord(
        objectID="news_adobe_ai",
        company="Adobe",
        title="Adobe launches AI update",
        url="https://news.adobe.com",
    )
    research = ResearchRecord(
        objectID="research_adobe_about",
        topic="Adobe",
        url="https://www.adobe.com/about-adobe.html",
    )

    assert investor.schema_version == "investor_asset.v1"
    assert careers.record_type == "career_site"
    assert news.record_type == "news_signal"
    assert research.record_type == "research_record"
